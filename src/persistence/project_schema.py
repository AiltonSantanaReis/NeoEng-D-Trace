"""Strict versioned schema for NeoEng-D-Trace project files."""

from __future__ import annotations

import math
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.app_identity import (
    APP_DISPLAY_NAME,
    APP_VERSION,
    PROJECT_FORMAT_ID,
    PROJECT_FORMAT_VERSION,
)
from src.core.operational_limits import (
    MAX_BEZIER_SEGMENTS,
    MAX_GROUP_MEMBERS,
    MAX_POLYGON_POINTS,
)
from src.core.operational_limits import (
    MAX_PROJECT_FILE_BYTES as _MAX_PROJECT_FILE_BYTES,
)
from src.core.operational_limits import (
    MAX_PROJECT_GROUPS,
    MAX_PROJECT_LAYERS,
    MAX_PROJECT_OBJECTS,
    MAX_PROJECT_POINTS,
    MAX_PROJECT_POLYGON_COMPLEXITY,
)
from src.core.polygon_validation import is_valid_polygon

if PROJECT_FORMAT_ID != "neoeng-d-trace-project":
    raise RuntimeError("unexpected project format identifier")
if PROJECT_FORMAT_VERSION != 1:
    raise RuntimeError("unexpected project format version")

PROJECT_FILE_EXTENSION = ".ndtproj"
MAX_ID_LENGTH = 256
MAX_NAME_LENGTH = 1024
MAX_PATH_LENGTH = 32_768
SHA256_HEX_LENGTH = 64
MAX_PROJECT_FILE_BYTES = _MAX_PROJECT_FILE_BYTES


class StrictProjectModel(BaseModel):
    """Base model shared by all persisted project records."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )


class PointRecord(StrictProjectModel):
    """A finite two-dimensional coordinate."""

    x: int | float
    y: int | float

    @field_validator("x", "y")
    @classmethod
    def validate_finite_coordinate(cls, value: int | float) -> int | float:
        if isinstance(value, bool):
            raise ValueError("boolean coordinates are not allowed")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("coordinates must be finite")
        return value


class Point3Record(StrictProjectModel):
    """A finite three-dimensional coordinate used by object transforms."""

    x: int | float
    y: int | float
    z: int | float

    @field_validator("x", "y", "z")
    @classmethod
    def validate_finite_coordinate(cls, value: int | float) -> int | float:
        if isinstance(value, bool):
            raise ValueError("boolean coordinates are not allowed")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("coordinates must be finite")
        return value


class TransformRecord(StrictProjectModel):
    """Persisted position, rotation, scale and normalized pivot."""

    position: Point3Record
    rotation: Point3Record
    scale: Point3Record
    pivot: PointRecord


class BezierSegmentRecord(StrictProjectModel):
    """A cubic Bezier segment with exactly four control points."""

    p0: PointRecord
    p1: PointRecord
    p2: PointRecord
    p3: PointRecord


class ProjectMetadataRecord(StrictProjectModel):
    """Deterministic metadata that does not change between identical saves."""

    generator: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    app_version: str = Field(min_length=1, max_length=128)


class ImageReferenceRecord(StrictProjectModel):
    """External source-image reference stored without opening the image."""

    path: str = Field(min_length=1, max_length=MAX_PATH_LENGTH)
    path_kind: Literal["relative", "absolute"]
    sha256: str | None = Field(
        default=None,
        min_length=SHA256_HEX_LENGTH,
        max_length=SHA256_HEX_LENGTH,
        pattern=r"^[0-9a-f]{64}$",
    )

    @field_validator("path")
    @classmethod
    def validate_path_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("image paths cannot contain NUL bytes")
        if not value.strip():
            raise ValueError("image paths cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_path_kind(self) -> "ImageReferenceRecord":
        absolute = (
            PurePosixPath(self.path).is_absolute()
            or PureWindowsPath(self.path).is_absolute()
        )
        if self.path_kind == "absolute" and not absolute:
            raise ValueError("relative image paths cannot be marked absolute")
        if self.path_kind == "relative" and absolute:
            raise ValueError("absolute image paths cannot be marked relative")
        if self.path_kind == "relative":
            normalized_parts = PurePosixPath(self.path.replace("\\", "/")).parts
            if ".." in normalized_parts:
                raise ValueError(
                    "relative image paths cannot escape the project directory"
                )
        return self


class LayerRecord(StrictProjectModel):
    """Persisted scene layer."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(max_length=MAX_NAME_LENGTH)
    visible: bool
    locked: bool


class SceneObjectRecord(StrictProjectModel):
    """Persisted scene object, including lossless optional geometry."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    layer_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    polygon: list[PointRecord] = Field(max_length=MAX_POLYGON_POINTS)
    collision: list[PointRecord] | None = Field(
        default=None,
        max_length=MAX_POLYGON_POINTS,
    )
    collision_parts: list[list[PointRecord]] | None = Field(
        default=None,
        max_length=MAX_POLYGON_POINTS,
    )
    beziers: list[BezierSegmentRecord] | None = Field(
        default=None,
        max_length=MAX_BEZIER_SEGMENTS,
    )

    transform: TransformRecord | None = None


class GroupRecord(StrictProjectModel):
    """Persisted object group."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(max_length=MAX_NAME_LENGTH)
    visible: bool
    locked: bool
    members: list[str] = Field(max_length=MAX_GROUP_MEMBERS)

    @field_validator("members")
    @classmethod
    def validate_member_ids(cls, members: list[str]) -> list[str]:
        for member in members:
            if not member or len(member) > MAX_ID_LENGTH:
                raise ValueError("group member IDs must be non-empty")
        if len(members) != len(set(members)):
            raise ValueError("group members must be unique")
        return members


class ProjectDocumentV1(StrictProjectModel):
    """Approved NeoEng-D-Trace project-file contract version 1."""

    format_id: Literal["neoeng-d-trace-project"] = "neoeng-d-trace-project"
    schema_version: Literal[1] = 1
    metadata: ProjectMetadataRecord
    image: ImageReferenceRecord | None = None
    layers: list[LayerRecord] = Field(max_length=MAX_PROJECT_LAYERS)
    objects: list[SceneObjectRecord] = Field(max_length=MAX_PROJECT_OBJECTS)
    groups: list[GroupRecord] = Field(max_length=MAX_PROJECT_GROUPS)

    @model_validator(mode="after")
    def validate_references_and_limits(self) -> "ProjectDocumentV1":
        layer_ids = [layer.id for layer in self.layers]
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("layer IDs must be unique")
        if "layer_default" not in set(layer_ids):
            raise ValueError("layer_default is required")

        object_ids = [item.id for item in self.objects]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("object IDs must be unique")

        known_layers = set(layer_ids)
        for item in self.objects:
            if item.layer_id not in known_layers:
                raise ValueError(
                    f"object {item.id!r} references unknown layer " f"{item.layer_id!r}"
                )

        known_objects = set(object_ids)
        group_ids = [group.id for group in self.groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("group IDs must be unique")
        for group in self.groups:
            missing = [
                member for member in group.members if member not in known_objects
            ]
            if missing:
                raise ValueError(
                    f"group {group.id!r} references unknown objects: {missing!r}"
                )

        total_points = 0
        polygon_complexity = 0
        for item in self.objects:
            polygon_points = len(item.polygon)
            collision_points = len(item.collision or [])
            collision_parts_points = sum(
                len(part) for part in (item.collision_parts or [])
            )
            if polygon_points > MAX_POLYGON_POINTS:
                raise ValueError(
                    f"object {item.id!r} exceeds the {MAX_POLYGON_POINTS} "
                    "polygon point limit"
                )
            if collision_points > MAX_POLYGON_POINTS:
                raise ValueError(
                    f"object {item.id!r} exceeds the {MAX_POLYGON_POINTS} "
                    "collision point limit"
                )
            total_points += polygon_points
            total_points += collision_points
            total_points += collision_parts_points
            total_points += 4 * len(item.beziers or [])
            polygon_complexity += polygon_points * polygon_points
        if total_points > MAX_PROJECT_POINTS:
            raise ValueError(f"project exceeds the {MAX_PROJECT_POINTS} point limit")
        if polygon_complexity > MAX_PROJECT_POLYGON_COMPLEXITY:
            raise ValueError(
                "project exceeds the polygon validation complexity limit of "
                f"{MAX_PROJECT_POLYGON_COMPLEXITY}"
            )

        for item in self.objects:
            polygon = [(point.x, point.y) for point in item.polygon]
            if polygon and not is_valid_polygon(polygon):
                raise ValueError(f"object {item.id!r} has invalid polygon geometry")
            if item.collision is not None:
                collision = [(point.x, point.y) for point in item.collision]
                if not is_valid_polygon(collision):
                    raise ValueError(
                        f"object {item.id!r} has invalid collision geometry"
                    )
            for part in item.collision_parts or []:
                part_points = [(point.x, point.y) for point in part]
                if not is_valid_polygon(part_points):
                    raise ValueError(
                        f"object {item.id!r} has invalid collision part geometry"
                    )
        return self


def default_metadata() -> ProjectMetadataRecord:
    """Return stable metadata for newly serialized project documents."""

    return ProjectMetadataRecord(
        generator=APP_DISPLAY_NAME,
        app_version=APP_VERSION,
    )
