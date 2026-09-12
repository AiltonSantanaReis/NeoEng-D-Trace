"""Deterministic 2D lighting primitives used by the raster scene renderer.

The module is intentionally independent from Qt and from the persisted scene
schema.  It provides the renderer with an explicit material/light contract so
that zero-intensity, normal-map and shadow behavior can be tested at pixel
level without coupling domain state to a widget.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

Color3 = tuple[float, float, float]
Point2 = tuple[float, float]
Polygon2 = tuple[Point2, ...]


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _color(value: Sequence[float], field: str) -> Color3:
    if isinstance(value, (str, bytes)) or len(value) != 3:
        raise ValueError(f"{field} must contain three components")
    result = tuple(
        _finite(component, f"{field}[{index}]") for index, component in enumerate(value)
    )
    if any(component < 0.0 or component > 1.0 for component in result):
        raise ValueError(f"{field} components must be between 0 and 1")
    return result  # type: ignore[return-value]


def _point(value: Sequence[float], field: str) -> Point2:
    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError(f"{field} must contain two coordinates")
    return (_finite(value[0], f"{field}.x"), _finite(value[1], f"{field}.y"))


@dataclass(frozen=True)
class SceneLightingMaterial:
    """Surface parameters for one authored object."""

    albedo: Color3 = (1.0, 1.0, 1.0)
    normal_xy: Point2 = (0.0, 0.0)
    normal_strength: float = 1.0
    emission: Color3 = (0.0, 0.0, 0.0)
    emission_strength: float = 0.0
    opacity: float = 1.0
    receives_shadow: bool = True
    casts_shadow: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "albedo", _color(self.albedo, "albedo"))
        object.__setattr__(self, "normal_xy", _point(self.normal_xy, "normal_xy"))
        object.__setattr__(
            self, "normal_strength", _finite(self.normal_strength, "normal_strength")
        )
        object.__setattr__(self, "emission", _color(self.emission, "emission"))
        object.__setattr__(
            self,
            "emission_strength",
            _finite(self.emission_strength, "emission_strength"),
        )
        object.__setattr__(self, "opacity", _finite(self.opacity, "opacity"))
        if self.normal_strength < 0.0 or self.normal_strength > 1.0:
            raise ValueError("normal_strength must be between 0 and 1")
        if self.emission_strength < 0.0:
            raise ValueError("emission_strength must be non-negative")
        if self.opacity < 0.0 or self.opacity > 1.0:
            raise ValueError("opacity must be between 0 and 1")


@dataclass(frozen=True)
class ScenePointLight:
    """A bounded point light in scene/world coordinates."""

    id: str
    position: Point2
    color: Color3 = (1.0, 1.0, 1.0)
    intensity: float = 1.0
    radius: float = 256.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("light id must not be empty")
        object.__setattr__(self, "position", _point(self.position, "light.position"))
        object.__setattr__(self, "color", _color(self.color, "light.color"))
        object.__setattr__(
            self, "intensity", _finite(self.intensity, "light.intensity")
        )
        object.__setattr__(self, "radius", _finite(self.radius, "light.radius"))
        if self.intensity < 0.0:
            raise ValueError("light.intensity must be non-negative")
        if self.radius <= 0.0:
            raise ValueError("light.radius must be positive")


@dataclass(frozen=True)
class SceneDirectionalLight:
    """An infinite light with a stable 2D incoming direction.

    ``direction_degrees`` is the vector from a shaded surface toward the
    light source in screen coordinates (0 degrees is +X, 90 degrees is +Y).
    This convention matches the editor's rotation Z and the reference
    surface normal used by this raster backend.
    """

    id: str
    direction_degrees: float = 90.0
    color: Color3 = (1.0, 1.0, 1.0)
    intensity: float = 1.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("light id must not be empty")
        object.__setattr__(
            self,
            "direction_degrees",
            _finite(self.direction_degrees, "directional light direction"),
        )
        object.__setattr__(self, "color", _color(self.color, "light.color"))
        object.__setattr__(
            self, "intensity", _finite(self.intensity, "light.intensity")
        )
        if self.intensity < 0.0:
            raise ValueError("light.intensity must be non-negative")


@dataclass(frozen=True)
class SceneLightingSettings:
    """Complete frame-independent lighting state for the raster backend."""

    ambient_color: Color3 = (1.0, 1.0, 1.0)
    ambient_intensity: float = 0.18
    lights: tuple[ScenePointLight | SceneDirectionalLight, ...] = ()
    occluders: tuple[Polygon2, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "ambient_color", _color(self.ambient_color, "ambient_color")
        )
        object.__setattr__(
            self,
            "ambient_intensity",
            _finite(self.ambient_intensity, "ambient_intensity"),
        )
        if self.ambient_intensity < 0.0 or self.ambient_intensity > 1.0:
            raise ValueError("ambient_intensity must be between 0 and 1")
        object.__setattr__(self, "lights", tuple(self.lights))
        object.__setattr__(
            self,
            "occluders",
            tuple(
                tuple(_point(point, "occluder.point") for point in polygon)
                for polygon in self.occluders
            ),
        )


def default_scene_lighting() -> SceneLightingSettings:
    """Return the portable reference lighting used by the scenario preview."""

    return SceneLightingSettings(
        ambient_intensity=0.22,
        lights=(
            ScenePointLight(
                id="key-light",
                position=(160.0, 220.0),
                color=(1.0, 0.86, 0.68),
                intensity=1.35,
                radius=720.0,
            ),
        ),
    )


def _dot(first: Point2, second: Point2) -> float:
    return first[0] * second[0] + first[1] * second[1]


def _normalize(value: Point2) -> Point2:
    length = math.hypot(value[0], value[1])
    if length <= 1e-12:
        return (0.0, 0.0)
    return (value[0] / length, value[1] / length)


def _normal(material: SceneLightingMaterial) -> Point2:
    # The 2D reference backend treats the authored surface as facing +Y in
    # screen space; normal_xy is the tangent-space normal-map perturbation.
    perturbed = (
        material.normal_xy[0] * material.normal_strength,
        1.0 + material.normal_xy[1] * material.normal_strength,
    )
    return _normalize(perturbed)


def _orientation(first: Point2, second: Point2, third: Point2) -> float:
    return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
        third[0] - first[0]
    )


def _segments_intersect(
    first: Point2, second: Point2, third: Point2, fourth: Point2
) -> bool:
    epsilon = 1e-9
    a = _orientation(first, second, third)
    b = _orientation(first, second, fourth)
    c = _orientation(third, fourth, first)
    d = _orientation(third, fourth, second)
    if ((a > epsilon and b < -epsilon) or (a < -epsilon and b > epsilon)) and (
        (c > epsilon and d < -epsilon) or (c < -epsilon and d > epsilon)
    ):
        return True
    return False


def _blocked(
    position: Point2, light: ScenePointLight, occluders: Iterable[Polygon2]
) -> bool:
    for polygon in occluders:
        if len(polygon) < 3:
            continue
        for index, start in enumerate(polygon):
            end = polygon[(index + 1) % len(polygon)]
            if _segments_intersect(position, light.position, start, end):
                return True
    return False


def _blocked_directional(
    position: Point2, direction: Point2, occluders: Iterable[Polygon2]
) -> bool:
    """Check a finite approximation of the ray toward an infinite source."""

    end = (
        position[0] + direction[0] * 1_000_000.0,
        position[1] + direction[1] * 1_000_000.0,
    )
    for polygon in occluders:
        if len(polygon) < 3:
            continue
        for index, start in enumerate(polygon):
            edge_end = polygon[(index + 1) % len(polygon)]
            if _segments_intersect(position, end, start, edge_end):
                return True
    return False


def shade_color(
    position: Point2,
    material: SceneLightingMaterial,
    settings: SceneLightingSettings,
) -> tuple[Color3, float, tuple[str, ...]]:
    """Shade one surface sample and return color, opacity and light IDs."""

    point = _point(position, "position")
    normal = _normal(material)
    illumination = [
        settings.ambient_intensity * component for component in settings.ambient_color
    ]
    contributors: list[str] = []
    for light in settings.lights:
        if not light.enabled or light.intensity <= 0.0:
            continue
        if isinstance(light, SceneDirectionalLight):
            angle = math.radians(light.direction_degrees)
            direction = _normalize((math.cos(angle), math.sin(angle)))
            if material.receives_shadow and _blocked_directional(
                point, direction, settings.occluders
            ):
                continue
            falloff = 1.0
        else:
            vector = (light.position[0] - point[0], light.position[1] - point[1])
            distance = math.hypot(vector[0], vector[1])
            if distance >= light.radius:
                continue
            if material.receives_shadow and _blocked(point, light, settings.occluders):
                continue
            direction = _normalize(vector)
            falloff = max(0.0, 1.0 - distance / light.radius)
        diffuse = max(0.0, _dot(normal, direction))
        strength = diffuse * falloff * light.intensity
        if strength <= 0.0:
            continue
        contributors.append(light.id)
        for index in range(3):
            illumination[index] += strength * light.color[index]
    color: Color3 = (
        min(
            1.0,
            max(
                0.0,
                material.albedo[0] * illumination[0]
                + material.emission[0] * material.emission_strength,
            ),
        ),
        min(
            1.0,
            max(
                0.0,
                material.albedo[1] * illumination[1]
                + material.emission[1] * material.emission_strength,
            ),
        ),
        min(
            1.0,
            max(
                0.0,
                material.albedo[2] * illumination[2]
                + material.emission[2] * material.emission_strength,
            ),
        ),
    )
    return color, material.opacity, tuple(contributors)


__all__ = [
    "Color3",
    "Point2",
    "Polygon2",
    "SceneLightingMaterial",
    "SceneLightingSettings",
    "SceneDirectionalLight",
    "ScenePointLight",
    "default_scene_lighting",
    "shade_color",
]
