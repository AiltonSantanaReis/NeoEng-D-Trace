"""Strict, engine-neutral tilemap runtime package export.

The authoring tilemap is intentionally sparse and destination-neutral.  Runtime
adapters need a small, explicit contract that binds the authored cells to the
exact atlas bytes that were used to author them.  This module creates that
contract and refuses unsafe paths, missing atlases, and asset drift.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from typing import Any, Mapping

from src.core.tilemap_model import TileMapDocument, TileMapError
from src.core.tilemap_rules import TileRuleSet
from src.persistence.tilemap_io import load_tilemap

TILEMAP_RUNTIME_FORMAT_ID = "neoeng-d-trace-tilemap-runtime"
TILEMAP_RUNTIME_SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TileMapRuntimeExportError(TileMapError):
    """Raised when a runtime tilemap cannot be exported safely."""


@dataclass(frozen=True)
class TileMapRuntimePackage:
    """Files produced for a runtime adapter without mutating source assets."""

    directory: Path
    payload_path: Path
    tilemap_path: Path
    atlas_path: Path
    payload: dict[str, Any]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise TileMapRuntimeExportError(f"cannot read asset: {path}") from exc
    return digest.hexdigest()


def _safe_relative_reference(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TileMapRuntimeExportError(f"{field} must be a relative path")
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if (
        normalized.startswith("/")
        or ":" in normalized
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise TileMapRuntimeExportError(f"{field} must be a safe relative path")
    return normalized


def _relative_path(path: Path, root: Path, field: str) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise TileMapRuntimeExportError(
            f"{field} must be inside the runtime project root"
        ) from exc
    return _safe_relative_reference(relative.as_posix(), field)


def _resolve_reference(root: Path, reference: object, field: str) -> Path:
    safe_reference = _safe_relative_reference(reference, field)
    resolved_root = root.resolve()
    resolved = (resolved_root / Path(*safe_reference.split("/"))).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise TileMapRuntimeExportError(
            f"{field} resolves outside the runtime project root"
        ) from exc
    return resolved


def _sha256_text_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise TileMapRuntimeExportError(f"cannot read source tilemap: {path}") from exc


def _rules_payload(document: TileMapDocument) -> dict[str, Any]:
    if document.rule_set_payload is None:
        return {
            "fallback_tile_id": document.tileset.tiles[0].id,
            "rules": [],
        }
    try:
        return TileRuleSet.from_dict(document.rule_set_payload).to_dict()
    except (TypeError, ValueError, TileMapError) as exc:
        raise TileMapRuntimeExportError(f"invalid tilemap rules: {exc}") from exc


def _cell_payload(document: TileMapDocument) -> list[dict[str, Any]]:
    return [
        {
            "layer_id": layer_id,
            "x": coordinate[0],
            "y": coordinate[1],
            "tile_id": cell.tile_id,
            "variant": cell.variant,
            "metadata": dict(cell.metadata),
        }
        for layer_id, coordinate, cell in document.iter_cells()
    ]


def build_tilemap_runtime_payload(
    document: TileMapDocument,
    *,
    tilemap_path: str | os.PathLike[str],
    project_root: str | os.PathLike[str],
    source_reference: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic runtime payload bound to source and atlas bytes."""

    source_path = Path(tilemap_path)
    root = Path(project_root)
    if not source_path.is_file():
        raise TileMapRuntimeExportError(f"source tilemap not found: {source_path}")
    if not root.is_dir():
        raise TileMapRuntimeExportError(f"project root not found: {root}")
    source_path = source_path.resolve()
    root = root.resolve()
    source_path_reference = (
        _safe_relative_reference(source_reference, "source.path")
        if source_reference is not None
        else _relative_path(source_path, root, "source.path")
    )
    atlas_reference = document.tileset.atlas_path
    if atlas_reference is None:
        raise TileMapRuntimeExportError(
            "runtime atlas path is required; save the tileset with atlas_path first"
        )
    atlas_path = _resolve_reference(root, atlas_reference, "atlas.path")
    if not atlas_path.is_file():
        raise TileMapRuntimeExportError(f"runtime atlas not found: {atlas_reference}")
    actual_atlas_sha = _sha256_file(atlas_path)
    if actual_atlas_sha != document.tileset.atlas_sha256:
        raise TileMapRuntimeExportError(
            "runtime atlas hash mismatch: authored tileset does not match atlas bytes"
        )
    rules = _rules_payload(document)
    tiles = [tile.to_dict() for tile in document.tileset.tiles]
    cells = _cell_payload(document)
    payload: dict[str, Any] = {
        "format_id": TILEMAP_RUNTIME_FORMAT_ID,
        "schema_version": TILEMAP_RUNTIME_SCHEMA_VERSION,
        "generator": "NeoEng-D-Trace tilemap runtime exporter",
        "source": {
            "path": source_path_reference,
            "sha256": _sha256_text_file(source_path),
            "bytes": source_path.stat().st_size,
        },
        "id": document.id,
        "name": document.name,
        "grid": document.grid,
        "chunk_size": document.chunk_size,
        "bounds": None if document.bounds is None else document.bounds.to_dict(),
        "tileset": {
            "id": document.tileset.id,
            "atlas_asset_id": document.tileset.atlas_asset_id,
            "atlas_sha256": document.tileset.atlas_sha256,
            "version": document.tileset.version,
            "tiles": tiles,
        },
        "atlas": {
            "path": _safe_relative_reference(atlas_reference, "atlas.path"),
            "sha256": actual_atlas_sha,
            "bytes": atlas_path.stat().st_size,
        },
        "layers": [layer.to_dict() for layer in document.layers],
        "cells": cells,
        "rules": rules,
        "counts": {
            "layers": len(document.layers),
            "tiles": len(tiles),
            "cells": len(cells),
            "rules": len(rules["rules"]),
        },
    }
    validate_tilemap_runtime_payload(payload)
    return payload


def _require_mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TileMapRuntimeExportError(f"{field} must be an object")
    return value


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TileMapRuntimeExportError(f"{field} must be a non-empty string")
    return value


def _require_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TileMapRuntimeExportError(f"{field} must be an integer")
    return value


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise TileMapRuntimeExportError(f"{field} must be a boolean")
    return value


def _require_sha(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise TileMapRuntimeExportError(f"{field} must be a lowercase SHA-256")
    return value


def _validate_rect(value: object, field: str) -> None:
    rect = _require_mapping(value, field)
    for name in ("x", "y", "w", "h"):
        number = _require_int(rect.get(name), f"{field}.{name}")
        if name in {"x", "y"} and number < 0:
            raise TileMapRuntimeExportError(f"{field}.{name} must be non-negative")
        if name in {"w", "h"} and number <= 0:
            raise TileMapRuntimeExportError(f"{field}.{name} must be positive")


def _validate_rules(value: object, tile_ids: set[str]) -> tuple[dict[str, Any], int]:
    rules = _require_mapping(value, "rules")
    fallback = _require_text(rules.get("fallback_tile_id"), "rules.fallback_tile_id")
    if fallback not in tile_ids:
        raise TileMapRuntimeExportError("rules fallback tile ID is not in the tileset")
    rule_entries = rules.get("rules")
    if not isinstance(rule_entries, list):
        raise TileMapRuntimeExportError("rules.rules must be a list")
    try:
        normalized = TileRuleSet.from_dict(rules).to_dict()
    except (TypeError, ValueError, TileMapError) as exc:
        raise TileMapRuntimeExportError(f"invalid runtime rules: {exc}") from exc
    for rule in normalized["rules"]:
        if rule["target_tile_id"] not in tile_ids:
            raise TileMapRuntimeExportError(
                f"rule target tile ID is not in the tileset: {rule['target_tile_id']}"
            )
        for condition in rule["conditions"]:
            if any(
                tile_id not in tile_ids for tile_id in condition["allowed_tile_ids"]
            ):
                raise TileMapRuntimeExportError(
                    f"rule condition references an unknown tile ID: {rule['id']}"
                )
    return normalized, len(normalized["rules"])


def validate_tilemap_runtime_payload(
    payload: Mapping[str, Any],
    *,
    project_root: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Validate structure, references, counts, and optionally bytes on disk."""

    if not isinstance(payload, Mapping):
        raise TileMapRuntimeExportError("runtime payload must be an object")
    if payload.get("format_id") != TILEMAP_RUNTIME_FORMAT_ID:
        raise TileMapRuntimeExportError("unsupported tilemap runtime format")
    if payload.get("schema_version") != TILEMAP_RUNTIME_SCHEMA_VERSION:
        raise TileMapRuntimeExportError("unsupported tilemap runtime schema version")
    source = _require_mapping(payload.get("source"), "source")
    source_path = _safe_relative_reference(source.get("path"), "source.path")
    source_sha = _require_sha(source.get("sha256"), "source.sha256")
    source_bytes = _require_int(source.get("bytes"), "source.bytes")
    if source_bytes <= 0:
        raise TileMapRuntimeExportError("source.bytes must be positive")
    atlas = _require_mapping(payload.get("atlas"), "atlas")
    atlas_path = _safe_relative_reference(atlas.get("path"), "atlas.path")
    atlas_sha = _require_sha(atlas.get("sha256"), "atlas.sha256")
    atlas_bytes = _require_int(atlas.get("bytes"), "atlas.bytes")
    if atlas_bytes <= 0:
        raise TileMapRuntimeExportError("atlas.bytes must be positive")
    grid = payload.get("grid")
    if grid not in {"orthogonal", "isometric", "hexagonal"}:
        raise TileMapRuntimeExportError("runtime grid is unsupported")
    _require_text(payload.get("id"), "id")
    _require_text(payload.get("name"), "name")
    chunk_size = _require_int(payload.get("chunk_size"), "chunk_size")
    if chunk_size < 8 or chunk_size > 128 or chunk_size & (chunk_size - 1):
        raise TileMapRuntimeExportError(
            "runtime chunk_size must be a power of two 8..128"
        )
    bounds = payload.get("bounds")
    if bounds is not None:
        bounds_data = _require_mapping(bounds, "bounds")
        for name in ("min_x", "min_y", "max_x", "max_y"):
            _require_int(bounds_data.get(name), f"bounds.{name}")
        if (
            bounds_data["max_x"] < bounds_data["min_x"]
            or bounds_data["max_y"] < bounds_data["min_y"]
        ):
            raise TileMapRuntimeExportError("runtime bounds must be ordered")

    tileset = _require_mapping(payload.get("tileset"), "tileset")
    _require_text(tileset.get("id"), "tileset.id")
    _require_text(tileset.get("atlas_asset_id"), "tileset.atlas_asset_id")
    tileset_sha = _require_sha(tileset.get("atlas_sha256"), "tileset.atlas_sha256")
    if tileset_sha != atlas_sha:
        raise TileMapRuntimeExportError("tileset and atlas hashes do not match")
    _require_int(tileset.get("version"), "tileset.version")
    tile_entries = tileset.get("tiles")
    if not isinstance(tile_entries, list) or not tile_entries:
        raise TileMapRuntimeExportError("tileset.tiles must be a non-empty list")
    tile_ids: set[str] = set()
    for tile in tile_entries:
        tile_data = _require_mapping(tile, "tile")
        tile_id = _require_text(tile_data.get("id"), "tile.id")
        if tile_id in tile_ids:
            raise TileMapRuntimeExportError(f"duplicate tile ID: {tile_id}")
        tile_ids.add(tile_id)
        _require_text(tile_data.get("asset_id"), "tile.asset_id")
        _validate_rect(tile_data.get("source_rect"), "tile.source_rect")
        pivot = _require_mapping(tile_data.get("pivot"), "tile.pivot")
        for name in ("x", "y"):
            value = pivot.get(name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                raise TileMapRuntimeExportError(
                    f"tile.pivot.{name} must be between 0 and 1"
                )
        _require_text(tile_data.get("variant"), "tile.variant")
        frames = tile_data.get("animation_frames", [])
        if not isinstance(frames, list) or any(
            not isinstance(frame, str) for frame in frames
        ):
            raise TileMapRuntimeExportError(
                "tile.animation_frames must be a list of strings"
            )
        _require_mapping(tile_data.get("properties", {}), "tile.properties")
        _require_int(tile_data.get("version"), "tile.version")

    layers = payload.get("layers")
    if not isinstance(layers, list) or not layers:
        raise TileMapRuntimeExportError("layers must be a non-empty list")
    layer_ids: set[str] = set()
    for layer in layers:
        layer_data = _require_mapping(layer, "layer")
        layer_id = _require_text(layer_data.get("id"), "layer.id")
        if layer_id in layer_ids:
            raise TileMapRuntimeExportError(f"duplicate layer ID: {layer_id}")
        layer_ids.add(layer_id)
        _require_text(layer_data.get("name"), "layer.name")
        _require_int(layer_data.get("order"), "layer.order")
        _require_bool(layer_data.get("visible"), "layer.visible")
        _require_bool(layer_data.get("locked"), "layer.locked")
        opacity = layer_data.get("opacity")
        if (
            isinstance(opacity, bool)
            or not isinstance(opacity, (int, float))
            or not 0 <= opacity <= 1
        ):
            raise TileMapRuntimeExportError("layer.opacity must be between 0 and 1")

    cells = payload.get("cells")
    if not isinstance(cells, list):
        raise TileMapRuntimeExportError("cells must be a list")
    cell_keys: set[tuple[str, int, int]] = set()
    for cell in cells:
        cell_data = _require_mapping(cell, "cell")
        layer_id = _require_text(cell_data.get("layer_id"), "cell.layer_id")
        if layer_id not in layer_ids:
            raise TileMapRuntimeExportError(
                f"cell references unknown layer: {layer_id}"
            )
        x = _require_int(cell_data.get("x"), "cell.x")
        y = _require_int(cell_data.get("y"), "cell.y")
        key = (layer_id, x, y)
        if key in cell_keys:
            raise TileMapRuntimeExportError(f"duplicate runtime cell: {key}")
        cell_keys.add(key)
        tile_id = _require_text(cell_data.get("tile_id"), "cell.tile_id")
        if tile_id not in tile_ids:
            raise TileMapRuntimeExportError(f"cell references unknown tile: {tile_id}")
        _require_text(cell_data.get("variant"), "cell.variant")
        _require_mapping(cell_data.get("metadata", {}), "cell.metadata")
        if bounds is not None and not (
            bounds["min_x"] <= x <= bounds["max_x"]
            and bounds["min_y"] <= y <= bounds["max_y"]
        ):
            raise TileMapRuntimeExportError(f"cell is outside runtime bounds: {key}")

    _normalized_rules, rule_count = _validate_rules(payload.get("rules"), tile_ids)
    counts = _require_mapping(payload.get("counts"), "counts")
    expected_counts = {
        "layers": len(layers),
        "tiles": len(tile_entries),
        "cells": len(cells),
        "rules": rule_count,
    }
    if {key: counts.get(key) for key in expected_counts} != expected_counts:
        raise TileMapRuntimeExportError("runtime counts do not match payload contents")

    if project_root is not None:
        root = Path(project_root).resolve()
        source_file = _resolve_reference(root, source_path, "source.path")
        atlas_file = _resolve_reference(root, atlas_path, "atlas.path")
        if (
            not source_file.is_file()
            or source_file.stat().st_size != source_bytes
            or _sha256_file(source_file) != source_sha
        ):
            raise TileMapRuntimeExportError("source tilemap hash mismatch")
        if not atlas_file.is_file():
            raise TileMapRuntimeExportError("runtime atlas file is missing")
        if (
            atlas_file.stat().st_size != atlas_bytes
            or _sha256_file(atlas_file) != atlas_sha
        ):
            raise TileMapRuntimeExportError("runtime atlas hash or byte-size mismatch")
    return dict(payload)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as exc:
        raise TileMapRuntimeExportError(
            f"cannot write runtime payload: {path}"
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_tilemap_runtime_package(
    tilemap_path: str | os.PathLike[str],
    *,
    project_root: str | os.PathLike[str],
    destination: str | os.PathLike[str],
) -> TileMapRuntimePackage:
    """Copy source tilemap/atlas and emit a validated, self-contained package."""

    source = Path(tilemap_path).resolve()
    root = Path(project_root).resolve()
    output = Path(destination).resolve()
    if output.exists():
        raise TileMapRuntimeExportError(
            f"refusing to overwrite existing runtime package: {output}"
        )
    try:
        document = load_tilemap(source)
    except TileMapError as exc:
        raise TileMapRuntimeExportError(f"cannot load source tilemap: {exc}") from exc
    output.mkdir(parents=True)
    copied_tilemap = output / "tilemap.json"
    copy2(source, copied_tilemap)
    atlas_reference = _safe_relative_reference(
        document.tileset.atlas_path, "atlas.path"
    )
    source_atlas = _resolve_reference(root, atlas_reference, "atlas.path")
    copied_atlas = _resolve_reference(output, atlas_reference, "atlas.path")
    copied_atlas.parent.mkdir(parents=True, exist_ok=True)
    copy2(source_atlas, copied_atlas)
    payload = build_tilemap_runtime_payload(
        document,
        tilemap_path=copied_tilemap,
        project_root=output,
        source_reference="tilemap.json",
    )
    payload_path = output / "tilemap-runtime.json"
    _write_json(payload_path, payload)
    validate_tilemap_runtime_payload(payload, project_root=output)
    return TileMapRuntimePackage(
        directory=output,
        payload_path=payload_path,
        tilemap_path=copied_tilemap,
        atlas_path=copied_atlas,
        payload=payload,
    )


__all__ = [
    "TILEMAP_RUNTIME_FORMAT_ID",
    "TILEMAP_RUNTIME_SCHEMA_VERSION",
    "TileMapRuntimeExportError",
    "TileMapRuntimePackage",
    "build_tilemap_runtime_package",
    "build_tilemap_runtime_payload",
    "validate_tilemap_runtime_payload",
]
