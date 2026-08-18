"""Deterministic runtime export for the lateral scenario contract.

The editor sidecar remains the source document.  This module emits a smaller,
consumer-neutral runtime payload that keeps the project and sidecar hashes,
camera state, layer order, object references and parallax parameters.  It does
not embed textures or claim to be a game runtime; the Godot and Unity adapters
consume the same payload to build a named layer hierarchy and metadata.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

from src.core.app_identity import APP_ID, APP_VERSION
from src.core.atomic_outputs import AtomicOutputTransaction
from src.persistence.scenario_io import scenario_sha256
from src.persistence.scenario_schema import (
    MAX_SCENARIO_FILE_BYTES,
    SCENARIO_FORMAT_ID,
    SCENARIO_SCHEMA_VERSION,
    ScenarioDocumentV1,
)

SCENARIO_EXPORT_FORMAT_ID = "neoeng-d-trace-scenario-runtime"
SCENARIO_EXPORT_SCHEMA_VERSION = 1
SCENARIO_EXPORT_FILE_EXTENSION = ".ndtscenario.runtime.json"


class ScenarioExportError(ValueError):
    """Raised when a runtime scenario export is invalid or unsafe."""


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


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScenarioExportError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ScenarioExportError(f"{field} must be a finite number")
    return number


def _unit(value: Any, field: str) -> float:
    number = _finite(value, field)
    if number < 0.0 or number > 1.0:
        raise ScenarioExportError(f"{field} must be between 0 and 1")
    return number


def _point(value: Mapping[str, Any], field: str) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise ScenarioExportError(f"{field} must be an object")
    return {
        "x": _finite(value.get("x"), f"{field}.x"),
        "y": _finite(value.get("y"), f"{field}.y"),
    }


def _validate_export(payload: Mapping[str, Any]) -> None:
    expected = {
        "format_id",
        "schema_version",
        "generator",
        "source",
        "project",
        "camera",
        "layers",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise ScenarioExportError("scenario runtime export keys do not match schema")
    if payload["format_id"] != SCENARIO_EXPORT_FORMAT_ID:
        raise ScenarioExportError("unsupported scenario runtime export format")
    if payload["schema_version"] != SCENARIO_EXPORT_SCHEMA_VERSION:
        raise ScenarioExportError("unsupported scenario runtime export version")
    generator = payload["generator"]
    if not isinstance(generator, Mapping) or generator.get("id") != APP_ID:
        raise ScenarioExportError("scenario runtime generator identity is invalid")
    if not isinstance(generator.get("version"), str) or not generator["version"]:
        raise ScenarioExportError("scenario runtime generator version is invalid")
    source = payload["source"]
    if (
        not isinstance(source, Mapping)
        or set(source) != {"format_id", "schema_version", "sha256"}
        or source["format_id"] != SCENARIO_FORMAT_ID
        or source["schema_version"] != SCENARIO_SCHEMA_VERSION
        or not isinstance(source["sha256"], str)
        or len(source["sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in source["sha256"])
    ):
        raise ScenarioExportError("scenario runtime source binding is invalid")
    project = payload["project"]
    if (
        not isinstance(project, Mapping)
        or set(project) != {"format_id", "schema_version", "sha256"}
        or project["format_id"] != "neoeng-d-trace-project"
        or project["schema_version"] != 1
        or not isinstance(project["sha256"], str)
        or len(project["sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in project["sha256"])
    ):
        raise ScenarioExportError("scenario runtime project binding is invalid")
    camera = payload["camera"]
    if not isinstance(camera, Mapping) or set(camera) != {"position", "zoom"}:
        raise ScenarioExportError("scenario runtime camera is invalid")
    _point(camera["position"], "camera.position")
    if _finite(camera["zoom"], "camera.zoom") <= 0:
        raise ScenarioExportError("camera.zoom must be positive")
    layers = payload["layers"]
    if not isinstance(layers, list) or len(layers) > 256:
        raise ScenarioExportError("scenario runtime layers are invalid")
    seen_layers: set[str] = set()
    seen_objects: set[str] = set()
    for index, layer in enumerate(layers):
        field = f"layers[{index}]"
        if not isinstance(layer, Mapping) or set(layer) != {
            "id",
            "name",
            "visible",
            "object_ids",
            "parallax",
        }:
            raise ScenarioExportError(f"{field} is invalid")
        layer_id = layer["id"]
        if not isinstance(layer_id, str) or not layer_id or layer_id in seen_layers:
            raise ScenarioExportError(f"{field}.id is invalid or duplicated")
        seen_layers.add(layer_id)
        if not isinstance(layer["name"], str) or not isinstance(layer["visible"], bool):
            raise ScenarioExportError(f"{field} metadata is invalid")
        object_ids = layer["object_ids"]
        if not isinstance(object_ids, list):
            raise ScenarioExportError(f"{field}.object_ids is invalid")
        for object_id in object_ids:
            if (
                not isinstance(object_id, str)
                or not object_id
                or object_id in seen_objects
            ):
                raise ScenarioExportError(
                    f"{field}.object_ids contains invalid reference"
                )
            seen_objects.add(object_id)
        parallax = layer["parallax"]
        if not isinstance(parallax, Mapping) or set(parallax) != {
            "depth",
            "translation_strength",
            "zoom_strength",
        }:
            raise ScenarioExportError(f"{field}.parallax is invalid")
        for key in ("depth", "translation_strength", "zoom_strength"):
            _unit(parallax[key], f"{field}.parallax.{key}")


def build_scenario_runtime_export(document: ScenarioDocumentV1) -> dict[str, Any]:
    """Build and validate the consumer-neutral runtime payload."""

    try:
        validated = ScenarioDocumentV1.model_validate(document, strict=True)
    except Exception as exc:  # pydantic error type varies across supported versions
        raise ScenarioExportError(f"scenario document is invalid: {exc}") from exc
    payload = {
        "format_id": SCENARIO_EXPORT_FORMAT_ID,
        "schema_version": SCENARIO_EXPORT_SCHEMA_VERSION,
        "generator": {"id": APP_ID, "version": APP_VERSION},
        "source": {
            "format_id": SCENARIO_FORMAT_ID,
            "schema_version": SCENARIO_SCHEMA_VERSION,
            "sha256": scenario_sha256(validated),
        },
        "project": validated.project.model_dump(mode="json"),
        "camera": validated.camera.model_dump(mode="json"),
        "layers": [layer.model_dump(mode="json") for layer in validated.layers],
    }
    _validate_export(payload)
    return payload


def serialize_scenario_runtime_export(document: ScenarioDocumentV1) -> bytes:
    """Serialize a validated runtime export deterministically."""

    payload = build_scenario_runtime_export(document)
    serialized = _canonical_json_bytes(payload)
    if len(serialized) > MAX_SCENARIO_FILE_BYTES:
        raise ScenarioExportError("scenario runtime export exceeds file limit")
    return serialized


def scenario_runtime_export_sha256(document: ScenarioDocumentV1) -> str:
    return hashlib.sha256(serialize_scenario_runtime_export(document)).hexdigest()


def save_scenario_runtime_export(
    document: ScenarioDocumentV1,
    path: str | os.PathLike[str],
) -> None:
    """Atomically save the deterministic runtime export."""

    destination = Path(path)
    if not destination.parent.is_dir():
        raise ScenarioExportError("scenario runtime export directory does not exist")
    if destination.exists() and destination.is_dir():
        raise ScenarioExportError("scenario runtime export destination is a directory")
    payload = serialize_scenario_runtime_export(document)
    try:
        with AtomicOutputTransaction() as transaction:
            staged = Path(transaction.stage_path(str(destination)))
            with staged.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            transaction.commit()
    except OSError as exc:
        raise ScenarioExportError(
            f"failed to save scenario runtime export: {exc}"
        ) from exc


def validate_scenario_runtime_export(payload: Mapping[str, Any]) -> None:
    """Public strict validator used by tests and evidence tooling."""

    _validate_export(payload)
