"""Versioned contract for the professional scenario authoring extension.

This contract is intentionally separate from ``ScenarioDocumentV1`` and from
the existing ``.ndtproj`` v1 document. It models authored scene objects and
their assets without changing the meaning of any existing project field.
Persistence is provided by `scene_authoring_io` and engine adapters by
`scene_authoring_export`.
"""

from __future__ import annotations

import math
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION
from src.core.operational_limits import (
    MAX_GROUP_MEMBERS,
    MAX_PROJECT_GROUPS,
    MAX_PROJECT_LAYERS,
    MAX_PROJECT_OBJECTS,
    MAX_POLYGON_POINTS,
)
from src.core.polygon_validation import is_valid_polygon
from src.persistence.project_schema import (
    MAX_ID_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PATH_LENGTH,
    Point3Record,
    PointRecord,
    StrictProjectModel,
)
from src.persistence.scenario_schema import ProjectReferenceRecord

SCENE_AUTHORING_FORMAT_ID = "neoeng-d-trace-scene-authoring"
SCENE_AUTHORING_SCHEMA_VERSION = 1
SCENE_AUTHORING_FILE_EXTENSION = ".ndtscene.json"
MAX_SCENE_ASSETS = MAX_PROJECT_OBJECTS
MAX_SCENE_SOCKETS = MAX_PROJECT_OBJECTS


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


def _bounded(
    value: int | float,
    field: str,
    lower: float,
    upper: float,
) -> int | float:
    number = _finite(value, field)
    if number < lower or number > upper:
        raise ValueError(f"{field} must be between {lower} and {upper}")
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
    # Optional non-portable provenance; never used to resolve project assets.
    source_path: str | None = Field(default=None, max_length=MAX_PATH_LENGTH)

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or chr(0) in value):
            raise ValueError("asset source path must be non-empty and NUL-free")
        return value

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


class SceneMaterialAuthoringRecord(StrictProjectModel):
    """Persisted material inputs consumed by the deterministic raster pass."""

    albedo: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    normal_map_xy: PointRecord = PointRecord(x=0.0, y=0.0)
    normal_strength: int | float = 1.0
    emission: str = Field(default="#000000", pattern=r"^#[0-9a-fA-F]{6}$")
    emission_strength: int | float = 0.0
    opacity: int | float = 1.0
    receives_shadow: bool = True
    casts_shadow: bool = True

    @field_validator("albedo", "emission")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        return value.lower()

    @field_validator("normal_map_xy")
    @classmethod
    def validate_normal_map(cls, value: PointRecord) -> PointRecord:
        _bounded(value.x, "material.normal_map_xy.x", -1.0, 1.0)
        _bounded(value.y, "material.normal_map_xy.y", -1.0, 1.0)
        return value

    @field_validator("normal_strength", "opacity")
    @classmethod
    def validate_unit_material_values(cls, value: int | float) -> int | float:
        return _unit(value, "material unit value")

    @field_validator("emission_strength")
    @classmethod
    def validate_emission_strength(cls, value: int | float) -> int | float:
        return _bounded(value, "material.emission_strength", 0.0, 16.0)


class SceneVectorImageSizeRecord(StrictProjectModel):
    """Decoded source dimensions retained with a vectorized object."""

    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)


class SceneVectorGeometryRecord(StrictProjectModel):
    """Portable vector geometry plus source/detection provenance."""

    algorithm: str = Field(min_length=1, max_length=128)
    source_sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    image_size: SceneVectorImageSizeRecord
    original_polygon: list[PointRecord] = Field(
        min_length=3, max_length=MAX_POLYGON_POINTS
    )
    polygon: list[PointRecord] = Field(min_length=3, max_length=MAX_POLYGON_POINTS)
    collision_polygon: list[PointRecord] = Field(
        min_length=3, max_length=MAX_POLYGON_POINTS
    )
    detection_parameters: dict[str, str | int | float | bool] = Field(
        default_factory=dict
    )

    @model_validator(mode="after")
    def validate_geometry(self) -> "SceneVectorGeometryRecord":
        for name, points in (
            ("original_polygon", self.original_polygon),
            ("polygon", self.polygon),
            ("collision_polygon", self.collision_polygon),
        ):
            if not is_valid_polygon([(point.x, point.y) for point in points]):
                raise ValueError(f"vector geometry {name} must be a valid polygon")
        for key, value in self.detection_parameters.items():
            if not key.strip() or len(key) > 128:
                raise ValueError("vector detection parameter names must be non-empty")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("vector detection parameters must be finite")
        return self


class SceneObjectAuthoringRecord(StrictProjectModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    asset_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    layer_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    transform: SceneTransformRecord
    visible: bool = True
    locked: bool = False
    vector_geometry: SceneVectorGeometryRecord | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    material: SceneMaterialAuthoringRecord | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


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


class SceneGroupAuthoringRecordV2(SceneGroupAuthoringRecord):
    """V2 group record with optional nested-group parentage."""

    parent_group_id: str | None = Field(default=None, max_length=MAX_ID_LENGTH)


class SceneComponentAuthoringRecord(StrictProjectModel):
    """Versioned, data-only component attached to one authored entity."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    type: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    version: int = Field(ge=1, le=10_000)
    properties: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_property_values(self) -> "SceneComponentAuthoringRecord":
        for key, value in self.properties.items():
            if not key.strip() or len(key) > MAX_NAME_LENGTH:
                raise ValueError("component property names must be non-empty")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("component property numbers must be finite")
        return self


class SceneEntityAuthoringRecord(StrictProjectModel):
    """Stable authored identity with typed components and optional instance source."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    layer_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    transform: SceneTransformRecord
    components: list[SceneComponentAuthoringRecord] = Field(
        default_factory=list, max_length=MAX_PROJECT_OBJECTS
    )
    instance_of: str | None = Field(default=None, max_length=MAX_ID_LENGTH)
    parent_entity_id: str | None = Field(default=None, max_length=MAX_ID_LENGTH)
    visible: bool = True
    locked: bool = False

    @model_validator(mode="after")
    def validate_component_identity(self) -> "SceneEntityAuthoringRecord":
        component_ids = [component.id for component in self.components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("entity component IDs must be unique")
        if self.instance_of == self.id:
            raise ValueError("entity cannot instance itself")
        if self.parent_entity_id == self.id:
            raise ValueError("entity cannot parent itself")
        return self


class ScenePrefabOverrideRecord(StrictProjectModel):
    """Scalar override kept separate from the prefab source definition."""

    path: str = Field(min_length=1, max_length=MAX_PATH_LENGTH)
    value: str | int | float | bool | None

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | int | float | bool | None):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("prefab override numbers must be finite")
        return value


class ScenePrefabAuthoringRecord(StrictProjectModel):
    """Versioned prefab asset referencing a stable source entity selection."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    source_entity_ids: list[str] = Field(min_length=1, max_length=MAX_PROJECT_OBJECTS)
    version: int = Field(default=1, ge=1, le=10_000)

    @field_validator("source_entity_ids")
    @classmethod
    def validate_source_ids(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("prefab source entity IDs must be non-empty")
        if len(values) != len(set(values)):
            raise ValueError("prefab source entity IDs must be unique")
        return values


class ScenePrefabInstanceAuthoringRecord(StrictProjectModel):
    """Independent prefab instance identity with explicit overrides."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    prefab_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    root_entity_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    overrides: list[ScenePrefabOverrideRecord] = Field(
        default_factory=list, max_length=MAX_PROJECT_OBJECTS
    )
    detached: bool = False

    @model_validator(mode="after")
    def validate_overrides(self) -> "ScenePrefabInstanceAuthoringRecord":
        paths = [override.path for override in self.overrides]
        if len(paths) != len(set(paths)):
            raise ValueError("prefab override paths must be unique")
        return self


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


class SceneCameraAuthoringRecord(StrictProjectModel):
    """Camera state used only by the professional scenario authoring view."""

    position: PointRecord = PointRecord(x=0.0, y=0.0)
    zoom: int | float = 1.0
    rotation: int | float = 0.0

    @field_validator("position")
    @classmethod
    def validate_position(cls, value: PointRecord) -> PointRecord:
        _finite(value.x, "camera.position.x")
        _finite(value.y, "camera.position.y")
        return value

    @field_validator("zoom")
    @classmethod
    def validate_zoom(cls, value: int | float) -> int | float:
        return _positive(value, "camera.zoom")

    @field_validator("rotation")
    @classmethod
    def validate_rotation(cls, value: int | float) -> int | float:
        return _bounded(value, "camera.rotation", -36000.0, 36000.0)


class SceneParallaxLayerRecord(StrictProjectModel):
    """Versioned layer parameters for deterministic professional preview.

    The original depth/strength fields remain unchanged.  E08-B adds signed
    axis-specific scroll and manual offsets with defaults that reproduce the
    previous projection exactly; repeat/mirror flags are explicit render
    metadata and never reinterpret ``position.z``.
    """

    layer_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    depth: int | float = 0.0
    translation_strength: int | float = 1.0
    zoom_strength: int | float = 1.0
    scroll_x: int | float = 1.0
    scroll_y: int | float = 1.0
    offset_x: int | float = 0.0
    offset_y: int | float = 0.0
    repeat_x: bool = False
    repeat_y: bool = False
    mirror_x: bool = False
    mirror_y: bool = False

    @field_validator("depth", "translation_strength", "zoom_strength")
    @classmethod
    def validate_normalized(cls, value: int | float) -> int | float:
        return _unit(value, "parallax parameter")

    @field_validator("scroll_x", "scroll_y")
    @classmethod
    def validate_scroll(cls, value: int | float, info) -> int | float:
        return _bounded(value, f"parallax.{info.field_name}", -4.0, 4.0)

    @field_validator("offset_x", "offset_y")
    @classmethod
    def validate_offset(cls, value: int | float, info) -> int | float:
        return _finite(value, f"parallax.{info.field_name}")


class _SceneSocketBase(StrictProjectModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    layer_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    object_id: str | None = Field(default=None, max_length=MAX_ID_LENGTH)
    position: Point3Record
    # Optional in the wire contract so documents created before orientable
    # sockets remain valid.  Z is the 2D authoring heading; X/Y are reserved
    # for the hybrid 2.5D/3D editor without changing the socket identity.
    rotation: Point3Record = Field(
        default_factory=lambda: Point3Record(x=0.0, y=0.0, z=0.0)
    )

    @field_validator("position", "rotation")
    @classmethod
    def validate_transform(cls, value: Point3Record) -> Point3Record:
        for coordinate in (value.x, value.y, value.z):
            _finite(coordinate, "socket transform")
        return value


class SceneLightSocketRecord(_SceneSocketBase):
    type: Literal["light"] = "light"
    # ``point`` is the legacy default.  Directional lights use the socket
    # rotation Z angle as the incoming light vector in screen space.
    kind: Literal["point", "directional"] = "point"
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    intensity: int | float = 1.0
    radius: int | float = 64.0

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        return value.lower()

    @field_validator("intensity", "radius")
    @classmethod
    def validate_positive_values(cls, value: int | float) -> int | float:
        return _positive(value, "light socket value")


class SceneVfxSocketRecord(_SceneSocketBase):
    type: Literal["vfx"] = "vfx"
    effect_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    scale: int | float = 1.0
    enabled: bool = True

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, value: int | float) -> int | float:
        return _positive(value, "VFX socket scale")


class SceneTriggerSocketRecord(_SceneSocketBase):
    type: Literal["trigger"] = "trigger"
    event_id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    size: Point3Record

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: Point3Record) -> Point3Record:
        for coordinate in (value.x, value.y, value.z):
            _positive(coordinate, "trigger socket size")
        return value


SceneSocketRecord: TypeAlias = Annotated[
    SceneLightSocketRecord | SceneVfxSocketRecord | SceneTriggerSocketRecord,
    Field(discriminator="type"),
]


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


from src.persistence.scene_sequence_schema import SceneSequence


class SceneAuthoringDocumentV2(StrictProjectModel):
    """Professional scenario contract with camera, parallax and sockets.

    Version 1 remains unchanged and readable. V2 repeats the stable V1 fields
    explicitly so the two contracts remain statically and dynamically distinct.
    """

    format_id: Literal["neoeng-d-trace-scene-authoring"] = (
        "neoeng-d-trace-scene-authoring"
    )
    schema_version: Literal[2] = 2
    sequence: SceneSequence | None = Field(default=None, exclude_if=lambda value: value is None)
    metadata: SceneAuthoringMetadataRecord
    project: ProjectReferenceRecord
    assets: list[AssetReferenceRecord] = Field(max_length=MAX_SCENE_ASSETS)
    layers: list[SceneLayerAuthoringRecord] = Field(max_length=MAX_PROJECT_LAYERS)
    objects: list[SceneObjectAuthoringRecord] = Field(max_length=MAX_PROJECT_OBJECTS)
    groups: list[SceneGroupAuthoringRecordV2] = Field(max_length=MAX_PROJECT_GROUPS)
    entities: list[SceneEntityAuthoringRecord] = Field(
        default_factory=list,
        max_length=MAX_PROJECT_OBJECTS,
        exclude_if=lambda value: not value,
    )
    prefabs: list[ScenePrefabAuthoringRecord] = Field(
        default_factory=list,
        max_length=MAX_PROJECT_OBJECTS,
        exclude_if=lambda value: not value,
    )
    prefab_instances: list[ScenePrefabInstanceAuthoringRecord] = Field(
        default_factory=list,
        max_length=MAX_PROJECT_OBJECTS,
        exclude_if=lambda value: not value,
    )
    snap: SceneSnapRecord = SceneSnapRecord()
    camera: SceneCameraAuthoringRecord = SceneCameraAuthoringRecord()
    parallax_layers: list[SceneParallaxLayerRecord] = Field(
        default_factory=list, max_length=MAX_PROJECT_LAYERS
    )
    sockets: list[SceneSocketRecord] = Field(
        default_factory=list, max_length=MAX_SCENE_SOCKETS
    )

    @model_validator(mode="after")
    def validate_references(self) -> "SceneAuthoringDocumentV2":
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
        entity_ids = [item.id for item in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("entity IDs must be unique")
        known_entities = set(entity_ids)
        prefab_ids = [item.id for item in self.prefabs]
        if len(prefab_ids) != len(set(prefab_ids)):
            raise ValueError("prefab IDs must be unique")
        known_prefabs = set(prefab_ids)
        for prefab in self.prefabs:
            missing_sources = [
                source_id
                for source_id in prefab.source_entity_ids
                if source_id not in known_entities
            ]
            if missing_sources:
                raise ValueError(
                    f"prefab {prefab.id!r} references unknown source entity"
                )
        instance_ids = [item.id for item in self.prefab_instances]
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("prefab instance IDs must be unique")
        if set(instance_ids) & known_entities:
            raise ValueError("prefab instance IDs must not collide with entity IDs")
        for instance in self.prefab_instances:
            if instance.prefab_id not in known_prefabs:
                raise ValueError(
                    f"prefab instance {instance.id!r} references unknown prefab"
                )
            if instance.root_entity_id not in known_entities:
                raise ValueError(
                    f"prefab instance {instance.id!r} references unknown root entity"
                )
        for entity in self.entities:
            if entity.layer_id not in known_layers:
                raise ValueError(
                    f"entity {entity.id!r} references unknown layer {entity.layer_id!r}"
                )
            if (
                entity.instance_of is not None
                and entity.instance_of not in known_entities
            ):
                raise ValueError(
                    f"entity {entity.id!r} references unknown source entity"
                )
            if (
                entity.parent_entity_id is not None
                and entity.parent_entity_id not in known_entities
            ):
                raise ValueError(
                    f"entity {entity.id!r} references unknown parent entity"
                )
            seen = {entity.id}
            entity_current = entity.parent_entity_id
            while entity_current is not None:
                if entity_current in seen:
                    raise ValueError("entity hierarchy contains a cycle")
                seen.add(entity_current)
                entity_parent = next(
                    item for item in self.entities if item.id == entity_current
                )
                entity_current = entity_parent.parent_entity_id
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
        group_by_id = {item.id: item for item in self.groups}
        for group in self.groups:
            parent_id = group.parent_group_id
            if parent_id is None:
                continue
            if parent_id not in group_by_id:
                raise ValueError(
                    f"group {group.id!r} references unknown parent group {parent_id!r}"
                )
            seen = {group.id}
            group_current: str | None = parent_id
            while group_current is not None:
                if group_current in seen:
                    raise ValueError("group hierarchy contains a cycle")
                seen.add(group_current)
                parent = group_by_id.get(group_current)
                if parent is None:
                    raise ValueError(
                        f"group hierarchy references unknown parent {group_current!r}"
                    )
                group_current = parent.parent_group_id
        parallax_ids = [item.layer_id for item in self.parallax_layers]
        if len(parallax_ids) != len(set(parallax_ids)):
            raise ValueError("parallax layer IDs must be unique")
        for layer_id in parallax_ids:
            if layer_id not in known_layers:
                raise ValueError(f"parallax references unknown layer {layer_id!r}")
        socket_ids = [item.id for item in self.sockets]
        if self.sequence is not None:
            for clip in self.sequence.clips:
                if clip.target_id is not None and clip.target_id not in known_objects:
                    raise ValueError(f"clip {clip.name!r}: remove or relink its object track first")
                if clip.layer_id is not None and clip.layer_id not in known_layers:
                    raise ValueError(f"clip {clip.name!r} references unknown layer")
                if clip.asset_id is not None and clip.asset_id not in known_assets:
                    raise ValueError(f"clip {clip.name!r} references unknown asset")
        if len(socket_ids) != len(set(socket_ids)):
            raise ValueError("socket IDs must be unique")
        for socket in self.sockets:
            if socket.layer_id not in known_layers:
                raise ValueError(f"socket references unknown layer {socket.layer_id!r}")
            if socket.object_id is not None and socket.object_id not in known_objects:
                raise ValueError(
                    f"socket references unknown object {socket.object_id!r}"
                )
        return self


SceneAuthoringDocument: TypeAlias = SceneAuthoringDocumentV1 | SceneAuthoringDocumentV2


def validate_scene_authoring_document(value: object) -> SceneAuthoringDocument:
    """Validate and preserve the explicit schema version of a scene document."""

    if isinstance(value, SceneAuthoringDocumentV2):
        return SceneAuthoringDocumentV2.model_validate(value, strict=True)
    if isinstance(value, SceneAuthoringDocumentV1):
        if value.schema_version != 1:
            raise ValueError("unsupported scene authoring schema version")
        return SceneAuthoringDocumentV1.model_validate(value, strict=True)
    if not isinstance(value, dict):
        raise TypeError("scene authoring document must be a mapping or versioned model")
    version = value.get("schema_version", 1)
    if version == 2:
        return SceneAuthoringDocumentV2.model_validate(value, strict=True)
    if version == 1:
        return SceneAuthoringDocumentV1.model_validate(value, strict=True)
    raise ValueError(f"unsupported scene authoring schema version {version!r}")


def upgrade_scene_authoring_document(
    value: SceneAuthoringDocumentV1 | SceneAuthoringDocumentV2,
) -> SceneAuthoringDocumentV2:
    """Create an explicit V2 document without changing V1 in place."""

    if isinstance(value, SceneAuthoringDocumentV2):
        return value
    data = value.model_dump()
    data["schema_version"] = 2
    data.update(
        camera=SceneCameraAuthoringRecord(),
        parallax_layers=[],
        sockets=[],
    )
    return SceneAuthoringDocumentV2(**data)
