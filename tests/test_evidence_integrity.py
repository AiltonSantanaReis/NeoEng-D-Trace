"""Tests for the immutable evidence-byte contract."""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

from tools import evidence_integrity


def test_canonical_text_bytes_normalizes_all_supported_line_endings() -> None:
    assert evidence_integrity.canonical_text_bytes("a\r\nb\rc\n") == b"a\nb\nc\n"


def test_write_text_lf_never_emits_crlf(tmp_path: Path) -> None:
    target = tmp_path / "report.log"
    evidence_integrity.write_text_lf(target, "first\r\nsecond\rthird\n")
    assert target.read_bytes() == b"first\nsecond\nthird\n"


def test_manifest_entry_extraction_covers_supported_shapes(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(evidence_integrity, "ROOT", tmp_path)
    manifest = tmp_path / "manifest.json"
    data = {
        "files": {"one.json": {"sha256": "a", "bytes": 1}},
        "artifacts": [{"path": "two.log", "sha256": "b", "bytes": 2}],
        "captures": {"desktop": {"files": {"three.png": {"sha256": "c", "bytes": 3}}}},
    }
    entries = list(evidence_integrity.iter_manifest_entries(manifest, data))
    assert [entry.target.name for entry in entries] == [
        "one.json",
        "two.log",
        "three.png",
    ]


def test_validator_rejects_noncanonical_bytes_and_then_stale_hash(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(evidence_integrity, "ROOT", tmp_path)
    artifact = tmp_path / "artifact.log"
    artifact.write_bytes(b"line\r\n")
    manifest = tmp_path / "manifest.json"
    digest = evidence_integrity.digest_path(artifact)
    evidence_integrity.write_json_lf(manifest, {"files": {"artifact.log": digest}})

    issues = evidence_integrity.validate_manifest(manifest, require_tracked=False)
    assert any("non-canonical" in issue.message for issue in issues)
    assert not any("sha256 mismatch" in issue.message for issue in issues)

    artifact.write_bytes(b"line\n")
    issues = evidence_integrity.validate_manifest(manifest, require_tracked=False)
    assert any("sha256 mismatch" in issue.message for issue in issues)


def test_validator_blocks_untracked_references_when_required(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(evidence_integrity, "ROOT", tmp_path)
    artifact = tmp_path / "artifact.json"
    evidence_integrity.write_text_lf(artifact, "{}\n")
    manifest = tmp_path / "manifest.json"
    evidence_integrity.write_json_lf(
        manifest, {"files": {"artifact.json": evidence_integrity.digest_path(artifact)}}
    )
    monkeypatch.setattr(evidence_integrity, "_tracked", lambda path: False)
    monkeypatch.setattr(evidence_integrity, "_ignored", lambda path: False)

    issues = evidence_integrity.validate_manifest(manifest, require_tracked=True)
    assert any("untracked artifact" in issue.message for issue in issues)


def test_validator_reads_member_from_evidence_zip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(evidence_integrity, "ROOT", tmp_path)
    bundle = tmp_path / "bundle.zip"
    payload = b'{"ok": true}\n'
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("artifact.json", payload)
    manifest = tmp_path / "manifest.json"
    evidence_integrity.write_json_lf(
        manifest,
        {
            "files": {
                "artifact.json": evidence_integrity.digest_bytes(payload),
            }
        },
    )
    monkeypatch.setattr(evidence_integrity, "_tracked", lambda path: True)
    monkeypatch.setattr(evidence_integrity, "_ignored", lambda path: False)

    assert evidence_integrity.validate_manifest(manifest, require_tracked=True) == []


def test_git_blob_mode_validates_index_bytes_not_worktree_conversion(
    tmp_path: Path, monkeypatch
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Evidence Test"], cwd=tmp_path, check=True
    )
    artifact = tmp_path / "artifact.py"
    artifact.write_bytes(b"line\n")
    manifest = tmp_path / "manifest.json"
    evidence_integrity.write_json_lf(
        manifest, {"files": {"artifact.py": evidence_integrity.digest_path(artifact)}}
    )
    subprocess.run(
        ["git", "add", "artifact.py", "manifest.json"], cwd=tmp_path, check=True
    )
    artifact.write_bytes(b"line\r\n")
    monkeypatch.setattr(evidence_integrity, "ROOT", tmp_path)
    monkeypatch.setattr(evidence_integrity, "EVIDENCE_ROOT", tmp_path)

    assert (
        evidence_integrity.validate_manifest(
            manifest, require_tracked=True, use_git_blob=True
        )
        == []
    )
    worktree_issues = evidence_integrity.validate_manifest(
        manifest, require_tracked=True, use_git_blob=False
    )
    assert any("non-canonical" in issue.message for issue in worktree_issues)
    assert any("sha256 mismatch" in issue.message for issue in worktree_issues)


def test_ci_requires_strict_evidence_gate_in_both_jobs() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert (
        workflow.count(
            "python tools/evidence_integrity.py --require-tracked --git-blob"
        )
        == 2
    )
    attributes = (root / ".gitattributes").read_text(encoding="utf-8")
    assert "/docs/evidence/** text eol=lf" in attributes
    assert "*.py text eol=lf" in attributes
