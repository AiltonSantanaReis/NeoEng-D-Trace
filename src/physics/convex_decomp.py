"""Compatibility imports for historical convex-decomposition paths."""

from src.core.convex_decomp import (
    convex_decompose_polygon,
    ear_clipping_triangulation,
    is_convex_polygon,
    is_ear,
    is_point_in_triangle,
    merge_triangles_to_convex,
    polygon_area,
    triangulate_to_convex,
    try_merge_polygons,
)

__all__ = [
    "convex_decompose_polygon",
    "ear_clipping_triangulation",
    "is_convex_polygon",
    "is_ear",
    "is_point_in_triangle",
    "merge_triangles_to_convex",
    "polygon_area",
    "triangulate_to_convex",
    "try_merge_polygons",
]
