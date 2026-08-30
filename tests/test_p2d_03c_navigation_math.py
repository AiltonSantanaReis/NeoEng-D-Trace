from __future__ import annotations

import math

import pytest

from src.core.scene_view_navigation import (
    NAVIGATION_MAX_ZOOM,
    NAVIGATION_MIN_ZOOM,
    anchored_navigation_center,
    clamp_navigation_zoom,
    fit_navigation_zoom,
    panned_navigation_center,
    wheel_navigation_zoom,
)


def test_navigation_zoom_is_bounded_and_finite() -> None:
    assert clamp_navigation_zoom(-10.0) == NAVIGATION_MIN_ZOOM
    assert clamp_navigation_zoom(100.0) == NAVIGATION_MAX_ZOOM
    with pytest.raises(ValueError):
        clamp_navigation_zoom(math.inf)
    with pytest.raises(ValueError):
        clamp_navigation_zoom(float("nan"))


def test_wheel_zoom_uses_standard_delta_and_preserves_limits() -> None:
    assert wheel_navigation_zoom(1.0, 120.0) == pytest.approx(1.15)
    assert wheel_navigation_zoom(1.0, -120.0) == pytest.approx(1.0 / 1.15)
    assert wheel_navigation_zoom(1.0, 60.0) == pytest.approx(math.sqrt(1.15))
    assert wheel_navigation_zoom(1.0, 0.0) == 1.0
    assert wheel_navigation_zoom(NAVIGATION_MAX_ZOOM, 120.0) == NAVIGATION_MAX_ZOOM
    assert wheel_navigation_zoom(NAVIGATION_MIN_ZOOM, -120.0) == NAVIGATION_MIN_ZOOM


def test_zoom_anchor_and_pan_are_deterministic() -> None:
    assert anchored_navigation_center((100.0, 80.0), (140.0, 100.0), (320.0, 240.0), 2.0) == (
        190.0,
        150.0,
    )
    assert panned_navigation_center((190.0, 150.0), (140.0, 100.0), (180.0, 60.0), 2.0) == (
        170.0,
        170.0,
    )


def test_fit_zoom_applies_ten_percent_margin_and_bounds() -> None:
    assert fit_navigation_zoom((800.0, 600.0), (400.0, 200.0)) == pytest.approx(800.0 / 480.0)
    assert fit_navigation_zoom((80.0, 60.0), (400.0, 200.0)) == pytest.approx(80.0 / 480.0)
    assert fit_navigation_zoom((8000.0, 6000.0), (1.0, 1.0)) == pytest.approx(8.0)
    with pytest.raises(ValueError):
        fit_navigation_zoom((800.0, 600.0), (400.0, 200.0), margin=0.5)
