from __future__ import annotations

import hashlib
import io
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = (b"co" + b"dex", b"open" + b"ai")
LOCAL_USER_PATH = re.compile(rb"[a-z]:[\\/]" + b"users" + rb"[\\/]", re.IGNORECASE)
MAX_ARCHIVE_DEPTH = 8
SANITIZED_ARCHIVES = {
    "NeoEng-D-Trace_Etapa2_PostMerge_Main_20260731_132248.zip": (
        "3aed50811c30d5f49ed7d53695d9e04a73cbac6135121128ff1ac0519a288ffc",
        393672,
    ),
    "NeoEng-D-Trace_Etapa2_Raw_Evidence_Bundle.zip": (
        "37fbff9bc0e07faa60c3c64e0735f7c7466b248875314833fcb446c3e162d7c8",
        339557,
    ),
    "NeoEng-D-Trace_Etapa3_Pacote1_PostMerge_Main_20260731_232857.zip": (
        "29fa47466b23b426e94dc919e5239fce7143bf73b78c93121890a16b6aa2e270",
        2546619,
    ),
    "NeoEng-D-Trace_Etapa3_Pacote1_Raw_Evidence_Bundle.zip": (
        "22cbc2d80e5116ef991bdb91b4fc99891d9730db43b05735c408c76f018cbb8b",
        1755602,
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
    if LOCAL_USER_PATH.search(data):
        violations.append(f"{label}: local user path")
    if depth >= MAX_ARCHIVE_DEPTH or not zipfile.is_zipfile(io.BytesIO(data)):
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
