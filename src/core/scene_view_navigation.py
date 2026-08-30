"""Deterministic transient navigation math for the professional scene viewport."""

from __future__ import annotations

import math
from typing import Sequence

NAVIGATION_MIN_ZOOM = 0.10
NAVIGATION_MAX_ZOOM = 8.00
NAVIGATION_WHEEL_FACTOR = 1.15
NAVIGATION_WHEEL_DELTA = 120.0
NAVIGATION_FIT_MARGIN = 0.10


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def clamp_navigation_zoom(value: object) -> float:
    """Clamp a transient viewport zoom to the accepted navigation interval."""

    result = _finite(value, "zoom")
    return max(NAVIGATION_MIN_ZOOM, min(NAVIGATION_MAX_ZOOM, result))


def wheel_navigation_zoom(current: object, angle_delta_y: object) -> float:
    """Return the zoom after a standard Qt wheel delta, without side effects."""

    zoom = clamp_navigation_zoom(current)
    delta = _finite(angle_delta_y, "angle_delta_y")
    if delta == 0.0:
        return zoom
    steps = delta / NAVIGATION_WHEEL_DELTA
    return clamp_navigation_zoom(zoom * (NAVIGATION_WHEEL_FACTOR**steps))


def anchored_navigation_center(
    anchor_scene: Sequence[float],
    pointer_view: Sequence[float],
    viewport_center: Sequence[float],
    zoom: object,
) -> tuple[float, float]:
    """Calculate the scene center that keeps a scene point under the cursor."""

    if len(anchor_scene) != 2 or len(pointer_view) != 2 or len(viewport_center) != 2:
        raise ValueError("navigation points must contain two coordinates")
    anchor_x = _finite(anchor_scene[0], "anchor_scene.x")
    anchor_y = _finite(anchor_scene[1], "anchor_scene.y")
    pointer_x = _finite(pointer_view[0], "pointer_view.x")
    pointer_y = _finite(pointer_view[1], "pointer_view.y")
    center_x = _finite(viewport_center[0], "viewport_center.x")
    center_y = _finite(viewport_center[1], "viewport_center.y")
    scale = clamp_navigation_zoom(zoom)
    return (
        anchor_x - (pointer_x - center_x) / scale,
        anchor_y - (pointer_y - center_y) / scale,
    )


def panned_navigation_center(
    start_center: Sequence[float],
    start_pointer_view: Sequence[float],
    current_pointer_view: Sequence[float],
    zoom: object,
) -> tuple[float, float]:
    """Return the scene center after a middle-button presentation pan."""

    if len(start_center) != 2 or len(start_pointer_view) != 2 or len(current_pointer_view) != 2:
        raise ValueError("navigation points must contain two coordinates")
    center_x = _finite(start_center[0], "start_center.x")
    center_y = _finite(start_center[1], "start_center.y")
    start_x = _finite(start_pointer_view[0], "start_pointer_view.x")
    start_y = _finite(start_pointer_view[1], "start_pointer_view.y")
    current_x = _finite(current_pointer_view[0], "current_pointer_view.x")
    current_y = _finite(current_pointer_view[1], "current_pointer_view.y")
    scale = clamp_navigation_zoom(zoom)
    return (
        center_x - (current_x - start_x) / scale,
        center_y - (current_y - start_y) / scale,
    )


def fit_navigation_zoom(
    viewport_size: Sequence[float],
    content_size: Sequence[float],
    *,
    margin: object = NAVIGATION_FIT_MARGIN,
) -> float:
    """Return a bounded fit zoom with a margin on each side."""

    if len(viewport_size) != 2 or len(content_size) != 2:
        raise ValueError("fit sizes must contain two coordinates")
    viewport_width = _finite(viewport_size[0], "viewport.width")
    viewport_height = _finite(viewport_size[1], "viewport.height")
    content_width = _finite(content_size[0], "content.width")
    content_height = _finite(content_size[1], "content.height")
    fit_margin = _finite(margin, "margin")
    if viewport_width <= 0.0 or viewport_height <= 0.0:
        raise ValueError("viewport dimensions must be positive")
    if content_width < 0.0 or content_height < 0.0:
        raise ValueError("content dimensions must be non-negative")
    if not 0.0 <= fit_margin < 0.5:
        raise ValueError("margin must be between 0 and 0.5")
    width = max(1.0, content_width) * (1.0 + 2.0 * fit_margin)
    height = max(1.0, content_height) * (1.0 + 2.0 * fit_margin)
    return clamp_navigation_zoom(min(viewport_width / width, viewport_height / height))
