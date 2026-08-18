"""Deterministic, hash-bound and atomic I/O for lateral scenario documents."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from src.core.atomic_outputs import AtomicOutputTransaction

from .errors import ProjectPersistenceError
from .scenario_schema import (
    MAX_SCENARIO_FILE_BYTES,
    SCENARIO_FORMAT_ID,
    SCENARIO_SCHEMA_VERSION,
    ProjectReferenceRecord,
    ScenarioDocumentV1,
)


class ScenarioReadError(ProjectPersistenceError):
    """Raised when a scenario sidecar cannot be read safely."""


class ScenarioWriteError(ProjectPersistenceError):
    """Raised when a scenario sidecar cannot be replaced atomically."""


class ScenarioFormatError(ProjectPersistenceError):
    """Raised when a sidecar is not valid UTF-8/JSON or has duplicate keys."""


class ScenarioValidationError(ProjectPersistenceError):
    """Raised when a sidecar violates the versioned scenario schema."""


def _canonical_json_bytes(document: ScenarioDocumentV1) -> bytes:
    payload = document.model_dump(mode="json")
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
        raise ScenarioReadError(f"scenario file not found: {path}")
    if not path.is_file():
        raise ScenarioReadError(f"scenario path is not a file: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ScenarioReadError(f"cannot stat scenario file {path}: {exc}") from exc
    if size > MAX_SCENARIO_FILE_BYTES:
        raise ScenarioReadError(
            f"scenario file exceeds {MAX_SCENARIO_FILE_BYTES} bytes"
        )
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_SCENARIO_FILE_BYTES + 1)
    except OSError as exc:
        raise ScenarioReadError(f"cannot read scenario file {path}: {exc}") from exc
    if len(raw) > MAX_SCENARIO_FILE_BYTES:
        raise ScenarioReadError(
            f"scenario file exceeds {MAX_SCENARIO_FILE_BYTES} bytes"
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ScenarioFormatError("UTF-8 BOM is not allowed")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ScenarioFormatError("scenario file is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ScenarioFormatError(f"invalid scenario JSON: {exc}") from exc


def _validate_document(value: Any) -> ScenarioDocumentV1:
    if not isinstance(value, Mapping):
        raise ScenarioFormatError("scenario root must be a JSON object")
    if value.get("format_id") != SCENARIO_FORMAT_ID:
        raise ScenarioFormatError(
            f"unsupported scenario format identifier: {value.get('format_id')!r}"
        )
    if value.get("schema_version") != SCENARIO_SCHEMA_VERSION:
        raise ScenarioFormatError(
            f"unsupported scenario schema version: {value.get('schema_version')!r}"
        )
    try:
        return ScenarioDocumentV1.model_validate(value, strict=True)
    except ValidationError as exc:
        raise ScenarioValidationError(str(exc)) from exc


def serialize_scenario(document: ScenarioDocumentV1) -> bytes:
    """Validate and serialize a scenario deterministically as UTF-8 JSON."""

    try:
        validated = ScenarioDocumentV1.model_validate(document, strict=True)
    except ValidationError as exc:
        raise ScenarioValidationError(str(exc)) from exc
    return _canonical_json_bytes(validated)


def scenario_sha256(document: ScenarioDocumentV1) -> str:
    """Return the SHA-256 of the exact canonical sidecar bytes."""

    return hashlib.sha256(serialize_scenario(document)).hexdigest()


def hash_project_file(path: str | os.PathLike[str]) -> str:
    """Hash an existing bounded ``.ndtproj`` without modifying or parsing it."""

    source = Path(path)
    if source.suffix.lower() != ".ndtproj":
        raise ScenarioReadError("scenario project reference must target a .ndtproj")
    if not source.is_file():
        raise ScenarioReadError(f"project file not found: {source}")
    try:
        size = source.stat().st_size
    except OSError as exc:
        raise ScenarioReadError(f"cannot stat project file {source}: {exc}") from exc
    if size > MAX_SCENARIO_FILE_BYTES:
        raise ScenarioReadError(f"project file exceeds {MAX_SCENARIO_FILE_BYTES} bytes")
    digest = hashlib.sha256()
    total = 0
    try:
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                total += len(chunk)
                if total > MAX_SCENARIO_FILE_BYTES:
                    raise ScenarioReadError(
                        f"project file exceeds {MAX_SCENARIO_FILE_BYTES} bytes"
                    )
                digest.update(chunk)
    except OSError as exc:
        raise ScenarioReadError(f"cannot read project file {source}: {exc}") from exc
    return digest.hexdigest()


def project_reference_for(path: str | os.PathLike[str]) -> ProjectReferenceRecord:
    """Build the explicit v1 project reference used by a scenario document."""

    return ProjectReferenceRecord(sha256=hash_project_file(path))


def verify_project_reference(
    document: ScenarioDocumentV1,
    project_path: str | os.PathLike[str],
) -> None:
    """Raise if the sidecar is not bound to the exact supplied project bytes."""

    actual = hash_project_file(project_path)
    if actual != document.project.sha256:
        raise ScenarioValidationError(
            "scenario project reference hash does not match the supplied project"
        )


def save_scenario(
    document: ScenarioDocumentV1,
    path: str | os.PathLike[str],
) -> None:
    """Atomically replace one sidecar while preserving an existing file on error."""

    destination = Path(path)
    parent = destination.parent
    if not parent.exists() or not parent.is_dir():
        raise ScenarioWriteError(f"destination directory does not exist: {parent}")
    if destination.exists() and destination.is_dir():
        raise ScenarioWriteError(f"destination is a directory: {destination}")
    payload = serialize_scenario(document)
    if len(payload) > MAX_SCENARIO_FILE_BYTES:
        raise ScenarioWriteError(
            f"serialized scenario exceeds {MAX_SCENARIO_FILE_BYTES} bytes"
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
        raise ScenarioWriteError(
            f"failed to atomically write scenario {destination}: {exc}"
        ) from exc


def load_scenario(
    path: str | os.PathLike[str],
    *,
    project_path: str | os.PathLike[str] | None = None,
) -> ScenarioDocumentV1:
    """Read, validate and optionally verify the bound project hash."""

    document = _validate_document(_read_json(Path(path)))
    if project_path is not None:
        verify_project_reference(document, project_path)
    return document
