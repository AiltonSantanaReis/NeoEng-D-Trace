#!/usr/bin/env python3
"""Generate or verify the NeoEng-D-Trace source baseline manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "baseline_manifest.json"
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "build",
    "dist",
}
IGNORED_FILES = {
    MANIFEST_PATH.name,
    ".coverage",
    "coverage.xml",
    "config.json",
    "config.json.corrupted",
    "project_context.txt",
    "report_api_locations.json",
    "tests_compat_report.json",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".backup", ".tmp", ".rar"}
FORBIDDEN_TOP_LEVEL_DIRS = {"backup", "backups", ".venv", "venv", "env"}


def iter_source_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if relative.name in IGNORED_FILES:
            continue
        yield path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest() -> dict[str, object]:
    files = {
        path.relative_to(ROOT).as_posix(): {
            "sha256": sha256(path),
            "size": path.stat().st_size,
        }
        for path in iter_source_files()
    }
    return {
        "schema_version": 1,
        "project": "NeoEng-D-Trace",
        "baseline_date": "2026-07-29",
        "hash_algorithm": "sha256",
        "files": files,
    }


def find_forbidden_paths() -> list[str]:
    problems: list[str] = []
    for name in sorted(FORBIDDEN_TOP_LEVEL_DIRS):
        if (ROOT / name).exists():
            problems.append(name)
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            problems.append(relative.as_posix())
    return sorted(set(problems))


def write_manifest() -> int:
    forbidden = find_forbidden_paths()
    if forbidden:
        print("Refusing to create a baseline with forbidden paths:")
        for item in forbidden:
            print(f"  - {item}")
        return 2
    MANIFEST_PATH.write_text(
        json.dumps(build_manifest(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {MANIFEST_PATH.relative_to(ROOT)}")
    return 0


def verify_manifest() -> int:
    if not MANIFEST_PATH.is_file():
        print("baseline_manifest.json is missing")
        return 2
    forbidden = find_forbidden_paths()
    expected = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    actual = build_manifest()
    expected_files = expected.get("files", {})
    actual_files = actual["files"]
    if forbidden or expected_files != actual_files:
        if forbidden:
            print("Forbidden paths detected:")
            for item in forbidden:
                print(f"  - {item}")
        expected_keys = set(expected_files)
        actual_keys = set(actual_files)
        for item in sorted(expected_keys - actual_keys):
            print(f"Missing: {item}")
        for item in sorted(actual_keys - expected_keys):
            print(f"Unexpected: {item}")
        for item in sorted(expected_keys & actual_keys):
            if expected_files[item] != actual_files[item]:
                print(f"Changed: {item}")
        return 1
    print(f"Baseline verified: {len(actual_files)} files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    return write_manifest() if args.write else verify_manifest()


if __name__ == "__main__":
    raise SystemExit(main())
