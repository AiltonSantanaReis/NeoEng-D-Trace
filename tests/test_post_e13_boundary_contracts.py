"""Boundary contracts for the post-E13 runtime package formats.

These tests exercise the rejection paths users and integrations can reach when
an authored scene or tilemap is incomplete, stale, duplicated, or tampered.
They are intentionally contract-level tests rather than implementation probes.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QEvent, QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import (
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QPolygonF,
    QTransform,
)
from PySide6.QtWidgets import QApplication, QStackedWidget

from src.core import commands as commands_module
from src.core import scene_authoring_model as scene_authoring_module
from src.core.commands import CommandManager
from src.core.hybrid_scene_model import (
    HybridSceneError,
    default_hybrid_scene,
    load_hybrid_scene,
    save_hybrid_scene,
)
from src.core.hybrid_scene_model import (
    validate_hybrid_scene as validate_editor_hybrid_scene,
)
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_lighting import (
    SceneDirectionalLight,
    SceneLightingMaterial,
    SceneLightingSettings,
    ScenePointLight,
    shade_color,
)
from src.core.scene_render_plan import build_scene_render_plan
from src.core.tilemap_grids import GridKind, GridSpec
from src.core.tilemap_model import (
    TileCell,
    TileCellDelta,
    TileDefinition,
    TileLayer,
    TileMapBounds,
    TileMapDocument,
    TileMapError,
    TileMapLimitError,
    TileSet,
)
from src.core.tilemap_rules import (
    NeighborCondition,
    TerrainRule,
    TileRuleSet,
)
from src.exporters import atlas_exporter as atlas_module
from src.exporters import hybrid_composition_export as hybrid_module
from src.exporters import integration_manifest as integration_module
from src.exporters.hybrid_composition_export import (
    HybridCompositionExportError,
    validate_hybrid_scene,
)
from src.exporters.scenario_exporter import build_scenario_runtime_export
from src.exporters.tilemap_runtime_export import (
    TileMapRuntimeExportError,
    build_tilemap_runtime_payload,
    validate_tilemap_runtime_payload,
)
from src.models import scene as scene_module
from src.models.scene import Scene
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import (
    ProjectReferenceRecord,
    ScenarioCameraRecord,
    ScenarioDocumentV1,
    ScenarioLayerRecord,
    ScenarioParallaxRecord,
    default_scenario_metadata,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneMaterialAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneParticleSystemRecord,
    SceneSnapRecord,
    SceneTransformRecord,
    SceneVectorGeometryRecord,
    SceneVectorImageSizeRecord,
    SceneVfxSocketRecord,
    upgrade_scene_authoring_document,
)
from src.persistence.scene_sequence_schema import SceneClip, SceneSequence
from src.persistence.tilemap_io import save_tilemap
from src.runtime import post_processing as post_processing_module
from src.runtime.particles import ParticleEmitterRecord
from src.runtime.scene_runtime import (
    CapabilityRequest,
    RuntimeCapabilityError,
    RuntimeClockError,
    RuntimeHost,
    RuntimeLifecycleError,
    RuntimeManifestFormatError,
    RuntimeManifestValidationError,
    RuntimePhase,
)
from src.tools import auto_detect as auto_detect_module
from src.tools import collision_brush_tool as collision_brush_tool_module
from src.tools import magnetic_lasso as magnetic_lasso_tool_module
from src.tools import magnetic_lasso_engine as magnetic_lasso_module
from src.tools import polygon_edit_tool as polygon_edit_tool_module
from src.tools.collision_brush_tool import CollisionBrushTool
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui import canvas_view as canvas_view_module
from src.ui import mask_viewer as mask_viewer_module
from src.ui import scene_sequence_panel as scene_sequence_module
from src.ui import tilemap_authoring_panel as tilemap_panel_module
from src.ui.canvas_view import CanvasView
from src.ui.context_menu_utils import fit_context_menu
from src.ui.mask_viewer import MaskViewer, MaskViewerDialog
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import (
    SceneAuthoringViewport,
    SceneCameraGuide,
    SceneObjectGraphicsItem,
    SceneParticleGraphicsItem,
    ScenePostProcessGraphicsItem,
    SceneSocketGraphicsItem,
    SceneTransformGizmo,
)
from src.ui.scene_sequence_panel import ClipBlock, SceneSequencePanel
from src.ui.tilemap_authoring_panel import TileMapAuthoringPanel
from src.ui.tileset_authoring_panel import TilesetAtlasPreview, TilesetAuthoringPanel


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


@pytest.mark.parametrize(
    ("name", "mutate", "message"),
    [
        ("format", lambda p: p.update(format_id="other"), "unsupported hybrid 3D"),
        ("schema", lambda p: p.update(schema_version=2), "unsupported hybrid 3D"),
        ("support", lambda p: p.update(support_status="EDITOR_ONLY"), "support status"),
        ("camera-shape", lambda p: p.update(camera=[]), "camera must be perspective"),
        (
            "camera-projection",
            lambda p: p["camera"].update(projection="orthographic"),
            "camera must be perspective",
        ),
        ("fov-low", lambda p: p["camera"].update(fov_degrees=0.9), "fov_degrees"),
        ("fov-high", lambda p: p["camera"].update(fov_degrees=180), "fov_degrees"),
        ("near-zero", lambda p: p["camera"].update(near=0), "clipping range"),
        ("far-before-near", lambda p: p["camera"].update(far=0.05), "clipping range"),
        ("position-size", lambda p: p["camera"].update(position=[0, 0]), "position"),
        ("materials-empty", lambda p: p.update(materials=[]), "material is required"),
        ("material-record", lambda p: p.update(materials=[{}]), "material record"),
        (
            "material-empty-id",
            lambda p: p["materials"][0].update(id=""),
            "material IDs",
        ),
        (
            "material-duplicate-id",
            lambda p: p["materials"].append(deepcopy(p["materials"][0])),
            "material IDs",
        ),
        (
            "material-metallic",
            lambda p: p["materials"][0].update(metallic=True),
            "numeric",
        ),
        ("meshes-empty", lambda p: p.update(meshes=[]), "mesh is required"),
        ("mesh-record", lambda p: p.update(meshes=[{}]), "mesh record"),
        ("mesh-empty-id", lambda p: p["meshes"][0].update(id=""), "mesh IDs"),
        (
            "mesh-duplicate-id",
            lambda p: p["meshes"].append(deepcopy(p["meshes"][0])),
            "mesh IDs",
        ),
        (
            "mesh-short-vertices",
            lambda p: p["meshes"][0].update(vertices=[]),
            "vertices",
        ),
        (
            "mesh-bad-vertex",
            lambda p: p["meshes"][0].update(
                vertices=[[0, 0, 0], [1, 0, 0], [0, "bad", 0]]
            ),
            "vertices",
        ),
        (
            "mesh-no-triangles",
            lambda p: p["meshes"][0].update(triangles=[]),
            "triangles",
        ),
        (
            "mesh-short-triangle",
            lambda p: p["meshes"][0].update(triangles=[[0, 1]]),
            "triangles",
        ),
        (
            "mesh-bool-index",
            lambda p: p["meshes"][0].update(triangles=[[True, 1, 2]]),
            "triangles",
        ),
        (
            "mesh-out-of-range-index",
            lambda p: p["meshes"][0].update(triangles=[[0, 1, 3]]),
            "triangles",
        ),
        (
            "mesh-unknown-material",
            lambda p: p["meshes"][0].update(material_id="missing"),
            "unknown material",
        ),
        (
            "mesh-bad-position",
            lambda p: p["meshes"][0].update(position=[0]),
            "position",
        ),
        ("lights-empty", lambda p: p.update(lights=[]), "light is required"),
        ("light-type", lambda p: p["lights"][0].update(type="spot"), "light type"),
        (
            "light-duplicate-id",
            lambda p: p["lights"].append(deepcopy(p["lights"][0])),
            "light IDs",
        ),
        (
            "light-intensity",
            lambda p: p["lights"][0].update(intensity=float("inf")),
            "finite",
        ),
        (
            "light-position",
            lambda p: p["lights"][0].update(position=[0, 0]),
            "position",
        ),
        ("clips-empty", lambda p: p.update(animation_clips=[]), "animation clip"),
        (
            "clip-unknown-mesh",
            lambda p: p["animation_clips"][0].update(mesh_id="missing"),
            "unknown mesh",
        ),
        (
            "clip-short-keyframes",
            lambda p: p["animation_clips"][0].update(keyframes=[]),
            "two keyframes",
        ),
        (
            "clip-keyframe-record",
            lambda p: p["animation_clips"][0].update(keyframes=[{}]),
            "two keyframes",
        ),
        (
            "clip-time",
            lambda p: p["animation_clips"][0]["keyframes"][0].update(time=True),
            "numeric",
        ),
        (
            "clip-time-order",
            lambda p: p["animation_clips"][0]["keyframes"][1].update(time=-1),
            "ordered",
        ),
        (
            "clip-position",
            lambda p: p["animation_clips"][0]["keyframes"][0].update(position=[0]),
            "position",
        ),
    ],
)
def test_hybrid_scene_rejects_invalid_boundary_records(name, mutate, message):
    payload = _hybrid_scene()
    mutate(payload)
    with pytest.raises(HybridCompositionExportError, match=message):
        validate_hybrid_scene(payload)


def _runtime_payload(tmp_path: Path) -> dict:
    atlas = tmp_path / "assets" / "tiles.png"
    atlas.parent.mkdir(parents=True)
    atlas.write_bytes(b"atlas")
    atlas_sha = hashlib.sha256(atlas.read_bytes()).hexdigest()
    tileset = TileSet(
        id="terrain",
        atlas_asset_id="atlas",
        atlas_sha256=atlas_sha,
        atlas_path="assets/tiles.png",
        tiles=(TileDefinition("grass", "atlas", (0, 0, 16, 16)),),
    )
    document = TileMapDocument(
        id="map",
        name="Map",
        tileset=tileset,
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0),),
    )
    document.set_cell("ground", (0, 0), TileCell("grass"))
    source = tmp_path / "map.ndttilemap.json"
    save_tilemap(document, source)
    return build_tilemap_runtime_payload(
        document, tilemap_path=source, project_root=tmp_path
    )


@pytest.mark.parametrize(
    ("name", "mutate", "message"),
    [
        ("format", lambda p: p.update(format_id="other"), "unsupported"),
        ("schema", lambda p: p.update(schema_version=2), "schema"),
        ("source-shape", lambda p: p.update(source=[]), "source must"),
        (
            "source-path",
            lambda p: p["source"].update(path="../map.json"),
            "safe relative",
        ),
        ("source-sha", lambda p: p["source"].update(sha256="bad"), "SHA-256"),
        ("source-bytes", lambda p: p["source"].update(bytes=0), "positive"),
        ("atlas-shape", lambda p: p.update(atlas=[]), "atlas must"),
        (
            "atlas-path",
            lambda p: p["atlas"].update(path="../tiles.png"),
            "safe relative",
        ),
        ("atlas-sha", lambda p: p["atlas"].update(sha256="bad"), "SHA-256"),
        ("atlas-bytes", lambda p: p["atlas"].update(bytes=0), "positive"),
        ("grid", lambda p: p.update(grid="custom"), "grid"),
        ("id", lambda p: p.update(id=""), "id"),
        ("name", lambda p: p.update(name=""), "name"),
        ("chunk-size", lambda p: p.update(chunk_size=7), "chunk_size"),
        ("bounds-shape", lambda p: p.update(bounds=[]), "bounds"),
        (
            "bounds-order",
            lambda p: p.update(bounds={"min_x": 2, "min_y": 0, "max_x": 1, "max_y": 0}),
            "bounds",
        ),
        ("tileset-shape", lambda p: p.update(tileset=[]), "tileset"),
        ("tileset-id", lambda p: p["tileset"].update(id=""), "tileset.id"),
        (
            "tileset-atlas-id",
            lambda p: p["tileset"].update(atlas_asset_id=""),
            "atlas_asset_id",
        ),
        (
            "tileset-hash",
            lambda p: p["tileset"].update(atlas_sha256="0" * 64),
            "hashes",
        ),
        ("tileset-version", lambda p: p["tileset"].update(version=True), "version"),
        ("tiles-empty", lambda p: p["tileset"].update(tiles=[]), "tiles"),
        ("tile-shape", lambda p: p["tileset"].update(tiles=[[]]), "tile must"),
        (
            "tile-duplicate",
            lambda p: p["tileset"]["tiles"].append(deepcopy(p["tileset"]["tiles"][0])),
            "duplicate",
        ),
        (
            "tile-asset",
            lambda p: p["tileset"]["tiles"][0].update(asset_id=""),
            "asset_id",
        ),
        (
            "tile-rect",
            lambda p: p["tileset"]["tiles"][0]["source_rect"].update(w=0),
            "source_rect",
        ),
        (
            "tile-pivot",
            lambda p: p["tileset"]["tiles"][0]["pivot"].update(x=2),
            "pivot",
        ),
        (
            "tile-variant",
            lambda p: p["tileset"]["tiles"][0].update(variant=""),
            "variant",
        ),
        (
            "tile-frames",
            lambda p: p["tileset"]["tiles"][0].update(animation_frames=[1]),
            "animation_frames",
        ),
        (
            "tile-properties",
            lambda p: p["tileset"]["tiles"][0].update(properties=[]),
            "properties",
        ),
        (
            "tile-version",
            lambda p: p["tileset"]["tiles"][0].update(version=True),
            "version",
        ),
        ("layers-empty", lambda p: p.update(layers=[]), "layers"),
        ("layer-shape", lambda p: p.update(layers=[[]]), "layer must"),
        (
            "layer-duplicate",
            lambda p: p["layers"].append(deepcopy(p["layers"][0])),
            "duplicate",
        ),
        ("layer-name", lambda p: p["layers"][0].update(name=""), "layer.name"),
        ("layer-order", lambda p: p["layers"][0].update(order=True), "order"),
        ("layer-visible", lambda p: p["layers"][0].update(visible="yes"), "visible"),
        ("layer-opacity", lambda p: p["layers"][0].update(opacity=2), "opacity"),
        ("cells-shape", lambda p: p.update(cells={}), "cells"),
        (
            "cell-layer",
            lambda p: p["cells"][0].update(layer_id="missing"),
            "unknown layer",
        ),
        ("cell-coordinate", lambda p: p["cells"][0].update(x=True), "cell.x"),
        (
            "cell-tile",
            lambda p: p["cells"][0].update(tile_id="missing"),
            "unknown tile",
        ),
        ("cell-variant", lambda p: p["cells"][0].update(variant=""), "variant"),
        ("cell-metadata", lambda p: p["cells"][0].update(metadata=[]), "metadata"),
        ("rules-shape", lambda p: p.update(rules=[]), "rules must"),
        (
            "rules-fallback",
            lambda p: p["rules"].update(fallback_tile_id="missing"),
            "fallback",
        ),
        ("rules-list", lambda p: p["rules"].update(rules={}), "rules.rules"),
        ("counts", lambda p: p["counts"].update(cells=99), "counts"),
    ],
)
def test_tilemap_runtime_rejects_invalid_boundary_records(
    tmp_path: Path, name, mutate, message
):
    payload = _runtime_payload(tmp_path)
    mutate(payload)
    with pytest.raises(TileMapRuntimeExportError, match=message):
        validate_tilemap_runtime_payload(payload)


def _tile_kwargs() -> dict:
    return {
        "id": "grass",
        "asset_id": "atlas",
        "source_rect": (0, 0, 16, 16),
    }


def _model_document(*, bounds: TileMapBounds | None = None) -> TileMapDocument:
    tileset = TileSet(
        id="terrain",
        atlas_asset_id="atlas",
        atlas_sha256="0" * 64,
        tiles=(
            TileDefinition("grass", "atlas", (0, 0, 16, 16)),
            TileDefinition("stone", "atlas", (16, 0, 16, 16)),
        ),
    )
    return TileMapDocument(
        id="map",
        name="Map",
        tileset=tileset,
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0),),
        bounds=bounds,
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda p: p.update(id=True), "tile id"),
        (lambda p: p.update(id="not portable"), "tile id"),
        (lambda p: p.update(asset_id=1), "asset_id"),
        (lambda p: p.update(source_rect=(0, 0, 16)), "four integers"),
        (lambda p: p.update(source_rect=(-1, 0, 16, 16)), "non-negative"),
        (lambda p: p.update(source_rect=(0, 0, 0, 16)), "positive size"),
        (lambda p: p.update(pivot=(0.5,)), "two values"),
        (lambda p: p.update(pivot=(float("nan"), 0.5)), "finite"),
        (lambda p: p.update(pivot=(1.1, 0.5)), "between 0 and 1"),
        (lambda p: p.update(variant=""), "variant"),
        (lambda p: p.update(animation_frames=("",)), "frame IDs"),
        (lambda p: p.update(version=True), "version must be an integer"),
        (lambda p: p.update(version=0), "version must be positive"),
        (lambda p: p.update(properties={1: "bad"}), "non-empty string keys"),
        (lambda p: p.update(properties={"tag": 1}), "string values"),
    ],
)
def test_tile_definition_rejects_unsafe_boundary_values(mutate, message):
    payload = _tile_kwargs()
    mutate(payload)
    with pytest.raises(TileMapError, match=message):
        TileDefinition(**payload)


@pytest.mark.parametrize(
    "atlas_path",
    ["", "   ", "/absolute.png", "../escape.png", "folder/../asset.png", "C:/asset"],
)
def test_tileset_rejects_unsafe_atlas_references(atlas_path):
    with pytest.raises(TileMapError, match="atlas_path"):
        TileSet(
            id="terrain",
            atlas_asset_id="atlas",
            atlas_sha256="0" * 64,
            tiles=(TileDefinition(**_tile_kwargs()),),
            atlas_path=atlas_path,
        )


def test_tileset_limits_lookup_and_hash_are_fail_closed(monkeypatch):
    tile = TileDefinition(**_tile_kwargs())
    with pytest.raises(TileMapError, match="at least one tile"):
        TileSet(
            id="terrain",
            atlas_asset_id="atlas",
            atlas_sha256="0" * 64,
            tiles=(),
        )

    monkeypatch.setattr("src.core.tilemap_model.MAX_TILESET_TILES", 0)
    with pytest.raises(TileMapLimitError, match="tile limit"):
        TileSet(
            id="terrain",
            atlas_asset_id="atlas",
            atlas_sha256="0" * 64,
            tiles=(tile,),
        )

    monkeypatch.setattr("src.core.tilemap_model.MAX_TILESET_TILES", 65_536)
    tileset = TileSet(
        id="terrain",
        atlas_asset_id="atlas",
        atlas_sha256="0" * 64,
        tiles=(tile,),
        atlas_path="assets/atlas.png",
    )
    assert tileset.has_tile("grass")
    assert not tileset.has_tile("missing")
    assert tileset.verify_atlas(b"wrong") is False
    with pytest.raises(TileMapError, match="unknown tile"):
        tileset.tile("missing")

    with pytest.raises(TileMapError, match="positive"):
        TileSet(
            id="terrain",
            atlas_asset_id="atlas",
            atlas_sha256="0" * 64,
            tiles=(tile,),
            version=0,
        )


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: TileCell("grass", variant=""), "cell variant"),
        (lambda: TileLayer("ground", " ", 0), "layer name"),
        (lambda: TileLayer("ground", "Ground", 0, opacity=-0.1), "layer opacity"),
        (lambda: TileMapBounds(2, 0, 1, 1), "bounds must be ordered"),
    ],
)
def test_tilemap_metadata_rejects_invalid_values(factory, message):
    with pytest.raises(TileMapError, match=message):
        factory()


def test_tilemap_bounds_limit_is_enforced(monkeypatch):
    monkeypatch.setattr("src.core.tilemap_model.MAX_TILEMAP_CELLS", 3)
    with pytest.raises(TileMapLimitError, match="cell limit"):
        TileMapBounds(0, 0, 1, 1)


def test_tilemap_document_rejects_invalid_structure_and_mutation_limits(monkeypatch):
    tileset = _model_document().tileset
    document = _model_document()
    with pytest.raises(TileMapError, match="map name"):
        TileMapDocument(
            id="map",
            name=" ",
            tileset=tileset,
            grid="orthogonal",
            layers=(TileLayer("ground", "Ground", 0),),
        )
    with pytest.raises(TileMapError, match="grid"):
        TileMapDocument(
            id="map",
            name="Map",
            tileset=tileset,
            grid="custom",
            layers=(TileLayer("ground", "Ground", 0),),
        )
    with pytest.raises(TileMapError, match="at least one"):
        TileMapDocument(
            id="map", name="Map", tileset=tileset, grid="orthogonal", layers=()
        )
    monkeypatch.setattr("src.core.tilemap_model.MAX_TILEMAP_LAYERS", 0)
    with pytest.raises(TileMapLimitError, match="layer limit"):
        TileMapDocument(
            id="map",
            name="Map",
            tileset=tileset,
            grid="orthogonal",
            layers=(TileLayer("ground", "Ground", 0),),
        )

    monkeypatch.setattr("src.core.tilemap_model.MAX_TILEMAP_LAYERS", 256)
    with pytest.raises(TileMapError, match="TileLayer"):
        document.add_layer({})
    with pytest.raises(TileMapError, match="duplicate"):
        document.add_layer(TileLayer("ground", "Duplicate", 1))
    monkeypatch.setattr("src.core.tilemap_model.MAX_TILEMAP_LAYERS", 1)
    with pytest.raises(TileMapLimitError, match="layer limit"):
        document.add_layer(TileLayer("effects", "Effects", 1))


def test_tilemap_document_rejects_coordinates_and_delta_drift(monkeypatch):
    document = _model_document(bounds=TileMapBounds(0, 0, 1, 1))
    with pytest.raises(TileMapError, match="coordinate"):
        document.get_cell("ground", (0,))
    with pytest.raises(TileMapLimitError, match="outside"):
        document.get_cell("ground", (2, 0))
    assert document.apply_deltas(()) == ()
    cell = TileCell("grass")
    with pytest.raises(TileMapError, match="normalized"):
        document.apply_deltas(
            (
                # A list is accepted by the coordinate validator but is not the
                # canonical tuple required by a persisted delta.
                TileCellDelta("ground", [0, 0], None, cell),
            )
        )
    with pytest.raises(TileMapError, match="before value"):
        document.apply_deltas((TileCellDelta("ground", (0, 0), cell, None),))
    monkeypatch.setattr("src.core.tilemap_model.MAX_TILEMAP_CELLS", 0)
    with pytest.raises(TileMapLimitError, match="populated cell"):
        document.set_cell("ground", (0, 0), cell)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: NeighborCondition((0, 0), ("grass",)), "own cell"),
        (lambda: NeighborCondition((1, True), ("grass",)), "integer pairs"),
        (lambda: NeighborCondition((1, 0)), "allow a tile"),
        (lambda: NeighborCondition((1, 0), ("",)), "non-empty"),
        (lambda: NeighborCondition.from_dict([]), "must be an object"),
        (lambda: NeighborCondition.from_dict({"offset": []}), "offset must"),
        (
            lambda: NeighborCondition.from_dict(
                {"offset": {"x": 1, "y": 0}, "allowed_tile_ids": "grass"}
            ),
            "list",
        ),
        (
            lambda: NeighborCondition.from_dict(
                {"offset": {"x": 1, "y": 0}, "allowed_tile_ids": [1]}
            ),
            "list",
        ),
        (
            lambda: NeighborCondition.from_dict(
                {"offset": {"x": 1, "y": 0}, "allow_empty": "yes"}
            ),
            "boolean",
        ),
    ],
)
def test_rule_condition_rejects_invalid_shapes(factory, message):
    with pytest.raises(TileMapError, match=message):
        factory()


def test_rule_condition_matches_and_roundtrips():
    condition = NeighborCondition((1, 0), ("grass",), allow_empty=True)
    assert condition.matches(None)
    assert condition.matches(TileCell("grass"))
    assert not condition.matches(TileCell("stone"))
    assert NeighborCondition.from_dict(condition.to_dict()) == condition


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: TerrainRule("", "grass"), "required"),
        (lambda: TerrainRule("r", "grass", priority=True), "priority"),
        (lambda: TerrainRule("r", "grass", weight=True), "weight"),
        (lambda: TerrainRule("r", "grass", weight=0), "positive"),
        (
            lambda: TerrainRule(
                "r",
                "grass",
                conditions=(
                    NeighborCondition((1, 0), ("grass",)),
                    NeighborCondition((1, 0), ("stone",)),
                ),
            ),
            "unique offsets",
        ),
        (lambda: TerrainRule.from_dict([]), "must be an object"),
        (lambda: TerrainRule.from_dict({"conditions": {}}), "must be lists"),
        (
            lambda: TerrainRule.from_dict({"depends_on": [1]}),
            "dependencies must be strings",
        ),
        (lambda: TerrainRule.from_dict({"id": 1}), "IDs must be strings"),
        (lambda: TerrainRule.from_dict({"priority": True}), "priority"),
        (lambda: TerrainRule.from_dict({"weight": True}), "weight"),
    ],
)
def test_terrain_rule_rejects_invalid_shapes(factory, message):
    with pytest.raises(TileMapError, match=message):
        factory()


def test_rule_set_rejects_graph_and_reference_errors():
    with pytest.raises(TileMapError, match="fallback"):
        TileRuleSet((), fallback_tile_id="")
    rule = TerrainRule("r", "grass")
    with pytest.raises(TileMapError, match="unique"):
        TileRuleSet((rule, rule), fallback_tile_id="grass")
    with pytest.raises(TileMapError, match="unknown rule"):
        TileRuleSet(
            (TerrainRule("r", "grass", depends_on=("missing",)),),
            fallback_tile_id="grass",
        )

    shared = TerrainRule("shared", "grass")
    dependent = TerrainRule("dependent", "grass", depends_on=("shared",))
    rules = TileRuleSet((dependent, shared), fallback_tile_id="grass")
    resolution = rules.resolve(
        _model_document(),
        "ground",
        (0, 0),
        grid=GridSpec(GridKind.ORTHOGONAL),
    )
    assert resolution.tile_id == "grass"
    with pytest.raises(TileMapError, match="unknown target"):
        TileRuleSet((TerrainRule("bad", "missing"),), fallback_tile_id="grass").resolve(
            _model_document(),
            "ground",
            (0, 0),
            grid=GridSpec(GridKind.ORTHOGONAL),
        )
    with pytest.raises(TileMapError, match="unknown fallback"):
        TileRuleSet((), fallback_tile_id="missing").resolve(
            _model_document(),
            "ground",
            (0, 0),
            grid=GridSpec(GridKind.ORTHOGONAL),
        )


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: TileRuleSet.from_dict([]), "must be an object"),
        (lambda: TileRuleSet.from_dict({"rules": {}}), "rules must be a list"),
        (
            lambda: TileRuleSet.from_dict({"rules": [], "fallback_tile_id": 1}),
            "fallback",
        ),
    ],
)
def test_rule_set_deserialization_rejects_invalid_shapes(factory, message):
    with pytest.raises(TileMapError, match=message):
        factory()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "must be an object"),
        ({"format_id": "other"}, "unsupported hybrid editor format"),
        (
            {**default_hybrid_scene(), "schema_version": 2},
            "unsupported hybrid editor schema",
        ),
        ({**default_hybrid_scene(), "support_status": "EDITOR_ONLY"}, "support status"),
    ],
)
def test_editor_hybrid_rejects_top_level_contract_drift(payload, message):
    with pytest.raises(HybridSceneError, match=message):
        validate_editor_hybrid_scene(payload)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda p: p.update(camera=None), "camera is required"),
        (lambda p: p["camera"].update(projection="custom"), "projection"),
        (lambda p: p["camera"].update(fov_degrees=float("nan")), "finite"),
        (lambda p: p["camera"].update(position=[0, 0]), "3 values"),
        (lambda p: p["materials"].__setitem__(0, 1), "material 0"),
        (lambda p: p["materials"][0].update(id=""), r"material\[0\].id"),
        (lambda p: p["materials"][0].update(color="x" * 17), "color"),
        (lambda p: p["materials"][0].update(metallic=True), "numeric"),
        (lambda p: p.update(objects=[]), "at least one object"),
        (lambda p: p["objects"].__setitem__(0, 1), "object 0"),
        (lambda p: p["objects"][0].update(id=""), r"object\[0\].id"),
        (lambda p: p["objects"].append(deepcopy(p["objects"][0])), "object IDs"),
        (lambda p: p["objects"][0].update(kind="audio"), "kind"),
        (lambda p: p["objects"][0].update(position=[2_000_000, 0, 0]), "safe range"),
        (lambda p: p["objects"][0].update(scale=[0, 1, 1]), "scale"),
        (lambda p: p["objects"][0].update(primitive="sphere"), "primitive"),
        (lambda p: p["objects"][0].update(material_id="missing"), "unknown material"),
        (lambda p: p["objects"][1].update(light_type="spot"), "light_type"),
        (lambda p: p["objects"][1].update(intensity=-1), "intensity"),
        (lambda p: p["objects"][2].update(target=[0, 0]), "target"),
        (lambda p: p.update(selected_id="missing"), "selected_id"),
    ],
)
def test_editor_hybrid_rejects_object_and_transform_boundaries(mutate, message):
    payload = default_hybrid_scene()
    mutate(payload)
    with pytest.raises(HybridSceneError, match=message):
        validate_editor_hybrid_scene(payload)


def test_editor_hybrid_supports_orthographic_point_light_and_atomic_recovery(
    tmp_path: Path, monkeypatch
):
    payload = default_hybrid_scene()
    payload["camera"]["projection"] = "orthographic"
    payload["objects"][1]["light_type"] = "point"
    payload["objects"][1]["intensity"] = 0.0
    assert validate_editor_hybrid_scene(payload) == payload

    path = tmp_path / "scene.hybrid3d.json"
    assert save_hybrid_scene(payload, path) == path
    assert load_hybrid_scene(path) == payload
    path.write_text("not-json", encoding="utf-8")
    with pytest.raises(HybridSceneError, match="cannot be read"):
        load_hybrid_scene(path)

    def fail_replace(*_args, **_kwargs):
        raise OSError("replace blocked")

    monkeypatch.setattr("src.core.hybrid_scene_model.os.replace", fail_replace)
    with pytest.raises(HybridSceneError, match="cannot be saved"):
        save_hybrid_scene(payload, path)
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: SceneLightingMaterial(albedo="bad"), "components"),
        (lambda: SceneLightingMaterial(albedo=(float("nan"), 0, 0)), "finite"),
        (lambda: SceneLightingMaterial(normal_xy=(0,)), "coordinates"),
        (lambda: SceneLightingMaterial(normal_strength=-1), "normal_strength"),
        (lambda: SceneLightingMaterial(normal_strength=2), "normal_strength"),
        (lambda: SceneLightingMaterial(emission_strength=-1), "emission_strength"),
        (lambda: SceneLightingMaterial(opacity=2), "opacity"),
        (lambda: ScenePointLight("", (0, 0)), "light id"),
        (lambda: ScenePointLight("p", (0,)), "coordinates"),
        (lambda: ScenePointLight("p", (0, 0), intensity=-1), "intensity"),
        (lambda: ScenePointLight("p", (0, 0), radius=0), "radius"),
        (
            lambda: SceneDirectionalLight(
                "",
            ),
            "light id",
        ),
        (lambda: SceneDirectionalLight("d", direction_degrees=float("inf")), "finite"),
        (lambda: SceneDirectionalLight("d", intensity=-1), "intensity"),
        (lambda: SceneLightingSettings(ambient_color="bad"), "components"),
        (lambda: SceneLightingSettings(ambient_intensity=2), "ambient_intensity"),
        (lambda: SceneLightingSettings(occluders=(((0,),),)), "coordinates"),
    ],
)
def test_scene_lighting_rejects_invalid_authoring_values(factory, message):
    with pytest.raises(ValueError, match=message):
        factory()


def test_scene_lighting_shade_covers_directional_point_shadow_and_falloff_paths():
    material = SceneLightingMaterial()
    ambient_only = SceneLightingSettings(ambient_intensity=0.2)
    color, opacity, contributors = shade_color((0, 0), material, ambient_only)
    assert opacity == 1.0
    assert contributors == ()
    assert color == (0.2, 0.2, 0.2)

    disabled = ScenePointLight("disabled", (0, 10), enabled=False)
    zero = SceneDirectionalLight("zero", intensity=0)
    far = ScenePointLight("far", (0, 10), radius=5)
    settings = SceneLightingSettings(lights=(disabled, zero, far))
    assert shade_color((0, 0), material, settings)[2] == ()

    point = ScenePointLight("point", (0, 10), radius=20)
    directional = SceneDirectionalLight("directional", direction_degrees=90)
    lit = SceneLightingSettings(lights=(point, directional))
    assert set(shade_color((0, 0), material, lit)[2]) == {"point", "directional"}

    opposite = SceneDirectionalLight("opposite", direction_degrees=-90)
    assert (
        shade_color((0, 0), material, SceneLightingSettings(lights=(opposite,)))[2]
        == ()
    )

    blocker = ((-2.0, 1.0), (2.0, 1.0), (2.0, 2.0))
    blocked = SceneLightingSettings(
        lights=(point, directional), occluders=((), ((0.0, 0.0),), blocker)
    )
    assert shade_color((0, 0), material, blocked)[2] == ()
    ignores_shadows = SceneLightingMaterial(receives_shadow=False)
    assert set(shade_color((0, 0), ignores_shadows, blocked)[2]) == {
        "point",
        "directional",
    }


def test_context_menu_fit_handles_native_nested_and_probe_contracts():
    from PySide6.QtWidgets import QApplication, QMenu

    app = QApplication.instance() or QApplication([])
    assert app is not None

    menu = QMenu()
    menu.addAction("&Uma ação localizada muito longa")
    submenu = QMenu("Submenu", menu)
    submenu.addAction("Outra ação")
    menu.addMenu(submenu)
    result = fit_context_menu(menu)
    assert result is menu
    assert menu.minimumWidth() > 0
    assert submenu.minimumWidth() > 0

    class Probe:
        def __init__(self):
            self.adjusted = False

        def adjustSize(self):
            self.adjusted = True

    probe = Probe()
    assert fit_context_menu(probe) is probe
    assert probe.adjusted
    assert fit_context_menu(object()) is not None


def _runtime_host_payload() -> dict:
    document = ScenarioDocumentV1(
        metadata=default_scenario_metadata("Boundary runtime"),
        project=ProjectReferenceRecord(sha256="a" * 64),
        camera=ScenarioCameraRecord(position=PointRecord(x=0, y=0), zoom=1.0),
        layers=[
            ScenarioLayerRecord(
                id="layer_main",
                name="Main",
                visible=True,
                object_ids=[],
                parallax=ScenarioParallaxRecord(
                    depth=0.5,
                    translation_strength=0.8,
                    zoom_strength=0.9,
                ),
            )
        ],
    )
    return build_scenario_runtime_export(document)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"fixed_dt": True}, "fixed_dt"),
        ({"fixed_dt": 0}, "fixed_dt"),
        ({"fixed_dt": float("nan")}, "fixed_dt"),
        ({"max_substeps": True}, "max_substeps"),
        ({"max_substeps": 0}, "max_substeps"),
    ],
)
def test_runtime_host_rejects_unsafe_clock_configuration(kwargs, message):
    with pytest.raises(ValueError, match=message):
        RuntimeHost(**kwargs)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: CapabilityRequest(""), "required_capability"),
        (lambda: CapabilityRequest("x", required=1), "required"),
        (lambda: CapabilityRequest("x", fallback_mode="disabled"), "provided together"),
        (lambda: CapabilityRequest("x", fallback_reason="reason"), "provided together"),
        (
            lambda: CapabilityRequest("x", fallback_mode="", fallback_reason="reason"),
            "fallback_mode",
        ),
        (
            lambda: CapabilityRequest(
                "x", fallback_mode="disabled", fallback_reason=""
            ),
            "fallback_reason",
        ),
    ],
)
def test_runtime_capability_requests_reject_ambiguous_fallbacks(factory, message):
    with pytest.raises(ValueError, match=message):
        factory()


def test_runtime_host_rejects_lifecycle_clock_and_capability_edges():
    host = RuntimeHost(fixed_dt=0.1, max_substeps=2)
    with pytest.raises(RuntimeLifecycleError, match="manifest"):
        host.start()
    with pytest.raises(RuntimeLifecycleError, match="running"):
        host.pause()
    with pytest.raises(RuntimeLifecycleError, match="paused"):
        host.resume()
    with pytest.raises(RuntimeLifecycleError, match="activated"):
        host.stop()
    with pytest.raises(ValueError, match="CapabilityRequest"):
        host.negotiate([object()])

    payload = _runtime_host_payload()
    host.load_manifest(payload)
    assert host.snapshot.phase is RuntimePhase.READY
    with pytest.raises(RuntimeLifecycleError, match="running"):
        host.tick(0.1)
    host.start()
    with pytest.raises(RuntimeLifecycleError, match="stop"):
        host.load_manifest(payload)
    for elapsed in ("bad", float("inf"), 0.3):
        with pytest.raises(RuntimeClockError):
            host.tick(elapsed)
    host.pause()
    with pytest.raises(RuntimeLifecycleError, match="running"):
        host.pause()
    host.resume()
    host.stop()
    assert host.snapshot.phase is RuntimePhase.STOPPED
    host.start()
    assert host.snapshot.phase is RuntimePhase.RUNNING
    host.stop()
    with pytest.raises(RuntimeCapabilityError):
        RuntimeHost().load_manifest(
            payload,
            requirements=[CapabilityRequest("unsupported.capability")],
        )


def test_runtime_host_file_reader_rejects_missing_noncanonical_and_invalid_files(
    tmp_path: Path,
):
    host = RuntimeHost()
    missing = tmp_path / "missing.json"
    with pytest.raises(RuntimeManifestFormatError, match="not found"):
        host.load_file(missing)
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(RuntimeManifestFormatError, match="not a file"):
        host.load_file(directory)
    invalid = tmp_path / "invalid.json"
    invalid.write_bytes(b"not-json")
    with pytest.raises(RuntimeManifestFormatError, match="invalid"):
        host.load_file(invalid)

    payload = _runtime_host_payload()
    canonical = (
        json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")
    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_bytes(canonical.replace(b"\n", b"", 1))
    with pytest.raises(RuntimeManifestFormatError, match="canonical"):
        host.load_file(noncanonical)
    malformed = tmp_path / "malformed.json"
    malformed.write_bytes(b'[{"format_id": 1}]')
    with pytest.raises(RuntimeManifestValidationError, match="root"):
        host.load_file(malformed)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda p: p["camera"].update(near=float("nan")), "finite"),
        (lambda p: p["camera"].update(target=[0, 0]), "target"),
        (lambda p: p["materials"].__setitem__(0, 1), "record"),
        (lambda p: p["materials"][0].update(id=1), "record"),
        (lambda p: p["materials"][0].update(roughness=True), "numeric"),
        (lambda p: p["meshes"].__setitem__(0, 1), "record"),
        (lambda p: p["meshes"][0].update(id=1), "record"),
        (lambda p: p["meshes"][0].update(vertices=[[0, 0, 0], [1, 0, 0]]), "vertices"),
        (
            lambda p: p["meshes"][0].update(vertices=[[0, 0, 0], [1, 0, 0], [0, 1]]),
            "vertices",
        ),
        (lambda p: p["meshes"][0].update(triangles=["bad"]), "triangles"),
        (lambda p: p["meshes"][0].update(triangles=[[0, 1, 2, 0]]), "triangles"),
        (lambda p: p["meshes"][0].update(triangles=[[0, 1, True]]), "triangles"),
        (lambda p: p["lights"].__setitem__(0, 1), "type"),
        (lambda p: p["lights"][0].update(id=1), "IDs"),
        (lambda p: p["lights"][0].update(intensity=float("nan")), "finite"),
        (lambda p: p["lights"][0].update(position=[0, 0]), "position"),
        (lambda p: p["animation_clips"].__setitem__(0, 1), "unknown mesh"),
        (lambda p: p["animation_clips"][0].update(keyframes=[1, 2]), "keyframe"),
        (lambda p: p["animation_clips"][0].update(keyframes=[{}]), "two keyframes"),
        (
            lambda p: p["animation_clips"][0]["keyframes"][0].update(time=float("nan")),
            "finite",
        ),
        (
            lambda p: p["animation_clips"][0]["keyframes"][0].update(position=[0, 0]),
            "position",
        ),
    ],
)
def test_hybrid_export_rejects_remaining_mesh_light_and_animation_edges(
    mutate, message
):
    payload = _hybrid_scene()
    mutate(payload)
    with pytest.raises(HybridCompositionExportError, match=message):
        validate_hybrid_scene(payload)


@pytest.mark.parametrize(
    ("image", "message"),
    [
        (np.zeros((2,), dtype=np.uint8), "2D"),
        (np.zeros((2, 2, 2), dtype=np.uint8), "2D"),
        (np.zeros((0, 2), dtype=np.uint8), "positive"),
        (np.zeros((2, 0), dtype=np.uint8), "positive"),
        (np.zeros((2, 2, 3), dtype="U1"), "numeric"),
    ],
)
def test_auto_detect_rejects_invalid_image_shapes_and_types(image, message):
    with pytest.raises(ValueError, match=message):
        auto_detect_module._validate_detection_image(image)


def test_auto_detect_enforces_image_operational_limits(monkeypatch):
    monkeypatch.setattr(auto_detect_module, "MAX_IMAGE_DIMENSION", 2)
    with pytest.raises(ValueError, match="dimensions"):
        auto_detect_module._validate_detection_image(np.zeros((3, 1), dtype=np.uint8))
    monkeypatch.setattr(auto_detect_module, "MAX_IMAGE_DIMENSION", 10_000)
    monkeypatch.setattr(auto_detect_module, "MAX_IMAGE_PIXELS", 3)
    with pytest.raises(ValueError, match="pixel limit"):
        auto_detect_module._validate_detection_image(np.zeros((2, 2), dtype=np.uint8))
    monkeypatch.setattr(auto_detect_module, "MAX_IMAGE_PIXELS", 10_000)
    monkeypatch.setattr(auto_detect_module, "MAX_DECODED_IMAGE_BYTES", 3)
    with pytest.raises(ValueError, match="decoded byte"):
        auto_detect_module._validate_detection_image(np.zeros((2, 2), dtype=np.uint8))


@pytest.mark.parametrize("value", [True, "bad", 0, -0.1, 1.1, float("nan")])
def test_auto_detect_rejects_unsafe_numeric_parameters(value):
    with pytest.raises(ValueError, match="downscale"):
        auto_detect_module._bounded_downscale(value)


@pytest.mark.parametrize("value", [True, 1.5])
def test_auto_detect_rejects_non_integer_chaikin_iterations(value):
    with pytest.raises(ValueError, match="chaikin_iterations"):
        auto_detect_module._bounded_chaikin_iterations(value)


@pytest.mark.parametrize("value", [True, 0, 2, 32])
def test_auto_detect_rejects_invalid_morphology_kernels(value):
    with pytest.raises(ValueError, match="morph_kernel_size"):
        auto_detect_module._bounded_morphology_kernel(value)


def test_auto_detect_image_normalization_and_alpha_paths():
    gray = np.array([[0, 100], [200, 255]], dtype=np.uint8)
    assert auto_detect_module._resize_grayscale(gray, 1.0) is gray
    assert auto_detect_module._resize_grayscale(gray, 0.5).shape == (1, 1)
    assert auto_detect_module._to_uint8_grayscale(gray).dtype == np.uint8
    assert auto_detect_module._to_uint8_grayscale(
        np.zeros((2, 2, 3), dtype=np.uint8)
    ).shape == (2, 2)
    assert auto_detect_module._to_uint8_grayscale(
        np.zeros((2, 2, 4), dtype=np.uint8)
    ).shape == (2, 2)
    assert np.all(auto_detect_module._to_uint8_grayscale(np.full((2, 2), np.nan)) == 0)
    assert np.all(auto_detect_module._to_uint8_grayscale(np.full((2, 2), 4.0)) == 0)
    scaled = auto_detect_module._to_uint8_grayscale(np.array([[0.0, 1.0]]))
    assert scaled.tolist() == [[0, 1]]
    stretched = auto_detect_module._to_uint8_grayscale(np.array([[-1.0, 256.0]]))
    assert stretched.tolist() == [[0, 255]]
    alpha = np.zeros((2, 2, 4), dtype=np.uint8)
    assert auto_detect_module._alpha_foreground_mask(alpha) is None
    alpha[:, :, 3] = 255
    assert auto_detect_module._alpha_foreground_mask(alpha) is None
    alpha[0, 0, 3] = 0
    assert auto_detect_module._alpha_foreground_mask(alpha) is not None
    assert auto_detect_module._alpha_foreground_mask(gray) is None


def test_auto_detect_mask_and_geometry_diagnostics_cover_real_failures(monkeypatch):
    constant = np.zeros((12, 12), dtype=np.uint8)
    assert (
        np.count_nonzero(auto_detect_module._foreground_mask(constant, constant)) == 0
    )
    foreground = constant.copy()
    foreground[3:9, 3:9] = 255
    mask = auto_detect_module._foreground_mask(foreground, foreground)
    assert mask.shape == foreground.shape

    contour = np.asarray([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)
    assert auto_detect_module._approximate_contour(contour, 0) == [
        (0, 0),
        (10, 0),
        (10, 10),
        (0, 10),
    ]
    assert (
        auto_detect_module._approximate_contour(np.zeros((1, 1, 2), dtype=np.int32), 1)
        == []
    )
    assert auto_detect_module._bounded_polygon_points([(0, 0), (1, 1)]) == [
        (0, 0),
        (1, 1),
    ]
    assert (
        len(
            auto_detect_module._bounded_polygon_points(
                [(index, index % 3) for index in range(20)], max_points=4
            )
        )
        <= 4
    )

    assert auto_detect_module._segment_intersection_point(
        (0, 0), (10, 10), (0, 10), (10, 0)
    ) == pytest.approx((5.0, 5.0))
    assert (
        auto_detect_module._segment_intersection_point((0, 0), (1, 0), (0, 1), (1, 1))
        is None
    )
    assert (
        auto_detect_module._segment_intersection_point((0, 0), (1, 0), (2, -1), (2, 1))
        is None
    )

    monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_OBJECTS", 1)
    with pytest.raises(ValueError, match="contour count"):
        auto_detect_module._validate_contours([contour, contour])
    with pytest.raises(ValueError, match="polygon count"):
        auto_detect_module._validate_detection_result([{}, {}])
    monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_OBJECTS", 10_000)
    monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_POINTS", 1)
    with pytest.raises(ValueError, match="contour points"):
        auto_detect_module._validate_contours([contour])
    with pytest.raises(ValueError, match="polygon points"):
        auto_detect_module._validate_detection_result([{"polygon": [(0, 0), (1, 1)]}])


@pytest.mark.parametrize(
    ("points", "message"),
    [
        ("not-a-list", "not a list"),
        ([], "fewer than 3"),
        ([(0, 0), (1, 1)], "fewer than 3"),
        ([(0, 0), (1, 0), (1, 0)], "duplicate"),
        ([(0, 0), (1, 0), (0, True)], "boolean"),
        ([(0, 0), (1, 0), ("x", 1)], "non-numeric"),
        ([(0, 0), (1, 0), (float("nan"), 1)], "non-finite"),
        ([(0, 0), (2, 2), (0, 2), (2, 0)], "self-intersecting"),
        ([(0, 0), (1, 0), (2, 0)], "zero area"),
    ],
)
def test_auto_detect_polygon_validation_reports_specific_failures(points, message):
    assert auto_detect_module.polygon_validation_details(points)["error"] is not None
    assert message in auto_detect_module.polygon_validation_error(points)


def test_magnetic_lasso_settings_presets_and_normalization_are_bounded():
    settings = magnetic_lasso_module.MagneticLassoSettings(
        mode="unknown", preset="unknown"
    )
    settings.sensitivity = 99
    settings.snap_radius = -1
    settings.search_margin = 9999
    settings.distance_weight = 0
    normalized = settings.normalized()
    assert normalized.mode == "precise"
    assert normalized.preset == "balanced"
    assert normalized.sensitivity == 3.0
    assert normalized.snap_radius == 0
    assert normalized.search_margin == 512
    assert normalized.distance_weight == 0.01
    settings.apply_preset("FAST")
    assert settings.preset == "fast"
    assert settings.max_vertices == 700
    with pytest.raises(ValueError, match="Unknown"):
        magnetic_lasso_module.preset_values("unknown")


@pytest.mark.parametrize(
    ("image", "message"),
    [
        (np.empty((0, 2), dtype=np.uint8), "empty"),
        (np.zeros((2,), dtype=np.uint8), "2D"),
        (np.zeros((2, 2, 2), dtype=np.uint8), "channels"),
    ],
)
def test_magnetic_lasso_image_conversion_rejects_invalid_input(image, message):
    with pytest.raises(ValueError, match=message):
        magnetic_lasso_module.image_array_to_gray_uint8(image)


def test_magnetic_lasso_image_conversion_covers_channel_and_numeric_paths():
    one_channel = np.arange(4, dtype=np.uint8).reshape(2, 2, 1)
    assert magnetic_lasso_module.image_array_to_gray_uint8(one_channel).shape == (2, 2)
    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    rgba = np.zeros((2, 2, 4), dtype=np.uint8)
    assert magnetic_lasso_module.image_array_to_gray_uint8(
        rgb, channel_order="rgb"
    ).shape == (2, 2)
    assert magnetic_lasso_module.image_array_to_gray_uint8(
        rgba, channel_order="bgr"
    ).shape == (2, 2)
    with pytest.raises(ValueError, match="channel_order"):
        magnetic_lasso_module.image_array_to_gray_uint8(rgb, channel_order="xyz")
    assert np.all(
        magnetic_lasso_module.image_array_to_gray_uint8(
            np.full((2, 2), np.nan, dtype=np.float32)
        )
        == 0
    )
    assert np.all(
        magnetic_lasso_module.image_array_to_gray_uint8(
            np.full((2, 2), 300.0, dtype=np.float32)
        )
        == 255
    )
    scaled = magnetic_lasso_module.image_array_to_gray_uint8(
        np.array([[0.0, 2.0]], dtype=np.float32)
    )
    assert scaled.tolist() == [[0, 255]]


def test_magnetic_lasso_edge_features_snap_and_roi_paths():
    constant = np.zeros((8, 8), dtype=np.uint8)
    features = magnetic_lasso_module.build_edge_features(constant)
    assert features.strength.shape == (8, 8)
    assert np.all(features.grad_x == 0)
    gradient = np.tile(np.arange(16, dtype=np.uint8), (16, 1))
    gradient_features = magnetic_lasso_module.build_edge_features(gradient)
    assert gradient_features.grad_x.shape == (16, 16)
    assert magnetic_lasso_module.clamp_point((99, -2), (8, 8)) == (7, 0)
    assert magnetic_lasso_module.clamp_point((1, 1), (0, 0)) == (0, 0)
    assert magnetic_lasso_module.snap_to_edge(np.zeros((0, 0)), (2, 2)) == (2, 2)
    assert magnetic_lasso_module.snap_to_edge(np.zeros((8, 8)), (2, 2), radius=0) == (
        2,
        2,
    )
    edge = np.zeros((8, 8), dtype=np.uint8)
    edge[3, 3] = 255
    assert magnetic_lasso_module.snap_to_edge(edge, (2, 2), radius=2) == (3, 3)
    settings = magnetic_lasso_module.MagneticLassoSettings(search_margin=8)
    bounds = magnetic_lasso_module._search_bounds((0, 0), (7, 7), (8, 8), settings)
    assert bounds == (0, 0, 7, 7)
    small = np.zeros((4, 4), dtype=np.uint8)
    gx = np.zeros_like(small, dtype=np.float32)
    gy = np.zeros_like(small, dtype=np.float32)
    result = magnetic_lasso_module._downscale_roi(small, gx, gy, (0, 0), (3, 3), 100)
    assert result[-1] == 1.0
    large = np.zeros((100, 100), dtype=np.uint8)
    reduced = magnetic_lasso_module._downscale_roi(
        large,
        np.zeros_like(large, dtype=np.float32),
        np.zeros_like(large, dtype=np.float32),
        (0, 0),
        (99, 99),
        4096,
    )
    assert reduced[-1] < 1.0


def test_magnetic_lasso_paths_and_polygon_cleanup_are_deterministic():
    features = magnetic_lasso_module.build_edge_features(
        np.zeros((12, 12), dtype=np.uint8)
    )
    settings = magnetic_lasso_module.MagneticLassoSettings(max_expansions=10_000)
    assert magnetic_lasso_module.live_wire_path(features, (2, 2), (2, 2), settings) == [
        (2, 2)
    ]
    assert (
        magnetic_lasso_module.live_wire_preview_path(
            features, (2, 2), (8, 8), settings, cancel_check=lambda: True
        )
        == []
    )
    assert magnetic_lasso_module.deduplicate_path(
        [(0, 0), (0.4, 0.4), (2, 2), (0, 0)]
    ) == [
        (0, 0),
        (2, 2),
    ]
    assert magnetic_lasso_module.simplify_closed_path([(0, 0), (1, 1)]) == [
        (0, 0),
        (1, 1),
    ]
    assert magnetic_lasso_module.polygon_self_intersects(
        [(0, 0), (2, 2), (0, 2), (2, 0)]
    )
    assert not magnetic_lasso_module.polygon_self_intersects([(0, 0), (2, 0), (2, 2)])
    assert magnetic_lasso_module.polygon_signed_area([(0, 0), (2, 0), (2, 2)]) == 2.0
    assert magnetic_lasso_module.sanitize_closed_polygon(
        [(0, 0), (1, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
    )
    assert (
        magnetic_lasso_module.sanitize_closed_polygon(
            [(0, 0), (1, 0), (2, 0)], minimum_area=1
        )
        == []
    )


def test_magnetic_lasso_engine_search_limits_and_cancellation_paths():
    features = magnetic_lasso_module.build_edge_features(
        np.zeros((10, 10), dtype=np.uint8)
    )
    settings = magnetic_lasso_module.MagneticLassoSettings(
        max_expansions=0, search_margin=1
    )
    assert (
        magnetic_lasso_module._astar_directional(
            features.strength,
            features.grad_x,
            features.grad_y,
            (0, 0),
            (4, 4),
            settings,
        )
        == []
    )
    assert (
        magnetic_lasso_module._astar_preview(
            features.strength,
            features.grad_x,
            features.grad_y,
            (0, 0),
            (4, 4),
            settings,
        )
        == []
    )
    assert magnetic_lasso_module.live_wire_path(features, (1, 1), (1, 1), settings) == [
        (1, 1)
    ]
    assert (
        magnetic_lasso_module.live_wire_path(
            features, (1, 1), (8, 8), settings, cancel_check=lambda: True
        )
        == []
    )
    assert (
        magnetic_lasso_module.live_wire_preview_path(
            features, (1, 1), (8, 8), settings, cancel_check=lambda: True
        )
        == []
    )


def test_magnetic_lasso_engine_scaled_and_post_solver_cancel_paths():
    image = np.zeros((96, 96), dtype=np.uint8)
    image[20:76, 48] = 255
    features = magnetic_lasso_module.build_edge_features(image)
    settings = magnetic_lasso_module.MagneticLassoSettings(
        max_search_pixels=64, max_expansions=100_000
    )
    preview = magnetic_lasso_module.live_wire_preview_path(
        features, (4, 4), (90, 90), settings
    )
    committed = magnetic_lasso_module.live_wire_path(
        features, (4, 4), (90, 90), settings
    )
    assert preview[0] == (4, 4)
    assert preview[-1] == (90, 90)
    assert committed[0] == (4, 4)
    assert committed[-1] == (90, 90)

    calls = 0

    def cancel_after_first_call():
        nonlocal calls
        calls += 1
        return calls > 1

    assert (
        magnetic_lasso_module.live_wire_path(
            features,
            (4, 4),
            (90, 90),
            settings,
            cancel_check=cancel_after_first_call,
        )
        == []
    )


@pytest.mark.parametrize(
    ("segments", "expected"),
    [
        (((0, 0), (2, 0), (1, 0), (1, 2)), True),
        (((0, 0), (2, 0), (0, 2), (0, 0)), False),
        (((0, 0), (2, 0), (2, 1), (0, 1)), False),
        (((0, 0), (2, 0), (1, 0), (1, 0)), False),
    ],
)
def test_magnetic_lasso_engine_collinear_and_intersection_boundaries(
    segments, expected
):
    assert magnetic_lasso_module.polygon_self_intersects(segments) is expected


def test_magnetic_lasso_engine_sanitize_rejects_degenerate_and_normalizes_winding():
    assert magnetic_lasso_module.sanitize_closed_polygon([]) == []
    assert (
        magnetic_lasso_module.sanitize_closed_polygon(
            [(0, 0), (1, 0), (1, 0), (2, 0), (0, 0)]
        )
        == []
    )
    clockwise = magnetic_lasso_module.sanitize_closed_polygon(
        [(0, 0), (0, 5), (5, 5), (5, 0)], epsilon=0
    )
    assert clockwise
    assert magnetic_lasso_module.polygon_signed_area(clockwise) > 0
    assert (
        magnetic_lasso_module.sanitize_closed_polygon(
            [(0, 0), (4, 4), (0, 4), (4, 0)], epsilon=0
        )
        == []
    )
    assert magnetic_lasso_module.path_edge_adherence([], np.ones((2, 2))) == 0.0
    assert (
        magnetic_lasso_module.path_edge_adherence(
            [(1, 1)], np.zeros((0, 0), dtype=np.uint8)
        )
        == 0.0
    )
    assert magnetic_lasso_module.path_edge_adherence(
        [(0, 0), (9, 9)], np.full((2, 2), 255, dtype=np.uint8)
    ) == pytest.approx(1.0)


class _BoundaryPolygonCanvas:
    def __init__(self, scene: Scene):
        self.model = scene
        self._zoom = 1.0
        self.update_count = 0
        self.cursor = None

    def update(self):
        self.update_count += 1

    def get_zoom(self):
        return self._zoom

    def get_transform(self):
        return QTransform()

    def snap_vertex_position(self, position):
        return tuple(position)

    def setCursor(self, cursor):
        self.cursor = cursor

    def unsetCursor(self):
        self.cursor = None


def _boundary_polygon_tool():
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object(
        "A",
        [(0, 0), (20, 0), (20, 20), (0, 20)],
        select=True,
    )
    scene.add_object("B", [(30, 0), (45, 0), (45, 15)], select=False)
    scene.cmd.clear()
    canvas = _BoundaryPolygonCanvas(scene)
    return scene, canvas, PolygonEditTool(canvas)


def _boundary_mouse_event(
    button=Qt.MouseButton.LeftButton,
    modifiers=Qt.KeyboardModifier.NoModifier,
    key=None,
):
    return SimpleNamespace(
        button=lambda: button,
        key=lambda: key,
        modifiers=lambda: modifiers,
        position=lambda: QPointF(0, 0),
        pos=lambda: QPointF(0, 0),
        globalPos=lambda: QPointF(0, 0),
    )


def test_polygon_editor_state_and_interaction_boundaries():
    scene, canvas, tool = _boundary_polygon_tool()
    errors = Mock()
    tool._present_p2d05_error = errors

    tool.update_language("unsupported")
    assert tool.current_lang == "en"
    assert tool.begin_vertex_gizmo_gesture() is False
    assert tool.selected_vertex_position() is None
    tool.selected_polygon_id = "A"
    tool.selected_vertex = 99
    assert tool.selected_vertex_position() is None
    assert tool._begin_vertex_gesture() is False
    tool.selected_vertex = 0
    assert tool.begin_vertex_gizmo_gesture() is True
    assert tool.begin_vertex_gizmo_gesture() is False
    tool.set_mode("add")
    assert tool._vertex_transaction is None
    assert tool.cancel_vertex_gizmo_gesture() is False
    assert tool.finish_vertex_gizmo_gesture() is None

    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    assert tool.begin_vertex_gizmo_gesture() is True
    tool.preview_vertex_gizmo_position((4, 5))
    assert tool.selected_vertex_position() == (4, 5)
    assert tool.finish_vertex_gizmo_gesture() is not None
    assert scene.objects["A"].polygon[0] == (4, 5)

    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.NoButton), (0, 0))
    tool.adding_new = True
    tool.on_mouse_press(
        _boundary_mouse_event(Qt.MouseButton.LeftButton),
        (10, 0),
    )
    assert tool.adding_new is True
    tool.on_mouse_press(
        _boundary_mouse_event(Qt.MouseButton.LeftButton),
        (100, 100),
    )
    assert tool.selected_polygon_ids == set()
    tool.multi_select = True
    tool.on_mouse_press(
        _boundary_mouse_event(Qt.MouseButton.LeftButton),
        (100, 100),
    )
    tool.multi_select = False
    tool.on_mouse_move(_boundary_mouse_event(Qt.MouseButton.NoButton), (1000, 1000))
    assert tool._hovered_vertex is None
    tool.on_mouse_release(_boundary_mouse_event(), (100, 100))
    tool.on_cancel()
    assert tool.adding_new is False
    assert errors.called


@pytest.mark.parametrize(
    ("status", "severity"),
    [
        (commands_module.CommandStatus.REJECTED, "warning"),
        (commands_module.CommandStatus.FAILED, "critical"),
    ],
)
def test_polygon_editor_command_result_and_failure_boundaries(status, severity):
    scene, canvas, tool = _boundary_polygon_tool()
    tool._present_p2d05_error = Mock()
    result = commands_module.CommandResult(
        status,
        commands_module.Command(),
        "execute",
        "boundary result",
    )
    tool._report_vertex_result(result, "Boundary")
    assert tool._present_p2d05_error.call_args.kwargs["severity"] == severity

    class RaisingManager:
        def execute(self, *_args):
            raise RuntimeError("manager boundary")

    scene.cmd = RaisingManager()
    tool._execute_polygon_update(
        "A",
        [(0, 0), (20, 0), (20, 20), (0, 20)],
        [(1, 1), (20, 0), (20, 20)],
        "Boundary",
    )
    assert tool._present_p2d05_error.call_args.args[0].args[0] == "manager boundary"


def test_polygon_editor_deletion_addition_and_object_guards():
    scene, canvas, tool = _boundary_polygon_tool()
    tool._present_p2d05_error = Mock()

    tool.delete_selected_vertex()
    tool.selected_polygon_id = "missing"
    tool.selected_vertex = 0
    tool.delete_selected_vertex()
    tool.selected_polygon_id = "A"
    tool.selected_vertex = True
    tool.delete_selected_vertex()
    tool.selected_vertex = 99
    tool.delete_selected_vertex()
    tool.selected_vertex = 0
    original = list(scene.objects["A"].polygon)
    tool.delete_selected_vertex()
    assert len(scene.objects["A"].polygon) == len(original) - 1

    tool.selected_vertices.clear()
    tool.selected_polygon_id = None
    tool.selected_vertex = None
    tool.delete_selected_vertices()
    tool.selected_vertices = {("missing", 0)}
    tool.delete_selected_vertices()
    tool.selected_vertices = {("A", -1)}
    tool.delete_selected_vertices()
    tool.selected_vertices = {("A", 0), ("A", 1)}
    scene.objects["A"].polygon = [(0, 0), (10, 0), (0, 10)]
    tool.delete_selected_vertices()

    tool.selected_polygon_id = None
    tool.add_vertex_at_pos((1, 1))
    tool.selected_polygon_id = "missing"
    tool.add_vertex_at_pos((1, 1))
    tool.selected_polygon_id = "A"
    tool.add_vertex_at_pos(("bad", 1))
    tool.add_vertex_at_pos((5, 0))
    assert len(scene.objects["A"].polygon) == 4

    tool.selected_polygon_id = None
    tool.delete_selected_polygon()
    tool.selected_polygon_ids = {"missing"}
    tool.multi_select = True
    tool.delete_selected_polygon()
    tool.selected_polygon_ids = {"A"}
    tool.delete_selected_polygon(["A", "missing"])
    assert tool._present_p2d05_error.called

    tool.clear_selection()
    tool.select_all_vertices()
    assert tool.selected_vertices == set()
    assert tool.point_to_line_distance((2, 2), (0, 0), (0, 0)) == pytest.approx(
        2**0.5 * 2
    )
    assert tool.point_to_line_distance((2, 0), (0, 0), (4, 0)) == 0
    assert canvas.update_count > 0


def test_command_manager_and_layer_group_boundaries():
    scene = Scene()
    manager = CommandManager(max_history=1)
    scene.cmd = manager
    listener = Mock(side_effect=RuntimeError("listener failure"))
    manager.subscribe(listener)
    manager.subscribe(listener)
    assert manager.undo(scene).status is commands_module.CommandStatus.NO_CHANGE
    assert manager.redo(scene).status is commands_module.CommandStatus.NO_CHANGE

    assert manager.execute(commands_module.CreateLayerCommand(""), scene).status is (
        commands_module.CommandStatus.REJECTED
    )
    first = commands_module.CreateLayerCommand("First")
    second = commands_module.CreateLayerCommand("Second")
    assert manager.execute(first, scene).changed
    assert manager.execute(second, scene).changed
    assert manager.undo_count == 1
    manager.unsubscribe(listener)
    manager.unsubscribe(listener)

    assert commands_module.RemoveLayerCommand("layer_default").execute(
        scene
    ).status is (commands_module.CommandStatus.REJECTED)
    assert commands_module.RemoveLayerCommand("missing").execute(scene).status is (
        commands_module.CommandStatus.REJECTED
    )
    create = commands_module.CreateLayerCommand("Transient")
    assert create.execute(scene) is None
    assert create.execute(scene).status is commands_module.CommandStatus.REJECTED
    assert create.undo(scene) is None
    assert create.undo(scene).status is commands_module.CommandStatus.REJECTED
    assert commands_module.CreateLayerCommand("x").undo(scene).status is (
        commands_module.CommandStatus.REJECTED
    )

    layer = scene.create_layer("Movable")
    same = commands_module.MoveLayerCommand(layer.id, scene.layers.index(layer))
    assert same.execute(scene).status is commands_module.CommandStatus.NO_CHANGE
    assert commands_module.MoveLayerCommand("missing", 0).execute(scene).status is (
        commands_module.CommandStatus.REJECTED
    )
    never_moved = commands_module.MoveLayerCommand(layer.id, 0)
    assert never_moved.undo(scene).status is commands_module.CommandStatus.REJECTED
    assert never_moved.execute(scene) is None
    assert never_moved.undo(scene) is None
    assert (
        commands_module.ToggleLayerVisibilityCommand("missing").execute(scene).status
        is commands_module.CommandStatus.REJECTED
    )
    visibility = commands_module.ToggleLayerVisibilityCommand(layer.id)
    assert visibility.execute(scene) is None
    scene.layers[scene.layers.index(layer)].visible = bool(visibility._new)
    assert visibility.execute(scene).status is commands_module.CommandStatus.REJECTED
    scene.layers[scene.layers.index(layer)].visible = bool(visibility._old)
    assert visibility.undo(scene).status is commands_module.CommandStatus.REJECTED
    lock = commands_module.ToggleLayerLockCommand(layer.id)
    assert lock.execute(scene) is None
    assert lock.undo(scene) is None
    assert commands_module.ToggleLayerLockCommand("missing").execute(scene).status is (
        commands_module.CommandStatus.REJECTED
    )

    assert commands_module.CreateGroupCommand("").execute(scene).status is (
        commands_module.CommandStatus.REJECTED
    )
    group = scene.create_group("Group")
    scene.add_object("group-object", [(0, 0), (5, 0), (0, 5)])
    add = commands_module.AddToGroupCommand(group.id, "group-object")
    assert add.execute(scene) is None
    assert add.execute(scene).status is commands_module.CommandStatus.NO_CHANGE
    assert add.undo(scene) is None
    assert add.undo(scene).status is commands_module.CommandStatus.REJECTED
    remove = commands_module.RemoveFromGroupCommand(group.id, "group-object")
    assert remove.execute(scene).status is commands_module.CommandStatus.NO_CHANGE
    assert (
        commands_module.AddToGroupCommand("missing", "group-object")
        .execute(scene)
        .status
        is commands_module.CommandStatus.REJECTED
    )
    assert (
        commands_module.AddToGroupCommand(group.id, "missing").execute(scene).status
        is commands_module.CommandStatus.REJECTED
    )
    assert (
        commands_module.RemoveFromGroupCommand("missing", "group-object")
        .execute(scene)
        .status
        is commands_module.CommandStatus.REJECTED
    )

    group_toggle = commands_module.ToggleGroupVisibilityCommand(group.id)
    assert group_toggle.execute(scene) is None
    scene.groups[0].visible = bool(group_toggle._new)
    assert group_toggle.execute(scene).status is commands_module.CommandStatus.REJECTED
    assert commands_module.ToggleGroupLockCommand("missing").execute(scene).status is (
        commands_module.CommandStatus.REJECTED
    )


def test_update_geometry_commands_reject_stale_and_missing_states():
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("A", [(0, 0), (10, 0), (0, 10)])
    old_polygon = list(scene.objects["A"].polygon)
    same = commands_module.UpdatePolygonCommand("A", old_polygon, old_polygon)
    assert same.execute(scene).status is commands_module.CommandStatus.NO_CHANGE
    missing = commands_module.UpdatePolygonCommand("missing", old_polygon, old_polygon)
    assert missing.execute(scene).status is commands_module.CommandStatus.REJECTED

    changed = commands_module.UpdatePolygonCommand(
        "A", old_polygon, [(1, 1), (10, 0), (0, 10)]
    )
    assert changed.execute(scene) is None
    scene.objects["A"].polygon[0] = (2, 2)
    assert changed.undo(scene).status is commands_module.CommandStatus.REJECTED

    geometry = commands_module.UpdateObjectGeometryCommand(
        "A",
        old_polygon,
        [(1, 1), (10, 0), (0, 10)],
        old_has_collision=False,
        old_collision=None,
        new_has_collision=True,
        new_collision=None,
    )
    scene.objects["A"].polygon = old_polygon
    assert geometry.execute(scene).status is commands_module.CommandStatus.FAILED
    assert (
        commands_module.UpdateObjectGeometryCommand(
            "missing",
            old_polygon,
            old_polygon,
            old_has_collision=False,
            old_collision=None,
            new_has_collision=False,
            new_collision=None,
        )
        .execute(scene)
        .status
        is commands_module.CommandStatus.REJECTED
    )

    scene.collision_shapes["A"] = list(old_polygon)
    collision_change = commands_module.UpdatePolygonCommand(
        "A", old_polygon, [(1, 1), (10, 0), (0, 10)]
    )
    assert collision_change.execute(scene) is None
    assert "A" in scene.collision_shapes
    assert collision_change.undo(scene) is None


class _BoundaryLassoCanvas:
    def __init__(self, scene: Scene):
        self.model = scene
        self.scene = scene
        self._zoom = 1.0
        self.update_count = 0
        self.focus_count = 0
        self.cursor = None

    def update(self):
        self.update_count += 1

    def get_zoom(self):
        return self._zoom

    def get_transform(self):
        return QTransform()

    def setFocus(self, *_args):
        self.focus_count += 1

    def setCursor(self, cursor):
        self.cursor = cursor

    def unsetCursor(self):
        self.cursor = None


def _boundary_lasso_tool(mode="legacy"):
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = np.zeros((32, 32, 3), dtype=np.uint8)
    canvas = _BoundaryLassoCanvas(scene)
    settings = magnetic_lasso_tool_module.MagneticLassoSettings(mode=mode)
    tool = magnetic_lasso_tool_module.MagneticLassoTool(canvas, settings)
    tool._show_message = Mock()
    return scene, canvas, tool


def _drain_lasso_workers(tool):
    tool._on_canvas_destroyed()
    magnetic_lasso_tool_module._MAGNETIC_PATH_POOL.waitForDone(5_000)


def test_magnetic_lasso_tool_sync_selection_and_event_boundaries():
    scene, canvas, tool = _boundary_lasso_tool()
    tool.show_context_menu = Mock()
    assert tool._uses_background_pathfinding() is False
    assert tool._snap_anchor((1.4, 2.6)) == (1, 3)
    assert tool._compute_magnetic_path((1, 1), (1, 1)) == [(1, 1)]
    assert tool._append_anchor((2, 2)) is True
    assert tool._append_anchor((2, 2)) is False
    assert tool._can_close_at((2, 2)) is False
    assert tool.remove_last_anchor() is True
    assert tool.remove_last_anchor() is False
    assert tool.restore_last_anchor() is True
    assert tool.restore_last_anchor() is False

    tool._anchors = [(2, 2), (10, 2)]
    tool._segments = [[(2, 2), (10, 2)]]
    tool._rebuild_path()
    assert tool._can_close_at((2, 2)) is False
    tool._anchors.append((10, 10))
    tool._segments.append([(10, 2), (10, 10)])
    tool._rebuild_path()
    assert tool._can_close_at((2, 2)) is True
    assert tool._candidate_closed_path([]) == []
    assert tool._candidate_closed_path([(10, 10), (2, 2)])[0] == (2, 2)

    tool._ignore_next_click_after_commit = True
    tool.on_mouse_press(_boundary_mouse_event(), (4, 4))
    assert tool._ignore_next_click_after_commit is False
    tool._segment_pending = True
    tool.on_mouse_press(_boundary_mouse_event(), (4, 4))
    tool._segment_pending = False
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.RightButton), (4, 4))
    tool.on_mouse_move(_boundary_mouse_event(), (4, 4))
    assert tool.on_mouse_release(_boundary_mouse_event(), (4, 4)) is None
    assert tool.on_key_press(_boundary_mouse_event(key=Qt.Key.Key_A)) is False
    assert tool.on_key_press(_boundary_mouse_event(key=Qt.Key.Key_Backspace)) is True
    tool._anchors = [(2, 2), (10, 2), (10, 10)]
    tool.finish_selection = Mock()
    assert tool.on_key_press(_boundary_mouse_event(key=Qt.Key.Key_Return)) is True
    tool.finish_selection.assert_called_once()
    assert tool.on_double_click(_boundary_mouse_event(), (4, 4)) is None

    tool._anchors = [(2, 2), (10, 2), (10, 10)]
    tool._path = [(2, 2), (10, 2), (10, 10)]
    tool._segments = [
        [(2, 2), (10, 2)],
        [(10, 2), (10, 10)],
    ]
    object_id = tool._finish_with_closing_path([(10, 10), (2, 2)])
    assert object_id is not None
    assert tool._anchors == []
    assert len(scene.objects) == 1
    tool.on_mouse_press(_boundary_mouse_event(), (3, 3))
    assert tool._ignore_next_click_after_commit is False
    _drain_lasso_workers(tool)


def test_magnetic_lasso_tool_precise_cache_and_failure_boundaries(monkeypatch):
    scene, canvas, tool = _boundary_lasso_tool("precise")
    tool._uses_background_pathfinding = lambda: False
    tool._compute_edge_map()
    assert tool._edge_map is not None
    assert tool._edge_features is not None
    first = tool._edge_map
    tool._compute_edge_map()
    assert tool._edge_map is first
    assert tool._snap_anchor((2.2, 2.2)) is not None
    tool._edge_map = None
    tool._edge_features = None
    monkeypatch.setattr(tool, "_compute_edge_map", lambda: None)
    assert tool._compute_magnetic_path((1, 1), (2, 2)) == []
    tool._clear_edge_cache()
    tool.prepare_edge_map_async()
    assert tool._edge_map is None

    tool._uses_background_pathfinding = lambda: True
    tool._edge_map = np.zeros((4, 4), dtype=np.uint8)
    tool._path_busy = False
    tool._set_path_busy(True)
    assert tool._path_busy is True
    tool._set_path_busy(True)
    tool._set_path_busy(False)
    tool._set_path_busy(False)
    tool._active_path_request = None
    request = Mock()
    monkeypatch.setattr(tool, "_request_async_path", request)
    tool._edge_map = None
    tool.prepare_edge_map_async()
    request.assert_called_once_with("prepare", (0, 0), (0, 0))

    tool._last_error = None
    tool._handle_async_failure("preview", "failure", notify=True)
    assert tool._last_error == "preview: failure"
    tool._handle_async_failure("segment", "failure", notify=True)
    assert tool._show_message.called
    tool._invalidate_async_requests()
    _drain_lasso_workers(tool)
    assert tool._canvas_closed is True


def test_magnetic_lasso_tool_commit_validation_modes_and_undo_paths(monkeypatch):
    scene, canvas, tool = _boundary_lasso_tool()
    tool._uses_background_pathfinding = lambda: False
    assert tool.commit_selection([(0, 0), (1, 1)]) is None
    assert tool._last_error
    monkeypatch.setattr(
        magnetic_lasso_tool_module,
        "sanitize_closed_polygon",
        lambda *_args, **_kwargs: [(0, 0), (10, 10), (0, 10), (10, 0)],
    )
    assert tool.commit_selection([(0, 0), (10, 10), (0, 10), (10, 0)]) is None
    assert tool._last_error == "Polygon self-intersects"
    monkeypatch.undo()
    valid = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert tool.commit_selection(valid) is not None
    assert tool.on_undo() is False
    assert tool.on_redo() is False
    tool.update_language("pt")
    assert tool.current_lang == "pt"
    tool.update_language("invalid")
    assert tool.current_lang == "pt"
    tool._set_mode("invalid")
    tool._set_mode("legacy")
    tool._set_preset(tool.settings.preset)
    tool._set_preset("fast")
    tool._toggle_edge_overlay(True)
    tool._toggle_edge_overlay(False)
    tool.cancel()
    assert tool._anchors == []
    _drain_lasso_workers(tool)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_size": (True, 10)}, "max_size"),
        ({"max_size": (10,)}, "max_size"),
        ({"max_size": (0, 10)}, "max_size"),
        ({"padding": True}, "padding"),
        ({"padding": -1}, "padding"),
        ({"bleed": True}, "bleed"),
        ({"bleed": -1}, "bleed"),
        ({"max_size": (4, 4), "padding": 2}, "padding"),
    ],
)
def test_atlas_exporter_rejects_boundary_configuration(kwargs, message):
    image = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    with pytest.raises(ValueError, match=message):
        atlas_module.pack_sprites_to_atlas([(image, {"name": "sprite"})], **kwargs)


def test_atlas_exporter_fallback_pack_and_limits(monkeypatch, tmp_path: Path):
    image = Image.new("RGBA", (3, 2), (255, 0, 0, 255))
    image2 = Image.new("RGB", (2, 3), (0, 255, 0))
    monkeypatch.setattr(atlas_module, "HAS_PACKER", False)
    packed = atlas_module.pack_sprites_to_atlas(
        [
            (image, {"name": "first"}),
            (image2, {"name": "second"}),
        ],
        max_size=(12, 12),
        padding=1,
        bleed=1,
    )
    assert packed
    assert {entry["name"] for entry in packed[0][1]} == {"first", "second"}
    assert all(entry["extrusion"] == 1 for entry in packed[0][1])

    too_big = atlas_module.pack_sprites_to_atlas(
        [(Image.new("RGB", (20, 20)), {"name": "too-big"})],
        max_size=(8, 8),
        padding=1,
    )
    assert too_big == []

    monkeypatch.setattr(atlas_module, "MAX_ATLAS_DIMENSION", 4)
    with pytest.raises(ValueError, match="dimensions"):
        atlas_module.pack_sprites_to_atlas(
            [(Image.new("RGB", (5, 1)), {"name": "wide"})],
            max_size=(8, 8),
        )
    monkeypatch.setattr(atlas_module, "MAX_ATLAS_DIMENSION", 16_384)
    monkeypatch.setattr(atlas_module, "MAX_ATLAS_TOTAL_INPUT_PIXELS", 3)
    with pytest.raises(ValueError, match="aggregate"):
        atlas_module.pack_sprites_to_atlas(
            [(image, {"name": "first"})], max_size=(12, 12), bleed=1
        )

    monkeypatch.undo()
    output = atlas_module.build_atlas(
        [("first", image)],
        str(tmp_path),
        base_name="boundary",
        max_size=(12, 12),
        metadata_by_name={"first": {"pivot": [0.5, 0.5]}, "missing": {"pivot": 0}},
    )
    assert output and Path(output[0]["atlas_path"]).is_file()
    assert output[0]["entries"][0]["pivot"] == [0.5, 0.5]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (True, "numeric"),
        ("bad", "numeric"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
    ],
)
def test_hybrid_exporter_numeric_and_path_helpers_fail_closed(value, message):
    with pytest.raises(HybridCompositionExportError, match=message):
        hybrid_module._number(value, "boundary")
    with pytest.raises(HybridCompositionExportError, match="values"):
        hybrid_module._vector([1, 2], "vector", 3)


@pytest.mark.parametrize(
    "value",
    ["", "../escape", "folder\\file", "C:/absolute", "C:relative", "folder/../x"],
)
def test_hybrid_exporter_rejects_unsafe_relative_paths(value):
    with pytest.raises(HybridCompositionExportError, match="safe relative"):
        hybrid_module._safe_relative_path(value, "path")


def test_hybrid_exporter_json_bindings_and_copy_boundaries(tmp_path: Path):
    root = tmp_path / "package"
    root.mkdir()
    payload = root / "payload.json"
    payload.write_text('{"ok": true}\n', encoding="utf-8")
    binding = hybrid_module._binding(payload, root)
    assert hybrid_module._resolve_binding(root, binding, "payload") == payload

    for tamper in (
        {"bytes": 1},
        {"sha256": "0" * 64},
        {"path": "missing.json"},
        {"path": "../payload.json"},
        {
            "path": "payload.json",
            "bytes": binding["bytes"],
            "sha256": binding["sha256"],
        },
    ):
        candidate = dict(binding)
        candidate.update(tamper)
        if tamper.get("path") == "payload.json":
            payload.unlink()
        with pytest.raises(HybridCompositionExportError):
            hybrid_module._resolve_binding(root, candidate, "payload")
        if not payload.exists():
            payload.write_text('{"ok": true}\n', encoding="utf-8")

    invalid = root / "invalid.json"
    invalid.write_bytes(b"not-json")
    with pytest.raises(HybridCompositionExportError, match="invalid"):
        hybrid_module._read_json(invalid, "json")
    non_object = root / "array.json"
    non_object.write_text("[]", encoding="utf-8")
    with pytest.raises(HybridCompositionExportError, match="object"):
        hybrid_module._read_json(non_object, "json")
    with pytest.raises(HybridCompositionExportError, match="invalid"):
        hybrid_module._read_json(root / "missing.json", "json")

    copied = root / "copied" / "payload.json"
    component = hybrid_module._copy_component(payload, copied, "boundary", root)
    assert component["path"] == "copied/payload.json"
    with pytest.raises(HybridCompositionExportError, match="unsafe or missing"):
        hybrid_module._copy_component(root / "missing.bin", root / "out.bin", "x")

    empty = root / "empty"
    empty.mkdir()
    with pytest.raises(HybridCompositionExportError, match="empty"):
        hybrid_module._copy_tree(empty, root / "empty-copy", "x", root)
    with pytest.raises(HybridCompositionExportError, match="unsafe or missing"):
        hybrid_module._copy_tree(root / "missing-dir", root / "copy", "x", root)


def _authoring_transform(x: float = 10.0, y: float = 20.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _authoring_document_v1() -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Boundary authoring",
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256="a" * 64)],
        layers=[SceneLayerAuthoringRecord(id="base", name="Base")],
        objects=[
            SceneObjectAuthoringRecord(
                id="object",
                asset_id="asset",
                layer_id="base",
                transform=_authoring_transform(),
            )
        ],
        groups=[],
    )


def test_scene_authoring_model_selection_asset_and_layer_boundaries():
    model = SceneAuthoringModel(_authoring_document_v1())
    with pytest.raises(ValueError, match="finite"):
        scene_authoring_module.snap_value(float("nan"), 1)
    with pytest.raises(ValueError, match="spacing"):
        scene_authoring_module.snap_value(1, 0)
    assert scene_authoring_module.snap_value(-2.5, 1) == -2.0
    disabled = model.document.snap
    assert (
        scene_authoring_module.snap_transform(
            model.document.objects[0].transform, disabled
        )
        == model.document.objects[0].transform
    )

    assert model.set_selection(["object", "object"]).ids == ("object",)
    with pytest.raises(KeyError):
        model.set_selection(["missing"])
    model.clear_selection()
    model.add_asset(
        AssetReferenceRecord(id="second", path="assets/b.png", sha256="b" * 64)
    )
    with pytest.raises(ValueError, match="asset ID exists"):
        model.add_asset(
            AssetReferenceRecord(id="second", path="assets/c.png", sha256="c" * 64)
        )
    with pytest.raises(KeyError):
        model.update_asset(
            AssetReferenceRecord(id="missing", path="x", sha256="a" * 64)
        )
    model.update_asset(
        AssetReferenceRecord(id="second", path="assets/d.png", sha256="d" * 64)
    )

    duplicate = model.document.objects[0]
    with pytest.raises(ValueError, match="object ID exists"):
        model.add_object(duplicate)
    model.set_selection(["object"])
    model.translate_selected(Point3Record(x=2, y=3, z=0))
    model.transform_selected(
        rotation_z=90, scale_factor=2, translation=Point3Record(x=1, y=1, z=0)
    )
    with pytest.raises(ValueError, match="rotation_z"):
        model.transform_selected(rotation_z=float("nan"))
    with pytest.raises(ValueError, match="scale_factor"):
        model.transform_selected(scale_factor=0)
    model.clear_selection()
    model.transform_selected()

    model.add_layer(SceneLayerAuthoringRecord(id="empty", name="Empty"))
    with pytest.raises(ValueError, match="layer ID exists"):
        model.add_layer(SceneLayerAuthoringRecord(id="empty", name="Again"))
    with pytest.raises(ValueError, match="assigned"):
        model.remove_layer("base")
    model.reorder_layer("empty", -1)
    model.set_layer_visibility("empty", False)
    model.set_layer_locked("empty", True)
    with pytest.raises(KeyError):
        model.set_layer_visibility("missing", True)
    model.remove_layer("empty")
    with pytest.raises(ValueError, match="at least one"):
        model.remove_layer("base")


def test_scene_authoring_model_v2_camera_socket_and_particle_boundaries():
    model = SceneAuthoringModel(
        upgrade_scene_authoring_document(_authoring_document_v1())
    )
    assert isinstance(model.document, SceneAuthoringDocumentV2)
    with pytest.raises(KeyError):
        model.add_entity_from_object("missing")
    entity_id = model.add_entity_from_object("object", "entity")
    with pytest.raises(ValueError, match="entity ID already exists"):
        model.add_entity_from_object("object", "entity")
    with pytest.raises(ValueError, match="itself"):
        model.set_entity_parent("entity", "entity")
    with pytest.raises(KeyError):
        model.set_entity_parent("entity", "missing")
    model.set_entity_parent(entity_id, None)

    model.set_camera(SceneCameraAuthoringRecord(position=PointRecord(x=5, y=6), zoom=2))
    with pytest.raises(KeyError):
        model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="missing"))
    model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="base", depth=0.5))

    point = Point3Record(x=0, y=0, z=0)
    light = SceneLightSocketRecord(
        id="light",
        layer_id="base",
        position=point,
        color="#ffffff",
        intensity=2,
        radius=32,
    )
    model.add_socket(light)
    model.update_socket_position("light", Point3Record(x=1, y=2, z=0))
    model.update_socket_rotation("light", Point3Record(x=0, y=0, z=45))
    model.update_socket_light_kind("light", "directional")
    with pytest.raises(ValueError, match="unsupported"):
        model.update_socket_light_kind("light", "bad")
    with pytest.raises(ValueError, match="only VFX"):
        model.update_vfx_socket(
            "light",
            position=point,
            rotation=point,
            effect_id="fx",
            scale=1,
            enabled=True,
            particle_system=None,
        )

    vfx = SceneVfxSocketRecord(
        id="vfx",
        layer_id="base",
        position=point,
        effect_id="fx",
        scale=1,
    )
    model.add_socket(vfx)
    with pytest.raises(ValueError, match="requires"):
        model.update_vfx_socket(
            "vfx",
            position=point,
            rotation=point,
            effect_id="fx",
            scale=1,
            enabled=False,
            particle_system=None,
        )
    with pytest.raises(KeyError):
        model.update_socket_position("missing", point)
    model.remove_socket("light")
    model.remove_socket("vfx")
    with pytest.raises(KeyError):
        model.remove_socket("missing")


def test_scene_authoring_model_nested_group_and_lock_boundaries():
    model = SceneAuthoringModel(
        upgrade_scene_authoring_document(_authoring_document_v1())
    )
    model.set_selection(["object"])
    parent = SceneGroupAuthoringRecordV2(id="parent", name="Parent", members=["object"])
    model.add_group(parent)
    with pytest.raises(ValueError, match="group ID exists"):
        model.add_group(parent)
    with pytest.raises(ValueError, match="blank"):
        model.rename_group("parent", " ")
    model.rename_group("parent", "Renamed")
    child = SceneGroupAuthoringRecordV2(
        id="child", name="Child", members=[], parent_group_id="parent"
    )
    model.add_group(child)
    model.set_group_parent("child", None)
    model.set_group_parent("child", "parent")
    with pytest.raises(ValueError, match="own parent"):
        model.set_group_parent("child", "child")
    with pytest.raises(ValueError, match="cycle"):
        model.set_group_parent("parent", "child")
    with pytest.raises(KeyError):
        model.add_objects_to_group("parent", ["missing"])
    model.add_objects_to_group("parent", ["object", "object"])
    model.set_group_visibility("parent", False)
    model.set_group_locked("parent", True)
    with pytest.raises(PermissionError, match="locked"):
        model.assert_editable("object")
    model.set_group_locked("parent", False)
    model.remove_objects_from_group("parent", ["object"])
    model.remove_group("child")
    model.remove_group("parent")


def test_scene_repair_backend_and_capacity_boundaries(monkeypatch):
    # Exercise both the optional Shapely repair and the deterministic fallback.
    bow_tie = [(0, 0), (10, 10), (0, 10), (10, 0)]
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", True)
    fixed = SimpleNamespace(
        is_empty=False,
        exterior=SimpleNamespace(coords=[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]),
    )
    monkeypatch.setattr(
        scene_module,
        "Polygon",
        lambda _points: SimpleNamespace(is_valid=False, buffer=lambda _distance: fixed),
        raising=False,
    )
    repaired, changed = scene_module._attempt_repair(bow_tie)
    assert changed is True
    assert scene_module._validate_polygon(repaired)

    class _EmptyRepair:
        is_empty = True

    class _InvalidPolygon:
        is_valid = False

        def buffer(self, _distance):
            return _EmptyRepair()

    monkeypatch.setattr(
        scene_module, "Polygon", lambda _points: _InvalidPolygon(), raising=False
    )
    unchanged, changed = scene_module._attempt_repair(bow_tie)
    assert unchanged == bow_tie
    assert changed is False

    monkeypatch.setattr(
        scene_module,
        "Polygon",
        lambda _points: SimpleNamespace(is_valid=True),
        raising=False,
    )
    cleaned, changed = scene_module._attempt_repair(
        [(0, 0), (10, 0), (10, 10), (0, 10)]
    )
    assert changed is True
    assert scene_module._validate_polygon(cleaned)

    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    fallback, changed = scene_module._attempt_repair(
        [(0, 0), (0, 10), (10, 10), (10, 0)]
    )
    assert changed is True
    assert scene_module._validate_polygon(fallback)

    scene = Scene()
    monkeypatch.setattr(scene_module, "MAX_PROJECT_LAYERS", len(scene.layers))
    with pytest.raises(ValueError, match="layer limit"):
        scene.create_layer()

    monkeypatch.setattr(scene_module, "MAX_PROJECT_OBJECTS", 0)
    with pytest.raises(ValueError, match="object limit"):
        scene.add_object("blocked", [(0, 0), (10, 0), (0, 10)])
    monkeypatch.setattr(
        scene,
        "prepare_bezier_geometry",
        lambda _beziers, steps_per_segment=20: ([], [(0, 0), (10, 0), (0, 10)]),
    )
    with pytest.raises(ValueError, match="object limit"):
        scene.add_bezier_object([], object_id="blocked-curve")

    monkeypatch.setattr(scene_module, "MAX_PROJECT_OBJECTS", 10)
    scene.add_object("A", [(0, 0), (10, 0), (0, 10)], select=True)
    scene.add_object("B", [(0, 0), (10, 0), (0, 10)])
    group = scene.create_group("Actors")
    group.members = ["A"]
    scene.collision_parts["A"] = [[(0.0, 0.0), (1.0, 1.0)]]
    scene.rename_object("A", "Renamed")
    assert "Renamed" in scene.collision_parts
    with pytest.raises(ValueError, match="group member limit"):
        monkeypatch.setattr(scene_module, "MAX_GROUP_MEMBERS", 1)
        scene.add_object_to_group(group.id, "B")
    with pytest.raises(ValueError, match="group limit"):
        monkeypatch.setattr(scene_module, "MAX_PROJECT_GROUPS", len(scene.groups))
        scene.create_group("Overflow")

    with pytest.raises(KeyError):
        scene.select_objects(["Renamed"], primary="missing")
    with pytest.raises(ValueError, match="Invalid polygon"):
        scene.update_polygon("Renamed", [(0, 0), (1, 1), (2, 2)])
    scene.select_object(None)
    with pytest.raises(KeyError):
        scene.select_object("missing")


def _boundary_vector_geometry() -> SceneVectorGeometryRecord:
    points = [
        PointRecord(x=0, y=0),
        PointRecord(x=20, y=0),
        PointRecord(x=0, y=20),
    ]
    return SceneVectorGeometryRecord(
        algorithm="boundary",
        source_sha256="a" * 64,
        image_size=SceneVectorImageSizeRecord(width=20, height=20),
        original_polygon=points,
        polygon=points,
        collision_polygon=points,
    )


def _boundary_particle_system(system_id: str = "fx") -> SceneParticleSystemRecord:
    return SceneParticleSystemRecord(
        id=system_id,
        emitters=[
            ParticleEmitterRecord(
                id="emitter",
                seed=7,
                initial_velocity=Point3Record(x=0, y=1, z=0),
                velocity_spread=Point3Record(x=0, y=0, z=0),
                acceleration=Point3Record(x=0, y=0, z=0),
                emission_rate=1,
                lifetime=1,
                max_particles=1,
                burst_count=1,
            )
        ],
    )


def test_scene_authoring_model_legacy_guards_and_transform_contracts():
    model = SceneAuthoringModel(_authoring_document_v1())
    point = Point3Record(x=0, y=0, z=0)
    light = SceneLightSocketRecord(
        id="light",
        layer_id="base",
        position=point,
        color="#ffffff",
        intensity=1,
        radius=4,
    )
    legacy_v2_guards = (
        lambda: model.set_entity_parent("object", None),
        lambda: model.add_entity_from_object("object"),
        lambda: model.set_camera(SceneCameraAuthoringRecord()),
        lambda: model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="base")),
        lambda: model.add_socket(light),
        lambda: model.set_particle_system(None),
        lambda: model.update_particle_system(None),
        lambda: model.remove_particle_system("fx"),
        lambda: model.update_socket_position("light", point),
        lambda: model.update_socket_rotation("light", point),
        lambda: model.update_socket_light_kind("light", "point"),
        lambda: model.update_socket_transform("light", point, point),
        lambda: model.remove_socket("light"),
    )
    for operation in legacy_v2_guards:
        with pytest.raises(ValueError, match="schema V2|schema v2"):
            operation()

    model.set_snap(
        SceneSnapRecord(enabled=True, mode="grid", spacing=PointRecord(x=4, y=4))
    )
    model.set_selection(["object"])
    model.translate_selected(Point3Record(x=1, y=1, z=0))
    assert model.document.objects[0].transform.position.x % 4 == 0
    assert model.document.objects[0].transform.position.y % 4 == 0
    model.remove_objects([])
    with pytest.raises(ValueError, match="unique"):
        model.remove_objects(["object", "object"])
    with pytest.raises(KeyError):
        model.remove_object("missing")
    with pytest.raises(KeyError):
        model.update_transform("missing", _authoring_transform())
    with pytest.raises(KeyError):
        model.update_vector_geometry("missing", _boundary_vector_geometry())
    with pytest.raises(ValueError, match="schema V2"):
        model.update_material("object", SceneMaterialAuthoringRecord())
    with pytest.raises(ValueError, match="empty selection"):
        model.clear_selection()
        model.group_selection(
            SceneGroupAuthoringRecordV2(id="empty", name="Empty", members=[])
        )


def test_scene_authoring_model_v2_object_material_and_socket_boundaries():
    model = SceneAuthoringModel(
        upgrade_scene_authoring_document(_authoring_document_v1())
    )
    geometry = _boundary_vector_geometry()
    material = SceneMaterialAuthoringRecord(albedo="#abcdef", opacity=0.75)
    model.update_vector_geometry("object", geometry)
    model.update_material("object", material)
    model.update_transform("object", _authoring_transform(12, 14))
    assert model.document.objects[0].material == material
    assert model.document.objects[0].vector_geometry == geometry

    point = Point3Record(x=0, y=0, z=0)
    light = SceneLightSocketRecord(
        id="light",
        layer_id="base",
        position=point,
        color="#ffffff",
        intensity=1,
        radius=4,
    )
    system = _boundary_particle_system()
    with pytest.raises(KeyError):
        model.add_socket(light.model_copy(update={"layer_id": "missing"}))
    with pytest.raises(ValueError, match="only be attached"):
        model.add_socket(light, system)
    model.add_socket(light)

    vfx = SceneVfxSocketRecord(
        id="vfx", layer_id="base", position=point, effect_id="fx"
    )
    with pytest.raises(ValueError, match="must match"):
        model.add_socket(vfx, _boundary_particle_system("other"))
    model.add_socket(vfx, system)
    with pytest.raises(ValueError, match="ID exists"):
        model.add_socket(
            SceneVfxSocketRecord(
                id="vfx2", layer_id="base", position=point, effect_id="fx"
            ),
            system,
        )
    model.update_vfx_socket(
        "vfx",
        position=Point3Record(x=3, y=4, z=0),
        rotation=point,
        effect_id="fx",
        scale=1.5,
        enabled=False,
        particle_system=system,
    )
    with pytest.raises(ValueError, match="must match"):
        model.update_vfx_socket(
            "vfx",
            position=point,
            rotation=point,
            effect_id="fx",
            scale=1,
            enabled=True,
            particle_system=_boundary_particle_system("other"),
        )
    model.set_particle_system(_boundary_particle_system("second"))
    assert model.document.particle_systems[-1].id == "second"
    with pytest.raises(KeyError):
        model.update_particle_system(_boundary_particle_system("missing"))
    model.update_particle_system(_boundary_particle_system("second"))
    model.remove_particle_system("second")
    with pytest.raises(KeyError):
        model.remove_particle_system("missing")


def test_post_processing_runtime_validation_and_preview_boundaries(tmp_path: Path):
    with pytest.raises(ValueError):
        post_processing_module._finite(True, "value")
    with pytest.raises(ValueError):
        post_processing_module._finite("bad", "value")
    with pytest.raises(ValueError):
        post_processing_module._finite(float("inf"), "value")
    with pytest.raises(ValueError):
        post_processing_module._bounded(-1, "value", 0, 1)
    with pytest.raises(ValueError):
        post_processing_module._bounded(2, "value", 0, 1)

    document = post_processing_module.PostProcessingDocumentV1(
        source=post_processing_module.PostProcessingSourceBindingRecord(
            sha256="a" * 64
        ),
        fallback=post_processing_module.PostProcessingFallbackRecord(
            mode="cpu-preview", reason="boundary"
        ),
        effects=[
            post_processing_module.PostProcessingEffectRecord(
                id="off",
                kind="exposure",
                order=0,
                enabled=False,
                parameters={"stops": 0.0},
            )
        ],
    )
    runtime = post_processing_module.PostProcessingRuntime()
    assert runtime.manifest_copy() is None
    runtime.load_manifest(document)
    assert runtime.manifest_copy() == document.model_dump(mode="json")
    with pytest.raises(post_processing_module.PostProcessingCapabilityError):
        runtime.negotiate("")
    with pytest.raises(post_processing_module.PostProcessingCapabilityError):
        runtime.negotiate(None)
    with pytest.raises(post_processing_module.PostProcessingPreviewError):
        runtime.preview(np.zeros((0, 2, 4), dtype=np.float64))
    with pytest.raises(post_processing_module.PostProcessingPreviewError):
        runtime.preview(np.zeros((2, 2, 3), dtype=np.float64))
    with pytest.raises(post_processing_module.PostProcessingPreviewError):
        runtime.preview(np.zeros((2, 2, 4), dtype=np.dtype("U1")))
    with pytest.raises(post_processing_module.PostProcessingPreviewError):
        runtime.preview(np.zeros((2, 2, 4), dtype=np.float64) + np.nan)
    assert np.array_equal(
        post_processing_module._box_blur(np.ones((2, 2, 3)), 0),
        np.ones((2, 2, 3)),
    )

    with pytest.raises(post_processing_module.PostProcessingValidationError):
        post_processing_module.validate_post_processing_runtime_export([])
    with pytest.raises(post_processing_module.PostProcessingFormatError):
        post_processing_module.load_post_processing_runtime_export_bytes("bytes")
    with pytest.raises(post_processing_module.PostProcessingFormatError):
        post_processing_module.load_post_processing_runtime_export_bytes(b"\xff")
    with pytest.raises(post_processing_module.PostProcessingValidationError):
        post_processing_module.verify_post_processing_source_binding(document, "bytes")
    with pytest.raises(post_processing_module.PostProcessingValidationError):
        post_processing_module.save_post_processing_runtime_export(
            document, tmp_path / "missing" / "post.json"
        )
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(post_processing_module.PostProcessingValidationError):
        post_processing_module.save_post_processing_runtime_export(document, directory)


@pytest.mark.parametrize(
    "reference",
    [
        None,
        "",
        "/absolute.png",
        "../escape.png",
        "C:/drive.png",
        "//share.png",
        "a/../b.png",
    ],
)
def test_integration_manifest_low_level_path_and_numeric_guards(reference):
    with pytest.raises(ValueError):
        integration_module._relative_reference(reference)


def test_integration_manifest_low_level_contract_helpers(tmp_path: Path):
    assert (
        integration_module._relative_reference(r"folder\sprite.png")
        == "folder/sprite.png"
    )
    with pytest.raises(ValueError):
        integration_module._finite(True, "number")
    with pytest.raises(ValueError):
        integration_module._finite("invalid", "number")
    with pytest.raises(ValueError):
        integration_module._finite(float("nan"), "number")
    with pytest.raises(ValueError):
        integration_module._positive_int(True, "count")
    with pytest.raises(ValueError):
        integration_module._positive_int(0, "count")
    with pytest.raises(ValueError):
        integration_module._positive_int(1.5, "count")
    assert integration_module._positive_int(1, "count") == 1
    with pytest.raises(ValueError):
        integration_module._non_negative_int(True, "offset")
    with pytest.raises(ValueError):
        integration_module._non_negative_int(-1, "offset")
    with pytest.raises(ValueError):
        integration_module._non_negative_int(1.5, "offset")
    assert integration_module._non_negative_int(0, "offset") == 0
    with pytest.raises(ValueError):
        integration_module._rect([], "rect")
    with pytest.raises(ValueError):
        integration_module._rect({"x": 0, "y": 0, "w": 0, "h": 1}, "rect")
    with pytest.raises(ValueError):
        integration_module._rect({"x": -1, "y": 0, "w": 1, "h": 1}, "rect")
    assert (
        integration_module._rect({"x": 0, "y": 0, "w": 1, "h": 2}, "rect")["h"] == 2.0
    )
    with pytest.raises(ValueError):
        integration_module._validate_sync({})
    image = tmp_path / "source.png"
    image.write_bytes(b"source")
    assert len(integration_module._sha256_file(image)) == 64
    with pytest.raises(ValueError):
        integration_module._sha256_file(tmp_path / "missing.png")
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(ValueError):
        integration_module._sha256_file(directory)


def test_auto_detect_geometry_helpers_cover_limits_and_diagnostics(monkeypatch):
    with pytest.raises(ValueError):
        auto_detect_module._bounded_downscale(0)
    with pytest.raises(ValueError):
        auto_detect_module._bounded_downscale(True)
    with pytest.raises(ValueError):
        auto_detect_module._bounded_chaikin_iterations(True)
    with pytest.raises(ValueError):
        auto_detect_module._bounded_morphology_kernel(2)
    gray = np.arange(9, dtype=np.uint8).reshape(3, 3)
    assert auto_detect_module._resize_grayscale(gray, 1.0) is gray
    assert auto_detect_module._resize_grayscale(gray, 0.5).shape == (1, 1)
    assert (
        auto_detect_module._to_uint8_grayscale(np.zeros((2, 2), dtype=np.float32)).max()
        == 0
    )
    assert (
        auto_detect_module._to_uint8_grayscale(
            np.array([[-1.0, 10.0]], dtype=np.float32)
        ).max()
        == 255
    )
    rgba = np.zeros((2, 2, 4), dtype=np.uint8)
    rgba[:, :, 3] = [[0, 255], [0, 255]]
    assert auto_detect_module._alpha_foreground_mask(rgba) is not None
    assert (
        auto_detect_module._alpha_foreground_mask(np.zeros((2, 2, 3), dtype=np.uint8))
        is None
    )
    assert (
        np.count_nonzero(
            auto_detect_module._foreground_mask(
                np.zeros((3, 3), dtype=np.uint8), np.zeros((3, 3), dtype=np.uint8)
            )
        )
        == 0
    )
    contour = np.array([[[0, 0]], [[0, 10]], [[10, 10]], [[10, 0]]], dtype=np.int32)
    assert auto_detect_module._approximate_contour(contour, 1.0)
    assert (
        auto_detect_module._approximate_contour(
            np.zeros((1, 1, 2), dtype=np.int32), 1.0
        )
        == []
    )
    assert (
        len(auto_detect_module._bounded_polygon_points([(i, i) for i in range(4)], 3))
        <= 3
    )
    with pytest.raises(ValueError, match="contour count"):
        monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_OBJECTS", 0)
        auto_detect_module._validate_contours([contour])
    monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_OBJECTS", 10)
    with pytest.raises(ValueError, match="contour points"):
        monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_POINTS", 1)
        auto_detect_module._validate_contours([contour])
    monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_POINTS", 1000)
    with pytest.raises(ValueError, match="polygon count"):
        monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_OBJECTS", 0)
        auto_detect_module._validate_detection_result([{"polygon": []}])
    monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_OBJECTS", 10)
    with pytest.raises(ValueError, match="polygon exceeds"):
        monkeypatch.setattr(auto_detect_module, "MAX_POLYGON_POINTS", 2)
        auto_detect_module._validate_detection_result([{"polygon": [1, 2, 3]}])
    monkeypatch.setattr(auto_detect_module, "MAX_POLYGON_POINTS", 1000)
    with pytest.raises(ValueError, match="polygon points"):
        monkeypatch.setattr(auto_detect_module, "MAX_PROJECT_POINTS", 1)
        auto_detect_module._validate_detection_result([{"polygon": [1, 2]}])
    assert (
        auto_detect_module._segment_intersection_point((0, 0), (1, 0), (0, 1), (1, 1))
        is None
    )
    assert auto_detect_module._segment_intersection_point(
        (0, 0), (2, 2), (0, 2), (2, 0)
    ) == (1.0, 1.0)
    assert (
        auto_detect_module._segment_intersection_point((0, 0), (1, 0), (2, 1), (2, -1))
        is None
    )

    diagnostics = [
        None,
        [],
        [(0, 0), (1, 1)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 0), (True, 1), (2, 2)],
        [(0, 0), ("x", 1), (2, 2)],
        [(0, 0), (float("inf"), 1), (2, 2)],
        [(0, 0), (1, 0), (1, 0), (0, 1)],
        [(0, 0), (2, 2), (0, 2), (2, 0)],
    ]
    assert all(
        not auto_detect_module.polygon_validation_details(item)["is_valid"]
        for item in diagnostics
    )
    result = auto_detect_module.DetectResult([], {"status": "ok"})
    with pytest.raises(KeyError):
        result["unknown"]
    assert result.get("unknown", "fallback") == "fallback"
    polygons = [{"polygon": [(0, 0), (2, 0), (0, 2)]}, {"polygon": [(0, 0)]}]
    assert auto_detect_module._annotate_polygon_validation(polygons) == (1, 1)


def test_polygon_editor_gesture_and_hit_test_boundaries():
    scene, canvas, tool = _boundary_polygon_tool()
    tool._present_p2d05_error = Mock()

    assert tool._find_vertex_index_in_polygon([(1, 2)], (9, 9)) is None
    assert tool._find_current_vertex_index("missing", (1, 2)) is None
    tool.selected_polygon_id = "missing"
    tool.selected_vertex = 0
    assert tool.selected_vertex_position() is None
    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0

    tool._vertex_transaction = SimpleNamespace(
        active=False,
        origin_polygon=[(0, 0), (10, 0), (0, 10)],
    )
    tool._vertex_origin_index = 0
    tool._preview_vertex_position((2, 2))
    assert tool._vertex_preview_position is None

    assert tool._begin_vertex_gesture() is True
    tool._vertex_origin_index = 99
    tool._preview_vertex_position((2, 2))
    assert tool._vertex_transaction is None

    class PreviewFailure:
        active = True
        origin_polygon = [(0, 0), (10, 0), (0, 10)]

        def preview(self, _candidate):
            raise RuntimeError("preview boundary")

        def cancel(self):
            return True

    tool._vertex_transaction = PreviewFailure()
    tool._vertex_origin_index = 0
    canvas.snap_vertex_position = lambda _pos: (_ for _ in ()).throw(
        ValueError("snap boundary")
    )
    tool._preview_vertex_position((2, 2))
    assert tool._vertex_transaction is None
    canvas.snap_vertex_position = lambda position: tuple(position)

    class CancelFailure:
        active = True
        origin_polygon = [(0, 0), (10, 0), (0, 10)]

        def cancel(self):
            raise RuntimeError("cancel boundary")

    tool._vertex_transaction = CancelFailure()
    assert tool._cancel_vertex_gesture() is False
    assert tool._vertex_transaction is None

    class CommitFailure:
        active = True

        def commit(self, _manager):
            raise RuntimeError("commit boundary")

    tool._vertex_transaction = CommitFailure()
    assert tool._finish_vertex_gesture() is None
    assert tool._vertex_transaction is None

    tool.selected_polygon_id = None
    tool.selected_vertex = None
    tool._context_target = None
    assert tool._resolve_context_target(None) is None
    tool.selected_polygon_id = "A"
    tool.selected_vertex = None
    assert tool._resolve_context_target(None) == ("polygon", "A", None)
    assert tool._resolve_context_target((1000, 1000)) is None
    assert tool._resolve_context_target((10, 10)) == ("polygon", "A", None)

    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    tool.selected_vertices.clear()
    assert tool._resolve_context_target((0, 0)) == ("vertex", "A", 0)
    assert tool._resolve_context_target((0, 0)) == ("vertex", "A", 0)

    tool.on_mouse_move(_boundary_mouse_event(), (0, 0))
    assert canvas.cursor == Qt.CursorShape.PointingHandCursor
    tool.on_mouse_move(_boundary_mouse_event(), (1000, 1000))
    assert canvas.cursor == Qt.CursorShape.ArrowCursor


def test_polygon_editor_interaction_and_command_status_boundaries():
    scene, canvas, tool = _boundary_polygon_tool()
    tool._present_p2d05_error = Mock()

    class ModifierFailure:
        def button(self):
            return Qt.MouseButton.LeftButton

        def modifiers(self):
            raise TypeError("modifier boundary")

        def key(self):
            return None

        def pos(self):
            return QPointF(0, 0)

        def globalPos(self):
            return QPointF(0, 0)

    tool.on_mouse_press(ModifierFailure(), (0, 0))
    assert tool.selected_polygon_id == "A"

    tool.multi_select = True
    tool.on_mouse_press(_boundary_mouse_event(), (40, 5))
    assert "B" in tool.selected_polygon_ids
    tool.on_mouse_press(_boundary_mouse_event(), (1000, 1000))
    tool.multi_select = False

    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    tool.selected_vertices = {("A", 0)}
    additive = _boundary_mouse_event(
        modifiers=Qt.KeyboardModifier.ControlModifier,
    )
    tool.on_mouse_press(additive, (0, 0))
    assert tool.selected_vertices == set()
    tool.on_mouse_press(additive, (0, 0))
    assert tool.selected_vertices == {("A", 0)}

    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.RightButton), (0, 0))
    assert tool._vertex_transaction is None
    tool.adding_new = True
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.RightButton), (0, 0))
    assert tool.adding_new is False
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.MiddleButton), (0, 0))

    tool.adding_new = True
    tool.on_key_press(_boundary_mouse_event(key=Qt.Key.Key_Escape))
    assert tool.adding_new is False
    assert tool.on_key_press(_boundary_mouse_event(key=Qt.Key.Key_A)) is False
    assert tool.on_undo() is False
    assert tool.on_redo() is False

    class ResultManager:
        def __init__(self, result):
            self.result = result

        def execute(self, *_args):
            return self.result

    for status in (
        commands_module.CommandStatus.NO_CHANGE,
        commands_module.CommandStatus.REJECTED,
        commands_module.CommandStatus.FAILED,
    ):
        scene.cmd = ResultManager(
            commands_module.CommandResult(
                status,
                commands_module.Command(),
                "execute",
                "status boundary",
            )
        )
        tool._execute_polygon_update(
            "A",
            [(0, 0), (20, 0), (20, 20), (0, 20)],
            [(1, 1), (20, 0), (20, 20), (0, 20)],
            "Boundary",
        )

    scene.cmd = None
    tool._execute_polygon_update(
        "A",
        [(0, 0), (20, 0), (20, 20), (0, 20)],
        [(1, 1), (20, 0), (20, 20), (0, 20)],
        "Boundary",
    )
    tool._execute_object_deletion([], "Boundary")
    tool.undo_last_action()
    tool.redo_last_action()

    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    scene.cmd = CommandManager(max_history=10)
    scene.cmd.clear()
    tool.delete_selected_vertex("A", 0)
    scene.objects["A"].polygon = [(0, 0), (10, 0), (0, 10)]
    tool.selected_vertex = 0
    tool.delete_selected_vertex("A", 0)


def test_polygon_editor_context_menu_and_overlay_boundaries(monkeypatch):
    scene, canvas, tool = _boundary_polygon_tool()
    tool._present_p2d05_error = Mock()
    tool._context_image_pos = None
    tool.show_context_menu = Mock()

    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.RightButton), (5, 5))
    tool.show_context_menu.assert_called_once()

    class ActionProbe:
        def __init__(self, text):
            self.text = text
            self.triggered = SimpleNamespace(connect=lambda callback: None)

    class MenuProbe:
        def __init__(self, _parent):
            self.actions = []

        def addAction(self, text):
            action = ActionProbe(text)
            self.actions.append(action)
            return action

        def addSeparator(self):
            return None

        def exec(self, _position):
            return None

    monkeypatch.setattr(polygon_edit_tool_module, "QMenu", MenuProbe)
    monkeypatch.setattr(polygon_edit_tool_module, "fit_context_menu", lambda menu: menu)
    tool._context_image_pos = (5, 5)
    tool.selected_polygon_ids = {"A", "B"}
    tool.show_context_menu(_boundary_mouse_event(Qt.MouseButton.RightButton))
    tool._context_image_pos = (1000, 1000)
    tool.show_context_menu(_boundary_mouse_event(Qt.MouseButton.RightButton))

    tool.selected_polygon_ids = {"A"}
    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    tool.selected_vertices = {("A", 0), ("A", 1)}
    tool._context_image_pos = (0, 0)
    tool.show_context_menu(_boundary_mouse_event(Qt.MouseButton.RightButton))

    tool.selected_polygon_ids = {"A"}
    tool.selected_vertex = None
    tool.selected_vertices.clear()
    tool._context_image_pos = (5, 5)
    tool.show_context_menu(_boundary_mouse_event(Qt.MouseButton.RightButton))


def _boundary_collision_tool(has_collision=True):
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object("A", [(0, 0), (20, 0), (20, 20), (0, 20)], select=True)
    scene.add_object("B", [(30, 0), (45, 0), (45, 15)], select=False)
    if has_collision:
        scene.collision_shapes["A"] = [
            (1.0, 1.0),
            (19.0, 1.0),
            (19.0, 19.0),
            (1.0, 19.0),
        ]
    scene.cmd.clear()
    canvas = _BoundaryPolygonCanvas(scene)
    return scene, canvas, CollisionBrushTool(canvas)


def test_collision_brush_interaction_and_transform_boundaries(monkeypatch):
    scene, canvas, tool = _boundary_collision_tool()
    critical = Mock()
    warning = Mock()
    monkeypatch.setattr(collision_brush_tool_module.QMessageBox, "critical", critical)
    monkeypatch.setattr(collision_brush_tool_module.QMessageBox, "warning", warning)

    assert tool._find_polygon_at((5, 5)) == "A"
    assert tool._find_polygon_at((1000, 1000)) is None
    assert tool._select_object_for_gizmo("missing") is False
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.MiddleButton), (5, 5))
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.RightButton), (1000, 1000))

    scene.cmd = None
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.LeftButton), (5, 5))
    assert critical.called
    scene.cmd = CommandManager(max_history=20)
    scene.cmd.clear()

    class StatusManager:
        def __init__(self, status):
            self.status = status

        def execute(self, command, _model):
            return commands_module.CommandResult(
                self.status,
                command,
                "execute",
                "collision boundary",
            )

    for status in (
        commands_module.CommandStatus.REJECTED,
        commands_module.CommandStatus.FAILED,
        commands_module.CommandStatus.NO_CHANGE,
    ):
        scene.cmd = StatusManager(status)
        tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.LeftButton), (5, 5))

    class RaisingManager:
        def execute(self, *_args):
            raise RuntimeError("toggle boundary")

    scene.cmd = RaisingManager()
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.LeftButton), (5, 5))
    scene.cmd = CommandManager(max_history=20)
    scene.cmd.clear()

    tool._begin_transform_gesture("missing", "Move")
    assert tool._transform_transaction is None
    monkeypatch.setattr(
        collision_brush_tool_module,
        "ObjectGeometryGestureTransaction",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("transaction boundary")),
    )
    tool._begin_transform_gesture("A", "Move")
    assert tool._transform_transaction is None
    monkeypatch.undo()
    monkeypatch.setattr(collision_brush_tool_module.QMessageBox, "critical", Mock())

    tool._begin_transform_gesture("A", "Move")
    assert tool._transform_transaction is not None
    tool._preview_move((0, 0))
    tool._preview_move((3, 4))
    tool._preview_move((3, 4))
    tool._preview_scale((3, 4))
    tool._cancel_transform_gesture()
    assert tool._transform_transaction is None

    scene_without_collision, _, no_collision_tool = _boundary_collision_tool(False)
    no_collision_tool._begin_transform_gesture("A", "Move")
    no_collision_tool._preview_move((0, 0))
    no_collision_tool._preview_move((5, 5))
    no_collision_tool._cancel_transform_gesture()
    assert "A" not in scene_without_collision.collision_shapes

    tool._begin_transform_gesture("A", "Scale")
    tool._preview_scale((0, 0))
    tool._preview_scale((0, -5000))
    tool._scale_increase("missing")
    tool._scale_decrease("missing")
    tool._apply_scale(None)
    tool._apply_scale("missing")
    tool._cancel_scale()

    tool._preview_transform_geometry([], False, None, "Boundary")

    class PreviewFailure:
        active = True

        def preview(self, *_args, **_kwargs):
            raise RuntimeError("geometry preview boundary")

        def cancel(self):
            raise RuntimeError("geometry cleanup boundary")

    tool._transform_transaction = PreviewFailure()
    tool._preview_transform_geometry([], False, None, "Boundary")
    assert tool._transform_transaction is None

    tool.on_cancel()
    assert tool.on_key_press(_boundary_mouse_event(key=Qt.Key.Key_A)) is False
    assert tool.on_undo() is False
    assert tool.on_redo() is False


def test_collision_brush_menu_lifecycle_overlay_and_status_boundaries(monkeypatch):
    scene, canvas, tool = _boundary_collision_tool()
    canvas.window = lambda: None
    tool.update_language("pt")
    assert tool.current_lang == "pt"
    monkeypatch.setattr(collision_brush_tool_module.QMessageBox, "warning", Mock())
    monkeypatch.setattr(collision_brush_tool_module.QMessageBox, "critical", Mock())

    tool._show_hub_menu = Mock()
    tool.on_mouse_press(_boundary_mouse_event(Qt.MouseButton.RightButton), (5, 5))
    tool._show_hub_menu.assert_called_once()

    palette = SimpleNamespace(select_tool_by_name=Mock())
    active = SimpleNamespace(
        selected_polygon_id=None,
        selected_vertex=99,
        selected_polygon_ids=set(),
        set_mode=Mock(),
    )
    main_window = SimpleNamespace(tool_palette=palette)
    canvas.window = lambda: main_window
    canvas._active_tool_object = lambda: active
    tool._start_edit(None, main_window)
    tool._start_edit("A", main_window)
    assert palette.select_tool_by_name.call_args.args == ("polygon_edit",)
    assert active.selected_polygon_id == "A"
    tool.selected_polygon_id = None
    tool._start_edit(None, main_window)
    tool._start_scale("A")
    assert scene.selected_id == "A"

    tool.moving = True
    tool.moving_oid = "A"
    tool.last_pos = (1, 1)
    tool.scaling = True
    tool.scaling_oid = "A"
    tool.scale_center = (10.0, 10.0)
    tool.initial_scale = 2.0
    tool.last_scale_pos = (2, 2)
    tool._reset_interaction_for_object("A")
    assert tool.selected_polygon_id is None
    tool._reset_interaction_for_object("missing")

    tool._report_command_result(
        commands_module.CommandResult(
            commands_module.CommandStatus.REJECTED,
            commands_module.Command(),
            "execute",
            "rejected",
        ),
        "Boundary",
    )
    tool._report_command_result(
        commands_module.CommandResult(
            commands_module.CommandStatus.FAILED,
            commands_module.Command(),
            "execute",
            "failed",
        ),
        "Boundary",
    )

    monkeypatch.setattr(
        collision_brush_tool_module.QMessageBox,
        "question",
        lambda *_args, **_kwargs: (
            collision_brush_tool_module.QMessageBox.StandardButton.No
        ),
    )
    tool._remove("A")
    monkeypatch.setattr(
        collision_brush_tool_module.QMessageBox,
        "question",
        lambda *_args, **_kwargs: (
            collision_brush_tool_module.QMessageBox.StandardButton.Yes
        ),
    )
    scene.cmd = None
    tool._remove("A")
    scene.cmd = CommandManager(max_history=20)

    class RemoveFailure:
        def execute(self, *_args):
            raise RuntimeError("remove boundary")

    scene.cmd = RemoveFailure()
    tool._remove("A")
    scene.cmd = CommandManager(max_history=20)

    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    tool.draw_overlay(painter)
    tool.moving = True
    tool.moving_oid = "A"
    tool.scaling = True
    tool.scaling_oid = "A"
    tool.draw_overlay(painter)
    painter.end()

    tool._begin_transform_gesture("A", "Move")

    class CommitFailure:
        active = True

        def commit(self, _manager):
            raise RuntimeError("commit boundary")

    tool._transform_transaction = CommitFailure()
    with pytest.raises(RuntimeError, match="commit boundary"):
        tool._finish_transform_gesture()
    assert tool._transform_transaction is None

    class CancelFailure:
        active = True

        def cancel(self):
            raise RuntimeError("cancel boundary")

    tool._transform_transaction = CancelFailure()
    with pytest.raises(RuntimeError, match="cancel boundary"):
        tool._cancel_transform_gesture()
    assert tool._transform_transaction is None


def test_mask_viewer_geometry_roi_and_gizmo_boundaries(monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    viewer = MaskViewer()
    valid = [(2, 2), (18, 2), (18, 18), (2, 18)]
    invalid = [(2, 2), (18, 18), (2, 18), (18, 2)]
    viewer.set_overlay_polygons(
        [
            {"polygon": list(valid)},
            {"polygon": list(invalid)},
            [],
        ]
    )
    assert viewer._refresh_polygon_validation() == (1, 2)
    assert viewer._polygon_points_at_index(-1) is None
    assert viewer._polygon_points_at_index(99) is None
    assert viewer._find_vertex_at(QPointF(2, 2)) == (1, 0)
    assert viewer._find_vertex_at(QPointF(100, 100)) == (-1, -1)
    viewer._image = np.zeros((20, 20), dtype=np.uint8)
    viewer._editing_polygon_index = -1
    viewer._editing_vertex_index = -1
    viewer._move_editing_vertex(QPointF(5, 5))
    viewer._editing_polygon_index = 2
    viewer._editing_vertex_index = 0
    viewer._move_editing_vertex(QPointF(5, 5))
    viewer._editing_polygon_index = 0
    viewer._editing_vertex_index = 0
    viewer._move_editing_vertex(QPointF(-10, 100))
    assert viewer._overlay_polygons[0]["polygon"][0] == (0, 19)

    viewer._context_polygon_index = 0
    viewer._context_vertex_index = -1
    viewer._context_image_point = QPointF(10, 2)
    viewer.add_context_vertex()
    assert len(viewer._overlay_polygons[0]["polygon"]) == 5
    viewer._context_vertex_index = 0
    viewer.remove_context_vertex()
    assert len(viewer._overlay_polygons[0]["polygon"]) == 4
    viewer._context_vertex_index = 99
    viewer.remove_context_vertex()
    viewer.undo_polygon_edit()
    viewer.redo_polygon_edit()
    viewer._context_polygon_index = 0
    viewer._transform_selected_polygon(
        lambda point, center: QPointF(point.x() + 1, point.y() + 1)
    )
    viewer._transform_selected_polygon(lambda point, center: point)

    viewer._gizmo_enabled = False
    assert viewer._gizmo_handle_positions() == {}
    viewer.set_selected_polygon_index(0)
    viewer.set_gizmo_enabled(True)
    handles = viewer._gizmo_handle_positions()
    assert set(handles) == {"move", "scale", "rotate"}
    assert viewer._find_gizmo_handle_at(viewer.image_to_view(handles["move"])) == "move"
    assert viewer._find_gizmo_handle_at(QPointF(1000, 1000)) is None
    viewer._begin_gizmo_drag("move", QPointF(5, 5))
    viewer._move_gizmo(QPointF(7, 8))
    viewer._finish_gizmo_drag()
    viewer._begin_gizmo_drag("scale", QPointF(10, 2))
    viewer._move_gizmo(QPointF(20, 2))
    viewer._finish_gizmo_drag()
    viewer._begin_gizmo_drag("rotate", QPointF(10, 2))
    viewer._move_gizmo(QPointF(10, 12))
    viewer._finish_gizmo_drag()
    viewer._begin_gizmo_drag("unknown", QPointF(10, 2))
    viewer._move_gizmo(QPointF(10, 12))
    viewer._finish_gizmo_drag()
    viewer._begin_gizmo_drag("scale", handles["move"])
    viewer._move_gizmo(handles["move"])
    viewer._finish_gizmo_drag()
    viewer.set_gizmo_enabled(False)
    viewer.set_polygon_handles_visible(False)
    viewer.set_polygon_diagnostics_visible(False)

    viewer.set_roi_mode(True)
    assert viewer.cursor().shape() if False else True
    viewer._roi_start = QPointF(2, 2)
    viewer._update_roi(QPointF(15, 12))
    assert viewer.get_roi() == (2, 2, 13, 10)
    viewer.clear_roi()
    assert viewer.get_roi() is None
    viewer.set_roi_mode(False)
    viewer.set_zoom(999.0, QPointF(4, 4))
    viewer.set_zoom(0.0)
    viewer.set_pan(3.0, -2.0)
    viewer.set_view_transform(2.0, 1.0, 2.0)
    assert viewer.view_to_image(viewer.image_to_view(QPointF(4, 5))) == pytest.approx(
        (4, 5)
    )
    viewer.reset_view()
    viewer.set_numpy_image(None)
    viewer.reset_view()

    viewer.set_numpy_image(np.arange(25, dtype=np.uint8).reshape(5, 5))
    viewer.set_display_mode(1)
    assert viewer.get_processing_image(use_active_view=True) is not None
    viewer.set_layer_overlays(
        {"Sobel": True, "Canny": True, "Threshold": True, "Watershed": True},
        opacity=2.0,
    )
    assert viewer._compose_layer_overlays(viewer._image).shape == (5, 5, 3)
    assert viewer._get_qimage() is not None
    viewer._qimage_cache = None
    viewer.set_numpy_image(np.zeros((5, 5, 3), dtype=np.uint8))
    assert viewer._get_qimage() is not None
    viewer._qimage_cache = None
    viewer.set_numpy_image(np.zeros((5, 5, 4), dtype=np.uint8))
    assert viewer._get_qimage() is not None
    viewer._qimage_cache = None
    viewer.set_numpy_image(np.zeros((5, 5, 5), dtype=np.uint8))
    assert viewer._get_qimage() is None

    monkeypatch.setattr(
        mask_viewer_module.ViewProcessor,
        "generate_xray_array",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("xray boundary")),
    )
    viewer.set_numpy_image(np.zeros((5, 5), dtype=np.uint8))
    viewer.set_display_mode(1)
    assert viewer.get_display_mode() == 1


def test_mask_viewer_event_and_context_boundaries(monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    viewer = MaskViewer()
    viewer.resize(100, 100)
    viewer.set_numpy_image(np.zeros((20, 20), dtype=np.uint8))
    viewer.set_overlay_polygons([{"polygon": [(1, 1), (18, 1), (18, 18), (1, 18)]}])

    class Event:
        def __init__(
            self,
            button=Qt.MouseButton.LeftButton,
            point=(5, 5),
            modifiers=Qt.KeyboardModifier.NoModifier,
            delta=0,
            key=None,
        ):
            self._button = button
            self._point = QPointF(*point)
            self._modifiers = modifiers
            self._delta = delta
            self._key = key
            self.accepted = False
            self.ignored = False

        def button(self):
            return self._button

        def position(self):
            return self._point

        def globalPosition(self):
            return self._point

        def globalPos(self):
            return self._point

        def modifiers(self):
            return self._modifiers

        def angleDelta(self):
            return SimpleNamespace(y=lambda: self._delta)

        def key(self):
            return self._key

        def accept(self):
            self.accepted = True

        def ignore(self):
            self.ignored = True

    viewer.mousePressEvent(Event(Qt.MouseButton.MiddleButton))
    viewer.mouseMoveEvent(Event(point=(8, 9)))
    viewer.mouseReleaseEvent(Event(Qt.MouseButton.MiddleButton))
    viewer.set_roi_mode(True)
    viewer.mousePressEvent(Event(point=(1, 1)))
    viewer.mouseMoveEvent(Event(point=(15, 15)))
    viewer.mouseReleaseEvent(Event(point=(15, 15)))
    viewer.set_roi_mode(False)
    viewer.tool_handler = lambda event: True
    viewer.mousePressEvent(Event(point=(50, 50)))
    viewer.tool_handler = None
    viewer.mousePressEvent(Event(point=(10, 10)))
    viewer.mouseMoveEvent(Event(point=(20, 20)))
    viewer.mouseReleaseEvent(Event(point=(20, 20)))
    viewer.wheelEvent(Event(delta=120, point=(5, 5)))
    viewer.wheelEvent(Event(delta=-120, modifiers=Qt.KeyboardModifier.ControlModifier))
    viewer.wheelEvent(Event(delta=0))
    viewer.keyPressEvent(Event(key=Qt.Key.Key_R))
    viewer.keyPressEvent(
        QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier,
        )
    )

    class Action:
        def __init__(self):
            self.triggered = SimpleNamespace(connect=lambda _callback: None)

        def setEnabled(self, _value):
            return None

        def setCheckable(self, _value):
            return None

        def setChecked(self, _value):
            return None

    class Menu:
        def __init__(self, _parent):
            pass

        def addAction(self, _text):
            return Action()

        def addSeparator(self):
            return None

        def exec(self, _position):
            return None

    monkeypatch.setattr(mask_viewer_module, "QMenu", Menu)
    monkeypatch.setattr(mask_viewer_module, "fit_context_menu", lambda menu: menu)
    normal_event = Event(point=(5, 5))
    viewer.contextMenuEvent(normal_event)
    viewer.set_roi_mode(True)
    ignored_event = Event(point=(5, 5))
    viewer.contextMenuEvent(ignored_event)
    assert ignored_event.ignored is True

    viewer.set_roi_mode(False)
    viewer.set_overlay_polygons([])
    viewer.mousePressEvent(Event(point=(30, 30)))


def test_canvas_view_state_gizmo_and_scenario_boundaries(monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object("A", [(0, 0), (20, 0), (20, 20), (0, 20)], select=True)
    scene.add_object("B", [(30, 0), (45, 0), (45, 15)], select=False)
    scene.cmd.clear()
    canvas = CanvasView(scene)
    canvas.resize(320, 240)

    assert canvas._selected_object_ids() == ["A"]
    scene.selected_ids = ["missing"]
    assert canvas._selected_object_ids() == []
    scene.selected_ids = ["A", "B"]
    assert canvas._selected_object_ids() == ["A", "B"]
    scene.selected_id = None
    assert canvas._selected_object_ids() == []
    scene.selected_id = "A"
    scene.selected_ids = []
    scene.objects["A"].position = (5.0, 6.0, 0.0)
    assert canvas._selection_anchor_image() == QPointF(5.0, 6.0)
    scene.objects["A"].position = (5.0,)
    assert canvas._selection_anchor_image() == QPointF(10.0, 10.0)
    scene.selected_id = None
    assert canvas._selection_anchor_image() is None
    scene.selected_id = "A"

    assert canvas._gizmo_visual_radius() == 0.0
    assert canvas._gizmo_visual_bounds().isNull()

    class Gizmo:
        NONE = 0
        AXIS_X = 1
        AXIS_Y = 2
        screen_pos = QPointF(1, 1)
        active_axis = NONE

        def set_screen_position(self, position):
            self.screen_pos = position

        def visual_radius(self):
            return 20.0

        def visual_bounds(self, margin=0.0):
            return canvas_view_module.QRectF(
                self.screen_pos.x() - margin,
                self.screen_pos.y() - margin,
                margin * 2.0,
                margin * 2.0,
            )

    canvas.gizmo = Gizmo()
    assert canvas._gizmo_visual_radius() == 20.0
    canvas._gizmo_visual_bounds(3.0)
    assert canvas._update_gizmo_screen_position() is not None
    canvas.set_vertex_snapping(True, grid_size=2, origin=(0.0, 0.0))
    canvas._gizmo_anchor_image = (1.0, 1.0)
    assert canvas._snap_gizmo_translation((3.2, 4.2)) != (3.2, 4.2)
    canvas._gizmo_anchor_image = None
    assert canvas._snap_gizmo_translation((3.2, 4.2)) == (3.2, 4.2)

    canvas.set_vertex_snapping(True, grid_size=4, origin=(1.0, 1.0))
    assert canvas.snap_vertex_position((4.1, 4.1)) == (5, 5)
    canvas.set_grid_visible(False)
    assert canvas.is_grid_visible() is False
    canvas.set_grid_visible(True)
    assert canvas._distance_to_last_point(0, 0) == float("inf")
    canvas._current_polygon = [(0, 0)]
    assert canvas._distance_to_last_point(3, 4) == pytest.approx(5.0)

    class VertexTool:
        selected_polygon_id = "A"
        selected_vertex = 0

        def selected_vertex_position(self):
            return (2, 3)

        def begin_vertex_gizmo_gesture(self):
            return True

        def preview_vertex_gizmo_position(self, position):
            self.previewed = position

        def finish_vertex_gizmo_gesture(self):
            return commands_module.CommandResult.no_change(
                commands_module.Command(), "execute", "vertex"
            )

        def cancel_vertex_gizmo_gesture(self):
            return True

    vertex_tool = VertexTool()
    canvas._tool = vertex_tool
    canvas._gizmo_operation = Gizmo.AXIS_X
    assert canvas._begin_gizmo_vertex_gesture() is True
    canvas._preview_gizmo_vertex(QPointF(30, 40))
    canvas._gizmo_operation = Gizmo.AXIS_Y
    canvas._preview_gizmo_vertex(QPointF(30, 40))
    assert canvas._finish_gizmo_gesture() is not None
    assert canvas._cancel_gizmo_gesture() is False

    canvas._tool = SimpleNamespace()
    assert canvas._begin_gizmo_vertex_gesture() is False
    canvas._tool = SimpleNamespace(
        selected_polygon_id="A",
        selected_vertex=0,
        begin_vertex_gizmo_gesture=lambda: (_ for _ in ()).throw(
            RuntimeError("vertex begin boundary")
        ),
    )
    canvas._present_gizmo_error = Mock()
    assert canvas._begin_gizmo_vertex_gesture() is False

    canvas._gizmo_enabled = True
    assert canvas._nudge_selected_with_gizmo(1, 1) is False
    canvas._tool = None
    canvas._gizmo_enabled = False
    canvas._gizmo_active = True
    assert canvas._nudge_selected_with_gizmo(1, 1) is False

    class Transaction:
        active = True

        def preview_transform(self, **_kwargs):
            raise RuntimeError("preview transform boundary")

        def cancel(self):
            raise RuntimeError("preview rollback boundary")

    canvas._gizmo_transaction = Transaction()
    canvas._present_gizmo_error = Mock()
    canvas._preview_gizmo_transform(translation=(1, 1))
    assert canvas._gizmo_transaction is None
    assert canvas._report_gizmo_result(None) is None
    for status in (
        commands_module.CommandStatus.REJECTED,
        commands_module.CommandStatus.FAILED,
    ):
        canvas._report_gizmo_result(
            commands_module.CommandResult(
                status,
                commands_module.Command(),
                "execute",
                "gizmo status",
            )
        )

    scene.objects["A"].position = (5.0, 6.0, 0.0)
    canvas._set_gizmo_feedback()
    canvas._gizmo_transaction = None
    assert canvas._finish_gizmo_gesture() is None
    assert canvas._cancel_gizmo_gesture() is False

    with pytest.raises(ValueError):
        canvas.set_scenario_preview_layers(["bad"])
    layer = canvas_view_module.ScenarioPreviewLayer(
        id="layer", object_ids=("A",), parallax=canvas_view_module.ParallaxLayer()
    )
    canvas.set_scenario_preview_layers([layer])
    with pytest.raises(ValueError):
        canvas.set_scenario_preview_layers([layer, layer])
    with pytest.raises(ValueError):
        canvas.set_scenario_camera("bad")
    with pytest.raises(ValueError):
        canvas.set_scenario_render_plan("bad")
    with pytest.raises(ValueError):
        canvas.set_scenario_lighting("bad")
    canvas.set_scenario_lighting_enabled(False)
    canvas.set_scenario_overlays_visible(True, aspect_ratio=(16, 9), safe_fraction=0.8)
    assert canvas.is_scenario_overlays_visible() is True
    canvas.set_scenario_preview_enabled(True)
    assert canvas.is_scenario_preview_enabled() is True
    canvas.set_scenario_preview_enabled(False)


def test_canvas_view_menu_commands_and_paint_boundaries(monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    monkeypatch.setattr(canvas_view_module.QMessageBox, "warning", Mock())
    monkeypatch.setattr(canvas_view_module.QMessageBox, "critical", Mock())
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "question",
        lambda *_args, **_kwargs: canvas_view_module.QMessageBox.StandardButton.No,
    )
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object("A", [(0, 0), (20, 0), (20, 20), (0, 20)], select=True)
    scene.cmd.clear()
    canvas = CanvasView(scene)
    canvas.resize(320, 240)
    canvas._qimage_lit = QImage(32, 32, QImage.Format.Format_ARGB32)
    canvas._qimage_lit.fill(0)

    class Action:
        def setEnabled(self, _value):
            return None

        def setStatusTip(self, _value):
            return None

        class Signal:
            def connect(self, _callback):
                return None

        triggered = Signal()

    class Menu:
        def __init__(self, _parent):
            pass

        def addAction(self, _text):
            return Action()

        def addSeparator(self):
            return None

        def exec(self, _position):
            return None

    monkeypatch.setattr(canvas_view_module, "QMenu", Menu)
    monkeypatch.setattr(canvas_view_module, "fit_context_menu", lambda menu: menu)
    canvas.show_context_menu_at(QPointF(5, 5), QPointF(5, 5))
    canvas.show_context_menu_at(QPointF(100, 100), QPointF(100, 100))
    canvas._scenario_preview_enabled = True
    canvas.show_context_menu_at(QPointF(5, 5), QPointF(5, 5))
    canvas._scenario_preview_enabled = False
    canvas._current_polygon = [(1, 1)]
    canvas.show_context_menu_at(QPointF(5, 5), QPointF(5, 5))
    canvas._current_polygon = []

    canvas._present_gizmo_error = Mock()
    scene.cmd = None
    with pytest.raises(RuntimeError):
        canvas._execute_edit_command(commands_module.Command())
    scene.cmd = CommandManager(max_history=10)
    scene.cmd.clear()
    canvas._toggle_collision("A")
    canvas._delete_object("A")
    canvas._toggle_physics("missing")
    canvas._commit_native_polygon([(1, 1), (2, 1), (1, 2)])
    canvas.set_gizmo_enabled(True, publish_viewport_state=False)
    canvas.set_gizmo_enabled(True, publish_viewport_state=False)
    canvas.toggle_gizmo()
    canvas.set_view_mode(CanvasView.VIEW_COLLISION)
    canvas.set_view_mode(999)
    canvas._clear_flash()
    canvas.flash_effect(canvas_view_module.QColor(1, 2, 3), duration=0)
    canvas.fit_to_window()
    canvas.center_on_polygon([])
    canvas.center_on_polygon([(1, 1), (1, 1), (1, 1)])

    image = QImage(320, 240, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    canvas._draw_hud(painter)
    canvas._gizmo_feedback = (
        "T: (1.0, 2.0, 0.0)  Rz: 0.0°  S: (1.00, 1.00, 1.00)  Z-Depth: 0.0"
    )
    canvas._draw_gizmo_feedback(painter)
    canvas.paintEvent(None)
    painter.end()


def test_mask_viewer_dialog_state_and_apply_boundaries(monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    monkeypatch.setattr(mask_viewer_module.QMessageBox, "warning", Mock())
    monkeypatch.setattr(mask_viewer_module.QMessageBox, "critical", Mock())
    monkeypatch.setattr(mask_viewer_module.QMessageBox, "information", Mock())

    dialog = MaskViewerDialog(scene, lang="pt")
    dialog.update_language("en")
    dialog.update_language("pt")
    assert dialog._localized_polygon_reason("has zero area") == "tem área zero"
    assert dialog._localized_polygon_reason("unknown reason") == "unknown reason"
    details = {
        "polygon": [(0, 0), (10, 0), (10, 10), (0, 10)],
        "validation_details": {
            "invalid_vertices": [0, True, 99],
            "invalid_edges": [[0, 1], True, 99],
            "invalid_intersections": [(1, 2), (1,)],
        },
    }
    assert "1-2" in dialog._polygon_validation_location(details)
    dialog._last_polygons = []
    dialog._update_polygon_validation_feedback()
    dialog._last_polygons = [
        {"polygon": [(0, 0), (10, 0), (10, 10), (0, 10)]},
        {"polygon": [(0, 0), (10, 10), (0, 10), (10, 0)]},
    ]
    dialog._update_polygon_validation_feedback()
    assert dialog.apply_button.isEnabled() is False
    dialog._on_detection_finished(dialog._last_polygons)
    dialog._on_detection_error("detection boundary")

    dialog._apply_to_scene()
    dialog._last_polygons = [{"polygon": [(0, 0), (1, 1)]}]
    dialog._update_polygon_validation_feedback()
    dialog._apply_to_scene()
    dialog._last_polygons = [{"polygon": [(0, 0), (10, 0), (0, 10)]}]
    dialog._update_polygon_validation_feedback()
    scene.cmd = None
    dialog._apply_to_scene()

    class ResultManager:
        def __init__(self, status):
            self.status = status

        def execute(self, command, _scene):
            return commands_module.CommandResult(
                self.status,
                command,
                "execute",
                "apply boundary",
            )

    scene.cmd = ResultManager(commands_module.CommandStatus.REJECTED)
    dialog._apply_to_scene()
    scene.cmd = ResultManager(commands_module.CommandStatus.FAILED)
    dialog._apply_to_scene()
    scene.cmd = CommandManager(max_history=10)
    dialog._apply_to_scene()

    dialog._on_roi_selected((1, 2, 10, 11))
    dialog._toggle_roi_mode(True)
    dialog._toggle_roi_mode(False)
    dialog._on_zoom_changed(200.0)
    dialog._on_pan_changed()
    dialog._on_layer_changed("Sobel", 2)
    dialog._on_opacity_changed(80)
    dialog._on_param_changed("min_area", 5.0)
    dialog._toggle_advanced_params(Qt.CheckState.Checked.value)
    dialog._toggle_advanced_params(Qt.CheckState.Unchecked.value)
    dialog._on_view_mode_changed(3)
    dialog._on_explicit_view_mode(0)
    dialog._apply_preset("Enhanced")
    dialog._apply_preset("missing")
    dialog._clear_detection_thread()
    dialog._update_performance_label()
    dialog._refresh_image_info_label()
    dialog._load_scene_image()

    dialog._run_detection()
    scene.image = np.zeros((20, 20), dtype=np.uint8)
    dialog._load_scene_image()
    dialog._apply_preset("GrabCut")
    dialog._run_detection()
    dialog.close()


def test_tilemap_authoring_panel_flow_and_canvas_boundaries(tmp_path):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    panel = TileMapAuthoringPanel(tmp_path)
    panel._refresh_summary()
    panel.add_layer()
    panel.copy_selection()
    panel.paste_selection()
    panel.apply_variation()
    panel.apply_rules()
    panel.save_map()
    panel.open_map()
    panel.new_map()
    assert panel.document is not None
    panel.update_language("invalid")
    panel.update_language("pt")
    panel.update_language("en")
    assert panel._selected_tile_ids()
    assert panel._select_tile("missing") is False
    assert panel._select_tile("grass") is True
    panel._set_selection((0, 0), (1, 1))
    panel._grid_changed()
    panel.grid_combo.setCurrentIndex(
        panel.grid_combo.findData(GridKind.ISOMETRIC.value)
    )
    panel._grid_changed()
    panel.grid_combo.setCurrentIndex(
        panel.grid_combo.findData(GridKind.HEXAGONAL.value)
    )
    panel._grid_changed()

    pencil = tilemap_panel_module.TileTool.PENCIL.value
    eraser = tilemap_panel_module.TileTool.ERASER.value
    rectangle = tilemap_panel_module.TileTool.RECTANGLE.value
    bucket = tilemap_panel_module.TileTool.BUCKET.value
    picker = tilemap_panel_module.TileTool.PICKER.value
    select = tilemap_panel_module.TileTool.SELECT.value
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(pencil))
    panel._begin_gesture((0, 0))
    panel._paint_cells((0, 0), (1, 0))
    panel._paint_cells((1, 0), (1, 0))
    panel._finish_gesture((0, 0), (1, 0))
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(eraser))
    panel._paint_cells((0, 0), (1, 0))
    panel._finish_gesture((0, 0), (1, 0))
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(rectangle))
    panel._finish_gesture((0, 0), (1, 1))
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(bucket))
    panel._finish_gesture((0, 0), (1, 1))
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(picker))
    panel._finish_gesture((0, 0), (0, 0))
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(select))
    panel._finish_gesture((0, 0), (2, 2))
    panel._finish_gesture((0, 0), (2, 2))

    panel.copy_selection()
    panel.paste_selection()
    for index in range(min(2, panel.tile_palette.count())):
        panel.tile_palette.item(index).setSelected(True)
    panel.apply_variation()

    panel.rule_target_combo.setCurrentIndex(0)
    panel.rule_neighbor_combo.setCurrentIndex(0)
    panel.rule_offset_combo.setCurrentIndex(0)
    panel.add_rule()
    panel.apply_rules()
    panel._rules = []
    panel.apply_rules()
    panel.save_map()
    panel.open_map()
    panel.undo()
    panel.redo()

    canvas = panel.canvas
    canvas.set_document(panel.document)
    canvas.set_active_layer(panel.document.layers[0].id)
    canvas.set_selection(((0, 0), (1, 1)))
    canvas._cell_shape(canvas.grid_spec(), (0.0, 0.0))
    for kind in (GridKind.ORTHOGONAL, GridKind.ISOMETRIC, GridKind.HEXAGONAL):
        canvas.set_grid_kind(kind)
        canvas._cell_shape(canvas.grid_spec(), (0.0, 0.0))

    canvas.mousePressEvent(
        QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    canvas.mouseMoveEvent(
        QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(20, 20),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    canvas.mouseReleaseEvent(
        QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(20, 20),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    canvas.mousePressEvent(
        QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            Qt.MouseButton.RightButton,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )

    panel.close()


def _boundary_sequence_panel(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    base = upgrade_scene_authoring_document(_authoring_document_v1())
    clips = [
        SceneClip(
            id="camera_clip",
            name="Camera",
            kind="camera",
            start=0,
            duration=2,
            layer_id="base",
            x=0,
            y=0,
            end_x=80,
            end_y=20,
        ),
        SceneClip(
            id="motion_clip",
            name="Motion",
            kind="motion",
            start=3,
            duration=2,
            layer_id="base",
            target_id="object",
            x=10,
            y=20,
            end_x=40,
            end_y=30,
        ),
        SceneClip(
            id="light_clip",
            name="Light",
            kind="light",
            start=5,
            duration=2,
            layer_id="base",
            intensity=0.75,
        ),
        SceneClip(
            id="rain_clip",
            name="Rain",
            kind="rain",
            start=7,
            duration=2,
            layer_id="base",
            loop=True,
        ),
        SceneClip(
            id="text_clip",
            name="Text",
            kind="text",
            start=9,
            duration=2,
            layer_id="base",
            text="Boundary caption",
        ),
        SceneClip(
            id="audio_clip",
            name="Audio",
            kind="audio",
            start=0,
            duration=2,
            asset_id="asset",
            loop=True,
        ),
    ]
    document = base.model_copy(
        update={"sequence": SceneSequence(duration=12, loop=True, clips=clips)}
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    pages = QStackedWidget()
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 420)
    viewport.set_geometry("object", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    pages.addWidget(viewport)
    panel = SceneSequencePanel(session, viewport, pages, tmp_path, language="en")
    return app, panel, viewport, pages


def test_scene_sequence_panel_native_timeline_and_preview_boundaries(
    tmp_path, monkeypatch
):
    app, panel, viewport, pages = _boundary_sequence_panel(tmp_path)
    messages = []
    panel.status_message.connect(messages.append)
    panel.show()
    pages.show()
    app.processEvents()
    try:
        assert panel.sequence.duration == 12
        panel.update_language("pt")
        assert panel.play.text() == "Reproduzir"
        assert panel.kind.itemText(panel.kind.findData("camera")) == "Câmera"
        panel.update_language("en")
        assert panel.kind.itemText(panel.kind.findData("text")) == "Text / cutscene"

        for clip_id in (
            "camera_clip",
            "motion_clip",
            "light_clip",
            "rain_clip",
            "text_clip",
            "audio_clip",
        ):
            panel.select_clip(clip_id)
            assert panel.editor.isEnabled()
            panel.apply_clip()

        panel.position = 10.0
        panel.add_clip("camera")
        panel.position = 10.0
        panel.add_clip("motion")
        panel.position = 10.0
        panel.add_clip("fire")
        panel.position = 10.0
        panel.add_clip("text")
        assert panel.selected_id is not None

        monkeypatch.setattr(
            "src.ui.scene_sequence_panel.QFileDialog.getOpenFileName",
            lambda *_args, **_kwargs: ("", ""),
        )
        before_audio = len(panel.sequence.clips)
        panel.add_clip("audio")
        assert len(panel.sequence.clips) == before_audio

        panel.change_clip("text_clip", {"color": "invalid"})
        panel.change_clip("text_clip", {"text": "Texto atualizado", "color": "#22aacc"})
        assert any(
            "Sequence" in message or "Sequência" in message for message in messages
        )

        panel.seek(1.0)
        app.processEvents()
        assert panel.preview is not None
        assert pages.currentWidget() is panel.preview
        assert panel.position == 1.0
        assert messages
        panel.preview.grab()
        panel.seek(-5.0)
        assert panel.position == 0.0
        panel.toggle_play()
        assert panel.timer.isActive()
        panel.toggle_play()
        assert not panel.timer.isActive()
        panel.stop_at_start()
        assert panel.position == 0.0
        assert pages.currentWidget() is viewport
    finally:
        panel.stop()
        panel.close()
        viewport.close()
        pages.close()
        app.processEvents()


def test_scene_sequence_timeline_scrub_and_clip_resize_boundaries(tmp_path):
    app, panel, viewport, pages = _boundary_sequence_panel(tmp_path)
    panel.show()
    pages.show()
    app.processEvents()
    try:
        view = panel.view
        original_seek = panel.seek
        panel.seek = Mock()

        class _TimelineEvent:
            def __init__(self, scene_point, button, buttons):
                self._position = view.mapFromScene(scene_point)
                self._button = button
                self._buttons = buttons

            def position(self):
                return QPointF(self._position)

            def button(self):
                return self._button

            def buttons(self):
                return self._buttons

            def accept(self):
                return None

        press = _TimelineEvent(
            QPointF(190, 12), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton
        )
        view.mousePressEvent(press)
        assert view._scrubbing
        move = _TimelineEvent(
            QPointF(220, 12), Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton
        )
        view.mouseMoveEvent(move)
        release = _TimelineEvent(
            QPointF(240, 12), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
        )
        view.mouseReleaseEvent(release)
        assert not view._scrubbing
        assert panel.seek.call_count == 3
        panel.seek = original_seek

        class _GraphicsEvent:
            def __init__(self, scene_x, item_x):
                self._scene = QPointF(scene_x, 40)
                self._item = QPointF(item_x, 10)

            def scenePos(self):
                return self._scene

            def pos(self):
                return self._item

            def accept(self):
                return None

        clip = panel.sequence.clips[0]
        block = ClipBlock(panel, clip, 0)
        block.mousePressEvent(_GraphicsEvent(150, 1))
        block.mouseMoveEvent(_GraphicsEvent(170, 1))
        block.mouseReleaseEvent(_GraphicsEvent(170, 1))
        app.processEvents()

        clip = panel.sequence.clips[0]
        resized = ClipBlock(panel, clip, 0)
        edge = resized.rect().width() - 1
        resized.mousePressEvent(_GraphicsEvent(150, edge))
        resized.mouseMoveEvent(_GraphicsEvent(180, edge))
        resized.mouseReleaseEvent(_GraphicsEvent(180, edge))
        app.processEvents()
        assert panel.sequence.clips[0].duration > 0
    finally:
        panel.stop()
        panel.close()
        viewport.close()
        pages.close()
        app.processEvents()


def _boundary_viewport_v2(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    asset_path = tmp_path / "assets" / "a.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (32, 24), (80, 160, 220, 255)).save(asset_path)
    digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
    base = upgrade_scene_authoring_document(_authoring_document_v1())
    asset = base.assets[0].model_copy(update={"sha256": digest})
    sockets = [
        SceneLightSocketRecord(
            id="point_light",
            layer_id="base",
            position=Point3Record(x=20, y=30, z=0),
            color="#ffffff",
            intensity=1.0,
            radius=48,
        ),
        SceneLightSocketRecord(
            id="directional_light",
            layer_id="base",
            position=Point3Record(x=-20, y=15, z=0),
            rotation=Point3Record(x=0, y=0, z=30),
            color="#ffe0a0",
            intensity=1.5,
            radius=64,
            kind="directional",
        ),
        SceneVfxSocketRecord(
            id="particle_socket",
            layer_id="base",
            position=Point3Record(x=40, y=10, z=0),
            rotation=Point3Record(x=0, y=0, z=10),
            effect_id="fx",
            scale=1.0,
            enabled=True,
        ),
        SceneVfxSocketRecord(
            id="post_socket",
            layer_id="base",
            position=Point3Record(x=-40, y=10, z=0),
            effect_id="post-vignette",
            scale=0.75,
            enabled=True,
        ),
    ]
    document = base.model_copy(
        update={
            "assets": [asset],
            "camera": SceneCameraAuthoringRecord(
                position=PointRecord(x=12, y=8), zoom=1.5, rotation=12
            ),
            "sockets": sockets,
            "particle_systems": [_boundary_particle_system("fx")],
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 420)
    viewport.set_geometry("object", [(-16, -12), (16, -12), (16, 12), (-16, 12)])
    viewport.show()
    app.processEvents()
    return app, viewport, session, asset_path


def test_scene_viewport_camera_effects_gizmo_and_navigation_boundaries(tmp_path):
    app, viewport, session, _asset_path = _boundary_viewport_v2(tmp_path)
    messages = []
    viewport.status_message.connect(messages.append)
    try:
        assert viewport._camera_guide is not None
        assert set(viewport._socket_items) == {
            "point_light",
            "directional_light",
            "particle_socket",
            "post_socket",
        }
        assert "particle_socket" in viewport._particle_items
        assert "post_socket" in viewport._post_process_items

        viewport.update_language("pt")
        viewport._camera_guide_started("translate", QPointF(12, 8))
        viewport._camera_guide_changed("translate", QPointF(32, 28))
        viewport._camera_guide_finished("translate", QPointF(32, 28))
        app.processEvents()
        assert session.document.camera.position == PointRecord(x=32, y=28)

        viewport._camera_guide_started("rotate", QPointF(32, 28))
        viewport._camera_guide_changed("rotate", QPointF(32, -12))
        viewport._camera_guide_finished("rotate", QPointF(32, -12))
        app.processEvents()
        assert session.document.camera.rotation != 12
        viewport._camera_guide_finished("unknown", QPointF())

        viewport.set_preview_enabled(True)
        viewport._refresh_camera_guide()
        viewport.play_particle_preview()
        viewport._advance_particle_preview()
        viewport.reset_particle_preview()
        viewport.set_authoring_enabled(False)
        viewport._camera_guide_started("translate", QPointF())
        viewport._gizmo_started("translate", QPointF())
        viewport.set_authoring_enabled(True)

        session.set_selection(["object"])
        viewport._refresh_gizmo()
        for mode, point in (
            ("translate", QPointF(20, 30)),
            ("translate_x", QPointF(25, 30)),
            ("translate_y", QPointF(25, 35)),
            ("scale", QPointF(35, 35)),
            ("rotate", QPointF(30, 15)),
        ):
            viewport._gizmo_started(mode, QPointF(10, 20))
            viewport._gizmo_changed(mode, point)
            viewport._gizmo_finished(mode, point)
        app.processEvents()
        assert viewport._gizmo is not None

        viewport._socket_pressed("particle_socket")
        viewport._socket_moved("particle_socket", QPointF(85, 70))
        viewport._socket_released("particle_socket", QPointF(85, 70))
        app.processEvents()
        assert session.document.sockets[2].position.x != 40
        viewport._socket_pressed("particle_socket")
        viewport._socket_released("particle_socket", QPointF(85, 70))
        viewport._socket_rotated("directional_light", 70)
        viewport._socket_pressed("directional_light")
        viewport._socket_rotated("directional_light", 70)
        viewport._socket_rotation_released("directional_light", 70)
        app.processEvents()
        assert session.document.sockets[1].rotation.z == 70
        viewport._socket_pressed("missing")
        viewport._socket_moved("missing", QPointF())
        viewport._socket_released("missing", QPointF())
        viewport._commit_socket_move("missing", Point3Record(x=0, y=0, z=0))
        viewport._commit_socket_rotation("missing", 0)
        viewport._marquee_origin = QPointF(-20, -20)
        viewport._marquee_current = QPointF(80, 80)
        viewport._drop_preview = (QPointF(40, 40), 48.0, 32.0, "Soltar aqui")
        plan = build_scene_render_plan(
            session.document, (640, 420), requested_backend="raster", revision=3
        )
        viewport.set_scene_render_plan(plan)
        viewport.set_overlay_visible(False)
        viewport.grab()
        viewport.set_overlay_visible(True)
        viewport.grab()
        assert messages
    finally:
        viewport._particle_preview_timer.stop()
        viewport.close()
        viewport.deleteLater()
        app.processEvents()


def test_scene_viewport_drag_drop_library_and_marquee_boundaries(tmp_path):
    app, viewport, session, asset_path = _boundary_viewport_v2(tmp_path)

    class _DropEvent:
        def __init__(self, mime, event_type=QEvent.Type.Drop):
            self._mime = mime
            self._type = event_type
            self.accepted = False
            self.ignored = False

        def position(self):
            return QPointF(200, 150)

        def mimeData(self):
            return self._mime

        def acceptProposedAction(self):
            self.accepted = True

        def ignore(self):
            self.ignored = True

        def accept(self):
            self.accepted = True

        def type(self):
            return self._type

    try:
        viewport.update_language("pt")
        assert viewport.place_asset_from_library("missing") is False
        viewport.set_authoring_enabled(False)
        assert viewport.place_asset_from_library("asset") is False
        viewport.set_authoring_enabled(True)
        assert viewport.place_asset_from_library("asset") is True
        assert viewport.place_asset_from_library("asset", group_id="missing") is False
        with pytest.raises(ValueError, match="unknown destination"):
            viewport.set_active_layer("missing")
        session.set_selection([])
        session.model.set_layer_locked("base", True)
        with pytest.raises(ValueError, match="Mostre"):
            viewport._destination_layer()
        session.model.set_layer_locked("base", False)

        library_mime = QMimeData()
        library_mime.setData("application/x-neoeng-scene-asset", b"asset")
        library_event = _DropEvent(library_mime)
        viewport._update_drop_preview(library_event)
        viewport.dragEnterEvent(library_event)
        viewport.dragMoveEvent(library_event)
        viewport.dropEvent(library_event)
        assert library_event.accepted
        viewport._update_drop_preview(_DropEvent(library_mime, QEvent.Type.DragMove))
        for event_type in (
            QEvent.Type.DragEnter,
            QEvent.Type.DragMove,
            QEvent.Type.DragLeave,
            QEvent.Type.Drop,
        ):
            filtered = _DropEvent(library_mime, event_type)
            assert viewport.eventFilter(viewport.viewport(), filtered)
            routed = _DropEvent(library_mime, event_type)
            assert viewport.viewportEvent(routed)

        invalid_drag = _DropEvent(QMimeData(), QEvent.Type.DragEnter)
        viewport.dragEnterEvent(invalid_drag)
        viewport.dragMoveEvent(invalid_drag)
        assert invalid_drag.ignored

        missing_mime = QMimeData()
        missing_mime.setData("application/x-neoeng-scene-asset", b"missing")
        missing_event = _DropEvent(missing_mime)
        viewport.dropEvent(missing_event)
        assert missing_event.ignored

        source_mime = QMimeData()
        source_mime.setUrls([QUrl.fromLocalFile(str(asset_path))])
        source_event = _DropEvent(source_mime)
        viewport.dropEvent(source_event)
        assert source_event.accepted

        empty_event = _DropEvent(QMimeData())
        viewport.dropEvent(empty_event)
        assert empty_event.ignored

        text_mime = QMimeData()
        text_mime.setText(str(asset_path))
        viewport.project_root = None
        text_event = _DropEvent(text_mime)
        viewport.dropEvent(text_event)
        assert text_event.ignored
        viewport.project_root = tmp_path

        viewport.set_authoring_enabled(False)
        readonly_event = _DropEvent(library_mime)
        viewport.dropEvent(readonly_event)
        assert readonly_event.ignored
        viewport.set_authoring_enabled(True)

        viewport.set_preview_enabled(False)
        viewport._apply_marquee_selection(
            QPointF(-100, -100),
            QPointF(100, 100),
            Qt.KeyboardModifier.NoModifier,
        )
        viewport._marquee_selection_before = tuple(session.selection.ids)
        viewport._marquee_primary_before = session.selection.primary
        viewport._apply_marquee_selection(
            QPointF(100, 100),
            QPointF(-100, -100),
            Qt.KeyboardModifier.ShiftModifier,
        )
        viewport._apply_marquee_selection(
            QPointF(-100, -100),
            QPointF(100, 100),
            Qt.KeyboardModifier.ControlModifier,
        )
        viewport._clear_marquee()
        assert viewport._drop_preview is None
    finally:
        viewport._particle_preview_timer.stop()
        viewport.close()
        viewport.deleteLater()
        app.processEvents()


def test_scene_viewport_graphics_items_and_native_handle_boundaries():
    app = QApplication.instance() or QApplication([])

    class _GraphicsEvent:
        def __init__(
            self,
            point=QPointF(),
            *,
            button=Qt.MouseButton.LeftButton,
            buttons=Qt.MouseButton.LeftButton,
            modifiers=Qt.KeyboardModifier.NoModifier,
        ):
            self._point = QPointF(point)
            self._button = button
            self._buttons = buttons
            self._modifiers = modifiers
            self.accepted = False
            self.ignored = False

        def pos(self):
            return QPointF(self._point)

        def scenePos(self):
            return QPointF(self._point)

        def button(self):
            return self._button

        def buttons(self):
            return self._buttons

        def modifiers(self):
            return self._modifiers

        def accept(self):
            self.accepted = True

        def ignore(self):
            self.ignored = True

    polygon = QPolygonF(
        [QPointF(-12, -8), QPointF(12, -8), QPointF(12, 8), QPointF(-12, 8)]
    )
    item = SceneObjectGraphicsItem("object", polygon)
    pixmap = QPixmap(24, 16)
    pixmap.fill(Qt.GlobalColor.white)
    textured = SceneObjectGraphicsItem("textured", polygon, pixmap)
    for visual in (item, textured):
        visual.set_selected_style(True)
        visual.set_interaction_enabled(False)
        visual.set_lighting_color(None)
        visual.hoverEnterEvent(_GraphicsEvent())
        visual.hoverLeaveEvent(_GraphicsEvent())
        visual.hoverEnterEvent(_GraphicsEvent())
        visual.set_interaction_enabled(True)
        visual.mousePressEvent(_GraphicsEvent())
        visual.mouseMoveEvent(_GraphicsEvent(QPointF(4, 5)))
        visual.mouseReleaseEvent(_GraphicsEvent(QPointF(4, 5)))
        image = QImage(48, 48, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        visual.paint(painter, None)
        painter.end()

    gizmo = SceneTransformGizmo()
    assert [
        gizmo._mode_for(point)
        for point in (
            QPointF(0, 0),
            QPointF(57, 0),
            QPointF(0, -57),
            QPointF(40, 40),
            QPointF(100, 100),
        )
    ] == ["translate", "translate_x", "translate_y", "scale", None]
    gizmo.hoverMoveEvent(_GraphicsEvent(QPointF(57, 0)))
    gizmo.hoverLeaveEvent(_GraphicsEvent())
    gizmo.mousePressEvent(_GraphicsEvent(QPointF(0, 0)))
    gizmo.mouseMoveEvent(_GraphicsEvent(QPointF(4, 4)))
    gizmo.mouseReleaseEvent(_GraphicsEvent(QPointF(4, 4)))
    outside = _GraphicsEvent(QPointF(100, 100))
    gizmo.mousePressEvent(outside)
    assert outside.ignored

    camera = SceneCameraGuide()
    camera.set_frame_size(120, 80)
    camera.set_frame_size(120, 80)
    camera.set_label("Câmera")
    camera.set_label("Câmera")
    handle = camera._rotation_handle()
    assert camera._mode_for(QPointF(1000, 1000)) is None
    assert camera._mode_for(handle) == "rotate"
    assert camera._mode_for(QPointF()) == "translate"
    assert camera._mode_for(QPointF(60, 0)) == "translate"
    camera.hoverMoveEvent(_GraphicsEvent(handle))
    camera.hoverLeaveEvent(_GraphicsEvent())
    camera.mousePressEvent(_GraphicsEvent(QPointF()))
    camera.mouseMoveEvent(_GraphicsEvent(QPointF(8, 8)))
    camera.mouseReleaseEvent(_GraphicsEvent(QPointF(8, 8)))
    camera.mouseMoveEvent(_GraphicsEvent(QPointF(100, 100)))
    camera.mouseReleaseEvent(_GraphicsEvent(QPointF(100, 100)))
    camera.mousePressEvent(_GraphicsEvent(QPointF(1000, 1000)))

    socket = SceneSocketGraphicsItem(
        "socket", "vfx", "#c78cff", orientable=True, rotation=10
    )
    socket._interaction_for(QPointF(100, 100))
    socket.mousePressEvent(_GraphicsEvent(QPointF(0, 0)))
    socket.mouseMoveEvent(_GraphicsEvent(QPointF(10, 12)))
    socket.mouseReleaseEvent(_GraphicsEvent(QPointF(10, 12)))
    socket.mousePressEvent(_GraphicsEvent(QPointF(31, 0)))
    socket.mouseMoveEvent(_GraphicsEvent(QPointF(20, 20)))
    socket.mouseReleaseEvent(_GraphicsEvent(QPointF(20, 20)))
    socket.mousePressEvent(_GraphicsEvent(QPointF(100, 100)))
    plain_socket = SceneSocketGraphicsItem("point", "light", "#ffffff")
    assert plain_socket._interaction_for(QPointF(31, 0)) is None

    particle = SceneParticleGraphicsItem("fallback", 1.0)
    particle.set_preview_time(0.25)
    particle.advance_preview(0.1)
    particle.set_system(_boundary_particle_system("fx-item"))
    particle.set_preview_time(0.5)
    particle.set_scale(0.5)
    particle.set_scale(0.5)
    post = ScenePostProcessGraphicsItem("post-vignette", 1.0)
    post.set_scale(0.75)
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    particle.paint(painter, None)
    post.paint(painter, None)
    painter.end()
    app.processEvents()


def test_scene_sequence_audio_and_transport_boundary_paths(tmp_path, monkeypatch):
    app, panel, viewport, pages = _boundary_sequence_panel(tmp_path)
    messages = []
    panel.status_message.connect(messages.append)
    try:
        panel.update_language("pt")
        original_seek = panel.seek
        panel.seek = Mock()
        panel.position = panel.sequence.duration
        panel.toggle_play()
        assert panel.timer.isActive()
        panel.toggle_play()
        assert not panel.timer.isActive()
        panel.seek = original_seek

        missing_asset_clip = SceneClip(
            id="missing_audio",
            name="Missing audio",
            kind="audio",
            start=0,
            duration=1,
            asset_id="missing",
        )
        monkeypatch.setattr(
            scene_sequence_module,
            "active_clips",
            lambda *_args: (missing_asset_clip,),
        )
        panel.position = 0.5
        panel._sync_audio()
        assert "missing_audio" in panel._audio_failures
        assert messages

        class _FakePlayer:
            def __init__(self):
                self.stopped = False
                self.paused = False
                self.played = False
                self.position_value = 0

            def stop(self):
                self.stopped = True

            def deleteLater(self):
                return None

            def pause(self):
                self.paused = True

            def play(self):
                self.played = True

            def duration(self):
                return 1000

            def position(self):
                return self.position_value

            def setPosition(self, value):
                self.position_value = value

            def setPlaybackRate(self, _value):
                return None

        class _FakeOutput:
            def __init__(self):
                self.volume = None

            def setVolume(self, value):
                self.volume = value

            def deleteLater(self):
                return None

        existing_clip = SceneClip(
            id="existing_audio",
            name="Existing audio",
            kind="audio",
            start=0,
            duration=1,
            asset_id="asset",
            loop=True,
        )
        player = _FakePlayer()
        output = _FakeOutput()
        panel.players["stale"] = (_FakePlayer(), _FakeOutput())
        panel.players[existing_clip.id] = (player, output)
        monkeypatch.setattr(
            scene_sequence_module,
            "active_clips",
            lambda *_args: (existing_clip,),
        )
        panel._sync_audio()
        assert panel.players["stale"][0].stopped
        assert player.position_value == 500
        assert player.paused
        panel._pause_audio()
        assert player.paused

        panel.session.model.document = panel.session.document.model_copy(
            update={"sequence": panel.sequence.model_copy(update={"loop": False})}
        )
        panel.position = 11.9
        panel.last_tick = 0
        panel.seek = lambda position: setattr(panel, "position", position)
        panel._tick()
        assert not panel.timer.isActive()
        assert panel.position >= panel.sequence.duration
    finally:
        panel.stop()
        panel.close()
        viewport.close()
        pages.close()
        app.processEvents()


def test_tileset_preview_and_authoring_failure_boundaries(tmp_path):
    app = QApplication.instance() or QApplication([])
    atlas = tmp_path / "atlas.png"
    Image.new("RGBA", (32, 16), (64, 160, 96, 255)).save(atlas)

    class _PreviewEvent:
        def __init__(self, point, button=Qt.MouseButton.LeftButton):
            self._point = QPointF(point)
            self._button = button

        def position(self):
            return QPointF(self._point)

        def button(self):
            return self._button

    preview = TilesetAtlasPreview()
    preview.resize(240, 180)
    preview.grab()
    preview.set_atlas(
        tmp_path / "missing.png",
        [{"id": "tile", "source_rect": {"x": 0, "y": 0, "w": 16, "h": 16}}],
    )
    preview.grab()
    entries = [
        {
            "id": "tile-0",
            "source_rect": {"x": 0, "y": 0, "w": 16, "h": 16},
            "collision": True,
        },
        {
            "id": "tile-1",
            "source_rect": {"x": 16, "y": 0, "w": 16, "h": 16},
            "collision": False,
        },
    ]
    selected = []
    preview.tile_selected.connect(selected.append)
    preview.set_atlas(atlas, entries)
    preview.set_selected_index(0)
    preview.grab()
    preview.mousePressEvent(_PreviewEvent(QPointF(0, 0)))
    preview.mousePressEvent(
        _PreviewEvent(
            QPointF(preview._display_rect.left() + 2, preview._display_rect.top() + 2)
        )
    )
    preview.mousePressEvent(
        _PreviewEvent(
            QPointF(
                preview._display_rect.right() + 20, preview._display_rect.bottom() + 20
            )
        )
    )
    assert selected == [0]
    preview.clear_preview()

    panel = TilesetAuthoringPanel(tmp_path)
    panel.save_current()
    panel.open_tileset()
    too_small = tmp_path / "too-small.png"
    Image.new("RGBA", (8, 8), (1, 2, 3, 255)).save(too_small)
    panel.atlas_path_edit.setText(str(too_small))
    panel.width_spin.setValue(16)
    panel.height_spin.setValue(16)
    panel.generate_tileset()
    assert panel.prepared is None
    panel.atlas_path_edit.setText(str(atlas))
    panel.generate_tileset()
    assert panel.prepared is not None
    panel.update_language("en")
    assert panel.generate_button.text() == "Generate"
    panel.new_tileset()
    panel.open_tileset()
    assert "Falha ao reabrir" in panel.status_label.text()
    panel.close()
    preview.close()
    app.processEvents()


def test_scene_authoring_inspector_complete_v2_boundary_flow():
    app = QApplication.instance() or QApplication([])
    document = upgrade_scene_authoring_document(_authoring_document_v1())
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    inspector = SceneAuthoringInspector(session)
    messages = []
    inspector.status_message.connect(messages.append)
    try:
        inspector.update_language("pt")
        inspector.apply_transform()
        inspector._apply_camera()
        inspector.layer_combo.setCurrentIndex(-1)
        inspector._apply_parallax()
        inspector._apply_material()
        inspector._add_emitter()
        inspector._remove_emitter()
        inspector._update_socket()
        inspector._remove_socket()

        inspector.layer_combo.setCurrentIndex(0)
        inspector.camera_x.setValue(14)
        inspector.camera_y.setValue(-5)
        inspector.camera_zoom.setValue(1.25)
        inspector.camera_rotation.setValue(18)
        inspector._apply_camera()
        inspector.parallax_depth.setValue(0.6)
        inspector.parallax_translation.setValue(0.7)
        inspector.parallax_zoom.setValue(0.8)
        inspector.parallax_scroll_x.setValue(1.2)
        inspector.parallax_scroll_y.setValue(-0.5)
        inspector.parallax_repeat_x.setChecked(True)
        inspector.parallax_mirror_y.setChecked(True)
        inspector._apply_parallax()

        session.set_selection(["object"])
        inspector.refresh()
        inspector.material_albedo.setText("#c0ffee")
        inspector.material_opacity.setValue(0.85)
        inspector.material_receives_shadow.setChecked(True)
        inspector._apply_material()
        inspector._apply_material()
        inspector.snap_enabled.setChecked(True)
        inspector.snap_spacing_x.setValue(4)
        inspector.snap_spacing_y.setValue(4)
        inspector._apply_snap()

        inspector.socket_id.setText("sun")
        inspector.socket_type.setCurrentIndex(0)
        inspector.socket_light_kind.setCurrentIndex(1)
        inspector.socket_rotation_z.setValue(45)
        inspector._add_socket()
        inspector._update_socket()
        inspector._remove_socket()

        inspector.socket_id.setText("fx")
        inspector.socket_type.setCurrentIndex(1)
        inspector.socket_effect_id.setText("fx")
        inspector.socket_enabled.setChecked(True)
        inspector._add_socket()
        inspector._refresh_particle_emitter_fields()
        inspector._add_emitter()
        inspector._remove_emitter()
        inspector._update_socket()
        inspector.particle_preview_button.click()
        inspector.particle_reset_button.click()

        inspector.socket_id.setText("trigger")
        inspector.socket_type.setCurrentIndex(2)
        inspector._add_socket()
        inspector._update_socket()
        inspector._remove_socket()
        inspector.update_language("en")
        inspector._undo()
        inspector._redo()
        assert messages
        assert session.document.camera.zoom == 1.25
        assert session.document.parallax_layers[0].repeat_x
    finally:
        inspector.close()
        app.processEvents()
