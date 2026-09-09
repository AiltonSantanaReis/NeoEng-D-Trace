"""Prepare a self-contained offline fixture for the E11 native composition flow."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.navmesh_2d import NavMeshSource, NavObstacle, NavRegion  # noqa: E402
from src.core.scenario_colliders import (  # noqa: E402
    Collider,
    ColliderDocument,
    ColliderKind,
)
from src.core.tilemap_model import (  # noqa: E402
    TileCell,
    TileDefinition,
    TileLayer,
    TileMapDocument,
    TileSet,
)
from src.persistence.navmesh_io import save_navmesh  # noqa: E402
from src.persistence.project_schema import Point3Record, PointRecord  # noqa: E402
from src.persistence.scenario_collider_io import save_colliders  # noqa: E402
from src.persistence.scenario_schema import ProjectReferenceRecord  # noqa: E402
from src.persistence.scene_authoring_io import save_scene_authoring  # noqa: E402
from src.persistence.scene_authoring_schema import (  # noqa: E402
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneEntityAuthoringRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneMaterialAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    ScenePrefabAuthoringRecord,
    ScenePrefabInstanceAuthoringRecord,
    SceneSnapRecord,
    SceneTransformRecord,
    SceneVectorGeometryRecord,
    SceneVectorImageSizeRecord,
    SceneVfxSocketRecord,
)
from src.persistence.tilemap_io import save_tilemap  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_project(path: Path) -> None:
    payload = {
        "format_id": "neoeng-d-trace-project",
        "schema_version": 1,
        "metadata": {"app_version": "0.3.0", "generator": "NeoEng-D-Trace"},
        "image": None,
        "layers": [
            {"id": "layer_default", "name": "Default", "visible": True, "locked": False}
        ],
        "groups": [],
        "objects": [
            {
                "id": "hero-object",
                "layer_id": "layer_default",
                "polygon": [
                    {"x": 24, "y": 20},
                    {"x": 112, "y": 20},
                    {"x": 112, "y": 92},
                    {"x": 24, "y": 92},
                ],
                "beziers": None,
                "collision": None,
            }
        ],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def prepare(output: Path) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(f"fixture output already exists: {output}")
    output.mkdir(parents=True)
    project = output / "e11-composition.ndtproj"
    _write_project(project)

    asset = output / "assets" / "scene" / "hero.png"
    asset.parent.mkdir(parents=True)
    image = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 20, 112, 92), fill=(38, 178, 238, 255))
    draw.ellipse((42, 30, 94, 80), fill=(240, 198, 48, 255))
    image.save(asset, format="PNG")
    asset_hash = _sha256(asset)
    project_hash = _sha256(project)
    polygon = [
        PointRecord(x=24, y=20),
        PointRecord(x=112, y=20),
        PointRecord(x=112, y=92),
        PointRecord(x=24, y=92),
    ]
    geometry = SceneVectorGeometryRecord(
        algorithm="e09-grabcut-contour-v1",
        source_sha256=asset_hash,
        image_size=SceneVectorImageSizeRecord(width=128, height=96),
        original_polygon=polygon,
        polygon=polygon,
        collision_polygon=polygon,
        detection_parameters={"channel": "alpha", "threshold": 1},
    )
    transform = SceneTransformRecord(
        position=Point3Record(x=68, y=56, z=0),
        rotation=Point3Record(x=0, y=0, z=0),
        scale=Point3Record(x=1, y=1, z=1),
        pivot=PointRecord(x=0.5, y=0.5),
    )
    scene = SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="E11 composição completa",
            generator="NeoEng-D-Trace E11",
            app_version="0.3.0",
        ),
        project=ProjectReferenceRecord(sha256=project_hash),
        assets=[
            AssetReferenceRecord(
                id="hero", path="assets/scene/hero.png", sha256=asset_hash
            )
        ],
        layers=[
            SceneLayerAuthoringRecord(id="background", name="Fundo"),
            SceneLayerAuthoringRecord(id="foreground", name="Frente"),
        ],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero-object",
                asset_id="hero",
                layer_id="foreground",
                transform=transform,
                vector_geometry=geometry,
                material=SceneMaterialAuthoringRecord(
                    albedo="#26b2ee",
                    normal_map_xy=PointRecord(x=0.12, y=-0.08),
                    normal_strength=0.8,
                    emission="#182030",
                    emission_strength=0.25,
                ),
            )
        ],
        groups=[
            SceneGroupAuthoringRecordV2(
                id="hero-group", name="Herói", members=["hero-object"]
            )
        ],
        entities=[
            SceneEntityAuthoringRecord(
                id="hero-entity",
                name="Herói",
                layer_id="foreground",
                transform=transform,
                components=[
                    {
                        "id": "body",
                        "type": "CharacterBody2D",
                        "version": 1,
                        "properties": {"speed": 120},
                    },
                    {
                        "id": "fx",
                        "type": "ParticleEmitter",
                        "version": 1,
                        "properties": {"seed": 11},
                    },
                ],
            )
        ],
        prefabs=[
            ScenePrefabAuthoringRecord(
                id="hero-prefab", name="Herói Prefab", source_entity_ids=["hero-entity"]
            )
        ],
        prefab_instances=[
            ScenePrefabInstanceAuthoringRecord(
                id="hero-instance",
                prefab_id="hero-prefab",
                root_entity_id="hero-entity",
            )
        ],
        snap=SceneSnapRecord(enabled=True, mode="grid", spacing=PointRecord(x=8, y=8)),
        camera=SceneCameraAuthoringRecord(position=PointRecord(x=64, y=48), zoom=1.0),
        parallax_layers=[
            SceneParallaxLayerRecord(
                layer_id="background",
                depth=0.2,
                translation_strength=0.82,
                zoom_strength=0.92,
            ),
            SceneParallaxLayerRecord(
                layer_id="foreground",
                depth=0.7,
                translation_strength=1.0,
                zoom_strength=1.0,
            ),
        ],
        sockets=[
            SceneLightSocketRecord(
                id="key-light",
                layer_id="foreground",
                object_id="hero-object",
                position=Point3Record(x=64, y=24, z=1),
                color="#ffe0a0",
                intensity=1.5,
                radius=96,
            ),
            SceneVfxSocketRecord(
                id="hero-vfx",
                layer_id="foreground",
                object_id="hero-object",
                position=Point3Record(x=68, y=92, z=0),
                effect_id="hero-trail",
                scale=1.0,
            ),
        ],
    )
    scene_path = output / "e11-composition.ndtscene.json"
    save_scene_authoring(scene, scene_path)

    tilemap_path = output / "assets" / "tilemaps" / "scenario.tilemap.json"
    tilemap_path.parent.mkdir(parents=True)
    tilemap = TileMapDocument(
        id="e11-map",
        name="Terreno E11",
        tileset=TileSet(
            id="terrain",
            atlas_asset_id="hero",
            atlas_sha256=asset_hash,
            tiles=(
                TileDefinition(id="grass", asset_id="hero", source_rect=(0, 0, 16, 16)),
            ),
        ),
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0),),
    )
    for coordinate in ((0, 0), (1, 0), (2, 0), (3, 0)):
        tilemap.set_cell("ground", coordinate, TileCell("grass"))
    save_tilemap(tilemap, tilemap_path)

    collider_path = output / "assets" / "colliders" / "scenario.colliders.json"
    collider_path.parent.mkdir(parents=True)
    colliders = ColliderDocument()
    colliders.add(
        Collider("hero-wall", ColliderKind.BOX, size=(64, 12), position=(64, 106))
    )
    colliders.add(
        Collider(
            "hero-trigger",
            ColliderKind.CIRCLE,
            radius=12,
            position=(68, 56),
            is_trigger=True,
        )
    )
    save_colliders(colliders, collider_path)

    navmesh_path = output / "assets" / "navmesh" / "scenario.navmesh.json"
    navmesh_path.parent.mkdir(parents=True)
    save_navmesh(
        NavMeshSource(
            regions=[NavRegion("surface", (0, 0, 128, 112))],
            obstacles=[NavObstacle("hero-wall", (32, 92, 64, 12))],
            agent_radius=4,
            cell_size=8,
        ),
        navmesh_path,
    )

    files = [project, asset, scene_path, tilemap_path, collider_path, navmesh_path]
    manifest = {
        "status": "PREPARED_FOR_NATIVE_FLOW",
        "files": {
            path.relative_to(output).as_posix(): {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in files
        },
    }
    (output / "fixture-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
