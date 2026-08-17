from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_native_stage10 import (
    sanitize_output,
    sanitize_structure,
    snapshot_tree,
    write_artifacts,
)


def test_snapshot_tree_ignores_engine_meta_and_normalizes_guids(tmp_path: Path) -> None:
    root = tmp_path / "generated"
    root.mkdir()
    (root / "scene.tscn").write_bytes(
        b"guid=" + b"a" * 32 + b"\r\nfileID: 123\n--- !u!1 &123\n"
    )
    (root / "scene.tscn.meta").write_text("volatile", encoding="utf-8")
    first = snapshot_tree(root)
    (root / "scene.tscn").write_bytes(
        b"guid=" + b"b" * 32 + b"\nfileID: 456\n--- !u!1 &456\n"
    )
    assert snapshot_tree(root) == first
    assert list(first) == ["scene.tscn"]


def test_snapshot_tree_detects_real_generated_change(tmp_path: Path) -> None:
    root = tmp_path / "generated"
    root.mkdir()
    target = root / "scene.tscn"
    target.write_text("z_index = 1\n", encoding="utf-8")
    first = snapshot_tree(root)
    target.write_text("z_index = 2\n", encoding="utf-8")
    assert snapshot_tree(root) != first


def test_stage10_artifact_writer_is_fail_closed_and_indexes_payloads(
    tmp_path: Path,
) -> None:
    output = tmp_path / "evidence"
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    (temporary / "sample.log").write_text("ENGINE=PASS\n", encoding="utf-8")
    report = {
        "schema_version": 1,
        "stage": 10,
        "status": "SUCCESS",
        "engines": {
            "godot": {"fixtures": {}},
            "unity": {"fixtures": {}},
        },
    }
    write_artifacts(output, report, temporary)
    index = json.loads((output / "stage10-index.json").read_text(encoding="utf-8"))
    assert index["status"] == "SUCCESS"
    assert "sample.log" in index["files"]
    with pytest.raises(RuntimeError, match="already exists"):
        write_artifacts(output, report, temporary)


def test_stage10_audit_keeps_release_decision_explicitly_unapproved() -> None:
    source = Path("scripts/audit_native_stage10.py").read_text(encoding="utf-8")
    assert '"release_approved": False' in source
    assert "RELEASE_APPROVED=NO" in source


def test_stage10_sanitizes_nested_engine_report(tmp_path: Path) -> None:
    result = sanitize_structure(
        {"output": "process Id: 7777 WindowsEditor(7,Atnco)"}, tmp_path
    )
    assert "process Id: 7777" not in result["output"]
    assert "WindowsEditor(7,Atnco)" not in result["output"]


def test_stage10_sanitizes_engine_identity_and_local_output(tmp_path: Path) -> None:
    raw = (
        "C:\\private\\artifact\\project\\file\n"
        "LicenseClient-test-user PId: 1234\n"
        "process Id: 5678 WindowsEditor(7,Atnco)\n"
        "Machine Id: secret\n"
        "http://localhost:8080\n"
    )
    sanitized = sanitize_output(raw, tmp_path)
    assert "C:\\private" not in sanitized
    assert "LicenseClient-test-user" not in sanitized
    assert "PId: 1234" not in sanitized
    assert "Machine Id: secret" not in sanitized
    assert "localhost:8080" not in sanitized
