import copy
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from src.core.commands import (
    AutoGenerateCollisionShapesCommand,
    Command,
    CommandManager,
    CommandResult,
    CommandStatus,
    CompositeCommand,
    CreateObjectCommand,
)
from src.models.scene import Scene
from src.tools import auto_detect

TRIANGLE_A = [(0, 0), (20, 0), (20, 20)]
TRIANGLE_B = [(40, 0), (60, 0), (60, 20)]


def make_scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("A", TRIANGLE_A)
    scene.add_object("B", TRIANGLE_B)
    return scene


def test_auto_collision_generation_round_trips_exact_state():
    scene = make_scene()
    old = {"legacy": [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0)]}
    scene.collision_shapes = copy.deepcopy(old)
    command = AutoGenerateCollisionShapesCommand()

    result = scene.cmd.execute(command, scene)

    assert result.status is CommandStatus.APPLIED
    assert scene.cmd.undo_count == 1
    assert command.generated_count == 2
    generated = copy.deepcopy(scene.collision_shapes)
    assert generated == {
        "A": [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)],
        "B": [(40.0, 0.0), (60.0, 0.0), (60.0, 20.0)],
    }
    assert scene.cmd.undo(scene).changed
    assert scene.collision_shapes == old
    assert scene.cmd.redo(scene).changed
    assert scene.collision_shapes == generated


def test_auto_collision_generation_is_noop_without_valid_polygons():
    scene = Scene()
    scene.cmd = CommandManager()
    result = scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    assert result.status is CommandStatus.NO_CHANGE
    assert scene.cmd.undo_count == 0
    assert scene.collision_shapes == {}


def test_auto_collision_generation_is_noop_when_shapes_already_match():
    scene = make_scene()
    scene.collision_shapes = {
        "A": [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)],
        "B": [(40.0, 0.0), (60.0, 0.0), (60.0, 20.0)],
    }
    result = scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    assert result.status is CommandStatus.NO_CHANGE
    assert scene.cmd.undo_count == 0


def test_auto_collision_generation_rejects_invalid_coordinate_atomically():
    scene = make_scene()
    scene.objects["B"].polygon = [(0, 0), (10, 0), (float("nan"), 10)]
    old = {"A": [(9.0, 9.0), (10.0, 9.0), (10.0, 10.0)]}
    scene.collision_shapes = copy.deepcopy(old)
    result = scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    assert result.status is CommandStatus.REJECTED
    assert scene.collision_shapes == old
    assert scene.cmd.undo_count == 0


def test_auto_collision_generation_rejects_stale_collision_before_undo():
    scene = make_scene()
    scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    scene.collision_shapes["A"] = [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0)]
    result = scene.cmd.undo(scene)
    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 1


def test_auto_collision_generation_rejects_geometry_change_before_undo():
    scene = make_scene()
    scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    scene.objects["A"].polygon = [(0, 0), (30, 0), (30, 30)]
    result = scene.cmd.undo(scene)
    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.undo_count == 1


def test_auto_collision_generation_rejects_geometry_change_before_redo():
    scene = make_scene()
    scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    assert scene.cmd.undo(scene).changed
    scene.objects["A"].polygon = [(0, 0), (30, 0), (30, 30)]
    result = scene.cmd.redo(scene)
    assert result.status is CommandStatus.REJECTED
    assert scene.cmd.redo_count == 1


def test_auto_collision_generation_restores_orphaned_old_shape_exactly():
    scene = make_scene()
    old = {"orphan": [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0)]}
    scene.collision_shapes = copy.deepcopy(old)
    scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    assert scene.cmd.undo(scene).changed
    assert scene.collision_shapes == old


def test_auto_collision_generation_notifies_once_per_applied_operation():
    scene = make_scene()
    notifications = []
    scene.subscribe(lambda: notifications.append(copy.deepcopy(scene.collision_shapes)))
    notifications.clear()
    scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    scene.cmd.undo(scene)
    scene.cmd.redo(scene)
    assert len(notifications) == 3


def test_composite_creation_is_one_history_entry_and_round_trips():
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("before", TRIANGLE_A, select=True)
    first = CreateObjectCommand(TRIANGLE_A)
    second = CreateObjectCommand(TRIANGLE_B)
    result = scene.cmd.execute(CompositeCommand([first, second]), scene)
    ids = [first.object_id, second.object_id]
    assert result.changed
    assert scene.cmd.undo_count == 1
    assert all(object_id in scene.objects for object_id in ids)
    assert scene.cmd.undo(scene).changed
    assert tuple(scene.objects) == ("before",)
    assert scene.selected_id == "before"
    assert scene.cmd.redo(scene).changed
    assert all(object_id in scene.objects for object_id in ids)
    assert second.object_id == ids[1]


def test_composite_creation_rolls_back_invalid_subcommand():
    scene = Scene()
    scene.cmd = CommandManager()
    first = CreateObjectCommand(TRIANGLE_A)
    invalid = CreateObjectCommand([(0, 0), (1, 1)])
    result = scene.cmd.execute(CompositeCommand([first, invalid]), scene)
    assert result.status is CommandStatus.FAILED
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


class _FailingCommand(Command):
    def execute(self, scene):
        scene.objects["partial"] = SimpleNamespace(id="partial", polygon=TRIANGLE_A)
        raise RuntimeError("controlled")

    def undo(self, scene):
        scene.objects.pop("partial", None)


def test_composite_creation_rolls_back_failed_subcommand():
    scene = Scene()
    scene.cmd = CommandManager()
    first = CreateObjectCommand(TRIANGLE_A)
    result = scene.cmd.execute(CompositeCommand([first, _FailingCommand()]), scene)
    assert result.status is CommandStatus.FAILED
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


def detect_result(polygons):
    return auto_detect.DetectResult(polygons)


def test_auto_detect_creates_one_atomic_history_entry():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = CommandManager()
    polygons = [{"polygon": TRIANGLE_A}, {"polygon": TRIANGLE_B}]
    with patch.object(
        auto_detect, "detect_polygons", return_value=detect_result(polygons)
    ):
        ids = auto_detect.detect_and_create_objects(scene)
    assert len(ids) == 2
    assert scene.cmd.undo_count == 1
    assert tuple(scene.objects) == tuple(ids)


def test_auto_detect_undo_redo_preserves_ids_and_selection():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = CommandManager()
    scene.add_object("before", TRIANGLE_A, select=True)
    polygons = [{"polygon": TRIANGLE_A}, {"polygon": TRIANGLE_B}]
    with patch.object(
        auto_detect, "detect_polygons", return_value=detect_result(polygons)
    ):
        ids = auto_detect.detect_and_create_objects(scene)
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "before"
    assert scene.cmd.redo(scene).changed
    assert ids == [object_id for object_id in scene.objects if object_id != "before"]


def test_auto_detect_blocks_without_command_manager():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    with patch.object(
        auto_detect,
        "detect_polygons",
        return_value=detect_result([{"polygon": TRIANGLE_A}]),
    ):
        with pytest.raises(RuntimeError, match="history is unavailable"):
            auto_detect.detect_and_create_objects(scene)
    assert scene.objects == {}


def test_auto_detect_invalid_polygon_rejects_entire_batch():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = CommandManager()
    polygons = [{"polygon": TRIANGLE_A}, {"polygon": [(0, 0), (1, 1)]}]
    with patch.object(
        auto_detect, "detect_polygons", return_value=detect_result(polygons)
    ):
        with pytest.raises(RuntimeError, match="rolled back"):
            auto_detect.detect_and_create_objects(scene)
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


def test_auto_detect_apply_false_does_not_require_history():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    polygons = [{"polygon": TRIANGLE_A}, {"polygon": TRIANGLE_B}]
    with patch.object(
        auto_detect, "detect_polygons", return_value=detect_result(polygons)
    ):
        assert auto_detect.detect_and_create_objects(scene, apply=False) == [
            "preview_0",
            "preview_1",
        ]
    assert scene.objects == {}


def test_auto_detect_empty_result_creates_no_history():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = CommandManager()
    with patch.object(auto_detect, "detect_polygons", return_value=detect_result([])):
        assert auto_detect.detect_and_create_objects(scene) == []
    assert scene.cmd.undo_count == 0


def test_auto_detect_preserves_per_polygon_layer_ids():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = CommandManager()
    layer = scene.create_layer("Detected")
    polygons = [{"polygon": TRIANGLE_A, "layer_id": layer.id}]
    with patch.object(
        auto_detect, "detect_polygons", return_value=detect_result(polygons)
    ):
        ids = auto_detect.detect_and_create_objects(scene)
    assert scene.objects[ids[0]].layer_id == layer.id


def test_auto_detect_propagates_failed_manager_result_without_ids():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = SimpleNamespace(
        execute=lambda *_args: CommandResult.failed(
            CompositeCommand([]), "execute", "ControlledError", "controlled failure"
        )
    )
    with patch.object(
        auto_detect,
        "detect_polygons",
        return_value=detect_result([{"polygon": TRIANGLE_A}]),
    ):
        with pytest.raises(RuntimeError, match="controlled failure"):
            auto_detect.detect_and_create_objects(scene)
    assert scene.objects == {}


def test_auto_detect_rejects_non_mapping_detection_item():
    scene = Scene()
    scene.image = np.zeros((16, 16), dtype=np.uint8)
    scene.cmd = CommandManager()
    with patch.object(
        auto_detect, "detect_polygons", return_value=detect_result([TRIANGLE_A])
    ):
        with pytest.raises(ValueError, match="must be a mapping"):
            auto_detect.detect_and_create_objects(scene)
    assert scene.cmd.undo_count == 0
