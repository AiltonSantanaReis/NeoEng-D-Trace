"""Deterministic geometry helpers for object transforms."""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

Point2 = Tuple[float, float]


def finite_float(value: object, field: str) -> float:
    """Return a finite float and reject booleans or non-numeric values."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{field} must be a finite number")
    return converted


def validate_scale(scale_x: object, scale_y: object, scale_z: object = 1.0) -> Point2:
    """Validate a non-zero 2D scale used by the canvas."""

    values = (
        finite_float(scale_x, "scale.x"),
        finite_float(scale_y, "scale.y"),
        finite_float(scale_z, "scale.z"),
    )
    if any(abs(value) < 1e-9 for value in values):
        raise ValueError("scale components cannot be zero")
    return values[0], values[1]


def polygon_bounds(points: Iterable[Sequence[float]]) -> tuple[float, float, float, float]:
    """Return the image-space bounding box of a non-empty point sequence."""

    normalized = [
        (finite_float(point[0], "point.x"), finite_float(point[1], "point.y"))
        for point in points
    ]
    if not normalized:
        raise ValueError("polygon cannot be empty")
    xs = [point[0] for point in normalized]
    ys = [point[1] for point in normalized]
    return min(xs), min(ys), max(xs), max(ys)


def anchor_for_polygon(
    points: Iterable[Sequence[float]], pivot: Sequence[float]
) -> Point2:
    """Resolve a normalized bounding-box pivot to image-space coordinates."""

    min_x, min_y, max_x, max_y = polygon_bounds(points)
    px = finite_float(pivot[0], "pivot.x")
    py = finite_float(pivot[1], "pivot.y")
    return (
        min_x + (max_x - min_x) * px,
        min_y + (max_y - min_y) * py,
    )


def transform_point(
    point: Sequence[float],
    anchor: Sequence[float],
    *,
    translation: Sequence[float] = (0.0, 0.0),
    rotation_degrees: float = 0.0,
    scale: Sequence[float] = (1.0, 1.0),
) -> Point2:
    """Apply scale and rotation around ``anchor`` followed by translation."""

    x = finite_float(point[0], "point.x") - finite_float(anchor[0], "anchor.x")
    y = finite_float(point[1], "point.y") - finite_float(anchor[1], "anchor.y")
    sx, sy = validate_scale(scale[0], scale[1])
    x *= sx
    y *= sy
    angle = math.radians(finite_float(rotation_degrees, "rotation.z"))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    rotated_x = x * cosine - y * sine
    rotated_y = x * sine + y * cosine
    tx = finite_float(translation[0], "translation.x")
    ty = finite_float(translation[1], "translation.y")
    return (
        finite_float(anchor[0], "anchor.x") + rotated_x + tx,
        finite_float(anchor[1], "anchor.y") + rotated_y + ty,
    )


def transform_points(
    points: Iterable[Sequence[float]],
    anchor: Sequence[float],
    *,
    translation: Sequence[float] = (0.0, 0.0),
    rotation_degrees: float = 0.0,
    scale: Sequence[float] = (1.0, 1.0),
) -> list[Point2]:
    """Transform a point sequence without mutating the source."""

    return [
        transform_point(
            point,
            anchor,
            translation=translation,
            rotation_degrees=rotation_degrees,
            scale=scale,
        )
        for point in points
    ]
