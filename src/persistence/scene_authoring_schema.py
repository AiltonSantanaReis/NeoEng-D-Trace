"""Versioned contract for the professional scenario authoring extension.

This contract is intentionally separate from ``ScenarioDocumentV1`` and from
the existing ``.ndtproj`` v1 document. It models authored scene objects and
their assets without changing the meaning of any existing project field.
Persistence and engine adapters are implemented in later plan stages.
"""

from __future__ import annotations

import math
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal

from pydantic import Field, field_validator, model_validator

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION
from src.core.operational_limits import (
    MAX_GROUP_MEMBERS,
    MAX_PROJECT_GROUPS,
    MAX_PROJECT_LAYERS,
    MAX_PROJECT_OBJECTS,
)
from src.persistence.project_schema import (
    MAX_ID_LENGTH,
    MAX_NAME_LENGTH,
    Point3Record,
    PointRecord,
    StrictProjectModel,
)
from src.persistence.scenario_schema import ProjectReferenceRecord

SCENE_AUTHORING_FORMAT_ID = "neoeng-d-trace-scene-authoring"
SCENE_AUTHORING_SCHEMA_VERSION = 1
SCENE_AUTHORING_FILE_EXTENSION = ".ndtscene.json"
MAX_SCENE_ASSETS = MAX_PROJECT_OBJECTS


def _finite(value: int | float, field: str) -> int | float:
    if isinstance(value, bool) or (
        isinstance(value, float) and not math.isfinite(value)
    ):
        raise ValueError(f"{field} must be a finite number")
    return value


def _positive(value: int | float, field: str) -> int | float:
    number = _finite(value, field)
    if number <= 0:
        raise ValueError(f"{field} must be positive")
    return number


def _unit(value: int | float, field: str) -> int | float:
    number = _finite(value, field)
    if number < 0 or number > 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


class SceneAuthoringMetadataRecord(StrictProjectModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    generator: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    app_version: str = Field(min_length=1, max_length=128)


class AssetReferenceRecord(StrictProjectModel):
    """Portable, hash-verifiable reference to an authored scene asset."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    path: str = Field(min_length=1, max_length=32_768)
    path_kind: Literal["relative"] = "relative"
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        if "\x00" in value or "\\" in value:
            raise ValueError("asset paths must use portable POSIX separators")
        if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
            raise ValueError("asset paths must be relative")
        if not value.strip() or ".." in PurePosixPath(value).parts:
            raise ValueError("asset paths cannot be blank or escape the project")
        return value


class SceneTransformRecord(StrictProjectModel):
    """Full transform used by the authoring viewport."""

    position: Point3Record
    rotation: Point3Record
    scale: Point3Record
    pivot: PointRecord
    flip_x: bool = False
    flip_y: bool = False

    @field_validator("position", "rotation")
    @classmethod
    def validate_vectors(cls, value: Point3Record):
        for coordinate in (value.x, value.y, value.z):
            _finite(coordinate, "transform coordinate")
        return value

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, value: Point3Record):
        for name, coordinate in (("x", value.x), ("y", value.y), ("z", value.z)):
            _positive(coordinate, f"transform.scale.{name}")
        return value

    @field_validator("pivot")
    @classmethod
    def validate_pivot(cls, value: PointRecord):
        _unit(value.x, "transform.pivot.x")
        _unit(value.y, "transform.pivot.y")
        return value


class SceneLayerAuthoringRecord(StrictProjectModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    visible: bool = True
    locked: bool = False


class SceneObjectAuthoringRecord(StrictProjectModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    asset_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    layer_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    transform: SceneTransformRecord
    visible: bool = True
    locked: bool = False


class SceneGroupAuthoringRecord(StrictProjectModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    members: list[str] = Field(max_length=MAX_GROUP_MEMBERS)
    visible: bool = True
    locked: bool = False

    @field_validator("members")
    @classmethod
    def validate_members(cls, values: list[str]) -> list[str]:
        if any(not value or len(value) > MAX_ID_LENGTH for value in values):
            raise ValueError("group members must be non-empty object IDs")
        if len(values) != len(set(values)):
            raise ValueError("group members must be unique")
        return values


class SceneSnapRecord(StrictProjectModel):
    enabled: bool = False
    mode: Literal["pixel", "grid"] = "pixel"
    spacing: PointRecord = PointRecord(x=1.0, y=1.0)

    @field_validator("spacing")
    @classmethod
    def validate_spacing(cls, value: PointRecord):
        _positive(value.x, "snap.spacing.x")
        _positive(value.y, "snap.spacing.y")
        return value


class SceneAuthoringDocumentV1(StrictProjectModel):
    """Professional authored scene contract, version 1."""

    format_id: Literal["neoeng-d-trace-scene-authoring"] = (
        "neoeng-d-trace-scene-authoring"
    )
    schema_version: Literal[1] = 1
    metadata: SceneAuthoringMetadataRecord
    project: ProjectReferenceRecord
    assets: list[AssetReferenceRecord] = Field(max_length=MAX_SCENE_ASSETS)
    layers: list[SceneLayerAuthoringRecord] = Field(max_length=MAX_PROJECT_LAYERS)
    objects: list[SceneObjectAuthoringRecord] = Field(max_length=MAX_PROJECT_OBJECTS)
    groups: list[SceneGroupAuthoringRecord] = Field(max_length=MAX_PROJECT_GROUPS)
    snap: SceneSnapRecord = SceneSnapRecord()

    @model_validator(mode="after")
    def validate_references(self) -> "SceneAuthoringDocumentV1":
        id_sets = (
            ("asset", [item.id for item in self.assets]),
            ("layer", [item.id for item in self.layers]),
            ("object", [item.id for item in self.objects]),
            ("group", [item.id for item in self.groups]),
        )
        for label, values in id_sets:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")

        known_assets = {item.id for item in self.assets}
        known_layers = {item.id for item in self.layers}
        known_objects = {item.id for item in self.objects}
        for item in self.objects:
            if item.asset_id not in known_assets:
                raise ValueError(f"object {item.id!r} references unknown asset")
            if item.layer_id not in known_layers:
                raise ValueError(f"object {item.id!r} references unknown layer")
        for group in self.groups:
            missing = [
                member for member in group.members if member not in known_objects
            ]
            if missing:
                raise ValueError(
                    f"group {group.id!r} references unknown object {missing[0]!r}"
                )
        return self


def default_scene_authoring_metadata(
    name: str = "Scene",
) -> SceneAuthoringMetadataRecord:
    return SceneAuthoringMetadataRecord(
        name=name,
        generator=APP_DISPLAY_NAME,
        app_version=APP_VERSION,
    )
