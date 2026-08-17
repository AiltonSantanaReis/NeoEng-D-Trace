# src/tools/auto_detect.py
"""
Automatic polygon detection infrastructure.

This module provides high-level functions for detecting polygons in images
and creating scene objects from them.
"""

import math
from numbers import Real
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

import cv2
import numpy as np

from src.core.logger import logger
from src.core.operational_limits import (
    MAX_DECODED_IMAGE_BYTES,
    MAX_IMAGE_DIMENSION,
    MAX_IMAGE_PIXELS,
    MAX_POLYGON_POINTS,
    MAX_PROJECT_OBJECTS,
    MAX_PROJECT_POINTS,
)

from .edge_utils import enhanced_edge_detection, multi_scale_edges
from .mask_utils import (
    close_small_gaps,
    curvature_adaptive_simplify,
    rdp_simplify,
    threshold_adaptive,
)
from .segmentation import mask_contours, segment_grabcut
from .smoothing import catmull_rom_to_beziers, chaikin_smooth

# Large contours use bounded Douglas-Peucker to keep interactive detection responsive.
MAX_CURVATURE_SIMPLIFICATION_POINTS = 100


def _validate_detection_image(image: np.ndarray) -> None:
    if image.ndim not in {2, 3}:
        raise ValueError("image must be a 2D grayscale or RGB/RGBA array")
    if image.ndim == 3 and image.shape[2] not in {3, 4}:
        raise ValueError("image must be a 2D grayscale or RGB/RGBA array")
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


def _bounded_downscale(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("downscale must be a finite number inside (0, 1]")
    downscale = float(value)
    if not math.isfinite(downscale) or not 0.0 < downscale <= 1.0:
        raise ValueError("downscale must be a finite number inside (0, 1]")
    return downscale


def _bounded_chaikin_iterations(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("chaikin_iterations must be an integer")
    return value


def _bounded_morphology_kernel(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("morph_kernel_size must be an odd integer")
    if value < 1 or value > 31 or value % 2 == 0:
        raise ValueError("morph_kernel_size must be an odd integer between 1 and 31")
    return value


def _resize_grayscale(gray: np.ndarray, downscale: float) -> np.ndarray:
    if downscale == 1.0:
        return gray
    height, width = gray.shape
    new_width = max(1, int(width * downscale))
    new_height = max(1, int(height * downscale))
    return cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_LINEAR)


def _to_uint8_grayscale(image: np.ndarray) -> np.ndarray:
    """Return a stable 8-bit grayscale image for all supported inputs."""
    if image.ndim == 3:
        if image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()
    if gray.dtype == np.uint8:
        return gray
    values = np.asarray(gray, dtype=np.float32)
    if not np.isfinite(values).all():
        values = np.nan_to_num(values, nan=0.0, posinf=255.0, neginf=0.0)
    low = float(values.min())
    high = float(values.max())
    if high <= low:
        return np.zeros(values.shape, dtype=np.uint8)
    if low >= 0.0 and high <= 255.0:
        return np.rint(values).astype(np.uint8)
    return np.rint((values - low) * 255.0 / (high - low)).astype(np.uint8)


def _alpha_foreground_mask(image: np.ndarray) -> Optional[np.ndarray]:
    """Use a non-empty alpha channel when the source image has one."""
    if image.ndim != 3 or image.shape[2] != 4:
        return None
    alpha = _to_uint8_grayscale(image[:, :, 3])
    if int(alpha.max()) <= 0 or int(alpha.min()) == int(alpha.max()):
        return None
    return np.where(alpha > 8, 255, 0).astype(np.uint8)


def _foreground_mask(image: np.ndarray, gray: np.ndarray) -> np.ndarray:
    """Build a filled foreground mask, falling back to closed edges."""
    alpha_mask = _alpha_foreground_mask(image)
    if alpha_mask is not None:
        return cv2.morphologyEx(
            alpha_mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        )
    if int(gray.max()) == int(gray.min()):
        return np.zeros_like(gray, dtype=np.uint8)

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    height, width = gray.shape
    best = np.zeros_like(gray, dtype=np.uint8)
    best_score = 0.0
    best_has_interior_components = False
    for candidate in (binary, cv2.bitwise_not(binary)):
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            candidate, connectivity=8
        )
        selected = np.zeros_like(candidate, dtype=np.uint8)
        interior_area = 0
        for label in range(1, count):
            x, y, w, h, area = stats[label].tolist()
            if x != 0 and y != 0 and x + w < width and y + h < height:
                selected[labels == label] = 255
                interior_area += int(area)
        has_interior_components = interior_area > 0
        if interior_area == 0:
            selected = candidate.copy()  # type: ignore[assignment]
            interior_area = int(np.count_nonzero(selected))
        ratio = interior_area / float(max(1, width * height))
        score = float(interior_area) * (
            10.0 if has_interior_components else (0.1 if ratio > 0.5 else 1.0)
        )
        if (has_interior_components and not best_has_interior_components) or (
            has_interior_components == best_has_interior_components
            and score > best_score
        ):
            best = selected
            best_score = score
            best_has_interior_components = has_interior_components

    if np.count_nonzero(best) > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        return cv2.morphologyEx(best, cv2.MORPH_CLOSE, kernel)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), 1.0), 50, 150)
    return cv2.morphologyEx(
        edges, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    )


def _approximate_contour(
    contour: np.ndarray,
    epsilon: float,
    max_points: int = MAX_POLYGON_POINTS,
) -> List[Tuple[int, int]]:
    """Approximate a contour while keeping the persisted polygon bounded."""
    if float(cv2.arcLength(contour, True)) <= 0.0:
        return []
    current_epsilon = max(0.25, float(epsilon))
    approximation = cv2.approxPolyDP(contour, current_epsilon, True)
    while len(approximation) > max_points:
        current_epsilon *= 1.35
        approximation = cv2.approxPolyDP(contour, current_epsilon, True)
    return [
        (int(x), int(y))
        for x, y in np.asarray(approximation, dtype=np.int32).reshape(-1, 2).tolist()
    ]


def _bounded_polygon_points(
    points: Sequence[Tuple[Any, Any]], max_points: int = MAX_POLYGON_POINTS
) -> List[Tuple[int, int]]:
    """Reduce a smoothed polygon only when it exceeds the storage contract."""
    if len(points) <= max_points:
        return [(int(round(x)), int(round(y))) for x, y in points]
    array = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    return _approximate_contour(array, max(0.25, len(points) / max_points))


def _validate_contours(contours: Sequence[np.ndarray]) -> None:
    if len(contours) > MAX_PROJECT_OBJECTS:
        raise ValueError(
            f"detected contour count exceeds the limit of {MAX_PROJECT_OBJECTS}"
        )
    point_count = sum(len(contour) for contour in contours)
    if point_count > MAX_PROJECT_POINTS:
        raise ValueError(
            f"detected contour points exceed the limit of {MAX_PROJECT_POINTS}"
        )


def _validate_detection_result(polygons: Sequence[Dict[str, Any]]) -> None:
    if len(polygons) > MAX_PROJECT_OBJECTS:
        raise ValueError(
            f"detected polygon count exceeds the limit of {MAX_PROJECT_OBJECTS}"
        )
    point_count = 0
    for polygon in polygons:
        points = polygon.get("polygon", [])
        if len(points) > MAX_POLYGON_POINTS:
            raise ValueError(
                f"detected polygon exceeds the point limit of {MAX_POLYGON_POINTS}"
            )
        point_count += len(points)
    if point_count > MAX_PROJECT_POINTS:
        raise ValueError(
            f"detected polygon points exceed the limit of {MAX_PROJECT_POINTS}"
        )


class DetectResult(list):
    """List-like result that also supports dict-style access."""

    def __init__(self, polygons: List[Dict], feedback: Optional[Dict[str, Any]] = None):
        super().__init__(polygons)
        self.feedback: Dict[str, Any] = feedback or {}

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if key == "polygons":
                return list(self)
            if key == "feedback":
                return self.feedback
            raise KeyError(key)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "polygons":
            return list(self)
        if key == "feedback":
            return self.feedback
        return default


def detect_polygons(image: np.ndarray, mode: str = "basic", **kwargs: Any) -> Any:
    """
    Detect polygons in an image using various algorithms.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a numpy.ndarray")
    _validate_detection_image(image)
    if mode not in ["basic", "perfect", "enhanced", "grabcut"]:
        raise ValueError(f"Unknown mode: {mode}")
    try:
        if mode == "basic":
            result = _detect_polygons_basic(image, **kwargs)
        elif mode == "perfect":
            result = _detect_polygons_perfect(image, **kwargs)
        elif mode == "grabcut":
            result, segmentation_feedback = _detect_polygons_grabcut(image, **kwargs)
        else:
            result = _detect_polygons_enhanced(image, **kwargs)

        feedback = {
            "status": "ok",
            "message": f"Detected {len(result)} polygons in mode {mode}",
            "mode": mode,
            "polygon_count": len(result),
        }
        if mode == "grabcut":
            feedback["segmentation"] = segmentation_feedback
        return DetectResult(result, feedback)
    except Exception as e:
        logger.error(f"Error in detect_polygons: {e}")
        raise


def _detect_polygons_grabcut(
    image: np.ndarray, **kwargs: Any
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Detect one ROI foreground using the real OpenCV GrabCut algorithm."""
    roi = kwargs.get("roi")
    if roi is None:
        raise ValueError("grabcut detection requires an roi=(x, y, width, height)")
    segmentation = segment_grabcut(
        image,
        roi,
        iterations=int(kwargs.get("grabcut_iterations", 5)),
        padding=int(kwargs.get("roi_padding", 2)),
        keep_components=str(kwargs.get("keep_components", "largest")),
    )
    min_area = float(kwargs.get("min_area", 100.0))
    epsilon = float(kwargs.get("rdp_epsilon", 1.5))
    include_holes = bool(kwargs.get("detect_holes", True))
    contours, hierarchy = mask_contours(segmentation.mask, include_holes=include_holes)
    _validate_contours(contours)
    polygons: List[Dict[str, Any]] = []
    for index, contour in enumerate(contours):
        parent = (
            int(hierarchy[0][index][3])
            if hierarchy is not None and index < len(hierarchy[0])
            else -1
        )
        if parent != -1:
            continue
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue
        outer = _approximate_contour(contour, epsilon)
        if len(outer) < 3:
            continue
        holes: List[List[Tuple[int, int]]] = []
        child = (
            int(hierarchy[0][index][2])
            if hierarchy is not None and index < len(hierarchy[0])
            else -1
        )
        while child != -1:
            hole_contour = contours[child]
            if cv2.contourArea(hole_contour) >= min_area:
                hole = _approximate_contour(hole_contour, epsilon)
                if len(hole) >= 3:
                    holes.append(hole)
            child = int(hierarchy[0][child][0]) if hierarchy is not None else -1
        x, y, width, height = cv2.boundingRect(contour)
        perimeter = cv2.arcLength(contour, True)
        convex_hull_area = cv2.contourArea(cv2.convexHull(contour))
        record: Dict[str, Any] = {
            "polygon": outer,
            "area": area,
            "bbox": (x, y, width, height),
            "is_hole": False,
            "holes": holes,
            "quality_metrics": {
                "vertex_count": len(outer),
                "hole_count": len(holes),
                "foreground_ratio": segmentation.foreground_ratio,
                "circularity": (
                    float(4.0 * math.pi * area / (perimeter * perimeter))
                    if perimeter > 0.0
                    else 0.0
                ),
                "convexity": (
                    float(area / convex_hull_area) if convex_hull_area > 0.0 else 0.0
                ),
                "perimeter": float(perimeter),
            },
        }
        polygons.append(record)
    _validate_detection_result(polygons)
    return polygons, {
        "roi": segmentation.roi,
        "foreground_pixels": segmentation.foreground_pixels,
        "foreground_ratio": segmentation.foreground_ratio,
        "components": segmentation.components,
        "iterations": segmentation.iterations,
        "hole_contours_preserved": include_holes,
    }


def _detect_polygons_basic(image: np.ndarray, **kwargs: Any) -> List[Dict[str, Any]]:
    """Basic polygon detection."""
    downscale = _bounded_downscale(kwargs.get("downscale", 1.0))
    canny_threshold1 = int(kwargs.get("canny_threshold1", 100))
    canny_threshold2 = int(kwargs.get("canny_threshold2", 200))
    rdp_epsilon = float(kwargs.get("rdp_epsilon", 2.0))
    min_area = float(kwargs.get("min_area", 100.0))
    detect_holes = bool(kwargs.get("detect_holes", True))

    gray = _to_uint8_grayscale(image)
    source_mask = _foreground_mask(image, gray)
    mask = _resize_grayscale(source_mask, downscale)
    if np.count_nonzero(mask) == 0:
        gray = _resize_grayscale(gray, downscale)
        blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
        mask = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    retr_mode = cv2.RETR_CCOMP if detect_holes else cv2.RETR_EXTERNAL
    contours, hierarchy = cv2.findContours(mask, retr_mode, cv2.CHAIN_APPROX_NONE)
    _validate_contours(contours)

    detected_polygons = []

    for index, contour in enumerate(contours):
        if hierarchy is not None and hierarchy[0][index][3] != -1:
            continue
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        # Explicit type cast for contour points
        # Contour shape is (N, 1, 2)
        points_list: List[Tuple[float, float]] = []
        for i in range(len(contour)):
            # Accessing via item() or explicit index ensures we get
            # python scalars
            px = float(contour[i][0][0])
            py = float(contour[i][0][1])
            points_list.append((px, py))

        simplified_points: List[Tuple[float, float]]
        if len(points_list) > 2:
            # Pass epsilon as positional to allow mocks that expect positional arg
            simplified_points = rdp_simplify(points_list, rdp_epsilon)
        else:
            simplified_points = points_list

        if len(simplified_points) < 3:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        result_points: List[Tuple[int, int]] = []
        holes: List[List[Tuple[int, int]]] = []
        child_index = (
            int(hierarchy[0][index][2])
            if detect_holes and hierarchy is not None
            else -1
        )
        while child_index != -1:
            hole_contour = contours[child_index]
            if cv2.contourArea(hole_contour) >= min_area:
                hole_points = [
                    (float(hole_point[0][0]), float(hole_point[0][1]))
                    for hole_point in hole_contour
                ]
                if len(hole_points) > 2:
                    simplified_hole = rdp_simplify(hole_points, rdp_epsilon)
                else:
                    simplified_hole = hole_points
                if len(simplified_hole) >= 3:
                    holes.append(
                        [(int(px), int(py)) for px, py in simplified_hole]
                    )
            child_index = int(hierarchy[0][child_index][0])

        if downscale != 1.0:
            scale_factor = 1.0 / downscale
            result_points = [
                (int(px * scale_factor), int(py * scale_factor))
                for px, py in simplified_points
            ]
            holes = [
                [(int(px * scale_factor), int(py * scale_factor)) for px, py in hole]
                for hole in holes
            ]
            x, y, w, h = (
                int(x * scale_factor),
                int(y * scale_factor),
                int(w * scale_factor),
                int(h * scale_factor),
            )
            area = area * (scale_factor**2)
        else:
            result_points = [(int(px), int(py)) for px, py in simplified_points]

        detected_polygons.append(
            {
                "polygon": result_points,
                "area": float(area),
                "bbox": (x, y, w, h),
                "holes": holes,
            }
        )

    _validate_detection_result(detected_polygons)
    return detected_polygons


def _detect_polygons_perfect(image: np.ndarray, **kwargs: Any) -> List[Dict[str, Any]]:
    """Perfect polygon detection."""
    downscale = _bounded_downscale(kwargs.get("downscale", 1.0))
    base_eps = float(kwargs.get("base_eps", 2.0))
    curvature_factor = float(kwargs.get("curvature_factor", 1.0))
    min_area = float(kwargs.get("min_area", 100.0))
    decompose_convex = bool(kwargs.get("decompose_convex", False))
    watershed_distance = int(kwargs.get("watershed_distance", 10))
    separate_touching = bool(
        kwargs.get("separate_touching", "watershed_distance" in kwargs)
    )
    fg_bg_threshold = int(kwargs.get("fg_bg_threshold", 200))
    mean_threshold = int(kwargs.get("mean_threshold", 150))
    detect_holes = bool(kwargs.get("detect_holes", True))

    gray = _to_uint8_grayscale(image)
    source_mask = _foreground_mask(image, gray)
    orig_height, orig_width = gray.shape

    gray = _resize_grayscale(gray, downscale)
    mask = _resize_grayscale(source_mask, downscale)

    # Use explicit casting for numpy operations to satisfy mypy
    gray_float = gray.astype(np.float32)
    has_clear_fg_bg = (
        gray.max() >= fg_bg_threshold and np.mean(gray_float) < mean_threshold
    )
    small_image = (orig_width * orig_height) <= 40000

    if np.count_nonzero(mask) == 0:
        if has_clear_fg_bg:
            _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        elif small_image:
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            edge_response = multi_scale_edges(
                gray, scales=[1.0, 2.0, 4.0], weights=[0.5, 0.3, 0.2]
            )
            mask = threshold_adaptive(
                edge_response.astype(np.uint8), block_size=11, C=2
            )

    mask = close_small_gaps(mask, kernel_size=3)

    separated_mask: np.ndarray
    if not small_image and separate_touching:
        if has_clear_fg_bg:
            watershed_distance = max(1, watershed_distance // 2)

        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        sure_fg = np.uint8(dist_transform > watershed_distance)

        if np.sum(sure_fg) == 0 and watershed_distance > 1:
            sure_fg = np.uint8(dist_transform > max(1, watershed_distance // 2))

        kernel = np.ones((3, 3), np.uint8)
        sure_bg = cv2.dilate(mask, kernel, iterations=2)

        # Explicitly cast to prevent overload errors
        sure_bg_mat = sure_bg
        sure_fg_mat = sure_fg
        unknown = cv2.subtract(sure_bg_mat, sure_fg_mat)  # type: ignore

        _, markers = cv2.connectedComponents(sure_fg)  # type: ignore
        markers = markers + 1
        markers[unknown == 255] = 0

        color_gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(color_gray, markers)

        separated_mask = np.zeros_like(mask)
        for label in np.unique(markers):
            if label > 1:
                separated_mask[markers == label] = 255

        if np.sum(separated_mask) == 0:
            separated_mask = mask.copy()
    else:
        separated_mask = mask.copy()

    contours, hierarchy = cv2.findContours(
        separated_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )
    _validate_contours(contours)

    detected_polygons = []

    for i, contour in enumerate(contours):
        if hierarchy is not None and hierarchy[0][i][3] != -1:
            continue

        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        simplified_points_int: List[Tuple[int, int]]
        if small_image:
            peri = cv2.arcLength(contour, True)
            eps = max(1.0, 0.01 * peri)
            approx = cv2.approxPolyDP(contour, eps, True)
            simplified_points_int = [
                (int(x), int(y))
                for x, y in np.asarray(approx, dtype=np.int32).reshape(-1, 2).tolist()
            ]
        else:
            # The adaptive simplifier is quadratic for dense contours.
            if len(contour) > MAX_CURVATURE_SIMPLIFICATION_POINTS:
                simplified_points_int = _approximate_contour(
                    contour, max(0.25, base_eps * 0.25)
                )
            else:
                simplified_points_int = curvature_adaptive_simplify(
                    cast(Sequence[Any], contour),
                    base_eps=base_eps,
                    curvature_factor=curvature_factor,
                )

            # Curvature simplification can collapse a smooth arc to a few
            # vertices. Refine only those cases; polygon storage remains bounded.
            if len(simplified_points_int) <= 4 and len(contour) > 40:
                refined = _approximate_contour(contour, max(0.35, base_eps * 0.35))
                if len(refined) > len(simplified_points_int):
                    simplified_points_int = refined
            simplified_points_int = _bounded_polygon_points(simplified_points_int)
        if len(simplified_points_int) < 3:
            continue

        holes: List[List[Tuple[int, int]]] = []
        if detect_holes and hierarchy is not None:
            child_index = int(hierarchy[0][i][2])
            while child_index != -1:
                child_contour = contours[child_index]
                if cv2.contourArea(child_contour) >= min_area:
                    child_points = _approximate_contour(
                        child_contour, max(0.25, base_eps)
                    )
                    if len(child_points) >= 3:
                        holes.append(child_points)
                child_index = int(hierarchy[0][child_index][0])

        if decompose_convex:
            convex_hull = cv2.convexHull(contour)
            simplified_points_int = [
                (int(x), int(y))
                for x, y in np.asarray(convex_hull, dtype=np.int32)
                .reshape(-1, 2)
                .tolist()
            ]

        polygon_points = [(int(x), int(y)) for x, y in simplified_points_int]
        x, y, w, h = cv2.boundingRect(contour)

        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        convexity = area / cv2.contourArea(cv2.convexHull(contour)) if area > 0 else 0

        if downscale != 1.0:
            scale_factor = 1.0 / downscale
            polygon_points = [
                (int(px * scale_factor), int(py * scale_factor))
                for px, py in polygon_points
            ]
            holes = [
                [(int(px * scale_factor), int(py * scale_factor)) for px, py in hole]
                for hole in holes
            ]
            x, y, w, h = (
                int(x * scale_factor),
                int(y * scale_factor),
                int(w * scale_factor),
                int(h * scale_factor),
            )
            area = area * (scale_factor**2)

        detected_polygons.append(
            {
                "polygon": polygon_points,
                "area": float(area),
                "bbox": (x, y, w, h),
                "holes": holes,
                "quality_metrics": {
                    "vertex_count": len(polygon_points),
                    "circularity": float(circularity),
                    "convexity": float(convexity),
                    "perimeter": float(perimeter),
                },
            }
        )

    _validate_detection_result(detected_polygons)
    return detected_polygons


def _detect_polygons_enhanced(image: np.ndarray, **kwargs: Any) -> List[Dict[str, Any]]:
    """Enhanced polygon detection."""
    # Simplified for brevity, follows similar pattern of fixing types
    downscale = _bounded_downscale(kwargs.get("downscale", 1.0))
    canny_thresh1 = int(kwargs.get("canny_thresh1", 50))
    canny_thresh2 = int(kwargs.get("canny_thresh2", 150))
    min_area = float(kwargs.get("min_area", 50.0))
    chaikin_iterations = _bounded_chaikin_iterations(
        kwargs.get("chaikin_iterations", 0)
    )
    fit_bezier = bool(kwargs.get("fit_bezier", False))
    detect_holes = bool(kwargs.get("detect_holes", False))
    filled_shapes_threshold = int(kwargs.get("filled_shapes_threshold", 3))

    morph_kernel_size = _bounded_morphology_kernel(kwargs.get("morph_kernel_size", 3))
    gray = _to_uint8_grayscale(image)
    source_mask = _foreground_mask(image, gray)
    gray = _resize_grayscale(gray, downscale)
    mask = _resize_grayscale(source_mask, downscale)

    unique_vals = np.unique(gray)
    has_filled_shapes = (
        len(unique_vals) <= filled_shapes_threshold and 255 in unique_vals
    )
    if np.count_nonzero(mask) == 0 and has_filled_shapes:
        _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    elif np.count_nonzero(mask) == 0:
        edge_response = enhanced_edge_detection(gray, canny_thresh1, canny_thresh2)
        _, mask = cv2.threshold(
            edge_response, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
    mask = close_small_gaps(mask, kernel_size=morph_kernel_size)

    retr_mode = cv2.RETR_TREE if detect_holes else cv2.RETR_EXTERNAL
    contours, hierarchy = cv2.findContours(mask, retr_mode, cv2.CHAIN_APPROX_NONE)
    _validate_contours(contours)

    detected_polygons = []

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        hier_info = (
            hierarchy[0][i]
            if hierarchy is not None and i < len(hierarchy[0])
            else [-1, -1, -1, -1]
        )
        is_hole = detect_holes and hier_info[3] != -1

        raw_points = [
            (float(x), float(y))
            for x, y in np.asarray(contour, dtype=np.float32).reshape(-1, 2).tolist()
        ]
        unique_points = {point for point in raw_points}
        if len(unique_points) < 3 or cv2.arcLength(contour, True) <= 0:
            if len(raw_points) > MAX_POLYGON_POINTS:
                raise ValueError(
                    f"detected polygon exceeds the point limit of {MAX_POLYGON_POINTS}"
                )
            continue
        epsilon = max(0.25, float(kwargs.get("rdp_epsilon", 0.5)))
        if len(raw_points) > MAX_POLYGON_POINTS:
            epsilon = max(
                epsilon,
                cv2.arcLength(contour, True) / (MAX_POLYGON_POINTS * 2.0),
            )
        polygon_points_int = _approximate_contour(contour, epsilon)

        points_float = [(float(px), float(py)) for px, py in polygon_points_int]
        if chaikin_iterations > 0:
            points_float = chaikin_smooth(points_float, iterations=chaikin_iterations)
            polygon_points_int = _bounded_polygon_points(points_float)
            points_float = [(float(px), float(py)) for px, py in polygon_points_int]

        bezier_segments = None
        if fit_bezier:
            try:
                bezier_segments = catmull_rom_to_beziers(points_float, closed=True)
            except Exception:
                pass

        if len(polygon_points_int) < 3:
            continue

        holes: List[List[Tuple[int, int]]] = []
        if detect_holes and not is_hole:
            child_index = int(hier_info[2])
            while child_index != -1:
                child_contour = contours[child_index]
                if cv2.contourArea(child_contour) >= min_area:
                    child_points = _approximate_contour(
                        child_contour, max(0.25, float(kwargs.get("rdp_epsilon", 1.0)))
                    )
                    if len(child_points) >= 3:
                        holes.append(child_points)
                child_index = (
                    int(hierarchy[0][child_index][0]) if hierarchy is not None else -1
                )

        x, y, w, h = cv2.boundingRect(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        convexity = area / cv2.contourArea(cv2.convexHull(contour)) if area > 0 else 0

        if downscale != 1.0:
            scale_factor = 1.0 / downscale
            polygon_points_int = [
                (int(px * scale_factor), int(py * scale_factor))
                for px, py in polygon_points_int
            ]
            holes = [
                [(int(px * scale_factor), int(py * scale_factor)) for px, py in hole]
                for hole in holes
            ]
            x, y, w, h = (
                int(x * scale_factor),
                int(y * scale_factor),
                int(w * scale_factor),
                int(h * scale_factor),
            )
            area = area * (scale_factor**2)

        poly_data = {
            "polygon": polygon_points_int,
            "area": float(area),
            "bbox": (x, y, w, h),
            "is_hole": is_hole,
            "holes": holes,
            "hierarchy_level": hier_info[2],
            "quality_metrics": {
                "vertex_count": len(polygon_points_int),
                "circularity": float(circularity),
                "convexity": float(convexity),
                "perimeter": float(perimeter),
            },
        }
        if bezier_segments:
            poly_data["bezier_segments"] = bezier_segments

        detected_polygons.append(poly_data)

    _validate_detection_result(detected_polygons)
    return detected_polygons


def detect_and_create_objects(
    scene: Any,
    image: Optional[np.ndarray] = None,
    mode: str = "basic",
    apply: bool = True,
    **kwargs: Any,
) -> List[str]:
    """Detect polygons and optionally create one atomic history entry."""
    if image is None:
        if hasattr(scene, "image") and scene.image is not None:
            image = scene.image
        else:
            raise ValueError("No image provided and scene has no image")

    try:
        result = detect_polygons(image, mode, **kwargs)
        polygons = list(result)

        if not apply:
            return [f"preview_{i}" for i in range(len(polygons))]

        manager = getattr(scene, "cmd", None)
        if manager is None:
            raise RuntimeError("Undo/Redo command history is unavailable.")

        from src.core.commands import (
            Command,
            CommandStatus,
            CompositeCommand,
            CreateObjectCommand,
        )

        layer_id = kwargs.get("layer_id", "layer_default")
        commands: List[CreateObjectCommand] = []
        for poly_data in polygons:
            if not isinstance(poly_data, dict):
                raise ValueError("Detected polygon data must be a mapping.")
            if poly_data.get("is_hole", False):
                continue
            polygon = poly_data.get("polygon", [])
            poly_layer_id = poly_data.get("layer_id", layer_id)
            commands.append(CreateObjectCommand(polygon, poly_layer_id))

        if not commands:
            return []

        composite_commands: List[Command] = list(commands)
        composite = CompositeCommand(composite_commands)
        command_result = manager.execute(composite, scene)
        if command_result.status is CommandStatus.FAILED:
            raise RuntimeError(
                command_result.message or "Automatic object creation failed."
            )
        if command_result.status is CommandStatus.REJECTED:
            raise RuntimeError(
                command_result.message or "Automatic object creation was rejected."
            )
        if not command_result.changed:
            return []

        object_ids = [
            str(command.object_id)
            for command in commands
            if command.object_id is not None
        ]
        if len(object_ids) != len(commands):
            raise RuntimeError("Automatic object creation returned incomplete ids.")
        return object_ids
    except Exception as exc:
        logger.error("Error in detect_and_create_objects: %s", exc)
        raise
