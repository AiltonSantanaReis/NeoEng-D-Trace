"""Independent, validated scenario-collider domain model for E05."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from src.core.operational_limits import MAX_POLYGON_POINTS, MAX_PROJECT_OBJECTS
from src.core.polygon_validation import is_valid_polygon

Point = tuple[float, float]
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_MASK_MAX = 0xFFFF


class ColliderError(ValueError):
    """A rejected collider mutation with a stable diagnostic code."""

    def __init__(self, code: str, message: str, *, collider_id: str | None = None):
        self.code = code
        self.collider_id = collider_id
        prefix = f"{collider_id}: " if collider_id else ""
        super().__init__(f"{prefix}[{code}] {message}")


class ColliderKind(str, Enum):
    BOX = "box"
    CIRCLE = "circle"
    POLYGON = "polygon"
    SEGMENT = "segment"
    CHAIN = "chain"


def _finite_pair(value: Any, field_name: str) -> Point:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ColliderError("invalid_vector", f"{field_name} must contain two numbers")
    numbers: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ColliderError("invalid_vector", f"{field_name} must contain numbers")
        number = float(item)
        if not math.isfinite(number):
            raise ColliderError("invalid_number", f"{field_name} must be finite")
        numbers.append(number)
    return numbers[0], numbers[1]


def _points(value: Any, field_name: str) -> tuple[Point, ...]:
    if not isinstance(value, (tuple, list)) or len(value) > MAX_POLYGON_POINTS:
        raise ColliderError("vertex_limit", f"{field_name} exceeds the vertex limit")
    result = tuple(_finite_pair(point, field_name) for point in value)
    return result


def _positive(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ColliderError("invalid_number", f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ColliderError("non_positive", f"{field_name} must be positive")
    return number


def _mask(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= _MASK_MAX
    ):
        raise ColliderError(
            "invalid_mask", f"{field_name} must be an integer from 1 to 65535"
        )
    return value


@dataclass(frozen=True)
class Collider:
    """One independent collider; geometry is expressed in local coordinates."""

    id: str
    kind: ColliderKind
    points: tuple[Point, ...] = ()
    size: Point | None = None
    radius: float | None = None
    closed: bool = False
    position: Point = (0.0, 0.0)
    scale: Point = (1.0, 1.0)
    rotation_degrees: float = 0.0
    entity_id: str | None = None
    category: int = 1
    mask: int = _MASK_MAX
    is_trigger: bool = False
    visible: bool = True
    material: str | None = None
    version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _ID_RE.fullmatch(self.id):
            raise ColliderError(
                "invalid_id",
                "id must use 1-128 ASCII identifier characters",
                collider_id=self.id,
            )
        try:
            kind = (
                self.kind
                if isinstance(self.kind, ColliderKind)
                else ColliderKind(self.kind)
            )
        except (TypeError, ValueError) as exc:
            raise ColliderError(
                "invalid_kind", "unsupported collider kind", collider_id=self.id
            ) from exc
        object.__setattr__(self, "kind", kind)
        position = _finite_pair(self.position, "position")
        scale = _finite_pair(self.scale, "scale")
        rotation = float(self.rotation_degrees)
        if not math.isfinite(rotation) or scale[0] == 0.0 or scale[1] == 0.0:
            raise ColliderError(
                "invalid_transform",
                "position, scale and rotation must be finite",
                collider_id=self.id,
            )
        if self.entity_id is not None and (
            not isinstance(self.entity_id, str) or not _ID_RE.fullmatch(self.entity_id)
        ):
            raise ColliderError(
                "invalid_entity_id",
                "entity_id is not a valid identifier",
                collider_id=self.id,
            )
        category = _mask(self.category, "category")
        mask = _mask(self.mask, "mask")
        if not isinstance(self.version, int) or self.version < 1:
            raise ColliderError(
                "invalid_version",
                "version must be a positive integer",
                collider_id=self.id,
            )
        if self.material is not None and (
            not isinstance(self.material, str) or len(self.material) > 128
        ):
            raise ColliderError(
                "invalid_material",
                "material must be at most 128 characters",
                collider_id=self.id,
            )

        points = _points(self.points, "points")
        size = None if self.size is None else _finite_pair(self.size, "size")
        radius = None if self.radius is None else _positive(self.radius, "radius")
        if kind is ColliderKind.BOX:
            if size is None or size[0] <= 0.0 or size[1] <= 0.0:
                raise ColliderError(
                    "invalid_box", "box size must be positive", collider_id=self.id
                )
            if points or radius is not None:
                raise ColliderError(
                    "geometry_conflict", "box accepts only size", collider_id=self.id
                )
        elif kind is ColliderKind.CIRCLE:
            if radius is None:
                raise ColliderError(
                    "invalid_circle", "circle radius is required", collider_id=self.id
                )
            if abs(scale[0] - scale[1]) > 1e-9:
                raise ColliderError(
                    "circle_scale", "circle scale must be uniform", collider_id=self.id
                )
            if points or size is not None:
                raise ColliderError(
                    "geometry_conflict",
                    "circle accepts only radius",
                    collider_id=self.id,
                )
        elif kind is ColliderKind.POLYGON:
            if (
                size is not None
                or radius is not None
                or not is_valid_polygon([list(point) for point in points])
            ):
                raise ColliderError(
                    "invalid_polygon",
                    "polygon must be finite, CCW, simple and non-degenerate",
                    collider_id=self.id,
                )
        elif kind is ColliderKind.SEGMENT:
            if (
                size is not None
                or radius is not None
                or len(points) != 2
                or points[0] == points[1]
            ):
                raise ColliderError(
                    "invalid_segment",
                    "segment requires two distinct points",
                    collider_id=self.id,
                )
        else:
            if (
                size is not None
                or radius is not None
                or len(points) < 2
                or any(
                    points[index] == points[index + 1]
                    for index in range(len(points) - 1)
                )
            ):
                raise ColliderError(
                    "invalid_chain",
                    "chain requires distinct consecutive points",
                    collider_id=self.id,
                )
        object.__setattr__(self, "position", position)
        object.__setattr__(self, "scale", scale)
        object.__setattr__(self, "rotation_degrees", rotation)
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "mask", mask)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "points": [{"x": x, "y": y} for x, y in self.points],
            "size": (
                None if self.size is None else {"x": self.size[0], "y": self.size[1]}
            ),
            "radius": self.radius,
            "closed": self.closed,
            "position": {"x": self.position[0], "y": self.position[1]},
            "scale": {"x": self.scale[0], "y": self.scale[1]},
            "rotation_degrees": self.rotation_degrees,
            "entity_id": self.entity_id,
            "category": self.category,
            "mask": self.mask,
            "is_trigger": self.is_trigger,
            "visible": self.visible,
            "material": self.material,
            "version": self.version,
        }


@dataclass
class ColliderDocument:
    """Bounded collection with atomic replacement semantics."""

    id: str = "scenario-colliders"
    version: int = 1
    colliders: dict[str, Collider] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _ID_RE.fullmatch(self.id):
            raise ColliderError("invalid_id", "document id is invalid")
        if self.version != 1:
            raise ColliderError(
                "invalid_version", "unsupported collider document version"
            )
        if len(self.colliders) > MAX_PROJECT_OBJECTS:
            raise ColliderError(
                "object_limit", "collider collection exceeds the project limit"
            )
        if any(key != value.id for key, value in self.colliders.items()):
            raise ColliderError(
                "id_mismatch", "collider dictionary key must equal collider id"
            )

    def replace_all(self, values: Iterable[Collider]) -> None:
        items = tuple(values)
        candidate = {value.id: value for value in items}
        if len(candidate) != len(items):
            raise ColliderError("duplicate_id", "collider IDs must be unique")
        if len(candidate) > MAX_PROJECT_OBJECTS:
            raise ColliderError(
                "object_limit", "collider collection exceeds the project limit"
            )
        self.colliders = candidate

    def add(self, collider: Collider) -> None:
        if collider.id in self.colliders:
            raise ColliderError(
                "duplicate_id", "collider ID already exists", collider_id=collider.id
            )
        if len(self.colliders) >= MAX_PROJECT_OBJECTS:
            raise ColliderError(
                "object_limit", "collider collection exceeds the project limit"
            )
        self.colliders[collider.id] = collider

    def remove(self, collider_id: str) -> Collider:
        try:
            return self.colliders.pop(collider_id)
        except KeyError as exc:
            raise ColliderError(
                "missing_id", "collider does not exist", collider_id=collider_id
            ) from exc


__all__ = ["Collider", "ColliderDocument", "ColliderError", "ColliderKind", "Point"]
