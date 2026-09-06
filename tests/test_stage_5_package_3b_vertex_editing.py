"""Stage 5 package 3B: transactional vertex editing."""

from __future__ import annotations

import inspect

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui.canvas_view import CanvasView


class _CanvasStub:
    def __init__(self, scene):
        self.model = scene
        self.update_count = 0
        self._zoom = 1.0

    def update(self):
        self.update_count += 1

    def get_zoom(self):
        return self._zoom


class _MouseEventStub:
    def __init__(self, button):
        self._button = button

    def button(self):
        return self._button


class _KeyEventStub:
    def __init__(self, key):
        self._key = key

    def key(self):
        return self._key


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def _polygon(vertex_count=4):
    if vertex_count == 3:
        return [(20, 20), (180, 20), (100, 160)]
    if vertex_count == 5:
        return [
            (20, 20),
            (180, 20),
            (210, 100),
            (100, 180),
            (10, 100),
        ]
    return [(20, 20), (180, 20), (180, 160), (20, 160)]


def _scene(vertex_count=4, with_collision=True):
    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    scene.add_object(
        "object",
        _polygon(vertex_count),
        select=True,
    )
    if with_collision:
        polygon = scene.objects["object"].polygon
        scene.collision_shapes["object"] = [
            (float(x) + index + 0.25, float(y) + index + 0.5)
            for index, (x, y) in enumerate(polygon)
        ]
    return scene


def _tool(scene):
    return PolygonEditTool(_CanvasStub(scene))


def _start_drag(tool, position):
    tool.on_mouse_press(
        _MouseEventStub(Qt.MouseButton.LeftButton),
        position,
    )
    assert tool._vertex_transaction is not None


def test_vertex_drag_previews_without_history_and_commits_once():
    scene = _scene()
    tool = _tool(scene)
    original = list(scene.objects["object"].polygon)
    start = tuple(original[0])

    _start_drag(tool, start)
    tool.on_mouse_move(
        _MouseEventStub(Qt.MouseButton.NoButton),
        (start[0] + 12, start[1] + 7),
    )
    tool.on_mouse_move(
        _MouseEventStub(Qt.MouseButton.NoButton),
        (start[0] + 18, start[1] + 11),
    )

    assert scene.cmd.undo_count == 0
    assert scene.objects["object"].polygon != original

    result = tool._finish_vertex_gesture()
    assert result is not None
    assert result.status is CommandStatus.APPLIED
    assert scene.cmd.undo_count == 1
    assert tool._vertex_transaction is None
    assert (start[0] + 18, start[1] + 11) in scene.objects["object"].polygon


def test_vertex_drag_undo_redo_restores_exact_collision():
    scene = _scene()
    tool = _tool(scene)
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    start = tuple(original_polygon[1])
    target = (start[0] + 9, start[1] + 13)

    _start_drag(tool, start)
    tool.on_mouse_move(
        _MouseEventStub(Qt.MouseButton.NoButton),
        target,
    )
    tool.on_mouse_release(
        _MouseEventStub(Qt.MouseButton.LeftButton),
        target,
    )
    moved_polygon = list(scene.objects["object"].polygon)

    assert scene.cmd.undo_count == 1
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == moved_polygon
    assert scene.collision_shapes["object"] == [
        (float(x), float(y)) for x, y in moved_polygon
    ]


def test_tool_cancel_restores_vertex_preview_without_history():
    scene = _scene()
    tool = _tool(scene)
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    start = tuple(original_polygon[2])

    _start_drag(tool, start)
    tool.on_mouse_move(
        _MouseEventStub(Qt.MouseButton.NoButton),
        (start[0] - 20, start[1] + 5),
    )
    assert scene.objects["object"].polygon != original_polygon

    tool.on_cancel()

    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0
    assert tool._vertex_transaction is None


def test_escape_cancels_active_vertex_gesture_and_is_consumed():
    scene = _scene()
    tool = _tool(scene)
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    start = tuple(original_polygon[0])

    _start_drag(tool, start)
    tool.on_mouse_move(
        _MouseEventStub(Qt.MouseButton.NoButton),
        (start[0] + 15, start[1] + 6),
    )

    consumed = tool.on_key_press(_KeyEventStub(Qt.Key.Key_Escape))

    assert consumed is True
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0


def test_preview_mode_cancels_active_vertex_gesture(
    qt_app,
):
    scene = _scene()
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    canvas = CanvasView(scene)
    tool = PolygonEditTool(canvas)
    canvas.set_tool(tool.interface())
    tool.selected_polygon_id = "object"
    tool.selected_vertex = 0
    assert tool._begin_vertex_gesture() is True
    tool.drag_start_pos = QPointF(*original_polygon[0])
    tool.on_mouse_move(
        _MouseEventStub(Qt.MouseButton.NoButton),
        (
            original_polygon[0][0] + 22,
            original_polygon[0][1] + 9,
        ),
    )

    canvas.set_preview_mode(True)
    qt_app.processEvents()

    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0
    assert tool._vertex_transaction is None
    canvas.close()


def test_missing_manager_blocks_move_add_and_delete(
    monkeypatch,
):
    scene = _scene(vertex_count=5)
    scene.cmd = None
    tool = _tool(scene)
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    messages = []

    monkeypatch.setattr(
        "src.tools.polygon_edit_tool.QMessageBox.critical",
        lambda *args, **kwargs: messages.append(args),
    )

    start = tuple(original_polygon[0])
    tool.on_mouse_press(
        _MouseEventStub(Qt.MouseButton.LeftButton),
        start,
    )
    tool.selected_polygon_id = "object"
    tool.add_vertex_at_pos((90, 20))
    tool.selected_vertex = 1
    tool.delete_selected_vertex()

    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert tool._vertex_transaction is None
    assert "P2D05-OPERATION" in tool._last_error
    assert "No change was applied" in tool._last_error


def test_add_vertex_uses_one_command_and_round_trips_collision():
    scene = _scene()
    tool = _tool(scene)
    tool.selected_polygon_id = "object"
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    target = (100, 20)

    tool.add_vertex_at_pos(target)

    assert scene.cmd.undo_count == 1
    assert len(scene.objects["object"].polygon) == 5
    assert target in scene.objects["object"].polygon
    assert tool.selected_vertex is not None

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert len(scene.objects["object"].polygon) == 5
    assert target in scene.objects["object"].polygon


def test_delete_vertex_uses_one_command_and_round_trips_collision():
    scene = _scene(vertex_count=5)
    tool = _tool(scene)
    tool.selected_polygon_id = "object"
    tool.selected_vertex = 2
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    deleted = tuple(original_polygon[2])

    tool.delete_selected_vertex()

    assert scene.cmd.undo_count == 1
    assert len(scene.objects["object"].polygon) == 4
    assert deleted not in scene.objects["object"].polygon
    assert tool.selected_vertex is None

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert len(scene.objects["object"].polygon) == 4


def test_triangle_vertex_delete_is_blocked_without_history():
    scene = _scene(vertex_count=3)
    tool = _tool(scene)
    tool.selected_polygon_id = "object"
    tool.selected_vertex = 1
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])

    tool.delete_selected_vertex()

    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0


def test_vertex_edit_paths_have_no_manual_scene_mutation_fallbacks():
    move_source = inspect.getsource(PolygonEditTool.on_mouse_move)
    add_source = inspect.getsource(PolygonEditTool.add_vertex_at_pos)
    delete_source = inspect.getsource(PolygonEditTool.delete_selected_vertex)
    release_source = inspect.getsource(PolygonEditTool.on_mouse_release)
    preview_source = inspect.getsource(CanvasView.set_preview_mode)

    assert "obj.polygon[" not in move_source
    assert "collision_shapes[" not in move_source
    assert "model._notify" not in move_source
    assert "obj.polygon.insert" not in add_source
    assert "collision_shapes[" not in add_source
    assert "model._notify" not in add_source
    assert "obj.polygon.pop" not in delete_source
    assert "collision_shapes[" not in delete_source
    assert "model._notify" not in delete_source
    assert "_finish_vertex_gesture" in release_source
    assert "_tool.on_cancel()" in preview_source
    assert "PolygonGestureTransaction" in inspect.getsource(
        PolygonEditTool._begin_vertex_gesture
    )
    assert "UpdatePolygonCommand" in inspect.getsource(
        PolygonEditTool._execute_polygon_update
    )


def test_mouse_press_starts_vertex_transaction_once(monkeypatch):
    scene = _scene()
    tool = _tool(scene)
    start = tuple(scene.objects["object"].polygon[0])
    calls = 0
    original_begin = tool._begin_vertex_gesture

    def tracked_begin():
        nonlocal calls
        calls += 1
        return original_begin()

    monkeypatch.setattr(
        tool,
        "_begin_vertex_gesture",
        tracked_begin,
    )

    tool.on_mouse_press(
        _MouseEventStub(Qt.MouseButton.LeftButton),
        start,
    )

    assert calls == 1
    assert tool._vertex_transaction is not None
    assert tool.drag_start_pos == QPointF(start[0], start[1])
    assert tool.selected_polygon_id == "object"
    assert tool.selected_vertex is not None

    tool.on_cancel()


def test_polygon_body_click_does_not_leave_legacy_drag_state(
    monkeypatch,
):
    scene = _scene()
    tool = _tool(scene)
    body_position = (100, 80)

    monkeypatch.setattr(
        tool,
        "find_vertex_at",
        lambda pos: (None, None),
    )
    monkeypatch.setattr(
        tool,
        "find_polygon_at",
        lambda pos: "object",
    )

    tool.on_mouse_press(
        _MouseEventStub(Qt.MouseButton.LeftButton),
        body_position,
    )

    assert tool.selected_polygon_id == "object"
    assert tool.selected_vertex is None
    assert tool.selected_polygon_ids == {"object"}
    assert tool.drag_start_pos is None
    assert tool._vertex_transaction is None
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0
