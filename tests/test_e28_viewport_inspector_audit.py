from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui.canvas_view import CanvasView
from src.ui.numeric_controls import ProtectedDoubleSpinBox, ScrubbableLabel


@pytest.fixture(scope="module")
def qt_app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _view_with_two_polygons():
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object("A", [(10, 10), (70, 10), (70, 70), (10, 70)], select=True)
    scene.add_object("B", [(100, 10), (160, 10), (160, 70), (100, 70)])
    scene.image = np.zeros((200, 200, 3), dtype=np.uint8)
    scene.cmd.clear()
    view = CanvasView(scene)
    view.resize(640, 480)
    return scene, view


def test_context_focus_uses_quiet_toolbar_framing(qt_app, monkeypatch):
    scene, view = _view_with_two_polygons()
    try:
        centers: list[tuple[list[tuple[int, int]], int]] = []
        flashes: list[object] = []
        monkeypatch.setattr(
            view,
            "center_on_polygon",
            lambda polygon, margin=50: centers.append((polygon, margin)),
        )
        monkeypatch.setattr(view, "flash_effect", lambda *args: flashes.append(args))
        view.focus_on_object("A")
        assert len(centers) == 1
        assert flashes == []
    finally:
        view.close()


def test_polygon_edit_delete_is_scoped_to_selected_vertex_or_object(qt_app):
    scene, view = _view_with_two_polygons()
    try:
        tool = PolygonEditTool(view)
        view.set_tool(tool.interface())
        tool.selected_polygon_id = "A"
        tool.selected_polygon_ids = {"A"}
        tool.selected_vertex = 1
        original_a = list(scene.objects["A"].polygon)
        original_b = list(scene.objects["B"].polygon)

        tool.delete_selected_vertex()
        assert len(scene.objects["A"].polygon) == len(original_a) - 1
        assert scene.objects["B"].polygon == original_b
        assert "A" in scene.objects and "B" in scene.objects

        tool.selected_polygon_id = "A"
        tool.selected_polygon_ids = {"A"}
        tool.selected_vertex = None
        tool.delete_selected_polygon()
        assert "A" not in scene.objects
        assert "B" in scene.objects
        assert scene.objects["B"].polygon == original_b
    finally:
        view.close()


def test_numeric_fields_support_label_scrubbing_and_ignore_wheel(qt_app):
    _ = qt_app
    field = ProtectedDoubleSpinBox()
    field.setRange(-100.0, 100.0)
    field.setSingleStep(1.0)
    field.setValue(10.0)
    label = ScrubbableLabel("Position X", field)
    label.resize(120, 24)

    class Mouse:
        def __init__(self, x, button):
            self._x = x
            self._button = button

        def position(self):
            return QPointF(self._x, 10.0)

        def button(self):
            return self._button

        def accept(self):
            return None

    label.mousePressEvent(Mouse(10, Qt.MouseButton.LeftButton))
    label.mouseMoveEvent(Mouse(18, Qt.MouseButton.LeftButton))
    label.mouseReleaseEvent(Mouse(18, Qt.MouseButton.LeftButton))
    assert field.value() == pytest.approx(12.0)

    before = field.value()
    event = QWheelEvent(
        QPointF(1, 1),
        QPointF(1, 1),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )
    field.wheelEvent(event)
    assert field.value() == before
