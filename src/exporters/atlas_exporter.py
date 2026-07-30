"""Implementation of :mod:`src.exporters.atlas_exporter`.

Implementation preserved in the single ``src`` source tree.
"""

import json
import os
import tempfile
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple, cast

from PIL import Image

# Tenta importar o Packer otimizado
try:
    from src.utils.packing import Packer

    HAS_PACKER = True
except ImportError:
    HAS_PACKER = False

from src.core.logger import logger


class _AtlasNode(Protocol):
    x: int
    y: int
    w: int
    h: int


def _deterministic_sort(
    items: Iterable[Tuple[Image.Image, Dict[str, Any]]],
) -> List[Tuple[Image.Image, Dict[str, Any]]]:
    """Sort by area desc, then width desc, then name (safe)."""
    return sorted(
        items,
        key=lambda it: (
            it[0].width * it[0].height,
            it[0].width,
            it[1].get("name", "unknown"),
        ),
        reverse=True,
    )


def pack_sprites_to_atlas(
    items: List[Tuple[Image.Image, Dict[str, Any]]],
    max_size: Tuple[int, int] = (2048, 2048),
    padding: int = 2,
    allow_rotate: bool = False,
) -> List[Tuple[Image.Image, List[Dict[str, Any]]]]:
    """
    Pack sprites into texture atlas(es) using MaxRects (if available) or Shelf.
    """
    if not items:
        return []

    sorted_items = _deterministic_sort(items)
    max_w, max_h = max_size

    atlases = []

    # Keep track of items remaining to pack
    remaining_items = list(sorted_items)
    current_atlas_index = 0

    while remaining_items:
        # Create a new atlas
        if HAS_PACKER:
            packer = Packer(max_w, max_h, padding)
        else:
            # Fallback simple variables
            x, y, row_h = padding, padding, 0

        atlas_img = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
        meta: List[Dict[str, Any]] = []
        packed_in_this_atlas = []

        # Try to fit remaining items
        for img, meta_dict in list(remaining_items):
            w, h = img.width, img.height
            name = meta_dict["name"]
            node: Optional[_AtlasNode] = None
            rotated = False

            if HAS_PACKER:
                # Try normal
                node = packer.insert(w, h, name)

                # Try rotated if allowed and not fit
                if node is None and allow_rotate:
                    node = packer.insert(h, w, name)
                    if node:
                        rotated = True
            else:
                # Simple Shelf logic fallback
                if x + w <= max_w - padding and y + h <= max_h - padding:
                    node = cast(
                        _AtlasNode,
                        SimpleNamespace(x=x, y=y, w=w, h=h),
                    )
                    x += w + padding
                    row_h = max(row_h, h)
                    # Wrap to new row
                    if (
                        x > max_w - padding
                    ):  # This logic is imperfect for mixed sizes but it's a fallback
                        pass

                # Naive row wrap logic for fallback
                if x + w > max_w - padding:
                    x = padding
                    y += row_h + padding
                    row_h = 0

                if y + h <= max_h - padding and x + w <= max_w - padding:
                    node = cast(
                        _AtlasNode,
                        SimpleNamespace(x=x, y=y, w=w, h=h),
                    )
                    x += w + padding
                    row_h = max(row_h, h)

            if node:
                # Place image on atlas
                if rotated:
                    # Rotate 90 deg clockwise to fit
                    img_to_paste = img.transpose(Image.Transpose.ROTATE_270)
                else:
                    img_to_paste = img

                atlas_img.paste(
                    img_to_paste,
                    (node.x, node.y),
                    img_to_paste if "A" in img_to_paste.getbands() else None,
                )

                entry = {
                    "name": name,
                    "atlas": current_atlas_index,
                    "rect": {"x": node.x, "y": node.y, "w": w, "h": h},
                    "rotated": rotated,
                }
                meta.append(entry)
                packed_in_this_atlas.append((img, meta_dict))  # Record success

        # Remove packed items from remaining list
        for item in packed_in_this_atlas:
            remaining_items.remove(item)

        # If nothing fit in an empty atlas, the item is too big
        if not packed_in_this_atlas and remaining_items:
            logger.warning(
                f"Item {remaining_items[0][1]['name']} too big for atlas size {max_size}"
            )
            # Skip this item to prevent infinite loop
            remaining_items.pop(0)
            continue

        # Crop atlas to used size (Optional optimization)
        # For simplicity, we keep full size or crop to content bounding box
        bbox = atlas_img.getbbox()
        if bbox:
            atlas_cropped = atlas_img.crop((0, 0, bbox[2] + padding, bbox[3] + padding))
        else:
            atlas_cropped = atlas_img

        atlases.append((atlas_cropped, meta))
        current_atlas_index += 1

    return atlases


def save_atlas(
    atlas: Image.Image,
    metadata: List[Dict[str, Any]],
    atlas_path: str,
    json_path: str,
):
    """Save atlas image and metadata with atomic replacement per file.

    The image and JSON are fully written to temporary files before either
    destination is replaced. A filesystem cannot atomically replace two files
    as one transaction, so callers must still validate both outputs together.
    """

    atlas_dir = os.path.dirname(atlas_path)
    json_dir = os.path.dirname(json_path)
    if atlas_dir:
        os.makedirs(atlas_dir, exist_ok=True)
    if json_dir:
        os.makedirs(json_dir, exist_ok=True)

    fd_img, tmp_img = tempfile.mkstemp(
        prefix="tmp_atlas_", suffix=".png", dir=atlas_dir or "."
    )
    os.close(fd_img)
    fd_json, tmp_json = tempfile.mkstemp(
        prefix="tmp_atlas_", suffix=".json", dir=json_dir or ".", text=True
    )
    os.close(fd_json)

    try:
        atlas.save(tmp_img, format="PNG")
        with open(tmp_json, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_img, atlas_path)
        tmp_img = ""
        os.replace(tmp_json, json_path)
        tmp_json = ""
    except Exception as exc:
        logger.error("Failed to save atlas outputs: %s", exc)
        raise
    finally:
        for temporary in (tmp_img, tmp_json):
            if temporary and os.path.exists(temporary):
                os.remove(temporary)


def build_atlas(
    items: List[Tuple[str, Image.Image]],
    out_dir: str,
    base_name: str = "atlas",
    max_size: Tuple[int, int] = (2048, 2048),
    padding: int = 2,
    allow_rotate: bool = False,
) -> List[Dict[str, Any]]:
    """High-level helper used by UI."""
    os.makedirs(out_dir, exist_ok=True)
    converted_items = [(img, {"name": name}) for name, img in items]

    atlases = pack_sprites_to_atlas(
        converted_items,
        max_size=max_size,
        padding=padding,
        allow_rotate=allow_rotate,
    )

    results = []
    for idx, (atlas_img, meta) in enumerate(atlases):
        atlas_path = os.path.join(out_dir, f"{base_name}_{idx}.png")
        json_path = os.path.join(out_dir, f"{base_name}_{idx}.json")
        save_atlas(atlas_img, meta, atlas_path, json_path)
        results.append(
            {"atlas_path": atlas_path, "json_path": json_path, "entries": meta}
        )
    return results
