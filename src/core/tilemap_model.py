"""Validated sparse TileSet/TileMap model for the E04 authoring contract.

The model deliberately has no Qt dependency.  Maps store only populated cells
inside sparse chunks, and edits can be represented as cell deltas so the UI can
provide transactional Undo/Redo without copying a complete map.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Mapping

TileCoordinate = tuple[int, int]
ChunkCoordinate = tuple[int, int]
MAX_TILE_ID_LENGTH = 256
MAX_TILESET_TILES = 65_536
MAX_TILEMAP_LAYERS = 256
MAX_TILEMAP_CELLS = 4_000_000
MAX_TILEMAP_CHUNKS = 250_000
MIN_CHUNK_SIZE = 8
MAX_CHUNK_SIZE = 128
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}$")


class TileMapError(ValueError):
    """Base error for invalid or unsafe tilemap operations."""


class TileMapLimitError(TileMapError):
    """Raised when an operational map limit would be exceeded."""


class TileMapLockedError(TileMapError):
    """Raised when a mutation targets a locked layer."""


def _check_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise TileMapError(f"{field} must be a non-empty portable identifier")
    return value


def _check_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TileMapError(f"{field} must be an integer")
    return value


def _check_finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TileMapError(f"{field} must be a finite number")
    result = float(value)
    if result != result or result in (float("inf"), float("-inf")):
        raise TileMapError(f"{field} must be a finite number")
    return result


def _check_rect(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    if len(rect) != 4:
        raise TileMapError("tile source_rect must contain four integers")
    x, y, width, height = (_check_int(value, "tile source_rect") for value in rect)
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise TileMapError("tile source_rect must be non-negative with positive size")
    return x, y, width, height


def _check_properties(
    properties: Mapping[str, str] | Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    values = dict(properties)
    if any(not isinstance(key, str) or not key for key in values):
        raise TileMapError("tile properties must use non-empty string keys")
    if any(not isinstance(value, str) for value in values.values()):
        raise TileMapError("tile properties must use string values")
    return tuple(sorted(values.items()))


def _check_relative_path(value: object, field: str) -> str | None:
    """Validate an optional project-relative path without touching the filesystem."""

    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise TileMapError(f"{field} must be a relative path")
    normalized = value.replace("\\", "/")
    if (
        normalized.startswith("/")
        or ":" in normalized
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise TileMapError(f"{field} must be a safe relative path")
    return normalized


@dataclass(frozen=True)
class TileDefinition:
    """Stable tile identity and versioned atlas metadata."""

    id: str
    asset_id: str
    source_rect: tuple[int, int, int, int]
    pivot: tuple[float, float] = (0.5, 0.5)
    variant: str = "default"
    animation_frames: tuple[str, ...] = ()
    properties: tuple[tuple[str, str], ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        _check_id(self.id, "tile id")
        _check_id(self.asset_id, "tile asset_id")
        _check_rect(self.source_rect)
        if len(self.pivot) != 2:
            raise TileMapError("tile pivot must contain two values")
        for value in self.pivot:
            pivot = _check_finite_number(value, "tile pivot")
            if pivot < 0 or pivot > 1:
                raise TileMapError("tile pivot values must be between 0 and 1")
        if not isinstance(self.variant, str) or not self.variant:
            raise TileMapError("tile variant must be non-empty")
        if any(
            not isinstance(frame, str) or not frame for frame in self.animation_frames
        ):
            raise TileMapError("tile animation frame IDs must be non-empty")
        _check_properties(self.properties)
        version = _check_int(self.version, "tile version")
        if version <= 0:
            raise TileMapError("tile version must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "source_rect": {
                "x": self.source_rect[0],
                "y": self.source_rect[1],
                "w": self.source_rect[2],
                "h": self.source_rect[3],
            },
            "pivot": {"x": self.pivot[0], "y": self.pivot[1]},
            "variant": self.variant,
            "animation_frames": list(self.animation_frames),
            "properties": dict(self.properties),
            "version": self.version,
        }


@dataclass(frozen=True)
class TileSet:
    """Tile library independent of any map position."""

    id: str
    atlas_asset_id: str
    atlas_sha256: str
    tiles: tuple[TileDefinition, ...]
    version: int = 1
    atlas_path: str | None = None

    def __post_init__(self) -> None:
        _check_id(self.id, "tileset id")
        _check_id(self.atlas_asset_id, "tileset atlas_asset_id")
        if not re.fullmatch(r"[0-9a-f]{64}", self.atlas_sha256):
            raise TileMapError("tileset atlas_sha256 must be lowercase SHA-256")
        if not self.tiles:
            raise TileMapError("tileset must contain at least one tile")
        if len(self.tiles) > MAX_TILESET_TILES:
            raise TileMapLimitError("tileset exceeds the tile limit")
        ids = [tile.id for tile in self.tiles]
        if len(ids) != len(set(ids)):
            raise TileMapError("tile IDs must be unique within a tileset")
        version = _check_int(self.version, "tileset version")
        if version <= 0:
            raise TileMapError("tileset version must be positive")
        _check_relative_path(self.atlas_path, "tileset atlas_path")

    def tile(self, tile_id: str) -> TileDefinition:
        for tile in self.tiles:
            if tile.id == tile_id:
                return tile
        raise TileMapError(f"unknown tile ID: {tile_id}")

    def has_tile(self, tile_id: str) -> bool:
        return any(tile.id == tile_id for tile in self.tiles)

    def verify_atlas(self, actual_bytes: bytes) -> bool:
        """Return whether the runtime atlas still matches the authored hash."""

        return hashlib.sha256(actual_bytes).hexdigest() == self.atlas_sha256

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "atlas_asset_id": self.atlas_asset_id,
            "atlas_sha256": self.atlas_sha256,
            "version": self.version,
            "tiles": [tile.to_dict() for tile in self.tiles],
        }
        if self.atlas_path is not None:
            payload["atlas_path"] = self.atlas_path
        return payload


@dataclass(frozen=True)
class TileCell:
    """One occupied cell, independent of its map coordinate."""

    tile_id: str
    variant: str = "default"
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _check_id(self.tile_id, "cell tile_id")
        if not isinstance(self.variant, str) or not self.variant:
            raise TileMapError("cell variant must be non-empty")
        _check_properties(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tile_id": self.tile_id,
            "variant": self.variant,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TileLayer:
    """Layer metadata; cell contents stay in the map's sparse chunk store."""

    id: str
    name: str
    order: int
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0

    def __post_init__(self) -> None:
        _check_id(self.id, "layer id")
        if not isinstance(self.name, str) or not self.name.strip():
            raise TileMapError("layer name must be non-empty")
        _check_int(self.order, "layer order")
        opacity = _check_finite_number(self.opacity, "layer opacity")
        if opacity < 0 or opacity > 1:
            raise TileMapError("layer opacity must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "visible": self.visible,
            "locked": self.locked,
            "opacity": self.opacity,
        }


@dataclass(frozen=True)
class TileMapBounds:
    """Inclusive finite cell bounds; ``None`` means a bounded operational map."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int

    def __post_init__(self) -> None:
        for name, value in (
            ("min_x", self.min_x),
            ("min_y", self.min_y),
            ("max_x", self.max_x),
            ("max_y", self.max_y),
        ):
            _check_int(value, f"bounds.{name}")
        if self.max_x < self.min_x or self.max_y < self.min_y:
            raise TileMapError("map bounds must be ordered")
        area = (self.max_x - self.min_x + 1) * (self.max_y - self.min_y + 1)
        if area > MAX_TILEMAP_CELLS:
            raise TileMapLimitError("map bounds exceed the operational cell limit")

    def contains(self, coordinate: TileCoordinate) -> bool:
        x, y = coordinate
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def to_dict(self) -> dict[str, int]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
        }


@dataclass(frozen=True)
class TileCellDelta:
    """Atomic before/after change used by tools and history."""

    layer_id: str
    coordinate: TileCoordinate
    before: TileCell | None
    after: TileCell | None


class TileMapDocument:
    """Sparse, bounded, mutable document with atomic delta application."""

    def __init__(
        self,
        *,
        id: str,
        name: str,
        tileset: TileSet,
        grid: str,
        layers: Iterable[TileLayer],
        chunk_size: int = 64,
        bounds: TileMapBounds | None = None,
        rule_set_payload: Mapping[str, Any] | None = None,
    ) -> None:
        _check_id(id, "map id")
        if not isinstance(name, str) or not name.strip():
            raise TileMapError("map name must be non-empty")
        if grid not in {"orthogonal", "isometric", "hexagonal"}:
            raise TileMapError("grid must be orthogonal, isometric or hexagonal")
        chunk = _check_int(chunk_size, "chunk_size")
        if chunk < MIN_CHUNK_SIZE or chunk > MAX_CHUNK_SIZE:
            raise TileMapError(
                f"chunk_size must be between {MIN_CHUNK_SIZE} and {MAX_CHUNK_SIZE}"
            )
        if chunk & (chunk - 1):
            raise TileMapError("chunk_size must be a power of two")
        layer_tuple = tuple(layers)
        if not layer_tuple:
            raise TileMapError("tilemap must contain at least one layer")
        if len(layer_tuple) > MAX_TILEMAP_LAYERS:
            raise TileMapLimitError("tilemap exceeds the layer limit")
        ids = [layer.id for layer in layer_tuple]
        if len(ids) != len(set(ids)):
            raise TileMapError("layer IDs must be unique")
        self.id = id
        self.name = name
        self.tileset = tileset
        self.grid = grid
        self.chunk_size = chunk
        self.bounds = bounds
        self.rule_set_payload = (
            None if rule_set_payload is None else dict(rule_set_payload)
        )
        self._layers: dict[str, TileLayer] = {layer.id: layer for layer in layer_tuple}
        self._cells: dict[
            str, dict[ChunkCoordinate, dict[TileCoordinate, TileCell]]
        ] = {layer.id: {} for layer in layer_tuple}

    @property
    def layers(self) -> tuple[TileLayer, ...]:
        return tuple(
            sorted(self._layers.values(), key=lambda layer: (layer.order, layer.id))
        )

    @property
    def populated_cell_count(self) -> int:
        return sum(
            len(cells) for chunks in self._cells.values() for cells in chunks.values()
        )

    @property
    def populated_chunk_count(self) -> int:
        return len(
            {
                (layer_id, chunk)
                for layer_id, chunks in self._cells.items()
                for chunk in chunks
            }
        )

    def layer(self, layer_id: str) -> TileLayer:
        try:
            return self._layers[layer_id]
        except KeyError as exc:
            raise TileMapError(f"unknown layer ID: {layer_id}") from exc

    def set_layer_lock(self, layer_id: str, locked: bool) -> None:
        layer = self.layer(layer_id)
        self._layers[layer_id] = TileLayer(
            layer.id,
            layer.name,
            layer.order,
            layer.visible,
            bool(locked),
            layer.opacity,
        )

    def add_layer(self, layer: TileLayer) -> None:
        """Add an empty authoring layer without changing existing cells."""

        if not isinstance(layer, TileLayer):
            raise TileMapError("layer must be a TileLayer")
        if layer.id in self._layers:
            raise TileMapError(f"duplicate layer ID: {layer.id}")
        if len(self._layers) >= MAX_TILEMAP_LAYERS:
            raise TileMapLimitError("tilemap exceeds the layer limit")
        self._layers[layer.id] = layer
        self._cells[layer.id] = {}

    def set_layer_visibility(self, layer_id: str, visible: bool) -> None:
        """Toggle rendering of a layer while preserving its cells."""

        layer = self.layer(layer_id)
        self._layers[layer_id] = TileLayer(
            layer.id,
            layer.name,
            layer.order,
            bool(visible),
            layer.locked,
            layer.opacity,
        )

    def _validate_coordinate(self, coordinate: TileCoordinate) -> TileCoordinate:
        if len(coordinate) != 2:
            raise TileMapError("cell coordinate must contain two integers")
        x = _check_int(coordinate[0], "cell.x")
        y = _check_int(coordinate[1], "cell.y")
        normalized = (x, y)
        if self.bounds is not None and not self.bounds.contains(normalized):
            raise TileMapLimitError(f"cell coordinate outside map bounds: {normalized}")
        return normalized

    def chunk_for(self, coordinate: TileCoordinate) -> ChunkCoordinate:
        x, y = self._validate_coordinate(coordinate)
        return x // self.chunk_size, y // self.chunk_size

    def get_cell(self, layer_id: str, coordinate: TileCoordinate) -> TileCell | None:
        self.layer(layer_id)
        normalized = self._validate_coordinate(coordinate)
        chunk = self._cells[layer_id].get(self.chunk_for(normalized))
        return None if chunk is None else chunk.get(normalized)

    def _validate_cell(self, cell: TileCell | None) -> None:
        if cell is not None and not self.tileset.has_tile(cell.tile_id):
            raise TileMapError(f"unknown tile ID: {cell.tile_id}")

    def _validate_delta(self, delta: TileCellDelta) -> None:
        layer = self.layer(delta.layer_id)
        if layer.locked:
            raise TileMapLockedError(f"layer is locked: {layer.id}")
        coordinate = self._validate_coordinate(delta.coordinate)
        if coordinate != delta.coordinate:
            raise TileMapError("delta coordinate was not normalized")
        self._validate_cell(delta.before)
        self._validate_cell(delta.after)
        actual = self.get_cell(delta.layer_id, delta.coordinate)
        if actual != delta.before:
            raise TileMapError("delta before value does not match current map")

    def apply_deltas(
        self, deltas: Iterable[TileCellDelta]
    ) -> tuple[TileCellDelta, ...]:
        """Validate every delta first, then apply all changes atomically."""

        values = tuple(deltas)
        if not values:
            return ()
        if (
            self.populated_cell_count
            + sum(
                1
                for delta in values
                if delta.before is None and delta.after is not None
            )
            > MAX_TILEMAP_CELLS
        ):
            raise TileMapLimitError("tilemap exceeds the populated cell limit")
        for delta in values:
            self._validate_delta(delta)
        for delta in values:
            chunks = self._cells[delta.layer_id]
            chunk_key = self.chunk_for(delta.coordinate)
            chunk = chunks.get(chunk_key)
            if delta.after is None:
                if chunk is not None:
                    chunk.pop(delta.coordinate, None)
                    if not chunk:
                        chunks.pop(chunk_key, None)
                continue
            if chunk is None:
                if self.populated_chunk_count >= MAX_TILEMAP_CHUNKS:
                    raise TileMapLimitError("tilemap exceeds the chunk limit")
                chunk = {}
                chunks[chunk_key] = chunk
            chunk[delta.coordinate] = delta.after
        return values

    def set_cell(
        self, layer_id: str, coordinate: TileCoordinate, cell: TileCell | None
    ) -> TileCellDelta:
        before = self.get_cell(layer_id, coordinate)
        delta = TileCellDelta(
            layer_id, self._validate_coordinate(coordinate), before, cell
        )
        self.apply_deltas((delta,))
        return delta

    def iter_cells(
        self, layer_id: str | None = None
    ) -> Iterator[tuple[str, TileCoordinate, TileCell]]:
        layer_ids = (layer_id,) if layer_id is not None else tuple(self._cells)
        for current_layer in layer_ids:
            self.layer(current_layer)
            for chunk in self._cells[current_layer].values():
                for coordinate, cell in sorted(chunk.items()):
                    yield current_layer, coordinate, cell

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "format_id": "neoeng-d-trace-tilemap",
            "schema_version": 1,
            "id": self.id,
            "name": self.name,
            "grid": self.grid,
            "chunk_size": self.chunk_size,
            "bounds": None if self.bounds is None else self.bounds.to_dict(),
            "tileset": self.tileset.to_dict(),
            "layers": [layer.to_dict() for layer in self.layers],
            "cells": [
                {
                    "layer_id": current_layer,
                    "x": coordinate[0],
                    "y": coordinate[1],
                    "cell": cell.to_dict(),
                }
                for current_layer, coordinate, cell in self.iter_cells()
            ],
        }
        if self.rule_set_payload is not None:
            payload["rules"] = self.rule_set_payload
        return payload
