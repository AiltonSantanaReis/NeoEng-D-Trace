#!/usr/bin/env python3
"""Run the complete test suite in isolated subprocesses with one coverage set.

Windows/PySide6 can abort inside a long-lived pytest process after several Qt
modules have run under coverage.  This runner keeps the official test set and
coverage policy unchanged while giving every top-level test file a fresh
Python/Qt process.  It is fail-closed: a failed, timed-out, or aborted shard
prevents the final coverage report and returns a non-zero status.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]


def discover_test_files(project_root: Path = ROOT) -> list[Path]:
    """Return every official top-level test file in deterministic order."""

    tests_root = project_root / "tests"
    return sorted(
        tests_root.glob("test_*.py"), key=lambda path: (path.name.casefold(), path.name)
    )


def parse_junit(path: Path) -> dict[str, Any]:
    """Read the metrics emitted by one pytest shard."""

    metrics: dict[str, Any] = {
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "time": 0.0,
        "junit_missing": False,
    }
    if not path.is_file():
        metrics["errors"] = 1
        metrics["junit_missing"] = True
        return metrics

    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    for suite in suites:
        metrics["tests"] += int(suite.attrib.get("tests", 0))
        metrics["failures"] += int(suite.attrib.get("failures", 0))
        metrics["errors"] += int(suite.attrib.get("errors", 0))
        metrics["skipped"] += int(suite.attrib.get("skipped", 0))
        metrics["time"] += float(suite.attrib.get("time", 0.0))
    return metrics


def build_pytest_command(
    python_executable: str,
    test_file: Path,
    junit_path: Path,
    *,
    append_coverage: bool,
    final_shard: bool,
    coverage_path: Path,
) -> list[str]:
    """Build the unfiltered command for one official test-file shard."""

    command = [
        python_executable,
        "-m",
        "pytest",
        str(test_file),
        "--cov=src",
        "--cov-branch",
        "--cov-report=",
        "-q",
        f"--junitxml={junit_path}",
    ]
    if append_coverage:
        command.append("--cov-append")
    if final_shard:
        command.extend(
            [
                "--cov-fail-under=90",
                "--cov-report=term-missing",
                f"--cov-report=xml:{coverage_path}",
            ]
        )
    return command


def resolve_external_output(requested: Path) -> Path:
    """Resolve an output directory that cannot pollute the source tree."""

    output = (requested if requested.is_absolute() else ROOT / requested).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        return output
    raise ValueError("Windows coverage output must be outside the project tree")


def resolve_tested_commit(project_root: Path = ROOT) -> str:
    """Resolve the exact Git revision being tested."""

    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    commit = process.stdout.strip().lower()
    if (
        process.returncode != 0
        or len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
    ):
        raise RuntimeError("Unable to resolve the tested Git commit")
    return commit


def _display_command(
    command: Sequence[str], project_root: Path, output: Path
) -> list[str]:
    """Remove local machine paths from the external summary."""

    project_text = str(project_root.resolve())
    output_text = str(output.resolve())
    return [
        value.replace(output_text, "<output>").replace(project_text, "<project>")
        for value in command
    ]


def _write_json_lf(path: Path, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes(payload.replace("\r\n", "\n").replace("\r", "\n").encode())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="External report directory"
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="Maximum runtime for each test-file shard",
    )
    args = parser.parse_args(argv)

    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    try:
        output = resolve_external_output(args.output)
        if output.exists() and not output.is_dir():
            raise ValueError("Windows coverage output must be a directory")
        if output.is_dir() and any(output.iterdir()):
            raise ValueError("Windows coverage output must be empty")
        output.mkdir(parents=True, exist_ok=True)
        junit_root = output / "junit"
        log_root = output / "logs"
        junit_root.mkdir()
        log_root.mkdir()
        test_files = discover_test_files()
        if not test_files:
            raise ValueError("No official test files were discovered")
        tested_commit = resolve_tested_commit()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Windows coverage shard setup failed: {exc}", file=sys.stderr)
        return 2

    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(ROOT) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")

    results: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, test_file in enumerate(test_files, start=1):
        stem = test_file.stem
        junit_path = junit_root / f"{index:03d}-{stem}.xml"
        log_path = log_root / f"{index:03d}-{stem}.log"
        coverage_path = output / "coverage.xml"
        command = build_pytest_command(
            sys.executable,
            test_file,
            junit_path,
            append_coverage=index > 1,
            final_shard=index == len(test_files),
            coverage_path=coverage_path,
        )
        shard_started = time.monotonic()
        timed_out = False
        try:
            process = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                timeout=args.timeout_seconds,
            )
            output_text = process.stdout
            returncode = process.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            output_text = captured + f"\nTIMEOUT after {args.timeout_seconds} seconds\n"
            returncode = 124
        except OSError as exc:
            output_text = f"Unable to start pytest shard: {exc}\n"
            returncode = 127

        log_path.write_bytes(
            output_text.replace("\r\n", "\n")
            .replace("\r", "\n")
            .encode("utf-8", errors="replace")
        )
        metrics = parse_junit(junit_path)
        status = "passed"
        if returncode != 0 or metrics["failures"] or metrics["errors"]:
            status = "timeout" if timed_out else "failed"
        result = {
            "index": index,
            "file": test_file.relative_to(ROOT).as_posix(),
            "returncode": returncode,
            "status": status,
            "timed_out": timed_out,
            "duration_seconds": round(time.monotonic() - shard_started, 3),
            "junit": junit_path.relative_to(output).as_posix(),
            "log": log_path.relative_to(output).as_posix(),
            "command": _display_command(command, ROOT, output),
            **metrics,
        }
        results.append(result)
        print(
            f"[{status.upper():7}] {index}/{len(test_files)} {test_file.name}: "
            f"tests={metrics['tests']} failures={metrics['failures']} "
            f"errors={metrics['errors']} skipped={metrics['skipped']}"
        )
        if status != "passed":
            break

    totals = {
        key: sum(int(result[key]) for result in results)
        for key in ("tests", "failures", "errors", "skipped")
    }
    coverage_path = output / "coverage.xml"
    accepted = (
        len(results) == len(test_files)
        and all(result["status"] == "passed" for result in results)
        and coverage_path.is_file()
    )
    summary = {
        "schema": "neoeng.windows.coverage-shards",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "tested_commit": tested_commit,
        "project_root": "<project>",
        "python": sys.version,
        "platform": platform.platform(),
        "runner": {
            "official_test_glob": "tests/test_*.py",
            "test_file_order": "casefold/name ascending",
            "subprocess_per_test_file": True,
            "coverage": "--cov=src --cov-branch --cov-append",
            "threshold": 90,
            "timeout_seconds": args.timeout_seconds,
            "selection_filters": [],
        },
        "expected_files": len(test_files),
        "completed_files": len(results),
        "totals": totals,
        "coverage_xml": "coverage.xml" if coverage_path.is_file() else None,
        "accepted": accepted,
        "duration_seconds": round(time.monotonic() - started, 3),
        "results": results,
    }
    _write_json_lf(output / "summary.json", summary)
    print(
        "Windows coverage shards: "
        f"{'ACCEPTED' if accepted else 'FAILED'}; "
        f"files={len(results)}/{len(test_files)}; "
        f"tests={totals['tests']}; failures={totals['failures']}; "
        f"errors={totals['errors']}; skipped={totals['skipped']}"
    )
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
