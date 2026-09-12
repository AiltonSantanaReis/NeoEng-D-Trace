"""Qt-independent point-edit gesture contract for independent scenes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from src.persistence.independent_scene_schema import (
    IndependentScenePrimitiveGeometryRecord,
    PrimitiveKind,
)
from src.persistence.project_schema import PointRecord

PointEditState = Literal[
    "idle",
    "creating",
    "editing",
    "preview_invalid",
    "finalized",
    "cancelled",
]
MIN_POINT_DISTANCE = 24.0


@dataclass
class IndependentScenePointEditGesture:
    """Transactional point-edit state used by both tests and the Qt adapter."""

    primitive_id: str | None = None
    state: PointEditState = "idle"
    point_index: int | None = None
    original_points: tuple[PointRecord, ...] = ()
    working_points: tuple[PointRecord, ...] = ()
    closed: bool = True
    filled: bool = True
    kind: PrimitiveKind = "path"
    last_error: str | None = None

    def begin(
        self,
        primitive_id: str,
        geometry: IndependentScenePrimitiveGeometryRecord,
        *,
        locked: bool = False,
    ) -> None:
        if locked:
            raise PermissionError(f"primitive {primitive_id!r} is locked")
        self.primitive_id = primitive_id
        self.kind = geometry.kind
        self.closed = geometry.closed
        self.filled = geometry.filled
        self.original_points = tuple(geometry.points)
        self.working_points = tuple(geometry.points)
        self.point_index = None
        self.last_error = None
        self.state = "editing"

    def begin_creation(
        self, primitive_id: str, geometry: IndependentScenePrimitiveGeometryRecord
    ) -> None:
        self.begin(primitive_id, geometry)
        self.state = "creating"

    def preview_point(self, point_index: int, point: PointRecord) -> bool:
        if self.state not in {"creating", "editing", "preview_invalid"}:
            raise RuntimeError("point edit gesture is not active")
        if not 0 <= point_index < len(self.working_points):
            raise IndexError(point_index)
        candidate = list(self.working_points)
        candidate[point_index] = point
        try:
            for index, other in enumerate(candidate):
                if index == point_index:
                    continue
                if (
                    math.hypot(point.x - other.x, point.y - other.y)
                    < MIN_POINT_DISTANCE
                ):
                    raise ValueError(
                        "preview points must remain at least 24 pixels apart"
                    )
            IndependentScenePrimitiveGeometryRecord(
                kind=self.kind,
                points=candidate,
                closed=self.closed,
                filled=self.filled,
            )
        except ValueError as exc:
            self.working_points = tuple(candidate)
            self.point_index = point_index
            self.last_error = str(exc)
            self.state = "preview_invalid"
            return False
        self.working_points = tuple(candidate)
        self.point_index = point_index
        self.last_error = None
        self.state = "editing"
        return True

    def commit(self) -> tuple[PointRecord, ...]:
        if self.state not in {"creating", "editing"}:
            raise ValueError("cannot finalize an invalid or inactive point edit")
        IndependentScenePrimitiveGeometryRecord(
            kind=self.kind,
            points=list(self.working_points),
            closed=self.closed,
            filled=self.filled,
        )
        self.state = "finalized"
        self.point_index = None
        return self.working_points

    def double_click_finalize(self) -> tuple[PointRecord, ...]:
        return self.commit()

    def cancel(self) -> tuple[PointRecord, ...]:
        self.working_points = self.original_points
        self.point_index = None
        self.last_error = None
        self.state = "cancelled"
        return self.original_points

    def escape(self) -> tuple[PointRecord, ...]:
        return self.cancel()

    def click_empty(self) -> tuple[PointRecord, ...]:
        return self.cancel()

    def reactivate(self) -> None:
        if self.primitive_id is None:
            raise RuntimeError("no primitive is available for reactivation")
        self.working_points = self.original_points
        self.point_index = None
        self.last_error = None
        self.state = "editing"


__all__ = ["IndependentScenePointEditGesture", "PointEditState"]
