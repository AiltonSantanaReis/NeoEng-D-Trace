"""Unity JSON metadata profile."""

from typing import Any, Dict

from src.exporters.profiles.common import normalized_rect_and_pivot

UNITY_SCHEMA = "neoeng-d-trace-unity-sprite"
UNITY_SCHEMA_VERSION = 1


def format_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Format one object for a Unity editor importer."""
    rect, (pivot_x, pivot_y) = normalized_rect_and_pivot(meta)
    normalized_pivot = {
        "x": pivot_x / rect["w"],
        "y": pivot_y / rect["h"],
    }

    return {
        "schema": UNITY_SCHEMA,
        "schema_version": UNITY_SCHEMA_VERSION,
        "engine": "unity",
        "name": str(meta.get("id", "sprite")),
        "coordinate_origin": "top-left",
        "rect": {
            "x": rect["x"],
            "y": rect["y"],
            "width": rect["w"],
            "height": rect["h"],
        },
        "pivot": normalized_pivot,
        "border": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 0.0},
        "polygon": meta.get("polygon", meta.get("polygon_in_sprite", [])),
        "collision": meta.get("collision"),
    }
