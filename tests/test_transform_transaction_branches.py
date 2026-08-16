"""Branch contracts for transform transactions and command preconditions."""

from __future__ import annotations

import pytest

from src.core.commands import CommandManager, CommandStatus
from src.core.transform_gesture import (
    TransformGestureTransaction,
    TransformObjectsCommand,
    apply_transform_state,
    capture_transform_state,
)
from src.models.scene import Scene


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object("box", [(10, 20), (30, 20), (30, 40), (10, 40)])
    return scene


def test_transaction_rejects_empty_or_unknown_objects() -> None:
    scene = _scene()
    with pytest.raises(ValueError, match="at least one"):
        TransformGestureTransaction(scene, [])
    with pytest.raises(KeyError, match="missing"):
        TransformGestureTransaction(scene, ["missing"])


def test_transaction_no_change_and_cancel_without_preview() -> None:
    scene = _scene()
    gesture = TransformGestureTransaction(scene, ["box"])
    result = gesture.commit(scene.cmd)
    assert result.status is CommandStatus.NO_CHANGE
    assert gesture.active is False

    second = TransformGestureTransaction(scene, ["box"])
    assert second.cancel() is False
    assert second.cancel() is False
    assert second.active is False


def test_transaction_rejects_external_state_change_on_cancel_and_commit() -> None:
    scene = _scene()
    gesture = TransformGestureTransaction(scene, ["box"])
    gesture.preview_transform(translation=(1.0, 0.0))
    scene.objects["box"].position = (999.0, 0.0, 0.0)
    with pytest.raises(RuntimeError, match="changed outside"):
        gesture.cancel()

    fresh = TransformGestureTransaction(scene, ["box"])
    scene.objects["box"].position = (998.0, 0.0, 0.0)
    with pytest.raises(RuntimeError, match="changed outside"):
        fresh.commit(scene.cmd)


def test_command_rejects_stale_states_and_handles_missing_collisions() -> None:
    scene = _scene()
    before = capture_transform_state(scene, ["box"])
    after = capture_transform_state(scene, ["box"])
    after["box"].position = (3.0, 4.0, 0.0)
    command = TransformObjectsCommand(before, after)

    scene.objects["box"].position = (1.0, 0.0, 0.0)
    assert command.execute(scene) is not None
    scene.objects["box"].position = before["box"].position
    command.execute(scene)
    assert scene.objects["box"].position == after["box"].position
    scene.objects["box"].position = (9.0, 9.0, 0.0)
    assert command.undo(scene).status is CommandStatus.REJECTED
    assert scene.objects["box"].position == (9.0, 9.0, 0.0)

    scene.objects["box"].position = after["box"].position
    command.undo(scene)
    assert scene.objects["box"].position == before["box"].position
    assert apply_transform_state(scene, before) is None


def test_transform_state_rejects_unknown_object_and_transforms_bezier_segments() -> (
    None
):
    scene = _scene()
    before = capture_transform_state(scene, ["box"])
    with pytest.raises(KeyError, match="missing"):
        apply_transform_state(scene, {"missing": before["box"]})

    scene.objects["box"].beziers = [
        ((10.0, 20.0), (15.0, 25.0), (20.0, 30.0)),
    ]
    gesture = TransformGestureTransaction(scene, ["box"])
    gesture.preview_transform(translation=(2.0, 3.0))
    assert scene.objects["box"].beziers == [
        ((12.0, 23.0), (17.0, 28.0), (22.0, 33.0)),
    ]


def test_transform_command_no_change_and_inactive_transaction_guards() -> None:
    scene = _scene()
    before = capture_transform_state(scene, ["box"])
    assert (
        TransformObjectsCommand(before, before).execute(scene).status
        is CommandStatus.NO_CHANGE
    )

    gesture = TransformGestureTransaction(scene, ["box"])
    gesture.commit(scene.cmd)
    with pytest.raises(RuntimeError, match="no longer active"):
        gesture.preview_transform()
    with pytest.raises(RuntimeError, match="no longer active"):
        gesture.commit(scene.cmd)
