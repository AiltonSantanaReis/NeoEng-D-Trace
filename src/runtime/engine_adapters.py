"""Versioned runtime adapter bundle shared by the Godot and Unity adapters.

The bundle is deliberately a transport contract, not a claim that both engines
implement every effect identically.  It binds the canonical scenario manifest
and every sidecar to exact bytes, validates the sidecar dependency graph, and
records the native/degraded/incompatible decision for each engine capability.
Engine code consumes the same bundle and is required to preserve these
decisions instead of silently converting unsupported effects.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping

from src.core.app_identity import APP_ID, APP_VERSION
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.exporters.scenario_exporter import validate_scenario_runtime_export
from src.runtime.lighting import (
    LIGHTING_FORMAT_ID,
    LIGHTING_SCHEMA_VERSION,
    load_lighting_runtime_export_bytes,
)
from src.runtime.particles import (
    PARTICLES_FORMAT_ID,
    PARTICLES_SCHEMA_VERSION,
    load_particle_runtime_export_bytes,
)
from src.runtime.post_processing import (
    POST_PROCESSING_FORMAT_ID,
    POST_PROCESSING_SCHEMA_VERSION,
    load_post_processing_runtime_export_bytes,
)
from src.runtime.shaders import (
    SHADER_FORMAT_ID,
    SHADER_SCHEMA_VERSION,
    load_shader_runtime_export_bytes,
)
from src.runtime.streaming import (
    STREAMING_FORMAT_ID,
    STREAMING_SCHEMA_VERSION,
    load_streaming_runtime_export_bytes,
)
from src.runtime.triggers import (
    TRIGGERS_FORMAT_ID,
    TRIGGERS_SCHEMA_VERSION,
    load_trigger_runtime_export_bytes,
)

ADAPTER_BUNDLE_FORMAT_ID = "neoeng-d-trace-runtime-adapters"
ADAPTER_BUNDLE_SCHEMA_VERSION = 1
ADAPTER_API_VERSION = 1
MAX_ADAPTER_SIDECARS = 6

ENGINE_IDS = ("godot", "unity")
CAPABILITIES = (
    "runtime.scene_loading",
    "runtime.lifecycle",
    "runtime.fixed_update",
    "runtime.lighting",
    "runtime.shaders",
    "runtime.particles",
    "runtime.post_processing",
    "runtime.triggers",
    "runtime.streaming",
)

_SIDECAR_FORMATS: dict[str, tuple[str, int, Callable[[bytes], object]]] = {
    "runtime.lighting": (
        LIGHTING_FORMAT_ID,
        LIGHTING_SCHEMA_VERSION,
        load_lighting_runtime_export_bytes,
    ),
    "runtime.shaders": (
        SHADER_FORMAT_ID,
        SHADER_SCHEMA_VERSION,
        load_shader_runtime_export_bytes,
    ),
    "runtime.particles": (
        PARTICLES_FORMAT_ID,
        PARTICLES_SCHEMA_VERSION,
        load_particle_runtime_export_bytes,
    ),
    "runtime.post_processing": (
        POST_PROCESSING_FORMAT_ID,
        POST_PROCESSING_SCHEMA_VERSION,
        load_post_processing_runtime_export_bytes,
    ),
    "runtime.triggers": (
        TRIGGERS_FORMAT_ID,
        TRIGGERS_SCHEMA_VERSION,
        load_trigger_runtime_export_bytes,
    ),
    "runtime.streaming": (
        STREAMING_FORMAT_ID,
        STREAMING_SCHEMA_VERSION,
        load_streaming_runtime_export_bytes,
    ),
}


class AdapterBundleError(ValueError):
    """Base class for controlled adapter bundle failures."""


class AdapterBundleFormatError(AdapterBundleError):
    """Raised when bundle bytes are not canonical UTF-8 JSON."""


class AdapterBundleValidationError(AdapterBundleError):
    """Raised when the bundle or its dependency graph is invalid."""


@dataclass(frozen=True)
class AdapterBundleReport:
    """Validated, immutable information exposed to engine harnesses."""

    bundle_sha256: str
    scenario_sha256: str
    sidecar_capabilities: tuple[str, ...]
    engine: str
    decisions: Mapping[str, Mapping[str, str]]


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
        raise AdapterBundleValidationError(
            f"adapter bundle is not serializable: {exc}"
        ) from exc


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hash_field(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise AdapterBundleValidationError(f"{field} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise AdapterBundleValidationError(f"{field} must be lowercase SHA-256")
    return value


def _safe_relative_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AdapterBundleValidationError(f"{field} must be a POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AdapterBundleValidationError(f"{field} escapes the bundle root")
    if ":" in value:
        raise AdapterBundleValidationError(f"{field} must not contain a drive prefix")
    return value


def _strict_size(value: object, expected: int, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != expected:
        raise AdapterBundleValidationError(f"{field} does not match the exact bytes")
    if value < 0 or value > MAX_PROJECT_FILE_BYTES:
        raise AdapterBundleValidationError(f"{field} exceeds the file limit")


def _validate_engine_matrix(value: object) -> dict[str, dict[str, dict[str, str]]]:
    if not isinstance(value, Mapping) or set(value) != set(ENGINE_IDS):
        raise AdapterBundleValidationError("capabilities must contain Godot and Unity")
    result: dict[str, dict[str, dict[str, str]]] = {}
    for engine in ENGINE_IDS:
        entry = value[engine]
        if not isinstance(entry, Mapping) or set(entry) != {
            "adapter_id",
            "adapter_version",
            "support",
        }:
            raise AdapterBundleValidationError(f"{engine} adapter entry is invalid")
        adapter_id = entry["adapter_id"]
        version = entry["adapter_version"]
        if not isinstance(adapter_id, str) or not adapter_id:
            raise AdapterBundleValidationError(f"{engine} adapter id is invalid")
        if isinstance(version, bool) or not isinstance(version, int) or version != 1:
            raise AdapterBundleValidationError(f"{engine} adapter version is invalid")
        support = entry["support"]
        if not isinstance(support, list) or len(support) != len(CAPABILITIES):
            raise AdapterBundleValidationError(f"{engine} capability matrix is invalid")
        decisions: dict[str, dict[str, str]] = {}
        for decision in support:
            if not isinstance(decision, Mapping) or set(decision) != {
                "id",
                "compatibility",
                "mode",
                "reason",
            }:
                raise AdapterBundleValidationError(
                    f"{engine} capability decision is invalid"
                )
            capability = decision["id"]
            if capability not in CAPABILITIES or capability in decisions:
                raise AdapterBundleValidationError(f"{engine} capability id is invalid")
            compatibility = decision["compatibility"]
            if compatibility not in {"native", "degraded", "incompatible"}:
                raise AdapterBundleValidationError(
                    f"{engine}.{capability} compatibility is invalid"
                )
            if not isinstance(decision["mode"], str) or not decision["mode"]:
                raise AdapterBundleValidationError(
                    f"{engine}.{capability} mode is invalid"
                )
            if not isinstance(decision["reason"], str) or not decision["reason"]:
                raise AdapterBundleValidationError(
                    f"{engine}.{capability} reason is invalid"
                )
            decisions[capability] = {
                "compatibility": compatibility,
                "mode": decision["mode"],
                "reason": decision["reason"],
            }
        if set(decisions) != set(CAPABILITIES):
            raise AdapterBundleValidationError(
                f"{engine} capability matrix is incomplete"
            )
        result[engine] = decisions
    return result


def _decode_canonical(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes):
        raise AdapterBundleFormatError("adapter bundle bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise AdapterBundleFormatError("adapter bundle exceeds the file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise AdapterBundleFormatError("UTF-8 BOM is not allowed")
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
        raise AdapterBundleFormatError(f"invalid adapter bundle JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise AdapterBundleFormatError("adapter bundle root must be an object")
    copied = copy.deepcopy(dict(payload))
    if raw != _canonical_json_bytes(copied):
        raise AdapterBundleFormatError("adapter bundle bytes are not canonical")
    return copied


def _validate_bundle_structure(payload: Mapping[str, Any]) -> None:
    if set(payload) != {
        "format_id",
        "schema_version",
        "api_version",
        "generator",
        "source",
        "sidecars",
        "capabilities",
    }:
        raise AdapterBundleValidationError("adapter bundle keys do not match schema")
    if payload["format_id"] != ADAPTER_BUNDLE_FORMAT_ID:
        raise AdapterBundleValidationError("unsupported adapter bundle format")
    if payload["schema_version"] != ADAPTER_BUNDLE_SCHEMA_VERSION:
        raise AdapterBundleValidationError("unsupported adapter bundle schema version")
    if payload["api_version"] != ADAPTER_API_VERSION:
        raise AdapterBundleValidationError("unsupported adapter API version")
    generator = payload["generator"]
    if not isinstance(generator, Mapping) or set(generator) != {"id", "version"}:
        raise AdapterBundleValidationError("adapter bundle generator is invalid")
    if generator["id"] != APP_ID or not isinstance(generator["version"], str):
        raise AdapterBundleValidationError(
            "adapter bundle generator identity is invalid"
        )
    source = payload["source"]
    if not isinstance(source, Mapping) or set(source) != {
        "path",
        "format_id",
        "schema_version",
        "sha256",
        "bytes",
    }:
        raise AdapterBundleValidationError("adapter bundle source is invalid")
    _safe_relative_path(source["path"], "source.path")
    if (
        source["format_id"] != "neoeng-d-trace-scenario-runtime"
        or source["schema_version"] != 1
    ):
        raise AdapterBundleValidationError("adapter bundle source contract is invalid")
    _hash_field(source["sha256"], "source.sha256")
    sidecars = payload["sidecars"]
    if not isinstance(sidecars, list) or len(sidecars) != MAX_ADAPTER_SIDECARS:
        raise AdapterBundleValidationError(
            "adapter bundle must contain all six sidecars"
        )
    seen_capabilities: set[str] = set()
    seen_paths: set[str] = set()
    for index, sidecar in enumerate(sidecars):
        field = f"sidecars[{index}]"
        if not isinstance(sidecar, Mapping) or set(sidecar) != {
            "capability",
            "path",
            "format_id",
            "schema_version",
            "sha256",
            "bytes",
            "required",
        }:
            raise AdapterBundleValidationError(f"{field} is invalid")
        capability = sidecar["capability"]
        if capability not in _SIDECAR_FORMATS or capability in seen_capabilities:
            raise AdapterBundleValidationError(f"{field}.capability is invalid")
        seen_capabilities.add(capability)
        path = _safe_relative_path(sidecar["path"], f"{field}.path")
        if path in seen_paths or path == source["path"]:
            raise AdapterBundleValidationError(f"{field}.path is duplicated")
        seen_paths.add(path)
        expected_format, expected_version, _ = _SIDECAR_FORMATS[capability]
        if (
            sidecar["format_id"] != expected_format
            or sidecar["schema_version"] != expected_version
        ):
            raise AdapterBundleValidationError(
                f"{field} contract does not match capability"
            )
        _hash_field(sidecar["sha256"], f"{field}.sha256")
        if not isinstance(sidecar["required"], bool) or not sidecar["required"]:
            raise AdapterBundleValidationError(f"{field}.required must be true")
        if not isinstance(sidecar["bytes"], int) or isinstance(sidecar["bytes"], bool):
            raise AdapterBundleValidationError(f"{field}.bytes is invalid")
        if sidecar["bytes"] < 1 or sidecar["bytes"] > MAX_PROJECT_FILE_BYTES:
            raise AdapterBundleValidationError(f"{field}.bytes exceeds the file limit")
    _validate_engine_matrix(payload["capabilities"])
    if set(seen_capabilities) != set(_SIDECAR_FORMATS):
        raise AdapterBundleValidationError("adapter bundle sidecar set is incomplete")


def build_adapter_bundle(
    *,
    source_path: str,
    source_bytes: bytes,
    sidecars: Mapping[str, tuple[str, bytes]],
    capabilities: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the canonical bundle from exact source and sidecar bytes."""

    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise AdapterBundleValidationError("source bytes must be non-empty")
    if len(source_bytes) > MAX_PROJECT_FILE_BYTES:
        raise AdapterBundleValidationError("source bytes exceed the file limit")
    source_path = _safe_relative_path(source_path, "source_path")
    try:
        source_payload = _decode_canonical(source_bytes)
        validate_scenario_runtime_export(source_payload)
    except (AdapterBundleError, TypeError, ValueError, KeyError) as exc:
        raise AdapterBundleValidationError(f"invalid scenario source: {exc}") from exc
    if not isinstance(sidecars, Mapping) or set(sidecars) != set(_SIDECAR_FORMATS):
        raise AdapterBundleValidationError("all six runtime sidecars are required")
    sidecar_records: list[dict[str, Any]] = []
    for capability in sorted(_SIDECAR_FORMATS):
        path, raw = sidecars[capability]
        path = _safe_relative_path(path, f"{capability}.path")
        if not isinstance(raw, bytes) or not raw:
            raise AdapterBundleValidationError(f"{capability} bytes are invalid")
        expected_format, expected_version, loader = _SIDECAR_FORMATS[capability]
        try:
            document = loader(raw)
        except Exception as exc:
            raise AdapterBundleValidationError(
                f"{capability} sidecar is invalid: {exc}"
            ) from exc
        source_binding = getattr(document, "source", None)
        if source_binding is None:
            raise AdapterBundleValidationError(
                f"{capability} source binding is missing"
            )
        expected_source = _hash(source_bytes)
        if capability == "runtime.shaders":
            lighting = sidecars["runtime.lighting"][1]
            expected_source = _hash(lighting)
        if source_binding.sha256 != expected_source:
            raise AdapterBundleValidationError(
                f"{capability} is not bound to the exact dependency bytes"
            )
        sidecar_records.append(
            {
                "capability": capability,
                "path": path,
                "format_id": expected_format,
                "schema_version": expected_version,
                "sha256": _hash(raw),
                "bytes": len(raw),
                "required": True,
            }
        )
    payload = {
        "format_id": ADAPTER_BUNDLE_FORMAT_ID,
        "schema_version": ADAPTER_BUNDLE_SCHEMA_VERSION,
        "api_version": ADAPTER_API_VERSION,
        "generator": {"id": APP_ID, "version": APP_VERSION},
        "source": {
            "path": source_path,
            "format_id": "neoeng-d-trace-scenario-runtime",
            "schema_version": 1,
            "sha256": _hash(source_bytes),
            "bytes": len(source_bytes),
        },
        "sidecars": sidecar_records,
        "capabilities": copy.deepcopy(dict(capabilities)),
    }
    _validate_bundle_structure(payload)
    return payload


def serialize_adapter_bundle(payload: Mapping[str, Any]) -> bytes:
    """Validate and serialize the adapter bundle canonically."""

    _validate_bundle_structure(payload)
    encoded = _canonical_json_bytes(payload)
    if len(encoded) > MAX_PROJECT_FILE_BYTES:
        raise AdapterBundleValidationError("adapter bundle exceeds the file limit")
    return encoded


def validate_adapter_bundle(payload: Mapping[str, Any]) -> None:
    """Validate only the bundle structure, without reading referenced files."""

    _validate_bundle_structure(payload)


def load_adapter_bundle(
    root: str | os.PathLike[str],
    bundle_path: str | os.PathLike[str],
    *,
    engine: str = "godot",
) -> tuple[dict[str, Any], AdapterBundleReport]:
    """Load a bundle and verify every referenced file and dependency hash."""

    if engine not in ENGINE_IDS:
        raise AdapterBundleValidationError(f"unsupported engine: {engine}")
    root_path = Path(root).resolve()
    candidate = Path(bundle_path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root_path)
    except ValueError as exc:
        raise AdapterBundleFormatError("adapter bundle path escapes its root") from exc
    raw = candidate.read_bytes()
    payload = _decode_canonical(raw)
    _validate_bundle_structure(payload)
    source = payload["source"]
    source_file = _resolve_reference(root_path, source["path"])
    source_bytes = source_file.read_bytes()
    _strict_size(source["bytes"], len(source_bytes), "source.bytes")
    if _hash(source_bytes) != source["sha256"]:
        raise AdapterBundleValidationError("scenario source hash mismatch")
    _validate_source_bytes(source_bytes)
    loaded: dict[str, object] = {}
    for sidecar in payload["sidecars"]:
        path = _resolve_reference(root_path, sidecar["path"])
        sidecar_bytes = path.read_bytes()
        field = f"{sidecar['capability']}.bytes"
        _strict_size(sidecar["bytes"], len(sidecar_bytes), field)
        if _hash(sidecar_bytes) != sidecar["sha256"]:
            raise AdapterBundleValidationError(
                f"{sidecar['capability']} sidecar hash mismatch"
            )
        _, _, loader = _SIDECAR_FORMATS[sidecar["capability"]]
        try:
            loaded[sidecar["capability"]] = loader(sidecar_bytes)
        except Exception as exc:
            raise AdapterBundleValidationError(
                f"{sidecar['capability']} sidecar cannot be loaded: {exc}"
            ) from exc
    lighting_hash = _hash(
        _resolve_reference(
            root_path,
            next(
                item["path"]
                for item in payload["sidecars"]
                if item["capability"] == "runtime.lighting"
            ),
        ).read_bytes()
    )
    for sidecar in payload["sidecars"]:
        document = loaded[sidecar["capability"]]
        expected = (
            lighting_hash
            if sidecar["capability"] == "runtime.shaders"
            else _hash(source_bytes)
        )
        if getattr(document, "source").sha256 != expected:
            raise AdapterBundleValidationError(
                f"{sidecar['capability']} dependency binding mismatch"
            )
    decisions = _validate_engine_matrix(payload["capabilities"])[engine]
    return payload, AdapterBundleReport(
        bundle_sha256=_hash(raw),
        scenario_sha256=source["sha256"],
        sidecar_capabilities=tuple(item["capability"] for item in payload["sidecars"]),
        engine=engine,
        decisions=decisions,
    )


def _resolve_reference(root: Path, relative: str) -> Path:
    candidate = (root / PurePosixPath(relative)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AdapterBundleValidationError(
            "referenced file escapes bundle root"
        ) from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise AdapterBundleValidationError("referenced file is missing or is a symlink")
    return candidate


def _validate_source_bytes(raw: bytes) -> None:
    payload = _decode_canonical(raw)
    try:
        validate_scenario_runtime_export(payload)
    except (TypeError, ValueError, KeyError) as exc:
        raise AdapterBundleValidationError(
            f"scenario source is invalid: {exc}"
        ) from exc


def write_adapter_bundle(
    path: str | os.PathLike[str], payload: Mapping[str, Any]
) -> None:
    """Atomically write the canonical bundle without touching referenced files."""

    destination = Path(path)
    if not destination.parent.is_dir() or destination.exists() and destination.is_dir():
        raise AdapterBundleValidationError(
            "bundle destination is not a writable file path"
        )
    encoded = serialize_adapter_bundle(payload)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise AdapterBundleError(f"failed to write adapter bundle: {exc}") from exc


__all__ = [
    "ADAPTER_API_VERSION",
    "ADAPTER_BUNDLE_FORMAT_ID",
    "ADAPTER_BUNDLE_SCHEMA_VERSION",
    "CAPABILITIES",
    "ENGINE_IDS",
    "AdapterBundleError",
    "AdapterBundleFormatError",
    "AdapterBundleReport",
    "AdapterBundleValidationError",
    "build_adapter_bundle",
    "load_adapter_bundle",
    "serialize_adapter_bundle",
    "validate_adapter_bundle",
    "write_adapter_bundle",
]
