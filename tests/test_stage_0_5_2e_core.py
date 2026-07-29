import math

import numpy as np
import pytest

from src.physics.convex_decomp import (
    convex_decompose_polygon,
    is_convex_polygon,
    polygon_area,
    try_merge_polygons,
)
from src.tools.mask_utils import curvature_adaptive_simplify


def test_concave_polygon_is_not_reported_as_convex():
    polygon = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (1.0, 2.0), (1.0, 1.0), (0.0, 1.0)]
    assert is_convex_polygon(polygon) is False


def test_convex_polygon_is_recognized_in_either_orientation():
    square = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
    assert is_convex_polygon(square) is True
    assert is_convex_polygon(list(reversed(square))) is True


def test_triangle_merge_rejects_concave_result():
    first = [(0.0, 1.0), (0.0, 0.0), (3.0, 0.0)]
    second = [(3.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    merged = try_merge_polygons(first, second)
    if merged is not None:
        assert is_convex_polygon(merged)


def test_valid_l_shape_decomposition_preserves_area_and_convexity():
    polygon = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (1.0, 2.0), (1.0, 1.0), (0.0, 1.0)]
    pieces = convex_decompose_polygon(polygon)
    assert len(pieces) >= 2
    assert all(is_convex_polygon(piece) for piece in pieces)
    assert math.isclose(
        sum(polygon_area(piece) for piece in pieces),
        polygon_area(polygon),
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def _circle_contour(point_count=32):
    points = []
    for index in range(point_count):
        angle = 2 * np.pi * index / point_count
        points.append((int(50 + 30 * np.cos(angle)), int(50 + 30 * np.sin(angle))))
    return np.asarray(points).reshape(-1, 1, 2)


def test_curvature_min_points_is_opt_in_and_preserves_requested_floor():
    result = curvature_adaptive_simplify(
        _circle_contour(), base_eps=5.0, curvature_factor=1.0, min_points=8
    )
    assert 8 <= len(result) < 32


def test_curvature_default_remains_backward_compatible():
    result = curvature_adaptive_simplify(
        _circle_contour(), base_eps=5.0, curvature_factor=1.0
    )
    assert len(result) >= 3


def test_curvature_rejects_invalid_min_points_type():
    with pytest.raises(ValueError, match="min_points"):
        curvature_adaptive_simplify(_circle_contour(), min_points=3.5)


def test_decomposition_never_returns_zero_area_pieces():
    overlapping_fixture = [
        (0.0, 0.0),
        (3.0, 0.0),
        (3.0, 2.0),
        (1.0, 2.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (0.0, 2.0),
    ]
    pieces = convex_decompose_polygon(overlapping_fixture)
    assert all(polygon_area(piece) > 1e-10 for piece in pieces)
    assert all(is_convex_polygon(piece) for piece in pieces)
