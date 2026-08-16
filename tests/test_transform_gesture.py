"""Real geometry, collision and history contracts for TransformGestureTransaction."""

from __future__ import annotations

import pytest

from src.core.commands import CommandManager, CommandStatus
from src.core.transform_gesture import TransformGestureTransaction
from src.models.scene import Scene


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object("box", [(10, 20), (30, 20), (30, 40), (10, 40)])
    scene.collision_shapes["box"] = [(12.0, 22.0), (28.0, 22.0), (20.0, 37.0)]
    scene.collision_parts["box"] = [
        [(12.0, 22.0), (20.0, 22.0), (20.0, 30.0)],
        [(20.0, 30.0), (28.0, 22.0), (28.0, 37.0)],
    ]
    return scene


def test_translation_preserves_compound_collision_relationships_and_history():
    scene = _scene()
    before_polygon = list(scene.objects["box"].polygon)
    before_parts = [list(part) for part in scene.collision_parts["box"]]
    gesture = TransformGestureTransaction(scene, ["box"])

    gesture.preview_transform(translation=(5.0, -3.0))
    assert scene.objects["box"].polygon[0] == (15.0, 17.0)
    assert scene.collision_parts["box"][0][0] == (17.0, 19.0)

    result = gesture.commit(scene.cmd)
    assert result.status is CommandStatus.APPLIED
    assert scene.cmd.undo_count == 1
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["box"].polygon == before_polygon
    assert scene.collision_parts["box"] == before_parts
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene.objects["box"].position == (25.0, 27.0, 0.0)


def test_rotation_and_non_uniform_scale_keep_pivot_fixed():
    scene = _scene()
    gesture = TransformGestureTransaction(scene, ["box"])

    gesture.preview_transform(rotation_degrees=90.0, scale=(2.0, 0.5))

    assert scene.objects["box"].position == (20.0, 30.0, 0.0)
    assert scene.objects["box"].rotation == (0.0, 0.0, 90.0)
    assert scene.objects["box"].scale == (2.0, 0.5, 1.0)
    assert scene.objects["box"].polygon[0] == (25.0, 10.0)


def test_multiple_objects_transform_around_shared_selection_anchor():
    scene = _scene()
    scene.add_object("second", [(50, 20), (70, 20), (70, 40), (50, 40)])
    gesture = TransformGestureTransaction(scene, ["box", "second"])

    gesture.preview_transform(
        scale=(2.0, 2.0),
        anchor_override=(35.0, 30.0),
    )

    assert scene.objects["box"].position == (5.0, 30.0, 0.0)
    assert scene.objects["second"].position == (85.0, 30.0, 0.0)

def test_escape_cancel_restores_exact_state_without_history():
    scene = _scene()
    original = scene.objects["box"].polygon[:]
    original_collision = scene.collision_shapes["box"][:]
    original_parts = [list(part) for part in scene.collision_parts["box"]]
    gesture = TransformGestureTransaction(scene, ["box"])
    gesture.preview_transform(translation=(12.0, 8.0), rotation_degrees=15.0)

    assert gesture.cancel() is True
    assert scene.objects["box"].polygon == original
    assert scene.collision_shapes["box"] == original_collision
    assert scene.collision_parts["box"] == original_parts
    assert scene.cmd.undo_count == 0


def test_missing_history_rolls_back_transform():
    scene = _scene()
    original = scene.objects["box"].polygon[:]
    gesture = TransformGestureTransaction(scene, ["box"])
    gesture.preview_transform(translation=(1.0, 2.0))

    result = gesture.commit(None)

    assert result.status is CommandStatus.FAILED
    assert scene.objects["box"].polygon == original


def test_external_mutation_rejects_preview_and_does_not_overwrite_it():
    scene = _scene()
    gesture = TransformGestureTransaction(scene, ["box"])
    gesture.preview_transform(translation=(1.0, 0.0))
    scene.objects["box"].polygon[0] = (999.0, 999.0)

    with pytest.raises(RuntimeError, match="changed outside"):
        gesture.preview_transform(translation=(2.0, 0.0))
