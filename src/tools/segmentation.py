"""Deterministic foreground segmentation helpers used by automatic detection.

The module intentionally keeps GrabCut as an assisted, ROI-based operation.
GrabCut is not a universal zero-shot segmenter: its quality depends on the
rectangle containing one foreground subject and on the image contrast.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import cv2
import numpy as np

from src.core.operational_limits import (
    MAX_DECODED_IMAGE_BYTES,
    MAX_IMAGE_DIMENSION,
    MAX_IMAGE_PIXELS,
)


@dataclass(frozen=True)
class GrabCutResult:
    """Validated result of one GrabCut run."""

    mask: np.ndarray
    roi: tuple[int, int, int, int]
    foreground_pixels: int
    foreground_ratio: float
    components: int
    iterations: int


def _validate_image(image: np.ndarray) -> None:
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a numpy.ndarray")
    if image.ndim not in {2, 3}:
        raise ValueError("image must be grayscale, RGB, or RGBA")
    if image.ndim == 3 and image.shape[2] not in {3, 4}:
        raise ValueError("image must be grayscale, RGB, or RGBA")
    height, width = image.shape[:2]
    if height < 1 or width < 1:
        raise ValueError("image dimensions must be positive")
    if height > MAX_IMAGE_DIMENSION or width > MAX_IMAGE_DIMENSION:
        raise ValueError(f"image dimensions cannot exceed {MAX_IMAGE_DIMENSION}")
    if height * width > MAX_IMAGE_PIXELS:
        raise ValueError(f"image exceeds the pixel limit of {MAX_IMAGE_PIXELS}")
    if image.nbytes > MAX_DECODED_IMAGE_BYTES:
        raise ValueError(
            f"image exceeds the decoded byte limit of {MAX_DECODED_IMAGE_BYTES}"
        )
    if not np.issubdtype(image.dtype, np.number):
        raise ValueError("image dtype must be numeric")


def _uint8_image(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        values = image
    elif image.shape[2] == 4:
        values = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    else:
        values = image
    if values.dtype == np.uint8:
        return values if values.ndim == 3 else cv2.cvtColor(values, cv2.COLOR_GRAY2RGB)
    data = np.asarray(values, dtype=np.float32)
    if not np.isfinite(data).all():
        data = np.nan_to_num(data, nan=0.0, posinf=255.0, neginf=0.0)
    low = float(data.min())
    high = float(data.max())
    if high <= low:
        scaled = np.zeros(data.shape, dtype=np.uint8)
    elif low >= 0.0 and high <= 255.0:
        scaled = np.rint(data).astype(np.uint8)
    else:
        scaled = np.rint((data - low) * 255.0 / (high - low)).astype(np.uint8)
    return scaled if scaled.ndim == 3 else cv2.cvtColor(scaled, cv2.COLOR_GRAY2RGB)


def normalize_roi(
    roi: Sequence[Any], image_shape: Sequence[int], *, padding: int = 0
) -> tuple[int, int, int, int]:
    """Clamp an ROI to the image and reject empty or malformed selections."""
    if len(roi) != 4:
        raise ValueError("roi must contain x, y, width, and height")
    if isinstance(padding, bool) or not isinstance(padding, int) or padding < 0:
        raise ValueError("padding must be a non-negative integer")
    try:
        raw = [int(value) for value in roi]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("roi coordinates must be integers") from exc
    height, width = int(image_shape[0]), int(image_shape[1])
    x, y, w, h = raw
    if w <= 0 or h <= 0:
        raise ValueError("roi width and height must be positive")
    left = max(0, x - padding)
    top = max(0, y - padding)
    right = min(width, x + w + padding)
    bottom = min(height, y + h + padding)
    if right <= left or bottom <= top:
        raise ValueError("roi does not intersect the image")
    return left, top, right - left, bottom - top


def _clean_mask(mask: np.ndarray, *, keep_components: str) -> np.ndarray:
    binary = np.where(mask > 0, 255, 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(
        binary, cv2.MORPH_CLOSE, kernel
    )  # type: ignore[assignment]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count <= 1:
        return binary
    if keep_components not in {"largest", "all"}:
        raise ValueError("keep_components must be 'largest' or 'all'")
    if keep_components == "all":
        return binary
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return np.where(labels == largest, 255, 0).astype(np.uint8)


def segment_grabcut(
    image: np.ndarray,
    roi: Sequence[Any],
    *,
    iterations: int = 5,
    padding: int = 2,
    keep_components: str = "largest",
) -> GrabCutResult:
    """Segment the foreground inside a user-provided rectangle.

    The returned mask is binary (0/255), has the same dimensions as the
    source image, and is produced by the real OpenCV GrabCut implementation.
    """
    _validate_image(image)
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise ValueError("iterations must be an integer")
    if iterations < 1 or iterations > 20:
        raise ValueError("iterations must be between 1 and 20")
    normalized_roi = normalize_roi(roi, image.shape[:2], padding=padding)
    source = _uint8_image(image)
    x, y, width, height = normalized_roi
    grabcut_mask = np.zeros(source.shape[:2], dtype=np.uint8)
    background_model = np.zeros((1, 65), dtype=np.float64)
    foreground_model = np.zeros((1, 65), dtype=np.float64)
    cv2.grabCut(
        source,
        grabcut_mask,
        (x, y, width, height),
        background_model,
        foreground_model,
        iterations,
        cv2.GC_INIT_WITH_RECT,
    )
    binary = _clean_mask(
        np.where(
            (grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD),
            255,
            0,
        ),
        keep_components=keep_components,
    )
    components, _, _, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    foreground_pixels = int(np.count_nonzero(binary))
    total_pixels = int(binary.shape[0] * binary.shape[1])
    return GrabCutResult(
        binary,
        normalized_roi,
        foreground_pixels,
        foreground_pixels / float(max(1, total_pixels)),
        max(0, components - 1),
        iterations,
    )


def mask_contours(
    mask: np.ndarray, *, include_holes: bool = False
) -> tuple[list[np.ndarray], np.ndarray | None]:
    """Extract contours while preserving hierarchy information when requested."""
    if not isinstance(mask, np.ndarray) or mask.ndim != 2:
        raise ValueError("mask must be a two-dimensional numpy array")
    if mask.dtype != np.uint8:
        mask = np.where(mask > 0, 255, 0).astype(np.uint8)
    mode = cv2.RETR_CCOMP if include_holes else cv2.RETR_EXTERNAL
    raw_contours, raw_hierarchy = cv2.findContours(mask, mode, cv2.CHAIN_APPROX_NONE)
    contours = [np.asarray(contour) for contour in raw_contours]
    hierarchy = np.asarray(raw_hierarchy) if raw_hierarchy is not None else None
    return contours, hierarchy
