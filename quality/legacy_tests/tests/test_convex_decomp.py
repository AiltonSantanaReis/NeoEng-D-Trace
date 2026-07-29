"""
Tests for Ear Clipping Triangulation and Convex Decomposition.
"""

import pytest
import math
from src.physics.convex_decomp import (
    polygon_area,
    is_point_in_triangle,
    is_ear,
    ear_clipping_triangulation,
    convex_decompose_polygon
)


class TestConvexDecomp:
    """Test cases for convex decomposition algorithms."""

    def test_polygon_area_triangle(self):
        """Test area calculation for a triangle."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        area = polygon_area(triangle)
        expected = 2.0  # Base 2, height 2, area = 2
        assert abs(area - expected) < 1e-10

    def test_polygon_area_rectangle(self):
        """Test area calculation for a rectangle."""
        rect = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        area = polygon_area(rect)
        expected = 2.0  # Width 2, height 1
        assert abs(area - expected) < 1e-10

    def test_polygon_area_empty(self):
        """Test area calculation for empty polygon."""
        area = polygon_area([])
        assert area == 0.0

    def test_polygon_area_single_point(self):
        """Test area calculation for single point."""
        area = polygon_area([(0.0, 0.0)])
        assert area == 0.0

    def test_point_in_triangle_inside(self):
        """Test point inside triangle."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        point = (1.0, 0.5)
        assert is_point_in_triangle(point, triangle) is True

    def test_point_in_triangle_outside(self):
        """Test point outside triangle."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        point = (3.0, 1.0)
        assert is_point_in_triangle(point, triangle) is False

    def test_point_in_triangle_vertex(self):
        """Test point on triangle vertex."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        point = (0.0, 0.0)
        assert is_point_in_triangle(point, triangle) is True

    def test_point_in_triangle_edge(self):
        """Test point on triangle edge."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        point = (1.0, 0.0)  # Midpoint of base
        assert is_point_in_triangle(point, triangle) is True

    def test_is_ear_convex_vertex(self):
        """Test ear detection for a convex vertex."""
        # Triangle - all vertices should be ears
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        assert is_ear(triangle, 0) is True
        assert is_ear(triangle, 1) is True
        assert is_ear(triangle, 2) is True

    def test_is_ear_concave_vertex(self):
        """Test ear detection for a vertex that is not an ear."""
        # Polygon with a dent where vertex 3's triangle contains another vertex
        polygon = [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (1.5, 1.5), (0.0, 3.0)]
        # Vertex at index 0 should not be an ear because vertex 3 is inside its triangle
        assert is_ear(polygon, 0) is False

    def test_ear_clipping_triangle(self):
        """Test triangulation of a triangle."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        triangles = ear_clipping_triangulation(triangle)

        assert len(triangles) == 1
        assert triangles[0] == triangle

    def test_ear_clipping_quadrilateral(self):
        """Test triangulation of a quadrilateral."""
        quad = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        triangles = ear_clipping_triangulation(quad)

        assert len(triangles) == 2

        # Check that all triangles are valid
        for triangle in triangles:
            assert len(triangle) == 3

        # Check area preservation
        original_area = polygon_area(quad)
        triangulated_area = sum(polygon_area(t) for t in triangles)
        assert abs(original_area - triangulated_area) < 1e-10

    def test_ear_clipping_concave_l_shape(self):
        """Test triangulation of concave L-shaped polygon."""
        # L-shaped polygon: starts at (0,0), goes right to (3,0), up to (3,2), left to (1,2), down to (1,1), left to (0,1), up to (0,2)
        l_shape = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (1.0, 2.0), (1.0, 1.0), (0.0, 1.0), (0.0, 2.0)]

        triangles = ear_clipping_triangulation(l_shape)

        assert len(triangles) == 5  # L-shape should triangulate into 5 triangles

        # Check area preservation
        original_area = polygon_area(l_shape)
        triangulated_area = sum(polygon_area(t) for t in triangles)
        assert abs(original_area - triangulated_area) < 1e-10

    def test_convex_decompose_triangle(self):
        """Test convex decomposition of a triangle."""
        triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
        convex_polygons = convex_decompose_polygon(triangle)

        assert len(convex_polygons) == 1
        assert convex_polygons[0] == triangle

    def test_convex_decompose_l_shape(self):
        """Test convex decomposition of L-shaped polygon."""
        l_shape = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (1.0, 2.0), (1.0, 1.0), (0.0, 1.0), (0.0, 2.0)]

        convex_polygons = convex_decompose_polygon(l_shape)

        # Should decompose into multiple convex polygons (currently returns triangles)
        assert len(convex_polygons) == 5

        # Check area preservation
        original_area = polygon_area(l_shape)
        decomposed_area = sum(polygon_area(p) for p in convex_polygons)
        assert abs(original_area - decomposed_area) < 1e-10

    def test_convex_decompose_empty_polygon(self):
        """Test convex decomposition of empty polygon."""
        convex_polygons = convex_decompose_polygon([])
        assert convex_polygons == []

    def test_convex_decompose_single_point(self):
        """Test convex decomposition of single point."""
        convex_polygons = convex_decompose_polygon([(0.0, 0.0)])
        assert convex_polygons == []

    def test_convex_decompose_two_points(self):
        """Test convex decomposition of two points."""
        convex_polygons = convex_decompose_polygon([(0.0, 0.0), (1.0, 1.0)])
        assert convex_polygons == []

    def test_area_preservation_complex_polygon(self):
        """Test area preservation for a complex polygon."""
        # Star-like polygon
        star = [
            (0.0, 2.0), (0.5, 0.5), (2.0, 0.0), (0.5, -0.5),
            (0.0, -2.0), (-0.5, -0.5), (-2.0, 0.0), (-0.5, 0.5)
        ]

        triangles = ear_clipping_triangulation(star)

        # Star should triangulate into 6 triangles
        assert len(triangles) == 6

        # Check area preservation
        original_area = polygon_area(star)
        triangulated_area = sum(polygon_area(t) for t in triangles)
        assert abs(original_area - triangulated_area) < 1e-6  # Slightly looser tolerance for complex shapes