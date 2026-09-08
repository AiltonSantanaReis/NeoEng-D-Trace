"""Pure orthographic camera and parallax projection primitives.

This module deliberately has no Qt, scene, persistence, or exporter dependency.
It models only the math needed by the future scenario preview.  Parallax depth
is normalized and independent from ``SceneObject.position.z`` and exporter
``z_depth`` values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

Point2 = tuple[float, float]


def _finite(value: object, field: str) -> float:
    """Convert a numeric value to a finite float, rejecting booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _bounded(value: object, field: str, lower: float, upper: float) -> float:
    """Return a finite value inside an inclusive interval."""

    result = _finite(value, field)
    if result < lower or result > upper:
        raise ValueError(f"{field} must be between {lower} and {upper}")
    return result


def _point(value: Sequence[float], field: str) -> Point2:
    """Validate and normalize a two-dimensional point."""

    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError(f"{field} must contain exactly two coordinates")
    return (_finite(value[0], f"{field}.x"), _finite(value[1], f"{field}.y"))


@dataclass(frozen=True)
class ParallaxLayer:
    """Normalized parallax parameters for one future scenario layer.

    ``depth`` is a normalized value from 0 to 1.  A depth of 0 is the
    foreground and receives the full camera translation/zoom.  A depth of 1
    is the far plane and is stationary when both strengths are 1.  The
    strengths are independent so a scenario can attenuate translation and
    zoom differently without changing the depth contract.
    """

    depth: float = 0.0
    translation_strength: float = 1.0
    zoom_strength: float = 1.0
    scroll_x: float = 1.0
    scroll_y: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    repeat_x: bool = False
    repeat_y: bool = False
    mirror_x: bool = False
    mirror_y: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "depth", _bounded(self.depth, "depth", 0.0, 1.0))
        object.__setattr__(
            self,
            "translation_strength",
            _bounded(
                self.translation_strength,
                "translation_strength",
                0.0,
                1.0,
            ),
        )
        object.__setattr__(
            self,
            "zoom_strength",
            _bounded(self.zoom_strength, "zoom_strength", 0.0, 1.0),
        )
        object.__setattr__(
            self, "scroll_x", _bounded(self.scroll_x, "scroll_x", -4.0, 4.0)
        )
        object.__setattr__(
            self, "scroll_y", _bounded(self.scroll_y, "scroll_y", -4.0, 4.0)
        )
        object.__setattr__(self, "offset_x", _finite(self.offset_x, "offset_x"))
        object.__setattr__(self, "offset_y", _finite(self.offset_y, "offset_y"))
        for field in ("repeat_x", "repeat_y", "mirror_x", "mirror_y"):
            value = getattr(self, field)
            if not isinstance(value, bool):
                raise ValueError(f"{field} must be boolean")

    @property
    def translation_factor(self) -> float:
        """Fraction of camera translation applied to this layer."""

        return 1.0 - self.depth * self.translation_strength

    @property
    def zoom_factor(self) -> float:
        """Fraction of camera zoom delta applied to this layer."""

        return 1.0 - self.depth * self.zoom_strength

    @property
    def camera_scroll_x(self) -> float:
        """Effective signed horizontal camera response for this layer."""

        return self.translation_factor * self.scroll_x

    @property
    def camera_scroll_y(self) -> float:
        """Effective signed vertical camera response for this layer."""

        return self.translation_factor * self.scroll_y

    def tile_variants(
        self,
        tile_size: Sequence[float],
        *,
        radius: int = 1,
    ) -> tuple[tuple[float, float, bool, bool], ...]:
        """Return deterministic repeat/mirror variants around the anchor.

        This is renderer-neutral metadata: the caller supplies the actual
        texture/geometry tile size and decides how to draw each variant.
        With both repeat flags disabled the result is exactly one anchor.
        """

        width, height = _point(tile_size, "tile_size")
        if width <= 0.0 or height <= 0.0:
            raise ValueError("tile_size coordinates must be positive")
        if isinstance(radius, bool) or not isinstance(radius, int) or radius < 0:
            raise ValueError("radius must be a non-negative integer")
        x_indices = range(-radius, radius + 1) if self.repeat_x else (0,)
        y_indices = range(-radius, radius + 1) if self.repeat_y else (0,)
        return tuple(
            (
                index_x * width,
                index_y * height,
                bool(self.mirror_x and index_x % 2),
                bool(self.mirror_y and index_y % 2),
            )
            for index_y in y_indices
            for index_x in x_indices
        )


@dataclass(frozen=True)
class OrthographicCamera:
    """Deterministic 2D orthographic camera in screen pixels.

    ``position`` is a camera offset from the world origin.  The viewport is
    centered on the screen, and ``zoom`` is 1.0 at the neutral scale.  The
    projection applies the layer's parallax translation before its depth-
    attenuated zoom.  No scene object or persisted project field is changed.
    """

    viewport_size: Point2
    position: Point2 = (0.0, 0.0)
    zoom: float = 1.0

    def __post_init__(self) -> None:
        viewport = _point(self.viewport_size, "viewport_size")
        if viewport[0] <= 0.0 or viewport[1] <= 0.0:
            raise ValueError("viewport_size coordinates must be positive")
        object.__setattr__(self, "viewport_size", viewport)
        object.__setattr__(self, "position", _point(self.position, "position"))
        object.__setattr__(self, "zoom", _finite(self.zoom, "zoom"))
        if self.zoom <= 0.0:
            raise ValueError("zoom must be positive")

    @property
    def viewport_center(self) -> Point2:
        """Return the pixel center used by the orthographic projection."""

        return (self.viewport_size[0] / 2.0, self.viewport_size[1] / 2.0)

    def effective_zoom(self, layer: ParallaxLayer | None = None) -> float:
        """Return the zoom applied to a layer after depth attenuation."""

        resolved = layer or ParallaxLayer()
        return 1.0 + (self.zoom - 1.0) * resolved.zoom_factor

    def project(
        self,
        world_point: Sequence[float],
        layer: ParallaxLayer | None = None,
    ) -> Point2:
        """Project a world point to viewport pixels for one parallax layer."""

        world = _point(world_point, "world_point")
        resolved = layer or ParallaxLayer()
        zoom = self.effective_zoom(resolved)
        camera_x = self.position[0] * resolved.camera_scroll_x - resolved.offset_x
        camera_y = self.position[1] * resolved.camera_scroll_y - resolved.offset_y
        center_x, center_y = self.viewport_center
        return (
            (world[0] - camera_x) * zoom + center_x,
            (world[1] - camera_y) * zoom + center_y,
        )

    def unproject(
        self,
        screen_point: Sequence[float],
        layer: ParallaxLayer | None = None,
    ) -> Point2:
        """Invert :meth:`project` for the same camera and layer."""

        screen = _point(screen_point, "screen_point")
        resolved = layer or ParallaxLayer()
        zoom = self.effective_zoom(resolved)
        center_x, center_y = self.viewport_center
        camera_x = self.position[0] * resolved.camera_scroll_x - resolved.offset_x
        camera_y = self.position[1] * resolved.camera_scroll_y - resolved.offset_y
        return (
            (screen[0] - center_x) / zoom + camera_x,
            (screen[1] - center_y) / zoom + camera_y,
        )

    def project_points(
        self,
        points: Iterable[Sequence[float]],
        layer: ParallaxLayer | None = None,
    ) -> list[Point2]:
        """Project a point sequence without mutating the source."""

        return [self.project(point, layer) for point in points]

    def with_position(self, position: Sequence[float]) -> "OrthographicCamera":
        """Return a camera with a new position, preserving other fields."""

        return OrthographicCamera(
            self.viewport_size, _point(position, "position"), self.zoom
        )

    def with_zoom(self, zoom: float) -> "OrthographicCamera":
        """Return a camera with a new positive zoom, preserving other fields."""

        return OrthographicCamera(
            self.viewport_size, self.position, _finite(zoom, "zoom")
        )
