"""Deterministic polygon validity shared by runtime and persistence."""

from __future__ import annotations

import math
from typing import Any, Sequence

from src.core.operational_limits import MAX_POLYGON_POINTS

Point = tuple[float, float]


def signed_polygon_area2(points: Sequence[Point]) -> float:
    return sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


def lines_intersect(first_start, first_end, second_start, second_end) -> bool:
    """Return whether two closed line segments intersect or touch."""

    def orientation(start, end, point) -> float:
        return (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (
            point[0] - start[0]
        )

    def sign(value: float) -> int:
        if value > 1e-9:
            return 1
        if value < -1e-9:
            return -1
        return 0

    def on_segment(start, end, point) -> bool:
        return (
            min(start[0], end[0]) - 1e-9 <= point[0] <= max(start[0], end[0]) + 1e-9
            and min(start[1], end[1]) - 1e-9 <= point[1] <= max(start[1], end[1]) + 1e-9
        )

    first = orientation(first_start, first_end, second_start)
    second = orientation(first_start, first_end, second_end)
    third = orientation(second_start, second_end, first_start)
    fourth = orientation(second_start, second_end, first_end)
    first_sign = sign(first)
    second_sign = sign(second)
    third_sign = sign(third)
    fourth_sign = sign(fourth)

    if first_sign * second_sign < 0 and third_sign * fourth_sign < 0:
        return True
    if first_sign == 0 and on_segment(first_start, first_end, second_start):
        return True
    if second_sign == 0 and on_segment(first_start, first_end, second_end):
        return True
    if third_sign == 0 and on_segment(second_start, second_end, first_start):
        return True
    if fourth_sign == 0 and on_segment(second_start, second_end, first_end):
        return True
    return False


def has_self_intersections(points: Sequence[Point]) -> bool:
    count = len(points)
    for first_index in range(count):
        first_end = (first_index + 1) % count
        for second_index in range(first_index + 1, count):
            second_end = (second_index + 1) % count
            if first_end == second_index or second_end == first_index:
                continue
            if lines_intersect(
                points[first_index],
                points[first_end],
                points[second_index],
                points[second_end],
            ):
                return True
    return False


def is_valid_polygon(points: Any) -> bool:
    """Validate one finite, simple, counter-clockwise bounded polygon."""

    if (
        not isinstance(points, list)
        or len(points) < 3
        or len(points) > MAX_POLYGON_POINTS
    ):
        return False

    numeric_points: list[Point] = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            return False
        horizontal, vertical = point
        if (
            isinstance(horizontal, bool)
            or isinstance(vertical, bool)
            or not isinstance(horizontal, (int, float))
            or not isinstance(vertical, (int, float))
        ):
            return False
        try:
            numeric = (float(horizontal), float(vertical))
        except (OverflowError, TypeError, ValueError):
            return False
        if not math.isfinite(numeric[0]) or not math.isfinite(numeric[1]):
            return False
        numeric_points.append(numeric)

    count = len(numeric_points)
    if any(
        numeric_points[index] == numeric_points[(index + 1) % count]
        for index in range(count)
    ):
        return False
    area2 = signed_polygon_area2(numeric_points)
    if not math.isfinite(area2) or area2 <= 0.0:
        return False
    return not has_self_intersections(numeric_points)
