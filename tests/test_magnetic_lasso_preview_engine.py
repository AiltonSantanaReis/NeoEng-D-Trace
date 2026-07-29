"""Headless contracts for the responsive magnetic-lasso preview path."""

from __future__ import annotations

from unittest.mock import patch

import cv2
import numpy as np

from src.tools import magnetic_lasso_engine as engine


def _circle_features(size: int = 320):
    image = np.zeros((size, size), dtype=np.uint8)
    cv2.circle(image, (size // 2, size // 2), size // 3, 255, 3)
    return engine.build_edge_features(image)


def test_preview_solver_is_separate_from_directional_commit_solver():
    features = _circle_features()
    settings = engine.MagneticLassoSettings()
    settings.max_search_pixels = 45_000
    settings.max_expansions = 100_000
    start = (160, 54)
    end = (266, 160)

    with patch.object(
        engine,
        "_astar_directional",
        side_effect=AssertionError("preview must not call the committed solver"),
    ):
        path = engine.live_wire_preview_path(features, start, end, settings)

    assert path
    assert path[0] == start
    assert path[-1] == end


def test_preview_solver_is_deterministic_and_follows_detected_edges():
    features = _circle_features()
    settings = engine.MagneticLassoSettings()
    settings.max_search_pixels = 45_000
    settings.max_expansions = 100_000
    start = (160, 54)
    end = (266, 160)

    first = engine.live_wire_preview_path(features, start, end, settings)
    second = engine.live_wire_preview_path(features, start, end, settings)

    assert first == second
    assert engine.path_edge_adherence(first, features.strength) >= 0.25


def test_committed_solver_still_uses_directional_algorithm():
    features = _circle_features(128)
    settings = engine.MagneticLassoSettings()
    sentinel = [(10, 10), (20, 20)]

    with patch.object(engine, "_astar_directional", return_value=sentinel) as solver:
        path = engine.live_wire_path(features, sentinel[0], sentinel[-1], settings)

    solver.assert_called_once()
    assert path[0] == sentinel[0]
    assert path[-1] == sentinel[-1]
