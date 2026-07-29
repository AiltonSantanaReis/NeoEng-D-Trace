"""Pure-numpy/OpenCV engine for the precise magnetic lasso.

This module deliberately has no Qt dependency.  It can be tested headlessly and
is kept separate from the UI adapter in :mod:`src.tools.magnetic_lasso`.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

Point = Tuple[int, int]


@dataclass
class MagneticLassoSettings:
    """Mutable preferences shared by magnetic-lasso tool instances."""

    mode: str = "precise"  # "precise" or "legacy"
    preset: str = "balanced"  # "fast", "balanced" or "precise"
    sensitivity: float = 1.0
    snap_radius: int = 10
    search_margin: int = 64
    edge_weight: float = 8.0
    direction_weight: float = 2.3
    turn_weight: float = 0.8
    distance_weight: float = 0.35
    simplify_epsilon: float = 1.35
    preview_interval_ms: int = 45
    max_search_pixels: int = 120_000
    max_expansions: int = 350_000
    max_vertices: int = 1_200
    close_radius_screen: float = 11.0
    show_edge_map: bool = False

    def apply_preset(self, preset: str) -> None:
        """Apply a named preset without changing the selected mode."""
        preset = str(preset).lower().strip()
        values = preset_values(preset)
        self.preset = preset
        for name, value in values.items():
            setattr(self, name, value)

    def normalized(self) -> "MagneticLassoSettings":
        """Return a validated copy suitable for numerical routines."""
        mode = self.mode if self.mode in {"legacy", "precise"} else "precise"
        preset = (
            self.preset
            if self.preset in {"fast", "balanced", "precise"}
            else "balanced"
        )
        return replace(
            self,
            mode=mode,
            preset=preset,
            sensitivity=max(0.25, min(float(self.sensitivity), 3.0)),
            snap_radius=max(0, min(int(self.snap_radius), 64)),
            search_margin=max(8, min(int(self.search_margin), 512)),
            edge_weight=max(0.0, min(float(self.edge_weight), 50.0)),
            direction_weight=max(0.0, min(float(self.direction_weight), 20.0)),
            turn_weight=max(0.0, min(float(self.turn_weight), 20.0)),
            distance_weight=max(0.01, min(float(self.distance_weight), 10.0)),
            simplify_epsilon=max(0.0, min(float(self.simplify_epsilon), 20.0)),
            preview_interval_ms=max(0, min(int(self.preview_interval_ms), 500)),
            max_search_pixels=max(4_096, min(int(self.max_search_pixels), 2_000_000)),
            max_expansions=max(10_000, min(int(self.max_expansions), 5_000_000)),
            max_vertices=max(16, min(int(self.max_vertices), 20_000)),
            close_radius_screen=max(3.0, min(float(self.close_radius_screen), 64.0)),
        )


def preset_values(preset: str) -> Dict[str, object]:
    presets: Dict[str, Dict[str, object]] = {
        "fast": {
            "sensitivity": 0.9,
            "snap_radius": 8,
            "search_margin": 42,
            "edge_weight": 6.5,
            "direction_weight": 1.5,
            "turn_weight": 0.45,
            "distance_weight": 0.48,
            "simplify_epsilon": 2.0,
            "preview_interval_ms": 65,
            "max_search_pixels": 65_000,
            "max_expansions": 160_000,
            "max_vertices": 700,
        },
        "balanced": {
            "sensitivity": 1.0,
            "snap_radius": 10,
            "search_margin": 64,
            "edge_weight": 8.0,
            "direction_weight": 2.3,
            "turn_weight": 0.8,
            "distance_weight": 0.35,
            "simplify_epsilon": 1.35,
            "preview_interval_ms": 45,
            "max_search_pixels": 120_000,
            "max_expansions": 350_000,
            "max_vertices": 1_200,
        },
        "precise": {
            "sensitivity": 1.15,
            "snap_radius": 14,
            "search_margin": 96,
            "edge_weight": 10.0,
            "direction_weight": 3.2,
            "turn_weight": 1.1,
            "distance_weight": 0.25,
            "simplify_epsilon": 0.75,
            "preview_interval_ms": 55,
            "max_search_pixels": 220_000,
            "max_expansions": 700_000,
            "max_vertices": 2_000,
        },
    }
    if preset not in presets:
        raise ValueError(f"Unknown magnetic-lasso preset: {preset}")
    return dict(presets[preset])


@dataclass(frozen=True)
class EdgeFeatures:
    strength: np.ndarray  # uint8, 0..255
    grad_x: np.ndarray  # float32, normalized -1..1
    grad_y: np.ndarray  # float32, normalized -1..1


def image_array_to_gray_uint8(
    image: np.ndarray,
    *,
    channel_order: str = "rgb",
) -> np.ndarray:
    """Convert a numpy image to contiguous 8-bit grayscale.

    ``cv2.imread`` returns BGR/BGRA arrays, while image-oriented APIs commonly
    expose RGB/RGBA.  Requiring the caller to state the channel order prevents
    silent red/blue inversions and makes the UI adapter compatible with the real
    image-loading pipeline.
    """
    arr = np.asarray(image)
    if arr.size == 0:
        raise ValueError("image array is empty")

    if arr.ndim == 3 and arr.shape[2] == 1:
        arr = arr[:, :, 0]
    elif arr.ndim == 3:
        channels = int(arr.shape[2])
        order = str(channel_order).lower().strip()
        if order not in {"rgb", "bgr"}:
            raise ValueError("channel_order must be 'rgb' or 'bgr'")
        if channels == 3:
            code = cv2.COLOR_RGB2GRAY if order == "rgb" else cv2.COLOR_BGR2GRAY
            arr = cv2.cvtColor(np.ascontiguousarray(arr), code)
        elif channels == 4:
            code = cv2.COLOR_RGBA2GRAY if order == "rgb" else cv2.COLOR_BGRA2GRAY
            arr = cv2.cvtColor(np.ascontiguousarray(arr), code)
        else:
            raise ValueError("image array must have 1, 3 or 4 channels")

    if arr.ndim != 2:
        raise ValueError("image must be a 2D grayscale or RGB/RGBA array")

    if arr.dtype != np.uint8:
        arr_float = arr.astype(np.float32)
        finite = arr_float[np.isfinite(arr_float)]
        if finite.size == 0:
            return np.zeros(arr.shape, dtype=np.uint8)
        lo = float(finite.min())
        hi = float(finite.max())
        if hi <= lo:
            value = int(np.clip(lo, 0.0, 255.0))
            return np.full(arr.shape, value, dtype=np.uint8)
        arr = np.nan_to_num(arr_float, nan=lo, posinf=hi, neginf=lo)
        arr = np.clip((arr - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)

    return np.ascontiguousarray(arr, dtype=np.uint8)


def _as_gray_uint8(image: np.ndarray) -> np.ndarray:
    """Internal RGB/RGBA conversion retained for the public engine API."""
    return image_array_to_gray_uint8(image, channel_order="rgb")


def build_edge_features(
    image: np.ndarray,
    sensitivity: float = 1.0,
) -> EdgeFeatures:
    """Build a robust edge-strength and gradient-direction representation."""
    gray = _as_gray_uint8(image)
    sensitivity = max(0.25, min(float(sensitivity), 3.0))

    # A small blur suppresses pixel noise without erasing sprite contours.
    blurred = cv2.GaussianBlur(gray, (3, 3), 0.8)
    gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)

    positive = magnitude[magnitude > 0]
    scale = float(np.percentile(positive, 98.5)) if positive.size else 1.0
    scale = max(scale / sensitivity, 1e-6)
    sobel = np.clip(magnitude * (255.0 / scale), 0.0, 255.0).astype(np.uint8)

    median = float(np.median(blurred))
    low = int(max(0.0, (0.66 / sensitivity) * median))
    high = int(min(255.0, (1.33 / max(sensitivity, 1e-6)) * median + 24.0))
    if high <= low:
        high = min(255, low + 32)
    canny = cv2.Canny(blurred, low, high)

    # Sobel gives a graded attraction field; Canny stabilizes the edge centreline.
    strength = cv2.addWeighted(sobel, 0.78, canny, 0.22, 0.0)
    strength = cv2.GaussianBlur(strength, (3, 3), 0.55)

    norm = np.maximum(magnitude, 1e-6)
    grad_x = (gx / norm).astype(np.float32)
    grad_y = (gy / norm).astype(np.float32)
    grad_x[magnitude < 1e-5] = 0.0
    grad_y[magnitude < 1e-5] = 0.0

    return EdgeFeatures(
        strength=np.ascontiguousarray(strength, dtype=np.uint8),
        grad_x=np.ascontiguousarray(grad_x, dtype=np.float32),
        grad_y=np.ascontiguousarray(grad_y, dtype=np.float32),
    )


def clamp_point(point: Sequence[float], shape: Tuple[int, int]) -> Point:
    height, width = shape
    if width <= 0 or height <= 0:
        return 0, 0
    x = max(0, min(width - 1, int(round(float(point[0])))))
    y = max(0, min(height - 1, int(round(float(point[1])))))
    return x, y


def snap_to_edge(
    edge_strength: np.ndarray,
    point: Sequence[float],
    radius: int = 10,
    minimum_strength: int = 12,
) -> Point:
    """Snap a point to the best nearby edge, balancing strength and distance."""
    edge = np.asarray(edge_strength)
    if edge.ndim != 2 or edge.size == 0:
        return int(round(float(point[0]))), int(round(float(point[1])))

    x, y = clamp_point(point, edge.shape)
    radius = max(0, int(radius))
    if radius == 0:
        return x, y

    y0, y1 = max(0, y - radius), min(edge.shape[0], y + radius + 1)
    x0, x1 = max(0, x - radius), min(edge.shape[1], x + radius + 1)
    patch = edge[y0:y1, x0:x1].astype(np.float32)
    if patch.size == 0 or float(patch.max()) < float(minimum_strength):
        return x, y

    yy, xx = np.mgrid[y0:y1, x0:x1]
    distance = np.hypot(xx - x, yy - y)
    valid = distance <= radius
    # Keep strong edges attractive, but do not jump unnecessarily across the image.
    score = patch - distance * (255.0 / max(1.0, radius * 3.2))
    score[~valid] = -np.inf
    flat_index = int(np.argmax(score))
    py, px = np.unravel_index(flat_index, score.shape)
    return int(x0 + px), int(y0 + py)


_DIRECTIONS: Tuple[Tuple[int, int], ...] = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)
_DIRECTION_LENGTHS = tuple(math.hypot(dx, dy) for dx, dy in _DIRECTIONS)
_DIRECTION_UNITS = tuple(
    (dx / length, dy / length)
    for (dx, dy), length in zip(_DIRECTIONS, _DIRECTION_LENGTHS)
)


def _search_bounds(
    start: Point,
    end: Point,
    shape: Tuple[int, int],
    settings: MagneticLassoSettings,
) -> Tuple[int, int, int, int]:
    height, width = shape
    distance = math.hypot(end[0] - start[0], end[1] - start[1])
    margin = max(settings.search_margin, int(distance * 0.38))
    margin = min(margin, 240)
    x0 = max(0, min(start[0], end[0]) - margin)
    x1 = min(width - 1, max(start[0], end[0]) + margin)
    y0 = max(0, min(start[1], end[1]) - margin)
    y1 = min(height - 1, max(start[1], end[1]) + margin)
    return x0, y0, x1, y1


def _downscale_roi(
    strength: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    start: Point,
    end: Point,
    max_pixels: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Point, Point, float]:
    pixels = int(strength.shape[0] * strength.shape[1])
    if pixels <= max_pixels:
        return strength, gx, gy, start, end, 1.0

    scale = math.sqrt(float(max_pixels) / float(max(1, pixels)))
    scale = max(0.18, min(1.0, scale))
    new_w = max(2, int(round(strength.shape[1] * scale)))
    new_h = max(2, int(round(strength.shape[0] * scale)))
    strength_small = cv2.resize(strength, (new_w, new_h), interpolation=cv2.INTER_AREA)
    gx_small = cv2.resize(gx, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    gy_small = cv2.resize(gy, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    start_small = clamp_point(
        (start[0] * scale, start[1] * scale), strength_small.shape
    )
    end_small = clamp_point((end[0] * scale, end[1] * scale), strength_small.shape)
    return strength_small, gx_small, gy_small, start_small, end_small, scale


def _astar_directional(
    strength: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    start: Point,
    end: Point,
    settings: MagneticLassoSettings,
) -> List[Point]:
    if start == end:
        return [start]

    height, width = strength.shape
    start = clamp_point(start, strength.shape)
    end = clamp_point(end, strength.shape)
    start_state = (start[0], start[1], 8)  # 8 means no previous direction.

    queue: List[Tuple[float, float, int, int, int]] = []
    heapq.heappush(queue, (0.0, 0.0, start[0], start[1], 8))
    best: Dict[Tuple[int, int, int], float] = {start_state: 0.0}
    parent: Dict[Tuple[int, int, int], Optional[Tuple[int, int, int]]] = {
        start_state: None
    }
    final_state: Optional[Tuple[int, int, int]] = None
    expansions = 0

    while queue and expansions < settings.max_expansions:
        _, current_g, x, y, previous_direction = heapq.heappop(queue)
        state = (x, y, previous_direction)
        if current_g > best.get(state, float("inf")) + 1e-9:
            continue
        expansions += 1
        if (x, y) == end:
            final_state = state
            break

        for direction_index, ((dx, dy), move_length, move_unit) in enumerate(
            zip(_DIRECTIONS, _DIRECTION_LENGTHS, _DIRECTION_UNITS)
        ):
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue

            edge_norm = float(strength[ny, nx]) / 255.0
            edge_cost = ((1.0 - edge_norm) ** 2) * settings.edge_weight

            gradient_x = float(gx[ny, nx])
            gradient_y = float(gy[ny, nx])
            # A contour direction is perpendicular to its gradient.  Moving across
            # the gradient is therefore penalized.
            across_gradient = abs(move_unit[0] * gradient_x + move_unit[1] * gradient_y)
            direction_cost = across_gradient * settings.direction_weight

            turn_cost = 0.0
            if previous_direction < 8:
                prev_unit = _DIRECTION_UNITS[previous_direction]
                alignment = max(
                    -1.0,
                    min(1.0, prev_unit[0] * move_unit[0] + prev_unit[1] * move_unit[1]),
                )
                turn_cost = (1.0 - alignment) * settings.turn_weight

            step_cost = (
                0.05 * move_length
                + settings.distance_weight * move_length
                + edge_cost
                + direction_cost
                + turn_cost
            )
            new_g = current_g + step_cost
            next_state = (nx, ny, direction_index)
            if new_g + 1e-9 >= best.get(next_state, float("inf")):
                continue

            best[next_state] = new_g
            parent[next_state] = state
            remaining = math.hypot(end[0] - nx, end[1] - ny)
            heuristic = remaining * 0.05
            heapq.heappush(queue, (new_g + heuristic, new_g, nx, ny, direction_index))

    if final_state is None:
        candidates = [
            (cost, state)
            for state, cost in best.items()
            if state[0] == end[0] and state[1] == end[1]
        ]
        if candidates:
            final_state = min(candidates, key=lambda item: item[0])[1]
        else:
            return []

    reversed_path: List[Point] = []
    current: Optional[Tuple[int, int, int]] = final_state
    while current is not None:
        point = (current[0], current[1])
        if not reversed_path or reversed_path[-1] != point:
            reversed_path.append(point)
        current = parent.get(current)
    reversed_path.reverse()
    return reversed_path


def _astar_preview(
    strength: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    start: Point,
    end: Point,
    settings: MagneticLassoSettings,
) -> List[Point]:
    """Fast single-state A* used only for interactive previews.

    The committed precise segment still uses :func:`_astar_directional`.  This
    preview variant intentionally omits previous-direction state and turn cost,
    reducing the state space by roughly a factor of eight while preserving edge
    strength and gradient-direction attraction.
    """
    if start == end:
        return [start]

    height, width = strength.shape
    start = clamp_point(start, strength.shape)
    end = clamp_point(end, strength.shape)

    queue: List[Tuple[float, float, int, int]] = [(0.0, 0.0, start[0], start[1])]
    best = np.full((height, width), np.inf, dtype=np.float64)
    parent = np.full((height, width, 2), -1, dtype=np.int32)
    best[start[1], start[0]] = 0.0
    expansions = 0

    while queue and expansions < settings.max_expansions:
        _, current_g, x, y = heapq.heappop(queue)
        if current_g > float(best[y, x]) + 1e-9:
            continue
        expansions += 1
        if (x, y) == end:
            break

        for (dx, dy), move_length, move_unit in zip(
            _DIRECTIONS, _DIRECTION_LENGTHS, _DIRECTION_UNITS
        ):
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue

            edge_norm = float(strength[ny, nx]) / 255.0
            edge_cost = ((1.0 - edge_norm) ** 2) * settings.edge_weight
            across_gradient = abs(
                move_unit[0] * float(gx[ny, nx]) + move_unit[1] * float(gy[ny, nx])
            )
            direction_cost = across_gradient * settings.direction_weight
            step_cost = (
                0.05 * move_length
                + settings.distance_weight * move_length
                + edge_cost
                + direction_cost
            )
            new_g = current_g + step_cost
            if new_g + 1e-9 >= float(best[ny, nx]):
                continue

            best[ny, nx] = new_g
            parent[ny, nx] = (x, y)
            remaining = math.hypot(end[0] - nx, end[1] - ny)
            heapq.heappush(
                queue,
                (new_g + remaining * 0.05, new_g, nx, ny),
            )

    if not np.isfinite(best[end[1], end[0]]):
        return []

    reversed_path: List[Point] = []
    x, y = end
    while x >= 0 and y >= 0:
        reversed_path.append((x, y))
        parent_x, parent_y = parent[y, x]
        x, y = int(parent_x), int(parent_y)
    reversed_path.reverse()
    return reversed_path


def live_wire_preview_path(
    features: EdgeFeatures,
    start: Sequence[float],
    end: Sequence[float],
    settings: Optional[MagneticLassoSettings] = None,
) -> List[Point]:
    """Calculate a bounded, responsive preview without changing final quality.

    This function is for cursor-following feedback only.  A committed segment
    must still be calculated with :func:`live_wire_path`.
    """
    settings = (settings or MagneticLassoSettings()).normalized()
    shape = features.strength.shape
    start_global = clamp_point(start, shape)
    end_global = clamp_point(end, shape)
    if start_global == end_global:
        return [start_global]

    x0, y0, x1, y1 = _search_bounds(start_global, end_global, shape, settings)
    strength_roi = features.strength[y0 : y1 + 1, x0 : x1 + 1]
    gx_roi = features.grad_x[y0 : y1 + 1, x0 : x1 + 1]
    gy_roi = features.grad_y[y0 : y1 + 1, x0 : x1 + 1]
    start_local = (start_global[0] - x0, start_global[1] - y0)
    end_local = (end_global[0] - x0, end_global[1] - y0)

    strength_search, gx_search, gy_search, start_search, end_search, scale = (
        _downscale_roi(
            strength_roi,
            gx_roi,
            gy_roi,
            start_local,
            end_local,
            settings.max_search_pixels,
        )
    )
    path = _astar_preview(
        strength_search,
        gx_search,
        gy_search,
        start_search,
        end_search,
        settings,
    )
    if not path:
        return []

    if scale != 1.0:
        mapped: List[Point] = []
        refinement_radius = max(1, min(5, int(math.ceil(1.5 / scale))))
        for px, py in path:
            local_x = int(round(px / scale))
            local_y = int(round(py / scale))
            global_point = clamp_point((local_x + x0, local_y + y0), shape)
            global_point = snap_to_edge(
                features.strength,
                global_point,
                radius=refinement_radius,
                minimum_strength=8,
            )
            if not mapped or mapped[-1] != global_point:
                mapped.append(global_point)
        path = mapped
    else:
        path = [(px + x0, py + y0) for px, py in path]

    if path:
        path[0] = start_global
        path[-1] = end_global
    return path


def live_wire_path(
    features: EdgeFeatures,
    start: Sequence[float],
    end: Sequence[float],
    settings: Optional[MagneticLassoSettings] = None,
) -> List[Point]:
    """Calculate a direction-aware edge-following path between two anchors."""
    settings = (settings or MagneticLassoSettings()).normalized()
    shape = features.strength.shape
    start_global = clamp_point(start, shape)
    end_global = clamp_point(end, shape)
    if start_global == end_global:
        return [start_global]

    x0, y0, x1, y1 = _search_bounds(start_global, end_global, shape, settings)
    strength_roi = features.strength[y0 : y1 + 1, x0 : x1 + 1]
    gx_roi = features.grad_x[y0 : y1 + 1, x0 : x1 + 1]
    gy_roi = features.grad_y[y0 : y1 + 1, x0 : x1 + 1]
    start_local = (start_global[0] - x0, start_global[1] - y0)
    end_local = (end_global[0] - x0, end_global[1] - y0)

    strength_search, gx_search, gy_search, start_search, end_search, scale = (
        _downscale_roi(
            strength_roi,
            gx_roi,
            gy_roi,
            start_local,
            end_local,
            settings.max_search_pixels,
        )
    )
    path = _astar_directional(
        strength_search,
        gx_search,
        gy_search,
        start_search,
        end_search,
        settings,
    )
    if not path:
        return []

    if scale != 1.0:
        mapped: List[Point] = []
        refinement_radius = max(1, min(5, int(math.ceil(1.5 / scale))))
        for px, py in path:
            local_x = int(round(px / scale))
            local_y = int(round(py / scale))
            global_point = clamp_point((local_x + x0, local_y + y0), shape)
            global_point = snap_to_edge(
                features.strength,
                global_point,
                radius=refinement_radius,
                minimum_strength=8,
            )
            if not mapped or mapped[-1] != global_point:
                mapped.append(global_point)
        path = mapped
    else:
        path = [(px + x0, py + y0) for px, py in path]

    if path:
        path[0] = start_global
        path[-1] = end_global
    return path


def deduplicate_path(points: Iterable[Sequence[float]]) -> List[Point]:
    result: List[Point] = []
    for point in points:
        current = (int(round(float(point[0]))), int(round(float(point[1]))))
        if not result or current != result[-1]:
            result.append(current)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    return result


def simplify_closed_path(
    points: Sequence[Sequence[float]],
    epsilon: float = 1.35,
    max_vertices: int = 1_200,
) -> List[Point]:
    """Simplify a closed contour while keeping a valid editable polygon."""
    clean = deduplicate_path(points)
    if len(clean) < 3:
        return clean

    contour = np.asarray(clean, dtype=np.float32).reshape((-1, 1, 2))
    epsilon = max(0.0, float(epsilon))
    simplified = cv2.approxPolyDP(contour, epsilon, True).reshape((-1, 2))

    max_vertices = max(3, int(max_vertices))
    adaptive_epsilon = max(epsilon, 0.25)
    while len(simplified) > max_vertices and adaptive_epsilon < 64.0:
        adaptive_epsilon *= 1.35
        simplified = cv2.approxPolyDP(contour, adaptive_epsilon, True).reshape((-1, 2))

    result = deduplicate_path(simplified.tolist())
    return result if len(result) >= 3 else clean


def _orientation(a: Point, b: Point, c: Point) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(value) < 1e-9:
        return 0
    return 1 if value > 0 else 2


def _on_segment(a: Point, b: Point, c: Point) -> bool:
    return min(a[0], c[0]) <= b[0] <= max(a[0], c[0]) and min(a[1], c[1]) <= b[
        1
    ] <= max(a[1], c[1])


def _segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(a, c, b):
        return True
    if o2 == 0 and _on_segment(a, d, b):
        return True
    if o3 == 0 and _on_segment(c, a, d):
        return True
    if o4 == 0 and _on_segment(c, b, d):
        return True
    return False


def polygon_self_intersects(points: Sequence[Sequence[float]]) -> bool:
    polygon = deduplicate_path(points)
    count = len(polygon)
    if count < 4:
        return False
    for first in range(count):
        a, b = polygon[first], polygon[(first + 1) % count]
        for second in range(first + 1, count):
            # Adjacent edges share a vertex by design.
            if second in {first, (first + 1) % count, (first - 1) % count}:
                continue
            if first == 0 and second == count - 1:
                continue
            c, d = polygon[second], polygon[(second + 1) % count]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def polygon_signed_area(points: Sequence[Sequence[float]]) -> float:
    """Return the signed shoelace area of a closed polygon path."""
    polygon = deduplicate_path(points)
    if len(polygon) < 3:
        return 0.0
    area = 0.0
    for index, current in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        area += float(current[0]) * float(following[1])
        area -= float(following[0]) * float(current[1])
    return area * 0.5


def _remove_collinear_and_backtracking(
    points: Sequence[Sequence[float]],
) -> List[Point]:
    """Remove redundant collinear vertices, including immediate edge backtracking.

    Live-wire paths are pixel chains.  When two independently calculated
    segments meet, the chain can contain short A-B-A spikes or overlapping
    collinear steps.  Those are not meaningful polygon vertices and Shapely
    correctly rejects some of them as an invalid ring.
    """
    clean = deduplicate_path(points)
    if len(clean) < 3:
        return clean

    # Iteration is bounded because every successful pass removes vertices.
    changed = True
    while changed and len(clean) >= 3:
        changed = False
        result: List[Point] = []
        count = len(clean)
        for index, current in enumerate(clean):
            previous = clean[index - 1]
            following = clean[(index + 1) % count]
            if current == previous or current == following:
                changed = True
                continue
            ax = current[0] - previous[0]
            ay = current[1] - previous[1]
            bx = following[0] - current[0]
            by = following[1] - current[1]
            cross = ax * by - ay * bx
            if cross == 0 and count - 1 >= 3:
                # This covers both ordinary collinearity and a local reversal.
                changed = True
                continue
            result.append(current)
        next_clean = deduplicate_path(result)
        if len(next_clean) < 3:
            return next_clean
        clean = next_clean
    return clean


def sanitize_closed_polygon(
    points: Sequence[Sequence[float]],
    epsilon: float = 1.35,
    max_vertices: int = 1_200,
    minimum_area: float = 1.0,
) -> List[Point]:
    """Prepare a live-wire contour for the strict Scene polygon contract.

    The operation is deterministic and limited to representation cleanup:
    consecutive duplicates, closing duplicates, collinear runs and immediate
    backtracking are removed.  Self-intersections are never repaired silently.
    """
    clean = _remove_collinear_and_backtracking(points)
    if len(clean) < 3:
        return []

    clean = simplify_closed_path(clean, epsilon=epsilon, max_vertices=max_vertices)
    clean = _remove_collinear_and_backtracking(clean)
    if len(clean) < 3:
        return []
    if abs(polygon_signed_area(clean)) < max(0.0, float(minimum_area)):
        return []
    if polygon_self_intersects(clean):
        return []

    # Scene normalizes winding too, but returning a consistent CCW ring makes
    # the tool result stable for direct consumers and tests.
    if polygon_signed_area(clean) < 0.0:
        clean = list(reversed(clean))
    return clean


def path_edge_adherence(
    path: Sequence[Sequence[float]], edge_strength: np.ndarray
) -> float:
    """Return the mean normalized edge strength sampled by a path."""
    if not path:
        return 0.0
    edge = np.asarray(edge_strength)
    if edge.ndim != 2 or edge.size == 0:
        return 0.0
    values = []
    for point in path:
        x, y = clamp_point(point, edge.shape)
        values.append(float(edge[y, x]) / 255.0)
    return float(np.mean(values)) if values else 0.0
