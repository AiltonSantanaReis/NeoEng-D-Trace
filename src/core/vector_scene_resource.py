"""Integration of a detected/editable contour into authored scene objects."""

from __future__ import annotations

from typing import Literal

from src.core.convex_decomp import convex_hull_polygon
from src.core.polygon_validation import is_valid_polygon
from src.core.vectorization import VectorizationError, VectorizationResult
from src.persistence.project_schema import PointRecord
from src.persistence.scene_authoring_schema import (
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    SceneVectorGeometryRecord,
    SceneVectorImageSizeRecord,
)

CollisionStrategy = Literal["polygon", "convex_hull"]


def _points(value: object, *, field: str) -> list[tuple[float, float]]:
    if not isinstance(value, (list, tuple)):
        raise VectorizationError(
            "invalid_geometry", f"{field} must be a point sequence"
        )
    points: list[tuple[float, float]] = []
    for point in value:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise VectorizationError(
                "invalid_geometry", f"{field} contains an invalid point"
            )
        try:
            points.append((float(point[0]), float(point[1])))
        except (TypeError, ValueError, OverflowError) as exc:
            raise VectorizationError(
                "invalid_geometry", f"{field} contains a non-numeric point"
            ) from exc
    if not is_valid_polygon(points):
        raise VectorizationError(
            "invalid_geometry", f"{field} must be a valid simple polygon"
        )
    return points


def _records(points: list[tuple[float, float]]) -> list[PointRecord]:
    return [PointRecord(x=point[0], y=point[1]) for point in points]


def build_vector_geometry(
    result: VectorizationResult,
    edited_polygon: object | None = None,
    *,
    collision_strategy: CollisionStrategy = "polygon",
) -> SceneVectorGeometryRecord:
    """Create a validated, portable geometry record from E09-A/B output."""

    original = _points(list(result.polygon), field="original polygon")
    current = _points(
        list(result.polygon) if edited_polygon is None else edited_polygon,
        field="edited polygon",
    )
    if collision_strategy not in ("polygon", "convex_hull"):
        raise VectorizationError(
            "invalid_collision_strategy", "unsupported collision strategy"
        )
    collision = (
        current if collision_strategy == "polygon" else convex_hull_polygon(current)
    )
    if not is_valid_polygon(collision):
        raise VectorizationError("invalid_collision", "collision geometry is invalid")
    return SceneVectorGeometryRecord(
        algorithm=result.algorithm,
        source_sha256=result.source_sha256,
        image_size=SceneVectorImageSizeRecord(
            width=result.image_width, height=result.image_height
        ),
        original_polygon=_records(original),
        polygon=_records(current),
        collision_polygon=_records(collision),
        detection_parameters={
            "channel": result.channel,
            "threshold": result.threshold,
            "approximation_epsilon": result.approximation_epsilon,
            "minimum_area": result.minimum_area,
            "collision_strategy": collision_strategy,
        },
    )


def create_vector_scene_object(
    result: VectorizationResult,
    *,
    object_id: str,
    asset_id: str,
    layer_id: str,
    transform: SceneTransformRecord,
    edited_polygon: object | None = None,
    collision_strategy: CollisionStrategy = "polygon",
) -> SceneObjectAuthoringRecord:
    """Create one self-contained authored object from a vector result."""

    return SceneObjectAuthoringRecord(
        id=object_id,
        asset_id=asset_id,
        layer_id=layer_id,
        transform=transform,
        vector_geometry=build_vector_geometry(
            result,
            edited_polygon,
            collision_strategy=collision_strategy,
        ),
    )


__all__ = [
    "CollisionStrategy",
    "build_vector_geometry",
    "create_vector_scene_object",
]
