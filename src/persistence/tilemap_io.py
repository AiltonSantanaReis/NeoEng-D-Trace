"""Atomic, versioned persistence for the E04 tilemap document."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.core.tilemap_model import (
    TileCell,
    TileDefinition,
    TileLayer,
    TileMapBounds,
    TileMapDocument,
    TileMapError,
    TileSet,
)
from src.core.tilemap_rules import TileRuleSet

TILEMAP_FORMAT_ID = "neoeng-d-trace-tilemap"
TILEMAP_SCHEMA_VERSION = 1
MAX_TILEMAP_BYTES = 32 * 1024 * 1024


class TileMapPersistenceError(TileMapError):
    """Raised when a tilemap file cannot be safely read or written."""


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TileMapPersistenceError(f"{field} must be an object")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TileMapPersistenceError(f"{field} must be a string")
    return value


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TileMapPersistenceError(f"{field} must be an integer")
    return value


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TileMapPersistenceError(f"{field} must be a number")
    return float(value)


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise TileMapPersistenceError(f"{field} must be a boolean")
    return value


def _tuple_properties(value: object, field: str) -> tuple[tuple[str, str], ...]:
    mapping = _mapping(value, field)
    return tuple(
        sorted((_text(key, field), _text(item, field)) for key, item in mapping.items())
    )


def _tile_definition(value: object) -> TileDefinition:
    payload = _mapping(value, "tile")
    rect = _mapping(payload.get("source_rect"), "tile.source_rect")
    pivot = _mapping(payload.get("pivot"), "tile.pivot")
    frames = payload.get("animation_frames", [])
    if not isinstance(frames, list):
        raise TileMapPersistenceError("tile.animation_frames must be a list")
    return TileDefinition(
        id=_text(payload.get("id"), "tile.id"),
        asset_id=_text(payload.get("asset_id"), "tile.asset_id"),
        source_rect=(
            _integer(rect.get("x"), "tile.source_rect.x"),
            _integer(rect.get("y"), "tile.source_rect.y"),
            _integer(rect.get("w"), "tile.source_rect.w"),
            _integer(rect.get("h"), "tile.source_rect.h"),
        ),
        pivot=(
            _number(pivot.get("x"), "tile.pivot.x"),
            _number(pivot.get("y"), "tile.pivot.y"),
        ),
        variant=_text(payload.get("variant"), "tile.variant"),
        animation_frames=tuple(
            _text(frame, "tile.animation_frame") for frame in frames
        ),
        properties=_tuple_properties(payload.get("properties", {}), "tile.properties"),
        version=_integer(payload.get("version"), "tile.version"),
    )


def _tileset(value: object) -> TileSet:
    payload = _mapping(value, "tileset")
    tiles = payload.get("tiles")
    if not isinstance(tiles, list):
        raise TileMapPersistenceError("tileset.tiles must be a list")
    return TileSet(
        id=_text(payload.get("id"), "tileset.id"),
        atlas_asset_id=_text(payload.get("atlas_asset_id"), "tileset.atlas_asset_id"),
        atlas_sha256=_text(payload.get("atlas_sha256"), "tileset.atlas_sha256"),
        tiles=tuple(_tile_definition(item) for item in tiles),
        version=_integer(payload.get("version"), "tileset.version"),
        atlas_path=(
            None
            if payload.get("atlas_path") is None
            else _text(payload.get("atlas_path"), "tileset.atlas_path")
        ),
    )


def _layer(value: object) -> TileLayer:
    payload = _mapping(value, "layer")
    return TileLayer(
        id=_text(payload.get("id"), "layer.id"),
        name=_text(payload.get("name"), "layer.name"),
        order=_integer(payload.get("order"), "layer.order"),
        visible=_boolean(payload.get("visible"), "layer.visible"),
        locked=_boolean(payload.get("locked"), "layer.locked"),
        opacity=_number(payload.get("opacity"), "layer.opacity"),
    )


def load_tilemap(path: str | os.PathLike[str]) -> TileMapDocument:
    source = Path(path)
    if not source.is_file():
        raise TileMapPersistenceError(f"tilemap file not found: {source}")
    try:
        if source.stat().st_size > MAX_TILEMAP_BYTES:
            raise TileMapPersistenceError(
                "tilemap file exceeds the operational size limit"
            )
        payload = json.loads(source.read_text(encoding="utf-8"))
    except TileMapPersistenceError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TileMapPersistenceError(f"cannot read tilemap: {exc}") from exc
    root = _mapping(payload, "tilemap")
    if root.get("format_id") != TILEMAP_FORMAT_ID:
        raise TileMapPersistenceError("unsupported tilemap format")
    if root.get("schema_version") != TILEMAP_SCHEMA_VERSION:
        raise TileMapPersistenceError("unsupported tilemap schema version")
    bounds_payload = root.get("bounds")
    bounds = None
    if bounds_payload is not None:
        bounds_data = _mapping(bounds_payload, "bounds")
        bounds = TileMapBounds(
            _integer(bounds_data.get("min_x"), "bounds.min_x"),
            _integer(bounds_data.get("min_y"), "bounds.min_y"),
            _integer(bounds_data.get("max_x"), "bounds.max_x"),
            _integer(bounds_data.get("max_y"), "bounds.max_y"),
        )
    layers = root.get("layers")
    cells = root.get("cells")
    if not isinstance(layers, list) or not isinstance(cells, list):
        raise TileMapPersistenceError("tilemap layers and cells must be lists")
    loaded_layers = tuple(_layer(item) for item in layers)
    rule_set_payload = root.get("rules")
    if rule_set_payload is not None:
        try:
            rule_set_payload = TileRuleSet.from_dict(
                _mapping(rule_set_payload, "tilemap.rules")
            ).to_dict()
        except (TypeError, ValueError, TileMapError) as exc:
            raise TileMapPersistenceError(f"invalid tilemap rules: {exc}") from exc
    document = TileMapDocument(
        id=_text(root.get("id"), "tilemap.id"),
        name=_text(root.get("name"), "tilemap.name"),
        tileset=_tileset(root.get("tileset")),
        grid=_text(root.get("grid"), "tilemap.grid"),
        layers=tuple(
            TileLayer(
                layer.id,
                layer.name,
                layer.order,
                layer.visible,
                False,
                layer.opacity,
            )
            for layer in loaded_layers
        ),
        chunk_size=_integer(root.get("chunk_size"), "tilemap.chunk_size"),
        bounds=bounds,
        rule_set_payload=rule_set_payload,
    )
    seen: set[tuple[str, int, int]] = set()
    for item in cells:
        cell_payload = _mapping(item, "cell record")
        layer_id = _text(cell_payload.get("layer_id"), "cell.layer_id")
        x = _integer(cell_payload.get("x"), "cell.x")
        y = _integer(cell_payload.get("y"), "cell.y")
        key = (layer_id, x, y)
        if key in seen:
            raise TileMapPersistenceError("duplicate tilemap cell")
        seen.add(key)
        cell_data = _mapping(cell_payload.get("cell"), "cell.cell")
        document.set_cell(
            layer_id,
            (x, y),
            TileCell(
                _text(cell_data.get("tile_id"), "cell.tile_id"),
                _text(cell_data.get("variant"), "cell.variant"),
                _tuple_properties(cell_data.get("metadata", {}), "cell.metadata"),
            ),
        )
    for layer in loaded_layers:
        if layer.locked:
            document.set_layer_lock(layer.id, True)
    return document


def save_tilemap(document: TileMapDocument, path: str | os.PathLike[str]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(
                document.to_dict(), handle, ensure_ascii=False, indent=2, sort_keys=True
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    except OSError as exc:
        raise TileMapPersistenceError(f"cannot atomically save tilemap: {exc}") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    return destination


__all__ = [
    "MAX_TILEMAP_BYTES",
    "TILEMAP_FORMAT_ID",
    "TILEMAP_SCHEMA_VERSION",
    "TileMapPersistenceError",
    "load_tilemap",
    "save_tilemap",
]
