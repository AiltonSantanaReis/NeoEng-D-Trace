# src/tools/edge_utils.py
"""
Multi-scale edge detection utilities for computer vision.
"""

from typing import List, Optional

import cv2
import numpy as np

try:
    from src.core.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def normalize_array(arr: np.ndarray) -> np.ndarray:
    """Normalize array to 0-255 range."""
    try:
        a = np.asarray(arr, dtype=np.float32)
        a_min = a.min()
        a_max = a.max()
        if a_max == a_min:
            return np.zeros(a.shape, dtype=np.uint8)
        normalized = ((a - a_min) / (a_max - a_min) * 255.0).astype(np.uint8)
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing array: {e}")
        return np.zeros_like(arr, dtype=np.uint8)


def sobel_magnitude(img: np.ndarray) -> np.ndarray:
    """Compute Sobel edge magnitude."""
    if not isinstance(img, np.ndarray):
        raise ValueError("img deve ser um numpy array")

    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Use CV_32F to prevent overflow/clipping during calculation
    sobelx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)

    sx_sq = np.square(sobelx, dtype=np.float32)
    sy_sq = np.square(sobely, dtype=np.float32)
    magnitude = np.sqrt(sx_sq + sy_sq)

    return magnitude.astype(np.float32)


def canny_edges(
    image: np.ndarray, threshold1: int = 100, threshold2: int = 200
) -> np.ndarray:
    """Apply Canny edge detection."""
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    return cv2.Canny(image, threshold1, threshold2)


def log_response(img: np.ndarray, sigma: float) -> np.ndarray:
    """Compute Laplacian of Gaussian (LoG) response."""
    if not isinstance(img, np.ndarray):
        raise ValueError("img deve ser um numpy array")
    if sigma <= 0:
        raise ValueError("sigma deve ser > 0")

    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Calculate optimal kernel size based on sigma
    ksize = int(6 * sigma + 1)
    if ksize < 3:
        ksize = 3
    if ksize % 2 == 0:
        ksize += 1

    blurred = cv2.GaussianBlur(img.astype(np.float32), (ksize, ksize), sigma)
    laplacian = cv2.Laplacian(blurred, cv2.CV_32F, ksize=3)
    return np.abs(laplacian).astype(np.float32)


def multi_scale_edges(
    img: np.ndarray,
    scales: Optional[List[float]] = None,
    weights: Optional[List[float]] = None,
) -> np.ndarray:
    """Compute multi-scale edge detection."""
    if not isinstance(img, np.ndarray):
        raise ValueError("img deve ser um numpy array")

    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    if scales is None:
        scales = [1.0, 2.0, 4.0]

    if weights is None:
        weights = [1.0 / len(scales)] * len(scales)
    elif len(weights) != len(scales):
        raise ValueError("Weights list must match scales list length")

    weights_arr = np.array(weights, dtype=np.float32)
    weights_arr = weights_arr / weights_arr.sum()

    combined: Optional[np.ndarray] = None

    for scale, w in zip(scales, weights_arr.tolist()):
        response = log_response(img, sigma=float(scale))
        if combined is None:
            combined = w * response.astype(np.float32)
        else:
            combined += w * response.astype(np.float32)

    if combined is None:
        return np.zeros_like(img, dtype=np.float32)

    return combined


def enhanced_edge_detection(
    img: np.ndarray, canny_thresh1: int = 50, canny_thresh2: int = 150
) -> np.ndarray:
    """
    Enhanced edge detection combining LoG, Sobel and Canny.
    Returns a uint8 image.
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 1. Multi-scale LoG (Textura fina e bordas suaves)
    log_edges = multi_scale_edges(img, scales=[0.5, 1.0, 2.0], weights=[0.4, 0.4, 0.2])

    # 2. Sobel (Gradiente direcional forte)
    sobel_edges = sobel_magnitude(img)

    # 3. Canny (Bordas finas e binárias)
    canny_edges_result = canny_edges(img, canny_thresh1, canny_thresh2).astype(float)

    # Normalização para 0.0 - 1.0
    log_norm = normalize_array(log_edges).astype(float) / 255.0
    sobel_norm = normalize_array(sobel_edges).astype(float) / 255.0
    canny_norm = canny_edges_result / 255.0

    # Combinação Ponderada
    # LoG e Sobel dão "corpo" à borda, Canny dá precisão
    combined = 0.4 * log_norm + 0.4 * sobel_norm + 0.2 * canny_norm

    result = (combined * 255).astype(np.uint8)
    return result
