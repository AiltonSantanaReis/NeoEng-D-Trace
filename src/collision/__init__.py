"""Public API for 2D collision helpers in the single ``src`` tree."""

from src.physics.sat2d import overlap_intervals, project_polygon

from .sat2d import polygon_collision_sat

__all__ = [
    "project_polygon",
    "overlap_intervals",
    "polygon_collision_sat",
]
