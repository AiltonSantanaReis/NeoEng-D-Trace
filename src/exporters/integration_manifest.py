"""Versioned source contracts consumed by the optional engine adapters."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from src.core.app_identity import APP_ID, APP_VERSION

INTEGRATION_FORMAT_ID = "neoeng-d-trace-engine-integration"
INTEGRATION_SCHEMA_VERSION = 1
ADVANCED_INTEGRATION_SCHEMA_VERSION = 2
ADVANCED_PAYLOAD_SCHEMA_VERSION = 1
SUPPORTED_ENGINES = frozenset({"godot", "unity"})
GENERATED_ROOT = "NeoEngGenerated"
OVERRIDE_SUFFIX = ".ndt.override.json"


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
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


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _rect(value: Any, field: str) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    result = {
        key: _finite(value.get(key), f"{field}.{key}") for key in ("x", "y", "w", "h")
    }
    if result["x"] < 0 or result["y"] < 0 or result["w"] <= 0 or result["h"] <= 0:
        raise ValueError(f"{field} must be inside a positive image rectangle")
    return result


def _validate_sync(sync: Any) -> None:
    if sync != {
        "direction": "dtrace-to-engine",
        "generated_root": GENERATED_ROOT,
        "override_suffix": OVERRIDE_SUFFIX,
        "destructive_update": False,
    }:
        raise ValueError("integration sync policy is invalid")


def _validate_common(manifest: Mapping[str, Any], schema_version: int) -> None:
    expected_keys = {
        "format_id",
        "schema_version",
        "generator",
        "engine",
        "source",
        "sync",
        "metadata",
    }
    if schema_version == ADVANCED_INTEGRATION_SCHEMA_VERSION:
        expected_keys.add("advanced")
    if set(manifest) != expected_keys:
        raise ValueError(
            f"integration manifest keys do not match schema version {schema_version}"
        )
    if manifest["format_id"] != INTEGRATION_FORMAT_ID:
        raise ValueError("unsupported integration manifest format")
    if manifest["schema_version"] != schema_version:
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
    _validate_sync(manifest["sync"])


def build_integration_manifest(
    metadata: Mapping[str, Any],
    *,
    engine: str,
    image_path: str | Path,
    image_reference: str,
    generator_version: str = APP_VERSION,
) -> dict[str, Any]:
    """Build the strict v1 manifest shared by the Godot and Unity adapters."""
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


def _default_engine_properties() -> dict[str, dict[str, Any]]:
    return {
        "godot": {
            "texture_filter": "nearest",
            "texture_repeat": "disabled",
            "centered": True,
            "z_index": 0,
        },
        "unity": {
            "pixels_per_unit": 100.0,
            "filter_mode": "Point",
            "wrap_mode": "Clamp",
            "sorting_layer": "Default",
            "sorting_order": 0,
            "z_depth": 0.0,
        },
    }


def build_advanced_integration_manifest(
    metadata: Mapping[str, Any],
    *,
    engine: str,
    image_path: str | Path,
    image_reference: str,
    atlas_pages: Sequence[Mapping[str, Any]],
    engine_properties: Mapping[str, Mapping[str, Any]] | None = None,
    generator_version: str = APP_VERSION,
) -> dict[str, Any]:
    """Build schema v2 from real atlas pages while retaining the v1 payload shape."""
    base = build_integration_manifest(
        metadata,
        engine=engine,
        image_path=image_path,
        image_reference=image_reference,
        generator_version=generator_version,
    )
    if (
        not isinstance(atlas_pages, Sequence)
        or isinstance(atlas_pages, (str, bytes))
        or not atlas_pages
    ):
        raise ValueError("advanced atlas_pages must be a non-empty sequence")
    properties = _default_engine_properties()
    if engine_properties is not None:
        for name in ("godot", "unity"):
            if name in engine_properties:
                if not isinstance(engine_properties[name], Mapping):
                    raise ValueError(
                        f"advanced engine properties for {name} must be an object"
                    )
                properties[name].update(dict(engine_properties[name]))
    pages: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    first_reference = _relative_reference(image_reference)
    for page_index, page in enumerate(atlas_pages):
        if not isinstance(page, Mapping):
            raise ValueError("advanced atlas page must be an object")
        file_path = page.get("file_path", page.get("path"))
        reference = _relative_reference(
            str(page.get("path", page.get("reference", "")))
        )
        if not isinstance(file_path, (str, Path)):
            raise ValueError("advanced atlas page file_path is required")
        raw_entries = page.get("entries")
        if (
            not isinstance(raw_entries, Sequence)
            or isinstance(raw_entries, (str, bytes))
            or not raw_entries
        ):
            raise ValueError("advanced atlas page entries must be non-empty")
        page_width = page.get("width")
        page_height = page.get("height")
        if page_width is None or page_height is None:
            from PIL import Image

            with Image.open(file_path) as atlas_image:
                page_width, page_height = atlas_image.size
        page_data: dict[str, Any] = {
            "id": str(page.get("id", f"atlas_{page_index}")),
            "path": reference,
            "sha256": _sha256_file(file_path),
            "width": _positive_int(page_width, "advanced atlas page width"),
            "height": _positive_int(page_height, "advanced atlas page height"),
            "sprites": [],
        }
        for entry in raw_entries:
            if not isinstance(entry, Mapping):
                raise ValueError("advanced atlas sprite entry must be an object")
            object_id = entry.get("name", entry.get("id"))
            if not isinstance(object_id, str) or not object_id or object_id in seen_ids:
                raise ValueError(
                    "advanced atlas sprite ids must be unique and non-empty"
                )
            rect = _rect(entry.get("rect"), f"advanced atlas sprite {object_id}.rect")
            packed_rect = _rect(
                entry.get("packed_rect"),
                f"advanced atlas sprite {object_id}.packed_rect",
            )
            extrusion = _non_negative_int(
                entry.get("extrusion"), f"advanced atlas sprite {object_id}.extrusion"
            )
            rotated = entry.get("rotated")
            if not isinstance(rotated, bool):
                raise ValueError(
                    f"advanced atlas sprite {object_id}.rotated must be boolean"
                )
            seen_ids.add(object_id)
            page_data["sprites"].append(
                {
                    "id": object_id,
                    "rect": rect,
                    "packed_rect": packed_rect,
                    "extrusion": extrusion,
                    "rotated": rotated,
                }
            )
        pages.append(page_data)
    metadata_ids = {
        str(item.get("id"))
        for item in metadata.get("sprites", [])
        if isinstance(item, Mapping)
    }
    if metadata_ids != seen_ids:
        raise ValueError(
            "advanced atlas entries must cover metadata sprites exactly once"
        )
    if pages[0]["path"] != first_reference:
        raise ValueError(
            "source image reference must point to the first advanced atlas page"
        )
    bleed_values = {sprite["extrusion"] for page in pages for sprite in page["sprites"]}
    if len(bleed_values) != 1:
        raise ValueError("advanced atlas extrusion must be uniform across pages")
    advanced = {
        "schema_version": ADVANCED_PAYLOAD_SCHEMA_VERSION,
        "coordinate_system": {
            "image_origin": "top-left",
            "polygon_origin": "sprite-top-left",
            "engine_y_axis": "up",
            "pixels_per_unit": {
                "godot": 1.0,
                "unity": float(properties["unity"]["pixels_per_unit"]),
            },
        },
        "atlas": {"bleed": next(iter(bleed_values)), "pages": pages},
        "engine_properties": properties,
    }
    manifest = dict(base)
    manifest["schema_version"] = ADVANCED_INTEGRATION_SCHEMA_VERSION
    manifest["advanced"] = advanced
    validate_integration_manifest(manifest)
    return manifest


def _validate_advanced(manifest: Mapping[str, Any]) -> None:
    advanced = manifest.get("advanced")
    if not isinstance(advanced, Mapping) or set(advanced) != {
        "schema_version",
        "coordinate_system",
        "atlas",
        "engine_properties",
    }:
        raise ValueError("advanced integration contract is invalid")
    if advanced["schema_version"] != ADVANCED_PAYLOAD_SCHEMA_VERSION:
        raise ValueError("advanced integration payload schema is unsupported")
    coordinates = advanced["coordinate_system"]
    if not isinstance(coordinates, Mapping) or set(coordinates) != {
        "image_origin",
        "polygon_origin",
        "engine_y_axis",
        "pixels_per_unit",
    }:
        raise ValueError("advanced coordinate contract is invalid")
    if (
        coordinates["image_origin"] != "top-left"
        or coordinates["polygon_origin"] != "sprite-top-left"
        or coordinates["engine_y_axis"] != "up"
    ):
        raise ValueError("advanced coordinate contract values are invalid")
    ppu = coordinates["pixels_per_unit"]
    if (
        not isinstance(ppu, Mapping)
        or set(ppu) != {"godot", "unity"}
        or _finite(ppu["godot"], "pixels_per_unit.godot") <= 0
        or _finite(ppu["unity"], "pixels_per_unit.unity") <= 0
    ):
        raise ValueError("advanced pixels_per_unit is invalid")
    atlas = advanced["atlas"]
    if not isinstance(atlas, Mapping) or set(atlas) != {"bleed", "pages"}:
        raise ValueError("advanced atlas contract is invalid")
    bleed = _non_negative_int(atlas["bleed"], "advanced atlas bleed")
    pages = atlas["pages"]
    if not isinstance(pages, Sequence) or isinstance(pages, (str, bytes)) or not pages:
        raise ValueError("advanced atlas pages must be non-empty")
    ids: set[str] = set()
    for page in pages:
        if not isinstance(page, Mapping) or set(page) != {
            "id",
            "path",
            "sha256",
            "width",
            "height",
            "sprites",
        }:
            raise ValueError("advanced atlas page contract is invalid")
        if (
            not isinstance(page["id"], str)
            or not page["id"]
            or _relative_reference(page["path"]) != page["path"]
        ):
            raise ValueError("advanced atlas page identity or path is invalid")
        if not isinstance(page["sha256"], str) or len(page["sha256"]) != 64:
            raise ValueError("advanced atlas page hash is invalid")
        _positive_int(page["width"], "advanced atlas page width")
        _positive_int(page["height"], "advanced atlas page height")
        sprites = page["sprites"]
        if (
            not isinstance(sprites, Sequence)
            or isinstance(sprites, (str, bytes))
            or not sprites
        ):
            raise ValueError("advanced atlas page sprites must be non-empty")
        for sprite in sprites:
            if not isinstance(sprite, Mapping) or set(sprite) != {
                "id",
                "rect",
                "packed_rect",
                "extrusion",
                "rotated",
            }:
                raise ValueError("advanced atlas sprite contract is invalid")
            if (
                not isinstance(sprite["id"], str)
                or not sprite["id"]
                or sprite["id"] in ids
            ):
                raise ValueError("advanced atlas sprite ids must be unique")
            ids.add(sprite["id"])
            _rect(sprite["rect"], "advanced atlas sprite rect")
            _rect(sprite["packed_rect"], "advanced atlas sprite packed_rect")
            if _non_negative_int(
                sprite["extrusion"], "advanced atlas sprite extrusion"
            ) != bleed or not isinstance(sprite["rotated"], bool):
                raise ValueError(
                    "advanced atlas sprite extrusion or rotation is invalid"
                )
    properties = advanced["engine_properties"]
    if not isinstance(properties, Mapping) or set(properties) != {"godot", "unity"}:
        raise ValueError("advanced engine properties are invalid")
    godot = properties["godot"]
    if (
        not isinstance(godot, Mapping)
        or set(godot) != {"texture_filter", "texture_repeat", "centered", "z_index"}
        or godot["texture_filter"] not in {"nearest", "linear"}
        or godot["texture_repeat"] not in {"disabled", "enabled"}
        or not isinstance(godot["centered"], bool)
        or isinstance(godot["z_index"], bool)
        or not isinstance(godot["z_index"], int)
    ):
        raise ValueError("advanced Godot properties are invalid")
    unity = properties["unity"]
    if (
        not isinstance(unity, Mapping)
        or set(unity)
        != {
            "pixels_per_unit",
            "filter_mode",
            "wrap_mode",
            "sorting_layer",
            "sorting_order",
            "z_depth",
        }
        or _finite(unity["pixels_per_unit"], "Unity pixels_per_unit") <= 0
        or unity["filter_mode"] not in {"Point", "Bilinear"}
        or unity["wrap_mode"] not in {"Clamp", "Repeat", "Mirror"}
        or not isinstance(unity["sorting_layer"], str)
        or not unity["sorting_layer"]
        or isinstance(unity["sorting_order"], bool)
        or not isinstance(unity["sorting_order"], int)
        or not math.isfinite(_finite(unity["z_depth"], "Unity z_depth"))
    ):
        raise ValueError("advanced Unity properties are invalid")
    metadata_ids = {
        str(item.get("id"))
        for item in manifest["metadata"].get("sprites", [])
        if isinstance(item, Mapping)
    }
    if ids != metadata_ids:
        raise ValueError("advanced atlas sprites do not match metadata sprites")


def validate_integration_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate v1 or the explicit v2 advanced manifest without engine APIs."""
    if not isinstance(manifest, Mapping):
        raise ValueError("integration manifest must be a mapping")
    schema_version = manifest.get("schema_version")
    if schema_version not in {
        INTEGRATION_SCHEMA_VERSION,
        ADVANCED_INTEGRATION_SCHEMA_VERSION,
    }:
        raise ValueError("unsupported integration manifest schema version")
    _validate_common(manifest, schema_version)
    if schema_version == ADVANCED_INTEGRATION_SCHEMA_VERSION:
        _validate_advanced(manifest)


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
