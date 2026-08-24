#!/usr/bin/env python3
"""Strict official entry point for evidence collection.

This wrapper refuses dirty worktrees and delegates the package format to the
canonical collector. There is deliberately no force or bypass option.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts import collect_evidence_package_canonical as canonical


def clean_worktree(workspace: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--official", action="store_true")
    known, _ = parser.parse_known_args(argv)
    workspace = known.workspace.resolve()
    if known.official and not clean_worktree(workspace):
        print(
            '{"status":"FAIL","error":"official evidence requires a clean worktree"}',
            file=sys.stderr,
        )
        return 2
    return canonical.collector.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
