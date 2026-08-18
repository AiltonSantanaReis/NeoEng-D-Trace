"""Strict lateral scenario schema for the approved parallax MVP.

The scenario document is deliberately separate from ``.ndtproj``.  It stores
only authoring data for the future camera/parallax preview and binds itself to
one project by the SHA-256 of the exact project bytes.  In particular, its
depth field is not ``SceneObject.position.z`` and cannot change the project v1
contract implicitly.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, field_validator, model_validator

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION
from src.core.operational_limits import (
    MAX_PROJECT_FILE_BYTES,
    MAX_PROJECT_LAYERS,
    MAX_PROJECT_OBJECTS,
)

from .project_schema import (
    MAX_ID_LENGTH,
    MAX_NAME_LENGTH,
    SHA256_HEX_LENGTH,
    PointRecord,
    StrictProjectModel,
)

SCENARIO_FORMAT_ID = "neoeng-d-trace-scenario"
SCENARIO_SCHEMA_VERSION = 1
SCENARIO_FILE_EXTENSION = ".ndtscenario.json"

# These limits intentionally reuse the approved project ceilings.  They are
# explicit here so a future scenario loader cannot silently grow beyond the
# safety envelope used by the project loader.
MAX_SCENARIO_FILE_BYTES = MAX_PROJECT_FILE_BYTES
MAX_SCENARIO_LAYERS = MAX_PROJECT_LAYERS
MAX_SCENARIO_OBJECT_REFERENCES = MAX_PROJECT_OBJECTS


class ScenarioMetadataRecord(StrictProjectModel):
    """Stable metadata for a lateral scenario document."""

    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    generator: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    app_version: str = Field(min_length=1, max_length=128)


class ProjectReferenceRecord(StrictProjectModel):
    """The exact project contract and bytes a scenario was authored for."""

    format_id: Literal["neoeng-d-trace-project"] = "neoeng-d-trace-project"
    schema_version: Literal[1] = 1
    sha256: str = Field(
        min_length=SHA256_HEX_LENGTH,
        max_length=SHA256_HEX_LENGTH,
        pattern=r"^[0-9a-f]{64}$",
    )


def _finite_number(value: int | float, field: str) -> int | float:
    """Reject booleans and non-finite numbers without coercing their type."""

    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return value


def _unit_interval(value: int | float, field: str) -> int | float:
    """Validate a normalized parallax value in the inclusive unit interval."""

    number = _finite_number(value, field)
    if number < 0 or number > 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


class ScenarioCameraRecord(StrictProjectModel):
    """Persisted authoring camera state; viewport size remains runtime state."""

    position: PointRecord
    zoom: int | float = 1.0

    @field_validator("zoom")
    @classmethod
    def validate_zoom(cls, value: int | float) -> int | float:
        number = _finite_number(value, "camera.zoom")
        if number <= 0:
            raise ValueError("camera.zoom must be positive")
        return number


class ScenarioParallaxRecord(StrictProjectModel):
    """Normalized parallax parameters matching the pure camera model."""

    depth: int | float = 0.0
    translation_strength: int | float = 1.0
    zoom_strength: int | float = 1.0

    @field_validator("depth", "translation_strength", "zoom_strength")
    @classmethod
    def validate_unit_values(cls, value: int | float, info):
        return _unit_interval(value, f"parallax.{info.field_name}")


class ScenarioLayerRecord(StrictProjectModel):
    """A scenario layer and the project objects assigned to it."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(max_length=MAX_NAME_LENGTH)
    visible: bool = True
    object_ids: list[str] = Field(max_length=MAX_SCENARIO_OBJECT_REFERENCES)
    parallax: ScenarioParallaxRecord

    @field_validator("object_ids")
    @classmethod
    def validate_object_ids(cls, values: list[str]) -> list[str]:
        for object_id in values:
            if not object_id or len(object_id) > MAX_ID_LENGTH:
                raise ValueError("scenario object IDs must be non-empty")
        if len(values) != len(set(values)):
            raise ValueError("scenario object IDs must be unique within a layer")
        return values


class ScenarioDocumentV1(StrictProjectModel):
    """Approved version 1 lateral scenario contract."""

    format_id: Literal["neoeng-d-trace-scenario"] = "neoeng-d-trace-scenario"
    schema_version: Literal[1] = 1
    metadata: ScenarioMetadataRecord
    project: ProjectReferenceRecord
    camera: ScenarioCameraRecord
    layers: list[ScenarioLayerRecord] = Field(max_length=MAX_SCENARIO_LAYERS)

    @model_validator(mode="after")
    def validate_references_and_limits(self) -> "ScenarioDocumentV1":
        layer_ids = [layer.id for layer in self.layers]
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("scenario layer IDs must be unique")

        referenced_objects = [
            object_id for layer in self.layers for object_id in layer.object_ids
        ]
        if len(referenced_objects) > MAX_SCENARIO_OBJECT_REFERENCES:
            raise ValueError(
                "scenario exceeds the "
                f"{MAX_SCENARIO_OBJECT_REFERENCES} object reference limit"
            )
        if len(referenced_objects) != len(set(referenced_objects)):
            raise ValueError("scenario object references must be unique")
        return self


def default_scenario_metadata(name: str = "Scenario") -> ScenarioMetadataRecord:
    """Return stable metadata for a newly authored lateral scenario."""

    return ScenarioMetadataRecord(
        name=name,
        generator=APP_DISPLAY_NAME,
        app_version=APP_VERSION,
    )
