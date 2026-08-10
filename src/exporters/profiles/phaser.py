"""Implementation of :mod:`src.exporters.profiles.phaser`.

Implementation preserved in the single ``src`` source tree.
"""

from typing import Any, Dict


def format_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format internal metadata to Phaser frame format.

    Args:
        meta: Internal metadata dict with keys: id, rect, pivot, polygon, etc.

    Returns:
        Dict in Phaser frame format
    """
    rect = meta.get("rect", {"x": 0, "y": 0, "w": 0, "h": 0})
    obj_id = meta.get("id", "sprite")

    return {
        "filename": obj_id,
        "frame": {
            "x": rect.get("x", 0),
            "y": rect.get("y", 0),
            "w": rect.get("w", 0),
            "h": rect.get("h", 0),
        },
        "rotated": False,
        "trimmed": True,  # Assume trimmed if we are exporting polygons
        "spriteSourceSize": {
            "x": 0,
            "y": 0,
            "w": rect.get("w", 0),
            "h": rect.get("h", 0),
        },
        "sourceSize": {"w": rect.get("w", 0), "h": rect.get("h", 0)},
        # Phaser usually calculates pivot/anchor at runtime or via custom properties
        # but we can include it in specific custom fields if needed.
    }
