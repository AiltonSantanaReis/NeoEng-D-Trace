"""E08-D particle authoring/render integration checks."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneVfxSocketRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scene_authoring_viewport import (
    SceneAuthoringViewport,
    SceneParticleGraphicsItem,
    ScenePostProcessGraphicsItem,
)

SHA = "d" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _document():
    asset = AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)
    layer = SceneLayerAuthoringRecord(id="layer", name="FX")
    base = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="E08-D FX", generator="NeoEng-D-Trace", app_version="0.3.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[asset],
        layers=[layer],
        objects=[
            SceneObjectAuthoringRecord(
                id="object",
                asset_id=asset.id,
                layer_id=layer.id,
                transform=SceneTransformRecord(
                    position=Point3Record(x=0.0, y=0.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )
        ],
        groups=[],
    )
    return upgrade_scene_authoring_document(base).model_copy(
        update={
            "sockets": [
                SceneVfxSocketRecord(
                    id="spark",
                    layer_id=layer.id,
                    position=Point3Record(x=80.0, y=60.0, z=0.0),
                    effect_id="spark-fx",
                    scale=1.25,
                    enabled=True,
                )
            ]
        }
    )


def test_particle_preview_is_seeded_and_observable() -> None:
    first = SceneParticleGraphicsItem("spark-fx", 1.25)
    second = SceneParticleGraphicsItem("spark-fx", 1.25)
    assert first._states
    assert first._states == second._states
    assert first.boundingRect().width() == pytest.approx(240.0)


def test_vfx_socket_creates_particle_pixels_in_professional_viewport(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 480)
    viewport.show()
    qt_app.processEvents()
    try:
        assert "spark" in viewport._particle_items
        particle = viewport._particle_items["spark"]
        assert particle._states
        assert particle.pos().x() == pytest.approx(80.0)
        assert particle.pos().y() == pytest.approx(60.0)
    finally:
        viewport.close()
        qt_app.processEvents()


def test_post_process_preview_is_ordered_and_observable() -> None:
    item = ScenePostProcessGraphicsItem("post-vignette", 1.0)

    assert item._applied_effect_ids == ("warm-tint", "vignette")
    assert item._edge_color.alpha() == 135
    assert item._edge_color.red() < 255
    assert item.boundingRect().width() == pytest.approx(4000.0)


def test_post_process_socket_creates_overlay_in_professional_viewport(
    qt_app: QApplication, tmp_path: Path
) -> None:
    document = _document().model_copy(
        update={
            "sockets": [
                SceneVfxSocketRecord(
                    id="post-vignette",
                    layer_id="layer",
                    position=Point3Record(x=0.0, y=0.0, z=0.0),
                    effect_id="post-vignette",
                    scale=1.0,
                    enabled=True,
                )
            ]
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 480)
    viewport.show()
    qt_app.processEvents()
    try:
        assert "post-vignette" in viewport._post_process_items
        post_process = viewport._post_process_items["post-vignette"]
        assert post_process._applied_effect_ids == ("warm-tint", "vignette")
        assert post_process.pos().x() == pytest.approx(0.0)
        assert post_process.pos().y() == pytest.approx(0.0)
    finally:
        viewport.close()
        qt_app.processEvents()
