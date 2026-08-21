# src/tools/magnetic_lasso.py
"""Magnetic-lasso UI tool with preserved legacy and precise modes."""

from __future__ import annotations

import hashlib
import math
import time
import weakref
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PySide6.QtCore import QObject, QPointF, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import (
    QActionGroup,
    QColor,
    QCursor,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QMenu, QMessageBox, QWidget

from .base_tool import BaseTool
from .edge_utils import normalize_array, sobel_magnitude
from .magnetic_lasso_engine import (
    EdgeFeatures,
    MagneticLassoSettings,
    build_edge_features,
    deduplicate_path,
    image_array_to_gray_uint8,
    live_wire_path,
    live_wire_preview_path,
    polygon_self_intersects,
    sanitize_closed_polygon,
    snap_to_edge,
)

Point = Tuple[int, int]


# A module-lifetime pool prevents tool switching from blocking while a stale
# calculation finishes. Requests remain serialized to avoid CPU saturation.
_MAGNETIC_PATH_POOL = QThreadPool()
_MAGNETIC_PATH_POOL.setMaxThreadCount(1)


def sobel_edge_detection(image_array):
    """Historical public helper retained for compatibility."""
    mag = sobel_magnitude(image_array)
    return normalize_array(mag)


def dijkstra_pathfinding(edge_map, start, end):
    """Historical pathfinder retained unchanged for Legacy mode."""
    h, w = edge_map.shape
    sx, sy = int(round(start[0])), int(round(start[1]))
    ex, ey = int(round(end[0])), int(round(end[1]))

    pad = 20
    min_x = max(0, min(sx, ex) - pad)
    max_x = min(w - 1, max(sx, ex) + pad)
    min_y = max(0, min(sy, ey) - pad)
    max_y = min(h - 1, max(sy, ey) + pad)

    sub = edge_map[min_y : max_y + 1, min_x : max_x + 1]
    cost_map = 255 - sub.astype(np.int32) + 1

    import heapq

    start_local = (sx - min_x, sy - min_y)
    end_local = (ex - min_x, ey - min_y)

    open_set: List[Tuple[float, float, Tuple[int, int]]] = []
    g_score = {start_local: 0.0}
    heapq.heappush(open_set, (0.0, 0.0, start_local))
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start_local: None}

    max_x_local = max_x - min_x
    max_y_local = max_y - min_y

    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        if current == end_local:
            break

        cx, cy = current
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = cx + dx, cy + dy
                if nx < 0 or ny < 0 or nx > max_x_local or ny > max_y_local:
                    continue

                neighbor = (nx, ny)
                move_cost = math.hypot(dx, dy)
                pixel_cost = float(cost_map[ny, nx])
                tentative_g = current_g + pixel_cost + move_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    h_score = math.hypot(end_local[0] - nx, end_local[1] - ny)
                    f_score = tentative_g + h_score
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
                    came_from[neighbor] = current

    if end_local not in came_from:
        return []

    path = []
    cursor: Optional[Tuple[int, int]] = end_local
    while cursor is not None:
        path.append((cursor[0] + min_x, cursor[1] + min_y))
        cursor = came_from[cursor]
    path.reverse()
    return path


class _MagneticPathSignals(QObject):
    """Thread-safe result channel for a single path request."""

    completed = Signal(object)


class _MagneticPathWorker(QRunnable):
    """Run the expensive path search outside the Qt GUI thread."""

    def __init__(
        self,
        request_id: int,
        revision: int,
        purpose: str,
        mode: str,
        edge_map: Optional[np.ndarray],
        edge_features: Optional[EdgeFeatures],
        image_array: Optional[np.ndarray],
        image_token,
        settings: MagneticLassoSettings,
        start: Point,
        end: Point,
    ):
        super().__init__()
        self.request_id = request_id
        self.revision = revision
        self.purpose = purpose
        self.mode = mode
        self.edge_map = edge_map
        self.edge_features = edge_features
        self.image_array = image_array
        self.image_token = image_token
        self.settings = settings
        self.start = start
        self.end = end
        self.signals = _MagneticPathSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        error = None
        path: List[Point] = []
        edge_map = self.edge_map
        edge_features = self.edge_features
        image_hash = None
        try:
            if edge_map is None and self.image_array is not None:
                image_hash = hashlib.sha1(
                    self.image_array.tobytes(), usedforsecurity=False
                ).hexdigest()
                if self.mode == "precise":
                    edge_features = build_edge_features(
                        self.image_array,
                        sensitivity=self.settings.sensitivity,
                    )
                    edge_map = edge_features.strength
                else:
                    edge_features = None
                    edge_map = normalize_array(sobel_magnitude(self.image_array))

            if self.purpose == "prepare":
                path = []
            elif self.mode == "legacy" and edge_map is not None:
                path = dijkstra_pathfinding(edge_map, self.start, self.end)
            elif edge_features is not None:
                solver = (
                    live_wire_preview_path
                    if self.purpose == "preview"
                    else live_wire_path
                )
                path = solver(
                    edge_features,
                    self.start,
                    self.end,
                    self.settings,
                )
        except Exception as exc:  # pragma: no cover - exercised by Qt integration tests
            error = f"{type(exc).__name__}: {exc}"
        self.signals.completed.emit(
            {
                "request_id": self.request_id,
                "revision": self.revision,
                "purpose": self.purpose,
                "start": self.start,
                "end": self.end,
                "path": path,
                "error": error,
                "mode": self.mode,
                "commit_safe": self.mode == "legacy" or self.purpose != "preview",
                "edge_map": edge_map,
                "edge_features": edge_features,
                "image_hash": image_hash,
                "image_token": self.image_token,
                "edge_signature": (
                    self.mode,
                    round(float(self.settings.sensitivity), 6),
                ),
            }
        )


class _MagneticPathBridge(QObject):
    """Ensure worker results are delivered on the GUI thread."""

    def __init__(self, owner):
        super().__init__()
        self._owner_ref = weakref.ref(owner)

    @Slot(object)
    def dispatch(self, payload):
        owner = self._owner_ref()
        if owner is not None:
            owner._on_async_path_result(payload)


class MagneticLassoTool(BaseTool):
    """Edge-guided selection tool with Legacy and Precise implementations."""

    def __init__(
        self,
        canvas_view,
        settings: Optional[MagneticLassoSettings] = None,
    ):
        super().__init__(canvas_view)
        # Direct construction keeps the historical Legacy contract.  The real
        # application passes a shared settings object whose default is Precise.
        self.settings = (
            settings if settings is not None else MagneticLassoSettings(mode="legacy")
        )
        self.settings.mode = (
            self.settings.mode
            if self.settings.mode in {"legacy", "precise"}
            else "precise"
        )

        self._anchors: List[Point] = []
        self._segments: List[List[Point]] = []
        self._path: List[Point] = []
        self._preview_path: List[Point] = []
        self._redo_anchor_stack: List[Tuple[Point, Optional[List[Point]]]] = []

        self._edge_map: Optional[np.ndarray] = None
        self._edge_features: Optional[EdgeFeatures] = None
        self._edge_overlay_image: Optional[QImage] = None
        self._last_image_hash: Optional[str] = None
        self._last_image_token = None
        self._last_preview_time = 0.0
        self._last_preview_endpoint: Optional[Point] = None
        self._hover_can_close = False
        self._last_error: Optional[str] = None
        self._preview_path_start: Optional[Point] = None
        self._preview_path_endpoint: Optional[Point] = None

        # Expensive live-wire searches are serialized outside the GUI thread.
        # Mock/non-QWidget canvases keep synchronous behavior for compatibility
        # with headless contracts and external adapters.
        self._path_pool = _MAGNETIC_PATH_POOL
        self._path_bridge = _MagneticPathBridge(self)
        self._path_workers: Dict[int, _MagneticPathWorker] = {}
        self._active_path_request: Optional[int] = None
        self._queued_preview_request: Optional[Dict[str, Any]] = None
        self._queued_action_request: Optional[Dict[str, Any]] = None
        self._next_path_request_id = 0
        self._state_revision = 0
        self._segment_pending = False
        self._path_busy = False
        self._saved_cursor: Optional[QCursor] = None

        self.current_lang = "en"
        self.translations = {
            "en": {
                "finish_selection": "Finish Selection",
                "remove_anchor": "Remove Last Anchor",
                "cancel_selection": "Cancel Selection",
                "mode": "Mode",
                "mode_precise": "Precise (recommended)",
                "mode_legacy": "Legacy",
                "preset": "Precision Preset",
                "preset_fast": "Fast",
                "preset_balanced": "Balanced",
                "preset_precise": "Precise",
                "show_edges": "Show Detected Edges",
                "undo_project": "Undo Project",
                "redo_project": "Redo Project",
                "invalid_selection": (
                    "The magnetic path could not create a valid polygon. The "
                    "anchors were preserved so you can adjust or cancel the selection."
                ),
                "title": "Magnetic Lasso",
                "path_error": (
                    "The magnetic path calculation failed. The current anchors "
                    "were preserved."
                ),
            },
            "pt": {
                "finish_selection": "Concluir Seleção",
                "remove_anchor": "Remover Última Âncora",
                "cancel_selection": "Cancelar Seleção",
                "mode": "Modo",
                "mode_precise": "Preciso (recomendado)",
                "mode_legacy": "Legado",
                "preset": "Nível de Precisão",
                "preset_fast": "Rápido",
                "preset_balanced": "Equilibrado",
                "preset_precise": "Preciso",
                "show_edges": "Mostrar Bordas Detectadas",
                "undo_project": "Desfazer no Projeto",
                "redo_project": "Refazer no Projeto",
                "invalid_selection": (
                    "O caminho magnético não conseguiu criar um polígono válido. "
                    "As âncoras foram preservadas para ajuste ou cancelamento."
                ),
                "title": "Laço Magnético",
                "path_error": (
                    "O cálculo do caminho magnético falhou. As âncoras atuais "
                    "foram preservadas."
                ),
            },
        }

    # ------------------------------------------------------------------
    # Image and edge preparation
    # ------------------------------------------------------------------

    def _get_scene_image(self):
        scene = getattr(self.canvas_view, "scene", None)
        if scene is None:
            scene = getattr(self.canvas_view, "model", None)
        if scene is None or not hasattr(scene, "get_image"):
            return None
        return scene.get_image()

    @staticmethod
    def _image_token(image):
        """Return a cheap identity token without hashing image bytes on the
        GUI thread."""
        if isinstance(image, np.ndarray):
            pointer = int(image.__array_interface__["data"][0]) if image.size else 0
            return (
                "numpy",
                id(image),
                tuple(image.shape),
                str(image.dtype),
                tuple(image.strides),
                pointer,
            )
        if isinstance(image, QImage):
            return (
                "qimage",
                int(image.cacheKey()),
                int(image.width()),
                int(image.height()),
                int(image.format().value),
            )
        return ("other", id(image), type(image).__name__) if image is not None else None

    def _current_edge_signature(self):
        settings = self.settings.normalized()
        return (settings.mode, round(float(settings.sensitivity), 6))

    def _current_image_token(self):
        return self._image_token(self._get_scene_image())

    def _invalidate_stale_edge_cache(self) -> None:
        token = self._current_image_token()
        if self._last_image_token is not None and token != self._last_image_token:
            self._clear_edge_cache()

    def _get_image_array(self) -> Optional[np.ndarray]:
        image = self._get_scene_image()
        if image is None:
            return None

        # The production image loader uses cv2.imread(IMREAD_UNCHANGED), so the
        # scene normally stores a numpy BGR/BGRA array.  Historical tests and a
        # few adapters provide QImage instead.  Both representations are valid.
        if isinstance(image, np.ndarray):
            try:
                return image_array_to_gray_uint8(image, channel_order="bgr")
            except (TypeError, ValueError) as exc:
                self._last_error = f"Unsupported numpy image: {exc}"
                return None

        if not isinstance(image, QImage):
            self._last_error = "Unsupported scene image type: " + type(image).__name__
            return None

        image = image.convertToFormat(QImage.Format.Format_Grayscale8)
        width = int(image.width())
        height = int(image.height())
        try:
            bytes_per_line = int(image.bytesPerLine())
        except (TypeError, ValueError, AttributeError):
            # Historical wrappers may expose only tightly packed bytes.
            bytes_per_line = width
        if width <= 0 or height <= 0 or bytes_per_line < width:
            self._last_error = "Invalid QImage dimensions or row stride"
            return None

        ptr = image.constBits()
        raw = np.frombuffer(ptr, dtype=np.uint8, count=height * bytes_per_line)
        rows = raw.reshape((height, bytes_per_line))
        return np.ascontiguousarray(rows[:, :width]).copy()

    def _clear_edge_cache(self) -> None:
        self._edge_map = None
        self._edge_features = None
        self._edge_overlay_image = None
        self._last_image_hash = None
        self._last_image_token = None

    def _compute_edge_map(self) -> None:
        image_array = self._get_image_array()
        if image_array is None:
            self._clear_edge_cache()
            return

        image_token = self._current_image_token()
        digest = hashlib.sha1(image_array.tobytes(), usedforsecurity=False).hexdigest()
        if (
            digest == self._last_image_hash
            and image_token == self._last_image_token
            and self._edge_map is not None
        ):
            return

        if self.settings.mode == "precise":
            self._edge_features = build_edge_features(
                image_array,
                sensitivity=self.settings.normalized().sensitivity,
            )
            self._edge_map = self._edge_features.strength
        else:
            self._edge_features = None
            self._edge_map = normalize_array(sobel_magnitude(image_array))

        self._last_image_hash = digest
        self._last_image_token = image_token
        self._edge_overlay_image = self._make_edge_overlay(self._edge_map)

    @staticmethod
    def _make_edge_overlay(edge_map: Optional[np.ndarray]) -> Optional[QImage]:
        if edge_map is None or edge_map.ndim != 2 or edge_map.size == 0:
            return None
        data = np.ascontiguousarray(edge_map, dtype=np.uint8)
        height, width = data.shape
        return QImage(
            data.data,
            width,
            height,
            int(data.strides[0]),
            QImage.Format.Format_Grayscale8,
        ).copy()

    def _snap_anchor(self, point: Sequence[float]) -> Point:
        if self.settings.mode != "precise":
            return int(round(float(point[0]))), int(round(float(point[1])))
        self._invalidate_stale_edge_cache()
        if self._edge_map is None:
            if self._uses_background_pathfinding():
                self.prepare_edge_map_async()
                return int(round(float(point[0]))), int(round(float(point[1])))
            self._compute_edge_map()
        if self._edge_map is None:
            return int(round(float(point[0]))), int(round(float(point[1])))
        return snap_to_edge(
            self._edge_map,
            point,
            radius=self.settings.normalized().snap_radius,
        )

    def _compute_magnetic_path(self, start, end) -> List[Point]:
        if self._edge_map is None:
            self._compute_edge_map()
        if self._edge_map is None:
            return []

        height, width = self._edge_map.shape
        start_int = (
            max(0, min(width - 1, int(round(start[0])))),
            max(0, min(height - 1, int(round(start[1])))),
        )
        end_int = (
            max(0, min(width - 1, int(round(end[0])))),
            max(0, min(height - 1, int(round(end[1])))),
        )
        if start_int == end_int:
            return [start_int]

        if self.settings.mode == "legacy":
            return dijkstra_pathfinding(self._edge_map, start_int, end_int)

        if self._edge_features is None:
            self._compute_edge_map()
        if self._edge_features is None:
            return []
        return live_wire_path(
            self._edge_features,
            start_int,
            end_int,
            self.settings,
        )

    def _set_path_busy(self, busy: bool) -> None:
        if not self._uses_background_pathfinding():
            return
        busy = bool(busy)
        if busy == self._path_busy:
            return
        self._path_busy = busy
        if busy:
            try:
                self._saved_cursor = QCursor(self.canvas_view.cursor())
                self.canvas_view.setCursor(Qt.CursorShape.BusyCursor)
            except Exception:
                self._saved_cursor = None
        else:
            try:
                if self._saved_cursor is not None:
                    self.canvas_view.setCursor(self._saved_cursor)
                else:
                    self.canvas_view.unsetCursor()
            except Exception:
                pass
            self._saved_cursor = None

    def prepare_edge_map_async(self) -> None:
        """Warm the edge cache without blocking the GUI thread."""
        self._invalidate_stale_edge_cache()
        if self._edge_map is not None:
            return
        if not self._uses_background_pathfinding():
            self._compute_edge_map()
            return
        if self._active_path_request is None:
            self._request_async_path("prepare", (0, 0), (0, 0))

    def _uses_background_pathfinding(self) -> bool:
        """Return True only for a real Qt canvas in the running application."""
        return isinstance(self.canvas_view, QWidget)

    def _request_async_path(self, purpose: str, start: Point, end: Point) -> None:
        request = {
            "purpose": purpose,
            "start": start,
            "end": end,
            "revision": self._state_revision,
            "image_token": self._current_image_token(),
        }
        if self._active_path_request is not None:
            if purpose in {"segment", "finish"}:
                self._queued_action_request = request
                self._queued_preview_request = None
                self._segment_pending = True
                self._set_path_busy(True)
            elif purpose == "preview" and self._queued_action_request is None:
                # Coalesce mouse-move events: only the newest preview is useful.
                self._queued_preview_request = request
            # A path request already prepares the same cache, so an additional
            # explicit prepare request is intentionally discarded.
            return
        self._start_async_path(request)

    def _start_async_path(self, request) -> None:
        if request["revision"] != self._state_revision:
            return

        self._invalidate_stale_edge_cache()
        current_token = self._current_image_token()
        image_array = None
        if self._edge_map is None or self._last_image_token != current_token:
            image_array = self._get_image_array()
            if image_array is None:
                self._handle_async_failure(request["purpose"], "Image unavailable")
                return

        settings = self.settings.normalized()
        if request["purpose"] in {"segment", "finish"}:
            self._set_path_busy(True)
        if request["purpose"] == "preview":
            # Preview must not monopolize a CPU core. Committed segments retain
            # the selected preset's full search budget.
            settings.max_search_pixels = min(settings.max_search_pixels, 45_000)
            settings.max_expansions = min(settings.max_expansions, 100_000)

        self._next_path_request_id += 1
        request_id = self._next_path_request_id
        worker = _MagneticPathWorker(
            request_id=request_id,
            revision=request["revision"],
            purpose=request["purpose"],
            mode=self.settings.mode,
            edge_map=self._edge_map,
            edge_features=self._edge_features,
            image_array=image_array,
            image_token=current_token,
            settings=settings,
            start=request["start"],
            end=request["end"],
        )
        worker.signals.completed.connect(
            self._path_bridge.dispatch,
            Qt.ConnectionType.QueuedConnection,
        )
        self._path_workers[request_id] = worker
        self._active_path_request = request_id
        self._path_pool.start(worker)

    def _start_next_async_path(self) -> None:
        request = self._queued_action_request
        self._queued_action_request = None
        if request is None:
            request = self._queued_preview_request
            self._queued_preview_request = None
        if request is not None and request["revision"] == self._state_revision:
            self._start_async_path(request)
        else:
            self._segment_pending = False
            self._set_path_busy(False)

    def _on_async_path_result(self, payload) -> None:
        request_id = int(payload.get("request_id", -1))
        self._path_workers.pop(request_id, None)
        if self._active_path_request == request_id:
            self._active_path_request = None

        image_matches = payload.get("image_token") == self._current_image_token()
        edge_matches = payload.get("edge_signature") == self._current_edge_signature()
        prepared_edge_map = payload.get("edge_map")
        if image_matches and edge_matches and prepared_edge_map is not None:
            # Edge preparation is independent from anchor history, so a result
            # remains useful when only the selection revision changed.
            self._edge_map = prepared_edge_map
            self._edge_features = payload.get("edge_features")
            self._last_image_hash = payload.get("image_hash") or self._last_image_hash
            self._last_image_token = payload.get("image_token")
            self._edge_overlay_image = self._make_edge_overlay(self._edge_map)

        if (
            payload.get("revision") != self._state_revision
            or not image_matches
            or not edge_matches
        ):
            self._start_next_async_path()
            return

        purpose = payload.get("purpose")
        start = tuple(payload.get("start", ()))
        end = tuple(payload.get("end", ()))
        path = list(payload.get("path") or [])
        error = payload.get("error")

        # Reuse a just-completed preview when the user clicked the same point
        # while that preview was still running. This avoids a duplicate search.
        queued_action = self._queued_action_request
        if (
            purpose == "preview"
            and queued_action is not None
            and queued_action["start"] == start
            and queued_action["end"] == end
            and bool(payload.get("commit_safe"))
        ):
            purpose = queued_action["purpose"]
            self._queued_action_request = None

        if error:
            self._last_error = str(error)
            if purpose in {"segment", "finish"}:
                self._handle_async_failure(purpose, str(error))
        elif purpose == "prepare":
            self.canvas_view.update()
        elif purpose == "preview":
            if self._anchors and self._anchors[-1] == start:
                self._preview_path = path
                self._preview_path_start = start
                self._preview_path_endpoint = end
                self.canvas_view.update()
        elif purpose == "segment":
            self._segment_pending = False
            self._set_path_busy(False)
            if path and self._anchors and self._anchors[-1] == start:
                self._append_anchor(end, precomputed_segment=path)
                self._preview_path = []
                self._preview_path_start = None
                self._preview_path_endpoint = None
                self._queued_preview_request = None
                self.canvas_view.update()
            elif not path:
                self._handle_async_failure(purpose, "No path returned")
        elif purpose == "finish":
            self._segment_pending = False
            self._set_path_busy(False)
            if path:
                self._finish_with_closing_path(path)
            else:
                self._handle_async_failure(purpose, "No closing path returned")

        self._start_next_async_path()

    def _handle_async_failure(self, purpose: str, detail: str) -> None:
        self._segment_pending = False
        self._set_path_busy(False)
        self._last_error = f"{purpose}: {detail}"
        if purpose in {"segment", "finish"}:
            try:
                QMessageBox.warning(
                    self.canvas_view,
                    self.translations[self.current_lang]["title"],
                    self.translations[self.current_lang]["path_error"],
                )
            except Exception:
                pass
        self.canvas_view.update()

    def _invalidate_async_requests(self) -> None:
        self._state_revision += 1
        self._queued_preview_request = None
        self._queued_action_request = None
        self._segment_pending = False
        self._set_path_busy(False)
        self._preview_path_start = None
        self._preview_path_endpoint = None

    # ------------------------------------------------------------------
    # Selection state
    # ------------------------------------------------------------------

    def _reset_selection_state(self) -> None:
        self._invalidate_async_requests()
        self._anchors.clear()
        self._segments.clear()
        self._path.clear()
        self._preview_path.clear()
        self._redo_anchor_stack.clear()
        self._last_preview_endpoint = None
        self._hover_can_close = False

    def _rebuild_path(self) -> None:
        if not self._anchors:
            self._path = []
            return
        rebuilt: List[Point] = [self._anchors[0]]
        for segment in self._segments:
            if not segment:
                continue
            if rebuilt and segment[0] == rebuilt[-1]:
                rebuilt.extend(segment[1:])
            else:
                rebuilt.extend(segment)
        self._path = deduplicate_path(rebuilt)

    def _append_anchor(
        self,
        anchor: Point,
        precomputed_segment: Optional[Sequence[Point]] = None,
    ) -> bool:
        if self._anchors and anchor == self._anchors[-1]:
            return False

        if not self._anchors:
            self._anchors.append(anchor)
            self._path = [anchor]
            self._redo_anchor_stack.clear()
            self._state_revision += 1
            return True

        segment = (
            list(precomputed_segment)
            if precomputed_segment is not None
            else self._compute_magnetic_path(self._anchors[-1], anchor)
        )
        if not segment:
            return False
        self._anchors.append(anchor)
        self._segments.append(segment)
        self._redo_anchor_stack.clear()
        self._rebuild_path()
        self._state_revision += 1
        return True

    def remove_last_anchor(self) -> bool:
        if not self._anchors:
            return False
        self._invalidate_async_requests()
        anchor = self._anchors.pop()
        segment: Optional[List[Point]] = None
        if self._segments:
            segment = self._segments.pop()
        self._redo_anchor_stack.append((anchor, list(segment) if segment else None))
        self._preview_path = []
        self._preview_path_start = None
        self._preview_path_endpoint = None
        self._rebuild_path()
        self.canvas_view.update()
        return True

    def restore_last_anchor(self) -> bool:
        if not self._redo_anchor_stack:
            return False
        self._invalidate_async_requests()
        anchor, segment = self._redo_anchor_stack.pop()
        if not self._anchors:
            self._anchors.append(anchor)
        elif segment:
            self._anchors.append(anchor)
            self._segments.append(segment)
        else:
            computed = self._compute_magnetic_path(self._anchors[-1], anchor)
            if not computed:
                self._redo_anchor_stack.append((anchor, segment))
                return False
            self._anchors.append(anchor)
            self._segments.append(computed)
        self._rebuild_path()
        self._state_revision += 1
        self.canvas_view.update()
        return True

    def _can_close_at(self, point: Sequence[float]) -> bool:
        if len(self._anchors) < 3:
            return False
        zoom = self.get_canvas_zoom()
        distance_screen = (
            math.hypot(
                float(point[0]) - self._anchors[0][0],
                float(point[1]) - self._anchors[0][1],
            )
            * zoom
        )
        return distance_screen <= self.settings.normalized().close_radius_screen

    # ------------------------------------------------------------------
    # Canvas event adapter
    # ------------------------------------------------------------------

    def on_mouse_press(self, event: QMouseEvent, position: Tuple[float, float]):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._segment_pending:
                return
            if self._can_close_at(position):
                self.finish_selection()
                return
            anchor = self._snap_anchor(position)
            if not self._anchors:
                self._append_anchor(anchor)
            elif self._uses_background_pathfinding():
                start = self._anchors[-1]
                if (
                    self._preview_path
                    and self._preview_path_start == start
                    and self._preview_path_endpoint == anchor
                    and self.settings.mode == "legacy"
                ):
                    self._append_anchor(anchor, precomputed_segment=self._preview_path)
                    self._preview_path = []
                    self._preview_path_start = None
                    self._preview_path_endpoint = None
                else:
                    self._segment_pending = True
                    self._request_async_path("segment", start, anchor)
            else:
                self._append_anchor(anchor)
            self.canvas_view.setFocus(Qt.FocusReason.MouseFocusReason)
            self.canvas_view.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

    def on_mouse_move(self, event: QMouseEvent, position: Tuple[float, float]):
        if not self._anchors or self._segment_pending:
            return

        self._hover_can_close = self._can_close_at(position)
        endpoint = (
            self._anchors[0] if self._hover_can_close else self._snap_anchor(position)
        )
        now = time.monotonic()
        elapsed_ms = (now - self._last_preview_time) * 1000.0
        interval = self.settings.normalized().preview_interval_ms
        if endpoint == self._last_preview_endpoint and self._preview_path:
            return
        if elapsed_ms < interval and self._preview_path:
            return

        self._last_preview_time = now
        self._last_preview_endpoint = endpoint
        start = self._anchors[-1]
        if self._uses_background_pathfinding():
            self._request_async_path("preview", start, endpoint)
        else:
            self._preview_path = self._compute_magnetic_path(start, endpoint)
            self._preview_path_start = start
            self._preview_path_endpoint = endpoint
        self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, position: Tuple[float, float]):
        return None

    def on_double_click(self, event: QMouseEvent, position: Tuple[float, float]):
        if len(self._anchors) >= 3:
            self.finish_selection()

    def on_key_press(self, event) -> bool:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.cancel()
            return True
        if key in {Qt.Key.Key_Backspace, Qt.Key.Key_Delete} and self._anchors:
            self.remove_last_anchor()
            return True
        if key in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and len(self._anchors) >= 3:
            self.finish_selection()
            return True
        return False

    def on_undo(self) -> bool:
        return self.remove_last_anchor() if self._anchors else False

    def on_redo(self) -> bool:
        return self.restore_last_anchor() if self._redo_anchor_stack else False

    def on_cancel(self):
        self.cancel()

    # ------------------------------------------------------------------
    # Commit and validation
    # ------------------------------------------------------------------

    def _candidate_closed_path(
        self,
        precomputed_closing: Optional[Sequence[Point]] = None,
    ) -> List[Point]:
        if len(self._anchors) < 3:
            return []
        closing = (
            list(precomputed_closing)
            if precomputed_closing is not None
            else self._compute_magnetic_path(self._anchors[-1], self._anchors[0])
        )
        if not closing:
            return []
        candidate = list(self._path)
        if candidate and closing[0] == candidate[-1]:
            candidate.extend(closing[1:])
        else:
            candidate.extend(closing)
        return deduplicate_path(candidate)

    def _finish_with_closing_path(self, closing: Sequence[Point]) -> Optional[str]:
        candidate = self._candidate_closed_path(closing)
        if len(candidate) < 3:
            self._show_invalid_selection()
            return None
        object_id = self.commit_selection(candidate)
        if object_id is None:
            if not self._last_error:
                self._show_invalid_selection()
            return None
        self._reset_selection_state()
        self.canvas_view.update()
        return object_id

    def finish_selection(self) -> Optional[str]:
        if self._segment_pending:
            return None
        if self._uses_background_pathfinding() and len(self._anchors) >= 3:
            start = self._anchors[-1]
            end = self._anchors[0]
            if (
                self._preview_path
                and self._preview_path_start == start
                and self._preview_path_endpoint == end
                and self.settings.mode == "legacy"
            ):
                return self._finish_with_closing_path(self._preview_path)
            self._segment_pending = True
            self._request_async_path("finish", start, end)
            return None

        candidate = self._candidate_closed_path()
        if len(candidate) < 3:
            self._show_invalid_selection()
            return None
        object_id = self.commit_selection(candidate)
        if object_id is None:
            if not self._last_error:
                self._show_invalid_selection()
            return None
        self._reset_selection_state()
        self.canvas_view.update()
        return object_id

    def commit_selection(self, path: Optional[Sequence[Sequence[float]]] = None):
        self._last_error = ""
        source = path if path is not None else self._path
        polygon = deduplicate_path(source)
        normalized = self.settings.normalized()
        if self.settings.mode == "precise":
            polygon = sanitize_closed_polygon(
                polygon,
                epsilon=normalized.simplify_epsilon,
                max_vertices=normalized.max_vertices,
                minimum_area=1.0,
            )
        else:
            # Legacy mode keeps its pathfinder, but the final ring still needs
            # to obey the same non-destructive Scene contract.
            polygon = sanitize_closed_polygon(
                polygon,
                epsilon=0.0,
                max_vertices=max(len(polygon), 3),
                minimum_area=1.0,
            )

        if len(polygon) < 3:
            self._last_error = "Polygon has insufficient non-collinear area"
            return None
        if polygon_self_intersects(polygon):
            self._last_error = "Polygon self-intersects"
            return None

        try:
            # Validate with the exact same strict contract used by Scene before
            # sending anything to CommandManager.  CommandManager intentionally
            # logs and absorbs execution errors, so prevalidation prevents an
            # invalid command from polluting the terminal or project history.
            from src.models.scene import _normalize_polygon_winding, _validate_polygon

            polygon = _normalize_polygon_winding(list(polygon))
            if not _validate_polygon(polygon):
                self._last_error = "Polygon rejected by the Scene validation contract"
                return None

            return self.commit_polygon_command(
                polygon,
                action_name="Magnetic Lasso Creation",
            )
        except Exception as exc:
            self._last_error = str(exc)
            return None

    def _show_invalid_selection(self) -> None:
        text = self.translations[self.current_lang]["invalid_selection"]
        self._last_error = text
        try:
            QMessageBox.warning(
                self.canvas_view,
                self.translations[self.current_lang]["title"],
                text,
            )
        except Exception:
            # Headless/mocked environments still preserve the selection state.
            pass

    # ------------------------------------------------------------------
    # Drawing and options
    # ------------------------------------------------------------------

    def draw_overlay(self, painter: QPainter):
        if not self._anchors and not self._path and not self.settings.show_edge_map:
            return

        transform = self.canvas_view.get_transform()
        zoom = self.get_canvas_zoom()

        painter.save()
        painter.setTransform(transform, combine=True)

        if self.settings.show_edge_map:
            if self._edge_overlay_image is None:
                if self._uses_background_pathfinding():
                    self.prepare_edge_map_async()
                else:
                    self._compute_edge_map()
            if self._edge_overlay_image is not None:
                painter.save()
                painter.setOpacity(0.42)
                painter.drawImage(0, 0, self._edge_overlay_image)
                painter.restore()

        if self._path and len(self._path) > 1:
            pen = QPen(QColor(0, 255, 0), 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawPolyline(
                QPolygonF([QPointF(float(x), float(y)) for x, y in self._path])
            )

        if self._preview_path and len(self._preview_path) > 1:
            preview_pen = QPen(QColor(255, 220, 0), 1, Qt.PenStyle.DashLine)
            preview_pen.setCosmetic(True)
            painter.setPen(preview_pen)
            painter.drawPolyline(
                QPolygonF([QPointF(float(x), float(y)) for x, y in self._preview_path])
            )

        radius = 4.0 / zoom if zoom > 0 else 4.0
        for index, (x, y) in enumerate(self._anchors):
            color = (
                QColor(0, 220, 255)
                if self.settings.mode == "precise"
                else QColor(255, 0, 0)
            )
            if index == 0:
                color = QColor(255, 140, 0)
            painter.setPen(QPen(color, 1))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), radius, radius)

        if self._hover_can_close and self._anchors:
            close_pen = QPen(QColor(50, 255, 100), 2)
            close_pen.setCosmetic(True)
            painter.setPen(close_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            x, y = self._anchors[0]
            painter.drawEllipse(QPointF(x, y), radius * 2.2, radius * 2.2)

        painter.restore()

    def _set_mode(self, mode: str) -> None:
        if mode not in {"legacy", "precise"} or mode == self.settings.mode:
            return
        if self._anchors:
            self.cancel()
        self.settings.mode = mode
        self._clear_edge_cache()
        self.canvas_view.update()

    def _set_preset(self, preset: str) -> None:
        if preset == self.settings.preset:
            return
        if self._anchors:
            self.cancel()
        self.settings.apply_preset(preset)
        self._clear_edge_cache()
        self.canvas_view.update()

    def _toggle_edge_overlay(self, checked: bool) -> None:
        self.settings.show_edge_map = bool(checked)
        if self.settings.show_edge_map:
            self.prepare_edge_map_async()
        self.canvas_view.update()

    def show_context_menu(self, event: QMouseEvent):
        text = self.translations[self.current_lang]
        menu = QMenu(self.canvas_view)

        finish = menu.addAction(text["finish_selection"])
        finish.setEnabled(len(self._anchors) >= 3)
        finish.triggered.connect(self.finish_selection)

        remove = menu.addAction(text["remove_anchor"])
        remove.setEnabled(bool(self._anchors))
        remove.triggered.connect(self.remove_last_anchor)

        cancel = menu.addAction(text["cancel_selection"])
        cancel.setEnabled(bool(self._anchors) or bool(self._path))
        cancel.triggered.connect(self.cancel)

        menu.addSeparator()
        mode_menu = menu.addMenu(text["mode"])
        mode_group = QActionGroup(mode_menu)
        mode_group.setExclusive(True)
        for mode, label_key in (("precise", "mode_precise"), ("legacy", "mode_legacy")):
            action = mode_menu.addAction(text[label_key])
            action.setCheckable(True)
            action.setChecked(self.settings.mode == mode)
            action.triggered.connect(
                lambda checked=False, value=mode: self._set_mode(value)
            )
            mode_group.addAction(action)

        preset_menu = menu.addMenu(text["preset"])
        preset_group = QActionGroup(preset_menu)
        preset_group.setExclusive(True)
        for preset, label_key in (
            ("fast", "preset_fast"),
            ("balanced", "preset_balanced"),
            ("precise", "preset_precise"),
        ):
            action = preset_menu.addAction(text[label_key])
            action.setCheckable(True)
            action.setChecked(self.settings.preset == preset)
            action.triggered.connect(
                lambda checked=False, value=preset: self._set_preset(value)
            )
            preset_group.addAction(action)

        show_edges = menu.addAction(text["show_edges"])
        show_edges.setCheckable(True)
        show_edges.setChecked(self.settings.show_edge_map)
        show_edges.toggled.connect(self._toggle_edge_overlay)

        menu.addSeparator()
        undo_project = menu.addAction(text["undo_project"])
        undo_project.setEnabled(not self._anchors)
        undo_project.triggered.connect(self._undo_project)
        redo_project = menu.addAction(text["redo_project"])
        redo_project.setEnabled(not self._anchors)
        redo_project.triggered.connect(self._redo_project)

        menu.exec(event.globalPos())

    def _undo_project(self):
        model = self.canvas_view.model
        if hasattr(model, "cmd") and model.cmd:
            model.cmd.undo(model)

    def _redo_project(self):
        model = self.canvas_view.model
        if hasattr(model, "cmd") and model.cmd:
            model.cmd.redo(model)

    # Historical names remain available to external callers.
    def undo_last_action(self):
        if not self.on_undo():
            self._undo_project()

    def redo_last_action(self):
        if not self.on_redo():
            self._redo_project()

    def cancel(self):
        self._reset_selection_state()
        self.canvas_view.update()

    def update_language(self, lang):
        if lang in self.translations:
            self.current_lang = lang
