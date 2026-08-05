"""Stage 5 package 5C: Bézier creation and handle history contracts."""

from __future__ import annotations

import copy
import math
import os

import pytest

from src.core.bezier_geometry import (
    canonicalize_beziers,
    sample_beziers,
    sample_beziers_to_polygon,
)
from src.core.commands import (
    CommandManager,
    CommandResult,
    CommandStatus,
    CreateBezierObjectCommand,
    HandleMoveCommand,
)
from src.models.scene import Scene

BEZIERS = [((0, 0), (0, -100), (100, -100), (100, 0))]
NEW_HANDLE = (15.0, -125.0)
SQUARE = [(0, 0), (20, 0), (20, 20), (0, 20)]
_QT_APP = None


def _scene_with_bezier(*, clear_history: bool = True) -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=50)
    result = scene.cmd.execute(
        CreateBezierObjectCommand(BEZIERS, object_id="CURVE"),
        scene,
    )
    assert result.status is CommandStatus.APPLIED
    if clear_history:
        scene.cmd.clear()
    return scene


def test_canonicalize_beziers_copies_numeric_points():
    source = [[[(0, 0), (0, -10), (10, -10), (10, 0)][index] for index in range(4)]]
    canonical = canonicalize_beziers(source)
    source[0][1] = (99, 99)
    assert canonical == [((0.0, 0.0), (0.0, -10.0), (10.0, -10.0), (10.0, 0.0))]


def test_canonicalize_beziers_rejects_invalid_segment_shape():
    with pytest.raises(ValueError, match="four control points"):
        canonicalize_beziers([((0, 0), (1, 1), (2, 2))])


def test_canonicalize_beziers_rejects_non_finite_coordinates():
    with pytest.raises(ValueError, match="finite"):
        canonicalize_beziers([((0, 0), (math.inf, 1), (2, 2), (3, 3))])


def test_bezier_sampling_is_deterministic_and_removes_join_duplicate():
    beziers = [
        ((0, 0), (0, -20), (20, -20), (20, 0)),
        ((20, 0), (20, 20), (40, 20), (40, 0)),
    ]
    assert len(sample_beziers(beziers, steps_per_segment=4)) == 9
    polygon = sample_beziers_to_polygon(beziers, steps_per_segment=4)
    assert polygon[0] == (0, 0)
    assert polygon[-1] == (40, 0)
    assert all(a != b for a, b in zip(polygon, polygon[1:]))


def test_create_bezier_object_stores_canonical_geometry_and_polygon():
    scene = Scene()
    scene.cmd = CommandManager()
    command = CreateBezierObjectCommand(BEZIERS, object_id="CURVE")
    result = scene.cmd.execute(command, scene)
    assert result.status is CommandStatus.APPLIED
    assert scene.objects["CURVE"].beziers == canonicalize_beziers(BEZIERS)
    assert scene.objects["CURVE"].polygon == sample_beziers_to_polygon(BEZIERS)
    assert scene.selected_id == "CURVE"


def test_create_bezier_object_undo_redo_preserves_identity_and_selection():
    scene = Scene()
    scene.add_object("OLD", SQUARE, select=True)
    scene.cmd = CommandManager()
    command = CreateBezierObjectCommand(BEZIERS, object_id="CURVE")
    assert scene.cmd.execute(command, scene).changed
    snapshot = copy.deepcopy(scene.objects["CURVE"].__dict__)
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "OLD"
    assert scene.cmd.redo(scene).changed
    assert scene.selected_id == "CURVE"
    assert scene.objects["CURVE"].__dict__ == snapshot


def test_create_bezier_object_rejects_invalid_geometry_without_history():
    scene = Scene()
    scene.cmd = CommandManager()
    result = scene.cmd.execute(CreateBezierObjectCommand([]), scene)
    assert result.status is CommandStatus.REJECTED
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


def test_create_bezier_object_rejects_missing_layer_and_id_conflict():
    scene = Scene()
    scene.add_object("CURVE", SQUARE)
    scene.cmd = CommandManager()
    missing_layer = scene.cmd.execute(
        CreateBezierObjectCommand(BEZIERS, layer_id="missing"), scene
    )
    conflict = scene.cmd.execute(
        CreateBezierObjectCommand(BEZIERS, object_id="CURVE"), scene
    )
    assert missing_layer.status is CommandStatus.REJECTED
    assert conflict.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 0


def test_create_bezier_object_undo_rejects_modified_object_or_relationship():
    scene = _scene_with_bezier(clear_history=False)
    scene.collision_shapes["CURVE"] = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    result = scene.cmd.undo(scene)
    assert result.status is CommandStatus.REJECTED
    assert "CURVE" in scene.objects


def test_handle_move_execute_updates_bezier_and_sampled_polygon():
    scene = _scene_with_bezier()
    old_polygon = copy.deepcopy(scene.objects["CURVE"].polygon)
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), NEW_HANDLE), scene
    )
    assert result.status is CommandStatus.APPLIED
    assert scene.objects["CURVE"].beziers[0][1] == NEW_HANDLE
    assert scene.objects["CURVE"].polygon != old_polygon


def test_handle_move_undo_redo_restores_exact_states():
    scene = _scene_with_bezier()
    old = copy.deepcopy(scene.objects["CURVE"].__dict__)
    assert scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), NEW_HANDLE), scene
    ).changed
    new = copy.deepcopy(scene.objects["CURVE"].__dict__)
    assert scene.cmd.undo(scene).changed
    assert scene.objects["CURVE"].__dict__ == old
    assert scene.cmd.redo(scene).changed
    assert scene.objects["CURVE"].__dict__ == new


def test_handle_move_noop_creates_no_history():
    scene = _scene_with_bezier()
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), (0, -100)), scene
    )
    assert result.status is CommandStatus.NO_CHANGE
    assert scene.cmd.undo_count == 0


def test_handle_move_rejects_missing_object():
    scene = Scene()
    scene.cmd = CommandManager()
    result = scene.cmd.execute(
        HandleMoveCommand("missing", 0, 1, (0, 0), (1, 1)), scene
    )
    assert result.status is CommandStatus.REJECTED


def test_handle_move_rejects_object_without_beziers():
    scene = Scene()
    scene.add_object("A", SQUARE)
    scene.cmd = CommandManager()
    result = scene.cmd.execute(HandleMoveCommand("A", 0, 1, (0, 0), (1, 1)), scene)
    assert result.status is CommandStatus.REJECTED


def test_handle_move_rejects_invalid_segment_index():
    scene = _scene_with_bezier()
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 4, 1, (0, -100), NEW_HANDLE), scene
    )
    assert result.status is CommandStatus.REJECTED


def test_handle_move_rejects_invalid_handle_index():
    scene = _scene_with_bezier()
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 0, (0, 0), NEW_HANDLE), scene
    )
    assert result.status is CommandStatus.REJECTED


def test_handle_move_rejects_non_finite_position():
    scene = _scene_with_bezier()
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), (math.nan, 1)), scene
    )
    assert result.status is CommandStatus.REJECTED


def test_handle_move_rejects_stale_handle_before_execute():
    scene = _scene_with_bezier()
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (1, -100), NEW_HANDLE), scene
    )
    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 0


def test_handle_move_rejects_stale_bezier_before_undo():
    scene = _scene_with_bezier()
    assert scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), NEW_HANDLE), scene
    ).changed
    scene.objects["CURVE"].beziers[0] = (
        scene.objects["CURVE"].beziers[0][0],
        (22.0, -140.0),
        scene.objects["CURVE"].beziers[0][2],
        scene.objects["CURVE"].beziers[0][3],
    )
    assert scene.cmd.undo(scene).status is CommandStatus.REJECTED


def test_handle_move_rejects_stale_collision_before_undo():
    scene = _scene_with_bezier()
    scene.collision_shapes["CURVE"] = [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0)]
    scene.cmd.clear()
    assert scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), NEW_HANDLE), scene
    ).changed
    scene.collision_shapes["CURVE"][0] = (99.0, 99.0)
    assert scene.cmd.undo(scene).status is CommandStatus.REJECTED


def test_handle_move_rejects_stale_state_before_redo():
    scene = _scene_with_bezier()
    assert scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), NEW_HANDLE), scene
    ).changed
    assert scene.cmd.undo(scene).changed
    scene.objects["CURVE"].polygon[0] = (99, 99)
    assert scene.cmd.redo(scene).status is CommandStatus.REJECTED


def _qt_tool_scene(monkeypatch, *, with_manager: bool = True):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from src.tools.pen_tool import PenTool

    global _QT_APP
    _QT_APP = QApplication.instance() or QApplication([])

    class Canvas:
        def __init__(self, model):
            self.model = model
            self.update_count = 0

        def update(self):
            self.update_count += 1

        def get_zoom(self):
            return 1.0

    class Event:
        def button(self):
            return Qt.MouseButton.LeftButton

    scene = Scene()
    scene.cmd = CommandManager() if with_manager else None
    canvas = Canvas(scene)
    tool = PenTool(canvas)
    tool._load_nodes_from_beziers(canonicalize_beziers(BEZIERS))
    monkeypatch.setattr("src.tools.pen_tool.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("src.tools.pen_tool.QMessageBox.warning", lambda *a, **k: None)
    return scene, tool, Event()


def test_pen_runtime_creates_bezier_object_in_one_history_entry(monkeypatch):
    scene, tool, _ = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    assert object_id in scene.objects
    assert scene.objects[object_id].beziers is not None
    assert scene.cmd.undo_count == 1


def test_pen_runtime_blocks_creation_without_manager(monkeypatch):
    scene, tool, _ = _qt_tool_scene(monkeypatch, with_manager=False)
    assert tool.commit_selection() is None
    assert scene.objects == {}


def test_pen_runtime_keeps_persistent_nodes_after_creation(monkeypatch):
    scene, tool, _ = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    assert tool._editing_object_id == object_id
    assert len(tool._nodes) == 2
    assert scene.selected_id == object_id


def test_pen_handle_drag_previews_without_history_and_commits_once(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old_polygon = copy.deepcopy(scene.objects[object_id].polygon)
    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    assert scene.objects[object_id].polygon != old_polygon
    assert scene.cmd.undo_count == 0
    tool.on_mouse_release(event, NEW_HANDLE)
    assert scene.cmd.undo_count == 1
    assert scene.objects[object_id].beziers[0][1] == NEW_HANDLE


def test_pen_handle_cancel_restores_preview_without_history(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old = copy.deepcopy(scene.objects[object_id].__dict__)
    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    tool.on_cancel()
    assert scene.objects[object_id].__dict__ == old
    assert scene.cmd.undo_count == 0


def test_pen_handle_without_manager_restores_preview(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    old = copy.deepcopy(scene.objects[object_id].__dict__)
    scene.cmd = None
    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    tool.on_mouse_release(event, NEW_HANDLE)
    assert scene.objects[object_id].__dict__ == old


def test_pen_handle_controlled_failure_restores_without_history(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    old = copy.deepcopy(scene.objects[object_id].__dict__)
    scene.cmd.clear()
    monkeypatch.setattr(
        scene.cmd,
        "execute",
        lambda command, model: CommandResult.failed(
            command,
            "execute",
            "ControlledFailure",
            "Controlled test failure.",
        ),
    )
    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    tool.on_mouse_release(event, NEW_HANDLE)
    assert scene.objects[object_id].__dict__ == old
    assert scene.cmd.undo_count == 0
