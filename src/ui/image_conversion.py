"""Conversion of supported image arrays into detached Qt images."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image as PILImage
from PySide6.QtGui import QImage

from src.core.logger import logger


def to_qimage(
    image: Any,
    *,
    has_gpu: bool = False,
    cupy_module: Any = None,
) -> QImage | None:
    if image is None:
        return None
    if has_gpu and cupy_module is not None and isinstance(image, cupy_module.ndarray):
        try:
            image = cupy_module.asnumpy(image)
        except Exception:
            return None
    if isinstance(image, PILImage.Image):
        if image.mode == "L":
            image = np.asarray(image)
        elif image.mode == "RGB":
            image = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        else:
            rgba = np.asarray(image.convert("RGBA"))
            image = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
    if not isinstance(image, np.ndarray):
        logger.error(
            "Unsupported image type for Qt conversion: %s",
            type(image).__name__,
        )
        return None
    if image.ndim not in (2, 3):
        logger.error("Unsupported image dimensions for Qt conversion: %s", image.ndim)
        return None
    if image.ndim == 3 and image.shape[2] not in (3, 4):
        logger.error("Unsupported channel count for Qt conversion: %s", image.shape[2])
        return None
    if any(dimension <= 0 for dimension in image.shape[:2]):
        logger.error("Empty image cannot be converted to QImage")
        return None
    if not image.flags["C_CONTIGUOUS"]:
        image = np.ascontiguousarray(image)

    height, width = image.shape[:2]
    if image.ndim == 2:
        return QImage(
            image.data,
            width,
            height,
            image.strides[0],
            QImage.Format.Format_Grayscale8,
        ).copy()
    if image.shape[2] == 3:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return QImage(
            rgb.data,
            width,
            height,
            rgb.strides[0],
            QImage.Format.Format_RGB888,
        ).copy()
    rgba = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
    return QImage(
        rgba.data,
        width,
        height,
        rgba.strides[0],
        QImage.Format.Format_RGBA8888,
    ).copy()
