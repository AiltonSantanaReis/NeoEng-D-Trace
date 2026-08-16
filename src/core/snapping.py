"""Deterministic pixel/grid snapping for editable 2D geometry."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence, cast


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be finite")
    try:
        result = float(cast(Any, value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _nearest_grid(value: float, origin: float, size: int) -> float:
    # Half-up rounding avoids Python's banker rounding at exact half pixels.
    quotient = (value - origin) / size
    return origin + math.floor(quotient + 0.5) * size


def snap_point(
    point: Sequence[float],
    *,
    grid_size: int = 1,
    origin: Sequence[float] = (0.0, 0.0),
) -> tuple[int, int]:
    """Snap an x/y point to a deterministic integer grid."""

    if isinstance(grid_size, bool) or not isinstance(grid_size, int) or grid_size <= 0:
        raise ValueError("grid_size must be a positive integer")
    if isinstance(point, (str, bytes)) or len(point) != 2:
        raise ValueError("point must contain x and y")
    if isinstance(origin, (str, bytes)) or len(origin) != 2:
        raise ValueError("origin must contain x and y")
    x = _finite(point[0], "point.x")
    y = _finite(point[1], "point.y")
    ox = _finite(origin[0], "origin.x")
    oy = _finite(origin[1], "origin.y")
    return (
        int(_nearest_grid(x, ox, grid_size)),
        int(_nearest_grid(y, oy, grid_size)),
    )


@dataclass(frozen=True)
class SnapSettings:
    """Validated opt-in settings used by the vertex editor."""

    enabled: bool = False
    grid_size: int = 1
    origin: tuple[float, float] = (0.0, 0.0)

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be boolean")
        snap_point((0.0, 0.0), grid_size=self.grid_size, origin=self.origin)

    def apply(self, point: Sequence[float]) -> tuple[int, int]:
        if not self.enabled:
            if len(point) != 2:
                raise ValueError("point must contain x and y")
            return (
                int(round(_finite(point[0], "point.x"))),
                int(round(_finite(point[1], "point.y"))),
            )
        return snap_point(point, grid_size=self.grid_size, origin=self.origin)
