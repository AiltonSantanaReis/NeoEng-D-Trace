from __future__ import annotations

import pytest

from src.core.scene_render_plan import (
    RENDER_PASSES,
    RenderPlanCache,
    build_scene_render_plan,
    select_render_backend,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneTransformRecord,
)


def _transform(x: float, y: float, z: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=z),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document() -> SceneAuthoringDocumentV2:
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="E08 renderer", generator="test", app_version="0"
        ),
        project=ProjectReferenceRecord(sha256="1" * 64),
        assets=[
            AssetReferenceRecord(id="asset", path="assets/asset.png", sha256="1" * 64)
        ],
        layers=[
            SceneLayerAuthoringRecord(id="far", name="Far"),
            SceneLayerAuthoringRecord(id="front", name="Front"),
        ],
        objects=[
            SceneObjectAuthoringRecord(
                id="front-object",
                asset_id="asset",
                layer_id="front",
                transform=_transform(4.0, 4.0, 8.0),
            )
        ],
        groups=[],
        parallax_layers=[SceneParallaxLayerRecord(layer_id="far", depth=1.0)],
    )


def test_render_plan_has_explicit_order_and_layer_bindings():
    plan = build_scene_render_plan(_document(), (1280, 720))

    assert plan.passes == RENDER_PASSES
    assert [layer.layer_id for layer in plan.layers] == ["far", "front"]
    assert plan.layers[0].depth == 1.0
    assert plan.layers[1].object_ids == ("front-object",)
    assert plan.object_order()["front-object"] == (1, 0, 0.0)


def test_renderer_backend_fallback_is_explicit():
    state = select_render_backend("opengl", opengl_available=False)

    assert state.selected == "raster"
    assert state.status == "fallback"
    assert "unavailable" in state.reason


def test_render_plan_cache_reuses_and_invalidates_deterministically():
    document = _document()
    cache = RenderPlanCache()
    first = cache.build(document, (640, 360))
    same = cache.build(document, (640, 360))
    resized = cache.build(document, (800, 450))

    assert same is first
    assert resized is not first
    assert resized.revision == first.revision + 1

    cache.invalidate()
    rebuilt = cache.build(document, (800, 450))
    assert rebuilt.revision == resized.revision + 1


def test_render_plan_rejects_invalid_viewport():
    with pytest.raises(ValueError, match="positive integers"):
        build_scene_render_plan(_document(), (0, 720))
