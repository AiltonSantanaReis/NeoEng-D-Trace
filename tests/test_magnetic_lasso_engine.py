"""Headless contracts for the precise magnetic-lasso engine."""

from __future__ import annotations

import math
import time

import cv2
import numpy as np
import pytest

from src.tools.magnetic_lasso_engine import (
    MagneticLassoSettings,
    build_edge_features,
    image_array_to_gray_uint8,
    live_wire_path,
    path_edge_adherence,
    polygon_self_intersects,
    polygon_signed_area,
    sanitize_closed_polygon,
    simplify_closed_path,
    snap_to_edge,
)


def test_cv2_bgr_array_converts_to_gray_uint8():
    image = np.zeros((24, 31, 3), dtype=np.uint8)
    image[:, 16:, 2] = 255  # Red channel in OpenCV BGR order.

    gray = image_array_to_gray_uint8(image, channel_order="bgr")

    assert gray.shape == (24, 31)
    assert gray.dtype == np.uint8
    assert int(gray[:, 16:].mean()) > int(gray[:, :15].mean())


def test_cv2_bgra_and_single_channel_arrays_are_supported():
    bgra = np.zeros((18, 27, 4), dtype=np.uint8)
    bgra[:, 12:, :3] = 220
    bgra[:, :, 3] = 255
    single = np.full((18, 27, 1), 123, dtype=np.uint8)

    gray_bgra = image_array_to_gray_uint8(bgra, channel_order="bgr")
    gray_single = image_array_to_gray_uint8(single, channel_order="bgr")

    assert gray_bgra.shape == (18, 27)
    assert int(gray_bgra[:, 12:].mean()) > 200
    assert gray_single.shape == (18, 27)
    assert np.all(gray_single == 123)


def test_non_uint8_gray_array_is_normalized_without_nan_or_inf():
    image = np.array([[0.0, 4.0], [np.nan, np.inf]], dtype=np.float32)

    gray = image_array_to_gray_uint8(image, channel_order="bgr")

    assert gray.dtype == np.uint8
    assert gray.shape == (2, 2)
    assert np.isfinite(gray).all()


def test_presets_are_distinct_and_keep_mode():
    settings = MagneticLassoSettings(mode="legacy")
    settings.apply_preset("fast")
    fast_pixels = settings.max_search_pixels
    settings.apply_preset("precise")

    assert settings.mode == "legacy"
    assert settings.preset == "precise"
    assert settings.max_search_pixels > fast_pixels
    assert settings.snap_radius > 0


def test_edge_features_have_stable_shape_and_types():
    image = np.zeros((40, 55), dtype=np.uint8)
    image[:, 28:] = 200
    features = build_edge_features(image)

    assert features.strength.shape == image.shape
    assert features.grad_x.shape == image.shape
    assert features.grad_y.shape == image.shape
    assert features.strength.dtype == np.uint8
    assert features.grad_x.dtype == np.float32
    assert int(features.strength.max()) > 0


def test_anchor_snaps_to_nearby_edge():
    image = np.zeros((80, 80), dtype=np.uint8)
    image[:, 40:] = 255
    features = build_edge_features(image)

    snapped = snap_to_edge(features.strength, (34, 35), radius=10)

    assert abs(snapped[0] - 40) <= 2
    assert abs(snapped[1] - 35) <= 10


def test_precise_path_follows_quarter_circle_instead_of_cutting_inside():
    image = np.zeros((160, 160), dtype=np.uint8)
    cv2.circle(image, (80, 80), 50, 255, 2)
    features = build_edge_features(image)
    settings = MagneticLassoSettings()
    settings.apply_preset("balanced")

    start = snap_to_edge(features.strength, (30, 75), radius=12)
    end = snap_to_edge(features.strength, (80, 30), radius=12)
    path = live_wire_path(features, start, end, settings)

    assert path[0] == start
    assert path[-1] == end
    assert len(path) > 30
    radius_errors = [abs(math.hypot(x - 80, y - 80) - 50.0) for x, y in path]
    assert float(np.mean(radius_errors)) < 3.0
    assert path_edge_adherence(path, features.strength) > 0.55


def test_precise_path_handles_low_contrast_contour():
    image = np.full((120, 150), 100, dtype=np.uint8)
    cv2.rectangle(image, (25, 25), (125, 95), 128, 2)
    features = build_edge_features(image, sensitivity=1.4)
    settings = MagneticLassoSettings(sensitivity=1.4)

    start = snap_to_edge(features.strength, (22, 27), radius=8)
    end = snap_to_edge(features.strength, (123, 22), radius=8)
    path = live_wire_path(features, start, end, settings)

    assert path
    assert path[0] == start
    assert path[-1] == end
    assert path_edge_adherence(path, features.strength) > 0.35


def test_large_search_region_is_downscaled_but_keeps_endpoints():
    image = np.zeros((300, 420), dtype=np.uint8)
    cv2.line(image, (15, 150), (405, 150), 255, 2)
    features = build_edge_features(image)
    settings = MagneticLassoSettings(max_search_pixels=12_000, search_margin=90)

    start = snap_to_edge(features.strength, (15, 146), radius=8)
    end = snap_to_edge(features.strength, (405, 154), radius=8)
    started = time.perf_counter()
    path = live_wire_path(features, start, end, settings)
    elapsed = time.perf_counter() - started

    assert path[0] == start
    assert path[-1] == end
    assert elapsed < 3.0


def test_simplification_limits_vertices_and_preserves_polygon():
    angles = np.linspace(0.0, 2.0 * math.pi, 720, endpoint=False)
    points = [
        (100.0 + 60.0 * math.cos(angle), 100.0 + 60.0 * math.sin(angle))
        for angle in angles
    ]

    simplified = simplify_closed_path(points, epsilon=0.6, max_vertices=80)

    assert 8 <= len(simplified) <= 80
    assert not polygon_self_intersects(simplified)


@pytest.mark.parametrize(
    "points, expected",
    [
        ([(0, 0), (10, 0), (10, 10), (0, 10)], False),
        ([(0, 0), (10, 10), (0, 10), (10, 0)], True),
    ],
)
def test_self_intersection_detection(points, expected):
    assert polygon_self_intersects(points) is expected


def test_sanitize_removes_collinear_backtracking_spike():
    source = [(0, 0), (12, 0), (6, 0), (12, 10), (0, 10)]

    cleaned = sanitize_closed_polygon(source, epsilon=0.0)

    assert len(cleaned) >= 3
    assert not polygon_self_intersects(cleaned)
    assert polygon_signed_area(cleaned) > 0.0
    assert (12, 0) not in cleaned


def test_sanitize_rejects_collinear_zero_area_ring():
    cleaned = sanitize_closed_polygon(
        [(0, 0), (10, 0), (20, 0), (30, 0)],
        epsilon=0.0,
    )

    assert cleaned == []


def test_sanitize_normalizes_clockwise_ring_to_counter_clockwise():
    clockwise = [(0, 0), (0, 10), (10, 10), (10, 0)]

    cleaned = sanitize_closed_polygon(clockwise, epsilon=0.0)

    assert polygon_signed_area(cleaned) > 0.0
