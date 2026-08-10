"""Public API for validated static 2D polygon collisions."""

from .manager import CollisionObject, CollisionResult, StaticCollisionManager
from .sat2d import (
    overlap_intervals,
    polygon_collision_sat,
    polygons_overlap,
    project_polygon,
)

__all__ = [
    "CollisionObject",
    "CollisionResult",
    "StaticCollisionManager",
    "overlap_intervals",
    "polygon_collision_sat",
    "polygons_overlap",
    "project_polygon",
]
