#!/usr/bin/env python3
"""Strict official evidence package entry point with generic measurements.

The governance gate measures pipeline/test operations, not renderer frames.
This entry point accepts ``samples_ms`` for generic operations and preserves
``frame_time_ms`` for renderer-specific phases.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts import collect_evidence_package as collector


collector.PHASE_PATTERN = re.compile(r"^F[0-9]+$", re.IGNORECASE)

ALLOWED_UNTRACKED_PREFIXES = ("artifacts/", "coverage-", "release-", "stage")


def worktree_policy(workspace: Path) -> tuple[bool, list[str]]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    violations: list[str] = []
    for line in result.stdout.splitlines():
        status = line[:2]
        path = line[3:].replace("\\", "/") if len(line) >= 4 else line
        if status != "??" or not path.startswith(ALLOWED_UNTRACKED_PREFIXES):
            violations.append(line)
    return not violations, violations


def validate_measurement(path: Path) -> dict[str, Any]:
    payload = collector.load_json(path, "performance")
    key = "samples_ms" if "samples_ms" in payload else "frame_time_ms"
    raw_samples = payload.get(key)
    if not isinstance(raw_samples, list) or not raw_samples:
        raise collector.EvidenceError(f"performance.{key} must contain samples")
    samples = [float(item) for item in raw_samples]
    if not all(item >= 0 for item in samples):
        raise collector.EvidenceError("performance samples must be non-negative")
    minimum_samples = int(payload.get("minimum_samples", 1))
    if len(samples) < minimum_samples:
        raise collector.EvidenceError("insufficient performance samples")
    return {
        "measurement": payload.get("measurement", "frame_time_ms" if key == "frame_time_ms" else "generic_operation"),
        "sample_key": key,
        "sample_count": len(samples),
        "p50_ms": collector.percentile(samples, 0.50),
        "p95_ms": collector.percentile(samples, 0.95),
        "p99_ms": collector.percentile(samples, 0.99),
        "worst_ms": max(samples),
        "minimum_samples": minimum_samples,
        "backend": payload.get("backend", "NOT_APPLICABLE"),
        "hardware": payload.get("hardware", "NOT_APPLICABLE"),
    }


collector.validate_performance = validate_measurement


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--official", action="store_true")
    known, _ = parser.parse_known_args(argv)
    if known.official:
        clean, violations = worktree_policy(known.workspace.resolve())
        if not clean:
            print(
                json.dumps(
                    {
                        "status": "FAIL",
                        "error": "official evidence requires no tracked changes and only allowlisted untracked outputs",
                        "violations": violations,
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2
    return collector.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
