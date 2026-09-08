"""Transactional tilemap editing tools for the E04 authoring flow."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Sequence

from src.core.tilemap_grids import GridSpec
from src.core.tilemap_model import (
    TileCell,
    TileCellDelta,
    TileMapDocument,
    TileMapError,
    TileMapLimitError,
)


class TileTool(StrEnum):
    PENCIL = "pencil"
    ERASER = "eraser"
    RECTANGLE = "rectangle"
    BUCKET = "bucket"
    PICKER = "picker"


def _dedupe_coordinates(
    coordinates: Iterable[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return tuple(dict.fromkeys(coordinates))


def _bresenham(
    start: tuple[int, int], end: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    x0, y0 = start
    x1, y1 = end
    points: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        points.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return tuple(points)
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += sx
        if doubled <= dx:
            error += dx
            y0 += sy


def rectangle_cells(
    start: tuple[int, int], end: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    min_x, max_x = sorted((start[0], end[0]))
    min_y, max_y = sorted((start[1], end[1]))
    return tuple(
        (x, y) for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)
    )


def deterministic_tile_id(
    tile_ids: Sequence[str], *, seed: int, coordinate: tuple[int, int]
) -> str:
    """Choose a tile independently of iteration order for reproducible variation."""

    if not tile_ids:
        raise TileMapError("variation requires at least one tile ID")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TileMapError("variation seed must be an integer")
    x, y = coordinate
    generator = random.Random((seed * 1_000_003) ^ (x * 9176) ^ (y * 6113))
    return tile_ids[generator.randrange(len(tile_ids))]


@dataclass(frozen=True)
class TileClipboard:
    """Portable selected cells relative to an anchor."""

    cells: tuple[tuple[int, int, TileCell], ...]

    def __post_init__(self) -> None:
        if any(not isinstance(cell, TileCell) for _, _, cell in self.cells):
            raise TileMapError("clipboard contains an invalid cell")


class TileEditTransaction:
    """One atomic operation with explicit Undo/Redo deltas."""

    def __init__(self, document: TileMapDocument, deltas: Iterable[TileCellDelta]):
        self.document = document
        self.deltas = tuple(deltas)
        self._applied = False

    def apply(self) -> tuple[TileCellDelta, ...]:
        if self._applied:
            raise TileMapError("transaction is already applied")
        result = self.document.apply_deltas(self.deltas)
        self._applied = True
        return result

    def undo(self) -> tuple[TileCellDelta, ...]:
        if not self._applied:
            raise TileMapError("transaction is not applied")
        reverse = tuple(
            TileCellDelta(delta.layer_id, delta.coordinate, delta.after, delta.before)
            for delta in reversed(self.deltas)
        )
        result = self.document.apply_deltas(reverse)
        self._applied = False
        return result

    def redo(self) -> tuple[TileCellDelta, ...]:
        return self.apply()


def _transaction_for_cells(
    document: TileMapDocument,
    layer_id: str,
    coordinates: Iterable[tuple[int, int]],
    cell_factory,
) -> TileEditTransaction:
    deltas: list[TileCellDelta] = []
    for coordinate in _dedupe_coordinates(coordinates):
        before = document.get_cell(layer_id, coordinate)
        after = cell_factory(coordinate, before)
        if after == before:
            continue
        deltas.append(TileCellDelta(layer_id, coordinate, before, after))
    return TileEditTransaction(document, deltas)


def paint_line(
    document: TileMapDocument,
    layer_id: str,
    start: tuple[int, int],
    end: tuple[int, int],
    tile_id: str,
    *,
    variant: str = "default",
) -> TileEditTransaction:
    if not document.tileset.has_tile(tile_id):
        raise TileMapError(f"unknown tile ID: {tile_id}")
    cell = TileCell(tile_id, variant)
    transaction = _transaction_for_cells(
        document,
        layer_id,
        _bresenham(start, end),
        lambda _coordinate, _before: cell,
    )
    transaction.apply()
    return transaction


def erase_line(
    document: TileMapDocument,
    layer_id: str,
    start: tuple[int, int],
    end: tuple[int, int],
) -> TileEditTransaction:
    transaction = _transaction_for_cells(
        document, layer_id, _bresenham(start, end), lambda _coordinate, _before: None
    )
    transaction.apply()
    return transaction


def paint_rectangle(
    document: TileMapDocument,
    layer_id: str,
    start: tuple[int, int],
    end: tuple[int, int],
    tile_id: str,
) -> TileEditTransaction:
    if not document.tileset.has_tile(tile_id):
        raise TileMapError(f"unknown tile ID: {tile_id}")
    cell = TileCell(tile_id)
    transaction = _transaction_for_cells(
        document,
        layer_id,
        rectangle_cells(start, end),
        lambda _coordinate, _before: cell,
    )
    transaction.apply()
    return transaction


def bucket_fill(
    document: TileMapDocument,
    layer_id: str,
    start: tuple[int, int],
    tile_id: str,
    *,
    grid: GridSpec,
    max_cells: int = 100_000,
) -> TileEditTransaction:
    """Fill only a finite connected region; an unbounded map is rejected."""

    if document.bounds is None:
        raise TileMapLimitError("bucket fill requires finite map bounds")
    if not isinstance(max_cells, int) or isinstance(max_cells, bool) or max_cells <= 0:
        raise TileMapError("bucket max_cells must be positive")
    if not document.tileset.has_tile(tile_id):
        raise TileMapError(f"unknown tile ID: {tile_id}")
    target = document.get_cell(layer_id, start)
    replacement = TileCell(tile_id)
    if target == replacement:
        return TileEditTransaction(document, ())
    queue = [start]
    visited: set[tuple[int, int]] = set()
    region: list[tuple[int, int]] = []
    while queue:
        coordinate = queue.pop(0)
        if coordinate in visited or not document.bounds.contains(coordinate):
            continue
        visited.add(coordinate)
        if document.get_cell(layer_id, coordinate) != target:
            continue
        region.append(coordinate)
        if len(region) > max_cells:
            raise TileMapLimitError("bucket fill exceeds max_cells")
        queue.extend(grid.neighbors(coordinate))
    transaction = _transaction_for_cells(
        document, layer_id, region, lambda _coordinate, _before: replacement
    )
    transaction.apply()
    return transaction


def copy_cells(
    document: TileMapDocument,
    layer_id: str,
    coordinates: Iterable[tuple[int, int]],
) -> TileClipboard:
    source = []
    for coordinate in _dedupe_coordinates(coordinates):
        cell = document.get_cell(layer_id, coordinate)
        if cell is not None:
            source.append((coordinate[0], coordinate[1], cell))
    if not source:
        raise TileMapError("copy requires at least one occupied cell")
    min_x = min(x for x, _y, _cell in source)
    min_y = min(y for _x, y, _cell in source)
    return TileClipboard(tuple((x - min_x, y - min_y, cell) for x, y, cell in source))


def paste_cells(
    document: TileMapDocument,
    layer_id: str,
    anchor: tuple[int, int],
    clipboard: TileClipboard,
) -> TileEditTransaction:
    if not clipboard.cells:
        raise TileMapError("clipboard cannot be empty")
    coordinates = ((anchor[0] + x, anchor[1] + y) for x, y, _cell in clipboard.cells)
    by_coordinate = {
        (anchor[0] + x, anchor[1] + y): cell for x, y, cell in clipboard.cells
    }
    transaction = _transaction_for_cells(
        document,
        layer_id,
        coordinates,
        lambda coordinate, _before: by_coordinate[coordinate],
    )
    transaction.apply()
    return transaction


__all__ = [
    "TileClipboard",
    "TileEditTransaction",
    "TileTool",
    "bucket_fill",
    "copy_cells",
    "deterministic_tile_id",
    "erase_line",
    "paint_line",
    "paint_rectangle",
    "paste_cells",
    "rectangle_cells",
]
