"""Transactional support for continuous polygon gestures."""

from __future__ import annotations

import copy
from typing import Any, List, Optional, Tuple

from src.core.commands import (
    CommandManager,
    CommandResult,
    UpdatePolygonCommand,
)

Point = Tuple[int, int]
CollisionPoint = Tuple[float, float]


class PolygonGestureTransaction:
    """Preview continuously and commit one polygon history entry.

    The scene may notify on every preview for responsive rendering.
    Commit quietly restores the exact origin and then delegates the
    final replacement to UpdatePolygonCommand. Therefore the command
    manager observes one normal atomic edit instead of every mouse
    movement.
    """

    def __init__(self, scene: Any, object_id: str):
        obj = scene.objects.get(object_id)
        if obj is None:
            raise KeyError(object_id)

        self.scene = scene
        self.object_id = str(object_id)
        self._origin_polygon: List[Point] = [tuple(point) for point in obj.polygon]
        self._had_collision = self.object_id in scene.collision_shapes
        self._origin_collision: Optional[List[CollisionPoint]] = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if self._had_collision
            else None
        )
        self._last_preview: List[Point] = copy.deepcopy(self._origin_polygon)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    @property
    def origin_polygon(self) -> List[Point]:
        return copy.deepcopy(self._origin_polygon)

    @property
    def preview_polygon(self) -> List[Point]:
        return copy.deepcopy(self._last_preview)

    def _require_active_object(self):
        if not self._active:
            raise RuntimeError("The polygon gesture is no longer active.")
        obj = self.scene.objects.get(self.object_id)
        if obj is None:
            raise KeyError(self.object_id)
        return obj

    def _current_polygon(self) -> List[Point]:
        obj = self.scene.objects.get(self.object_id)
        if obj is None:
            return []
        return [tuple(point) for point in obj.polygon]

    def _state_differs_from_origin(self) -> bool:
        if self._current_polygon() != self._origin_polygon:
            return True
        if self._had_collision:
            return (
                self.scene.collision_shapes.get(self.object_id)
                != self._origin_collision
            )
        return self.object_id in self.scene.collision_shapes

    def _restore_origin(self, *, notify: bool) -> None:
        obj = self.scene.objects.get(self.object_id)
        if obj is None:
            return

        obj.polygon = copy.deepcopy(self._origin_polygon)
        if self._had_collision and self._origin_collision is not None:
            self.scene.collision_shapes[self.object_id] = copy.deepcopy(
                self._origin_collision
            )
        else:
            self.scene.collision_shapes.pop(self.object_id, None)
        if notify and hasattr(self.scene, "_notify"):
            self.scene._notify()

    def preview(self, polygon: List[Point]) -> List[Point]:
        obj = self._require_active_object()
        current = [tuple(point) for point in obj.polygon]
        if current != self._last_preview:
            raise RuntimeError("The polygon changed outside the active gesture.")

        candidate = [tuple(point) for point in polygon]
        self.scene.update_polygon(self.object_id, candidate)
        self._last_preview = self._current_polygon()
        return self.preview_polygon

    def cancel(self) -> bool:
        self._require_active_object()
        changed = self._state_differs_from_origin()
        self._restore_origin(notify=changed)
        self._active = False
        return changed

    def commit(
        self,
        manager: Optional[CommandManager],
    ) -> CommandResult:
        obj = self._require_active_object()
        current = [tuple(point) for point in obj.polygon]
        command = UpdatePolygonCommand(
            self.object_id,
            self._origin_polygon,
            current,
        )

        if current != self._last_preview:
            self._active = False
            return CommandResult.rejected(
                command,
                "execute",
                "The polygon changed outside the active gesture.",
            )

        if current == self._origin_polygon:
            self.cancel()
            return CommandResult.no_change(
                command,
                "execute",
                "The gesture ended without moving the polygon.",
            )

        if manager is None:
            self._restore_origin(notify=True)
            self._active = False
            return CommandResult.failed(
                command,
                "execute",
                "CommandManagerUnavailable",
                "The gesture was cancelled because history " "is unavailable.",
            )

        self._restore_origin(notify=False)
        self._active = False
        result = manager.execute(command, self.scene)
        if not result.changed and hasattr(self.scene, "_notify"):
            self.scene._notify()
        return result
