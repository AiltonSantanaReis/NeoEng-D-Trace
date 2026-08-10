#!/usr/bin/env python3
"""Generate or verify the NeoEng-D-Trace source baseline manifest.

Text files that are valid UTF-8 are hashed with canonical LF line endings so
that the same Git content produces the same manifest on Windows and Linux.
Binary files are hashed byte-for-byte without transformation.

When Git is available, the manifest covers tracked files plus new unignored
files. Local ignored content such as ``.venv`` and caches is excluded, while
forbidden content already tracked by Git remains a hard failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

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


def _git_paths(arguments: Sequence[str]) -> list[Path] | None:
    """Return repository-relative paths from ``git ls-files``.

    ``None`` means Git is unavailable or ``ROOT`` is not a Git work tree. An
    empty list is a valid result and must not trigger the filesystem fallback.
    """

    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", *arguments],
            check=False,
            capture_output=True,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    paths: list[Path] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        paths.append(Path(os.fsdecode(raw_path)))
    return paths


def _is_ignored(relative: Path) -> bool:
    return (
        any(part in IGNORED_DIRS for part in relative.parts)
        or relative.name in IGNORED_FILES
    )


def _filesystem_source_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if _is_ignored(relative):
            continue
        yield path


def iter_source_files() -> Iterable[Path]:
    """Yield files relevant to the repository integrity contract."""

    repository_paths = _git_paths(("--cached", "--others", "--exclude-standard"))
    if repository_paths is None:
        yield from _filesystem_source_files()
        return

    for relative in sorted(set(repository_paths), key=lambda item: item.as_posix()):
        if _is_ignored(relative):
            continue
        path = ROOT / relative
        if path.is_file():
            yield path


def canonical_bytes(path: Path) -> bytes:
    """Return deterministic bytes for hashing on every supported platform."""

    raw = path.read_bytes()
    if b"\x00" in raw:
        return raw

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_manifest() -> dict[str, object]:
    files: dict[str, dict[str, object]] = {}
    for path in iter_source_files():
        content = canonical_bytes(path)
        files[path.relative_to(ROOT).as_posix()] = {
            "sha256": sha256_bytes(content),
            "size": len(content),
        }

    return {
        "schema_version": 2,
        "project": "NeoEng-D-Trace",
        "baseline_date": date.today().isoformat(),
        "hash_algorithm": "sha256",
        "canonicalization": {
            "utf8_text_line_endings": "LF",
            "binary_files": "raw",
        },
        "files": files,
    }


def _is_forbidden(relative: Path) -> bool:
    top_level = relative.parts[0] if relative.parts else ""
    return (
        top_level in FORBIDDEN_TOP_LEVEL_DIRS
        or relative.suffix.lower() in FORBIDDEN_SUFFIXES
    )


def find_forbidden_paths() -> list[str]:
    """Return forbidden paths that are part of the tracked source tree.

    Ignored local directories are intentionally allowed. If Git metadata is
    unavailable, a conservative filesystem scan is used while still excluding
    normal local development directories such as ``.venv``.
    """

    tracked_paths = _git_paths(("--cached",))
    if tracked_paths is not None:
        return sorted(
            relative.as_posix()
            for relative in set(tracked_paths)
            if _is_forbidden(relative)
        )

    problems: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if _is_forbidden(relative):
            problems.append(relative.as_posix())
    return sorted(set(problems))


def write_manifest() -> int:
    forbidden = find_forbidden_paths()
    if forbidden:
        print("Refusing to create a baseline with forbidden tracked paths:")
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
    expected_metadata = {
        key: value for key, value in expected.items() if key != "files"
    }
    actual_metadata = {key: value for key, value in actual.items() if key != "files"}

    if forbidden or expected != actual:
        if forbidden:
            print("Forbidden tracked paths detected:")
            for item in forbidden:
                print(f"  - {item}")
        if expected_metadata != actual_metadata:
            print("Manifest metadata differs from the current integrity contract")
            print(f"Expected metadata: {expected_metadata}")
            print(f"Actual metadata:   {actual_metadata}")
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
