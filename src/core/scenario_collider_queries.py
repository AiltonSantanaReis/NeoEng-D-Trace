"""Deterministic minimum consumer for E05 overlap and trigger checks."""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.core.scenario_colliders import Collider, ColliderKind, Point


@dataclass(frozen=True)
class ColliderContact:
    first_id: str
    second_id: str
    overlaps: bool
    trigger: bool


def _world_points(collider: Collider) -> tuple[Point, ...]:
    angle = math.radians(collider.rotation_degrees)
    cosine, sine = math.cos(angle), math.sin(angle)

    def transform(point: Point) -> Point:
        x = point[0] * collider.scale[0]
        y = point[1] * collider.scale[1]
        return (
            collider.position[0] + x * cosine - y * sine,
            collider.position[1] + x * sine + y * cosine,
        )

    if collider.kind is ColliderKind.BOX:
        assert collider.size is not None
        half_x, half_y = collider.size[0] / 2.0, collider.size[1] / 2.0
        return tuple(
            transform(point)
            for point in (
                (-half_x, -half_y),
                (half_x, -half_y),
                (half_x, half_y),
                (-half_x, half_y),
            )
        )
    if collider.kind is ColliderKind.CIRCLE:
        assert collider.radius is not None
        radius = collider.radius * abs(collider.scale[0])
        return (
            (collider.position[0] - radius, collider.position[1] - radius),
            (collider.position[0] + radius, collider.position[1] - radius),
            (collider.position[0] + radius, collider.position[1] + radius),
            (collider.position[0] - radius, collider.position[1] + radius),
        )
    return tuple(transform(point) for point in collider.points)


def _bounds(collider: Collider) -> tuple[float, float, float, float]:
    values = _world_points(collider)
    xs, ys = zip(*values)
    return min(xs), min(ys), max(xs), max(ys)


def check_overlap(first: Collider, second: Collider) -> ColliderContact:
    """Run the bounded broad-phase consumer used by the E05 acceptance flow."""

    first_bounds = _bounds(first)
    second_bounds = _bounds(second)
    overlaps = not (
        first_bounds[2] < second_bounds[0]
        or second_bounds[2] < first_bounds[0]
        or first_bounds[3] < second_bounds[1]
        or second_bounds[3] < first_bounds[1]
    )
    category_match = bool(first.category & second.mask) and bool(
        second.category & first.mask
    )
    return ColliderContact(
        first.id,
        second.id,
        overlaps and category_match,
        first.is_trigger or second.is_trigger,
    )


__all__ = ["ColliderContact", "check_overlap"]
