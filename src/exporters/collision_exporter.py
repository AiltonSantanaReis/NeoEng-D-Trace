"""Canonical JSON schema for collision exports."""

from __future__ import annotations

import math
import os
import tempfile
from collections.abc import Mapping, Sequence
from typing import Any

from src.models.scene import Scene

COLLISION_FORMAT_ID = "neoeng-d-trace-collisions"
COLLISION_SCHEMA_VERSION = 1
COLLISION_COORDINATE_SPACE = "image"


def _finite_float(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(normalized):
        raise ValueError(f"{field} must be a finite number")
    return normalized


def _normalize_points(object_id: str, points: Any) -> list[list[float]]:
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
        raise ValueError(f"Collision {object_id} points must be a sequence")

    normalized: list[list[float]] = []
    for index, point in enumerate(points):
        if (
            not isinstance(point, Sequence)
            or isinstance(point, (str, bytes))
            or len(point) != 2
        ):
            raise ValueError(f"Collision {object_id} point {index} must contain x/y")
        normalized.append(
            [
                _finite_float(point[0], f"Collision {object_id} point {index}.x"),
                _finite_float(point[1], f"Collision {object_id} point {index}.y"),
            ]
        )

    if len(normalized) < 3 or len({tuple(point) for point in normalized}) < 3:
        raise ValueError(f"Collision {object_id} must contain three distinct points")

    area_twice = 0.0
    for index, point in enumerate(normalized):
        next_point = normalized[(index + 1) % len(normalized)]
        area_twice += point[0] * next_point[1] - next_point[0] * point[1]
    if abs(area_twice) <= 1e-12:
        raise ValueError(f"Collision {object_id} must have non-zero area")

    return normalized


def collision_shape_record(scene: Scene, object_id: str) -> dict[str, Any] | None:
    """Return the canonical collision record for one scene object."""
    if object_id not in scene.collision_shapes:
        return None
    if object_id not in scene.objects:
        raise ValueError(f"Collision references unknown object: {object_id}")
    return {
        "object_id": object_id,
        "shape_type": "polygon",
        "coordinate_space": COLLISION_COORDINATE_SPACE,
        "points": _normalize_points(object_id, scene.collision_shapes[object_id]),
    }


def _normalize_results(
    results: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, result in enumerate(results or ()):
        if not isinstance(result, Mapping):
            raise ValueError(f"Collision result {index} must be an object")
        obj1_id = result.get("obj1_id")
        obj2_id = result.get("obj2_id")
        colliding = result.get("colliding")
        if not isinstance(obj1_id, str) or not obj1_id:
            raise ValueError(f"Collision result {index} has invalid obj1_id")
        if not isinstance(obj2_id, str) or not obj2_id:
            raise ValueError(f"Collision result {index} has invalid obj2_id")
        if not isinstance(colliding, bool):
            raise ValueError(f"Collision result {index} has invalid colliding flag")
        record: dict[str, Any] = {
            "obj1_id": obj1_id,
            "obj2_id": obj2_id,
            "colliding": colliding,
            "mtv": None,
        }
        mtv = result.get("mtv")
        if mtv is not None:
            if (
                not isinstance(mtv, Sequence)
                or isinstance(mtv, (str, bytes))
                or len(mtv) != 2
            ):
                raise ValueError(f"Collision result {index} has invalid mtv")
            record["mtv"] = [
                _finite_float(mtv[0], f"Collision result {index} mtv.x"),
                _finite_float(mtv[1], f"Collision result {index} mtv.y"),
            ]
        normalized.append(record)
    return normalized


def _normalize_json_value(value: Any, field: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return _finite_float(value, field)
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_json_value(value[key], f"{field}.{key}")
            for key in sorted(value, key=str)
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [
            _normalize_json_value(item, f"{field}[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{field} contains a non-JSON value")


def export_collision_document(
    scene: Scene,
    *,
    results: Sequence[Mapping[str, Any]] | None = None,
    statistics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the single versioned collision document used by every JSON path."""
    shapes = []
    for object_id in sorted(scene.collision_shapes):
        shape = collision_shape_record(scene, object_id)
        if shape is not None:
            shapes.append(shape)

    return {
        "format_id": COLLISION_FORMAT_ID,
        "schema_version": COLLISION_SCHEMA_VERSION,
        "coordinate_space": COLLISION_COORDINATE_SPACE,
        "shapes": shapes,
        "results": _normalize_results(results),
        "statistics": _normalize_json_value(statistics or {}, "statistics"),
    }


def render_collision_text(document: Mapping[str, Any]) -> str:
    """Render the legacy text view from a canonical collision document."""
    lines: list[str] = []
    for shape in document.get("shapes", []):
        lines.append(f"Object {shape['object_id']}:")
        for x, y in shape["points"]:
            lines.append(f"  ({x}, {y})")
        lines.append("")
    return "\n".join(lines)


def save_collision_text(document: Mapping[str, Any], path: str) -> None:
    """Persist the derived text view with atomic replacement."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            dir=directory or ".",
            encoding="utf-8",
            newline="\n",
        ) as temporary:
            temporary.write(render_collision_text(document))
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = temporary.name
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
