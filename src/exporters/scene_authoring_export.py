"""Strict exports for the professional scene-authoring document.

The payload is deliberately consumer-neutral at its core.  Godot and Unity
receive the same authored scene plus an explicit coordinate mapping and a
capability report.  This prevents an adapter from silently dropping objects,
transforms or sockets while keeping runtime-only effects outside the editor
contract.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import ValidationError

from src.core.app_identity import APP_ID, APP_VERSION
from src.core.atomic_outputs import AtomicOutputTransaction
from src.persistence.scene_authoring_io import scene_authoring_sha256
from src.persistence.scene_authoring_schema import SceneAuthoringDocumentV2

SCENE_EXPORT_FORMAT_ID = "neoeng-d-trace-scene-authoring-export"
SCENE_EXPORT_SCHEMA_VERSION = 1
SceneExportTarget = Literal["generic", "godot", "unity"]

_CAPABILITIES: dict[str, dict[str, tuple[str, ...]]] = {
    "generic": {
        "supported": (
            "assets",
            "layers",
            "objects",
            "groups",
            "transforms",
            "camera",
            "parallax",
            "sockets",
            "snap_settings",
        ),
        "unsupported": (
            "runtime_lighting",
            "runtime_particles",
            "runtime_shaders",
            "runtime_post_processing",
        ),
    },
    "godot": {
        "supported": (
            "assets",
            "layers",
            "objects",
            "groups",
            "transforms",
            "camera",
            "parallax",
            "sockets",
            "snap_settings",
        ),
        "unsupported": (
            "runtime_lighting",
            "runtime_particles",
            "runtime_shaders",
            "runtime_post_processing",
        ),
    },
    "unity": {
        "supported": (
            "assets",
            "layers",
            "objects",
            "groups",
            "transforms",
            "camera",
            "parallax",
            "sockets",
            "snap_settings",
        ),
        "unsupported": (
            "runtime_lighting",
            "runtime_particles",
            "runtime_shaders",
            "runtime_post_processing",
        ),
    },
}

_COORDINATE_MAPPINGS: dict[str, dict[str, Any]] = {
    "generic": {
        "source_origin": "top-left",
        "target_origin": "top-left",
        "position_y_sign": 1,
        "rotation_sign": 1,
        "rotation_unit": "degrees",
    },
    "godot": {
        "source_origin": "top-left",
        "target_origin": "godot-2d-y-down",
        "position_y_sign": 1,
        "rotation_sign": 1,
        "rotation_unit": "degrees",
    },
    "unity": {
        "source_origin": "top-left",
        "target_origin": "unity-2d-y-up",
        "position_y_sign": -1,
        "rotation_sign": -1,
        "rotation_unit": "degrees",
    },
}


class SceneAuthoringExportError(ValueError):
    """Raised when a professional scene export is invalid or unsafe."""


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
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


def _hex_hash(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise SceneAuthoringExportError(f"{field} must be a lowercase SHA-256")
    return value


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SceneAuthoringExportError(f"{field} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise SceneAuthoringExportError(f"{field} must be finite")
    return number


def _validate_export(payload: Mapping[str, Any]) -> None:
    expected = {
        "format_id",
        "schema_version",
        "target",
        "generator",
        "source",
        "coordinate_mapping",
        "capabilities",
        "scene",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise SceneAuthoringExportError("scene export keys do not match schema")
    if payload["format_id"] != SCENE_EXPORT_FORMAT_ID:
        raise SceneAuthoringExportError("unsupported scene export format")
    if payload["schema_version"] != SCENE_EXPORT_SCHEMA_VERSION:
        raise SceneAuthoringExportError("unsupported scene export version")
    target = payload["target"]
    if target not in _CAPABILITIES:
        raise SceneAuthoringExportError("unsupported scene export target")
    generator = payload["generator"]
    if not isinstance(generator, Mapping) or set(generator) != {"id", "version"}:
        raise SceneAuthoringExportError("scene export generator is invalid")
    if generator["id"] != APP_ID or not isinstance(generator["version"], str):
        raise SceneAuthoringExportError("scene export generator identity is invalid")
    source = payload["source"]
    if (
        not isinstance(source, Mapping)
        or set(source) != {"format_id", "schema_version", "sha256"}
        or source["format_id"] != "neoeng-d-trace-scene-authoring"
        or source["schema_version"] != 2
    ):
        raise SceneAuthoringExportError("scene export source binding is invalid")
    _hex_hash(source["sha256"], "scene export source hash")
    mapping = payload["coordinate_mapping"]
    if (
        not isinstance(mapping, Mapping)
        or set(mapping)
        != {
            "source_origin",
            "target_origin",
            "position_y_sign",
            "rotation_sign",
            "rotation_unit",
        }
        or mapping["source_origin"] != "top-left"
        or mapping["rotation_unit"] != "degrees"
        or mapping["position_y_sign"] not in {-1, 1}
        or mapping["rotation_sign"] not in {-1, 1}
        or not isinstance(mapping["target_origin"], str)
    ):
        raise SceneAuthoringExportError("scene export coordinate mapping is invalid")
    capabilities = payload["capabilities"]
    if (
        not isinstance(capabilities, Mapping)
        or set(capabilities) != {"supported", "unsupported"}
        or not isinstance(capabilities["supported"], list)
        or not isinstance(capabilities["unsupported"], list)
        or any(not isinstance(value, str) for value in capabilities["supported"])
        or any(not isinstance(value, str) for value in capabilities["unsupported"])
        or set(capabilities["supported"]) & set(capabilities["unsupported"])
    ):
        raise SceneAuthoringExportError("scene export capabilities are invalid")
    try:
        scene = SceneAuthoringDocumentV2.model_validate(payload["scene"], strict=True)
    except (TypeError, ValueError, ValidationError) as exc:
        raise SceneAuthoringExportError(
            f"scene export document is invalid: {exc}"
        ) from exc
    if scene_authoring_sha256(scene) != source["sha256"]:
        raise SceneAuthoringExportError("scene export source hash does not match scene")
    expected_capabilities = _CAPABILITIES[target]
    if capabilities != {
        "supported": list(expected_capabilities["supported"]),
        "unsupported": list(expected_capabilities["unsupported"]),
    }:
        raise SceneAuthoringExportError("scene export capability declaration drifted")
    if mapping != _COORDINATE_MAPPINGS[target]:
        raise SceneAuthoringExportError("scene export coordinate mapping drifted")


def build_scene_authoring_export(
    document: SceneAuthoringDocumentV2,
    *,
    target: SceneExportTarget,
) -> dict[str, Any]:
    """Build a strict target export; V1 requires explicit upgrade first."""

    if not isinstance(document, SceneAuthoringDocumentV2):
        raise SceneAuthoringExportError(
            "professional scene export requires an explicit schema V2 document"
        )
    if target not in _CAPABILITIES:
        raise SceneAuthoringExportError("unsupported scene export target")
    validated = SceneAuthoringDocumentV2.model_validate(document, strict=True)
    payload = {
        "format_id": SCENE_EXPORT_FORMAT_ID,
        "schema_version": SCENE_EXPORT_SCHEMA_VERSION,
        "target": target,
        "generator": {"id": APP_ID, "version": APP_VERSION},
        "source": {
            "format_id": "neoeng-d-trace-scene-authoring",
            "schema_version": 2,
            "sha256": scene_authoring_sha256(validated),
        },
        "coordinate_mapping": dict(_COORDINATE_MAPPINGS[target]),
        "capabilities": {
            "supported": list(_CAPABILITIES[target]["supported"]),
            "unsupported": list(_CAPABILITIES[target]["unsupported"]),
        },
        "scene": validated.model_dump(mode="json"),
    }
    _validate_export(payload)
    return payload


def serialize_scene_authoring_export(
    document: SceneAuthoringDocumentV2,
    *,
    target: SceneExportTarget,
) -> bytes:
    """Serialize a deterministic professional export."""

    return _canonical_json_bytes(build_scene_authoring_export(document, target=target))


def scene_authoring_export_sha256(
    document: SceneAuthoringDocumentV2,
    *,
    target: SceneExportTarget,
) -> str:
    return hashlib.sha256(
        serialize_scene_authoring_export(document, target=target)
    ).hexdigest()


def save_scene_authoring_export(
    document: SceneAuthoringDocumentV2,
    path: str | os.PathLike[str],
    *,
    target: SceneExportTarget,
) -> None:
    """Atomically write one generic, Godot or Unity export."""

    destination = Path(path)
    if not destination.parent.is_dir():
        raise SceneAuthoringExportError("scene export directory does not exist")
    if destination.exists() and destination.is_dir():
        raise SceneAuthoringExportError("scene export destination is a directory")
    payload = serialize_scene_authoring_export(document, target=target)
    try:
        with AtomicOutputTransaction() as transaction:
            staged = Path(transaction.stage_path(str(destination)))
            with staged.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            transaction.commit()
    except OSError as exc:
        raise SceneAuthoringExportError(f"failed to save scene export: {exc}") from exc


def validate_scene_authoring_export(payload: Mapping[str, Any]) -> None:
    """Public strict validator used by native-adapter tests and audit tooling."""

    _validate_export(payload)


__all__ = [
    "SCENE_EXPORT_FORMAT_ID",
    "SCENE_EXPORT_SCHEMA_VERSION",
    "SceneAuthoringExportError",
    "build_scene_authoring_export",
    "save_scene_authoring_export",
    "scene_authoring_export_sha256",
    "serialize_scene_authoring_export",
    "validate_scene_authoring_export",
]
