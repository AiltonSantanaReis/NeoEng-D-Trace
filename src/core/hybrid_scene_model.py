"""Versioned, non-destructive model for the editor's hybrid 3D sidecar.

The existing scenario document remains the source of truth for the 2D
authoring path.  This module owns only the additive ``*.hybrid3d.json``
sidecar used by the 2D/2.5D/3D authoring viewport.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

HYBRID_EDITOR_FORMAT_ID = "neoeng-d-trace-hybrid-editor"
HYBRID_EDITOR_SCHEMA_VERSION = 1
HYBRID_EDITOR_SUPPORT_STATUS = "EDITOR_VERTICAL_SLICE"


class HybridSceneError(ValueError):
    """Raised when a hybrid sidecar cannot be safely read or validated."""


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HybridSceneError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise HybridSceneError(f"{name} must be finite")
    return result


def _vec3(value: Any, name: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise HybridSceneError(f"{name} must contain 3 values")
    return [
        _finite_number(item, f"{name}[{index}]") for index, item in enumerate(value)
    ]


def _text(value: Any, name: str, *, max_length: int = 128) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise HybridSceneError(f"{name} is invalid")
    return value


def _transform(record: Mapping[str, Any], prefix: str) -> None:
    position = _vec3(record.get("position"), f"{prefix}.position")
    rotation = _vec3(record.get("rotation", [0, 0, 0]), f"{prefix}.rotation")
    scale = _vec3(record.get("scale", [1, 1, 1]), f"{prefix}.scale")
    if any(abs(value) > 1_000_000 for value in position + rotation):
        raise HybridSceneError(f"{prefix} transform exceeds the safe range")
    if any(value <= 0 or value > 1_000_000 for value in scale):
        raise HybridSceneError(f"{prefix}.scale is invalid")


def default_hybrid_scene() -> dict[str, Any]:
    """Return a useful scene that can be authored without an imported asset."""

    return {
        "format_id": HYBRID_EDITOR_FORMAT_ID,
        "schema_version": HYBRID_EDITOR_SCHEMA_VERSION,
        "support_status": HYBRID_EDITOR_SUPPORT_STATUS,
        "camera": {
            "projection": "perspective",
            "fov_degrees": 55.0,
            "near": 0.1,
            "far": 1000.0,
            "position": [0.0, 2.5, 8.0],
            "target": [0.0, 0.0, 0.0],
        },
        "materials": [
            {
                "id": "default-material",
                "name": "Material padrão",
                "color": "#4d8fb8",
                "metallic": 0.0,
                "roughness": 0.6,
            }
        ],
        "objects": [
            {
                "id": "mesh-cube",
                "name": "Cubo principal",
                "kind": "mesh",
                "primitive": "cube",
                "position": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.5, 1.5, 1.5],
                "material_id": "default-material",
            },
            {
                "id": "light-key",
                "name": "Luz direcional",
                "kind": "light",
                "light_type": "directional",
                "position": [2.5, 4.0, 3.0],
                "rotation": [-35.0, -25.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "intensity": 1.2,
                "color": "#ffd58a",
            },
            {
                "id": "camera-main",
                "name": "Câmera principal",
                "kind": "camera",
                "position": [0.0, 2.5, 8.0],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "target": [0.0, 0.0, 0.0],
            },
        ],
        "selected_id": "mesh-cube",
    }


def validate_hybrid_scene(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and copy a sidecar, rejecting unknown unsafe shapes early."""

    if not isinstance(payload, Mapping):
        raise HybridSceneError("hybrid scene must be an object")
    if payload.get("format_id") != HYBRID_EDITOR_FORMAT_ID:
        raise HybridSceneError("unsupported hybrid editor format")
    if payload.get("schema_version") != HYBRID_EDITOR_SCHEMA_VERSION:
        raise HybridSceneError("unsupported hybrid editor schema")
    if payload.get("support_status") != HYBRID_EDITOR_SUPPORT_STATUS:
        raise HybridSceneError("hybrid editor support status must be explicit")

    camera = payload.get("camera")
    if not isinstance(camera, Mapping):
        raise HybridSceneError("hybrid camera is required")
    projection = camera.get("projection")
    if projection not in {"perspective", "orthographic"}:
        raise HybridSceneError("hybrid camera projection is invalid")
    fov = _finite_number(camera.get("fov_degrees"), "camera.fov_degrees")
    near = _finite_number(camera.get("near"), "camera.near")
    far = _finite_number(camera.get("far"), "camera.far")
    if not 1.0 <= fov < 180.0 or near <= 0.0 or far <= near:
        raise HybridSceneError("hybrid camera clipping or FOV is invalid")
    _vec3(camera.get("position"), "camera.position")
    _vec3(camera.get("target"), "camera.target")

    materials = payload.get("materials")
    if not isinstance(materials, list) or not materials:
        raise HybridSceneError("hybrid scene needs at least one material")
    material_ids: set[str] = set()
    for index, material in enumerate(materials):
        if not isinstance(material, Mapping):
            raise HybridSceneError(f"material {index} is invalid")
        material_id = _text(material.get("id"), f"material[{index}].id")
        if material_id in material_ids:
            raise HybridSceneError("hybrid material IDs must be unique")
        material_ids.add(material_id)
        _text(
            material.get("color", "#ffffff"), f"material[{index}].color", max_length=16
        )
        _finite_number(material.get("metallic", 0.0), f"material[{index}].metallic")
        _finite_number(material.get("roughness", 0.5), f"material[{index}].roughness")

    objects = payload.get("objects")
    if not isinstance(objects, list) or not objects:
        raise HybridSceneError("hybrid scene needs at least one object")
    object_ids: set[str] = set()
    for index, record in enumerate(objects):
        if not isinstance(record, Mapping):
            raise HybridSceneError(f"hybrid object {index} is invalid")
        object_id = _text(record.get("id"), f"object[{index}].id")
        if object_id in object_ids:
            raise HybridSceneError("hybrid object IDs must be unique")
        object_ids.add(object_id)
        kind = record.get("kind")
        if kind not in {"mesh", "light", "camera"}:
            raise HybridSceneError(f"object {object_id}.kind is invalid")
        _text(record.get("name"), f"object {object_id}.name")
        _transform(record, f"object {object_id}")
        if kind == "mesh":
            if record.get("primitive") not in {"cube", "plane"}:
                raise HybridSceneError(f"object {object_id}.primitive is invalid")
            if record.get("material_id") not in material_ids:
                raise HybridSceneError(
                    f"object {object_id} references an unknown material"
                )
        elif kind == "light":
            if record.get("light_type") not in {"directional", "point"}:
                raise HybridSceneError(f"object {object_id}.light_type is invalid")
            intensity = _finite_number(
                record.get("intensity"), f"object {object_id}.intensity"
            )
            if intensity < 0.0 or intensity > 100_000.0:
                raise HybridSceneError(f"object {object_id}.intensity is invalid")
            _text(
                record.get("color", "#ffffff"),
                f"object {object_id}.color",
                max_length=16,
            )
        else:
            _vec3(record.get("target", [0, 0, 0]), f"object {object_id}.target")

    selected = payload.get("selected_id")
    if selected is not None and selected not in object_ids:
        raise HybridSceneError("hybrid selected_id references an unknown object")
    return deepcopy(dict(payload))


def load_hybrid_scene(path: str | os.PathLike[str]) -> dict[str, Any]:
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HybridSceneError(f"hybrid scene cannot be read: {source}") from exc
    return validate_hybrid_scene(payload)


def save_hybrid_scene(payload: Mapping[str, Any], path: str | os.PathLike[str]) -> Path:
    """Atomically save canonical JSON without touching the 2D scene file."""

    validated = validate_hybrid_scene(payload)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(validated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise HybridSceneError(f"hybrid scene cannot be saved: {destination}") from exc
    return destination


__all__ = [
    "HYBRID_EDITOR_FORMAT_ID",
    "HYBRID_EDITOR_SCHEMA_VERSION",
    "HYBRID_EDITOR_SUPPORT_STATUS",
    "HybridSceneError",
    "default_hybrid_scene",
    "load_hybrid_scene",
    "save_hybrid_scene",
    "validate_hybrid_scene",
]
