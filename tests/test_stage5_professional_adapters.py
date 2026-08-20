"""Contract tests for the explicit Godot and Unity professional adapters."""

from __future__ import annotations

import hashlib
from pathlib import Path

from src.exporters.scene_authoring_export import build_scene_authoring_export
from tests.test_stage5_scene_authoring_persistence import _document

ROOT = Path(__file__).resolve().parents[1]
GODOT_IMPORTER = (
    ROOT / "integrations/godot/addons/neoeng_d_trace/professional_scene_importer.gd"
)
GODOT_PLUGIN = ROOT / "integrations/godot/addons/neoeng_d_trace/plugin.gd"
UNITY_IMPORTER = (
    ROOT
    / "integrations"
    / "unity"
    / "package"
    / "com.neoeng.dtrace"
    / "Editor"
    / "ProfessionalSceneImportGenerator.cs"
)
UNITY_METADATA = (
    ROOT
    / "integrations"
    / "unity"
    / "package"
    / "com.neoeng.dtrace"
    / "Runtime"
    / "NeoEngProfessionalSceneMetadata.cs"
)


def test_native_adapters_are_source_only_and_expose_professional_contract() -> None:
    godot = GODOT_IMPORTER.read_text(encoding="utf-8")
    plugin = GODOT_PLUGIN.read_text(encoding="utf-8")
    unity = UNITY_IMPORTER.read_text(encoding="utf-8")
    metadata = UNITY_METADATA.read_text(encoding="utf-8")

    assert "NeoEngDTraceProfessionalSceneImporter" in godot
    assert "static func import_scene" in godot
    assert "rotation_sign" in godot
    assert "neoeng_socket_data" in godot
    assert "PROFESSIONAL_SCENE_MENU_ITEM" in plugin
    assert "ProfessionalSceneImporter.import_scene" in plugin
    assert "ProfessionalSceneImportGenerator" in unity
    assert "LoadAssetAtPath<Sprite>" in unity
    assert "FileSha256" in unity
    assert "RunHeadlessProfessionalSceneImport" in unity
    assert "serializedGroups" in metadata


def test_godot_and_unity_exports_are_distinct_and_hash_bound(tmp_path: Path) -> None:
    document, asset = _document(tmp_path)
    godot = build_scene_authoring_export(document, target="godot")
    unity = build_scene_authoring_export(document, target="unity")

    assert godot["target"] == "godot"
    assert unity["target"] == "unity"
    assert godot["source"] == unity["source"]
    assert godot["coordinate_mapping"]["position_y_sign"] == 1
    assert godot["coordinate_mapping"]["rotation_sign"] == 1
    assert unity["coordinate_mapping"]["position_y_sign"] == -1
    assert unity["coordinate_mapping"]["rotation_sign"] == -1
    assert (
        godot["scene"]["assets"][0]["sha256"]
        == hashlib.sha256(asset.read_bytes()).hexdigest()
    )
