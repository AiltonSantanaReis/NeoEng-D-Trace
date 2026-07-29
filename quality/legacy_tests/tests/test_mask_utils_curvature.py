# tests/test_mask_utils_curvature.py
"""
Tests for curvature-adaptive simplification in mask_utils.
"""

import numpy as np
import pytest
from src.tools.mask_utils import curvature_adaptive_simplify


class TestCurvatureAdaptiveSimplify:
    """Test curvature-adaptive polygon simplification."""

    def test_straight_line_preservation(self):
        """Test that straight lines are simplified appropriately."""
        # Create a straight line with some noise
        points = [(0, 0), (10, 0), (20, 0), (30, 0), (40, 0)]
        result = curvature_adaptive_simplify(np.array(points), base_eps=1.0)

        # Should simplify to fewer points
        assert len(result) <= len(points)
        assert len(result) >= 2  # At least endpoints

    def test_high_curvature_preservation(self):
        """Test that high-curvature points are preserved."""
        # Create a contour with straight segments and a sharp corner
        points = [
            (0, 0), (10, 0), (20, 0),  # Straight segment
            (30, 0), (30, 10), (30, 20),  # Another straight segment (corner)
            (20, 20), (10, 20), (0, 20),  # Straight segment
            (0, 10), (0, 0)  # Back to start
        ]

        # Convert to numpy array in OpenCV contour format
        contour = np.array(points).reshape(-1, 1, 2)

        result = curvature_adaptive_simplify(contour, base_eps=2.0, curvature_factor=2.0)

        # Should preserve the corner points
        result_points = set(result)

        # The corner point (30, 10) should be preserved due to high curvature
        assert (30, 10) in result_points or (30, 20) in result_points

        # Should have simplified some straight segments
        assert len(result) < len(points)

    def test_circle_contour(self):
        """Test with a circular contour (uniform high curvature)."""
        # Create a circle contour
        center = (50, 50)
        radius = 30
        num_points = 32

        points = []
        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            points.append((int(x), int(y)))

        contour = np.array(points).reshape(-1, 1, 2)

        result = curvature_adaptive_simplify(contour, base_eps=5.0, curvature_factor=1.0)

        # Circle should be simplified but maintain some curvature points
        assert len(result) < len(points)
        assert len(result) >= 8  # Should keep reasonable number of points

    def test_minimal_contour(self):
        """Test with minimal contours."""
        # Triangle
        points = [(0, 0), (10, 0), (5, 10)]
        contour = np.array(points).reshape(-1, 1, 2)

        result = curvature_adaptive_simplify(contour, base_eps=1.0)
        assert len(result) == len(points)  # Should not simplify triangle

    def test_empty_and_small_contours(self):
        """Test edge cases."""
        # Empty contour
        result = curvature_adaptive_simplify(np.array([]))
        assert result == []

        # Single point
        result = curvature_adaptive_simplify(np.array([(0, 0)]))
        assert result == [(0, 0)]

        # Two points
        points = [(0, 0), (10, 10)]
        result = curvature_adaptive_simplify(np.array(points))
        assert result == points

    def test_parameter_effects(self):
        """Test that parameters affect simplification."""
        # Create a complex contour
        points = []
        for i in range(50):
            x = 50 + 40 * np.cos(2 * np.pi * i / 50)
            y = 50 + 40 * np.sin(2 * np.pi * i / 50)
            # Add some straight segments
            if i > 10 and i < 20:
                x = 50 + (i - 15) * 2
                y = 50
            points.append((int(x), int(y)))

        contour = np.array(points).reshape(-1, 1, 2)

        # Low curvature factor should simplify more
        result_low = curvature_adaptive_simplify(contour, base_eps=3.0, curvature_factor=0.5)
        result_high = curvature_adaptive_simplify(contour, base_eps=3.0, curvature_factor=2.0)

        # High curvature factor should preserve more points
        assert len(result_high) >= len(result_low)

    def test_curvature_computation(self):
        """Test that curvature is computed correctly."""
        from src.tools.mask_utils import _compute_discrete_curvature

        # Straight line - low curvature
        straight_points = [(0, 0), (10, 0), (20, 0), (30, 0)]
        curvatures = _compute_discrete_curvature(straight_points)

        # Middle points should have low curvature
        assert all(c < 0.1 for c in curvatures[1:-1])

        # Sharp corner - high curvature
        corner_points = [(0, 0), (10, 0), (10, 10)]
        curvatures = _compute_discrete_curvature(corner_points)

        # Corner point should have high curvature
        assert curvatures[1] > 1.0  # Close to π/2 or more