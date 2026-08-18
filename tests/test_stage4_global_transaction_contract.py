from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT_IMPORTER = ROOT / "integrations/godot/addons/neoeng_d_trace/import_generator.gd"
UNITY_IMPORTER = (
    ROOT / "integrations/unity/package/com.neoeng.dtrace/Editor/UnityImportGenerator.cs"
)
UNITY_SYNC = (
    ROOT
    / "integrations/unity/package/com.neoeng.dtrace/Editor/AutoSyncPostprocessor.cs"
)


def test_python_contract_exposes_one_transaction_for_all_manifest_outputs():
    source = (ROOT / "src/exporters/integration_sync.py").read_text(encoding="utf-8")
    assert "class GlobalIntegrationPlan" in source
    assert "def plan_manifest_batch" in source
    assert "def apply_manifest_batch" in source
    assert "_commit_output_items(plan.changed, all_outputs)" in source
    assert "AtomicOutputTransaction" in source


def test_godot_contract_snapshots_and_restores_the_whole_generated_tree():
    source = GODOT_IMPORTER.read_text(encoding="utf-8")
    assert "static func import_project" in source
    assert '"transaction": "GLOBAL"' in source
    assert '"rollback": "RESTORED"' in source
    assert "_snapshot_tree" in source
    assert "_restore_tree" in source
    assert "manifest_results.sort_custom" in source


def test_unity_contract_batches_manifests_and_restores_one_snapshot():
    source = UNITY_IMPORTER.read_text(encoding="utf-8")
    assert "public static ImportBatchResult ImportManifests" in source
    assert "OutputSnapshot snapshot = OutputSnapshot.Create()" in source
    assert "RestoreBatch(snapshot, results" in source
    assert "class ImportBatchResult" in source
