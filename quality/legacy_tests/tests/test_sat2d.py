"""
Tests for SAT (Separating Axis Theorem) 2D collision detection.
"""

import pytest
from src.physics.sat2d import project, polygon_edges, sat_polygon_vs_polygon


class TestSAT2D:
    """Test cases for SAT collision detection."""

    def test_project_empty_polygon(self):
        """Test projecting an empty polygon."""
        result = project([], (1.0, 0.0))
        assert result == (0.0, 0.0)

    def test_project_single_vertex(self):
        """Test projecting a single vertex."""
        polygon = [(1.0, 2.0)]
        result = project(polygon, (1.0, 0.0))
        assert result == (1.0, 1.0)

    def test_project_rectangle_on_axis(self):
        """Test projecting a rectangle onto x-axis."""
        # Rectangle vertices
        rect = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        # Project onto x-axis (1, 0)
        min_proj, max_proj = project(rect, (1.0, 0.0))
        assert min_proj == 0.0
        assert max_proj == 2.0

    def test_project_rectangle_on_y_axis(self):
        """Test projecting a rectangle onto y-axis."""
        # Rectangle vertices
        rect = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        # Project onto y-axis (0, 1)
        min_proj, max_proj = project(rect, (0.0, 1.0))
        assert min_proj == 0.0
        assert max_proj == 1.0

    def test_polygon_edges_rectangle(self):
        """Test getting edges from a rectangle."""
        rect = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        edges = polygon_edges(rect)

        expected_edges = [
            (2.0, 0.0),   # (0,0) -> (2,0)
            (0.0, 1.0),   # (2,0) -> (2,1)
            (-2.0, 0.0),  # (2,1) -> (0,1)
            (0.0, -1.0)   # (0,1) -> (0,0)
        ]

        assert len(edges) == 4
        for actual, expected in zip(edges, expected_edges):
            assert abs(actual[0] - expected[0]) < 1e-6
            assert abs(actual[1] - expected[1]) < 1e-6

    def test_polygon_edges_triangle(self):
        """Test getting edges from a triangle."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        edges = polygon_edges(triangle)

        expected_edges = [
            (2.0, 0.0),   # (0,0) -> (2,0)
            (-1.0, 2.0),  # (2,0) -> (1,2)
            (-1.0, -2.0)  # (1,2) -> (0,0)
        ]

        assert len(edges) == 3
        for actual, expected in zip(edges, expected_edges):
            assert abs(actual[0] - expected[0]) < 1e-6
            assert abs(actual[1] - expected[1]) < 1e-6

    def test_sat_rectangle_vs_rectangle_no_collision(self):
        """Test rectangle vs rectangle with no collision."""
        rect1 = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        rect2 = [(3.0, 0.0), (5.0, 0.0), (5.0, 1.0), (3.0, 1.0)]

        collision, mtv = sat_polygon_vs_polygon(rect1, rect2)
        assert collision is False
        assert mtv is None

    def test_sat_rectangle_vs_rectangle_collision(self):
        """Test rectangle vs rectangle with collision."""
        rect1 = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        rect2 = [(1.0, 0.5), (3.0, 0.5), (3.0, 1.5), (1.0, 1.5)]

        collision, mtv = sat_polygon_vs_polygon(rect1, rect2)
        assert collision is True
        assert mtv is not None
        assert len(mtv) == 2
        # MTV should be non-zero vector
        assert abs(mtv[0]) + abs(mtv[1]) > 0

    def test_sat_triangle_vs_rectangle_no_collision(self):
        """Test triangle vs rectangle with no collision."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        rect = [(3.0, 0.0), (5.0, 0.0), (5.0, 1.0), (3.0, 1.0)]

        collision, mtv = sat_polygon_vs_polygon(triangle, rect)
        assert collision is False
        assert mtv is None

    def test_sat_triangle_vs_rectangle_collision(self):
        """Test triangle vs rectangle with collision."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        rect = [(1.0, 1.0), (3.0, 1.0), (3.0, 2.0), (1.0, 2.0)]

        collision, mtv = sat_polygon_vs_polygon(triangle, rect)
        assert collision is True
        assert mtv is not None
        assert len(mtv) == 2
        # MTV should be non-zero vector
        assert abs(mtv[0]) + abs(mtv[1]) > 0

    def test_sat_empty_polygons(self):
        """Test SAT with empty polygons."""
        collision, mtv = sat_polygon_vs_polygon([], [])
        assert collision is False
        assert mtv is None

    def test_sat_single_empty_polygon(self):
        """Test SAT with one empty polygon."""
        rect = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        collision, mtv = sat_polygon_vs_polygon(rect, [])
        assert collision is False
        assert mtv is None

    def test_sat_identical_rectangles(self):
        """Test SAT with identical overlapping rectangles."""
        rect1 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        rect2 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

        collision, mtv = sat_polygon_vs_polygon(rect1, rect2)
        assert collision is True
        assert mtv is not None
        # For identical shapes, MTV should be non-zero
        assert abs(mtv[0]) + abs(mtv[1]) > 0
