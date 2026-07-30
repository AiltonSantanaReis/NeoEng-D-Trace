"""Implementation of :mod:`src.exporters.sprite_exporter`.

Implementation preserved in the single ``src`` source tree.
"""

import os
import tempfile
from typing import List, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw

try:
    import cv2

    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

# Robust Pillow Resampling Constants
try:
    RESAMPLING_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    # Fallback for Pillow < 9.1.0
    RESAMPLING_LANCZOS = Image.LANCZOS  # type: ignore

from src.core.logger import logger


def _to_pil_rgba(image: Union[np.ndarray, Image.Image]) -> Image.Image:
    """Normalize input image to PIL RGBA."""
    if isinstance(image, Image.Image):
        return image.convert("RGBA")

    if not isinstance(image, np.ndarray):
        raise ValueError("Image must be np.ndarray or PIL.Image")

    if image.ndim == 3:
        if image.shape[2] == 3:
            # Assume BGR if cv2 is available (standard for cv2.imread)
            if _HAS_CV2:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb = image  # Assume RGB if no cv2 context
            return Image.fromarray(rgb, "RGB").convert("RGBA")

        elif image.shape[2] == 4:
            if _HAS_CV2:
                rgba = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            else:
                rgba = image
            return Image.fromarray(rgba, "RGBA")

    raise ValueError(f"Unsupported numpy image shape: {image.shape}")


def extract_masked_sprite(
    image: Union[np.ndarray, Image.Image],
    polygon: List[Tuple[int, int]],
    padding: int = 4,
    antialias: str = "high",
    trim: bool = True,
) -> Image.Image:
    # Normalize image
    pil_img = _to_pil_rgba(image)
    w, h = pil_img.size

    # Sanitize and clamp polygon points to image boundaries
    # This prevents drawing outside the mask canvas
    poly_int = []
    for x, y in polygon:
        cx = max(0, min(w, int(round(x))))
        cy = max(0, min(h, int(round(y))))
        poly_int.append((cx, cy))

    if len(poly_int) < 3:
        # Invalid polygon, return empty sprite
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    # Create mask
    # 1. High Quality (Supersampling)
    if antialias == "high":
        scale = 2
        mask_w, mask_h = w * scale, h * scale
        mask_hr = Image.new("L", (mask_w, mask_h), 0)
        draw_hr = ImageDraw.Draw(mask_hr)

        # Scale polygon points
        poly_hr = [(x * scale, y * scale) for x, y in poly_int]
        draw_hr.polygon(poly_hr, fill=255)

        # Optional: Gaussian Blur for softer edges
        if _HAS_CV2:
            mask_np = np.array(mask_hr)
            # Kernel size 5x5 for 2x scale is appropriate
            mask_np = cv2.GaussianBlur(mask_np, (5, 5), 0)
            mask_hr = Image.fromarray(mask_np)

        # Downsample
        mask = mask_hr.resize((w, h), RESAMPLING_LANCZOS)

    # 2. Fast Quality (Standard)
    else:
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(poly_int, fill=255)

        if antialias == "fast" and _HAS_CV2:
            mask_np = np.array(mask)
            mask_np = cv2.GaussianBlur(mask_np, (3, 3), 0)
            mask = Image.fromarray(mask_np)

    # Apply mask as alpha channel
    # Note: original image might already have alpha, we compose them
    r, g, b, a = pil_img.split()

    # Combine original alpha with mask alpha (A_out = A_in * Mask / 255)
    # Using ImageChops.multiply logic but for L mode
    # A simpler way is using numpy or composite, but putalpha replaces.
    # Let's respect original transparency:

    # If image has transparency, mask should only reveal where BOTH are opaque
    # mask_final = min(original_alpha, polygon_mask)
    if a:
        # Convert to arrays for blending
        a_arr = np.array(a).astype(float)
        m_arr = np.array(mask).astype(float)
        # Normalize 0-1, multiply, scale back
        combined = (a_arr * m_arr) / 255.0
        mask = Image.fromarray(combined.astype(np.uint8))

    pil_img.putalpha(mask)

    # Get bbox of the visible content
    bbox = mask.getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    # Add padding
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)

    sprite = pil_img.crop((x1, y1, x2, y2))

    if trim:
        tb = sprite.getbbox()
        if tb:
            sprite = sprite.crop(tb)
        else:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    return sprite


def export_sprite(
    obj_id: str,
    scene,
    out_path: str,
    *,
    padding: int = 4,
    trim: bool = True,
    antialias: str = "high",
    format: str = "PNG",
    steps_per_segment: int = 20,
) -> Image.Image:
    """
    Exporta um sprite individual para arquivo.
    """
    # Validate inputs
    if not hasattr(scene, "image") or scene.image is None:
        raise ValueError("Scene must have a loaded image")

    if obj_id not in scene.objects:
        raise ValueError(f"Object {obj_id} not found in scene")

    obj = scene.objects[obj_id]

    # Resolve geometry (Polygon vs Bezier)
    if hasattr(obj, "beziers") and obj.beziers:
        if hasattr(scene, "sample_beziers_to_polygon"):
            polygon = scene.sample_beziers_to_polygon(obj.beziers, steps_per_segment)
        else:
            # Fallback if method missing
            polygon = obj.polygon
    else:
        polygon = obj.polygon

    if not polygon or len(polygon) < 3:
        raise ValueError(f"Object {obj_id} has invalid polygon")

    # Extract
    try:
        sprite = extract_masked_sprite(
            scene.image, polygon, padding=padding, antialias=antialias, trim=trim
        )
    except Exception as e:
        logger.error(f"Failed to extract sprite for {obj_id}: {e}")
        raise

    # Save
    if out_path:
        try:
            save_sprite(sprite, out_path)
        except Exception as e:
            logger.error(f"Failed to save sprite to {out_path}: {e}")
            raise IOError(f"Save failed: {e}")

    return sprite


def save_sprite(sprite: Image.Image, path: str):
    """Save a sprite with an atomic same-filesystem replacement."""
    dirn = os.path.dirname(path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)

    # Use the explicit PNG format when the destination has no extension;
    # otherwise Pillow infers the format from the requested extension.
    ext = os.path.splitext(path)[1].lower()
    fmt = "PNG" if not ext else None

    fd, tmp_path = tempfile.mkstemp(prefix="tmp_sprite_", suffix=ext, dir=dirn or ".")
    os.close(fd)

    try:
        sprite.save(tmp_path, format=fmt)
        # os.replace safely replaces an existing file on Windows and POSIX.
        os.replace(tmp_path, path)
        tmp_path = ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
