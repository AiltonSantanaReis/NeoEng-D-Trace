import hashlib
from pathlib import Path

import pytest
from PIL import Image

from src.core.navmesh_2d import NavMeshSource, NavObstacle, NavRegion
from src.exporters.composition_export import (
    CompositionExportError,
    CompositionInputs,
    build_composition_package,
    validate_composition_package,
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
        assets=[AssetReferenceRecord(id="asset", path="assets/asset.png", sha256=asset_hash)],
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
