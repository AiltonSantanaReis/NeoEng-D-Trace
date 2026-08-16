"""Regression coverage for deterministic gizmo previews."""

from src.core.commands import CommandManager
from src.core.transform_gesture import TransformGestureTransaction
from src.models.scene import Scene


def test_repeated_preview_is_always_relative_to_gesture_origin():
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object("box", [(0, 0), (20, 0), (20, 20), (0, 20)], select=True)
    gesture = TransformGestureTransaction(scene, ["box"])

    gesture.preview_transform(translation=(0.4, 0.0))
    gesture.preview_transform(translation=(0.8, 0.0))
    gesture.preview_transform(translation=(1.2, 0.0))

    assert scene.objects["box"].polygon == [
        (1.2, 0.0),
        (21.2, 0.0),
        (21.2, 20.0),
        (1.2, 20.0),
    ]
