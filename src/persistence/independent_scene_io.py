"""Strict, deterministic and atomic I/O for independent scene documents."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES

from .errors import ProjectPersistenceError
from .independent_scene_schema import (
    INDEPENDENT_SCENE_FORMAT_ID,
    INDEPENDENT_SCENE_SCHEMA_VERSION,
    IndependentSceneDocumentV1,
)

MAX_INDEPENDENT_SCENE_FILE_BYTES = MAX_PROJECT_FILE_BYTES


class IndependentSceneReadError(ProjectPersistenceError):
    """Raised when an independent scene cannot be read safely."""


class IndependentSceneWriteError(ProjectPersistenceError):
    """Raised when an independent scene cannot be atomically replaced."""


class IndependentSceneFormatError(ProjectPersistenceError):
    """Raised for invalid encoding, JSON or document identity."""


class IndependentSceneValidationError(ProjectPersistenceError):
    """Raised when the versioned independent scene contract is invalid."""


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_object_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _canonical_json_bytes(document: IndependentSceneDocumentV1) -> bytes:
    payload = document.model_dump(mode="json")
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise IndependentSceneReadError(f"independent scene file not found: {path}")
    if not path.is_file():
        raise IndependentSceneReadError(f"independent scene path is not a file: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise IndependentSceneReadError(
            f"cannot stat independent scene {path}: {exc}"
        ) from exc
    if size > MAX_INDEPENDENT_SCENE_FILE_BYTES:
        raise IndependentSceneReadError(
            f"independent scene exceeds {MAX_INDEPENDENT_SCENE_FILE_BYTES} bytes"
        )
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_INDEPENDENT_SCENE_FILE_BYTES + 1)
    except OSError as exc:
        raise IndependentSceneReadError(
            f"cannot read independent scene {path}: {exc}"
        ) from exc
    if len(raw) > MAX_INDEPENDENT_SCENE_FILE_BYTES:
        raise IndependentSceneReadError(
            f"independent scene exceeds {MAX_INDEPENDENT_SCENE_FILE_BYTES} bytes"
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise IndependentSceneFormatError("UTF-8 BOM is not allowed")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise IndependentSceneFormatError(
            "independent scene is not valid UTF-8"
        ) from exc
    try:
        return json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise IndependentSceneFormatError(
            f"invalid independent scene JSON: {exc}"
        ) from exc


def _validate_document(value: Any) -> IndependentSceneDocumentV1:
    if not isinstance(value, Mapping):
        raise IndependentSceneFormatError("independent scene root must be an object")
    if value.get("format_id") != INDEPENDENT_SCENE_FORMAT_ID:
        raise IndependentSceneFormatError(
            "unsupported independent scene format identifier: "
            f"{value.get('format_id')!r}"
        )
    if value.get("schema_version") != INDEPENDENT_SCENE_SCHEMA_VERSION:
        raise IndependentSceneFormatError(
            "unsupported independent scene schema version: "
            f"{value.get('schema_version')!r}"
        )
    try:
        return IndependentSceneDocumentV1.model_validate(value, strict=True)
    except ValidationError as exc:
        raise IndependentSceneValidationError(str(exc)) from exc


def serialize_independent_scene(document: IndependentSceneDocumentV1) -> bytes:
    """Validate and serialize an independent scene deterministically."""

    try:
        validated = IndependentSceneDocumentV1.model_validate(document, strict=True)
    except ValidationError as exc:
        raise IndependentSceneValidationError(str(exc)) from exc
    return _canonical_json_bytes(validated)


def independent_scene_sha256(document: IndependentSceneDocumentV1) -> str:
    """Return the SHA-256 of the exact canonical document bytes."""

    return hashlib.sha256(serialize_independent_scene(document)).hexdigest()


def save_independent_scene(
    document: IndependentSceneDocumentV1,
    path: str | os.PathLike[str],
) -> None:
    """Atomically replace an independent scene without partial output."""

    destination = Path(path)
    if destination.suffix.lower() != ".ndtscene":
        raise IndependentSceneWriteError(
            "independent scene destination must use the .ndtscene extension"
        )
    parent = destination.parent
    if not parent.exists() or not parent.is_dir():
        raise IndependentSceneWriteError(
            f"destination directory does not exist: {parent}"
        )
    if destination.exists() and destination.is_dir():
        raise IndependentSceneWriteError(f"destination is a directory: {destination}")
    payload = serialize_independent_scene(document)
    if len(payload) > MAX_INDEPENDENT_SCENE_FILE_BYTES:
        raise IndependentSceneWriteError(
            "serialized independent scene exceeds "
            f"{MAX_INDEPENDENT_SCENE_FILE_BYTES} bytes"
        )
    try:
        with AtomicOutputTransaction() as transaction:
            staged = Path(transaction.stage_path(str(destination)))
            with staged.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            transaction.commit()
    except OSError as exc:
        raise IndependentSceneWriteError(
            f"failed to atomically write independent scene {destination}: {exc}"
        ) from exc


def load_independent_scene(
    path: str | os.PathLike[str],
) -> IndependentSceneDocumentV1:
    """Read and validate one independent scene document."""

    return _validate_document(_read_json(Path(path)))


__all__ = [
    "IndependentSceneFormatError",
    "IndependentSceneReadError",
    "IndependentSceneValidationError",
    "IndependentSceneWriteError",
    "independent_scene_sha256",
    "load_independent_scene",
    "save_independent_scene",
    "serialize_independent_scene",
]
