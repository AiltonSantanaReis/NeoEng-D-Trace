"""Stage 5 package 5A: exact creation commands and active creation paths."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.core.commands import (
    AddPolygonCommand,
    CommandManager,
    CommandStatus,
    CreateObjectCommand,
)
from src.models.scene import Scene

SQUARE = [(0, 0), (20, 0), (20, 20), (0, 20)]
LARGE_SQUARE = [(0, 0), (40, 0), (40, 40), (0, 40)]
ROOT = Path(__file__).resolve().parents[1]
ACTIVE_CREATION_TOOLS = (
    "src/tools/lasso_tool.py",
    "src/tools/polygonal_lasso.py",
    "src/tools/magnetic_lasso.py",
    "src/tools/pen_tool.py",
    "src/tools/rect_selection.py",
    "src/tools/ellipse_selection.py",
)


def _scene_with_selection() -> Scene:
    scene = Scene()
    scene.add_object("EXISTING", SQUARE, select=True)
    scene.cmd = CommandManager(max_history=50)
    return scene


def test_add_polygon_preserves_identity_and_previous_selection():
    scene = _scene_with_selection()
    command = AddPolygonCommand(LARGE_SQUARE)

    assert scene.cmd.execute(command, scene).status is CommandStatus.APPLIED
    object_id = command.object_id
    assert object_id is not None
    assert scene.selected_id == object_id

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.selected_id == "EXISTING"
    assert object_id not in scene.objects

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert command.object_id == object_id
    assert scene.selected_id == object_id
    assert object_id in scene.objects


def test_add_polygon_restores_none_selection():
    scene = Scene()
    scene.cmd = CommandManager()
    command = AddPolygonCommand(SQUARE)

    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id is None


def test_add_polygon_redo_rejects_id_conflict_without_overwrite():
    scene = _scene_with_selection()
    command = AddPolygonCommand(LARGE_SQUARE)
    assert scene.cmd.execute(command, scene).changed
    object_id = str(command.object_id)
    assert scene.cmd.undo(scene).changed

    scene.add_object(object_id, SQUARE, select=False)
    before = list(scene.objects[object_id].polygon)
    result = scene.cmd.redo(scene)

    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.redo_count == 1
    assert list(scene.objects[object_id].polygon) == before


def test_add_polygon_undo_rejects_modified_object():
    scene = _scene_with_selection()
    command = AddPolygonCommand(LARGE_SQUARE)
    assert scene.cmd.execute(command, scene).changed
    object_id = str(command.object_id)
    scene.objects[object_id].polygon = list(SQUARE)

    result = scene.cmd.undo(scene)

    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 1
    assert object_id in scene.objects


def test_add_polygon_undo_rejects_changed_selection():
    scene = _scene_with_selection()
    command = AddPolygonCommand(LARGE_SQUARE)
    assert scene.cmd.execute(command, scene).changed
    object_id = str(command.object_id)
    scene.select_object("EXISTING")

    result = scene.cmd.undo(scene)

    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 1
    assert object_id in scene.objects
    assert scene.selected_id == "EXISTING"


def test_add_polygon_undo_rejects_new_relationships():
    scene = _scene_with_selection()
    command = AddPolygonCommand(LARGE_SQUARE)
    assert scene.cmd.execute(command, scene).changed
    object_id = str(command.object_id)
    scene.collision_shapes[object_id] = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]

    result = scene.cmd.undo(scene)

    assert result.status is CommandStatus.REJECTED
    assert object_id in scene.objects
    assert object_id in scene.collision_shapes


def test_add_polygon_redo_rejects_changed_object_collection():
    scene = _scene_with_selection()
    command = AddPolygonCommand(LARGE_SQUARE)
    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    scene.add_object("DIRECT", SQUARE)

    result = scene.cmd.redo(scene)

    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.redo_count == 1
    assert command.object_id not in scene.objects


def test_create_object_with_explicit_id_is_stable():
    scene = _scene_with_selection()
    command = CreateObjectCommand(LARGE_SQUARE, object_id="CREATED")

    assert scene.cmd.execute(command, scene).changed
    assert scene.selected_id == "CREATED"
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "EXISTING"
    assert scene.cmd.redo(scene).changed
    assert command.object_id == "CREATED"
    assert scene.selected_id == "CREATED"


def test_create_object_initial_conflict_is_rejected_without_overwrite():
    scene = _scene_with_selection()
    before = list(scene.objects["EXISTING"].polygon)
    command = CreateObjectCommand(LARGE_SQUARE, object_id="EXISTING")

    result = scene.cmd.execute(command, scene)

    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 0
    assert list(scene.objects["EXISTING"].polygon) == before


def test_create_object_redo_conflict_is_rejected_without_overwrite():
    scene = _scene_with_selection()
    command = CreateObjectCommand(LARGE_SQUARE, object_id="CREATED")
    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    scene.add_object("CREATED", SQUARE)

    result = scene.cmd.redo(scene)

    assert result.status is CommandStatus.REJECTED
    assert list(scene.objects["CREATED"].polygon) == SQUARE
    assert scene.cmd.redo_count == 1


def test_create_object_undo_rejects_modified_state():
    scene = _scene_with_selection()
    command = CreateObjectCommand(LARGE_SQUARE, object_id="CREATED")
    assert scene.cmd.execute(command, scene).changed
    scene.objects["CREATED"].layer_id = "unexpected-layer"

    result = scene.cmd.undo(scene)

    assert result.status is CommandStatus.REJECTED
    assert "CREATED" in scene.objects


def test_invalid_creation_fails_without_history_or_partial_state():
    scene = _scene_with_selection()
    invalid = [(0, 0), (0, 0), (0, 0)]
    command = AddPolygonCommand(invalid)
    before_ids = tuple(scene.objects)

    result = scene.cmd.execute(command, scene)

    assert result.status is CommandStatus.FAILED
    assert result.error_type == "ValueError"
    assert tuple(scene.objects) == before_ids
    assert scene.selected_id == "EXISTING"
    assert command.object_id is None
    assert scene.cmd.undo_count == 0


def test_redo_rejects_missing_target_layer():
    scene = _scene_with_selection()
    invalid = AddPolygonCommand(LARGE_SQUARE, "missing-layer")
    initial_result = scene.cmd.execute(invalid, scene)
    assert initial_result.status is CommandStatus.REJECTED
    assert invalid.object_id is None
    assert scene.cmd.undo_count == 0

    layer = scene.create_layer("Temporary")
    scene.cmd.clear()
    command = AddPolygonCommand(LARGE_SQUARE, layer.id)
    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    scene.remove_layer(layer.id)

    result = scene.cmd.redo(scene)

    assert result.status is CommandStatus.REJECTED
    assert command.object_id not in scene.objects


def test_sequential_creations_restore_selection_in_stack_order():
    scene = _scene_with_selection()
    first = AddPolygonCommand(SQUARE)
    second = AddPolygonCommand(LARGE_SQUARE)

    assert scene.cmd.execute(first, scene).changed
    assert scene.cmd.execute(second, scene).changed
    assert scene.selected_id == second.object_id
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == first.object_id
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "EXISTING"
    assert scene.cmd.redo(scene).changed
    assert scene.selected_id == first.object_id
    assert scene.cmd.redo(scene).changed
    assert scene.selected_id == second.object_id


def test_creation_execute_undo_redo_notifies_once_per_operation():
    scene = _scene_with_selection()
    notifications = []
    scene.subscribe(lambda: notifications.append(scene.selected_id))
    command = AddPolygonCommand(LARGE_SQUARE)

    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.cmd.redo(scene).changed

    assert notifications == [command.object_id, "EXISTING", command.object_id]


@pytest.mark.parametrize("relative_path", ACTIVE_CREATION_TOOLS)
def test_active_creation_tools_have_no_direct_add_polygon(relative_path):
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "add_polygon":
            direct_calls.append(node.lineno)
    assert direct_calls == []


@pytest.mark.parametrize("relative_path", ACTIVE_CREATION_TOOLS)
def test_active_creation_tools_use_shared_command_helper(relative_path):
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    assert "commit_polygon_command(" in source


def test_canvas_has_no_native_direct_add_polygon_path():
    source = (ROOT / "src/ui/canvas_view.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    direct_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if ast.unparse(node.func) == "self.model.add_polygon":
            direct_calls.append(node.lineno)
    assert direct_calls == []
    assert "AddPolygonCommand" in source
    assert "_commit_native_polygon" in source


def test_base_tool_helper_requires_manager_and_handles_results():
    source = (ROOT / "src/tools/base_tool.py").read_text(encoding="utf-8")
    assert "manager is None" in source
    assert "CommandStatus.REJECTED" in source
    assert "CommandStatus.FAILED" in source
    assert "manager.execute(command, model)" in source
    assert ".add_polygon(" not in source
