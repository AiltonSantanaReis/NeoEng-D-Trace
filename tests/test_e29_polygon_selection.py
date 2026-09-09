from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools import polygon_edit_tool as polygon_module
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui.canvas_view import CanvasView


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _event(button=Qt.MouseButton.LeftButton, modifiers=Qt.KeyboardModifier.NoModifier):
    event = SimpleNamespace()
    event.button = lambda: button
    event.modifiers = lambda: modifiers
    event.position = lambda: QPointF(10, 10)
    event.pos = lambda: QPoint(10, 10)
    event.globalPos = lambda: QPoint(10, 10)
    return event


def _view(qt_app):
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object(
        "A",
        [(10, 10), (70, 10), (90, 40), (70, 70), (10, 70)],
        select=True,
    )
    scene.image = np.zeros((120, 120, 3), dtype=np.uint8)
    scene.cmd.clear()
    view = CanvasView(scene)
    view.resize(320, 240)
    return scene, view


def test_right_click_vertex_binds_vertex_target_and_never_deletes_object(qt_app):
    scene, view = _view(qt_app)
    tool = PolygonEditTool(view)
    try:
        tool._context_image_pos = (10, 10)
        target = tool._resolve_context_target(tool._context_image_pos)

        assert target == ("vertex", "A", 0)
        assert tool.selected_vertices == {("A", 0)}

        tool.delete_selected_vertex(*target[1:])

        assert "A" in scene.objects
        assert len(scene.objects["A"].polygon) == 4
    finally:
        view.close()


def test_context_menu_for_vertex_excludes_polygon_deletion(qt_app, monkeypatch):
    scene, view = _view(qt_app)
    tool = PolygonEditTool(view)
    actions = []

    class ActionProbe:
        def __init__(self, text):
            self.text = text
            self.triggered = SimpleNamespace(connect=lambda callback: None)

    class MenuProbe:
        def __init__(self, parent):
            pass

        def addAction(self, text):
            action = ActionProbe(text)
            actions.append(action)
            return action

        def addSeparator(self):
            pass

        def exec(self, position):
            pass

    monkeypatch.setattr(polygon_module, "QMenu", MenuProbe)
    try:
        tool.update_language("pt")
        tool._context_image_pos = (10, 10)
        tool.show_context_menu(_event(Qt.MouseButton.RightButton))
        labels = [action.text for action in actions]

        assert "Excluir vértice" in labels
        assert "Excluir polígono" not in labels
        assert "A" in scene.objects
    finally:
        view.close()


def test_ctrl_click_selects_multiple_vertices_and_deletes_them_as_one_command(qt_app):
    scene, view = _view(qt_app)
    tool = PolygonEditTool(view)
    try:
        tool.on_mouse_press(_event(), (10, 10))
        tool.on_mouse_release(_event(), (10, 10))
        tool.on_mouse_press(
            _event(
                modifiers=Qt.KeyboardModifier.ControlModifier,
            ),
            (70, 10),
        )

        assert tool.selected_vertices == {("A", 0), ("A", 1)}
        assert tool.selected_polygon_ids == {"A"}

        tool.delete_selected_vertices()

        assert "A" in scene.objects
        assert len(scene.objects["A"].polygon) == 3
        assert scene.cmd.undo_count == 1
        assert tool.selected_vertices == set()
    finally:
        view.close()


def test_ctrl_click_selects_multiple_polygons(qt_app):
    scene, view = _view(qt_app)
    scene.add_object(
        "B",
        [(80, 80), (115, 80), (100, 115)],
        select=False,
    )
    scene.cmd.clear()
    tool = PolygonEditTool(view)
    try:
        tool.on_mouse_press(_event(), (30, 30))
        tool.on_mouse_press(
            _event(modifiers=Qt.KeyboardModifier.ControlModifier),
            (95, 95),
        )

        assert tool.selected_polygon_ids == {"A", "B"}
        assert tool.selected_polygon_id == "B"
    finally:
        view.close()
