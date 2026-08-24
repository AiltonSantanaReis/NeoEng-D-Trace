from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.validate_snapshot_chain import validate


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_root_snapshot_requires_no_parent_and_validates_hashes(tmp_path: Path) -> None:
    final_target = tmp_path / "final-target.json"
    final_target.write_text('{"baseline": 1}\n', encoding="utf-8")
    report = tmp_path / "stage0-report.json"
    report.write_text(
        json.dumps({"baseline_id": "FINAL_TARGET", "parent_snapshot_id": None}),
        encoding="utf-8",
    )
    inventory = tmp_path / "stage0-inventory.json"
    inventory.write_text('{"files": 1}\n', encoding="utf-8")
    artifact = tmp_path / "capture.png"
    artifact.write_bytes(b"png-placeholder")
    manifest = tmp_path / "stage0-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "snapshot_id": "STAGE_0_SNAPSHOT:abc123",
                "parent_snapshot_id": None,
                "final_target_manifest_sha256": _sha(final_target),
                "stage0_report": {"path": report.name, "sha256": _sha(report)},
                "inventory": {"path": inventory.name, "sha256": _sha(inventory)},
                "artifacts": [{"path": artifact.name, "sha256": _sha(artifact)}],
            }
        ),
        encoding="utf-8",
    )

    assert validate(manifest, final_target) == []


def test_root_snapshot_rejects_parent(tmp_path: Path) -> None:
    final_target = tmp_path / "final-target.json"
    final_target.write_text("{}", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps({"baseline_id": "FINAL_TARGET", "parent_snapshot_id": "unexpected"}),
        encoding="utf-8",
    )
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "snapshot_id": "STAGE_0_SNAPSHOT:abc123",
                "parent_snapshot_id": "unexpected",
                "final_target_manifest_sha256": _sha(final_target),
                "stage0_report": {"path": report.name, "sha256": _sha(report)},
                "inventory": {"path": inventory.name, "sha256": _sha(inventory)},
                "artifacts": [],
            }
        ),
        encoding="utf-8",
    )

    errors = validate(manifest, final_target)
    assert any("não pode possuir pai" in error for error in errors)
