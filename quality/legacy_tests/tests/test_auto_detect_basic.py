# tests/test_auto_detect_basic.py
"""
Unit tests for basic auto-detection mode.
"""

import pytest
import numpy as np
import cv2
from src.tools.auto_detect import detect_polygons


class TestAutoDetectBasic:
    """Test basic polygon detection functionality."""

    def test_detect_square(self):
        """Test detection of a simple square."""
        # Create a white square on black background
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (80, 80), 255, -1)  # Filled white square

        result = detect_polygons(image, mode='basic', min_area=50)
        polygons = result['polygons']
        assert len(polygons) == 1
        poly = polygons[0]
        assert poly['area'] > 3000  # Approximate area of 60x60 square
        assert len(poly['polygon']) <= 20  # Should be simplified to few vertices
        assert poly['bbox'][2] >= 50 and poly['bbox'][3] >= 50  # Width and height reasonable

    def test_detect_circle(self):
        """Test detection of a circle."""
        # Create a white circle on black background
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 30, 255, -1)  # Filled white circle

        result = detect_polygons(image, mode='basic', min_area=50)
        polygons = result['polygons']
        assert len(polygons) == 1
        poly = polygons[0]
        assert poly['area'] > 2500  # Approximate area of circle with radius 30
        assert len(poly['polygon']) <= 20  # Should be simplified
        assert poly['bbox'][2] >= 50 and poly['bbox'][3] >= 50  # Bounding box reasonable

    def test_detect_two_touching_rectangles(self):
        """Test detection of two touching rectangles."""
        # Create two touching rectangles
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(image, (10, 30), (45, 70), 255, -1)  # Left rectangle
        cv2.rectangle(image, (45, 30), (80, 70), 255, -1)  # Right rectangle (touching)

        result = detect_polygons(image, mode='basic', min_area=50)
        polygons = result['polygons']
        # Should detect 1 polygon (touching rectangles form one connected shape)
        assert len(polygons) == 1
        poly = polygons[0]
        assert poly['area'] > 2500  # Combined area of both rectangles
        assert len(poly['polygon']) <= 20  # Should be simplified
        assert poly['bbox'][2] >= 60 and poly['bbox'][3] >= 30  # Combined bounding box

    def test_filter_small_areas(self):
        """Test that small areas are filtered out."""
        # Create a large square and a small dot
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (80, 80), 255, -1)  # Large square
        cv2.circle(image, (10, 10), 2, 255, -1)  # Small dot

        # With high min_area, only large square should be detected
        result = detect_polygons(image, mode='basic', min_area=1000)
        polygons = result['polygons']
        assert len(polygons) == 1
        poly = polygons[0]
        assert poly['area'] > 3000

    def test_downscale_parameter(self):
        """Test downscale parameter works."""
        image = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(image, (40, 40), (160, 160), 255, -1)  # Large square

        # Detect with downscale
        result_scaled = detect_polygons(image, mode='basic', downscale=0.5, min_area=50)
        polygons_scaled = result_scaled['polygons']
        result_full = detect_polygons(image, mode='basic', min_area=50)
        polygons_full = result_full['polygons']

        # Should detect the same number of polygons
        assert len(polygons_scaled) == len(polygons_full) == 1

        # Areas should be similar (allowing for scaling approximation)
        area_scaled = polygons_scaled[0]['area']
        area_full = polygons_full[0]['area']
        assert abs(area_scaled - area_full) / area_full < 0.1  # Within 10%

    def test_rdp_simplification(self):
        """Test that RDP simplification reduces vertex count."""
        # Create a shape with many vertices (approximating a circle with rectangle)
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 40, 255, 2)  # Thick circle outline

        polygons = detect_polygons(image, mode='basic', min_area=50, rdp_epsilon=1.0)

        assert len(polygons) >= 1
        poly = polygons[0]
        assert len(poly['polygon']) <= 50  # Should be simplified from potentially hundreds of points

    def test_empty_image(self):
        """Test detection on empty image."""
        image = np.zeros((100, 100), dtype=np.uint8)

        polygons = detect_polygons(image, mode='basic')

        assert len(polygons) == 0

    def test_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        image = np.zeros((50, 50), dtype=np.uint8)

        with pytest.raises(ValueError, match="Unknown mode"):
            detect_polygons(image, mode='invalid')