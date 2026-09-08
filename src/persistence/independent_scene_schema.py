"""Versioned contract for a scenario that has no image project dependency.

This contract is intentionally separate from ``ProjectDocumentV1`` and from
the legacy/project-bound scenario sidecars.  A new empty scenario is a real
document in its own right; it never receives a fabricated project reference.
Future authoring fields must be added through an explicit schema successor and
an executable migration.
"""

from __future__ import annotations

import math
from typing import Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION
from src.core.operational_limits import MAX_PROJECT_OBJECTS
from src.persistence.project_schema import (
    MAX_NAME_LENGTH,
    PointRecord,
    StrictProjectModel,
)

INDEPENDENT_SCENE_FORMAT_ID = "neoeng-d-trace-independent-scene"
INDEPENDENT_SCENE_SCHEMA_VERSION = 1
INDEPENDENT_SCENE_SCHEMA_VERSION_V2 = 2
INDEPENDENT_SCENE_FILE_EXTENSION = ".ndtscene"
MAX_SCENE_WIDTH = 32_768
MAX_SCENE_HEIGHT = 32_768
MAX_SCENE_NAME_LENGTH = MAX_NAME_LENGTH


def _finite(value: int | float, field: str) -> int | float:
    if isinstance(value, bool) or (
        isinstance(value, float) and not math.isfinite(value)
    ):
        raise ValueError(f"{field} must be a finite number")
    return value


class IndependentSceneMetadataRecord(StrictProjectModel):
    """Stable identity for an independent scene document."""

    name: str = Field(min_length=1, max_length=MAX_SCENE_NAME_LENGTH)
    generator: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    app_version: str = Field(min_length=1, max_length=128)


class SceneResolutionRecord(StrictProjectModel):
    """Authorial canvas resolution; viewport size is runtime state."""

    width: int = Field(ge=1, le=MAX_SCENE_WIDTH)
    height: int = Field(ge=1, le=MAX_SCENE_HEIGHT)


class SceneCoordinateSystemRecord(StrictProjectModel):
    """Explicit authoring coordinates; no renderer-specific inference."""

    origin: Literal["top_left"] = "top_left"
    x_axis: Literal["right"] = "right"
    y_axis: Literal["down"] = "down"
    unit: Literal["pixel"] = "pixel"


class IndependentSceneCompatibilityRecord(StrictProjectModel):
    """Compatibility promise for explicit reader/writer evolution."""

    reader_min_schema_version: Literal[1] = 1
    writer_schema_version: Literal[1] = 1


class IndependentSceneCompatibilityRecordV2(StrictProjectModel):
    """Compatibility declaration for the first authoring-capable schema."""

    reader_min_schema_version: Literal[1] = 1
    writer_schema_version: Literal[2] = 2


class IndependentSceneCameraRecord(StrictProjectModel):
    """Persisted orthographic camera state for a new scene."""

    position: PointRecord = PointRecord(x=0.0, y=0.0)
    zoom: int | float = 1.0

    @field_validator("position")
    @classmethod
    def validate_position(cls, value: PointRecord) -> PointRecord:
        _finite(value.x, "camera.position.x")
        _finite(value.y, "camera.position.y")
        return value

    @field_validator("zoom")
    @classmethod
    def validate_zoom(cls, value: int | float) -> int | float:
        number = _finite(value, "camera.zoom")
        if number <= 0:
            raise ValueError("camera.zoom must be positive")
        return number


class IndependentSceneRootRecord(StrictProjectModel):
    """Stable root identity reserved for future authoring objects."""

    id: Literal["scene_root"] = "scene_root"
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)


PrimitiveKind = Literal["rectangle", "ellipse", "polygon", "path"]


class IndependentScenePrimitiveGeometryRecord(StrictProjectModel):
    """Portable geometry for one author-created primitive."""

    kind: PrimitiveKind
    points: list[PointRecord] = Field(min_length=2, max_length=4096)
    closed: bool = True
    filled: bool = True

    @model_validator(mode="after")
    def validate_geometry(self) -> "IndependentScenePrimitiveGeometryRecord":
        points = self.points
        if len({(point.x, point.y) for point in points}) != len(points):
            raise ValueError("primitive points must be unique")
        if self.kind in {"rectangle", "ellipse"} and len(points) != 2:
            raise ValueError(f"{self.kind} geometry requires two bounding points")
        if self.kind == "polygon" and (len(points) < 3 or not self.closed):
            raise ValueError(
                "polygon geometry must be a closed shape with three points"
            )
        if (
            self.closed
            and len(points) < 3
            and self.kind not in {"rectangle", "ellipse"}
        ):
            raise ValueError("closed path geometry requires at least three points")
        if not self.closed and self.filled:
            raise ValueError("open path geometry cannot be filled")
        if self.kind == "polygon" and _polygon_self_intersects(points):
            raise ValueError("polygon geometry must not self-intersect")
        return self


class IndependentScenePrimitiveTransformRecord(StrictProjectModel):
    """2D transform kept separate from geometry coordinates."""

    position: PointRecord = PointRecord(x=0.0, y=0.0)
    rotation: int | float = 0.0
    scale: PointRecord = PointRecord(x=1.0, y=1.0)
    pivot: PointRecord = PointRecord(x=0.5, y=0.5)

    @field_validator("position", "scale", "pivot")
    @classmethod
    def validate_points(cls, value: PointRecord) -> PointRecord:
        _finite(value.x, "primitive transform coordinate")
        _finite(value.y, "primitive transform coordinate")
        return value

    @field_validator("rotation")
    @classmethod
    def validate_rotation(cls, value: int | float) -> int | float:
        return _finite(value, "primitive rotation")

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, value: PointRecord) -> PointRecord:
        if value.x <= 0 or value.y <= 0:
            raise ValueError("primitive scale must be positive")
        return value

    @field_validator("pivot")
    @classmethod
    def validate_pivot(cls, value: PointRecord) -> PointRecord:
        if not 0 <= value.x <= 1 or not 0 <= value.y <= 1:
            raise ValueError("primitive pivot must be between zero and one")
        return value


class IndependentScenePrimitiveRecord(StrictProjectModel):
    """Stable identity and editable state for an E02 primitive."""

    id: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    geometry: IndependentScenePrimitiveGeometryRecord
    transform: IndependentScenePrimitiveTransformRecord = (
        IndependentScenePrimitiveTransformRecord()
    )
    visible: bool = True
    locked: bool = False


def _cross(first: PointRecord, second: PointRecord, third: PointRecord) -> float:
    return (second.x - first.x) * (third.y - first.y) - (second.y - first.y) * (
        third.x - first.x
    )


def _segments_intersect(
    first_start: PointRecord,
    first_end: PointRecord,
    second_start: PointRecord,
    second_end: PointRecord,
) -> bool:
    orientations = (
        _cross(first_start, first_end, second_start),
        _cross(first_start, first_end, second_end),
        _cross(second_start, second_end, first_start),
        _cross(second_start, second_end, first_end),
    )
    return (
        orientations[0] * orientations[1] < 0 and orientations[2] * orientations[3] < 0
    )


def _polygon_self_intersects(points: list[PointRecord]) -> bool:
    edges = [
        (points[index], points[(index + 1) % len(points)])
        for index in range(len(points))
    ]
    for first_index, (first_start, first_end) in enumerate(edges):
        for second_index in range(first_index + 1, len(edges)):
            if second_index in {
                first_index,
                (first_index + 1) % len(edges),
                (first_index - 1) % len(edges),
            }:
                continue
            second_start, second_end = edges[second_index]
            if _segments_intersect(first_start, first_end, second_start, second_end):
                return True
    return False


class IndependentSceneDocumentV1(StrictProjectModel):
    """Empty independent scene contract, version 1."""

    format_id: Literal["neoeng-d-trace-independent-scene"] = INDEPENDENT_SCENE_FORMAT_ID
    schema_version: Literal[1] = INDEPENDENT_SCENE_SCHEMA_VERSION
    metadata: IndependentSceneMetadataRecord
    resolution: SceneResolutionRecord
    coordinates: SceneCoordinateSystemRecord = SceneCoordinateSystemRecord()
    assets_root: Literal["assets"] = "assets"
    compatibility: IndependentSceneCompatibilityRecord = (
        IndependentSceneCompatibilityRecord()
    )
    camera: IndependentSceneCameraRecord = IndependentSceneCameraRecord()
    root: IndependentSceneRootRecord = IndependentSceneRootRecord(name="Scene")

    @model_validator(mode="after")
    def validate_independent_identity(self) -> "IndependentSceneDocumentV1":
        if not self.metadata.name.strip():
            raise ValueError("scene metadata name must not be blank")
        return self


class IndependentSceneDocumentV2(StrictProjectModel):
    """Authoring-capable successor of the empty independent scene contract."""

    format_id: Literal["neoeng-d-trace-independent-scene"] = INDEPENDENT_SCENE_FORMAT_ID
    schema_version: Literal[2] = INDEPENDENT_SCENE_SCHEMA_VERSION_V2
    metadata: IndependentSceneMetadataRecord
    resolution: SceneResolutionRecord
    coordinates: SceneCoordinateSystemRecord = SceneCoordinateSystemRecord()
    assets_root: Literal["assets"] = "assets"
    compatibility: IndependentSceneCompatibilityRecordV2 = (
        IndependentSceneCompatibilityRecordV2()
    )
    camera: IndependentSceneCameraRecord = IndependentSceneCameraRecord()
    root: IndependentSceneRootRecord = IndependentSceneRootRecord(name="Scene")
    objects: list[IndependentScenePrimitiveRecord] = Field(
        default_factory=list,
        max_length=MAX_PROJECT_OBJECTS,
    )

    @model_validator(mode="after")
    def validate_independent_identity(self) -> "IndependentSceneDocumentV2":
        if not self.metadata.name.strip():
            raise ValueError("scene metadata name must not be blank")
        object_ids = [item.id for item in self.objects]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("independent scene object IDs must be unique")
        return self


IndependentSceneDocument: TypeAlias = (
    IndependentSceneDocumentV1 | IndependentSceneDocumentV2
)


def default_independent_scene_metadata(
    name: str = "Untitled Scene",
) -> IndependentSceneMetadataRecord:
    """Return stable metadata for a newly created independent scene."""

    return IndependentSceneMetadataRecord(
        name=name.strip() or "Untitled Scene",
        generator=APP_DISPLAY_NAME,
        app_version=APP_VERSION,
    )


def default_independent_scene_document(
    *,
    name: str = "Untitled Scene",
    width: int = 1920,
    height: int = 1080,
) -> IndependentSceneDocumentV1:
    """Create the canonical empty scene used by New Scene."""

    return IndependentSceneDocumentV1(
        metadata=default_independent_scene_metadata(name),
        resolution=SceneResolutionRecord(width=width, height=height),
        camera=IndependentSceneCameraRecord(),
        root=IndependentSceneRootRecord(name=name.strip() or "Scene"),
    )


def default_independent_scene_document_v2(
    *,
    name: str = "Untitled Scene",
    width: int = 1920,
    height: int = 1080,
) -> IndependentSceneDocumentV2:
    """Create a new authoring-capable independent scene."""

    base = default_independent_scene_document(name=name, width=width, height=height)
    data = base.model_dump()
    data.pop("schema_version", None)
    data.pop("compatibility", None)
    return IndependentSceneDocumentV2(
        **data,
        schema_version=INDEPENDENT_SCENE_SCHEMA_VERSION_V2,
        compatibility=IndependentSceneCompatibilityRecordV2(),
        objects=[],
    )


def upgrade_independent_scene_document(
    document: IndependentSceneDocument,
) -> IndependentSceneDocumentV2:
    """Upgrade V1 in memory without mutating the original document."""

    if isinstance(document, IndependentSceneDocumentV2):
        return document
    data = document.model_dump()
    data.pop("schema_version", None)
    data.pop("compatibility", None)
    return IndependentSceneDocumentV2(
        **data,
        schema_version=INDEPENDENT_SCENE_SCHEMA_VERSION_V2,
        compatibility=IndependentSceneCompatibilityRecordV2(),
        objects=[],
    )


__all__ = [
    "INDEPENDENT_SCENE_FILE_EXTENSION",
    "INDEPENDENT_SCENE_FORMAT_ID",
    "INDEPENDENT_SCENE_SCHEMA_VERSION",
    "INDEPENDENT_SCENE_SCHEMA_VERSION_V2",
    "IndependentSceneCameraRecord",
    "IndependentSceneCompatibilityRecord",
    "IndependentSceneCompatibilityRecordV2",
    "IndependentSceneDocument",
    "IndependentSceneDocumentV1",
    "IndependentSceneDocumentV2",
    "IndependentScenePrimitiveGeometryRecord",
    "IndependentScenePrimitiveRecord",
    "IndependentScenePrimitiveTransformRecord",
    "IndependentSceneMetadataRecord",
    "IndependentSceneRootRecord",
    "SceneCoordinateSystemRecord",
    "SceneResolutionRecord",
    "default_independent_scene_document",
    "default_independent_scene_document_v2",
    "default_independent_scene_metadata",
    "upgrade_independent_scene_document",
]
