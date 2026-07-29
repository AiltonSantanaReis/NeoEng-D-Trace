# tests/test_edge_utils.py
"""
Tests for multi-scale edge detection utilities.
"""

import numpy as np
import pytest
from src.tools.edge_utils import sobel_magnitude, log_response, multi_scale_edges, normalize_array


class TestEdgeUtils:
    """Test edge detection utilities."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create synthetic test image with a circle
        self.image_size = 100
        self.img = np.zeros((self.image_size, self.image_size), dtype=np.uint8)

        # Draw a circle in the center
        center = (50, 50)
        radius = 20
        y, x = np.ogrid[:self.image_size, :self.image_size]
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        self.img[dist_from_center <= radius] = 255

        # Create mask for inside and boundary regions
        self.inside_mask = dist_from_center < radius - 2  # Inside the circle
        self.boundary_mask = (dist_from_center >= radius - 2) & (dist_from_center <= radius + 2)  # Near boundary

    def test_normalize_array(self):
        """Test array normalization."""
        # Test normal case
        arr = np.array([0.0, 0.5, 1.0])
        normalized = normalize_array(arr)
        assert normalized.dtype == np.uint8
        assert normalized.min() == 0
        assert normalized.max() == 255

        # Test constant array
        const_arr = np.full(10, 5.0)
        normalized_const = normalize_array(const_arr)
        assert np.all(normalized_const == 0)

    def test_sobel_magnitude(self):
        """Test Sobel edge magnitude computation."""
        magnitude = sobel_magnitude(self.img)

        # Should return float array
        assert magnitude.dtype == np.float64

        # Edge response should be higher at boundaries
        inside_mean = np.mean(magnitude[self.inside_mask])
        boundary_mean = np.mean(magnitude[self.boundary_mask])

        assert boundary_mean > inside_mean, f"Boundary mean ({boundary_mean}) should be > inside mean ({inside_mean})"

    def test_log_response(self):
        """Test Laplacian of Gaussian response."""
        sigma = 1.0
        response = log_response(self.img, sigma)

        # Should return float array
        assert isinstance(response, np.ndarray)
        assert response.dtype in [np.float32, np.float64]

        # Response should be higher at edges
        inside_mean = np.mean(response[self.inside_mask])
        boundary_mean = np.mean(response[self.boundary_mask])

        assert boundary_mean > inside_mean, f"Boundary mean ({boundary_mean}) should be > inside mean ({inside_mean})"

    def test_multi_scale_edges_basic(self):
        """Test basic multi-scale edge detection."""
        response = multi_scale_edges(self.img)

        # Should return float array
        assert isinstance(response, np.ndarray)
        assert response.dtype in [np.float32, np.float64]

        # Response should be higher at boundaries
        inside_mean = np.mean(response[self.inside_mask])
        boundary_mean = np.mean(response[self.boundary_mask])

        assert boundary_mean > inside_mean, f"Boundary mean ({boundary_mean}) should be > inside mean ({inside_mean})"

        # Inside should have much lower response
        assert inside_mean < boundary_mean * 0.5, "Inside response should be significantly lower than boundary"

    def test_multi_scale_edges_custom_scales(self):
        """Test multi-scale edges with custom scales."""
        scales = [0.5, 1.0, 2.0]
        response = multi_scale_edges(self.img, scales=scales)

        # Should work with custom scales
        assert isinstance(response, np.ndarray)

        # Response should be higher at boundaries
        inside_mean = np.mean(response[self.inside_mask])
        boundary_mean = np.mean(response[self.boundary_mask])

        assert boundary_mean > inside_mean

    def test_multi_scale_edges_custom_weights(self):
        """Test multi-scale edges with custom weights."""
        scales = [1, 2, 4]
        weights = [0.5, 0.3, 0.2]
        response = multi_scale_edges(self.img, scales=scales, weights=weights)

        # Should work with custom weights
        assert isinstance(response, np.ndarray)

        # Response should be higher at boundaries
        inside_mean = np.mean(response[self.inside_mask])
        boundary_mean = np.mean(response[self.boundary_mask])

        assert boundary_mean > inside_mean

    def test_multi_scale_edges_weights_mismatch(self):
        """Test error when weights don't match scales."""
        scales = [1, 2, 4]
        weights = [0.5, 0.5]  # Wrong length

        with pytest.raises(ValueError, match="Weights list must match scales list length"):
            multi_scale_edges(self.img, scales=scales, weights=weights)

    def test_rgb_input_handling(self):
        """Test that functions handle RGB input correctly."""
        # Create RGB version of test image
        rgb_img = np.stack([self.img, self.img, self.img], axis=2)

        # Test sobel_magnitude
        magnitude = sobel_magnitude(rgb_img)
        assert magnitude.ndim == 2  # Should be grayscale

        # Test log_response
        response = log_response(rgb_img, sigma=1.0)
        assert response.ndim == 2

        # Test multi_scale_edges
        ms_response = multi_scale_edges(rgb_img)
        assert ms_response.ndim == 2