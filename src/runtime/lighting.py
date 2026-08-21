"""Versioned deterministic lighting and material runtime for scene manifests.

The lighting contract is a sidecar to the existing scenario runtime export.
It binds to exact scenario-runtime bytes by SHA-256 and does not reinterpret
the approved scenario schema v1. The preview is bounded structural feedback,
not a replacement for an engine renderer.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_schema import Point3Record, StrictProjectModel

LIGHTING_FORMAT_ID = "neoeng-d-trace-runtime-lighting"
LIGHTING_SCHEMA_VERSION = 1
LIGHTING_API_VERSION = 1
LIGHTING_SOURCE_FORMAT_ID = "neoeng-d-trace-scenario-runtime"
LIGHTING_SOURCE_SCHEMA_VERSION = 1
MAX_LIGHTING_ID_LENGTH = 128
MAX_LIGHTS = 4_096
MAX_MATERIALS = 4_096
MAX_BINDINGS = 100_000
MAX_SOCKETS = 100_000
MAX_LIGHT_INTENSITY = 1_000.0
MAX_LIGHT_RANGE = 1_000_000.0


class LightingRuntimeError(ValueError):
    """Base class for controlled lighting contract failures."""


class LightingFormatError(LightingRuntimeError):
    """Raised when lighting bytes are not canonical UTF-8 JSON."""


class LightingValidationError(LightingRuntimeError):
    """Raised when a lighting document violates its versioned contract."""


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _bounded(value: float, field: str, minimum: float, maximum: float) -> float:
    number = _finite(value, field)
    if number < minimum or number > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return number


class LightingColorRecord(StrictProjectModel):
    """Linear RGB colour with components in the closed unit interval."""

    r: float
    g: float
    b: float

    @field_validator("r", "g", "b")
    @classmethod
    def validate_component(cls, value: float, info) -> float:
        return _bounded(value, f"color.{info.field_name}", 0.0, 1.0)


class LightingSourceBindingRecord(StrictProjectModel):
    """Exact runtime scenario export to which this sidecar is bound."""

    format_id: Literal["neoeng-d-trace-scenario-runtime"] = (
        "neoeng-d-trace-scenario-runtime"
    )
    schema_version: Literal[1] = 1
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class AmbientLightRecord(StrictProjectModel):
    """Scene-wide ambient contribution."""

    color: LightingColorRecord
    intensity: float = 0.0

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, value: float) -> float:
        return _bounded(value, "ambient.intensity", 0.0, 1.0)


class LightingSourceRecord(StrictProjectModel):
    """A deterministic point, directional or spot light."""

    id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)
    kind: Literal["point", "directional", "spot"]
    enabled: bool = True
    color: LightingColorRecord
    intensity: float = 1.0
    position: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0)
    direction_degrees: float = 0.0
    range: float = 100.0
    cone_angle_degrees: float = 45.0

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, value: float) -> float:
        return _bounded(value, "light.intensity", 0.0, MAX_LIGHT_INTENSITY)

    @field_validator("direction_degrees")
    @classmethod
    def validate_direction(cls, value: float) -> float:
        return _finite(value, "light.direction_degrees")

    @field_validator("range")
    @classmethod
    def validate_range(cls, value: float) -> float:
        return _bounded(value, "light.range", 0.000001, MAX_LIGHT_RANGE)

    @field_validator("cone_angle_degrees")
    @classmethod
    def validate_cone(cls, value: float) -> float:
        return _bounded(value, "light.cone_angle_degrees", 0.000001, 180.0)


class MaterialRecord(StrictProjectModel):
    """Bounded material parameters consumed by the deterministic preview."""

    id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)
    lighting_mode: Literal["lit", "unlit"] = "lit"
    albedo: LightingColorRecord
    emission: LightingColorRecord
    emission_strength: float = 0.0
    opacity: float = 1.0

    @field_validator("emission_strength")
    @classmethod
    def validate_emission_strength(cls, value: float) -> float:
        return _bounded(value, "material.emission_strength", 0.0, MAX_LIGHT_INTENSITY)

    @field_validator("opacity")
    @classmethod
    def validate_opacity(cls, value: float) -> float:
        return _bounded(value, "material.opacity", 0.0, 1.0)


class MaterialBindingRecord(StrictProjectModel):
    """Maps an authored object identifier to one material."""

    object_id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)
    material_id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)


class LightSocketRecord(StrictProjectModel):
    """Authoring marker that resolves a light source to an object position."""

    id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)
    object_id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)
    source_id: str = Field(min_length=1, max_length=MAX_LIGHTING_ID_LENGTH)
    position: Point3Record
    enabled: bool = True


class LightingDocumentV1(StrictProjectModel):
    """Complete version 1 lighting/material sidecar contract."""

    format_id: Literal["neoeng-d-trace-runtime-lighting"] = (
        "neoeng-d-trace-runtime-lighting"
    )
    schema_version: Literal[1] = 1
    source: LightingSourceBindingRecord
    ambient: AmbientLightRecord
    lights: list[LightingSourceRecord] = Field(max_length=MAX_LIGHTS)
    materials: list[MaterialRecord] = Field(max_length=MAX_MATERIALS)
    material_bindings: list[MaterialBindingRecord] = Field(max_length=MAX_BINDINGS)
    sockets: list[LightSocketRecord] = Field(max_length=MAX_SOCKETS)

    @model_validator(mode="after")
    def validate_references(self) -> "LightingDocumentV1":
        light_ids = [light.id for light in self.lights]
        material_ids = [material.id for material in self.materials]
        socket_ids = [socket.id for socket in self.sockets]
        if len(light_ids) != len(set(light_ids)):
            raise ValueError("lighting source IDs must be unique")
        if len(material_ids) != len(set(material_ids)):
            raise ValueError("material IDs must be unique")
        if len(socket_ids) != len(set(socket_ids)):
            raise ValueError("light socket IDs must be unique")
        if any(
            binding.material_id not in material_ids
            for binding in self.material_bindings
        ):
            raise ValueError("material binding references an unknown material")
        if any(socket.source_id not in light_ids for socket in self.sockets):
            raise ValueError("light socket references an unknown source")
        object_ids = [binding.object_id for binding in self.material_bindings]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("material object bindings must be unique")
        return self


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LightingValidationError(
            f"lighting document cannot be serialized: {exc}"
        ) from exc
    return (text + "\n").encode("utf-8")


def _validated_document(payload: object) -> LightingDocumentV1:
    if not isinstance(payload, Mapping):
        if isinstance(payload, LightingDocumentV1):
            return payload.model_copy(deep=True)
        raise LightingValidationError("lighting document root must be an object")
    try:
        return LightingDocumentV1.model_validate(payload, strict=True)
    except Exception as exc:
        raise LightingValidationError(str(exc)) from exc


def build_lighting_runtime_export(document: LightingDocumentV1) -> dict[str, Any]:
    """Validate and copy a lighting sidecar for deterministic export."""

    return _validated_document(document).model_dump(mode="json")


def serialize_lighting_runtime_export(document: LightingDocumentV1) -> bytes:
    """Serialize the lighting sidecar as canonical UTF-8 JSON."""

    payload = build_lighting_runtime_export(document)
    serialized = _canonical_json_bytes(payload)
    if len(serialized) > MAX_PROJECT_FILE_BYTES:
        raise LightingValidationError("lighting document exceeds file limit")
    return serialized


def lighting_runtime_export_sha256(document: LightingDocumentV1) -> str:
    """Return the hash of the exact canonical lighting bytes."""

    return hashlib.sha256(serialize_lighting_runtime_export(document)).hexdigest()


def validate_lighting_runtime_export(payload: Mapping[str, Any]) -> LightingDocumentV1:
    """Strictly validate a decoded lighting payload."""

    return _validated_document(payload)


def save_lighting_runtime_export(
    document: LightingDocumentV1,
    path: str | os.PathLike[str],
) -> None:
    """Atomically replace one lighting sidecar."""

    destination = Path(path)
    if not destination.parent.is_dir():
        raise LightingValidationError("lighting export directory does not exist")
    if destination.exists() and destination.is_dir():
        raise LightingValidationError("lighting export destination is a directory")
    payload = serialize_lighting_runtime_export(document)
    try:
        with AtomicOutputTransaction() as transaction:
            staged = Path(transaction.stage_path(str(destination)))
            with staged.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            transaction.commit()
    except OSError as exc:
        raise LightingValidationError(f"failed to save lighting export: {exc}") from exc


def verify_lighting_source_binding(
    document: LightingDocumentV1,
    source_bytes: bytes,
) -> None:
    """Verify that the sidecar is bound to the exact scenario bytes."""

    validated = _validated_document(document)
    if not isinstance(source_bytes, bytes):
        raise LightingValidationError("source_bytes must be bytes")
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != validated.source.sha256:
        raise LightingValidationError("lighting source hash does not match")


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _read_lighting_file(path: Path) -> LightingDocumentV1:
    if not path.exists() or not path.is_file():
        raise LightingFormatError(f"lighting manifest not found: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise LightingFormatError(f"lighting manifest cannot be read: {exc}") from exc
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise LightingFormatError("lighting manifest exceeds file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise LightingFormatError("UTF-8 BOM is not allowed")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as exc:
        raise LightingFormatError(f"invalid lighting JSON: {exc}") from exc
    document = _validated_document(payload)
    if raw != serialize_lighting_runtime_export(document):
        raise LightingFormatError("lighting manifest bytes are not canonical")
    return document


def load_lighting_runtime_export_bytes(raw: bytes) -> LightingDocumentV1:
    """Load canonical lighting sidecar bytes with strict JSON checks."""

    if not isinstance(raw, bytes):
        raise LightingFormatError("lighting manifest bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise LightingFormatError("lighting manifest exceeds file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise LightingFormatError("UTF-8 BOM is not allowed")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as exc:
        raise LightingFormatError(f"invalid lighting JSON: {exc}") from exc
    document = _validated_document(payload)
    if raw != serialize_lighting_runtime_export(document):
        raise LightingFormatError("lighting manifest bytes are not canonical")
    return document


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _angle_delta(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


def _rounded_color(values: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        round(_clamp(values[0]), 12),
        round(_clamp(values[1]), 12),
        round(_clamp(values[2]), 12),
    )


@dataclass(frozen=True)
class LightingPreview:
    """Deterministic structural preview result for one object sample."""

    color: tuple[float, float, float]
    opacity: float
    material_id: str | None
    contributing_light_ids: tuple[str, ...]


class LightingRuntime:
    """Atomic lighting sidecar loader and deterministic preview evaluator."""

    def __init__(self) -> None:
        self._document: LightingDocumentV1 | None = None

    @property
    def document(self) -> LightingDocumentV1 | None:
        return self._document

    def manifest_copy(self) -> dict[str, Any] | None:
        return (
            copy.deepcopy(self._document.model_dump(mode="json"))
            if self._document is not None
            else None
        )

    def load_manifest(
        self,
        payload: Mapping[str, Any],
        *,
        source_bytes: bytes | None = None,
    ) -> LightingDocumentV1:
        """Validate first and replace the active sidecar only on success."""

        candidate = _validated_document(payload)
        if source_bytes is not None:
            verify_lighting_source_binding(candidate, source_bytes)
        self._document = candidate
        return candidate

    def load_file(self, path: str | os.PathLike[str]) -> LightingDocumentV1:
        """Load canonical bytes and preserve the previous document on failure."""

        candidate = _read_lighting_file(Path(path))
        self._document = candidate
        return candidate

    def _material_for(self, object_id: str | None) -> MaterialRecord | None:
        if self._document is None or object_id is None:
            return None
        material_ids = {
            binding.material_id
            for binding in self._document.material_bindings
            if binding.object_id == object_id
        }
        return next(
            (
                material
                for material in self._document.materials
                if material.id in material_ids
            ),
            None,
        )

    @staticmethod
    def _source_factor(source: LightingSourceRecord, position: Point3Record) -> float:
        if not source.enabled or source.intensity <= 0:
            return 0.0
        if source.kind == "directional":
            return 1.0
        dx = float(position.x) - float(source.position.x)
        dy = float(position.y) - float(source.position.y)
        dz = float(position.z) - float(source.position.z)
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        factor = max(0.0, 1.0 - distance / source.range)
        if source.kind == "spot" and factor > 0.0:
            bearing = math.degrees(math.atan2(dy, dx))
            delta = _angle_delta(bearing, source.direction_degrees)
            half_cone = source.cone_angle_degrees / 2.0
            factor *= max(0.0, 1.0 - delta / half_cone)
        return factor

    def preview(
        self,
        position: Point3Record,
        *,
        object_id: str | None = None,
    ) -> LightingPreview:
        """Evaluate one bounded sample without wall-clock or random state."""

        if self._document is None:
            raise LightingRuntimeError("a validated lighting manifest is required")
        if not isinstance(position, Point3Record):
            raise LightingRuntimeError("position must be a Point3Record")
        material = self._material_for(object_id)
        albedo = (
            material.albedo
            if material is not None
            else LightingColorRecord(r=1.0, g=1.0, b=1.0)
        )
        emission = (
            material.emission
            if material is not None
            else LightingColorRecord(r=0.0, g=0.0, b=0.0)
        )
        opacity = material.opacity if material is not None else 1.0
        if material is not None and material.lighting_mode == "unlit":
            unlit_values: tuple[float, float, float] = (
                albedo.r + emission.r * material.emission_strength,
                albedo.g + emission.g * material.emission_strength,
                albedo.b + emission.b * material.emission_strength,
            )
            return LightingPreview(
                color=_rounded_color(unlit_values),
                opacity=opacity,
                material_id=material.id,
                contributing_light_ids=(),
            )
        contributions = [
            ("ambient", self._document.ambient.intensity, self._document.ambient.color)
        ]
        for source in self._document.lights:
            factor = self._source_factor(source, position)
            if factor > 0.0:
                contributions.append(
                    (source.id, factor * source.intensity, source.color)
                )

        def channel(component: str, albedo_component: float) -> float:
            return albedo_component * sum(
                strength * getattr(color, component)
                for _, strength, color in contributions
            ) + getattr(emission, component) * (
                material.emission_strength if material else 0.0
            )

        values: tuple[float, float, float] = (
            channel("r", albedo.r),
            channel("g", albedo.g),
            channel("b", albedo.b),
        )
        return LightingPreview(
            color=_rounded_color(values),
            opacity=opacity,
            material_id=material.id if material is not None else None,
            contributing_light_ids=tuple(
                source_id
                for source_id, strength, _ in contributions
                if source_id != "ambient" and strength > 0
            ),
        )

    def preview_socket(self, socket_id: str) -> LightingPreview:
        """Evaluate a light socket using its declared marker position."""

        if self._document is None:
            raise LightingRuntimeError("a validated lighting manifest is required")
        socket = next(
            (item for item in self._document.sockets if item.id == socket_id),
            None,
        )
        if socket is None:
            raise LightingRuntimeError(f"unknown light socket: {socket_id}")
        if not socket.enabled:
            return LightingPreview((0.0, 0.0, 0.0), 0.0, None, ())
        return self.preview(socket.position, object_id=socket.object_id)
