from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT_PLUGIN = ROOT / "integrations" / "godot" / "addons" / "neoeng_d_trace" / "plugin.gd"
UNITY_GENERATOR = ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace" / "Editor" / "UnityImportGenerator.cs"
UNITY_POSTPROCESSOR = ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace" / "Editor" / "AutoSyncPostprocessor.cs"


def test_godot_automatic_sync_uses_editor_filesystem_event_with_safety_gates():
    source = GODOT_PLUGIN.read_text(encoding="utf-8")
    assert "get_editor_interface().get_resource_filesystem()" in source
    assert "filesystem_changed.connect" in source
    assert "AUTO_SYNC_DEBOUNCE_SECONDS" in source
    assert "AUTO_SYNC_SUPPRESSION_MILLISECONDS" in source
    assert "ProjectSettings.get_setting(AUTO_SYNC_SETTING, true)" in source
    assert "_sync_running" in source
    assert "NEOENG_GODOT_AUTO_SYNC=" in source


def test_unity_automatic_sync_uses_asset_postprocessor_and_generator_contract():
    postprocessor = UNITY_POSTPROCESSOR.read_text(encoding="utf-8")
    generator = UNITY_GENERATOR.read_text(encoding="utf-8")
    assert "AssetPostprocessor" in postprocessor
    assert "OnPostprocessAllAssets" in postprocessor
    assert "EditorApplication.delayCall" in postprocessor
    assert "ProcessChangedAssets" in postprocessor
    assert "FindManifestsAffectedByAssets" in generator
    assert "AssetDatabase.FindAssets" in generator
    assert "ImportManifest(manifest)" in postprocessor
    assert "UNITY_NATIVE_AUTO_SYNC=" in postprocessor
    assert "HashRetryCounts" in postprocessor
    assert "ScheduleHashRetry" in postprocessor
    assert "MatchesChangedInput" in generator


def test_automatic_sync_does_not_delete_outputs_for_deleted_inputs():
    source = UNITY_POSTPROCESSOR.read_text(encoding="utf-8")
    assert "deletedAssets" in source
    assert "Directory.Delete" not in source
    godot = GODOT_PLUGIN.read_text(encoding="utf-8")
    assert "DirAccess.remove_absolute" not in godot