from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

SHA = "c" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _transform(x: float, y: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document():
    asset = AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)
    layer = SceneLayerAuthoringRecord(id="background", name="Background")
    first = SceneObjectAuthoringRecord(
        id="first", asset_id=asset.id, layer_id=layer.id, transform=_transform(100, 80)
    )
    second = SceneObjectAuthoringRecord(
        id="second",
        asset_id=asset.id,
        layer_id=layer.id,
        transform=_transform(500, 360),
    )
    return upgrade_scene_authoring_document(
        SceneAuthoringDocumentV1(
            metadata=SceneAuthoringMetadataRecord(
                name="P2D-03C test", generator="NeoEng-D-Trace", app_version="0.2.0"
            ),
            project=ProjectReferenceRecord(sha256=SHA),
            assets=[asset],
            layers=[layer],
            objects=[first, second],
            groups=[],
        )
    ).model_copy(
        update={
            "camera": SceneCameraAuthoringRecord(
                position=PointRecord(x=20.0, y=-10.0), zoom=1.5
            ),
            "parallax_layers": [
                SceneParallaxLayerRecord(
                    layer_id="background",
                    depth=0.5,
                    translation_strength=1.0,
                    zoom_strength=1.0,
                )
            ],
            "sockets": [
                SceneLightSocketRecord(
                    id="far-socket",
                    layer_id="background",
                    position=Point3Record(x=5000.0, y=5000.0, z=0.0),
                    color="#ffffff",
                )
            ],
        }
    )


def _viewport(
    qt_app: QApplication, tmp_path: Path
) -> tuple[SceneAuthoringSession, SceneAuthoringViewport]:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 480)
    viewport.set_geometry("first", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    viewport.set_geometry("second", [(-30, -10), (30, -10), (30, 10), (-30, 10)])
    viewport.show()
    qt_app.processEvents()
    return session, viewport


def test_navigation_is_transient_and_wheel_is_cursor_anchored(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session, viewport = _viewport(qt_app, tmp_path)
    try:
        session.set_selection(["first"], "first")
        before_document = session.document.model_dump(mode="json")
        before_history = len(session._undo)
        cursor = QPoint(190, 150)
        anchor_before = viewport.mapToScene(cursor)

        assert viewport._zoom_at(QPointF(cursor), 120.0) is True

        anchor_after = viewport.mapToScene(cursor)
        assert anchor_after.x() == pytest.approx(anchor_before.x(), abs=1.0)
        assert anchor_after.y() == pytest.approx(anchor_before.y(), abs=1.0)
        assert viewport.navigation_zoom == pytest.approx(1.15)
        assert session.document.model_dump(mode="json") == before_document
        assert session.is_dirty is False
        assert len(session._undo) == before_history
    finally:
        viewport.close()
        qt_app.processEvents()


def test_middle_pan_never_moves_objects_or_creates_history(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session, viewport = _viewport(qt_app, tmp_path)
    try:
        session.set_selection(["first"], "first")
        before_document = session.document.model_dump(mode="json")
        before_center = viewport.navigation_center
        QTest.mousePress(
            viewport.viewport(),
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(220, 180),
        )
        QTest.mouseMove(viewport.viewport(), QPoint(280, 240), 0)
        QTest.mouseRelease(
            viewport.viewport(),
            Qt.MouseButton.MiddleButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(280, 240),
        )

        assert viewport.navigation_center != before_center
        assert viewport._pan_origin is None
        assert session.document.model_dump(mode="json") == before_document
        assert session.is_dirty is False
        assert session.can_undo is False
    finally:
        viewport.close()
        qt_app.processEvents()


def test_fit_selection_and_fit_all_exclude_non_content_and_are_noop_safe(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session, viewport = _viewport(qt_app, tmp_path)
    try:
        session.set_selection(["first"], "first")
        before_document = session.document.model_dump(mode="json")
        before_history = len(session._undo)
        selection_bounds = viewport._content_bounds(["first"])
        assert selection_bounds is not None

        assert viewport.fit_selection() is True
        assert viewport.navigation_center.x() == pytest.approx(
            selection_bounds.center().x(), abs=1.0
        )
        assert viewport.navigation_center.y() == pytest.approx(
            selection_bounds.center().y(), abs=1.0
        )
        assert session.document.model_dump(mode="json") == before_document
        assert session.is_dirty is False
        assert len(session._undo) == before_history

        all_bounds = viewport._content_bounds()
        assert all_bounds is not None
        assert viewport.fit_all() is True
        assert viewport.navigation_center.x() == pytest.approx(
            all_bounds.center().x(), abs=1.0
        )
        assert viewport.navigation_center.y() == pytest.approx(
            all_bounds.center().y(), abs=1.0
        )
        assert viewport.navigation_center.x() < 1000.0

        session.clear_selection()
        before_navigation = (viewport.navigation_zoom, viewport.navigation_center)
        assert viewport.fit_selection() is False
        assert viewport.navigation_zoom == before_navigation[0]
        assert viewport.navigation_center == before_navigation[1]
        assert session.document.model_dump(mode="json") == before_document
    finally:
        viewport.close()
        qt_app.processEvents()


def test_preview_navigation_keeps_camera_persistence_and_world_round_trip(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session, viewport = _viewport(qt_app, tmp_path)
    try:
        viewport.set_preview_enabled(True)
        viewport._zoom_at(QPointF(240.0, 180.0), 120.0)
        world = Point3Record(x=32.0, y=48.0, z=0.0)
        projected = viewport._project_position(world, "background")
        viewport_point = viewport.mapFromScene(projected)
        round_trip = viewport._world_position(
            viewport.mapToScene(viewport_point), "background"
        )
        assert round_trip.x() == pytest.approx(world.x, abs=1.0)
        assert round_trip.y() == pytest.approx(world.y, abs=1.0)
        assert session.document.camera.position.x == 20.0
        assert session.document.camera.position.y == -10.0
        assert session.document.camera.zoom == 1.5
        assert session.is_dirty is False
    finally:
        viewport.close()
        qt_app.processEvents()


def test_fit_all_empty_scene_is_a_safe_noop(
    qt_app: QApplication, tmp_path: Path
) -> None:
    document = _document().model_copy(update={"objects": [], "sockets": []})
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 480)
    viewport.show()
    qt_app.processEvents()
    try:
        before_navigation = (viewport.navigation_zoom, viewport.navigation_center)
        before_document = session.document.model_dump(mode="json")
        assert viewport.fit_all() is False
        assert viewport.navigation_zoom == before_navigation[0]
        assert viewport.navigation_center == before_navigation[1]
        assert session.document.model_dump(mode="json") == before_document
        assert session.is_dirty is False
    finally:
        viewport.close()
        qt_app.processEvents()


def test_fit_selection_uses_transformed_scene_bounds(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session, viewport = _viewport(qt_app, tmp_path)
    try:
        transformed = session.document.objects[0].model_copy(
            update={
                "transform": session.document.objects[0].transform.model_copy(
                    update={
                        "rotation": Point3Record(x=0.0, y=0.0, z=45.0),
                        "scale": Point3Record(x=2.0, y=1.5, z=1.0),
                        "flip_x": True,
                        "flip_y": True,
                    }
                )
            }
        )
        session.model.document = session.document.model_copy(
            update={"objects": [transformed, *session.document.objects[1:]]}
        )
        viewport.sync()
        session.set_selection(["first"], "first")
        expected = viewport._content_bounds(["first"])
        assert expected is not None
        assert viewport.fit_selection() is True
        assert viewport.navigation_center.x() == pytest.approx(
            expected.center().x(), abs=1.0
        )
        assert viewport.navigation_center.y() == pytest.approx(
            expected.center().y(), abs=1.0
        )
        assert viewport.navigation_zoom > 0.0
    finally:
        viewport.close()
        qt_app.processEvents()
