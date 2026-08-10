# src/tools/mask_utils.py
"""
Mask processing utilities for polygon detection.

This module provides functions used by the automatic polygon
detection pipeline: thresholding, morphology, contour extraction
and simplification helpers.
"""

import logging
import math
from typing import Any, List, Optional, Sequence, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def threshold_adaptive(
    image: np.ndarray, block_size: int = 11, C: int = 2
) -> np.ndarray:
    """
    Apply adaptive thresholding to create binary mask.
    """
    if not isinstance(image, np.ndarray):
        raise ValueError("image deve ser np.ndarray")
    if image.ndim not in [2, 3]:
        raise ValueError("image deve ter 2 ou 3 dimensões")

    img_gray = image
    if len(image.shape) == 3:
        img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    return cv2.adaptiveThreshold(
        img_gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        C,
    )


def close_small_gaps(
    mask: np.ndarray,
    kernel_size: int = 3,
    kernel_shape: str = "rect",
    custom_kernel: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Close small gaps in binary mask using morphological operations.
    """
    if not isinstance(mask, np.ndarray):
        logger.error("mask deve ser np.ndarray")
        raise ValueError("mask deve ser np.ndarray")
    if mask.ndim != 2:
        logger.error("mask deve ser uma matriz 2D")
        raise ValueError("mask deve ser uma matriz 2D")

    if kernel_shape == "rect":
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    elif kernel_shape == "ellipse":
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )
    elif kernel_shape == "custom":
        if custom_kernel is None:
            logger.error('custom_kernel deve ser fornecido para kernel_shape="custom"')
            raise ValueError(
                'custom_kernel deve ser fornecido para kernel_shape="custom"'
            )
        kernel = custom_kernel
    else:
        logger.error(f"kernel_shape inválido: {kernel_shape}")
        raise ValueError(f"kernel_shape inválido: {kernel_shape}")

    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def extract_contours(mask: np.ndarray) -> List[np.ndarray]:
    """
    Extract contours from binary mask.
    """
    if not isinstance(mask, np.ndarray):
        raise ValueError("mask deve ser np.ndarray")
    if mask.ndim != 2:
        raise ValueError("mask deve ser uma matriz 2D")

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return list(contours)


def rdp_simplify(
    points: Sequence[Tuple[Any, Any]], epsilon: float = 2.0
) -> List[Tuple[float, float]]:
    """
    Simplify polygon using Ramer-Douglas-Peucker algorithm.
    """
    if not isinstance(points, (list, tuple, Sequence)):
        logger.error("points deve ser uma lista de tuplas")
        raise ValueError("points deve ser uma lista de tuplas")

    if len(points) < 3:
        # Menos de 3 pontos não formam um polígono fechado simplificável
        return [(float(x), float(y)) for x, y in points]

    # Ensure points are floats for numerical stability
    pts: List[Tuple[float, float]] = [(float(x), float(y)) for x, y in points]

    # Helper: Distance from point p to line segment p1-p2
    def point_line_distance(p, p1, p2):
        if p1 == p2:
            return math.hypot(p[0] - p1[0], p[1] - p1[1])

        # Area of triangle * 2 / base length
        # (x2-x1)(y1-y0) - (x1-x0)(y2-y1)
        num = abs((p2[0] - p1[0]) * (p1[1] - p[1]) - (p1[0] - p[0]) * (p2[1] - p1[1]))
        den = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        return num / den if den != 0 else 0.0

    max_dist = 0.0
    index = 0

    # Find point with max distance from line segment [first, last]
    for i in range(1, len(pts) - 1):
        dist = point_line_distance(pts[i], pts[0], pts[-1])
        if dist > max_dist:
            max_dist = dist
            index = i

    if max_dist > epsilon:
        # Recursive call
        left = rdp_simplify(pts[: index + 1], epsilon)
        right = rdp_simplify(pts[index:], epsilon)
        return left[:-1] + right
    else:
        return [pts[0], pts[-1]]


def curvature_adaptive_simplify(
    contour: Sequence[Any],
    base_eps: float = 2.0,
    curvature_factor: float = 1.0,
    min_points: int = 3,
) -> List[Tuple[int, int]]:
    """
    Simplify contour using a curvature-adaptive algorithm.
    """
    if not (isinstance(contour, np.ndarray) or isinstance(contour, list)):
        logger.error("contour deve ser np.ndarray ou list")
        raise ValueError("contour deve ser np.ndarray ou list")

    # Convert contour to list of points
    points: List[Tuple[int, int]] = []
    if isinstance(contour, np.ndarray):
        if contour.ndim == 3 and contour.shape[2] == 2:
            # OpenCV contour format (N, 1, 2)
            points = [(int(p[0][0]), int(p[0][1])) for p in contour]
        else:
            # Assume (N, 2) format
            points = [(int(p[0]), int(p[1])) for p in contour]
    else:
        points = [(int(p[0]), int(p[1])) for p in contour]  # type: ignore

    if len(points) < 3:
        return points

    # Compute discrete curvature for each point
    curvatures = _compute_discrete_curvature(points)

    # Adapt epsilon based on curvature
    adaptive_epsilons = []
    max_curvature = max(curvatures) if curvatures else 1.0

    for curvature in curvatures:
        if max_curvature > 0:
            normalized_curv = curvature / max_curvature
            # Higher curvature -> Lower epsilon (preserve detail)
            # Lower curvature -> Higher epsilon (simplify more)
            adaptive_eps = base_eps * (1.0 + curvature_factor * (1.0 - normalized_curv))
        else:
            adaptive_eps = base_eps
        adaptive_epsilons.append(adaptive_eps)

    if isinstance(min_points, bool) or not isinstance(min_points, int):
        raise ValueError("min_points deve ser um inteiro")
    min_points = max(3, min(min_points, len(points)))

    simplified = _iterative_rdp_with_weights(
        points, adaptive_epsilons, min_points=min_points
    )

    if len(simplified) < 3:
        logger.warning("Simplificação excessiva, poucos pontos preservados.")

    return [(int(round(x)), int(round(y))) for x, y in simplified]


def _compute_discrete_curvature(
    points: Sequence[Tuple[Any, Any]],
) -> List[float]:
    """
    Compute discrete curvature at each point using angle-based method.
    """
    if len(points) < 3:
        return [0.0] * len(points)

    curvatures = []

    for i in range(len(points)):
        prev_idx = (i - 1) % len(points)
        next_idx = (i + 1) % len(points)

        p_prev = np.array(points[prev_idx], dtype=float)
        p_curr = np.array(points[i], dtype=float)
        p_next = np.array(points[next_idx], dtype=float)

        v1 = p_prev - p_curr
        v2 = p_next - p_curr

        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        denominator = norm_v1 * norm_v2

        if denominator < 1e-8:
            curvatures.append(0.0)
            continue

        cos_angle = np.dot(v1, v2) / denominator
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)

        # Curvature is deviation from straight line (pi - angle)
        curvature = abs(np.pi - angle)
        curvatures.append(curvature)

    return curvatures


def _iterative_rdp_with_weights(
    points: Sequence[Tuple[Any, Any]],
    weights: Sequence[float],
    min_points: int = 3,
) -> List[Tuple[float, float]]:
    """
    Iterative RDP simplification with point weights.
    """
    if len(points) < 3:
        return [(float(x), float(y)) for x, y in points]

    current_points = [(float(x), float(y)) for x, y in points]
    current_weights = (
        list(weights) if len(weights) == len(points) else [1.0] * len(points)
    )

    min_points = max(3, min(int(min_points), len(current_points)))

    while len(current_points) > min_points:
        # Find point with least importance (highest epsilon/weight effectively)
        # Note: Logic inverted from docstring? Usually RDP removes points < epsilon.
        # Here we simulate RDP by iteratively removing the "flattest" point
        # that doesn't violate topology.

        # Remove the point with lowest curvature, represented by the
        # highest calculated adaptive epsilon.
        # High epsilon means low curvature and is therefore safe to remove.
        # So we want to remove points with HIGH weights first.

        # Find index with MAX weight (epsilon) excluding endpoints
        candidates = current_weights[1:-1]
        if not candidates:
            break

        max_weight = max(candidates)
        # Offset index by +1 because we sliced [1:-1]
        remove_idx = current_weights.index(max_weight, 1, -1)

        # Check geometric/topology constraints before removal
        removed_point = current_points[remove_idx]

        # Remove temporarily
        current_points.pop(remove_idx)
        current_weights.pop(remove_idx)

        # Check if removal breaks curvature preservation significantly
        if _violates_curvature_preservation(current_points, removed_point):
            # Revert and mark as non-removable (weight -1)
            current_points.insert(remove_idx, removed_point)
            current_weights.insert(remove_idx, -1.0)

        # Stop condition: if all remaining candidates are marked -1
        if all(w < 0 for w in current_weights[1:-1]):
            break

    return current_points


def _violates_curvature_preservation(
    points: List[Tuple[float, float]], removed_point: Tuple[float, float]
) -> bool:
    """
    Check if removing a point violates curvature preservation.
    """
    if len(points) < 3:
        return False

    threshold_rad = np.deg2rad(30)

    # We only need to check the neighbors of the removed point,
    # but since we don't know exactly where it was inserted in the simplified list
    # without finding nearest neighbors, we iterate (simplified for safety).
    # In a real heavy loop, this should be optimized.

    for i in range(len(points)):
        prev_idx = (i - 1) % len(points)
        next_idx = (i + 1) % len(points)

        v1 = np.array(points[prev_idx]) - np.array(points[i])
        v2 = np.array(points[next_idx]) - np.array(points[i])

        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            continue

        cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)

        if angle < threshold_rad:
            return True

    return False
