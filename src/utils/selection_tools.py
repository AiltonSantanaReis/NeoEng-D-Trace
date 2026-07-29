"""Implementation of :mod:`src.utils.selection_tools`.

Implementation preserved in the single ``src`` source tree.
"""

from typing import List, Tuple, Optional
import numpy as np
import cv2


def polygon_to_mask(
    polygon: List[Tuple[int, int]],
    shape: Tuple[int, int],
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Converts a polygon (list of points) to a binary mask.
    """
    h, w = shape
    if mask is None or mask.shape != (h, w):
        mask = np.zeros((h, w), dtype=np.uint8)
    else:
        mask.fill(0)  # Clear the mask for reuse
        
    if polygon:
        # Convert list of tuples to numpy array of shape (N, 1, 2)
        pts = np.array(polygon, dtype=np.int32)
        pts = pts.reshape((-1, 1, 2))
        # fillPoly expects a list of arrays
        cv2.fillPoly(mask, [pts], 255)
    return mask


def mask_to_polygon(
    mask: np.ndarray, approx_dp: float = 1.0
) -> List[Tuple[int, int]]:
    """
    Finds the largest polygon contour in a binary mask.
    """
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return []

    # Choose largest contour by area
    c = max(contours, key=cv2.contourArea)

    if approx_dp > 0:
        epsilon = approx_dp
        c = cv2.approxPolyDP(c, epsilon, True)

    # Convert numpy array (N, 1, 2) back to list of tuples
    poly: List[Tuple[int, int]] = []
    if c is not None:
        for p in c:
            px = int(p[0][0])
            py = int(p[0][1])
            poly.append((px, py))

    return poly


def expand_contract_polygon(
    polygon: List[Tuple[int, int]], shape: Tuple[int, int], delta: int
) -> List[Tuple[int, int]]:
    """
    Expands (positive delta) or contracts (negative delta) a polygon by pixels.
    """
    h, w = shape
    mask = polygon_to_mask(polygon, (h, w))

    # Kernel size must be odd
    kernel_size = abs(delta) * 2 + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )

    processed_mask: np.ndarray
    if delta > 0:
        processed_mask = cv2.dilate(mask, kernel, iterations=1)
    elif delta < 0:
        processed_mask = cv2.erode(mask, kernel, iterations=1)
    else:
        processed_mask = mask

    poly = mask_to_polygon(processed_mask, approx_dp=1.0)
    return poly


def invert_selection(
    polygon: List[Tuple[int, int]], shape: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """
    Inverts the selection (creates a polygon of the empty space/bounding box).
    """
    h, w = shape
    mask = polygon_to_mask(polygon, (h, w))
    inv = cv2.bitwise_not(mask)
    poly = mask_to_polygon(inv, approx_dp=1.0)
    return poly
