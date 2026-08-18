"""Characterization and contract tests for the Stage 4 camera math."""

from __future__ import annotations

import math

import pytest

from src.core.parallax_camera import OrthographicCamera, ParallaxLayer


def test_neutral_camera_projects_world_origin_to_viewport_center() -> None:
    camera = OrthographicCamera((800, 600))

    assert camera.project((0, 0)) == (400.0, 300.0)
    assert camera.project((10, -20)) == (410.0, 280.0)


def test_foreground_receives_full_camera_translation_and_zoom() -> None:
    camera = OrthographicCamera((800, 600), position=(100, -50), zoom=2.0)
    foreground = ParallaxLayer(depth=0.0)

    assert camera.project((100, -50), foreground) == (400.0, 300.0)
    assert camera.effective_zoom(foreground) == 2.0


def test_far_plane_ignores_camera_motion_and_zoom_delta_at_full_strength() -> None:
    camera = OrthographicCamera((800, 600), position=(100, -50), zoom=2.0)
    far_plane = ParallaxLayer(depth=1.0)

    assert camera.project((100, -50), far_plane) == (500.0, 250.0)
    assert camera.effective_zoom(far_plane) == 1.0


def test_translation_and_zoom_strengths_are_independent() -> None:
    camera = OrthographicCamera((800, 600), position=(100, 0), zoom=3.0)
    layer = ParallaxLayer(depth=0.5, translation_strength=0.4, zoom_strength=0.8)

    assert layer.translation_factor == pytest.approx(0.8)
    assert layer.zoom_factor == pytest.approx(0.6)
    assert camera.effective_zoom(layer) == pytest.approx(2.2)
    assert camera.project((0, 0), layer) == pytest.approx((224.0, 300.0))


@pytest.mark.parametrize(
    "camera, layer, point",
    [
        (
            OrthographicCamera((1920, 1080), (12.5, -7.25), 0.75),
            ParallaxLayer(),
            (3.0, 8.0),
        ),
        (
            OrthographicCamera((640, 480), (-90.0, 45.0), 4.0),
            ParallaxLayer(0.8, 0.25, 0.5),
            (-2.0, 11.0),
        ),
    ],
)
def test_projection_round_trip_is_deterministic(
    camera: OrthographicCamera,
    layer: ParallaxLayer,
    point: tuple[float, float],
) -> None:
    projected = camera.project(point, layer)

    assert camera.unproject(projected, layer) == pytest.approx(point)
    assert camera.project(point, layer) == projected
    assert all(math.isfinite(value) for value in projected)


def test_project_points_preserves_order_and_does_not_mutate_input() -> None:
    points = [(0, 0), (10, 0), (10, 10)]
    camera = OrthographicCamera((100, 100), position=(5, 5), zoom=2.0)

    projected = camera.project_points(points)

    assert points == [(0, 0), (10, 0), (10, 10)]
    assert projected == [(40.0, 40.0), (60.0, 40.0), (60.0, 60.0)]


def test_camera_updates_are_immutable_and_preserve_existing_contract() -> None:
    original = OrthographicCamera((800, 600), position=(10, 20), zoom=1.5)

    moved = original.with_position((30, 40))
    zoomed = original.with_zoom(2.0)

    assert original.position == (10.0, 20.0)
    assert original.zoom == 1.5
    assert moved.viewport_size == original.viewport_size
    assert moved.position == (30.0, 40.0)
    assert moved.zoom == original.zoom
    assert zoomed.position == original.position
    assert zoomed.zoom == 2.0


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ParallaxLayer(depth=-0.1),
        lambda: ParallaxLayer(depth=1.1),
        lambda: ParallaxLayer(translation_strength=float("nan")),
        lambda: OrthographicCamera((0, 600)),
        lambda: OrthographicCamera((800, 600), zoom=0),
        lambda: OrthographicCamera((800, 600), position=(float("inf"), 0)),
    ],
)
def test_invalid_camera_parameters_are_rejected(factory) -> None:
    with pytest.raises(ValueError):
        factory()


@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf")])
def test_non_finite_or_boolean_depth_is_rejected(value) -> None:
    with pytest.raises(ValueError):
        ParallaxLayer(depth=value)


def test_camera_math_has_no_scene_or_exporter_dependency() -> None:
    module_path = "src.core.parallax_camera"
    camera = OrthographicCamera((320, 240))
    assert camera.__class__.__module__ == module_path
    assert ParallaxLayer.__module__ == module_path


@pytest.mark.parametrize("point", ["12", (1, 2, 3)])
def test_projection_points_require_exactly_two_coordinates(point) -> None:
    with pytest.raises(ValueError):
        OrthographicCamera((320, 240)).project(point)
