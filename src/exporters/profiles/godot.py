"""Godot 4 JSON metadata profile."""

from typing import Any, Dict

from src.exporters.profiles.common import normalized_rect_and_pivot

GODOT_SCHEMA = "neoeng-d-trace-godot-sprite"
GODOT_SCHEMA_VERSION = 1


def format_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Format one object for a Godot 4 ``AtlasTexture``/``Sprite2D`` consumer."""
    rect, (pivot_x, pivot_y) = normalized_rect_and_pivot(meta)
    offset = {
        "x": rect["w"] / 2.0 - pivot_x,
        "y": rect["h"] / 2.0 - pivot_y,
    }

    return {
        "schema": GODOT_SCHEMA,
        "schema_version": GODOT_SCHEMA_VERSION,
        "engine": "godot-4",
        "name": str(meta.get("id", "sprite")),
        "coordinate_origin": "top-left",
        "rect": rect,
        "pivot": {"x": pivot_x, "y": pivot_y},
        "offset": offset,
        "polygon": meta.get("polygon", meta.get("polygon_in_sprite", [])),
        "collision": meta.get("collision"),
    }
