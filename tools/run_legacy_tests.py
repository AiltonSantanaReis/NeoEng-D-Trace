#!/usr/bin/env python3
"""Run preserved legacy tests without changing the official test suite.

Each test file is launched in an isolated pytest subprocess. This keeps import
or collection errors in one historical file from hiding all other results.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def normalize_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def resolve_tested_commit(project_root: Path) -> str:
    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    tested_commit = process.stdout.strip().lower()
    if (
        process.returncode != 0
        or len(tested_commit) != 40
        or any(character not in "0123456789abcdef" for character in tested_commit)
    ):
        raise RuntimeError("Unable to resolve the tested Git commit")
    ci_commit = os.environ.get("GITHUB_SHA", "").strip().lower()
    if ci_commit and ci_commit != tested_commit:
        raise RuntimeError(
            f"Tested commit {tested_commit} does not match CI commit {ci_commit}"
        )
    return tested_commit


def working_tree_is_dirty(project_root: Path) -> bool:
    process = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("Unable to inspect the tested Git working tree")
    return bool(process.stdout.strip())


def load_manifest(project_root: Path) -> tuple[Path, dict]:
    legacy_root = project_root / "quality" / "legacy_tests"
    manifest_path = legacy_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Legacy manifest not found: {manifest_path}")
    return legacy_root, json.loads(manifest_path.read_text(encoding="utf-8"))


def verify_integrity(legacy_root: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for item in manifest["files"]:
        path = legacy_root / item["path"]
        if not path.is_file():
            errors.append(f"missing: {item['path']}")
            continue
        digest = hashlib.sha256(normalize_lf(path.read_bytes())).hexdigest()
        if digest != item["sha256_lf"]:
            errors.append(
                f"hash mismatch: {item['path']} "
                f"expected={item['sha256_lf']} actual={digest}"
            )
    return errors


def parse_junit(path: Path) -> dict:
    result = {
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "time": 0.0,
        "failure_details": [],
    }
    if not path.is_file():
        result["errors"] = 1
        result["junit_missing"] = True
        return result
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    for suite in suites:
        result["tests"] += int(suite.attrib.get("tests", 0))
        result["failures"] += int(suite.attrib.get("failures", 0))
        result["errors"] += int(suite.attrib.get("errors", 0))
        result["skipped"] += int(suite.attrib.get("skipped", 0))
        result["time"] += float(suite.attrib.get("time", 0.0))
        for case in suite.findall("testcase"):
            for kind in ("failure", "error"):
                detail = case.find(kind)
                if detail is None:
                    continue
                result["failure_details"].append(
                    {
                        "classname": case.attrib.get("classname", ""),
                        "name": case.attrib.get("name", ""),
                        "kind": kind,
                        "message": detail.attrib.get("message", ""),
                        "body": detail.text or "",
                    }
                )
    return result


def load_reconciliation(legacy_root: Path) -> tuple[Path, dict[str, dict]]:
    path = legacy_root / "reconciliation.json"
    if not path.is_file():
        raise FileNotFoundError(f"Legacy reconciliation manifest not found: {path}")

    document = json.loads(path.read_text(encoding="utf-8"))
    expectations: dict[str, dict] = {}
    for item in document.get("expected_failures", []):
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(
                "Every legacy reconciliation entry requires a non-empty id"
            )
        if identifier in expectations:
            raise ValueError(f"Duplicate legacy reconciliation id: {identifier}")
        if not item.get("rationale") or not item.get("replacement_tests"):
            raise ValueError(
                f"Legacy reconciliation {identifier} requires rationale "
                "and replacement_tests"
            )
        expectations[identifier] = item
    return path, expectations


def reconcile_failures(
    selected: list[dict], results: list[dict], expectations: dict[str, dict]
) -> dict:
    selected_stems = {Path(item["path"]).stem for item in selected}
    relevant = {
        identifier: item
        for identifier, item in expectations.items()
        if identifier.split("::", 1)[0] in selected_stems
    }
    matched: set[str] = set()
    unexpected: list[dict] = []

    for result in results:
        stem = Path(result["file"]).stem
        for detail in result.get("failure_details", []):
            identifier = "::".join((stem, detail["classname"], detail["name"]))
            detail["id"] = identifier
            expectation = relevant.get(identifier)
            if expectation is None:
                unexpected.append(
                    {"id": identifier, "reason": "failure is not reconciled"}
                )
                continue
            expected_kind = expectation.get("kind", "failure")
            message_contains = expectation.get("message_contains", "")
            observed_text = detail["message"] + "\n" + detail["body"]
            if detail["kind"] != expected_kind:
                unexpected.append(
                    {
                        "id": identifier,
                        "reason": (
                            f"expected kind {expected_kind}, observed {detail['kind']}"
                        ),
                    }
                )
                continue
            if message_contains and message_contains not in observed_text:
                unexpected.append(
                    {
                        "id": identifier,
                        "reason": (
                            "failure signature changed; expected substring "
                            + repr(message_contains)
                        ),
                    }
                )
                continue
            if identifier in matched:
                unexpected.append(
                    {"id": identifier, "reason": "duplicate observed failure id"}
                )
                continue
            matched.add(identifier)

    missing = sorted(set(relevant) - matched)
    status = "passed" if not unexpected and not missing else "failed"
    return {
        "status": status,
        "expected_failures": len(relevant),
        "matched_failures": len(matched),
        "unexpected_failures": unexpected,
        "missing_expected_failures": missing,
    }


def ensure_pytest_available(project_root: Path) -> bool:
    """Return True when pytest is available in the current interpreter."""
    if importlib.util.find_spec("pytest") is not None:
        return True

    requirements = project_root / "requirements-dev.txt"
    print(
        f"pytest is not installed in the selected Python environment: {sys.executable}",
        file=sys.stderr,
    )
    print("Install the development dependencies with:", file=sys.stderr)
    print(
        f'  "{sys.executable}" -m pip install -r "{requirements}"',
        file=sys.stderr,
    )
    return False


def select_files(manifest: dict, group: str, requested: list[str]) -> list[dict]:
    files = manifest["files"]
    if requested:
        wanted = {Path(name).name for name in requested}
        selected = [item for item in files if Path(item["path"]).name in wanted]
        missing = sorted(wanted - {Path(item["path"]).name for item in selected})
        if missing:
            raise ValueError("Unknown legacy test file(s): " + ", ".join(missing))
        return selected
    if group == "all":
        return files
    return [item for item in files if item["group"] == group]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("non-qt", "qt", "all"), default="non-qt")
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="Run one legacy test file; repeatable.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Report directory. Defaults to the OS temp directory.",
    )
    parser.add_argument(
        "--list", action="store_true", help="List selected files without running them."
    )
    parser.add_argument(
        "--maxfail",
        type=int,
        default=0,
        help="Pass pytest --maxfail for each file; 0 means unlimited.",
    )
    parser.add_argument(
        "--pytest-arg",
        action="append",
        default=[],
        help="Additional argument passed to pytest; repeatable.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Maximum runtime for each test file.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    legacy_root, manifest = load_manifest(project_root)
    reconciliation_path, expectations = load_reconciliation(legacy_root)

    integrity_errors = verify_integrity(legacy_root, manifest)
    if integrity_errors:
        print("Legacy test integrity check failed:", file=sys.stderr)
        for error in integrity_errors:
            print(f"  - {error}", file=sys.stderr)
        return 3

    selected = select_files(manifest, args.group, args.file)
    if args.list:
        for item in selected:
            print(f"{item['group']:6} {item['test_count']:3} {item['path']}")
        return 0

    if not ensure_pytest_available(project_root):
        return 4

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (
        args.output
        or Path(tempfile.gettempdir()) / "neoeng-d-trace-legacy-tests" / timestamp
    )
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(project_root) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    results = []
    for item in selected:
        filename = Path(item["path"]).name
        source = legacy_root / item["path"]
        stem = Path(filename).stem
        junit_path = output / f"{stem}.xml"
        log_path = output / f"{stem}.txt"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(legacy_root / "pytest.ini"),
            str(source),
            "-q",
            f"--junitxml={junit_path}",
        ]
        if args.maxfail > 0:
            command.append(f"--maxfail={args.maxfail}")
        command.extend(args.pytest_arg)

        timed_out = False
        try:
            proc = subprocess.run(
                command,
                cwd=project_root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=args.timeout_seconds,
            )
            output_text = proc.stdout
            returncode = proc.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            output_text = captured + f"\nTIMEOUT after {args.timeout_seconds} seconds\n"
            returncode = 124
        log_path.write_text(output_text, encoding="utf-8", errors="replace")
        metrics = parse_junit(junit_path)
        status = "passed"
        if returncode != 0 or metrics["failures"] or metrics["errors"]:
            status = "timeout" if timed_out else "failed"
        results.append(
            {
                "file": filename,
                "group": item["group"],
                "declared_test_count": item["test_count"],
                "returncode": returncode,
                "status": status,
                "timed_out": timed_out,
                "junit": str(junit_path),
                "log": str(log_path),
                **metrics,
            }
        )
        print(
            f"[{status.upper():6}] {filename}: tests={metrics['tests']} "
            f"failures={metrics['failures']} errors={metrics['errors']} "
            f"skipped={metrics['skipped']}"
        )

    reconciliation = reconcile_failures(selected, results, expectations)
    summary = {
        "schema_version": 3,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "python": sys.version,
        "platform": platform.platform(),
        "group": args.group,
        "integrity": "passed",
        "tested_commit": resolve_tested_commit(project_root),
        "working_tree_dirty": working_tree_is_dirty(project_root),
        "legacy_source_commit": manifest["source_commit"],
        "reconciliation_manifest": str(reconciliation_path),
        "reconciliation": reconciliation,
        "selected_files": len(selected),
        "totals": {
            "tests": sum(item["tests"] for item in results),
            "failures": sum(item["failures"] for item in results),
            "errors": sum(item["errors"] for item in results),
            "skipped": sum(item["skipped"] for item in results),
            "failed_files": sum(item["status"] != "passed" for item in results),
        },
        "results": results,
    }
    summary_path = output / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "Reconciliation: "
        f"{reconciliation['status']} "
        f"matched={reconciliation['matched_failures']}/"
        f"{reconciliation['expected_failures']} "
        f"unexpected={len(reconciliation['unexpected_failures'])} "
        f"missing={len(reconciliation['missing_expected_failures'])}"
    )
    print(f"Report: {summary_path}")
    return 0 if reconciliation["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
