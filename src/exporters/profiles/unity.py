"""Implementation of :mod:`src.exporters.profiles.unity`.

Implementation preserved in the single ``src`` source tree.
"""

from typing import Any, Dict


def format_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format internal metadata to Unity SpriteMeta format.

    Args:
        meta: Internal metadata dict with keys: id, rect, pivot, polygon, etc.

    Returns:
        Dict in Unity format: name, rect, pivot, border
    """
    rect = meta.get("rect", {"x": 0, "y": 0, "w": 0, "h": 0})
    pivot_raw = meta.get("pivot", {"x": 0.5, "y": 0.5})

    # Normalize pivot access (handle dict or list/tuple)
    if isinstance(pivot_raw, (list, tuple)):
        px, py = pivot_raw[0], pivot_raw[1]
    else:
        px = pivot_raw.get("x", 0)
        py = pivot_raw.get("y", 0)

    # Normalize pivot to 0-1 range relative to the sprite rect
    # Note: Unity Pivot is (0,0) at Bottom-Left, but standard image tools are Top-Left.
    # Unity importers usually handle the Y-flip, so normalization stays
    # relative to Rect size.

    w = rect.get("w", 0)
    h = rect.get("h", 0)

    normalized_pivot = {
        "x": px / w if w > 0 else 0.5,
        "y": py / h if h > 0 else 0.5,
    }

    return {
        "name": meta.get("id", "sprite"),
        "rect": {
            "x": rect.get("x", 0),
            "y": rect.get("y", 0),
            "width": w,
            "height": h,
        },
        "pivot": normalized_pivot,
        "border": {"x": 0, "y": 0, "z": 0, "w": 0},  # No 9-slice support yet
    }
