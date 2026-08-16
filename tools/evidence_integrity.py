"""Validate and repair versioned evidence manifests.

Evidence digests are hashes of the bytes committed to the repository.  This
module deliberately does not normalize bytes while validating: a manifest
must describe the exact file that will be reviewed and checked out by CI.
Text normalization is only available through the explicit ``--rewrite``
repair command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "docs" / "evidence" / "artifacts"
TEXT_SUFFIXES = {
    ".cfg",
    ".cs",
    ".gd",
    ".json",
    ".md",
    ".ndtproj",
    ".res",
    ".tres",
    ".tscn",
    ".txt",
    ".log",
}
MANIFEST_NAMES = {
    "manifest.json",
    "artifact-index.json",
    "engine-validation-index.json",
}


@dataclass(frozen=True)
class ManifestEntry:
    manifest: Path
    target: Path
    record: dict[str, Any]
    label: str


@dataclass(frozen=True)
class Issue:
    manifest: Path
    message: str


def canonical_text_bytes(value: str) -> bytes:
    """Return UTF-8 text with the only supported line ending: LF."""

    return value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def write_text_lf(path: Path, value: str, *, encoding: str = "utf-8") -> None:
    """Write text with deterministic LF endings on every platform."""

    if encoding != "utf-8":
        path.write_bytes(
            value.replace("\r\n", "\n").replace("\r", "\n").encode(encoding)
        )
        return
    path.write_bytes(canonical_text_bytes(value))


def write_json_lf(path: Path, value: Any) -> None:
    """Serialize JSON deterministically with UTF-8 LF bytes."""

    write_text_lf(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest_bytes(raw: bytes) -> dict[str, Any]:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def digest_path(path: Path) -> dict[str, Any]:
    return digest_bytes(path.read_bytes())


def _repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _resolve_reference(manifest: Path, reference: str) -> Path:
    normalized = reference.replace("\\", "/")
    if normalized.startswith("docs/evidence/"):
        candidate = ROOT / normalized
    else:
        candidate = manifest.parent / normalized
    candidate = candidate.resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"reference escapes repository: {reference}") from exc
    return candidate


def _record_from_value(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _iter_map_entries(
    manifest: Path, value: Any, *, label_prefix: str
) -> Iterator[ManifestEntry]:
    if not isinstance(value, dict):
        return
    for name, record_value in value.items():
        record = _record_from_value(record_value)
        if record is None:
            continue
        yield ManifestEntry(
            manifest=manifest,
            target=_resolve_reference(manifest, str(name)),
            record=record,
            label=f"{label_prefix}.{name}",
        )


def _iter_list_entries(
    manifest: Path, value: Any, *, label_prefix: str
) -> Iterator[ManifestEntry]:
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        yield ManifestEntry(
            manifest=manifest,
            target=_resolve_reference(manifest, item["path"]),
            record=item,
            label=f"{label_prefix}[{index}]",
        )


def iter_manifest_entries(
    manifest: Path, data: dict[str, Any]
) -> Iterator[ManifestEntry]:
    """Extract all supported artifact references from known manifest shapes."""

    yield from _iter_map_entries(manifest, data.get("files"), label_prefix="files")
    yield from _iter_list_entries(manifest, data.get("files"), label_prefix="files")
    yield from _iter_map_entries(
        manifest, data.get("artifacts"), label_prefix="artifacts"
    )
    yield from _iter_list_entries(
        manifest, data.get("artifacts"), label_prefix="artifacts"
    )

    captures = data.get("captures")
    if isinstance(captures, dict):
        for capture_name, capture in captures.items():
            if not isinstance(capture, dict):
                continue
            yield from _iter_map_entries(
                manifest,
                capture.get("files"),
                label_prefix=f"captures.{capture_name}.files",
            )


def discover_manifests() -> list[Path]:
    return sorted(
        path
        for path in EVIDENCE_ROOT.rglob("*.json")
        if path.name in MANIFEST_NAMES or path.name.endswith("-index.json")
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest root must be an object")
    return value


def _tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", _repo_relative(path)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", _repo_relative(path)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _artifact_bytes(entry: ManifestEntry) -> tuple[bytes | None, Path | None]:
    """Read a file reference, or a member of a tracked evidence archive."""

    if entry.target.is_file():
        return entry.target.read_bytes(), entry.target
    for archive in sorted(entry.manifest.parent.glob("*.zip")):
        try:
            with zipfile.ZipFile(archive) as bundle:
                member_name = entry.target.relative_to(entry.manifest.parent).as_posix()
                if member_name in bundle.namelist():
                    return bundle.read(member_name), archive
        except (OSError, ValueError, zipfile.BadZipFile):
            continue
    return None, None


def validate_manifest(manifest: Path, *, require_tracked: bool) -> list[Issue]:
    issues: list[Issue] = []
    if _ignored(manifest):
        issues.append(Issue(manifest, "ignored manifest"))
    if require_tracked and not _tracked(manifest):
        issues.append(Issue(manifest, "untracked manifest"))
    try:
        data = _load_manifest(manifest)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [Issue(manifest, f"cannot load manifest: {exc}")]

    entries = list(iter_manifest_entries(manifest, data))
    seen: set[Path] = set()
    for entry in entries:
        if entry.target in seen:
            issues.append(Issue(manifest, f"duplicate reference: {entry.label}"))
            continue
        seen.add(entry.target)
        raw, tracked_source = _artifact_bytes(entry)
        if raw is None or tracked_source is None:
            issues.append(
                Issue(
                    manifest,
                    f"missing artifact: {entry.label} -> "
                    f"{_repo_relative(entry.target)}",
                )
            )
            continue
        if _ignored(tracked_source):
            issues.append(
                Issue(
                    manifest,
                    f"ignored artifact: {entry.label} -> "
                    f"{_repo_relative(tracked_source)}",
                )
            )
        if require_tracked and not _tracked(tracked_source):
            issues.append(
                Issue(
                    manifest,
                    f"untracked artifact: {entry.label} -> "
                    f"{_repo_relative(tracked_source)}",
                )
            )

        if entry.target.suffix.lower() in TEXT_SUFFIXES and b"\r" in raw:
            issues.append(
                Issue(
                    manifest,
                    f"non-canonical CRLF/CR bytes: {_repo_relative(tracked_source)}",
                )
            )
        actual = digest_bytes(raw)
        expected_hash = entry.record.get("sha256")
        expected_size = entry.record.get("bytes", entry.record.get("size"))
        if not isinstance(expected_hash, str):
            issues.append(Issue(manifest, f"missing sha256: {entry.label}"))
        elif expected_hash != actual["sha256"]:
            issues.append(Issue(manifest, f"sha256 mismatch: {entry.label}"))
        if not isinstance(expected_size, int):
            issues.append(Issue(manifest, f"missing byte size: {entry.label}"))
        elif expected_size != actual["bytes"]:
            issues.append(Issue(manifest, f"byte size mismatch: {entry.label}"))
    return issues


def _set_digest(record: dict[str, Any], digest: dict[str, Any]) -> None:
    record["bytes"] = digest["bytes"]
    record["sha256"] = digest["sha256"]
    if "size" in record:
        record["size"] = digest["bytes"]


def rewrite_manifests() -> list[Issue]:
    """Canonicalize referenced text and rewrite all supported digest records."""

    issues: list[Issue] = []
    manifests = discover_manifests()
    entries_by_manifest: dict[Path, list[ManifestEntry]] = {}
    for manifest in manifests:
        try:
            data = _load_manifest(manifest)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            issues.append(Issue(manifest, f"cannot load manifest: {exc}"))
            continue
        entries_by_manifest[manifest] = list(iter_manifest_entries(manifest, data))
        for entry in entries_by_manifest[manifest]:
            raw, source = _artifact_bytes(entry)
            if raw is None or source is None:
                issues.append(Issue(manifest, f"missing artifact: {entry.label}"))
                continue
            if source == entry.target and entry.target.suffix.lower() in TEXT_SUFFIXES:
                normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                if normalized != raw:
                    entry.target.write_bytes(normalized)
                    raw = normalized
            _set_digest(entry.record, digest_bytes(raw))

        if not any(issue.manifest == manifest for issue in issues):
            write_json_lf(manifest, data)
    return issues


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rewrite",
        action="store_true",
        help="canonicalize text and refresh manifest digests",
    )
    parser.add_argument(
        "--require-tracked",
        action="store_true",
        help="reject evidence that is not in the Git index; required in CI",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.rewrite:
        issues = rewrite_manifests()
        if issues:
            for issue in issues:
                print(f"ERROR {issue.manifest}: {issue.message}")
            return 1
    issues = [
        issue
        for manifest in discover_manifests()
        for issue in validate_manifest(manifest, require_tracked=args.require_tracked)
    ]
    if issues:
        for issue in issues:
            print(f"ERROR {issue.manifest}: {issue.message}")
        return 1
    print(
        f"Evidence integrity passed: {len(discover_manifests())} manifests validated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
