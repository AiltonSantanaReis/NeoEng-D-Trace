# src/tools/auto_detect.py
"""
Automatic polygon detection infrastructure.

This module provides high-level functions for detecting polygons in images
and creating scene objects from them.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

import cv2
import numpy as np

from src.core.logger import logger

from .edge_utils import enhanced_edge_detection, multi_scale_edges
from .mask_utils import (
    close_small_gaps,
    curvature_adaptive_simplify,
    rdp_simplify,
    threshold_adaptive,
)
from .smoothing import catmull_rom_to_beziers, chaikin_smooth


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
    if mode not in ["basic", "perfect", "enhanced"]:
        raise ValueError(f"Unknown mode: {mode}")
    try:
        if mode == "basic":
            result = _detect_polygons_basic(image, **kwargs)
        elif mode == "perfect":
            result = _detect_polygons_perfect(image, **kwargs)
        else:
            result = _detect_polygons_enhanced(image, **kwargs)

        feedback = {
            "status": "ok",
            "message": f"Detected {len(result)} polygons in mode {mode}",
            "mode": mode,
            "polygon_count": len(result),
        }
        return DetectResult(result, feedback)
    except Exception as e:
        logger.error(f"Error in detect_polygons: {e}")
        raise


def _detect_polygons_basic(image: np.ndarray, **kwargs: Any) -> List[Dict[str, Any]]:
    """Basic polygon detection."""
    downscale = float(kwargs.get("downscale", 1.0))
    canny_threshold1 = int(kwargs.get("canny_threshold1", 100))
    canny_threshold2 = int(kwargs.get("canny_threshold2", 200))
    rdp_epsilon = float(kwargs.get("rdp_epsilon", 2.0))
    min_area = float(kwargs.get("min_area", 100.0))

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    if downscale != 1.0:
        height, width = gray.shape
        new_width = int(width * downscale)
        new_height = int(height * downscale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_polygons = []

    for contour in contours:
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
        if downscale != 1.0:
            scale_factor = 1.0 / downscale
            result_points = [
                (int(px * scale_factor), int(py * scale_factor))
                for px, py in simplified_points
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
            }
        )

    return detected_polygons


def _detect_polygons_perfect(image: np.ndarray, **kwargs: Any) -> List[Dict[str, Any]]:
    """Perfect polygon detection."""
    downscale = float(kwargs.get("downscale", 1.0))
    base_eps = float(kwargs.get("base_eps", 2.0))
    curvature_factor = float(kwargs.get("curvature_factor", 1.0))
    min_area = float(kwargs.get("min_area", 100.0))
    decompose_convex = bool(kwargs.get("decompose_convex", False))
    watershed_distance = int(kwargs.get("watershed_distance", 10))
    fg_bg_threshold = int(kwargs.get("fg_bg_threshold", 200))
    mean_threshold = int(kwargs.get("mean_threshold", 150))

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    orig_height, orig_width = gray.shape

    if downscale != 1.0:
        height, width = gray.shape
        new_width = int(width * downscale)
        new_height = int(height * downscale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    # Use explicit casting for numpy operations to satisfy mypy
    gray_float = gray.astype(np.float32)
    has_clear_fg_bg = (
        gray.max() >= fg_bg_threshold and np.mean(gray_float) < mean_threshold
    )
    small_image = (orig_width * orig_height) <= 40000

    mask: np.ndarray
    if has_clear_fg_bg:
        _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    elif small_image:
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        edge_response = multi_scale_edges(
            gray, scales=[1.0, 2.0, 4.0], weights=[0.5, 0.3, 0.2]
        )
        mask = threshold_adaptive(edge_response.astype(np.uint8), block_size=11, C=2)

    mask = close_small_gaps(mask, kernel_size=3)

    separated_mask: np.ndarray
    if not small_image:
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
            # curvature_adaptive_simplify expects Sequence[Any] (the contour)
            simplified_points_int = curvature_adaptive_simplify(
                cast(Sequence[Any], contour),
                base_eps=base_eps,
                curvature_factor=curvature_factor,
            )

        if len(simplified_points_int) < 3:
            continue

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
                "quality_metrics": {
                    "vertex_count": len(polygon_points),
                    "circularity": float(circularity),
                    "convexity": float(convexity),
                    "perimeter": float(perimeter),
                },
            }
        )

    return detected_polygons


def _detect_polygons_enhanced(image: np.ndarray, **kwargs: Any) -> List[Dict[str, Any]]:
    """Enhanced polygon detection."""
    # Simplified for brevity, follows similar pattern of fixing types
    downscale = float(kwargs.get("downscale", 1.0))
    canny_thresh1 = int(kwargs.get("canny_thresh1", 50))
    canny_thresh2 = int(kwargs.get("canny_thresh2", 150))
    min_area = float(kwargs.get("min_area", 50.0))
    chaikin_iterations = int(kwargs.get("chaikin_iterations", 0))
    fit_bezier = bool(kwargs.get("fit_bezier", False))
    detect_holes = bool(kwargs.get("detect_holes", False))
    filled_shapes_threshold = int(kwargs.get("filled_shapes_threshold", 3))

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    if downscale != 1.0:
        height, width = gray.shape
        new_width = int(width * downscale)
        new_height = int(height * downscale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    unique_vals = np.unique(gray)
    has_filled_shapes = (
        len(unique_vals) <= filled_shapes_threshold and 255 in unique_vals
    )

    mask: np.ndarray
    if has_filled_shapes:
        _, mask = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    else:
        mask = enhanced_edge_detection(gray, canny_thresh1, canny_thresh2)

    retr_mode = cv2.RETR_CCOMP if detect_holes else cv2.RETR_EXTERNAL
    contours, hierarchy = cv2.findContours(mask, retr_mode, cv2.CHAIN_APPROX_NONE)

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

        points_float = [
            (float(x), float(y))
            for x, y in np.asarray(contour, dtype=np.float32).reshape(-1, 2).tolist()
        ]

        if chaikin_iterations > 0:
            points_float = chaikin_smooth(points_float, iterations=chaikin_iterations)

        polygon_points_float: List[Tuple[float, float]] = points_float
        bezier_segments = None
        if fit_bezier:
            try:
                bezier_segments = catmull_rom_to_beziers(points_float, closed=True)
            except Exception:
                pass

        polygon_points_int = [(int(px), int(py)) for px, py in polygon_points_float]

        if len(polygon_points_int) < 3:
            continue

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
