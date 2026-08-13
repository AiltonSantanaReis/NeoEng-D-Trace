from __future__ import annotations

import hashlib
import io
import json
import zipfile

from tools.sanitize_evidence_archives import sanitize_archive


def _archive(entries: dict[str, bytes]) -> bytes:
    checksums = "".join(
        f"{hashlib.sha256(payload).hexdigest()}  {name}\n"
        for name, payload in entries.items()
    ).encode("utf-8")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
        archive.writestr("SHA256SUMS.txt", checksums)
    return output.getvalue()


def _assert_checksums(data: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }
    for line in entries["SHA256SUMS.txt"].decode("utf-8").splitlines():
        digest, separator, target = line.partition("  ")
        assert separator
        assert hashlib.sha256(entries[target]).hexdigest() == digest
    for name, payload in entries.items():
        if name.endswith(".zip"):
            _assert_checksums(payload)


def test_nested_archive_sanitization_is_atomic_complete_and_idempotent(tmp_path):
    payload = json.dumps(
        {
            "windows": "C:" + r"\Users\private-user\workspace\result.json",
            "mac": "/" + "Users/private-user/workspace/result.json",
        }
    ).encode("utf-8")
    inner = _archive({"result.json": payload})
    target = tmp_path / "evidence.zip"
    target.write_bytes(_archive({"nested.zip": inner}))
    original = target.read_bytes()

    changed, stats, old_hash, new_hash = sanitize_archive(target, write=False)

    assert changed is True
    assert stats.replacements == 2
    assert old_hash != new_hash
    assert target.read_bytes() == original

    changed, stats, _, written_hash = sanitize_archive(target, write=True)

    assert changed is True
    assert stats.archives_rewritten == 2
    assert stats.checksums_updated == 2
    assert hashlib.sha256(target.read_bytes()).hexdigest() == written_hash
    assert b"private-user" not in target.read_bytes()
    _assert_checksums(target.read_bytes())

    changed, stats, stable_hash, repeated_hash = sanitize_archive(target, write=False)

    assert changed is False
    assert stats.replacements == 0
    assert stable_hash == repeated_hash == written_hash
