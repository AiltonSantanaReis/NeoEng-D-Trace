"""Transactional 2D/2.5D object transforms for the canvas gizmo."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

from src.core.commands import Command, CommandManager, CommandResult
from src.core.transform_geometry import transform_point, transform_points


@dataclass
class ObjectTransformState:
    """Complete mutable state owned by one transformed scene object."""

    polygon: list[tuple[float, float]]
    beziers: Any
    position: tuple[float, float, float]
    rotation: tuple[float, float, float]
    scale: tuple[float, float, float]
    pivot: tuple[float, float]
    collision: Optional[list[tuple[float, float]]]
    collision_parts: Optional[list[list[tuple[float, float]]]]


TransformSnapshot = dict[str, ObjectTransformState]


def capture_transform_state(scene: Any, object_ids: Iterable[str]) -> TransformSnapshot:
    """Capture geometry, metadata and all collision representations."""

    snapshot: TransformSnapshot = {}
    for object_id in object_ids:
        obj = scene.objects.get(object_id)
        if obj is None:
            raise KeyError(object_id)
        snapshot[str(object_id)] = ObjectTransformState(
            polygon=copy.deepcopy(obj.polygon),
            beziers=copy.deepcopy(getattr(obj, "beziers", None)),
            position=tuple(getattr(obj, "position", (0.0, 0.0, 0.0))),
            rotation=tuple(getattr(obj, "rotation", (0.0, 0.0, 0.0))),
            scale=tuple(getattr(obj, "scale", (1.0, 1.0, 1.0))),
            pivot=tuple(getattr(obj, "pivot", (0.5, 0.5))),
            collision=copy.deepcopy(scene.collision_shapes.get(object_id)),
            collision_parts=copy.deepcopy(scene.collision_parts.get(object_id)),
        )
    return snapshot


def apply_transform_state(scene: Any, snapshot: TransformSnapshot) -> None:
    """Apply a complete snapshot without silently dropping collision parts."""

    for object_id, state in snapshot.items():
        obj = scene.objects.get(object_id)
        if obj is None:
            raise KeyError(object_id)
        obj.polygon = copy.deepcopy(state.polygon)
        obj.beziers = copy.deepcopy(state.beziers)
        obj.position = tuple(state.position)
        obj.rotation = tuple(state.rotation)
        obj.scale = tuple(state.scale)
        obj.pivot = tuple(state.pivot)
        if state.collision is None:
            scene.collision_shapes.pop(object_id, None)
        else:
            scene.collision_shapes[object_id] = copy.deepcopy(state.collision)
        if state.collision_parts is None:
            scene.collision_parts.pop(object_id, None)
        else:
            scene.collision_parts[object_id] = copy.deepcopy(state.collision_parts)


def transformed_snapshot(
    scene: Any,
    object_ids: Iterable[str],
    *,
    translation: Sequence[float] = (0.0, 0.0),
    rotation_degrees: float = 0.0,
    scale: Sequence[float] = (1.0, 1.0),
    anchor_override: Optional[Sequence[float]] = None,
    base_snapshot: Optional[TransformSnapshot] = None,
) -> TransformSnapshot:
    """Build a transformed snapshot around each object's own pivot."""

    source = copy.deepcopy(base_snapshot) if base_snapshot is not None else capture_transform_state(scene, object_ids)
    result = copy.deepcopy(source)
    for object_id, state in source.items():
        anchor = (
            tuple(float(value) for value in anchor_override[:2])
            if anchor_override is not None
            else state.position[:2]
        )
        result[object_id].polygon = transform_points(
            state.polygon,
            anchor,
            translation=translation,
            rotation_degrees=rotation_degrees,
            scale=scale,
        )
        if state.collision is not None:
            result[object_id].collision = transform_points(
                state.collision,
                anchor,
                translation=translation,
                rotation_degrees=rotation_degrees,
                scale=scale,
            )
        if state.collision_parts is not None:
            result[object_id].collision_parts = [
                transform_points(
                    part,
                    anchor,
                    translation=translation,
                    rotation_degrees=rotation_degrees,
                    scale=scale,
                )
                for part in state.collision_parts
            ]
        if state.beziers is not None:
            result[object_id].beziers = [
                tuple(
                    transform_points(
                        segment,
                        anchor,
                        translation=translation,
                        rotation_degrees=rotation_degrees,
                        scale=scale,
                    )
                )
                for segment in state.beziers
            ]
        result_position = transform_point(
            state.position,
            anchor,
            translation=translation,
            rotation_degrees=rotation_degrees,
            scale=scale,
        )
        result[object_id].position = (
            result_position[0],
            result_position[1],
            state.position[2],
        )
        result[object_id].rotation = (
            state.rotation[0],
            state.rotation[1],
            state.rotation[2] + float(rotation_degrees),
        )
        result[object_id].scale = (
            state.scale[0] * float(scale[0]),
            state.scale[1] * float(scale[1]),
            state.scale[2],
        )
    return result


class TransformObjectsCommand(Command):
    """Apply one atomic transform to one or more objects."""

    def __init__(self, before: TransformSnapshot, after: TransformSnapshot):
        self.before = copy.deepcopy(before)
        self.after = copy.deepcopy(after)

    def execute(self, scene: Any):
        current = capture_transform_state(scene, self.before)
        if current != self.before:
            return CommandResult.rejected(
                self,
                "execute",
                "Object geometry or transform changed before the operation.",
            )
        if current == self.after:
            return CommandResult.no_change(
                self,
                "execute",
                "The transform did not change the selected objects.",
            )
        apply_transform_state(scene, self.after)
        scene._notify()

    def undo(self, scene: Any):
        current = capture_transform_state(scene, self.after)
        if current != self.after:
            return CommandResult.rejected(
                self,
                "undo",
                "Object geometry or transform changed before Undo.",
            )
        apply_transform_state(scene, self.before)
        scene._notify()


class TransformGestureTransaction:
    """Preview a transform and commit at most one history entry."""

    def __init__(self, scene: Any, object_ids: Iterable[str]):
        self.scene = scene
        self.object_ids = tuple(dict.fromkeys(str(value) for value in object_ids))
        if not self.object_ids:
            raise ValueError("at least one object is required")
        self._origin = capture_transform_state(scene, self.object_ids)
        self._last = copy.deepcopy(self._origin)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    @property
    def origin(self) -> TransformSnapshot:
        return copy.deepcopy(self._origin)

    @property
    def preview(self) -> TransformSnapshot:
        return copy.deepcopy(self._last)

    def preview_transform(
        self,
        *,
        translation: Sequence[float] = (0.0, 0.0),
        rotation_degrees: float = 0.0,
        scale: Sequence[float] = (1.0, 1.0),
        anchor_override: Optional[Sequence[float]] = None,
    ) -> TransformSnapshot:
        if not self._active:
            raise RuntimeError("The transform gesture is no longer active.")
        current = capture_transform_state(self.scene, self.object_ids)
        if current != self._last:
            raise RuntimeError("The object state changed outside the active gesture.")
        self._last = transformed_snapshot(
            self.scene,
            self.object_ids,
            translation=translation,
            rotation_degrees=rotation_degrees,
            scale=scale,
            anchor_override=anchor_override,
            base_snapshot=self._origin,
        )
        apply_transform_state(self.scene, self._last)
        self.scene._notify()
        return self.preview

    def cancel(self) -> bool:
        if not self._active:
            return False
        current = capture_transform_state(self.scene, self.object_ids)
        changed = current != self._origin
        if current != self._last:
            raise RuntimeError("The object state changed outside the active gesture.")
        apply_transform_state(self.scene, self._origin)
        if changed:
            self.scene._notify()
        self._active = False
        return changed

    def commit(self, manager: Optional[CommandManager]) -> CommandResult:
        if not self._active:
            raise RuntimeError("The transform gesture is no longer active.")
        current = capture_transform_state(self.scene, self.object_ids)
        if current != self._last:
            raise RuntimeError("The object state changed outside the active gesture.")
        command = TransformObjectsCommand(self._origin, self._last)
        if current == self._origin:
            self._active = False
            return CommandResult.no_change(
                command,
                "execute",
                "The gesture ended without changing the selected objects.",
            )
        if manager is None:
            apply_transform_state(self.scene, self._origin)
            self.scene._notify()
            self._active = False
            return CommandResult.failed(
                command,
                "execute",
                "CommandManagerUnavailable",
                "The transform was cancelled because history is unavailable.",
            )
        apply_transform_state(self.scene, self._origin)
        self._active = False
        return manager.execute(command, self.scene)
