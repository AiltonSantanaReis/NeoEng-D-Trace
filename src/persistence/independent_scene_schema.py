"""Versioned contract for a scenario that has no image project dependency.

This contract is intentionally separate from ``ProjectDocumentV1`` and from
the legacy/project-bound scenario sidecars.  A new empty scenario is a real
document in its own right; it never receives a fabricated project reference.
Future authoring fields must be added through an explicit schema successor and
an executable migration.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, field_validator, model_validator

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION
from src.persistence.project_schema import (
    MAX_NAME_LENGTH,
    PointRecord,
    StrictProjectModel,
)

INDEPENDENT_SCENE_FORMAT_ID = "neoeng-d-trace-independent-scene"
INDEPENDENT_SCENE_SCHEMA_VERSION = 1
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


__all__ = [
    "INDEPENDENT_SCENE_FILE_EXTENSION",
    "INDEPENDENT_SCENE_FORMAT_ID",
    "INDEPENDENT_SCENE_SCHEMA_VERSION",
    "IndependentSceneCameraRecord",
    "IndependentSceneCompatibilityRecord",
    "IndependentSceneDocumentV1",
    "IndependentSceneMetadataRecord",
    "IndependentSceneRootRecord",
    "SceneCoordinateSystemRecord",
    "SceneResolutionRecord",
    "default_independent_scene_document",
    "default_independent_scene_metadata",
]
