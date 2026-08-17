from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace"


def _package_manifest() -> dict:
    return json.loads((PACKAGE_ROOT / "package.json").read_text(encoding="utf-8"))


def test_unity_upm_package_has_stable_source_only_identity():
    manifest = _package_manifest()

    assert manifest == {
        "name": "com.neoeng.dtrace",
        "version": "0.2.0",
        "displayName": "NeoEng D-Trace Integration",
        "description": (
            "Source-only UPM package for the NeoEng-D-Trace integration contract."
        ),
        "unity": "2021.3",
        "author": {"name": "NeoEng-D-Trace"},
        "keywords": ["neoeng", "d-trace", "sprites", "collision", "integration"],
    }


def test_unity_upm_package_contains_runtime_and_editor_assemblies():
    runtime = json.loads(
        (PACKAGE_ROOT / "Runtime" / "NeoEngDTrace.Runtime.asmdef").read_text(
            encoding="utf-8"
        )
    )
    editor = json.loads(
        (PACKAGE_ROOT / "Editor" / "NeoEngDTrace.Editor.asmdef").read_text(
            encoding="utf-8"
        )
    )

    assert runtime["name"] == "NeoEngDTrace.Runtime"
    assert runtime["includePlatforms"] == []
    assert editor["name"] == "NeoEngDTrace.Editor"
    assert editor["includePlatforms"] == ["Editor"]
    assert editor["references"] == ["NeoEngDTrace.Runtime"]
    assert (PACKAGE_ROOT / "Runtime" / "PackageIdentity.cs").is_file()
    assert (PACKAGE_ROOT / "Editor" / "PackageDiagnostics.cs").is_file()
    assert (PACKAGE_ROOT / "Editor" / "AutoSyncPostprocessor.cs").is_file()
    assert (PACKAGE_ROOT / "Editor" / "AutoSyncPostprocessor.cs.meta").is_file()


def test_unity_importer_preserves_canonical_compound_collision_paths():
    source = (PACKAGE_ROOT / "Editor" / "UnityImportGenerator.cs").read_text(
        encoding="utf-8"
    )
    assert "ApplyCollisionArrays(manifest, manifestText);" in source
    assert "CollisionPartData" in source
    assert "collider.pathCount = unityCollisionPaths.Length;" in source
    assert "ColliderPointCounts" in source
    assert (
        'ComputeFingerprint(record.id, safeId + ".sprite", unityCollisionPaths)'
        in source
    )


def test_unity_upm_package_is_source_only_and_keeps_stage_boundary():
    forbidden = {".a", ".bundle", ".dll", ".dylib", ".exe", ".so"}
    assert not [
        path
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in forbidden
    ]

    readme = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")
    diagnostics = (PACKAGE_ROOT / "Editor" / "PackageDiagnostics.cs").read_text(
        encoding="utf-8"
    )
    assert "Etapa 6" in readme
    assert "RunHeadless" in diagnostics
    assert "UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS" in diagnostics
    assert "source_only" in diagnostics


def test_unity_stage3_optional_resources_have_native_contract_sources():
    editor_importer = PACKAGE_ROOT / "Editor" / "UnityOptionalResourceImporter.cs"
    animation_metadata = PACKAGE_ROOT / "Runtime" / "NeoEngImportedAnimationMetadata.cs"
    animation_driver = PACKAGE_ROOT / "Runtime" / "NeoEngAnimationCollisionDriver.cs"
    tileset_metadata = PACKAGE_ROOT / "Runtime" / "NeoEngImportedTilesetMetadata.cs"

    assert editor_importer.is_file()
    assert animation_metadata.is_file()
    assert animation_driver.is_file()
    assert tileset_metadata.is_file()

    editor_source = editor_importer.read_text(encoding="utf-8")
    generator_source = (PACKAGE_ROOT / "Editor" / "UnityImportGenerator.cs").read_text(
        encoding="utf-8"
    )
    runtime_asmdef = json.loads(
        (PACKAGE_ROOT / "Runtime" / "NeoEngDTrace.Runtime.asmdef").read_text(
            encoding="utf-8"
        )
    )

    assert "AnimationUtility.SetObjectReferenceCurve" in editor_source
    assert "PolygonCollider2D compoundCollider" in editor_source
    assert "TilesetCollisionPaths" in editor_source
    assert "UnityOptionalResourceImporter.Import" in generator_source
    assert "ApplyOptionalGeometryArrays" in generator_source
    assert runtime_asmdef["references"] == []
