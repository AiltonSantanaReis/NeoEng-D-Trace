"""Implementation of :mod:`src.exporters.profiles.godot`.

Implementation preserved in the single ``src`` source tree.
"""

"""
Godot export profile for NeoEng-D-Trace.
Handles formatting of metadata for Godot Engine (AtlasTexture style).
"""

from typing import Dict, Any

def format_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format internal metadata to Godot AtlasTexture format.

    Args:
        meta: Internal metadata dict with keys: id, rect, pivot, polygon, etc.

    Returns:
        Dict in Godot format: rect, offset (from center)
    """
    rect = meta.get("rect", {"x": 0, "y": 0, "w": 0, "h": 0})
    pivot_raw = meta.get("pivot", {"x": 0, "y": 0})

    # Normalize pivot access (handle dict or list/tuple)
    if isinstance(pivot_raw, (list, tuple)):
        px, py = pivot_raw[0], pivot_raw[1]
    else:
        px = pivot_raw.get("x", 0)
        py = pivot_raw.get("y", 0)

    # Calculate center of the rect
    center_x = rect["x"] + rect["w"] / 2
    center_y = rect["y"] + rect["h"] / 2

    # Godot Offset: Distance from center to pivot
    # Note: Godot usually treats offset as the drawing offset to align the sprite.
    # If pivot is the anchor point, the offset is typically (Pivot - Center).
    offset = {
        "x": px - center_x, 
        "y": py - center_y
    }

    return {
        "name": meta.get("id", "sprite"),
        "rect": rect,
        "offset": offset,
        # Godot 4+ might prefer a 'region' key instead of 'rect', 
        # but 'rect' is standard for generic JSON parsers in Godot.
    }
