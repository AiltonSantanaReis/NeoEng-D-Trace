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
                f"hash mismatch: {item['path']} expected={item['sha256_lf']} actual={digest}"
            )
    return errors


def parse_junit(path: Path) -> dict:
    result = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
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
    return result


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
            f"failures={metrics['failures']} errors={metrics['errors']} skipped={metrics['skipped']}"
        )

    summary = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "python": sys.version,
        "platform": platform.platform(),
        "group": args.group,
        "integrity": "passed",
        "source_commit": manifest["source_commit"],
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
    print(f"Report: {summary_path}")
    return 1 if summary["totals"]["failed_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
