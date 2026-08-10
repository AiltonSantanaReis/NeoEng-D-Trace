"""Stage 5 package 4B: transactional collision move and scale."""

from __future__ import annotations

import inspect

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.core.commands import (
    CommandManager,
    CommandStatus,
    ToggleCollisionCommand,
)
from src.models.scene import Scene
from src.tools.collision_brush_tool import CollisionBrushTool


class _CanvasStub:
    def __init__(self, scene):
        self.model = scene
        self.update_count = 0

    def update(self):
        self.update_count += 1

    def get_zoom(self):
        return 1.0

    def parent(self):
        return None


class _MouseEventStub:
    def __init__(self, button=Qt.MouseButton.LeftButton, key=None):
        self._button = button
        self._key = key

    def button(self):
        return self._button

    def key(self):
        return self._key


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def _scene():
    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    scene.add_object(
        "A",
        [(10, 10), (110, 10), (110, 90), (10, 90)],
        select=True,
    )
    scene.collision_shapes["A"] = [
        (12.25, 13.50),
        (112.25, 13.50),
        (112.25, 93.50),
        (12.25, 93.50),
    ]
    scene.cmd.clear()
    return scene


def _tool(scene):
    return CollisionBrushTool(_CanvasStub(scene))


def _snapshot(scene):
    return {
        "polygon": list(scene.objects["A"].polygon),
        "collision": list(scene.collision_shapes["A"]),
        "selected_id": scene.selected_id,
    }


def _assert_points_close(actual, expected):
    assert len(actual) == len(expected)
    for actual_point, expected_point in zip(actual, expected):
        assert actual_point[0] == pytest.approx(expected_point[0])
        assert actual_point[1] == pytest.approx(expected_point[1])


def _scaled(points, center, factor, *, integer):
    output = []
    for x, y in points:
        new_x = center[0] + (x - center[0]) * factor
        new_y = center[1] + (y - center[1]) * factor
        if integer:
            output.append(
                (
                    int(round(new_x)),
                    int(round(new_y)),
                )
            )
        else:
            output.append((new_x, new_y))
    return output


def _preview_move(tool):
    tool._start_move("A", None)
    tool.on_mouse_move(_MouseEventStub(), (200, 200))
    tool.on_mouse_move(_MouseEventStub(), (225, 235))


def _preview_scale(tool, delta_y=100):
    tool._start_scale("A", None)
    tool.on_mouse_move(_MouseEventStub(), (200, 200))
    tool.on_mouse_move(
        _MouseEventStub(),
        (200, 200 + delta_y),
    )


def test_move_previews_without_history_and_commits_once():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_move(tool)

    assert scene.objects["A"].polygon == [
        (x + 25, y + 35) for x, y in origin["polygon"]
    ]
    assert scene.collision_shapes["A"] == [
        (x + 25, y + 35) for x, y in origin["collision"]
    ]
    assert scene.cmd.undo_count == 0
    assert tool._transform_transaction is not None

    tool.on_mouse_release(_MouseEventStub(), (225, 235))

    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0
    assert tool._transform_transaction is None
    assert tool.moving is False
    assert tool.moving_oid is None
    assert tool.last_pos is None


def test_move_undo_redo_restores_exact_custom_collision():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_move(tool)
    tool.on_mouse_release(_MouseEventStub(), (225, 235))
    moved = _snapshot(scene)

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert _snapshot(scene) == origin
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert _snapshot(scene) == moved


def test_move_noop_creates_no_history():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    tool._start_move("A", None)
    tool.on_mouse_move(_MouseEventStub(), (200, 200))
    tool.on_mouse_release(_MouseEventStub(), (200, 200))

    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0
    assert tool._transform_transaction is None


def test_move_cancel_restores_exact_geometry_without_history():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_move(tool)
    tool.on_cancel()

    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0
    assert tool._transform_transaction is None
    assert tool.moving is False


def test_scale_mouse_preview_is_absolute_not_compounded():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    tool._start_scale("A", None)
    center = tool.scale_center
    assert center is not None

    tool.on_mouse_move(_MouseEventStub(), (200, 200))
    tool.on_mouse_move(_MouseEventStub(), (200, 300))
    assert scene.objects["A"].polygon == _scaled(
        origin["polygon"],
        center,
        1.1,
        integer=True,
    )

    tool.on_mouse_move(_MouseEventStub(), (200, 400))
    assert tool.initial_scale == pytest.approx(1.2)
    assert scene.objects["A"].polygon == _scaled(
        origin["polygon"],
        center,
        1.2,
        integer=True,
    )
    _assert_points_close(
        scene.collision_shapes["A"],
        _scaled(
            origin["collision"],
            center,
            1.2,
            integer=False,
        ),
    )
    assert scene.cmd.undo_count == 0


def test_scale_commits_once_and_preserves_custom_collision_shape():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_scale(tool, 100)
    center = tool.scale_center
    assert center is not None
    expected_collision = _scaled(
        origin["collision"],
        center,
        1.1,
        integer=False,
    )

    tool.on_mouse_press(_MouseEventStub(), (200, 300))

    assert scene.cmd.undo_count == 1
    _assert_points_close(
        scene.collision_shapes["A"],
        expected_collision,
    )
    assert tool._transform_transaction is None
    assert tool.scaling is False
    assert tool.scale_center is None


def test_scale_undo_redo_restores_exact_geometry():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_scale(tool, 100)
    tool.on_mouse_release(_MouseEventStub(), (200, 300))
    scaled = _snapshot(scene)

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert _snapshot(scene) == origin
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert _snapshot(scene) == scaled


def test_scale_menu_steps_preview_from_origin_and_commit_once():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    tool._start_scale("A", None)
    center = tool.scale_center
    assert center is not None

    tool._scale_increase("A")
    assert tool.initial_scale == pytest.approx(1.1)
    assert scene.objects["A"].polygon == _scaled(
        origin["polygon"],
        center,
        1.1,
        integer=True,
    )

    tool._scale_decrease("A")
    assert tool.initial_scale == pytest.approx(0.99)
    assert scene.objects["A"].polygon == _scaled(
        origin["polygon"],
        center,
        0.99,
        integer=True,
    )
    assert scene.cmd.undo_count == 0

    tool.on_mouse_press(_MouseEventStub(), (0, 0))

    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0


def test_cancel_scale_restores_exact_geometry_without_history():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_scale(tool, 150)
    tool._cancel_scale()

    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0
    assert tool._transform_transaction is None
    assert tool.scaling is False


def test_switch_scale_to_move_cancels_scale_before_new_transaction():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_scale(tool, 150)
    tool._switch_to_move("A")

    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0
    assert tool.scaling is False
    assert tool.moving is True
    assert tool.moving_oid == "A"
    assert tool._transform_transaction is not None


def test_escape_cancels_active_transform():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_move(tool)
    consumed = tool.on_key_press(_MouseEventStub(key=Qt.Key.Key_Escape))

    assert consumed is True
    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0


def test_undo_hook_cancels_active_transform_without_touching_history():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_scale(tool, 100)
    consumed = tool.on_undo()

    assert consumed is True
    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_redo_hook_cancels_active_transform_without_touching_history():
    scene = _scene()
    tool = _tool(scene)
    origin = _snapshot(scene)

    _preview_move(tool)
    consumed = tool.on_redo()

    assert consumed is True
    assert _snapshot(scene) == origin
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_menu_undo_cancels_active_gesture_without_undoing_history():
    scene = _scene()
    scene.add_object(
        "B",
        [(160, 10), (220, 10), (220, 70), (160, 70)],
        select=False,
    )
    scene.cmd.clear()
    result = scene.cmd.execute(
        ToggleCollisionCommand("B"),
        scene,
    )
    assert result.status is CommandStatus.APPLIED
    assert "B" in scene.collision_shapes
    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0

    tool = _tool(scene)
    origin = _snapshot(scene)
    _preview_move(tool)

    tool._undo()

    assert _snapshot(scene) == origin
    assert "B" in scene.collision_shapes
    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0
    assert tool._transform_transaction is None
    assert tool.moving is False


def test_menu_redo_cancels_active_gesture_without_redoing_history():
    scene = _scene()
    scene.add_object(
        "B",
        [(160, 10), (220, 10), (220, 70), (160, 70)],
        select=False,
    )
    scene.cmd.clear()
    result = scene.cmd.execute(
        ToggleCollisionCommand("B"),
        scene,
    )
    assert result.status is CommandStatus.APPLIED
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert "B" not in scene.collision_shapes
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 1

    tool = _tool(scene)
    origin = _snapshot(scene)
    _preview_scale(tool, 100)

    tool._redo()

    assert _snapshot(scene) == origin
    assert "B" not in scene.collision_shapes
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 1
    assert tool._transform_transaction is None
    assert tool.scaling is False


def test_missing_manager_blocks_move_and_scale(monkeypatch):
    scene = _scene()
    scene.cmd = None
    tool = _tool(scene)
    origin = _snapshot(scene)
    messages = []

    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.critical",
        lambda *args, **kwargs: messages.append(args),
    )

    tool._start_move("A", None)
    tool._start_scale("A", None)

    assert _snapshot(scene) == origin
    assert tool._transform_transaction is None
    assert tool.moving is False
    assert tool.scaling is False
    assert len(messages) == 2
    assert all("history is unavailable" in str(message) for message in messages)


def test_collision_transform_paths_have_no_direct_scene_mutation():
    move = inspect.getsource(CollisionBrushTool._preview_move)
    scale = inspect.getsource(CollisionBrushTool._apply_scale)
    event_move = inspect.getsource(CollisionBrushTool.on_mouse_move)
    finish = inspect.getsource(CollisionBrushTool._finish_transform_gesture)

    combined = "\n".join((move, scale, event_move, finish))
    assert "obj.polygon =" not in combined
    assert "collision_shapes[" not in combined
    assert "model._notify(" not in combined
    assert "ObjectGeometryGestureTransaction" in inspect.getsource(
        CollisionBrushTool._begin_transform_gesture
    )
    assert "transaction.preview(" in inspect.getsource(
        CollisionBrushTool._preview_transform_geometry
    )
    assert "transaction.commit(" in finish
