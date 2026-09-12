import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.core.navmesh_2d import NavMeshSource, NavObstacle, NavRegion
from src.exporters.composition_export import (
    CompositionExportError,
    CompositionInputs,
    build_composition_package,
    validate_composition_package,
)
from src.exporters.animation_batch import export_animation_frames
from src.exporters.hybrid_composition_export import (
    HybridCompositionExportError,
    build_hybrid_composition_package,
    validate_hybrid_composition_package,
    validate_hybrid_runtime_manifest,
    validate_hybrid_scene,
)
from src.persistence.navmesh_io import save_navmesh
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_collider_io import save_colliders
from src.core.scenario_colliders import Collider, ColliderDocument, ColliderKind
from src.persistence.scene_authoring_io import save_scene_authoring
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.core.tilemap_model import (
    TileCell,
    TileDefinition,
    TileLayer,
    TileMapDocument,
    TileSet,
)
from src.launcher import build_parser, run_headless
from src.persistence.tilemap_io import save_tilemap


def _inputs(root: Path) -> CompositionInputs:
    return CompositionInputs(
        scene=root / "scene.ndtscene.json",
        tilemap=root / "tilemap.json",
        colliders=root / "colliders.json",
        navmesh=root / "navmesh.json",
    )


@pytest.fixture
def valid_composition_inputs(tmp_path: Path) -> CompositionInputs:
    asset = tmp_path / "assets" / "asset.png"
    asset.parent.mkdir()
    Image.new("RGBA", (8, 8), (20, 120, 220, 255)).save(asset)
    asset_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
    project = tmp_path / "project.ndtproj"
    project.write_bytes(b"project")
    scene = SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="Composition", generator="test", app_version="0.3.0"
        ),
        project=ProjectReferenceRecord(
            sha256=hashlib.sha256(project.read_bytes()).hexdigest()
        ),
        assets=[
            AssetReferenceRecord(id="asset", path="assets/asset.png", sha256=asset_hash)
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[
            SceneObjectAuthoringRecord(
                id="sprite",
                asset_id="asset",
                layer_id="foreground",
                transform=SceneTransformRecord(
                    position=Point3Record(x=4, y=4, z=0),
                    rotation=Point3Record(x=0, y=0, z=0),
                    scale=Point3Record(x=1, y=1, z=1),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )
        ],
        groups=[],
    )
    scene_path = tmp_path / "scene.ndtscene.json"
    save_scene_authoring(scene, scene_path)

    tileset = TileSet(
        id="terrain",
        atlas_asset_id="asset",
        atlas_sha256=asset_hash,
        tiles=(TileDefinition(id="grass", asset_id="asset", source_rect=(0, 0, 8, 8)),),
        atlas_path="assets/asset.png",
    )
    tilemap = TileMapDocument(
        id="map",
        name="Map",
        tileset=tileset,
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0),),
    )
    tilemap.set_cell("ground", (0, 0), TileCell("grass"))
    tilemap_path = tmp_path / "tilemap.json"
    save_tilemap(tilemap, tilemap_path)

    colliders = ColliderDocument()
    colliders.add(Collider("wall", ColliderKind.BOX, size=(8, 8)))
    collider_path = tmp_path / "colliders.json"
    save_colliders(colliders, collider_path)

    navmesh_path = tmp_path / "navmesh.json"
    save_navmesh(
        NavMeshSource(
            regions=[NavRegion("room", (0, 0, 32, 32))],
            obstacles=[NavObstacle("wall", (12, 12, 4, 4))],
        ),
        navmesh_path,
    )
    return CompositionInputs(scene_path, tilemap_path, collider_path, navmesh_path)


def test_composition_requires_all_independent_documents(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    with pytest.raises(
        CompositionExportError, match="composition input validation failed"
    ):
        build_composition_package(inputs, tmp_path / "package")


def test_composition_binds_and_revalidates_components(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    package = tmp_path / "package"
    manifest = build_composition_package(valid_composition_inputs, package)
    assert {item["kind"] for item in manifest["components"]} == {
        "scene-export-godot",
        "scene-export-unity",
        "tilemap",
        "colliders",
        "navmesh",
        "asset",
    }
    validated = validate_composition_package(package)
    assert validated["format_id"] == "neoeng-d-trace-composition-package"
    assert (package / "assets" / "asset.png").is_file()

    tilemap = package / "tilemap.json"
    tilemap.write_bytes(tilemap.read_bytes() + b"\n")
    with pytest.raises(CompositionExportError, match="hash mismatch"):
        validate_composition_package(package)


def test_composition_automatically_emits_hash_bound_tilemap_runtime(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    package = tmp_path / "composition-with-tilemap-runtime"
    manifest = build_composition_package(
        replace(valid_composition_inputs, auto_tilemap_runtime=True), package
    )
    assert manifest["capabilities"]["tilemap-runtime"] == "emitted-hash-bound"
    kinds = {item["kind"] for item in manifest["components"]}
    assert {
        "tilemap-runtime-payload",
        "tilemap-runtime-source",
        "tilemap-runtime-asset",
    } <= kinds
    validate_composition_package(package)
    payload = json.loads(
        (package / "tilemap-runtime" / "tilemap-runtime.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["source"]["path"] == "tilemap.json"
    assert payload["atlas"]["path"] == "assets/asset.png"


def test_composition_preserves_legacy_tilemap_without_atlas_runtime(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    legacy_tilemap = tmp_path / "legacy-tilemap.json"
    payload = json.loads(valid_composition_inputs.tilemap.read_text(encoding="utf-8"))
    payload["tileset"].pop("atlas_path", None)
    legacy_tilemap.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    package = tmp_path / "composition-legacy-tilemap"
    manifest = build_composition_package(
        replace(
            valid_composition_inputs,
            tilemap=legacy_tilemap,
            auto_tilemap_runtime=True,
        ),
        package,
    )
    assert (
        manifest["capabilities"]["tilemap-runtime"]
        == "not-emitted-legacy-atlas-missing"
    )
    assert not any(
        item["kind"] == "tilemap-runtime-payload" for item in manifest["components"]
    )


def _hybrid_scene() -> dict:
    return {
        "format_id": "neoeng-d-trace-hybrid-3d-scene",
        "schema_version": 1,
        "support_status": "VERTICAL_SLICE_ONLY",
        "camera": {
            "projection": "perspective",
            "fov_degrees": 55,
            "near": 0.1,
            "far": 100,
            "position": [0, 0, 8],
            "target": [0, 0, 0],
        },
        "materials": [{"id": "hero-material", "metallic": 0.0, "roughness": 0.6}],
        "meshes": [
            {
                "id": "hero-mesh",
                "material_id": "hero-material",
                "position": [0, 0, 0],
                "vertices": [[-1, -1, 0], [1, -1, 0], [0, 1, 0]],
                "triangles": [[0, 1, 2]],
            }
        ],
        "lights": [
            {
                "id": "key-light",
                "type": "directional",
                "intensity": 1.2,
                "position": [2, 3, 4],
            }
        ],
        "animation_clips": [
            {
                "id": "hero-bob",
                "mesh_id": "hero-mesh",
                "keyframes": [
                    {"time": 0.0, "position": [0, 0, 0]},
                    {"time": 1.0, "position": [0, 0.25, 0]},
                ],
            }
        ],
    }


def _animation_directory(tmp_path: Path) -> Path:
    source = tmp_path / "animation-source"
    output = tmp_path / "animation"
    source.mkdir()
    for index, offset in enumerate((0, 1)):
        image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        ImageDraw.Draw(image).rectangle(
            (2 + offset, 2, 16 + offset, 16), fill=(255, 255, 255, 255)
        )
        image.save(source / f"input_{index}.png")
    export_animation_frames(source, output, mode="basic", min_area=10)
    return output


def test_hybrid_package_preserves_animation_and_validates_3d_slice(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    composition = tmp_path / "composition"
    build_composition_package(valid_composition_inputs, composition)
    animation = _animation_directory(tmp_path)
    package = tmp_path / "hybrid"

    manifest = build_hybrid_composition_package(
        composition, animation, _hybrid_scene(), package
    )

    assert manifest["support_status"] == "VERTICAL_SLICE_ONLY"
    assert validate_hybrid_composition_package(package)["schema_version"] == 1
    assert validate_hybrid_runtime_manifest(package)["schema_version"] == 1
    assert (package / "composition" / "composition.json").is_file()
    assert (package / "animation" / "frame_0001.png").is_file()
    assert (package / "hybrid-runtime-scene.json").is_file()
    assert (
        validate_hybrid_scene(_hybrid_scene())["camera"]["projection"] == "perspective"
    )


def test_hybrid_package_rejects_tampered_component_and_invalid_scene(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    composition = tmp_path / "composition"
    build_composition_package(valid_composition_inputs, composition)
    package = tmp_path / "hybrid"
    build_hybrid_composition_package(
        composition, _animation_directory(tmp_path), _hybrid_scene(), package
    )
    hybrid_scene_path = package / "hybrid3d.json"
    hybrid_scene_path.write_text(
        hybrid_scene_path.read_text(encoding="utf-8") + "\n", encoding="utf-8"
    )
    with pytest.raises(HybridCompositionExportError, match="hash mismatch"):
        validate_hybrid_composition_package(package)

    invalid = _hybrid_scene()
    invalid["camera"]["projection"] = "orthographic"
    with pytest.raises(HybridCompositionExportError, match="perspective"):
        validate_hybrid_scene(invalid)


def test_hybrid_runtime_manifest_rejects_tampered_normalized_scene(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    composition = tmp_path / "composition"
    build_composition_package(valid_composition_inputs, composition)
    package = tmp_path / "hybrid"
    build_hybrid_composition_package(
        composition, _animation_directory(tmp_path), _hybrid_scene(), package
    )
    normalized = package / "hybrid-runtime-scene.json"
    normalized.write_text(
        normalized.read_text(encoding="utf-8").replace(
            "hero-mesh", "hero-mesh-mutated", 1
        ),
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(HybridCompositionExportError, match="hash mismatch"):
        validate_hybrid_runtime_manifest(package)


def test_hybrid_export_is_available_through_product_cli(
    tmp_path: Path, valid_composition_inputs: CompositionInputs
) -> None:
    composition = tmp_path / "composition"
    build_composition_package(valid_composition_inputs, composition)
    animation = _animation_directory(tmp_path)
    scene_path = tmp_path / "hybrid-scene.json"
    scene_path.write_text(json.dumps(_hybrid_scene()), encoding="utf-8", newline="\n")
    output = tmp_path / "hybrid-cli"
    args = build_parser().parse_args(
        [
            "--headless",
            "--export-hybrid",
            str(output),
            "--hybrid-composition",
            str(composition),
            "--hybrid-animation",
            str(animation),
            "--hybrid-scene",
            str(scene_path),
        ]
    )
    assert run_headless(args) == 0
    assert validate_hybrid_composition_package(output)["support_status"] == (
        "VERTICAL_SLICE_ONLY"
    )
