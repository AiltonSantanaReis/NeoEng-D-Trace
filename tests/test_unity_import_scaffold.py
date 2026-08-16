from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace"


def test_unity_importer_is_present_in_editor_source_only_package():
    importer = PACKAGE_ROOT / "Editor" / "UnityImportGenerator.cs"
    runtime_metadata = PACKAGE_ROOT / "Runtime" / "NeoEngImportedSpriteMetadata.cs"

    assert importer.is_file()
    assert runtime_metadata.is_file()
    source = importer.read_text(encoding="utf-8")
    assert "RunHeadlessImport" in source
    assert "Sprite.Create" in source
    assert "PolygonCollider2D" in source
    assert "SaveAsPrefabAsset" in source
    assert "ValidateImageHash" in source
    assert "generated root contains manual content" in source


def test_unity_importer_keeps_stage_boundary_and_package_identity():
    package = json.loads((PACKAGE_ROOT / "package.json").read_text(encoding="utf-8"))
    readme = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")

    assert package["name"] == "com.neoeng.dtrace"
    assert package["version"] == "0.2.0"
    assert "Sincronização incremental" in readme
    assert "Assets/NeoEngGenerated" in readme
