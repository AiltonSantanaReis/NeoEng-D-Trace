"""Stage 5 package 5C: Bézier creation and handle history contracts."""

from __future__ import annotations

import copy
import math
import os

import pytest
from PIL import Image

import src.models.scene as scene_module
from src.core.bezier_geometry import (
    canonicalize_beziers,
    cubic_bezier_point,
    replace_handle,
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
from src.exporters.sprite_exporter import export_sprite
from src.models.scene import Scene, SceneObject

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


def test_canonicalize_beziers_translates_unrepresentable_integer_to_value_error():
    with pytest.raises(ValueError, match="finite and representable"):
        canonicalize_beziers([((0, 0), (10**400, 1), (2, 2), (3, 3))])


@pytest.mark.parametrize(
    "invalid_handle_index",
    [
        pytest.param(True, id="bool"),
        pytest.param(1.0, id="float"),
        pytest.param([], id="unhashable"),
    ],
)
def test_replace_handle_rejects_non_integer_handle_index(invalid_handle_index):
    with pytest.raises(ValueError, match="handle_index must be an integer"):
        replace_handle(BEZIERS, 0, invalid_handle_index, NEW_HANDLE)


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


def test_create_bezier_object_notifies_only_complete_final_state():
    scene = Scene()
    scene.cmd = CommandManager()
    observed = []

    def capture():
        obj = scene.objects.get("CURVE")
        observed.append(
            (
                scene.selected_id,
                copy.deepcopy(obj.__dict__) if obj is not None else None,
            )
        )

    scene.subscribe(capture)
    result = scene.cmd.execute(
        CreateBezierObjectCommand(BEZIERS, object_id="CURVE"),
        scene,
    )

    assert result.status is CommandStatus.APPLIED
    assert len(observed) == 1
    selected_id, snapshot = observed[0]
    assert selected_id == "CURVE"
    assert snapshot is not None
    assert snapshot["beziers"] == canonicalize_beziers(BEZIERS)
    assert snapshot["polygon"] == sample_beziers_to_polygon(BEZIERS)


def test_create_bezier_object_round_trip_preserves_control_points(tmp_path):
    scene = _scene_with_bezier()
    project = tmp_path / "bezier.ndtproj"

    scene.save_project(str(project))
    loaded = Scene()
    warnings = loaded.load_project(str(project))

    assert warnings == ()
    assert loaded.objects["CURVE"].beziers == canonicalize_beziers(BEZIERS)
    assert loaded.objects["CURVE"].polygon == sample_beziers_to_polygon(BEZIERS)


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


@pytest.mark.parametrize(
    "invalid_handle_index",
    [
        pytest.param(True, id="bool"),
        pytest.param(1.0, id="float"),
        pytest.param([], id="unhashable"),
    ],
)
def test_handle_move_rejects_non_integer_handle_index_without_history(
    invalid_handle_index,
):
    scene = _scene_with_bezier()
    before = copy.deepcopy(scene.objects["CURVE"].__dict__)
    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, invalid_handle_index, (0, -100), NEW_HANDLE),
        scene,
    )
    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 0
    assert scene.objects["CURVE"].__dict__ == before


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


def test_pen_selection_sync_clears_stale_non_bezier_target(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    curve_id = tool.commit_selection()
    scene.cmd.clear()
    scene.add_object("PLAIN", SQUARE, select=True)

    tool.on_mouse_press(event, (0.0, -100.0))

    assert tool._editing_object_id is None
    assert tool._nodes == []
    assert tool._active_handle_edit is None
    assert scene.selected_id == "PLAIN"
    assert scene.cmd.undo_count == 0
    assert scene.objects[curve_id].beziers == canonicalize_beziers(BEZIERS)


def test_pen_selection_sync_loads_new_selected_bezier(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    first_id = tool.commit_selection()
    second_beziers = [((200, 0), (200, -80), (280, -80), (280, 0))]
    result = scene.cmd.execute(
        CreateBezierObjectCommand(second_beziers, object_id="SECOND"),
        scene,
    )
    assert result.changed
    scene.cmd.clear()

    tool.on_mouse_press(event, (200.0, -80.0))

    assert first_id != "SECOND"
    assert tool._editing_object_id == "SECOND"
    assert tool._active_handle_edit is not None
    assert tool._active_handle_edit.object_id == "SECOND"
    assert scene.cmd.undo_count == 0


def test_pen_selection_sync_reloads_same_object_after_global_undo(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    tool.on_mouse_release(event, NEW_HANDLE)
    assert tool._nodes[0].handle_out == NEW_HANDLE

    assert scene.cmd.undo(scene).changed
    assert scene.objects[object_id].beziers[0][1] == (0.0, -100.0)
    assert tool._nodes[0].handle_out == NEW_HANDLE

    assert tool._synchronize_selected_bezier_object()
    assert tool._nodes[0].handle_out == (0.0, -100.0)


def test_pen_selection_sync_reloads_same_object_after_global_redo(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    tool.on_mouse_release(event, NEW_HANDLE)
    assert scene.cmd.undo(scene).changed
    assert tool._synchronize_selected_bezier_object()
    assert tool._nodes[0].handle_out == (0.0, -100.0)

    assert scene.cmd.redo(scene).changed
    assert scene.objects[object_id].beziers[0][1] == NEW_HANDLE
    assert tool._nodes[0].handle_out == (0.0, -100.0)

    assert tool._synchronize_selected_bezier_object()
    assert tool._nodes[0].handle_out == NEW_HANDLE


def test_pen_undo_hook_cancels_active_handle_preview_without_history(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old = copy.deepcopy(scene.objects[object_id].__dict__)

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)

    assert tool.on_undo()
    assert scene.objects[object_id].__dict__ == old
    assert tool._active_handle_edit is None
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_pen_redo_hook_cancels_active_handle_preview_without_history(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old = copy.deepcopy(scene.objects[object_id].__dict__)

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)

    assert tool.on_redo()
    assert scene.objects[object_id].__dict__ == old
    assert tool._active_handle_edit is None
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_pen_escape_cancels_active_handle_preview(monkeypatch):
    from PySide6.QtCore import Qt

    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old = copy.deepcopy(scene.objects[object_id].__dict__)

    class KeyEvent:
        def key(self):
            return Qt.Key.Key_Escape

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)

    assert tool.on_key_press(KeyEvent())
    assert scene.objects[object_id].__dict__ == old
    assert tool._active_handle_edit is None
    assert scene.cmd.undo_count == 0


@pytest.mark.parametrize("method_name", ["undo_last_action", "redo_last_action"])
def test_pen_context_history_cancels_active_preview_first(monkeypatch, method_name):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old = copy.deepcopy(scene.objects[object_id].__dict__)

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    getattr(tool, method_name)()

    assert scene.objects[object_id].__dict__ == old
    assert tool._active_handle_edit is None
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_pen_release_preserves_external_model_change(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, NEW_HANDLE)
    external_handle = (120.0, -90.0)
    result = scene.cmd.execute(
        HandleMoveCommand(
            object_id,
            0,
            2,
            (100.0, -100.0),
            external_handle,
        ),
        scene,
    )
    assert result.changed
    external_state = copy.deepcopy(scene.objects[object_id].__dict__)

    tool.on_mouse_release(event, NEW_HANDLE)

    assert scene.objects[object_id].__dict__ == external_state
    assert scene.objects[object_id].beziers[0][2] == external_handle
    assert tool._active_handle_edit is None
    assert scene.cmd.undo_count == 1


def test_pen_handle_edit_accepts_different_persisted_sampling_density(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    custom_polygon = sample_beziers_to_polygon(BEZIERS, steps_per_segment=5)
    scene.objects[object_id].polygon = copy.deepcopy(custom_polygon)
    tool._load_selected_bezier_object()

    tool.on_mouse_press(event, (0.0, -100.0))
    assert tool._active_handle_edit is not None
    tool.on_mouse_move(event, NEW_HANDLE)
    assert tool._active_handle_edit is not None

    assert tool.on_undo()
    assert scene.objects[object_id].beziers == canonicalize_beziers(BEZIERS)
    assert scene.objects[object_id].polygon == custom_polygon
    assert scene.cmd.undo_count == 0


@pytest.mark.parametrize("direction", ["undo", "redo"])
def test_pen_history_hook_cancels_preview_before_next_global_operation(
    monkeypatch, direction
):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    committed = (10.0, -110.0)

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, committed)
    tool.on_mouse_release(event, committed)
    assert scene.cmd.undo_count == 1

    if direction == "redo":
        assert scene.cmd.undo(scene).changed
        assert tool._synchronize_selected_bezier_object()
        start = (0.0, -100.0)
        expected_after_history = committed
    else:
        start = committed
        expected_after_history = (0.0, -100.0)

    undo_before = scene.cmd.undo_count
    redo_before = scene.cmd.redo_count
    tool.on_mouse_press(event, start)
    tool.on_mouse_move(event, NEW_HANDLE)

    hook = tool.on_undo if direction == "undo" else tool.on_redo
    operation = scene.cmd.undo if direction == "undo" else scene.cmd.redo
    assert hook()
    assert scene.cmd.undo_count == undo_before
    assert scene.cmd.redo_count == redo_before
    assert not hook()
    assert operation(scene).changed
    assert scene.objects[object_id].beziers[0][1] == expected_after_history


def _signed_area2(points):
    return sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


def test_create_bezier_object_normalizes_opposite_winding():
    opposite = [((0, 0), (0, 100), (100, 100), (100, 0))]
    raw_polygon = sample_beziers_to_polygon(opposite)
    assert _signed_area2(raw_polygon) < 0

    scene = Scene()
    scene.cmd = CommandManager()
    result = scene.cmd.execute(
        CreateBezierObjectCommand(opposite, object_id="CLOCKWISE"), scene
    )

    assert result.status is CommandStatus.APPLIED
    assert scene.objects["CLOCKWISE"].beziers == canonicalize_beziers(opposite)
    assert scene.objects["CLOCKWISE"].polygon == list(reversed(raw_polygon))
    assert _signed_area2(scene.objects["CLOCKWISE"].polygon) > 0


def test_create_bezier_object_rejects_self_intersecting_sample_without_history():
    self_intersecting = [((0, 0), (-300, 300), (100, -100), (100, 0))]
    scene = Scene()
    scene.cmd = CommandManager()

    result = scene.cmd.execute(
        CreateBezierObjectCommand(self_intersecting, object_id="INVALID"), scene
    )

    assert result.status is CommandStatus.REJECTED
    assert result.message == "Invalid sampled Bézier polygon"
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


def test_handle_move_normalizes_valid_opposite_winding():
    scene = _scene_with_bezier()
    requested = (200.0, 100.0)
    raw_polygon = sample_beziers_to_polygon(
        [((0, 0), requested, (100, -100), (100, 0))]
    )
    assert _signed_area2(raw_polygon) < 0

    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), requested), scene
    )

    assert result.status is CommandStatus.APPLIED
    assert scene.objects["CURVE"].polygon == list(reversed(raw_polygon))
    assert _signed_area2(scene.objects["CURVE"].polygon) > 0
    assert scene.cmd.undo_count == 1


@pytest.mark.parametrize("invalid_handle", [(0.0, 100.0), (-300.0, 300.0)])
def test_handle_move_rejects_invalid_sample_without_history(invalid_handle):
    scene = _scene_with_bezier()
    old = copy.deepcopy(scene.objects["CURVE"].__dict__)

    result = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), invalid_handle), scene
    )

    assert result.status is CommandStatus.REJECTED
    assert result.message == "Invalid sampled Bézier polygon"
    assert scene.objects["CURVE"].__dict__ == old
    assert scene.cmd.undo_count == 0


def test_set_object_beziers_normalizes_and_rejects_invalid_without_mutation():
    scene = _scene_with_bezier()
    opposite = [((0, 0), (0, 100), (100, 100), (100, 0))]
    scene.set_object_beziers("CURVE", opposite)
    assert _signed_area2(scene.objects["CURVE"].polygon) > 0
    accepted = copy.deepcopy(scene.objects["CURVE"].__dict__)

    with pytest.raises(ValueError, match="Invalid sampled Bézier polygon"):
        scene.set_object_beziers(
            "CURVE", [((0, 0), (-300, 300), (100, -100), (100, 0))]
        )
    assert scene.objects["CURVE"].__dict__ == accepted


def test_pen_invalid_handle_preview_is_visual_only_and_release_rejects(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    old = copy.deepcopy(scene.objects[object_id].__dict__)
    invalid_handle = (0.0, 100.0)

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, invalid_handle)

    assert scene.objects[object_id].__dict__ == old
    assert tool._nodes[0].handle_out == invalid_handle
    assert tool._active_handle_edit is not None
    assert tool._last_error == "Invalid sampled Bézier polygon"

    tool.on_mouse_release(event, invalid_handle)

    assert scene.objects[object_id].__dict__ == old
    assert scene.cmd.undo_count == 0
    assert tool._active_handle_edit is None
    assert tool._last_command_result.status is CommandStatus.REJECTED


def test_pen_valid_opposite_winding_preview_and_commit_are_normalized(monkeypatch):
    scene, tool, event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    scene.cmd.clear()
    requested = (200.0, 100.0)

    tool.on_mouse_press(event, (0.0, -100.0))
    tool.on_mouse_move(event, requested)

    assert _signed_area2(scene.objects[object_id].polygon) > 0
    assert scene.cmd.undo_count == 0

    tool.on_mouse_release(event, requested)

    assert scene.cmd.undo_count == 1
    assert scene.objects[object_id].beziers[0][1] == requested
    assert _signed_area2(scene.objects[object_id].polygon) > 0


def test_fallback_validator_rejects_missed_bezier_self_intersection(monkeypatch):
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    missed_by_v35 = [
        ((0, 0), (0, 50), (150, -150), (-50, -150)),
        ((-50, -150), (-200, -200), (-200, 150), (50, 100)),
    ]

    with pytest.raises(ValueError, match="Invalid sampled Bézier polygon"):
        Scene.prepare_bezier_geometry(missed_by_v35)


def test_fallback_validator_rejects_non_adjacent_collinear_touch(monkeypatch):
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    polygon = [(0, 0), (6, 0), (6, 6), (3, 0), (0, 6)]
    polygon = scene_module._normalize_polygon_winding(polygon)

    assert not scene_module._validate_polygon(polygon)


def test_deterministic_validator_rejects_invalid_numeric_atoms(monkeypatch):
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    invalid_polygons = (
        [(0, 0), (10, 0), (10, math.inf)],
        [(0, 0), (10, 0), (True, 10)],
        [(0, 0), (10, 0), (10**10000, 10)],
    )

    for polygon in invalid_polygons:
        assert not scene_module._validate_polygon(polygon)


def test_closed_bezier_loop_removes_duplicate_terminal_vertex(monkeypatch):
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    closed_loop = [((0, 0), (-50, -100), (-150, 100), (0, 0))]

    canonical, polygon = Scene.prepare_bezier_geometry(closed_loop)

    assert canonical == canonicalize_beziers(closed_loop)
    assert len(polygon) >= 3
    assert polygon[0] != polygon[-1]
    assert _signed_area2(polygon) > 0
    assert scene_module._validate_polygon(polygon)


def test_prepare_bezier_geometry_rejects_unrepresentable_control_point():
    huge = 10**400
    invalid = [((0, 0), (huge, 0), (100, -100), (100, 0))]

    with pytest.raises(ValueError, match="finite and representable"):
        Scene.prepare_bezier_geometry(invalid)


def test_create_bezier_rejects_unrepresentable_control_point_without_history():
    scene = Scene()
    scene.cmd = CommandManager()
    huge = 10**400
    command = CreateBezierObjectCommand(
        [((0, 0), (huge, 0), (100, -100), (100, 0))],
        object_id="TOO_LARGE",
    )

    result = scene.cmd.execute(command, scene)

    assert result.status is CommandStatus.REJECTED
    assert "representable" in result.message
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


def test_handle_move_rejects_unrepresentable_position_without_history():
    scene = _scene_with_bezier()
    old_state = copy.deepcopy(scene.objects["CURVE"].__dict__)
    command = HandleMoveCommand(
        "CURVE",
        0,
        1,
        BEZIERS[0][1],
        (10**400, -125),
    )

    result = scene.cmd.execute(command, scene)

    assert result.status is CommandStatus.REJECTED
    assert "representable" in result.message
    assert scene.objects["CURVE"].__dict__ == old_state
    assert scene.cmd.undo_count == 0


def test_pen_selection_sync_clears_unrepresentable_loaded_bezier(monkeypatch):
    scene, tool, _event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    assert object_id is not None
    scene.objects[object_id].beziers = [((0, 0), (10**400, 0), (100, -100), (100, 0))]

    assert not tool._synchronize_selected_bezier_object()
    assert tool._editing_object_id is None
    assert tool._nodes == []


def test_deterministic_validator_rejects_nonfinite_area_arithmetic(monkeypatch):
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    polygon = [(0.0, 0.0), (1e308, 0.0), (0.0, 1e308)]
    polygon = scene_module._normalize_polygon_winding(polygon)

    assert not scene_module._validate_polygon(polygon)


def test_deterministic_validator_does_not_consult_optional_shapely(monkeypatch):
    monkeypatch.setattr(scene_module, "HAS_SHAPELY", True)

    def unexpected_polygon_call(*_args, **_kwargs):
        raise AssertionError("Optional Shapely must not decide polygon validity.")

    monkeypatch.setattr(scene_module, "Polygon", unexpected_polygon_call, raising=False)
    polygon = scene_module._normalize_polygon_winding(SQUARE)

    assert scene_module._validate_polygon(polygon)


def test_scene_sampling_does_not_expose_overflow_for_unrepresentable_control():
    scene = Scene()
    invalid = [((0, 0), (10**400, 0), (100, -100), (100, 0))]

    with pytest.raises(ValueError, match="finite and representable"):
        scene.sample_beziers_to_polygon(invalid)


def test_sprite_export_does_not_expose_overflow_for_loaded_bezier():
    scene = Scene()
    scene.image = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
    obj = SceneObject("LOADED", [(0, 0), (8, 0), (0, 8)], "layer_default")
    obj.beziers = [((0, 0), (10**400, 0), (8, -8), (8, 0))]
    scene.objects[obj.id] = obj

    with pytest.raises(ValueError, match="finite and representable"):
        export_sprite(obj.id, scene, "")


def test_cubic_evaluator_keeps_extreme_equal_controls_finite():
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    point = (maximum, maximum)

    sampled = sample_beziers([(point, point, point, point)])

    assert sampled
    assert all(value == point for value in sampled)
    assert all(math.isfinite(x) and math.isfinite(y) for x, y in sampled)


def test_cubic_evaluator_preserves_historical_finite_rounding():
    controls = (
        (12335, 91416),
        (46535, 59711),
        (-55002, 86952),
        (3057, 95679),
    )
    parameter = 0.3
    u = 1.0 - parameter
    historical = (
        u**3 * controls[0][0]
        + 3.0 * u * u * parameter * controls[1][0]
        + 3.0 * u * parameter * parameter * controls[2][0]
        + parameter**3 * controls[3][0],
        u**3 * controls[0][1]
        + 3.0 * u * u * parameter * controls[1][1]
        + 3.0 * u * parameter * parameter * controls[2][1]
        + parameter**3 * controls[3][1],
    )

    evaluated = cubic_bezier_point(parameter, *controls)

    assert evaluated == historical
    assert tuple(round(value) for value in evaluated) == (14440, 76705)


def test_cubic_evaluator_keeps_opposite_extremes_finite():
    maximum = float.fromhex("0x1.fffffffffffffp+1023")

    point = cubic_bezier_point(
        0.5,
        (maximum, maximum),
        (-maximum, maximum),
        (-maximum, -maximum),
        (maximum, -maximum),
    )

    assert math.isfinite(point[0])
    assert math.isfinite(point[1])


def test_cubic_evaluator_rejects_invalid_parameters_without_raw_arithmetic():
    controls = ((0, 0), (0, -10), (10, -10), (10, 0))

    for parameter in (True, "0.5", math.nan, math.inf, -0.01, 1.01):
        with pytest.raises(ValueError, match="Bézier parameter"):
            cubic_bezier_point(parameter, *controls)


def test_scene_sampling_rejects_extreme_finite_geometry_without_raw_overflow():
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    extreme = [
        (
            (maximum, 0.0),
            (maximum, maximum),
            (-maximum, maximum),
            (-maximum, 0.0),
        )
    ]

    with pytest.raises(ValueError):
        Scene().sample_beziers_to_polygon(extreme)


def test_sprite_export_rejects_extreme_finite_loaded_bezier_without_raw_overflow():
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    scene = Scene()
    scene.image = Image.new("RGBA", (16, 16), (255, 255, 255, 255))
    obj = SceneObject("EXTREME", [(0, 0), (8, 0), (0, 8)], "layer_default")
    obj.beziers = [
        (
            (maximum, 0.0),
            (maximum, maximum),
            (-maximum, maximum),
            (-maximum, 0.0),
        )
    ]
    scene.objects[obj.id] = obj

    with pytest.raises(ValueError):
        export_sprite(obj.id, scene, "")


def test_pen_selection_sync_clears_extreme_finite_loaded_bezier(monkeypatch):
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    scene, tool, _event = _qt_tool_scene(monkeypatch)
    object_id = tool.commit_selection()
    assert object_id is not None
    scene.objects[object_id].beziers = [
        (
            (maximum, 0.0),
            (maximum, maximum),
            (-maximum, maximum),
            (-maximum, 0.0),
        )
    ]

    assert not tool._synchronize_selected_bezier_object()
    assert tool._editing_object_id is None
    assert tool._nodes == []


def test_add_object_invalid_unrepresentable_polygon_skips_repair_when_disabled():
    scene = Scene()
    invalid = [(0, 0), (10, 0), (10**400, 10)]

    with pytest.raises(ValueError, match="Invalid polygon"):
        scene.add_object("INVALID", invalid)

    assert scene.objects == {}


def test_add_object_invalid_unrepresentable_polygon_repair_is_controlled():
    scene = Scene()
    scene.set_auto_repair(True)
    invalid = [(0, 0), (10, 0), (10**400, 10)]

    with pytest.raises(ValueError, match="Invalid polygon"):
        scene.add_object("INVALID", invalid)

    assert scene.objects == {}
