from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stage7_native_adapters_keep_sync_contracts():
    godot = (
        ROOT
        / "integrations"
        / "godot"
        / "addons"
        / "neoeng_d_trace"
        / "import_generator.gd"
    ).read_text(encoding="utf-8")
    unity = (
        ROOT
        / "integrations"
        / "unity"
        / "package"
        / "com.neoeng.dtrace"
        / "Editor"
        / "UnityImportGenerator.cs"
    ).read_text(encoding="utf-8")

    for marker in (
        "_sha256_bytes",
        "_fingerprint",
        "_synchronize_generated",
        "_read_override",
        "_destructive_update_confirmed",
    ):
        assert marker in godot
    for marker in (
        "ApplyPolygonArrays",
        "InspectExistingPrefab",
        "SyncConflictException",
        "ConfirmDestructiveEnvironment",
        "MutateGeneratedPrefabFixture",
    ):
        assert marker in unity


def test_stage7_real_engine_evidence_is_successful_and_sanitized():
    godot = json.loads(
        (
            ROOT
            / "docs"
            / "evidence"
            / "artifacts"
            / "godot-sync-stage7-2026-08-16"
            / "stage7-report.json"
        ).read_text(encoding="utf-8")
    )
    unity = json.loads(
        (
            ROOT
            / "docs"
            / "evidence"
            / "artifacts"
            / "unity-sync-stage7-2026-08-16"
            / "stage7-report.json"
        ).read_text(encoding="utf-8")
    )
    for report in (godot, unity):
        assert report["status"] == "SUCCESS"
        assert all(report["scenarios"].values())
        serialized = json.dumps(report, ensure_ascii=False)
        local_path_marker = "C:" + ("\\" * 2) + "Users" + ("\\" * 2)
        assert local_path_marker not in serialized
        assert serialized.count("LicenseClient-") == serialized.count(
            "LicenseClient-<redacted>"
        )

    regression = json.loads(
        (
            ROOT
            / "docs"
            / "evidence"
            / "artifacts"
            / "godot-plugin-stage4-regression-2026-08-16.json"
        ).read_text(encoding="utf-8")
    )
    assert regression["status"] == "SUCCESS"
