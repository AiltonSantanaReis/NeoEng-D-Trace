"""Versioned deterministic post-processing runtime sidecar.

The sidecar is deliberately separate from the approved scenario manifest.  It
provides a bounded CPU preview backend for a small, explicit effect set.  A
request for an engine backend is never silently treated as native support: the
documented fallback policy returns a degraded CPU preview, disables the chain,
or rejects the request.
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

import numpy as np
from pydantic import Field, field_validator, model_validator

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_schema import StrictProjectModel

POST_PROCESSING_FORMAT_ID = "neoeng-d-trace-runtime-post-processing"
POST_PROCESSING_SCHEMA_VERSION = 1
POST_PROCESSING_API_VERSION = 1
POST_PROCESSING_ALGORITHM_VERSION = 1
POST_PROCESSING_SOURCE_FORMAT_ID = "neoeng-d-trace-scenario-runtime"
POST_PROCESSING_SOURCE_SCHEMA_VERSION = 1
POST_PROCESSING_BACKEND = "cpu-preview"
MAX_POST_PROCESSING_EFFECTS = 64
MAX_POST_PROCESSING_ID_LENGTH = 128
MAX_POST_PROCESSING_PIXELS = 16_777_216
MAX_POST_PROCESSING_BLUR_RADIUS = 8
MAX_POST_PROCESSING_EXPOSURE_STOPS = 16.0

PostProcessKind = Literal[
    "exposure",
    "grayscale",
    "tint",
    "vignette",
    "box_blur",
]
PostProcessFallbackMode = Literal["cpu-preview", "disable", "reject"]
PostProcessCompatibility = Literal["native", "degraded", "incompatible"]


class PostProcessingRuntimeError(ValueError):
    """Base class for controlled post-processing failures."""


class PostProcessingFormatError(PostProcessingRuntimeError):
    """Raised when sidecar bytes are not canonical UTF-8 JSON."""


class PostProcessingValidationError(PostProcessingRuntimeError):
    """Raised when a sidecar violates the versioned contract."""


class PostProcessingCapabilityError(PostProcessingRuntimeError):
    """Raised when the requested backend cannot be fulfilled safely."""


class PostProcessingPreviewError(PostProcessingRuntimeError):
    """Raised when preview input or execution is invalid."""


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


class PostProcessingSourceBindingRecord(StrictProjectModel):
    """Exact scenario-runtime bytes to which the sidecar is bound."""

    format_id: Literal["neoeng-d-trace-scenario-runtime"] = (
        "neoeng-d-trace-scenario-runtime"
    )
    schema_version: Literal[1] = 1
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class PostProcessingFallbackRecord(StrictProjectModel):
    """Explicit behavior when a requested backend is not native."""

    mode: PostProcessFallbackMode
    reason: str = Field(min_length=1, max_length=512)


class PostProcessingEffectRecord(StrictProjectModel):
    """One bounded effect in the deterministic chain.

    Parameters are intentionally a closed per-kind mapping.  Keeping the
    mapping closed prevents an apparently valid manifest from silently
    discarding parameters that the preview or an adapter does not understand.
    """

    id: str = Field(min_length=1, max_length=MAX_POST_PROCESSING_ID_LENGTH)
    kind: PostProcessKind
    order: int = Field(ge=0)
    enabled: bool = True
    parameters: dict[str, Any]

    @field_validator("order")
    @classmethod
    def validate_order(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("effect.order must be a strict non-negative integer")
        return value

    @model_validator(mode="after")
    def validate_parameters(self) -> "PostProcessingEffectRecord":
        params = self.parameters
        if not isinstance(params, dict):
            raise ValueError("effect.parameters must be an object")
        expected: dict[str, set[str]] = {
            "exposure": {"stops"},
            "grayscale": {"amount"},
            "tint": {"amount", "color"},
            "vignette": {"amount", "radius"},
            "box_blur": {"radius"},
        }
        if set(params) != expected[self.kind]:
            raise ValueError(
                f"{self.kind} parameters must be exactly "
                f"{sorted(expected[self.kind])}"
            )
        if self.kind == "exposure":
            _bounded(
                params["stops"],
                "effect.parameters.stops",
                -MAX_POST_PROCESSING_EXPOSURE_STOPS,
                MAX_POST_PROCESSING_EXPOSURE_STOPS,
            )
        elif self.kind == "grayscale":
            _bounded(params["amount"], "effect.parameters.amount", 0.0, 1.0)
        elif self.kind == "tint":
            _bounded(params["amount"], "effect.parameters.amount", 0.0, 1.0)
            color = params["color"]
            if (
                not isinstance(color, list)
                or len(color) != 3
                or any(
                    isinstance(component, bool)
                    or not isinstance(component, (int, float))
                    or not math.isfinite(float(component))
                    or not 0.0 <= float(component) <= 1.0
                    for component in color
                )
            ):
                raise ValueError(
                    "effect.parameters.color must be three finite RGB values"
                )
        elif self.kind == "vignette":
            _bounded(params["amount"], "effect.parameters.amount", 0.0, 1.0)
            _bounded(params["radius"], "effect.parameters.radius", 0.01, 1.0)
        else:
            radius = params["radius"]
            if isinstance(radius, bool) or not isinstance(radius, int):
                raise ValueError("effect.parameters.radius must be a strict integer")
            if radius < 0 or radius > MAX_POST_PROCESSING_BLUR_RADIUS:
                raise ValueError(
                    "effect.parameters.radius exceeds the post-processing limit"
                )
        return self


class PostProcessingDocumentV1(StrictProjectModel):
    """Complete version 1 post-processing sidecar contract."""

    format_id: Literal["neoeng-d-trace-runtime-post-processing"] = (
        "neoeng-d-trace-runtime-post-processing"
    )
    schema_version: Literal[1] = 1
    algorithm_version: Literal[1] = 1
    required_capability: Literal["runtime.post_processing"] = "runtime.post_processing"
    source: PostProcessingSourceBindingRecord
    backend: Literal["cpu-preview"] = "cpu-preview"
    compatibility: Literal["native"] = "native"
    fallback: PostProcessingFallbackRecord
    effects: list[PostProcessingEffectRecord] = Field(
        min_length=1, max_length=MAX_POST_PROCESSING_EFFECTS
    )

    @model_validator(mode="after")
    def validate_chain(self) -> "PostProcessingDocumentV1":
        effect_ids = [effect.id for effect in self.effects]
        orders = [effect.order for effect in self.effects]
        if len(effect_ids) != len(set(effect_ids)):
            raise ValueError("post-processing effect IDs must be unique")
        if len(orders) != len(set(orders)):
            raise ValueError("post-processing effect orders must be unique")
        if self.fallback.mode == "reject" and not self.fallback.reason:
            raise ValueError("reject fallback requires a reason")
        return self


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PostProcessingValidationError(
            f"post-processing document cannot be serialized: {exc}"
        ) from exc


def _validated_document(payload: object) -> PostProcessingDocumentV1:
    if isinstance(payload, PostProcessingDocumentV1):
        return payload.model_copy(deep=True)
    if not isinstance(payload, Mapping):
        raise PostProcessingValidationError(
            "post-processing document root must be an object"
        )
    try:
        return PostProcessingDocumentV1.model_validate(payload, strict=True)
    except Exception as exc:
        raise PostProcessingValidationError(str(exc)) from exc


def build_post_processing_runtime_export(
    document: PostProcessingDocumentV1,
) -> dict[str, Any]:
    """Validate and copy a post-processing sidecar for export."""

    return _validated_document(document).model_dump(mode="json")


def serialize_post_processing_runtime_export(
    document: PostProcessingDocumentV1,
) -> bytes:
    """Serialize the sidecar as canonical UTF-8 JSON."""

    payload = build_post_processing_runtime_export(document)
    encoded = _canonical_json_bytes(payload)
    if len(encoded) > MAX_PROJECT_FILE_BYTES:
        raise PostProcessingValidationError(
            "post-processing document exceeds the project file limit"
        )
    return encoded


def post_processing_runtime_export_sha256(
    document: PostProcessingDocumentV1,
) -> str:
    """Hash the exact canonical sidecar bytes."""

    return hashlib.sha256(
        serialize_post_processing_runtime_export(document)
    ).hexdigest()


def validate_post_processing_runtime_export(
    payload: Mapping[str, Any],
) -> PostProcessingDocumentV1:
    """Strictly validate a decoded sidecar payload."""

    return _validated_document(payload)


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_post_processing_runtime_export_bytes(
    raw: bytes,
) -> PostProcessingDocumentV1:
    """Load canonical sidecar bytes with strict JSON checks."""

    if not isinstance(raw, bytes):
        raise PostProcessingFormatError("post-processing manifest bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise PostProcessingFormatError(
            "post-processing manifest exceeds the file limit"
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise PostProcessingFormatError("UTF-8 BOM is not allowed")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PostProcessingFormatError(f"invalid post-processing JSON: {exc}") from exc
    document = _validated_document(payload)
    if raw != serialize_post_processing_runtime_export(document):
        raise PostProcessingFormatError(
            "post-processing manifest bytes are not canonical"
        )
    return document


def load_post_processing_runtime_export(
    path: str | os.PathLike[str],
) -> PostProcessingDocumentV1:
    """Load a canonical post-processing sidecar from disk."""

    candidate = Path(path)
    try:
        raw = candidate.read_bytes()
    except OSError as exc:
        raise PostProcessingFormatError(
            f"post-processing manifest cannot be read: {exc}"
        ) from exc
    return load_post_processing_runtime_export_bytes(raw)


def save_post_processing_runtime_export(
    document: PostProcessingDocumentV1,
    destination: str | os.PathLike[str],
) -> None:
    """Atomically replace one post-processing sidecar."""

    path = Path(destination)
    if path.exists() and path.is_dir():
        raise PostProcessingValidationError(
            "post-processing export destination is a directory"
        )
    if not path.parent.exists() or not path.parent.is_dir():
        raise PostProcessingValidationError(
            "post-processing export parent directory does not exist"
        )
    payload = serialize_post_processing_runtime_export(document)
    try:
        with AtomicOutputTransaction() as transaction:
            temporary = Path(transaction.stage_path(str(path)))
            with temporary.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            transaction.commit()
    except OSError as exc:
        raise PostProcessingValidationError(
            f"failed to save post-processing export: {exc}"
        ) from exc


def verify_post_processing_source_binding(
    document: PostProcessingDocumentV1,
    source_bytes: bytes,
) -> None:
    """Verify that the sidecar is bound to exact scenario bytes."""

    validated = _validated_document(document)
    if not isinstance(source_bytes, bytes):
        raise PostProcessingValidationError("source_bytes must be bytes")
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != validated.source.sha256:
        raise PostProcessingValidationError(
            "post-processing source hash does not match"
        )


def _validate_image(image: np.ndarray) -> np.ndarray:
    if not isinstance(image, np.ndarray):
        raise PostProcessingPreviewError("preview image must be a NumPy array")
    if image.ndim != 3 or image.shape[2] != 4:
        raise PostProcessingPreviewError(
            "preview image must have shape (height, width, 4)"
        )
    height, width, _ = image.shape
    if height <= 0 or width <= 0 or height * width > MAX_POST_PROCESSING_PIXELS:
        raise PostProcessingPreviewError(
            "preview image exceeds dimensions or pixel limits"
        )
    if not np.issubdtype(image.dtype, np.number):
        raise PostProcessingPreviewError("preview image must contain numeric values")
    if not np.isfinite(image).all():
        raise PostProcessingPreviewError("preview image must contain finite values")
    return np.ascontiguousarray(image, dtype=np.float64)


def _box_blur(rgb: np.ndarray, radius: int) -> np.ndarray:
    if radius == 0:
        return rgb.copy()
    kernel = 2 * radius + 1
    padded = np.pad(
        rgb,
        ((radius, radius), (radius, radius), (0, 0)),
        mode="edge",
    )
    integral = np.pad(padded, ((1, 0), (1, 0), (0, 0)), mode="constant")
    integral = integral.cumsum(axis=0).cumsum(axis=1)
    height, width, _ = rgb.shape
    return (
        integral[kernel : kernel + height, kernel : kernel + width]
        - integral[:height, kernel : kernel + width]
        - integral[kernel : kernel + height, :width]
        + integral[:height, :width]
    ) / float(kernel * kernel)


def _apply_effect(image: np.ndarray, effect: PostProcessingEffectRecord) -> np.ndarray:
    if not effect.enabled:
        return image
    result = image.copy()
    rgb = result[:, :, :3]
    params = effect.parameters
    if effect.kind == "exposure":
        rgb *= 2.0 ** float(params["stops"])
    elif effect.kind == "grayscale":
        amount = float(params["amount"])
        luma = np.sum(rgb * np.array([0.2126, 0.7152, 0.0722]), axis=2, keepdims=True)
        rgb[:] = rgb * (1.0 - amount) + luma * amount
    elif effect.kind == "tint":
        amount = float(params["amount"])
        color = np.asarray(params["color"], dtype=np.float64).reshape((1, 1, 3))
        rgb[:] = rgb * (1.0 - amount) + rgb * color * amount
    elif effect.kind == "vignette":
        amount = float(params["amount"])
        radius = float(params["radius"])
        height, width = rgb.shape[:2]
        y = np.linspace(-1.0, 1.0, height, dtype=np.float64)[:, None]
        x = np.linspace(-1.0, 1.0, width, dtype=np.float64)[None, :]
        distance = np.sqrt(x * x + y * y) / math.sqrt(2.0)
        factor = 1.0 - amount * np.clip((distance - radius) / (1.0 - radius), 0.0, 1.0)
        rgb[:] = rgb * factor[:, :, None]
    else:
        rgb[:] = _box_blur(rgb, int(params["radius"]))
    result[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    result[:, :, 3] = np.clip(result[:, :, 3], 0.0, 1.0)
    return result


@dataclass(frozen=True)
class PostProcessingPreview:
    """Deterministic preview result and auditable execution metadata."""

    image: np.ndarray
    backend: str
    compatibility: PostProcessCompatibility
    fallback_mode: str | None
    fallback_reason: str | None
    applied_effect_ids: tuple[str, ...]
    skipped_effect_ids: tuple[str, ...]
    input_sha256: str
    output_sha256: str


class PostProcessingRuntime:
    """Atomic sidecar loader and deterministic CPU preview evaluator."""

    def __init__(self) -> None:
        self._document: PostProcessingDocumentV1 | None = None

    @property
    def document(self) -> PostProcessingDocumentV1 | None:
        return self._document

    def manifest_copy(self) -> dict[str, Any] | None:
        return (
            copy.deepcopy(self._document.model_dump(mode="json"))
            if self._document is not None
            else None
        )

    def load_manifest(
        self, document: PostProcessingDocumentV1
    ) -> PostProcessingDocumentV1:
        validated = _validated_document(document)
        self._document = validated
        return validated

    def load_file(self, path: str | os.PathLike[str]) -> PostProcessingDocumentV1:
        return self.load_manifest(load_post_processing_runtime_export(path))

    def _require_document(self) -> PostProcessingDocumentV1:
        if self._document is None:
            raise PostProcessingPreviewError("no post-processing document is loaded")
        return self._document

    def negotiate(
        self, backend: str
    ) -> tuple[PostProcessCompatibility, str, str | None]:
        """Return explicit compatibility, mode and reason for a backend."""

        document = self._require_document()
        if backend == POST_PROCESSING_BACKEND:
            return "native", POST_PROCESSING_BACKEND, None
        if not isinstance(backend, str) or not backend:
            raise PostProcessingCapabilityError("backend must be a non-empty string")
        fallback = document.fallback
        if fallback.mode == "cpu-preview":
            return "degraded", POST_PROCESSING_BACKEND, fallback.reason
        if fallback.mode == "disable":
            return "degraded", "disable", fallback.reason
        return "incompatible", "reject", fallback.reason

    def preview(
        self,
        image: np.ndarray,
        *,
        backend: str = POST_PROCESSING_BACKEND,
    ) -> PostProcessingPreview:
        """Apply the ordered chain, or execute its explicit fallback."""

        document = self._require_document()
        source = _validate_image(image)
        input_hash = hashlib.sha256(
            np.ascontiguousarray(source, dtype=np.float64).tobytes()
        ).hexdigest()
        compatibility, mode, reason = self.negotiate(backend)
        if compatibility == "incompatible":
            raise PostProcessingCapabilityError(
                f"backend {backend!r} is incompatible: {reason}"
            )
        if mode == "disable":
            output = source.copy()
            applied: tuple[str, ...] = ()
            skipped = tuple(effect.id for effect in document.effects)
        else:
            output = source
            ordered = sorted(document.effects, key=lambda effect: effect.order)
            applied_list: list[str] = []
            skipped_list: list[str] = []
            for effect in ordered:
                if effect.enabled:
                    output = _apply_effect(output, effect)
                    applied_list.append(effect.id)
                else:
                    skipped_list.append(effect.id)
            applied = tuple(applied_list)
            skipped = tuple(skipped_list)
        output = np.ascontiguousarray(output, dtype=np.float64)
        return PostProcessingPreview(
            image=output,
            backend=mode,
            compatibility=compatibility,
            fallback_mode=None if backend == POST_PROCESSING_BACKEND else mode,
            fallback_reason=reason,
            applied_effect_ids=applied,
            skipped_effect_ids=skipped,
            input_sha256=input_hash,
            output_sha256=hashlib.sha256(output.tobytes()).hexdigest(),
        )
