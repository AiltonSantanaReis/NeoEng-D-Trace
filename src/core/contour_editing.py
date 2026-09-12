"""Safe manual editing and simplification for an E09 vectorization result."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import cv2
import numpy as np

from src.core.operational_limits import MAX_POLYGON_POINTS
from src.core.polygon_validation import is_valid_polygon, signed_polygon_area2
from src.core.vectorization import VectorizationError, VectorizationResult

EditOperation = Literal["move_vertex", "insert_vertex", "remove_vertex", "simplify"]


@dataclass(frozen=True)
class ContourEdit:
    operation: EditOperation
    before: tuple[tuple[float, float], ...]
    after: tuple[tuple[float, float], ...]


def _canonical_polygon(
    points: list[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    if signed_polygon_area2(points) < 0:
        points.reverse()
    first = min(range(len(points)), key=lambda index: points[index])
    ordered = points[first:] + points[:first]
    return tuple(ordered)


def _validate(points: tuple[tuple[float, float], ...]) -> None:
    if not is_valid_polygon([tuple(point) for point in points]):
        raise VectorizationError(
            "invalid_geometry", "manual contour edit must remain a valid simple polygon"
        )


class ContourEditSession:
    """Transactional contour editor with bounded undo/redo and cancel."""

    def __init__(
        self,
        result: VectorizationResult,
        *,
        maximum_history: int = 256,
    ) -> None:
        if isinstance(maximum_history, bool) or not 1 <= maximum_history <= 4096:
            raise VectorizationError(
                "invalid_history_limit", "maximum_history must be between 1 and 4096"
            )
        initial = tuple((float(point[0]), float(point[1])) for point in result.polygon)
        _validate(initial)
        self._result = replace(result, polygon=initial)
        self._original = initial
        self._current = initial
        self._history: list[ContourEdit] = []
        self._cursor = 0
        self._maximum_history = maximum_history
        self._cancelled = False

    @property
    def original_polygon(self) -> tuple[tuple[float, float], ...]:
        return self._original

    @property
    def current_polygon(self) -> tuple[tuple[float, float], ...]:
        return self._current

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def can_undo(self) -> bool:
        return self._cursor > 0 and not self._cancelled

    @property
    def can_redo(self) -> bool:
        return self._cursor < len(self._history) and not self._cancelled

    @property
    def history(self) -> tuple[ContourEdit, ...]:
        return tuple(self._history)

    def _ensure_active(self) -> None:
        if self._cancelled:
            raise VectorizationError(
                "session_cancelled", "contour edit session was cancelled"
            )

    def _record(
        self,
        operation: EditOperation,
        candidate: tuple[tuple[float, float], ...],
    ) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        _validate(candidate)
        if self._cursor < len(self._history):
            del self._history[self._cursor :]
        self._history.append(ContourEdit(operation, self._current, candidate))
        if len(self._history) > self._maximum_history:
            del self._history[0]
        else:
            self._cursor += 1
        self._current = candidate
        return candidate

    def move_vertex(
        self, index: int, point: tuple[float, float]
    ) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        if isinstance(index, bool) or not isinstance(index, int):
            raise VectorizationError(
                "invalid_vertex_index", "vertex index must be an integer"
            )
        if not 0 <= index < len(self._current):
            raise VectorizationError(
                "invalid_vertex_index", "vertex index is outside the contour"
            )
        if len(point) != 2 or any(isinstance(value, bool) for value in point):
            raise VectorizationError(
                "invalid_vertex", "vertex must contain two numeric coordinates"
            )
        candidate = list(self._current)
        candidate[index] = (float(point[0]), float(point[1]))
        return self._record("move_vertex", tuple(candidate))

    def insert_vertex(
        self, after_index: int, point: tuple[float, float]
    ) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        if not 0 <= after_index < len(self._current):
            raise VectorizationError(
                "invalid_vertex_index", "insertion index is outside the contour"
            )
        if len(self._current) >= MAX_POLYGON_POINTS:
            raise VectorizationError("vertex_limit", "contour vertex limit reached")
        candidate = list(self._current)
        candidate.insert(after_index + 1, (float(point[0]), float(point[1])))
        return self._record("insert_vertex", tuple(candidate))

    def remove_vertex(self, index: int) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        if not 0 <= index < len(self._current):
            raise VectorizationError(
                "invalid_vertex_index", "vertex index is outside the contour"
            )
        if len(self._current) <= 3:
            raise VectorizationError(
                "invalid_geometry", "a contour requires at least three vertices"
            )
        candidate = list(self._current)
        del candidate[index]
        return self._record("remove_vertex", tuple(candidate))

    def simplify(self, epsilon: float) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        if not np.isfinite(epsilon) or epsilon <= 0:
            raise VectorizationError(
                "invalid_epsilon", "simplification epsilon must be positive"
            )
        contour = np.asarray(self._current, dtype=np.float32).reshape((-1, 1, 2))
        simplified = cv2.approxPolyDP(contour, float(epsilon), True)
        points: list[tuple[float, float]] = [
            (float(point[0]), float(point[1])) for point in simplified.reshape(-1, 2)
        ]
        if len(points) > MAX_POLYGON_POINTS:
            raise VectorizationError(
                "vertex_limit", "simplification exceeded the vertex limit"
            )
        if len(points) < 3:
            raise VectorizationError(
                "invalid_geometry", "simplification removed the contour"
            )
        candidate = _canonical_polygon(points)
        return self._record("simplify", candidate)

    def undo(self) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        if not self.can_undo:
            raise VectorizationError(
                "nothing_to_undo", "there is no contour edit to undo"
            )
        self._cursor -= 1
        self._current = self._history[self._cursor].before
        return self._current

    def redo(self) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        if not self.can_redo:
            raise VectorizationError(
                "nothing_to_redo", "there is no contour edit to redo"
            )
        self._current = self._history[self._cursor].after
        self._cursor += 1
        return self._current

    def cancel(self) -> tuple[tuple[float, float], ...]:
        self._ensure_active()
        self._current = self._original
        self._history.clear()
        self._cursor = 0
        self._cancelled = True
        return self._current

    def result(self) -> VectorizationResult:
        """Return the edited result while retaining source/provenance metadata."""

        self._ensure_active()
        return replace(self._result, polygon=self._current)


__all__ = ["ContourEdit", "ContourEditSession"]
