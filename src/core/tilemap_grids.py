"""Deterministic cell/world transforms and neighbourhoods for E04 grids."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from src.core.tilemap_model import TileCoordinate, TileMapError


class GridKind(StrEnum):
    ORTHOGONAL = "orthogonal"
    ISOMETRIC = "isometric"
    HEXAGONAL = "hexagonal"


def _finite_positive(value: float, field: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise TileMapError(f"{field} must be finite and positive")
    return number


def _round_half_up(value: float) -> int:
    """Round ties toward positive infinity, including negative coordinates."""

    return math.floor(value + 0.5)


@dataclass(frozen=True)
class GridSpec:
    """Grid geometry shared by picking, drawing and snapping."""

    kind: GridKind | str
    cell_width: float = 64.0
    cell_height: float = 64.0
    origin_x: float = 0.0
    origin_y: float = 0.0

    def __post_init__(self) -> None:
        kind = GridKind(self.kind)
        object.__setattr__(self, "kind", kind)
        for name in ("cell_width", "cell_height"):
            _finite_positive(getattr(self, name), name)
        for name in ("origin_x", "origin_y"):
            if not math.isfinite(float(getattr(self, name))):
                raise TileMapError(f"{name} must be finite")

    def cell_to_world(self, coordinate: TileCoordinate) -> tuple[float, float]:
        x, y = coordinate
        if (
            isinstance(x, bool)
            or isinstance(y, bool)
            or not isinstance(x, int)
            or not isinstance(y, int)
        ):
            raise TileMapError("grid coordinates must be signed integers")
        if self.kind == GridKind.ORTHOGONAL:
            return (
                self.origin_x + (x + 0.5) * self.cell_width,
                self.origin_y + (y + 0.5) * self.cell_height,
            )
        if self.kind == GridKind.ISOMETRIC:
            half_w = self.cell_width / 2.0
            half_h = self.cell_height / 2.0
            return (
                self.origin_x + (x - y) * half_w,
                self.origin_y + (x + y + 1) * half_h,
            )
        # Pointy-top axial hexes: x is q and y is r.
        return (
            self.origin_x + self.cell_width * (x + y / 2.0),
            self.origin_y + self.cell_height * (0.75 * y + 0.5),
        )

    def world_to_cell(self, world: tuple[float, float]) -> TileCoordinate:
        wx, wy = world
        if not math.isfinite(float(wx)) or not math.isfinite(float(wy)):
            raise TileMapError("world coordinates must be finite")
        dx = float(wx) - self.origin_x
        dy = float(wy) - self.origin_y
        if self.kind == GridKind.ORTHOGONAL:
            return (
                math.floor(dx / self.cell_width),
                math.floor(dy / self.cell_height),
            )
        if self.kind == GridKind.ISOMETRIC:
            half_w = self.cell_width / 2.0
            half_h = self.cell_height / 2.0
            iso_x = (dx / half_w + dy / half_h - 1.0) / 2.0
            iso_y = (dy / half_h - dx / half_w - 1.0) / 2.0
            return _round_half_up(iso_x), _round_half_up(iso_y)
        # Inverse of pointy-top axial projection, followed by cube rounding.
        axial_r = (dy / self.cell_height - 0.5) / 0.75
        axial_q = dx / self.cell_width - axial_r / 2.0
        rounded_q, _rounded_cube, rounded_r = _cube_round(
            axial_q, -axial_q - axial_r, axial_r
        )
        return rounded_q, rounded_r

    def neighbors(self, coordinate: TileCoordinate) -> tuple[TileCoordinate, ...]:
        x, y = coordinate
        if self.kind == GridKind.HEXAGONAL:
            offsets: tuple[tuple[int, int], ...] = (
                (1, 0),
                (1, -1),
                (0, -1),
                (-1, 0),
                (-1, 1),
                (0, 1),
            )
        else:
            offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
        return tuple((x + dx, y + dy) for dx, dy in offsets)


def _cube_round(x: float, y: float, z: float) -> tuple[int, int, int]:
    rx, ry, rz = _round_half_up(x), _round_half_up(y), _round_half_up(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, ry, rz


def grid_round_trip(spec: GridSpec, coordinate: TileCoordinate) -> bool:
    """Convenience predicate used by diagnostics and tests."""

    return spec.world_to_cell(spec.cell_to_world(coordinate)) == coordinate


__all__ = ["GridKind", "GridSpec", "grid_round_trip"]
