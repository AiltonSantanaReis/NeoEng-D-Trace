"""Pure runtime geometry for the optional scenario preview.

This module intentionally contains no Qt, scene mutation, persistence or
exporter code.  It only validates preview layer bindings and computes the
screen-space rectangles used by the canvas overlays.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from .parallax_camera import OrthographicCamera, ParallaxLayer, Point2

Rect = tuple[float, float, float, float]


def _positive(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a positive finite number")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{field} must be a positive finite number")
    return result


def _point(value: Sequence[float], field: str) -> Point2:
    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError(f"{field} must contain exactly two coordinates")
    return (float(value[0]), float(value[1]))


@dataclass(frozen=True)
class ScenarioPreviewLayer:
    """Runtime-only mapping between scene objects and parallax parameters."""

    id: str
    object_ids: tuple[str, ...] = ()
    parallax: ParallaxLayer = ParallaxLayer()
    visible: bool = True

    def __post_init__(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError("preview layer IDs must be non-empty strings")
        if any(not item or not isinstance(item, str) for item in self.object_ids):
            raise ValueError("preview object IDs must be non-empty strings")
        if len(self.object_ids) != len(set(self.object_ids)):
            raise ValueError("preview object IDs must be unique within a layer")
        if not isinstance(self.parallax, ParallaxLayer):
            raise ValueError("preview layer parallax must be a ParallaxLayer")
        if not isinstance(self.visible, bool):
            raise ValueError("preview layer visibility must be boolean")


@dataclass(frozen=True)
class ScenarioOverlayGeometry:
    """Aspect-frame, safe-area and crop-mask rectangles in widget pixels."""

    viewport_size: Point2
    frame: Rect
    safe_area: Rect
    crop_regions: tuple[Rect, Rect, Rect, Rect]
    aspect_ratio: tuple[int, int]
    safe_fraction: float


def _rect_for_aspect(viewport: Point2, aspect_ratio: tuple[int, int]) -> Rect:
    width, height = viewport
    ratio_width, ratio_height = aspect_ratio
    target_ratio = ratio_width / ratio_height
    viewport_ratio = width / height
    if viewport_ratio >= target_ratio:
        frame_height = height
        frame_width = frame_height * target_ratio
        x = (width - frame_width) / 2.0
        return (x, 0.0, frame_width, frame_height)
    frame_width = width
    frame_height = frame_width / target_ratio
    y = (height - frame_height) / 2.0
    return (0.0, y, frame_width, frame_height)


def build_overlay_geometry(
    viewport_size: Sequence[float],
    *,
    aspect_ratio: tuple[int, int] = (16, 9),
    safe_fraction: float = 0.9,
) -> ScenarioOverlayGeometry:
    """Build deterministic frame, safe-area and outside-crop rectangles."""

    viewport = _point(viewport_size, "viewport_size")
    width = _positive(viewport[0], "viewport_size.width")
    height = _positive(viewport[1], "viewport_size.height")
    if (
        not isinstance(aspect_ratio, tuple)
        or len(aspect_ratio) != 2
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in aspect_ratio
        )
    ):
        raise ValueError("aspect_ratio must contain two positive integers")
    if (
        isinstance(safe_fraction, bool)
        or not isinstance(safe_fraction, (int, float))
        or not math.isfinite(float(safe_fraction))
        or not 0.0 < float(safe_fraction) <= 1.0
    ):
        raise ValueError("safe_fraction must be greater than 0 and at most 1")

    frame = _rect_for_aspect((width, height), aspect_ratio)
    x, y, frame_width, frame_height = frame
    margin_x = frame_width * (1.0 - float(safe_fraction)) / 2.0
    margin_y = frame_height * (1.0 - float(safe_fraction)) / 2.0
    safe_area = (
        x + margin_x,
        y + margin_y,
        frame_width - 2.0 * margin_x,
        frame_height - 2.0 * margin_y,
    )
    right = x + frame_width
    bottom = y + frame_height
    crop_regions = (
        (0.0, 0.0, x, height),
        (right, 0.0, width - right, height),
        (x, 0.0, frame_width, y),
        (x, bottom, frame_width, height - bottom),
    )
    return ScenarioOverlayGeometry(
        viewport_size=(width, height),
        frame=frame,
        safe_area=safe_area,
        crop_regions=crop_regions,
        aspect_ratio=aspect_ratio,
        safe_fraction=float(safe_fraction),
    )


def project_layer_points(
    camera: OrthographicCamera,
    layer: ScenarioPreviewLayer,
    points: Iterable[Sequence[float]],
) -> list[Point2]:
    """Project points using a layer's parallax without mutating the inputs."""

    if not layer.visible:
        return []
    return camera.project_points(points, layer.parallax)
