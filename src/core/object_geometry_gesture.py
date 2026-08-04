"""Transactional preview for polygon and collision geometry."""

from __future__ import annotations

import copy
from typing import Any, List, Optional, Tuple

from src.core.commands import (
    CommandManager,
    CommandResult,
    UpdateObjectGeometryCommand,
)

GeometryPoint = Tuple[float, float]


class ObjectGeometryGestureTransaction:
    """Preview one geometry transform and commit one history entry."""

    def __init__(self, scene: Any, object_id: str):
        obj = scene.objects.get(object_id)
        if obj is None:
            raise KeyError(object_id)

        self.scene = scene
        self.object_id = str(object_id)
        self._origin_polygon: List[GeometryPoint] = [
            (point[0], point[1]) for point in obj.polygon
        ]
        self._origin_has_collision = self.object_id in scene.collision_shapes
        self._origin_collision: Optional[List[GeometryPoint]] = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if self._origin_has_collision
            else None
        )
        self._last_polygon = copy.deepcopy(self._origin_polygon)
        self._last_has_collision = self._origin_has_collision
        self._last_collision = copy.deepcopy(self._origin_collision)
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    @property
    def origin_polygon(self) -> List[GeometryPoint]:
        return copy.deepcopy(self._origin_polygon)

    @property
    def origin_has_collision(self) -> bool:
        return self._origin_has_collision

    @property
    def origin_collision(self) -> Optional[List[GeometryPoint]]:
        return copy.deepcopy(self._origin_collision)

    @property
    def preview_polygon(self) -> List[GeometryPoint]:
        return copy.deepcopy(self._last_polygon)

    @property
    def preview_collision(self) -> Optional[List[GeometryPoint]]:
        return copy.deepcopy(self._last_collision)

    def _require_active_object(self):
        if not self._active:
            raise RuntimeError("The geometry gesture is no longer active.")
        obj = self.scene.objects.get(self.object_id)
        if obj is None:
            raise KeyError(self.object_id)
        return obj

    def _current_geometry(
        self,
    ) -> Tuple[
        List[GeometryPoint],
        bool,
        Optional[List[GeometryPoint]],
    ]:
        obj = self.scene.objects.get(self.object_id)
        if obj is None:
            return [], False, None
        has_collision = self.object_id in self.scene.collision_shapes
        collision = (
            copy.deepcopy(self.scene.collision_shapes[self.object_id])
            if has_collision
            else None
        )
        return (
            [(point[0], point[1]) for point in obj.polygon],
            has_collision,
            collision,
        )

    def _last_geometry(
        self,
    ) -> Tuple[
        List[GeometryPoint],
        bool,
        Optional[List[GeometryPoint]],
    ]:
        return (
            copy.deepcopy(self._last_polygon),
            self._last_has_collision,
            copy.deepcopy(self._last_collision),
        )

    def _origin_geometry(
        self,
    ) -> Tuple[
        List[GeometryPoint],
        bool,
        Optional[List[GeometryPoint]],
    ]:
        return (
            copy.deepcopy(self._origin_polygon),
            self._origin_has_collision,
            copy.deepcopy(self._origin_collision),
        )

    def _restore_origin(self, *, notify: bool) -> None:
        obj = self.scene.objects.get(self.object_id)
        if obj is None:
            return
        obj.polygon = copy.deepcopy(self._origin_polygon)
        if self._origin_has_collision:
            self.scene.collision_shapes[self.object_id] = copy.deepcopy(
                self._origin_collision
            )
        else:
            self.scene.collision_shapes.pop(
                self.object_id,
                None,
            )
        if notify and hasattr(self.scene, "_notify"):
            self.scene._notify()

    def preview(
        self,
        polygon: List[GeometryPoint],
        *,
        has_collision: bool,
        collision: Optional[List[GeometryPoint]],
    ) -> Tuple[
        List[GeometryPoint],
        Optional[List[GeometryPoint]],
    ]:
        obj = self._require_active_object()
        if self._current_geometry() != self._last_geometry():
            raise RuntimeError(
                "The object geometry changed outside " "the active gesture."
            )
        if has_collision and collision is None:
            raise ValueError(
                "Collision geometry is required when collision " "is enabled."
            )

        candidate_polygon: List[GeometryPoint] = [
            (point[0], point[1]) for point in polygon
        ]
        candidate_collision = copy.deepcopy(collision) if has_collision else None
        obj.polygon = copy.deepcopy(candidate_polygon)
        if has_collision:
            self.scene.collision_shapes[self.object_id] = copy.deepcopy(
                candidate_collision
            )
        else:
            self.scene.collision_shapes.pop(
                self.object_id,
                None,
            )
        self.scene._notify()

        self._last_polygon = copy.deepcopy(candidate_polygon)
        self._last_has_collision = bool(has_collision)
        self._last_collision = copy.deepcopy(candidate_collision)
        return (
            self.preview_polygon,
            self.preview_collision,
        )

    def cancel(self) -> bool:
        self._require_active_object()
        changed = self._current_geometry() != self._origin_geometry()
        self._restore_origin(notify=changed)
        self._active = False
        return changed

    def commit(
        self,
        manager: Optional[CommandManager],
    ) -> CommandResult:
        self._require_active_object()
        current = self._current_geometry()
        command = UpdateObjectGeometryCommand(
            self.object_id,
            self._origin_polygon,
            current[0],
            old_has_collision=self._origin_has_collision,
            old_collision=self._origin_collision,
            new_has_collision=current[1],
            new_collision=current[2],
        )

        if current != self._last_geometry():
            self._active = False
            return CommandResult.rejected(
                command,
                "execute",
                "The object geometry changed outside " "the active gesture.",
            )

        if current == self._origin_geometry():
            self.cancel()
            return CommandResult.no_change(
                command,
                "execute",
                "The gesture ended without changing geometry.",
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
