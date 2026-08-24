#!/usr/bin/env python3
"""Strict official evidence entry point with an explicit artifact allowlist.

Tracked source changes always block an official package. Existing untracked
outputs are accepted only when they match the documented evidence-output
patterns; untracked source, documentation or test files block the run.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts import collect_evidence_package_canonical as canonical


ALLOWED_UNTRACKED_PREFIXES = (
    "artifacts/",
    "coverage-",
    "release-",
    "stage",
)


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
        if len(line) < 4:
            violations.append(line)
            continue
        status = line[:2]
        path = line[3:].replace("\\", "/")
        if status != "??":
            violations.append(line)
            continue
        if not path.startswith(ALLOWED_UNTRACKED_PREFIXES):
            violations.append(line)
    return not violations, violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--official", action="store_true")
    known, _ = parser.parse_known_args(argv)
    workspace = known.workspace.resolve()
    if known.official:
        clean, violations = worktree_policy(workspace)
        if not clean:
            print(
                {
                    "status": "FAIL",
                    "error": "official evidence requires no tracked changes and only allowlisted untracked outputs",
                    "violations": violations,
                },
                file=sys.stderr,
            )
            return 2
    return canonical.collector.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
