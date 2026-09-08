"""E08-B contract tests for independent camera/parallax controls."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scene_authoring_bridge import preview_layers_from_professional_document
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_preview import build_scene_authoring_preview
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector

SHA = "c" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _document() -> SceneAuthoringDocumentV2:
    legacy = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="E08-B", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="background", name="Background")],
        objects=[
            SceneObjectAuthoringRecord(
                id="object",
                asset_id="asset",
                layer_id="background",
                transform=SceneTransformRecord(
                    position=Point3Record(x=10.0, y=-5.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )
        ],
        groups=[],
    )
    upgraded = upgrade_scene_authoring_document(legacy)
    assert isinstance(upgraded, SceneAuthoringDocumentV2)
    return upgraded


def test_legacy_defaults_preserve_projection_exactly() -> None:
    camera = OrthographicCamera((800, 600), position=(100.0, -50.0), zoom=2.0)
    legacy = ParallaxLayer(depth=0.5, translation_strength=0.4, zoom_strength=0.8)
    explicit = ParallaxLayer(
        depth=0.5,
        translation_strength=0.4,
        zoom_strength=0.8,
        scroll_x=1.0,
        scroll_y=1.0,
        offset_x=0.0,
        offset_y=0.0,
    )
    assert camera.project((12.0, 8.0), legacy) == camera.project((12.0, 8.0), explicit)


def test_axis_scroll_offsets_and_negative_motion_are_independent() -> None:
    camera = OrthographicCamera((800, 600), position=(100.0, -50.0), zoom=1.5)
    layer = ParallaxLayer(scroll_x=-0.5, scroll_y=2.0, offset_x=12.0, offset_y=-7.0)
    projected = camera.project((0.0, 0.0), layer)

    assert projected == pytest.approx((493.0, 439.5))
    assert camera.unproject(projected, layer) == pytest.approx((0.0, 0.0))


def test_repeat_and_mirror_variants_are_deterministic_and_seam_ready() -> None:
    layer = ParallaxLayer(repeat_x=True, repeat_y=True, mirror_x=True, mirror_y=True)

    variants = layer.tile_variants((64.0, 32.0), radius=1)

    assert len(variants) == 9
    assert variants[0] == (-64.0, -32.0, True, True)
    assert variants[4] == (0.0, 0.0, False, False)
    assert variants[-1] == (64.0, 32.0, True, True)
    assert ParallaxLayer().tile_variants((64.0, 32.0)) == ((0.0, 0.0, False, False),)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SceneParallaxLayerRecord(layer_id="background", scroll_x=4.1),
        lambda: SceneParallaxLayerRecord(layer_id="background", scroll_y=-4.1),
        lambda: SceneParallaxLayerRecord(layer_id="background", offset_x=float("inf")),
        lambda: ParallaxLayer(scroll_x=4.1),
        lambda: ParallaxLayer(scroll_y=-4.1),
        lambda: ParallaxLayer(repeat_x=1),  # type: ignore[arg-type]
    ],
)
def test_e08b_limits_and_types_are_fail_closed(factory) -> None:
    with pytest.raises(ValueError):
        factory()


def test_schema_round_trip_and_runtime_bridge_preserve_new_fields() -> None:
    document = _document().model_copy(
        update={
            "parallax_layers": [
                SceneParallaxLayerRecord(
                    layer_id="background",
                    depth=0.8,
                    scroll_x=-0.5,
                    scroll_y=1.5,
                    offset_x=12.0,
                    offset_y=-7.0,
                    repeat_x=True,
                    mirror_y=True,
                )
            ]
        }
    )
    restored = SceneAuthoringDocumentV2.model_validate(
        document.model_dump(mode="json"), strict=True
    )
    runtime = preview_layers_from_professional_document(restored)[0].parallax

    assert runtime.scroll_x == -0.5
    assert runtime.scroll_y == 1.5
    assert runtime.offset_x == 12.0
    assert runtime.offset_y == -7.0
    assert runtime.repeat_x is True
    assert runtime.mirror_y is True


def test_transactional_edit_updates_preview_without_double_application() -> None:
    document = _document()
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    session.set_parallax_layer(
        SceneParallaxLayerRecord(
            layer_id="background",
            scroll_x=-0.5,
            scroll_y=2.0,
            offset_x=12.0,
            offset_y=-7.0,
        )
    )
    assert isinstance(session.document, SceneAuthoringDocumentV2)
    first = build_scene_authoring_preview(
        session.document,
        (800.0, 600.0),
        {"object": [(-1.0, -1.0), (1.0, 1.0)]},
    )
    assert session.undo() is True
    assert session.document.parallax_layers == []
    assert first.objects[0].origin == pytest.approx((422.0, 288.0))


def test_professional_inspector_localizes_e08b_controls(qt_app) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    inspector = SceneAuthoringInspector(session)
    try:
        inspector.update_language("pt")
        assert inspector.stage4_group.title() == "Câmera, Paralaxe e Sockets"
        assert inspector.parallax_scroll_x is not None
        assert inspector.parallax_repeat_x.text() == "Repetir X"
        inspector.update_language("en")
        assert inspector.stage4_group.title() == "Camera, Parallax & Sockets"
        assert inspector.parallax_mirror_y.text() == "Mirror Y"
    finally:
        inspector.deleteLater()
        qt_app.processEvents()
