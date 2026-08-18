"""Pure geometry tests for the isolated scenario preview stage."""

from __future__ import annotations

import pytest

from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scenario_preview import (
    ScenarioPreviewLayer,
    _point,
    _positive,
    build_overlay_geometry,
    project_layer_points,
)


def test_overlay_geometry_fits_16_by_9_and_safe_area_inside_frame():
    geometry = build_overlay_geometry((1280, 720), aspect_ratio=(16, 9))

    assert geometry.frame == (0.0, 0.0, 1280.0, 720.0)
    assert geometry.safe_area == pytest.approx((64.0, 36.0, 1152.0, 648.0))
    assert geometry.crop_regions[0] == (0.0, 0.0, 0.0, 720.0)
    assert geometry.aspect_ratio == (16, 9)


@pytest.mark.parametrize(
    ("viewport", "aspect", "expected_frame"),
    [
        ((1920, 1080), (21, 9), (0.0, 128.57142857142856, 1920.0, 822.8571428571429)),
        ((1280, 720), (9, 16), (437.5, 0.0, 405.0, 720.0)),
    ],
)
def test_overlay_geometry_handles_wide_and_vertical_frames(
    viewport, aspect, expected_frame
):
    geometry = build_overlay_geometry(viewport, aspect_ratio=aspect)

    assert geometry.frame == pytest.approx(expected_frame)
    assert all(value >= 0.0 for rect in geometry.crop_regions for value in rect)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"viewport_size": (0, 720)},
        {"viewport_size": (1280, 720), "aspect_ratio": (16, 0)},
        {"viewport_size": (1280, 720), "aspect_ratio": (16.0, 9)},
        {"viewport_size": (1280, 720), "safe_fraction": 0},
        {"viewport_size": (1280, 720), "safe_fraction": 1.1},
    ],
)
def test_overlay_geometry_rejects_invalid_operational_values(kwargs):
    with pytest.raises(ValueError):
        build_overlay_geometry(**kwargs)


def test_layer_projection_is_deterministic_and_visibility_is_respected():
    camera = OrthographicCamera((800, 600), position=(100, 50), zoom=2.0)
    layer = ScenarioPreviewLayer(
        id="far",
        object_ids=("object",),
        parallax=ParallaxLayer(depth=1.0, translation_strength=1.0),
    )
    points = [(100.0, 50.0), (110.0, 50.0)]

    projected = project_layer_points(camera, layer, points)
    assert projected == pytest.approx([(500.0, 350.0), (510.0, 350.0)])
    assert projected == project_layer_points(camera, layer, points)

    hidden = ScenarioPreviewLayer(id="hidden", visible=False)
    assert project_layer_points(camera, hidden, points) == []


def test_layer_rejects_duplicate_or_invalid_object_bindings():
    with pytest.raises(ValueError, match="unique"):
        ScenarioPreviewLayer(id="layer", object_ids=("object", "object"))
    with pytest.raises(ValueError, match="non-empty"):
        ScenarioPreviewLayer(id="layer", object_ids=("",))
    with pytest.raises(ValueError, match="non-empty"):
        ScenarioPreviewLayer(id="", object_ids=())
    with pytest.raises(ValueError, match="ParallaxLayer"):
        ScenarioPreviewLayer(id="layer", parallax=object())


def test_preview_geometry_helpers_reject_wrong_value_shapes():
    with pytest.raises(ValueError, match="positive"):
        _positive(True, "value")
    with pytest.raises(ValueError, match="exactly two"):
        _point((1.0,), "point")
    with pytest.raises(ValueError, match="visibility"):
        ScenarioPreviewLayer(id="layer", visible=1)
