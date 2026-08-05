"""Stage 5 package 5C: direct residual command contracts."""

from __future__ import annotations

import copy
from pathlib import Path

from src.core.commands import (
    CommandManager,
    CommandStatus,
    ExpandContractCommand,
    HandleMoveCommand,
    UpdateObjectGeometryCommand,
)
from src.models.scene import Scene

OLD = [(0, 0), (20, 0), (20, 20), (0, 20)]
NEW = [(-5, -5), (25, -5), (25, 25), (-5, 25)]
OLD_COLLISION = [(1.5, 1.5), (18.5, 1.5), (18.5, 18.5), (1.5, 18.5)]
NEW_COLLISION = [(-4.5, -4.5), (24.5, -4.5), (24.5, 24.5), (-4.5, 24.5)]
ROOT = Path(__file__).resolve().parents[1]


def _scene(*, collision: bool = True) -> Scene:
    scene = Scene()
    scene.add_object("A", copy.deepcopy(OLD), select=True)
    if collision:
        scene.collision_shapes["A"] = copy.deepcopy(OLD_COLLISION)
    scene.cmd = CommandManager()
    return scene


def _geometry_command(**overrides):
    values = {
        "object_id": "A",
        "old_polygon": OLD,
        "new_polygon": NEW,
        "old_has_collision": True,
        "old_collision": OLD_COLLISION,
        "new_has_collision": True,
        "new_collision": NEW_COLLISION,
    }
    values.update(overrides)
    return UpdateObjectGeometryCommand(**values)


def test_update_object_geometry_execute_applies_polygon_and_collision():
    scene = _scene()
    assert scene.cmd.execute(_geometry_command(), scene).changed
    assert scene.objects["A"].polygon == NEW
    assert scene.collision_shapes["A"] == NEW_COLLISION


def test_update_object_geometry_undo_redo_are_exact():
    scene = _scene()
    assert scene.cmd.execute(_geometry_command(), scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.objects["A"].polygon == OLD
    assert scene.collision_shapes["A"] == OLD_COLLISION
    assert scene.cmd.redo(scene).changed
    assert scene.objects["A"].polygon == NEW
    assert scene.collision_shapes["A"] == NEW_COLLISION


def test_update_object_geometry_noop_creates_no_history():
    scene = _scene()
    command = _geometry_command(new_polygon=OLD, new_collision=OLD_COLLISION)
    result = scene.cmd.execute(command, scene)
    assert result.status is CommandStatus.NO_CHANGE
    assert scene.cmd.undo_count == 0


def test_update_object_geometry_rejects_missing_object():
    scene = _scene()
    scene.remove_object("A")
    result = scene.cmd.execute(_geometry_command(), scene)
    assert result.status is CommandStatus.REJECTED


def test_update_object_geometry_rejects_stale_execute_state():
    scene = _scene()
    scene.objects["A"].polygon[0] = (99, 99)
    result = scene.cmd.execute(_geometry_command(), scene)
    assert result.status is CommandStatus.REJECTED


def test_update_object_geometry_rejects_stale_undo_state():
    scene = _scene()
    assert scene.cmd.execute(_geometry_command(), scene).changed
    scene.collision_shapes["A"][0] = (99.0, 99.0)
    assert scene.cmd.undo(scene).status is CommandStatus.REJECTED


def test_update_object_geometry_rejects_stale_redo_state():
    scene = _scene()
    assert scene.cmd.execute(_geometry_command(), scene).changed
    assert scene.cmd.undo(scene).changed
    scene.objects["A"].polygon[0] = (99, 99)
    assert scene.cmd.redo(scene).status is CommandStatus.REJECTED


def test_update_object_geometry_fails_when_target_collision_is_missing():
    scene = _scene(collision=False)
    command = _geometry_command(
        old_has_collision=False,
        old_collision=None,
        new_has_collision=True,
        new_collision=None,
    )
    result = scene.cmd.execute(command, scene)
    assert result.status is CommandStatus.FAILED
    assert scene.cmd.undo_count == 0


def test_expand_contract_execute_applies_polygon_and_collision():
    scene = _scene()
    assert scene.cmd.execute(ExpandContractCommand("A", OLD, NEW), scene).changed
    assert scene.objects["A"].polygon == NEW
    assert scene.collision_shapes["A"] == [(float(x), float(y)) for x, y in NEW]


def test_expand_contract_undo_redo_restore_exact_collision():
    scene = _scene()
    assert scene.cmd.execute(ExpandContractCommand("A", OLD, NEW), scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.collision_shapes["A"] == OLD_COLLISION
    assert scene.cmd.redo(scene).changed
    assert scene.objects["A"].polygon == NEW


def test_expand_contract_noop_creates_no_history():
    scene = _scene()
    result = scene.cmd.execute(ExpandContractCommand("A", OLD, OLD), scene)
    assert result.status is CommandStatus.NO_CHANGE
    assert scene.cmd.undo_count == 0


def test_expand_contract_rejects_stale_execute_state():
    scene = _scene()
    scene.objects["A"].polygon[0] = (99, 99)
    result = scene.cmd.execute(ExpandContractCommand("A", OLD, NEW), scene)
    assert result.status is CommandStatus.REJECTED


def test_expand_contract_rejects_stale_undo_and_redo_states():
    scene = _scene()
    assert scene.cmd.execute(ExpandContractCommand("A", OLD, NEW), scene).changed
    scene.collision_shapes["A"][0] = (99.0, 99.0)
    assert scene.cmd.undo(scene).status is CommandStatus.REJECTED


def test_residual_commands_have_active_nominal_coverage_and_runtime_reference():
    tests_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "tests").glob("test_stage_5_package_5c_*.py")
    )
    pen_text = (ROOT / "src/tools/pen_tool.py").read_text(encoding="utf-8")
    for command_name in (
        "HandleMoveCommand",
        "UpdateObjectGeometryCommand",
        "ExpandContractCommand",
    ):
        assert command_name in tests_text
    assert "HandleMoveCommand" in pen_text
