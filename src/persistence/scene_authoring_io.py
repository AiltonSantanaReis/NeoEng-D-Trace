"""Versioned, hash-bound and atomic I/O for professional authored scenes.

The lateral `
eoeng-d-trace-scenario`` contract is intentionally not used
here.  This module persists the separate professional authoring contract and
preserves the explicit schema version on read.  V1 to V2 conversion is only
available through the explicit upgrade helper; loading never migrates data
silently.
"""

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
from .scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocument,
    SceneAuthoringDocumentV2,
    validate_scene_authoring_document,
)


class SceneAuthoringReadError(ProjectPersistenceError):
    """Raised when a professional scene file cannot be read safely."""


class SceneAuthoringWriteError(ProjectPersistenceError):
    """Raised when a professional scene cannot be replaced atomically."""


class SceneAuthoringFormatError(ProjectPersistenceError):
    """Raised when a scene file is not valid strict UTF-8 JSON."""


class SceneAuthoringValidationError(ProjectPersistenceError):
    """Raised when a scene violates its explicit versioned schema."""


class SceneAuthoringAssetError(ProjectPersistenceError):
    """Raised when a referenced asset is missing, unsafe or hash-different."""


def _canonical_json_bytes(document: SceneAuthoringDocument) -> bytes:
    payload = validate_scene_authoring_document(document).model_dump(mode="json")
    # Keep legacy canonical bytes stable: omit only the new optional provenance field when absent.
    for asset in payload.get("assets", []):
        if asset.get("source_path") is None:
            asset.pop("source_path", None)
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


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


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise SceneAuthoringReadError(f"scene file not found: {path}")
    if not path.is_file():
        raise SceneAuthoringReadError(f"scene path is not a file: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SceneAuthoringReadError(f"cannot stat scene file: {exc}") from exc
    if size > MAX_PROJECT_FILE_BYTES:
        raise SceneAuthoringReadError(
            f"scene file exceeds {MAX_PROJECT_FILE_BYTES} bytes"
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SceneAuthoringReadError(f"cannot read scene file: {exc}") from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SceneAuthoringFormatError("UTF-8 BOM is not allowed")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SceneAuthoringFormatError("scene file is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise SceneAuthoringFormatError(f"invalid scene JSON: {exc}") from exc


def _validate_document(value: Any) -> SceneAuthoringDocument:
    if not isinstance(value, Mapping):
        raise SceneAuthoringFormatError("scene root must be a JSON object")
    try:
        return validate_scene_authoring_document(value)
    except (TypeError, ValueError, ValidationError) as exc:
        raise SceneAuthoringValidationError(str(exc)) from exc


def serialize_scene_authoring(document: SceneAuthoringDocument) -> bytes:
    """Return canonical bytes while preserving the document's schema version."""

    try:
        return _canonical_json_bytes(document)
    except (TypeError, ValueError, ValidationError) as exc:
        raise SceneAuthoringValidationError(str(exc)) from exc


def scene_authoring_sha256(document: SceneAuthoringDocument) -> str:
    """Return the SHA-256 of the canonical document bytes."""

    return hashlib.sha256(serialize_scene_authoring(document)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SceneAuthoringAssetError(f"cannot read asset {path}: {exc}") from exc
    return digest.hexdigest()


def _asset_path(scene_path: Path, asset: AssetReferenceRecord) -> Path:
    root = scene_path.parent.resolve(strict=False)
    candidate = (root / Path(asset.path)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SceneAuthoringAssetError(
            f"asset path escapes the scene directory: {asset.path}"
        ) from exc
    if not candidate.is_file():
        raise SceneAuthoringAssetError(f"asset file not found: {asset.path}")
    return candidate


def verify_scene_assets(
    document: SceneAuthoringDocument,
    scene_path: str | os.PathLike[str],
) -> None:
    """Verify every relative asset reference against the scene's directory."""

    path = Path(scene_path)
    for asset in document.assets:
        actual = _sha256_file(_asset_path(path, asset))
        if actual != asset.sha256:
            raise SceneAuthoringAssetError(
                f"asset hash does not match for {asset.path}: "
                f"expected {asset.sha256}, got {actual}"
            )


def save_scene_authoring(
    document: SceneAuthoringDocument,
    path: str | os.PathLike[str],
) -> None:
    """Atomically save a deterministic V1 or V2 professional scene."""

    destination = Path(path)
    if not destination.parent.is_dir():
        raise SceneAuthoringWriteError(
            f"destination directory does not exist: {destination.parent}"
        )
    if destination.exists() and destination.is_dir():
        raise SceneAuthoringWriteError("scene destination is a directory")
    payload = serialize_scene_authoring(document)
    if len(payload) > MAX_PROJECT_FILE_BYTES:
        raise SceneAuthoringWriteError(
            f"serialized scene exceeds {MAX_PROJECT_FILE_BYTES} bytes"
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
        raise SceneAuthoringWriteError(f"failed to save scene: {exc}") from exc


def load_scene_authoring(
    path: str | os.PathLike[str],
    *,
    verify_assets: bool = True,
) -> SceneAuthoringDocument:
    """Load and validate a scene while preserving its explicit schema version."""

    scene_path = Path(path)
    document = _validate_document(_read_json(scene_path))
    if verify_assets:
        verify_scene_assets(document, scene_path)
    return document


def load_scene_authoring_v2(
    path: str | os.PathLike[str],
    *,
    verify_assets: bool = True,
) -> SceneAuthoringDocumentV2:
    """Load a V2 document; V1 is rejected instead of silently upgraded."""

    document = load_scene_authoring(path, verify_assets=verify_assets)
    if not isinstance(document, SceneAuthoringDocumentV2):
        raise SceneAuthoringValidationError(
            "scene schema v1 requires explicit upgrade before V2 use"
        )
    return document


__all__ = [
    "SceneAuthoringAssetError",
    "SceneAuthoringFormatError",
    "SceneAuthoringReadError",
    "SceneAuthoringValidationError",
    "SceneAuthoringWriteError",
    "load_scene_authoring",
    "load_scene_authoring_v2",
    "save_scene_authoring",
    "scene_authoring_sha256",
    "serialize_scene_authoring",
    "verify_scene_assets",
]
