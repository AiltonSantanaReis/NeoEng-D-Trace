"""Canonical cubic Bézier geometry used by scene commands and tools."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

BezierPoint = Tuple[float, float]
BezierSegment = Tuple[BezierPoint, BezierPoint, BezierPoint, BezierPoint]
BezierSegments = List[BezierSegment]
PolygonPoint = Tuple[int, int]


def canonical_point(value: Sequence[float], *, label: str = "point") -> BezierPoint:
    """Return one finite numeric point without retaining mutable aliases."""

    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{label} must contain exactly two coordinates.")
    x, y = value
    if (
        isinstance(x, bool)
        or isinstance(y, bool)
        or not isinstance(x, (int, float))
        or not isinstance(y, (int, float))
    ):
        raise ValueError(f"{label} coordinates must be numeric.")
    point = (float(x), float(y))
    if not math.isfinite(point[0]) or not math.isfinite(point[1]):
        raise ValueError(f"{label} coordinates must be finite.")
    return point


def canonicalize_beziers(
    beziers: Iterable[Sequence[Sequence[float]]],
) -> BezierSegments:
    """Validate cubic segments and return an independent canonical structure."""

    if not isinstance(beziers, (list, tuple)):
        raise ValueError("Bézier geometry must be a sequence of segments.")

    canonical: BezierSegments = []
    for segment_index, segment in enumerate(beziers):
        if not isinstance(segment, (list, tuple)) or len(segment) != 4:
            raise ValueError(
                f"Bézier segment {segment_index} must contain four control points."
            )
        points = tuple(
            canonical_point(point, label=f"segment {segment_index} point {point_index}")
            for point_index, point in enumerate(segment)
        )
        canonical.append(points)  # type: ignore[arg-type]

    if not canonical:
        raise ValueError("At least one Bézier segment is required.")

    for segment_index in range(1, len(canonical)):
        if canonical[segment_index - 1][3] != canonical[segment_index][0]:
            raise ValueError(
                f"Bézier segment {segment_index} is not continuous with the previous segment."
            )
    return canonical


def cubic_bezier_point(
    t: float,
    p0: BezierPoint,
    p1: BezierPoint,
    p2: BezierPoint,
    p3: BezierPoint,
) -> BezierPoint:
    """Evaluate one cubic Bézier segment at ``t``."""

    u = 1.0 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t
    return (
        uuu * p0[0] + 3.0 * uu * t * p1[0] + 3.0 * u * tt * p2[0] + ttt * p3[0],
        uuu * p0[1] + 3.0 * uu * t * p1[1] + 3.0 * u * tt * p2[1] + ttt * p3[1],
    )


def sample_beziers(
    beziers: Iterable[Sequence[Sequence[float]]],
    *,
    steps_per_segment: int = 20,
) -> List[BezierPoint]:
    """Sample continuous cubic segments deterministically."""

    if isinstance(steps_per_segment, bool) or not isinstance(steps_per_segment, int):
        raise ValueError("steps_per_segment must be an integer.")
    if steps_per_segment < 1:
        raise ValueError("steps_per_segment must be at least 1.")

    canonical = canonicalize_beziers(beziers)
    sampled: List[BezierPoint] = []
    for segment_index, segment in enumerate(canonical):
        segment_points = [
            cubic_bezier_point(step / steps_per_segment, *segment)
            for step in range(steps_per_segment + 1)
        ]
        if segment_index:
            segment_points = segment_points[1:]
        sampled.extend(segment_points)
    return sampled


def sample_beziers_to_polygon(
    beziers: Iterable[Sequence[Sequence[float]]],
    *,
    steps_per_segment: int = 20,
) -> List[PolygonPoint]:
    """Sample cubic geometry into the integer polygon stored by the scene."""

    polygon: List[PolygonPoint] = []
    for x, y in sample_beziers(beziers, steps_per_segment=steps_per_segment):
        point = (int(round(x)), int(round(y)))
        if not polygon or polygon[-1] != point:
            polygon.append(point)
    if len(polygon) < 3:
        raise ValueError("Sampled Bézier geometry must contain at least three points.")
    return polygon


def replace_handle(
    beziers: Iterable[Sequence[Sequence[float]]],
    segment_index: int,
    handle_index: int,
    position: Sequence[float],
) -> BezierSegments:
    """Return canonical geometry with one cubic handle replaced."""

    canonical = canonicalize_beziers(beziers)
    if isinstance(segment_index, bool) or not isinstance(segment_index, int):
        raise ValueError("segment_index must be an integer.")
    if segment_index < 0 or segment_index >= len(canonical):
        raise ValueError("segment_index is outside the Bézier geometry.")
    if handle_index not in {1, 2}:
        raise ValueError("handle_index must identify control point 1 or 2.")

    segment = list(canonical[segment_index])
    segment[handle_index] = canonical_point(position, label="handle position")
    canonical[segment_index] = tuple(segment)  # type: ignore[assignment]
    return canonical
