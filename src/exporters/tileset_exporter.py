"""Deterministic tile-sheet preparation and collision manifest export."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

from src.exporters.sprite_exporter import save_sprite

FORMAT_ID = "neoeng-d-trace-tileset"
SCHEMA_VERSION = 1


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _non_negative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def slice_tilesheet(
    image: Image.Image,
    *,
    tile_size: tuple[int, int],
    spacing: int = 0,
    margin: int = 0,
) -> list[dict[str, Any]]:
    """Slice only complete cells from a sheet, preserving source rectangles."""

    if not isinstance(image, Image.Image):
        raise ValueError("image must be a Pillow image")
    tile_w = _positive_int(tile_size[0], "tile_size.width")
    tile_h = _positive_int(tile_size[1], "tile_size.height")
    spacing = _non_negative_int(spacing, "spacing")
    margin = _non_negative_int(margin, "margin")
    usable_w = image.width - 2 * margin
    usable_h = image.height - 2 * margin
    if usable_w < tile_w or usable_h < tile_h:
        return []
    columns = 1 + (usable_w - tile_w) // (tile_w + spacing)
    rows = 1 + (usable_h - tile_h) // (tile_h + spacing)
    tiles: list[dict[str, Any]] = []
    for row in range(rows):
        for column in range(columns):
            x = margin + column * (tile_w + spacing)
            y = margin + row * (tile_h + spacing)
            tiles.append(
                {
                    "id": f"tile_{len(tiles):04d}",
                    "index": len(tiles),
                    "row": row,
                    "column": column,
                    "source_rect": {"x": x, "y": y, "w": tile_w, "h": tile_h},
                    "image": image.crop((x, y, x + tile_w, y + tile_h)).convert("RGBA"),
                }
            )
    return tiles


def _alpha_bounds(tile: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = tile.convert("RGBA").getchannel("A")
    return alpha.getbbox()


def _snap_bounds(
    bounds: tuple[int, int, int, int],
    size: tuple[int, int],
    tolerance: int,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bounds
    width, height = size
    if x0 <= tolerance:
        x0 = 0
    if y0 <= tolerance:
        y0 = 0
    if width - x1 <= tolerance:
        x1 = width
    if height - y1 <= tolerance:
        y1 = height
    return x0, y0, x1, y1


def collision_from_tile(
    tile: Image.Image, *, snap_to_edges: bool = True, tolerance: int = 1
) -> list[list[int]] | None:
    """Create a conservative rectangle from the tile alpha bounds."""

    tolerance = _non_negative_int(tolerance, "tolerance")
    bounds = _alpha_bounds(tile)
    if bounds is None:
        return None
    if snap_to_edges:
        bounds = _snap_bounds(bounds, tile.size, tolerance)
    x0, y0, x1, y1 = bounds
    if x1 <= x0 or y1 <= y0:
        return None
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def prepare_tileset(
    image: Image.Image,
    *,
    tile_size: tuple[int, int],
    spacing: int = 0,
    margin: int = 0,
    snap_to_edges: bool = True,
    tolerance: int = 1,
) -> dict[str, Any]:
    """Prepare tile images and local collision polygons without designing maps."""

    tiles = slice_tilesheet(image, tile_size=tile_size, spacing=spacing, margin=margin)
    entries: list[dict[str, Any]] = []
    for tile in tiles:
        collision = collision_from_tile(
            tile["image"], snap_to_edges=snap_to_edges, tolerance=tolerance
        )
        entries.append(
            {
                "id": tile["id"],
                "index": tile["index"],
                "row": tile["row"],
                "column": tile["column"],
                "source_rect": tile["source_rect"],
                "size": {"w": tile["image"].width, "h": tile["image"].height},
                "collision": collision,
                "image": tile["image"],
            }
        )
    return {
        "format_id": FORMAT_ID,
        "schema_version": SCHEMA_VERSION,
        "tile_size": {"w": tile_size[0], "h": tile_size[1]},
        "spacing": spacing,
        "margin": margin,
        "tiles": entries,
    }


def save_tileset(
    prepared: dict[str, Any], out_dir: str | os.PathLike[str]
) -> dict[str, Any]:
    """Write tile PNGs and a manifest atomically enough for the project outputs."""

    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    manifest_tiles: list[dict[str, Any]] = []
    for entry in prepared.get("tiles", []):
        image = entry.get("image")
        if not isinstance(image, Image.Image):
            raise ValueError("prepared tiles must contain images")
        filename = f"{entry['id']}.png"
        save_sprite(image, str(destination / filename))
        manifest_entry = {key: value for key, value in entry.items() if key != "image"}
        manifest_entry["texture"] = filename
        manifest_tiles.append(manifest_entry)

    manifest = {key: value for key, value in prepared.items() if key != "tiles"}
    manifest["tiles"] = manifest_tiles
    manifest_path = destination / "tileset.json"
    fd, temporary = tempfile.mkstemp(
        prefix="tmp_tileset_", suffix=".json", dir=str(destination), text=True
    )
    os.close(fd)
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, manifest_path)
        temporary = ""
    finally:
        if temporary and os.path.exists(temporary):
            os.remove(temporary)
    return {"manifest_path": str(manifest_path), "manifest": manifest}
