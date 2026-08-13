from __future__ import annotations

import hashlib
import io
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = (b"co" + b"dex", b"open" + b"ai")
LOCAL_USER_PATHS = (
    re.compile(rb"[a-z]:[\\/]+" + b"users" + rb"[\\/]+", re.IGNORECASE),
    re.compile(rb"/" + b"Users" + rb"/", re.IGNORECASE),
)
MAX_ARCHIVE_DEPTH = 8
SANITIZED_ARCHIVES = {
    "NeoEng-D-Trace_Etapa2_PostMerge_Main_20260731_132248.zip": (
        "5356fcfc5bbbe0597f1103e4f063ae7aa5d9474911dba9fc7ae7aac090374069",
        393802,
    ),
    "NeoEng-D-Trace_Etapa2_Raw_Evidence_Bundle.zip": (
        "b8cb15a9f199cf9428ba9ebedebe360444905882c35902d471df5690d7a78f49",
        339676,
    ),
    "NeoEng-D-Trace_Etapa3_Pacote1_PostMerge_Main_20260731_232857.zip": (
        "a057fa82620cd0f7a5d8644a615adc65f923a0db36d71caacbf2a6dd41e54396",
        2547724,
    ),
    "NeoEng-D-Trace_Etapa3_Pacote1_Raw_Evidence_Bundle.zip": (
        "e082e552c015dd7fd742e8a05a27e454c2db6b63feea052ba162c9e31e2dfe28",
        1756194,
    ),
}


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def _scan_payload(label: str, data: bytes, depth: int = 0) -> list[str]:
    violations = []
    lowered = data.lower()
    if any(term in lowered for term in FORBIDDEN_TERMS):
        violations.append(f"{label}: forbidden product/provider reference")
    if any(pattern.search(data) for pattern in LOCAL_USER_PATHS):
        violations.append(f"{label}: local user path")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        return violations
    if depth >= MAX_ARCHIVE_DEPTH:
        violations.append(f"{label}: archive nesting exceeds scan limit")
        return violations
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = {
            entry.filename: archive.read(entry)
            for entry in archive.infolist()
            if not entry.is_dir()
        }
        for name, payload in entries.items():
            if not name.endswith("SHA256SUMS.txt"):
                continue
            for line in payload.decode("utf-8").splitlines():
                digest, separator, target = line.partition("  ")
                if separator and target in entries:
                    actual = hashlib.sha256(entries[target]).hexdigest()
                    if actual.lower() != digest.lower():
                        violations.append(
                            f"{label}!{name}: checksum mismatch for {target}"
                        )
        for entry in archive.infolist():
            if not entry.is_dir():
                violations.extend(
                    _scan_payload(
                        f"{label}!{entry.filename}", entries[entry.filename], depth + 1
                    )
                )
    return violations


def test_tracked_files_and_nested_archives_have_no_prohibited_references() -> None:
    violations = []
    for path in _tracked_files():
        violations.extend(
            _scan_payload(path.relative_to(ROOT).as_posix(), path.read_bytes())
        )

    assert violations == []


def test_sanitized_archive_hash_chain_matches_repository() -> None:
    record_path = (
        ROOT / "docs" / "evidence" / "SANITIZACAO_PACOTES_HISTORICOS_2026-08-11.md"
    )
    record = record_path.read_text(encoding="utf-8")
    other_evidence = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "docs").rglob("*")
        if path.is_file() and path != record_path and path.suffix in {".md", ".json"}
    )
    assert "SHA-256 anterior" in record
    for filename, (sanitized, expected_size) in SANITIZED_ARCHIVES.items():
        archive = ROOT / "docs" / "evidence" / "raw" / filename
        assert archive.stat().st_size == expected_size
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == sanitized
        assert str(expected_size) in record
        assert sanitized in record
        assert sanitized in other_evidence
