"""Versioned, atomic persistence for the independent E05 collider document."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.core.scenario_colliders import (
    Collider,
    ColliderDocument,
    ColliderError,
    ColliderKind,
)

COLLIDER_FORMAT_ID = "neoeng-d-trace-scenario-colliders"
COLLIDER_SCHEMA_VERSION = 1
MAX_COLLIDER_FILE_BYTES = 32 * 1024 * 1024


class ColliderPersistenceError(ColliderError):
    """Raised when a collider file cannot be safely read or written."""


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ColliderPersistenceError("invalid_mapping", f"{field} must be an object")
    return value


def _pair(value: object, field: str) -> tuple[float, float]:
    payload = _mapping(value, field)
    try:
        return float(payload["x"]), float(payload["y"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ColliderPersistenceError(
            "invalid_vector", f"{field} must contain x/y"
        ) from exc


def _optional_pair(value: object, field: str) -> tuple[float, float] | None:
    return None if value is None else _pair(value, field)


def _collider(value: object) -> Collider:
    payload = _mapping(value, "collider")
    identifier = payload.get("id")
    raw_kind = payload.get("kind")
    if not isinstance(identifier, str):
        raise ColliderPersistenceError("invalid_id", "collider.id must be a string")
    try:
        kind = ColliderKind(raw_kind)
    except (TypeError, ValueError) as exc:
        raise ColliderPersistenceError(
            "invalid_kind", "collider.kind is unsupported"
        ) from exc
    raw_points = payload.get("points", [])
    if not isinstance(raw_points, list):
        raise ColliderPersistenceError(
            "invalid_points", "collider.points must be a list"
        )
    try:
        points = tuple(_pair(point, "collider.point") for point in raw_points)
        return Collider(
            id=identifier,
            kind=kind,
            points=points,
            size=_optional_pair(payload.get("size"), "collider.size"),
            radius=payload.get("radius"),
            closed=payload.get("closed", False),
            position=_pair(payload.get("position"), "collider.position"),
            scale=_pair(payload.get("scale"), "collider.scale"),
            rotation_degrees=payload.get("rotation_degrees", 0.0),
            entity_id=payload.get("entity_id"),
            category=payload.get("category", 1),
            mask=payload.get("mask", 0xFFFF),
            is_trigger=payload.get("is_trigger", False),
            visible=payload.get("visible", True),
            material=payload.get("material"),
            version=payload.get("version", 1),
        )
    except ColliderError as exc:
        raise ColliderPersistenceError(exc.code, str(exc)) from exc


def _payload(document: ColliderDocument) -> dict[str, Any]:
    return {
        "format_id": COLLIDER_FORMAT_ID,
        "schema_version": COLLIDER_SCHEMA_VERSION,
        "id": document.id,
        "version": document.version,
        "colliders": [
            document.colliders[key].to_dict() for key in sorted(document.colliders)
        ],
    }


def save_colliders(document: ColliderDocument, path: Path) -> Path:
    payload = (
        json.dumps(_payload(document), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
    try:
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def load_colliders(path: Path) -> ColliderDocument:
    source = Path(path)
    if source.stat().st_size > MAX_COLLIDER_FILE_BYTES:
        raise ColliderPersistenceError(
            "file_limit", "collider file exceeds the size limit"
        )
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ColliderPersistenceError(
            "invalid_json", "collider file is not valid JSON"
        ) from exc
    if (
        payload.get("format_id") != COLLIDER_FORMAT_ID
        or payload.get("schema_version") != COLLIDER_SCHEMA_VERSION
    ):
        raise ColliderPersistenceError(
            "unsupported_format", "unsupported collider format or schema"
        )
    values = payload.get("colliders")
    if not isinstance(values, list):
        raise ColliderPersistenceError("invalid_colliders", "colliders must be a list")
    try:
        document = ColliderDocument(
            id=payload.get("id"), version=payload.get("version", 1)
        )
        document.replace_all(_collider(value) for value in values)
        return document
    except ColliderError as exc:
        raise ColliderPersistenceError(exc.code, str(exc)) from exc


__all__ = [
    "COLLIDER_FORMAT_ID",
    "COLLIDER_SCHEMA_VERSION",
    "ColliderPersistenceError",
    "load_colliders",
    "save_colliders",
]
