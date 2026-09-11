"""Focused behavior contracts for the post-E13 authoring UX increment."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsScene

from src.persistence.project_schema import PointRecord
from src.persistence.scene_authoring_schema import SceneCameraAuthoringRecord
from src.ui.scene_authoring_viewport import SceneCameraGuide
from src.ui.scene_sequence_panel import TimelineView


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_camera_authoring_rotation_is_backward_compatible_and_bounded() -> None:
    legacy = SceneCameraAuthoringRecord(position=PointRecord(x=12.0, y=-8.0), zoom=1.25)
    rotated = legacy.model_copy(update={"rotation": 42.0})

    assert legacy.rotation == 0.0
    assert rotated.rotation == 42.0
    with pytest.raises(ValueError):
        SceneCameraAuthoringRecord(rotation=36001.0)


def test_camera_guide_exposes_distinct_translate_and_rotate_handles(qt_app) -> None:
    scene = QGraphicsScene(qt_app)
    guide = SceneCameraGuide()
    scene.addItem(guide)
    try:
        guide.set_frame_size(400.0, 200.0)

        assert guide._mode_for(QPointF(0.0, 0.0)) == "translate"
        assert guide._mode_for(QPointF(0.0, 100.0)) == "translate"
        assert guide._mode_for(guide._rotation_handle()) == "rotate"
        assert guide._mode_for(QPointF(0.0, 40.0)) is None
    finally:
        scene.clear()
        guide = None
        qt_app.processEvents()


def test_camera_guide_localized_hint_stays_inside_its_paint_bounds(qt_app) -> None:
    scene = QGraphicsScene(qt_app)
    guide = SceneCameraGuide()
    scene.addItem(guide)
    try:
        guide.set_frame_size(640.0, 360.0)
        guide.set_label("CÂMERA · ARRASTE PARA POSICIONAR")

        label_rect = QRectF(
            -320.0 + 10.0,
            180.0 - 36.0,
            guide._label_width(),
            26.0,
        )
        assert guide._label_width() > 188.0
        assert guide.boundingRect().contains(label_rect)
    finally:
        scene.clear()
        guide = None
        qt_app.processEvents()


def test_timeline_header_scrubs_continuously_during_drag(qt_app) -> None:
    class Parent:
        pixels_per_second = 10.0

        def __init__(self):
            self.positions = []

        def seek(self, position):
            self.positions.append(position)

    scene = QGraphicsScene()
    scene.setSceneRect(0.0, 0.0, 600.0, 80.0)
    view = TimelineView(scene)
    view.parent_panel = Parent()
    view.resize(600, 80)
    view.show()
    qt_app.processEvents()
    try:
        QTest.mousePress(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(250, 10),
        )
        QTest.mouseMove(view.viewport(), QPoint(350, 10), 10)
        QTest.mouseRelease(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(350, 10),
        )

        assert view.parent_panel.positions[0] == pytest.approx(10.0, abs=0.25)
        assert view.parent_panel.positions[-1] == pytest.approx(20.0, abs=0.25)
        assert len(view.parent_panel.positions) >= 2
    finally:
        view.close()
        qt_app.processEvents()
