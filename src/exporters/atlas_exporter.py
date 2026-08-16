"""Implementation of :mod:`src.exporters.atlas_exporter`.

Implementation preserved in the single ``src`` source tree.
"""

import json
import os
import shutil
import tempfile
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Tuple, cast

from PIL import Image

from src.core.operational_limits import (
    MAX_ATLAS_DIMENSION,
    MAX_ATLAS_ITEMS,
    MAX_ATLAS_PAGES,
    MAX_ATLAS_PIXELS,
    MAX_ATLAS_TOTAL_INPUT_PIXELS,
)

# Tenta importar o Packer otimizado
try:
    from src.utils.packing import Packer

    HAS_PACKER = True
except ImportError:
    HAS_PACKER = False

from src.core.logger import logger


def _commit_staged_files(staged_files: List[Tuple[str, str]]) -> None:
    """Commit staged files as one rollback-protected output set."""
    backups: Dict[str, Optional[str]] = {}
    committed: List[str] = []

    try:
        for _, destination in staged_files:
            if not os.path.exists(destination):
                backups[destination] = None
                continue
            directory = os.path.dirname(destination) or "."
            fd, backup_path = tempfile.mkstemp(
                prefix="tmp_atlas_backup_", dir=directory
            )
            os.close(fd)
            backups[destination] = backup_path
            shutil.copy2(destination, backup_path)

        for staged, destination in staged_files:
            os.replace(staged, destination)
            committed.append(destination)
    except Exception:
        for destination in reversed(committed):
            stored_backup = backups[destination]
            if stored_backup is None:
                if os.path.exists(destination):
                    os.remove(destination)
            else:
                os.replace(stored_backup, destination)
                backups[destination] = None
        raise
    finally:
        for staged, _ in staged_files:
            if os.path.exists(staged):
                os.remove(staged)
        for remaining_backup in backups.values():
            if remaining_backup and os.path.exists(remaining_backup):
                os.remove(remaining_backup)


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


def _extrude_edges(image: Image.Image, bleed: int) -> Image.Image:
    """Return an RGBA image with edge pixels duplicated by ``bleed`` pixels."""

    if bleed == 0:
        return image
    rgba = image.convert("RGBA")
    width, height = rgba.size
    result = Image.new("RGBA", (width + 2 * bleed, height + 2 * bleed))
    result.paste(rgba, (bleed, bleed))
    result.paste(
        rgba.crop((0, 0, width, 1)).resize((width, bleed), Image.Resampling.NEAREST),
        (bleed, 0),
    )
    result.paste(
        rgba.crop((0, height - 1, width, height)).resize(
            (width, bleed), Image.Resampling.NEAREST
        ),
        (bleed, height + bleed),
    )
    result.paste(
        rgba.crop((0, 0, 1, height)).resize((bleed, height), Image.Resampling.NEAREST),
        (0, bleed),
    )
    result.paste(
        rgba.crop((width - 1, 0, width, height)).resize(
            (bleed, height), Image.Resampling.NEAREST
        ),
        (width + bleed, bleed),
    )
    for source, position in (
        ((0, 0, 1, 1), (0, 0)),
        ((width - 1, 0, width, 1), (width + bleed, 0)),
        ((0, height - 1, 1, height), (0, height + bleed)),
        ((width - 1, height - 1, width, height), (width + bleed, height + bleed)),
    ):
        result.paste(
            rgba.crop(source).resize((bleed, bleed), Image.Resampling.NEAREST),
            position,
        )
    return result


def pack_sprites_to_atlas(
    items: List[Tuple[Image.Image, Dict[str, Any]]],
    max_size: Tuple[int, int] = (2048, 2048),
    padding: int = 2,
    allow_rotate: bool = False,
    bleed: int = 0,
) -> List[Tuple[Image.Image, List[Dict[str, Any]]]]:
    """
    Pack sprites into texture atlas(es) using MaxRects (if available) or Shelf.
    """
    if not items:
        return []

    if (
        not isinstance(max_size, (list, tuple))
        or len(max_size) != 2
        or any(
            isinstance(value, bool) or not isinstance(value, int) for value in max_size
        )
    ):
        raise ValueError("max_size must contain two positive integers")
    max_w, max_h = max_size
    if max_w <= 0 or max_h <= 0:
        raise ValueError("max_size must contain two positive integers")
    if max_w > MAX_ATLAS_DIMENSION or max_h > MAX_ATLAS_DIMENSION:
        raise ValueError(f"atlas dimensions cannot exceed {MAX_ATLAS_DIMENSION}")
    if max_w * max_h > MAX_ATLAS_PIXELS:
        raise ValueError(f"atlas exceeds the pixel limit of {MAX_ATLAS_PIXELS}")
    if isinstance(padding, bool) or not isinstance(padding, int) or padding < 0:
        raise ValueError("padding must be a non-negative integer")
    if isinstance(bleed, bool) or not isinstance(bleed, int) or bleed < 0:
        raise ValueError("bleed must be a non-negative integer")
    if padding * 2 >= min(max_w, max_h):
        raise ValueError("padding leaves no usable atlas area")
    if len(items) > MAX_ATLAS_ITEMS:
        raise ValueError(f"atlas item count exceeds the limit of {MAX_ATLAS_ITEMS}")

    total_input_pixels = 0
    prepared_items: List[Tuple[Image.Image, Dict[str, Any]]] = []
    for image, metadata in items:
        if not isinstance(image, Image.Image):
            raise ValueError("atlas items must contain Pillow images")
        if image.width <= 0 or image.height <= 0:
            raise ValueError("atlas item dimensions must be positive")
        if image.width > MAX_ATLAS_DIMENSION or image.height > MAX_ATLAS_DIMENSION:
            raise ValueError(
                f"atlas item dimensions cannot exceed {MAX_ATLAS_DIMENSION}"
            )
        prepared = _extrude_edges(image, bleed)
        if (
            prepared.width > MAX_ATLAS_DIMENSION
            or prepared.height > MAX_ATLAS_DIMENSION
        ):
            raise ValueError(
                "atlas item dimensions including bleed cannot exceed "
                f"{MAX_ATLAS_DIMENSION}"
            )
        pixels = prepared.width * prepared.height
        if pixels > MAX_ATLAS_PIXELS:
            raise ValueError(
                f"atlas item exceeds the pixel limit of {MAX_ATLAS_PIXELS}"
            )
        total_input_pixels += pixels
        if total_input_pixels > MAX_ATLAS_TOTAL_INPUT_PIXELS:
            raise ValueError(
                "atlas inputs exceed the aggregate pixel limit of "
                f"{MAX_ATLAS_TOTAL_INPUT_PIXELS}"
            )
        prepared_items.append(
            (
                prepared,
                {**metadata, "_atlas_source_size": (image.width, image.height)},
            )
        )

    sorted_items = _deterministic_sort(prepared_items)

    atlases = []

    # Keep track of items remaining to pack
    remaining_items = list(sorted_items)
    current_atlas_index = 0

    while remaining_items:
        if current_atlas_index >= MAX_ATLAS_PAGES:
            raise ValueError(f"atlas page count exceeds the limit of {MAX_ATLAS_PAGES}")
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
                    "rect": {
                        "x": node.x + bleed,
                        "y": node.y + bleed,
                        "w": (
                            meta_dict["_atlas_source_size"][0]
                            if not rotated
                            else meta_dict["_atlas_source_size"][1]
                        ),
                        "h": (
                            meta_dict["_atlas_source_size"][1]
                            if not rotated
                            else meta_dict["_atlas_source_size"][0]
                        ),
                    },
                    "packed_rect": {
                        "x": node.x,
                        "y": node.y,
                        "w": img_to_paste.width,
                        "h": img_to_paste.height,
                    },
                    "extrusion": bleed,
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
                f"Item {remaining_items[0][1]['name']} too big for atlas "
                f"size {max_size}"
            )
            # Skip this item to prevent infinite loop
            remaining_items.pop(0)
            continue

        used_width = max(
            entry["packed_rect"]["x"] + entry["packed_rect"]["w"] for entry in meta
        )
        used_height = max(
            entry["packed_rect"]["y"] + entry["packed_rect"]["h"] for entry in meta
        )
        atlas_cropped = atlas_img.crop(
            (
                0,
                0,
                min(max_w, used_width + padding),
                min(max_h, used_height + padding),
            )
        )

        atlases.append((atlas_cropped, meta))
        current_atlas_index += 1

    return atlases


def save_atlas(
    atlas: Image.Image,
    metadata: List[Dict[str, Any]],
    atlas_path: str,
    json_path: str,
):
    """Save image and metadata as one rollback-protected output set."""

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

        _commit_staged_files([(tmp_img, atlas_path), (tmp_json, json_path)])
        tmp_img = ""
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
    bleed: int = 1,
    metadata_by_name: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """High-level helper used by UI."""
    os.makedirs(out_dir, exist_ok=True)
    converted_items = [(img, {"name": name}) for name, img in items]

    atlases = pack_sprites_to_atlas(
        converted_items,
        max_size=max_size,
        padding=padding,
        allow_rotate=allow_rotate,
        bleed=bleed,
    )

    results = []
    for idx, (atlas_img, meta) in enumerate(atlases):
        if metadata_by_name:
            for entry in meta:
                source = metadata_by_name.get(entry["name"])
                if source is None:
                    continue
                for key in ("pivot", "pivot_normalized"):
                    if key in source:
                        entry[key] = source[key]
        atlas_path = os.path.join(out_dir, f"{base_name}_{idx}.png")
        json_path = os.path.join(out_dir, f"{base_name}_{idx}.json")
        save_atlas(atlas_img, meta, atlas_path, json_path)
        results.append(
            {"atlas_path": atlas_path, "json_path": json_path, "entries": meta}
        )
    return results
