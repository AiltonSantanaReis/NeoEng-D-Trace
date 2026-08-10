"""Canonical static 2D polygon collision API."""

from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

import numpy as np

from src.core.convex_decomp import triangulate_to_convex

Point = Tuple[float, float]
PolygonLike = Sequence[Sequence[float]]
Array2D = np.ndarray


def _canonical_polygon(polygon: PolygonLike) -> list[Point]:
    points: list[Point] = []
    for index, point in enumerate(polygon):
        if isinstance(point, (str, bytes)):
            raise ValueError(f"Polygon point {index} must contain two coordinates")
        try:
            point_length = len(point)
        except TypeError as exc:
            raise ValueError(
                f"Polygon point {index} must contain two coordinates"
            ) from exc
        if point_length != 2:
            raise ValueError(f"Polygon point {index} must contain two coordinates")
        x, y = point
        if isinstance(x, bool) or isinstance(y, bool):
            raise ValueError(f"Polygon point {index} must be numeric")
        try:
            canonical = (float(x), float(y))
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"Polygon point {index} must be numeric") from exc
        if not math.isfinite(canonical[0]) or not math.isfinite(canonical[1]):
            raise ValueError(f"Polygon point {index} must be finite")
        points.append(canonical)

    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    if len(points) < 3:
        raise ValueError("Polygon must have at least three points")
    return points


def project_polygon(axis: np.ndarray, verts: np.ndarray) -> Tuple[float, float]:
    """Project polygon vertices onto one normalized axis."""
    dots = verts.dot(axis)
    return float(np.min(dots)), float(np.max(dots))


def overlap_intervals(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    """Return the signed overlap between two scalar intervals."""
    return min(a_max, b_max) - max(a_min, b_min)


def _convex_collision(
    first: Sequence[Point],
    second: Sequence[Point],
    epsilon: float,
) -> Tuple[bool, Optional[Point]]:
    vertices_a = np.asarray(first, dtype=float)
    vertices_b = np.asarray(second, dtype=float)
    axes: list[np.ndarray] = []

    for vertices in (vertices_a, vertices_b):
        for index, point in enumerate(vertices):
            edge = vertices[(index + 1) % len(vertices)] - point
            axis = np.asarray((-edge[1], edge[0]), dtype=float)
            norm = float(np.linalg.norm(axis))
            if norm > 0.0:
                axes.append(axis / norm)

    minimum_depth = float("inf")
    minimum_axis: Optional[np.ndarray] = None
    for axis in axes:
        first_min, first_max = project_polygon(axis, vertices_a)
        second_min, second_max = project_polygon(axis, vertices_b)
        overlap = overlap_intervals(first_min, first_max, second_min, second_max)
        if overlap < -epsilon:
            return False, None
        if overlap < minimum_depth:
            minimum_depth = max(0.0, overlap)
            minimum_axis = axis

    if minimum_axis is None:
        return False, None

    direction = np.mean(vertices_b, axis=0) - np.mean(vertices_a, axis=0)
    if np.dot(direction, minimum_axis) > 0.0:
        minimum_axis = -minimum_axis
    mtv = minimum_axis * minimum_depth
    return True, (float(mtv[0]), float(mtv[1]))


def _is_convex(polygon: Sequence[Point], epsilon: float) -> bool:
    orientation = 0
    for index, point in enumerate(polygon):
        second = polygon[(index + 1) % len(polygon)]
        third = polygon[(index + 2) % len(polygon)]
        cross = (second[0] - point[0]) * (third[1] - second[1]) - (
            second[1] - point[1]
        ) * (third[0] - second[0])
        if abs(cross) <= epsilon:
            continue
        sign = 1 if cross > 0.0 else -1
        if orientation and sign != orientation:
            return False
        orientation = sign
    return orientation != 0


def polygons_overlap(
    first: PolygonLike,
    second: PolygonLike,
    epsilon: float = 1e-7,
) -> Tuple[bool, Optional[Point]]:
    """Test static overlap for two valid simple polygons.

    The MTV is returned only when both inputs are convex. For concave inputs,
    triangulation provides an exact overlap decision but no misleading partial MTV.
    """
    if not math.isfinite(epsilon) or epsilon < 0.0:
        raise ValueError("epsilon must be a finite non-negative number")

    canonical_first = _canonical_polygon(first)
    canonical_second = _canonical_polygon(second)
    first_parts = triangulate_to_convex(canonical_first)
    second_parts = triangulate_to_convex(canonical_second)

    if _is_convex(canonical_first, epsilon) and _is_convex(canonical_second, epsilon):
        return _convex_collision(canonical_first, canonical_second, epsilon)

    for first_part in first_parts:
        for second_part in second_parts:
            if _convex_collision(first_part, second_part, epsilon)[0]:
                return True, None
    return False, None


def validate_polygon(polygon: PolygonLike) -> tuple[Point, ...]:
    """Validate and return one immutable canonical simple polygon."""
    canonical = _canonical_polygon(polygon)
    triangulate_to_convex(canonical)
    return tuple(canonical)


def project(polygon: Sequence[Point], axis: Point) -> Tuple[float, float]:
    """Compatibility projection helper for historical callers."""
    if not polygon:
        return 0.0, 0.0
    axis_array = np.asarray(axis, dtype=float)
    norm = float(np.linalg.norm(axis_array))
    if norm == 0.0:
        return 0.0, 0.0
    return project_polygon(axis_array / norm, np.asarray(polygon, dtype=float))


def polygon_edges(polygon: Sequence[Point]) -> list[Point]:
    """Return each polygon edge as a ``(dx, dy)`` vector."""
    if not polygon:
        return []
    return [
        (
            float(polygon[(index + 1) % len(polygon)][0] - point[0]),
            float(polygon[(index + 1) % len(polygon)][1] - point[1]),
        )
        for index, point in enumerate(polygon)
    ]


def sat_polygon_vs_polygon(
    first: Sequence[Point],
    second: Sequence[Point],
    epsilon: float = 1e-7,
) -> Tuple[bool, Optional[Point]]:
    """Compatibility list adapter preserving incomplete-input behavior."""
    if len(first) < 3 or len(second) < 3:
        return False, None
    return polygons_overlap(first, second, epsilon)


def polygon_collision_sat(
    verts_a: Array2D,
    verts_b: Array2D,
    epsilon: float = 1e-7,
) -> Tuple[bool, Optional[np.ndarray]]:
    """Compatibility adapter for the historical NumPy SAT API."""
    if verts_a.ndim != 2 or verts_b.ndim != 2:
        raise ValueError("Polygon arrays must be two-dimensional")
    collides, mtv = polygons_overlap(verts_a.tolist(), verts_b.tolist(), epsilon)
    return collides, None if mtv is None else np.asarray(mtv, dtype=float)
