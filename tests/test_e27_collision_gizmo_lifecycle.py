from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.collision_brush_tool import CollisionBrushTool
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui.canvas_view import CanvasView


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _view_with_object():
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object(
        "A",
        [(20, 20), (120, 20), (120, 100), (20, 100)],
        select=True,
    )
    scene.set_object_collision("A", True)
    scene.image = np.zeros((160, 160, 3), dtype=np.uint8)
    scene.cmd.clear()
    view = CanvasView(scene)
    view.resize(640, 480)
    return scene, view


def test_context_scale_selects_object_and_delegates_to_gizmo(qt_app):
    scene, view = _view_with_object()
    try:
        tool = CollisionBrushTool(view)
        view.set_tool(tool.interface())
        origin = list(scene.objects["A"].polygon)

        tool._start_scale("A")

        assert scene.selected_id == "A"
        assert view.is_gizmo_enabled() is True
        assert tool._transform_transaction is None
        assert tool.scaling is False

        # Context-menu Scale must not reintroduce the old free mouse-drag path.
        tool.on_mouse_move(None, (480, 420))
        assert scene.objects["A"].polygon == origin

        assert view._begin_gizmo_object_gesture() is True
        view._preview_gizmo_transform(scale=(1.25, 1.25))
        assert scene.objects["A"].polygon != origin
        assert view._finish_gizmo_gesture() is not None
        assert scene.cmd.undo_count == 1
    finally:
        view.close()


def test_context_edit_transfers_selection_to_polygon_editor(qt_app):
    scene, view = _view_with_object()
    try:
        tool = CollisionBrushTool(view)
        view.set_tool(tool.interface())

        class Palette:
            def select_tool_by_name(self, name):
                assert name == "polygon_edit"
                editor = PolygonEditTool(view)
                view.set_tool(editor.interface())

        tool._start_edit("A", SimpleNamespace(tool_palette=Palette()))

        active = view._active_tool_object()
        assert isinstance(active, PolygonEditTool)
        assert active.selected_polygon_id == "A"
        assert active.selected_polygon_ids == {"A"}
        assert active.mode == "select"
        assert scene.selected_id == "A"
    finally:
        view.close()


def test_gizmo_scale_sensitivity_is_predictable(qt_app):
    _ = qt_app
    scene, view = _view_with_object()
    try:
        assert view._gizmo_scale_factor(
            view.GIZMO_SCALE_PIXELS_PER_DOUBLING
        ) == pytest.approx(2.0)
        assert view._gizmo_scale_factor(
            -view.GIZMO_SCALE_PIXELS_PER_DOUBLING
        ) == pytest.approx(0.5)
        assert view._gizmo_scale_factor(20.0) < 1.1
    finally:
        view.close()
