from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

LOCAL_PLACEHOLDER = b"[LOCAL_PATH_REMOVED]"
WINDOWS_USER_HOME = re.compile(
    rb"[a-z]:[\\/]+" + b"users" + rb"[\\/]+[^\\/\s\"']+",
    re.IGNORECASE,
)
MAC_USER_HOME = re.compile(rb"/" + b"Users" + rb"/[^/\s\"']+", re.IGNORECASE)
MAX_ARCHIVE_DEPTH = 16


@dataclass
class RewriteStats:
    replacements: int = 0
    archives_rewritten: int = 0
    checksums_updated: int = 0

    def include(self, other: RewriteStats) -> None:
        self.replacements += other.replacements
        self.archives_rewritten += other.archives_rewritten
        self.checksums_updated += other.checksums_updated


def _sanitize_bytes(data: bytes) -> tuple[bytes, int]:
    updated, windows_count = WINDOWS_USER_HOME.subn(LOCAL_PLACEHOLDER, data)
    updated, mac_count = MAC_USER_HOME.subn(LOCAL_PLACEHOLDER, updated)
    return updated, windows_count + mac_count


def _update_checksum_manifest(
    data: bytes, entries: dict[str, bytes]
) -> tuple[bytes, int]:
    changed = 0
    output = []
    for line in data.splitlines(keepends=True):
        body = line.rstrip(b"\r\n")
        ending = line[len(body) :]
        digest, separator, target = body.partition(b"  ")
        if separator:
            target_name = target.decode("utf-8")
            if target_name in entries:
                actual = (
                    hashlib.sha256(entries[target_name]).hexdigest().encode("ascii")
                )
                if digest.lower() != actual:
                    digest = actual
                    changed += 1
                line = digest + separator + target + ending
        output.append(line)
    return b"".join(output), changed


def _rewrite_payload(data: bytes, depth: int = 0) -> tuple[bytes, RewriteStats]:
    if depth > MAX_ARCHIVE_DEPTH:
        raise ValueError(f"archive nesting exceeds {MAX_ARCHIVE_DEPTH}")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        sanitized, replacements = _sanitize_bytes(data)
        return sanitized, RewriteStats(replacements=replacements)

    with zipfile.ZipFile(io.BytesIO(data)) as source:
        infos = source.infolist()
        original_entries = {
            info.filename: source.read(info) for info in infos if not info.is_dir()
        }

    stats = RewriteStats()
    entries: dict[str, bytes] = {}
    changed = False
    for info in infos:
        if info.is_dir():
            continue
        original = original_entries[info.filename]
        rewritten, child_stats = _rewrite_payload(original, depth + 1)
        entries[info.filename] = rewritten
        stats.include(child_stats)
        changed = changed or rewritten != original

    for info in infos:
        if info.is_dir() or not info.filename.endswith("SHA256SUMS.txt"):
            continue
        rewritten, checksum_count = _update_checksum_manifest(
            entries[info.filename], entries
        )
        entries[info.filename] = rewritten
        stats.checksums_updated += checksum_count
        changed = changed or rewritten != original_entries[info.filename]

    if not changed:
        return data, stats

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as destination:
        for info in infos:
            if info.is_dir():
                destination.writestr(info, b"")
            else:
                destination.writestr(info, entries[info.filename])
    stats.archives_rewritten += 1
    return output.getvalue(), stats


def sanitize_archive(path: Path, write: bool) -> tuple[bool, RewriteStats, str, str]:
    original = path.read_bytes()
    rewritten, stats = _rewrite_payload(original)
    changed = rewritten != original
    old_hash = hashlib.sha256(original).hexdigest()
    new_hash = hashlib.sha256(rewritten).hexdigest()
    if changed and write:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(rewritten)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
    return changed, stats, old_hash, new_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    pending = False
    for archive in args.archives:
        changed, stats, old_hash, new_hash = sanitize_archive(archive, args.write)
        pending = pending or changed
        print(
            f"{archive}: changed={changed} replacements={stats.replacements} "
            f"archives={stats.archives_rewritten} checksums={stats.checksums_updated} "
            f"old_sha256={old_hash} new_sha256={new_hash}"
        )
    return 0 if args.write or not pending else 1


if __name__ == "__main__":
    raise SystemExit(main())
