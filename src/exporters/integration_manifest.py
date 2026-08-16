"""Versioned source contract consumed by the optional engine adapters."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from src.core.app_identity import APP_ID, APP_VERSION

INTEGRATION_FORMAT_ID = "neoeng-d-trace-engine-integration"
INTEGRATION_SCHEMA_VERSION = 1
SUPPORTED_ENGINES = frozenset({"godot", "unity"})
GENERATED_ROOT = "NeoEngGenerated"
OVERRIDE_SUFFIX = ".ndt.override.json"


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: str | Path) -> str:
    source = Path(path)
    if not source.is_file():
        raise ValueError("integration source image must be a regular file")
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_reference(reference: str) -> str:
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("integration image reference must be relative and safe")
    normalized = reference.replace("\\", "/")
    path = PurePosixPath(normalized)
    has_windows_drive = len(normalized) >= 2 and normalized[1] == ":"
    if (
        path.is_absolute()
        or normalized.startswith("//")
        or has_windows_drive
        or ".." in path.parts
    ):
        raise ValueError("integration image reference must be relative and safe")
    return path.as_posix()


def build_integration_manifest(
    metadata: Mapping[str, Any],
    *,
    engine: str,
    image_path: str | Path,
    image_reference: str,
    generator_version: str = APP_VERSION,
) -> dict[str, Any]:
    """Build the strict manifest shared by the Godot and Unity adapters."""

    if not isinstance(metadata, Mapping):
        raise ValueError("integration metadata must be a mapping")
    normalized_engine = engine.strip().lower() if isinstance(engine, str) else ""
    if normalized_engine not in SUPPORTED_ENGINES:
        raise ValueError(f"unsupported integration engine: {engine}")
    if not isinstance(generator_version, str) or not generator_version.strip():
        raise ValueError("generator_version must be non-empty")
    metadata_format = metadata.get("format_id")
    metadata_version = metadata.get("schema_version")
    if not isinstance(metadata_format, str) or not isinstance(metadata_version, int):
        raise ValueError("metadata must contain format_id and integer schema_version")

    manifest = {
        "format_id": INTEGRATION_FORMAT_ID,
        "schema_version": INTEGRATION_SCHEMA_VERSION,
        "generator": {"id": APP_ID, "version": generator_version},
        "engine": normalized_engine,
        "source": {
            "image": {
                "path": _relative_reference(image_reference),
                "sha256": _sha256_file(image_path),
            },
            "metadata": {
                "format_id": metadata_format,
                "schema_version": metadata_version,
                "sha256": _sha256_bytes(_canonical_json_bytes(metadata)),
            },
        },
        "sync": {
            "direction": "dtrace-to-engine",
            "generated_root": GENERATED_ROOT,
            "override_suffix": OVERRIDE_SUFFIX,
            "destructive_update": False,
        },
        "metadata": dict(metadata),
    }
    validate_integration_manifest(manifest)
    return manifest


def validate_integration_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the public manifest without accessing engine APIs."""

    expected_keys = {
        "format_id",
        "schema_version",
        "generator",
        "engine",
        "source",
        "sync",
        "metadata",
    }
    if set(manifest) != expected_keys:
        raise ValueError("integration manifest keys do not match schema version 1")
    if manifest["format_id"] != INTEGRATION_FORMAT_ID:
        raise ValueError("unsupported integration manifest format")
    if manifest["schema_version"] != INTEGRATION_SCHEMA_VERSION:
        raise ValueError("unsupported integration manifest schema version")
    generator = manifest["generator"]
    if not isinstance(generator, Mapping) or generator.get("id") != APP_ID:
        raise ValueError("integration generator identity is invalid")
    if not isinstance(generator.get("version"), str) or not generator["version"]:
        raise ValueError("integration generator version is invalid")
    if manifest["engine"] not in SUPPORTED_ENGINES:
        raise ValueError("integration engine is not supported")

    source = manifest["source"]
    if not isinstance(source, Mapping) or set(source) != {"image", "metadata"}:
        raise ValueError("integration source section is invalid")
    image = source["image"]
    if not isinstance(image, Mapping) or set(image) != {"path", "sha256"}:
        raise ValueError("integration image source is invalid")
    reference = _relative_reference(image["path"])
    if (
        reference != image["path"]
        or not isinstance(image["sha256"], str)
        or len(image["sha256"]) != 64
    ):
        raise ValueError("integration image source hash or path is invalid")
    metadata_source = source["metadata"]
    metadata = manifest["metadata"]
    if not isinstance(metadata_source, Mapping) or not isinstance(metadata, Mapping):
        raise ValueError("integration metadata source is invalid")
    if metadata_source.get("format_id") != metadata.get("format_id"):
        raise ValueError("integration metadata format does not match payload")
    if metadata_source.get("schema_version") != metadata.get("schema_version"):
        raise ValueError("integration metadata version does not match payload")
    metadata_hash = metadata_source.get("sha256")
    if not isinstance(metadata_hash, str) or len(metadata_hash) != 64:
        raise ValueError("integration metadata hash is invalid")
    if metadata_hash != _sha256_bytes(_canonical_json_bytes(metadata)):
        raise ValueError("integration metadata hash does not match payload")

    sync = manifest["sync"]
    if sync != {
        "direction": "dtrace-to-engine",
        "generated_root": GENERATED_ROOT,
        "override_suffix": OVERRIDE_SUFFIX,
        "destructive_update": False,
    }:
        raise ValueError("integration sync policy is invalid")


def save_integration_manifest(manifest: Mapping[str, Any], path: str | Path) -> None:
    """Validate and atomically save a deterministic integration manifest."""

    validate_integration_manifest(manifest)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".neoeng-integration-", suffix=".json", dir=destination.parent
    )
    os.close(descriptor)
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = ""
    finally:
        if temporary and os.path.exists(temporary):
            os.remove(temporary)
