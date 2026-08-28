# src/ui/mask_viewer.py
"""
Mask Viewer widget with pan/zoom capabilities for visualizing images and masks.
"""

import logging
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPolygonF,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.view_processor import ViewProcessor

logger = logging.getLogger(__name__)

# Detection presets with parameters and expected performance
DETECTION_PRESETS = {
    "Basic": {
        "mode": "basic",
        "params": {
            "downscale": 1.0,
            "canny_threshold1": 100,
            "canny_threshold2": 200,
            "rdp_epsilon": 2.0,
            "min_area": 100.0,
            "detect_holes": True,
        },
        "estimated_runtime": "0.1-0.5s",
        "expected_polygons": "10-50",
    },
    "Perfect": {
        "mode": "perfect",
        "params": {
            "downscale": 0.65,
            "base_eps": 2.0,
            "curvature_factor": 1.0,
            "min_area": 100.0,
            "decompose_convex": False,
            "watershed_distance": 10,
            "separate_touching": False,
        },
        "estimated_runtime": "0.5-2.0s",
        "expected_polygons": "5-20",
    },
    "GrabCut": {
        "mode": "grabcut",
        "params": {
            "min_area": 100.0,
            "rdp_epsilon": 1.5,
            "grabcut_iterations": 5,
            "roi_padding": 2,
            "detect_holes": True,
        },
        "estimated_runtime": "0.2-1.5s",
        "expected_polygons": "1",
    },
    "Enhanced": {
        "mode": "enhanced",
        "params": {
            "downscale": 0.65,
            "canny_thresh1": 50,
            "canny_thresh2": 150,
            "min_area": 50.0,
            "chaikin_iterations": 0,
            "fit_bezier": False,
            "morph_kernel_size": 1,
            "detect_holes": False,
        },
        "estimated_runtime": "1.0-5.0s",
        "expected_polygons": "20-100",
    },
}


class DetectionWorker(QObject):
    finished = Signal(object)  # Retorna lista de polígonos
    error = Signal(str)

    def __init__(self, image, mode, params):
        super().__init__()
        # CRÍTICO: Copia a imagem para garantir thread safety
        self.image = image.copy() if image is not None else None
        self.mode = mode
        self.params = params

    def run(self):
        if self.image is None:
            self.error.emit("No image data provided to worker")
            return

        try:
            from src.tools.auto_detect import detect_polygons

            result = detect_polygons(self.image, mode=self.mode, **self.params)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Detection worker error: {e}")
            self.error.emit(str(e))


try:
    import PIL

    HAS_PIL = PIL is not None
except ImportError:
    HAS_PIL = False

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class MaskViewer(QWidget):
    """
    Interactive image viewer with pan/zoom capabilities.
    """

    viewChanged = Signal()
    imageClicked = Signal(QPointF)
    polygonSelected = Signal(int)  # Emits index of selected polygon, -1 for deselection
    roiSelected = Signal(object)  # Emits (x, y, width, height) in image pixels
    polygonsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # View transform state
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._min_zoom = 0.1
        self._max_zoom = 8.0

        # Image state
        self._image: Optional[np.ndarray] = None
        self._display_image: Optional[np.ndarray] = None
        self._display_mode = 0
        self._fit_pending = False
        self._qimage_cache: Optional[QImage] = None
        self._composed_image: Optional[np.ndarray] = None
        self._layer_overlays: Dict[str, bool] = {}
        self._layer_opacity = 0.5

        # Overlay Polygons (Visualization)
        self._overlay_polygons = []
        self._selected_polygon_index = -1  # Index of selected polygon, -1 for none
        self._editing_polygon_index = -1
        self._editing_vertex_index = -1
        self._roi_mode = False
        self._roi_start: Optional[QPointF] = None
        self._roi_rect: Optional[Tuple[float, float, float, float]] = None

        # Pan state
        self._panning = False
        self._pan_start_pos = QPointF()
        self._pan_start_offset = QPointF()

        # Tool handler for event delegation
        self.tool_handler: Optional[Callable[[QMouseEvent], bool]] = None
        self._suppress_tool_events = False

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(200, 200)

    def set_overlay_polygons(self, polygons):
        """Set polygons to draw over the image."""
        self._overlay_polygons = polygons
        self._selected_polygon_index = -1  # Reset selection when polygons change
        self._editing_polygon_index = -1
        self._editing_vertex_index = -1
        self._refresh_polygon_validation()
        self.update()

    def _refresh_polygon_validation(self) -> Tuple[int, int]:
        """Refresh diagnostics after a user edits an overlay vertex."""
        from src.tools.auto_detect import polygon_validation_error

        valid_count = 0
        invalid_count = 0
        for polygon_data in self._overlay_polygons:
            polygon = (
                polygon_data.get("polygon", [])
                if isinstance(polygon_data, dict)
                else polygon_data
            )
            reason = polygon_validation_error(polygon)
            if isinstance(polygon_data, dict):
                polygon_data["is_valid"] = reason is None
            if reason is None:
                if isinstance(polygon_data, dict):
                    polygon_data.pop("validation_error", None)
                valid_count += 1
            else:
                if isinstance(polygon_data, dict):
                    polygon_data["validation_error"] = reason
                invalid_count += 1
        return valid_count, invalid_count

    def _find_vertex_at(self, view_point: QPointF) -> Tuple[int, int]:
        threshold = 9.0
        best = (-1, -1)
        best_distance = threshold
        for polygon_index, polygon_data in enumerate(self._overlay_polygons):
            polygon = (
                polygon_data.get("polygon")
                if isinstance(polygon_data, dict)
                else polygon_data
            )
            if not polygon:
                continue
            for vertex_index, point in enumerate(polygon):
                vertex = self.image_to_view(QPointF(float(point[0]), float(point[1])))
                distance = math.hypot(
                    vertex.x() - view_point.x(), vertex.y() - view_point.y()
                )
                if distance <= best_distance:
                    best = (polygon_index, vertex_index)
                    best_distance = distance
        return best

    def _move_editing_vertex(self, view_point: QPointF) -> None:
        if self._editing_polygon_index < 0 or self._editing_vertex_index < 0:
            return
        polygon_data = self._overlay_polygons[self._editing_polygon_index]
        polygon = (
            polygon_data.get("polygon")
            if isinstance(polygon_data, dict)
            else polygon_data
        )
        if not polygon:
            return
        x, y = self.view_to_image(view_point)
        if self._image is not None:
            height, width = self._image.shape[:2]
            x = min(max(x, 0.0), float(max(0, width - 1)))
            y = min(max(y, 0.0), float(max(0, height - 1)))
        polygon[self._editing_vertex_index] = (int(round(x)), int(round(y)))
        self._refresh_polygon_validation()
        self.polygonsChanged.emit()
        self.update()
    def set_roi_mode(self, enabled: bool) -> None:
        """Enable rectangle selection for the assisted GrabCut workflow."""
        self._roi_mode = bool(enabled)
        self._roi_start = None
        self.setCursor(
            Qt.CursorShape.CrossCursor if self._roi_mode else Qt.CursorShape.ArrowCursor
        )
        self.update()

    def get_roi(self) -> Optional[Tuple[int, int, int, int]]:
        if self._roi_rect is None:
            return None
        x, y, width, height = self._roi_rect
        return (int(round(x)), int(round(y)), int(round(width)), int(round(height)))

    def clear_roi(self) -> None:
        self._roi_rect = None
        self._roi_start = None
        self.update()

    def _update_roi(self, current_view: QPointF) -> None:
        if self._roi_start is None:
            return
        start_x, start_y = self.view_to_image(self._roi_start)
        current_x, current_y = self.view_to_image(current_view)
        if self._image is not None:
            height, width = self._image.shape[:2]
            start_x = min(max(start_x, 0.0), float(width))
            current_x = min(max(current_x, 0.0), float(width))
            start_y = min(max(start_y, 0.0), float(height))
            current_y = min(max(current_y, 0.0), float(height))
        self._roi_rect = (
            min(start_x, current_x),
            min(start_y, current_y),
            abs(current_x - start_x),
            abs(current_y - start_y),
        )
        self.update()

    def get_selected_polygon_index(self) -> int:
        """Get the index of the currently selected polygon."""
        return self._selected_polygon_index

    def set_selected_polygon_index(self, index: int):
        """Set the selected polygon index."""
        if index < -1 or index >= len(self._overlay_polygons):
            index = -1
        if self._selected_polygon_index != index:
            self._selected_polygon_index = index
            self.polygonSelected.emit(index)
            self.update()

    def _find_polygon_at(self, image_point: QPointF) -> int:
        """Find the index of the polygon containing the given image point."""
        for i, poly_data in enumerate(self._overlay_polygons):
            polygon = (
                poly_data.get("polygon") if isinstance(poly_data, dict) else poly_data
            )
            if polygon and len(polygon) >= 3:
                qpoints = [QPointF(float(p[0]), float(p[1])) for p in polygon]
                qpoly = QPolygonF(qpoints)
                if qpoly.containsPoint(image_point, Qt.FillRule.OddEvenFill):
                    return i
        return -1

    def set_numpy_image(self, image: Optional[np.ndarray]):
        """Set the source image and refresh the selected display mode."""
        self._image = image.copy() if image is not None else None
        self._fit_pending = self._image is not None
        self._qimage_cache = None
        if self.isVisible():
            QTimer.singleShot(0, self._fit_after_layout)
        self.set_display_mode(self._display_mode, update=False)
        self.update()

    def showEvent(self, event) -> None:
        """Fit after the parent layout has assigned the final viewport size."""
        super().showEvent(event)
        if self._fit_pending:
            QTimer.singleShot(0, self._fit_after_layout)

    def _fit_after_layout(self) -> None:
        if not self._fit_pending or self._image is None:
            return
        if self.width() <= 0 or self.height() <= 0:
            return
        self._fit_pending = False
        self.reset_view()

    def set_display_mode(self, mode: int, update: bool = True) -> None:
        """Show the source image or one of the shared X-Ray processors."""
        self._display_mode = max(0, min(3, int(mode)))
        if self._image is None or self._display_mode == 0:
            self._display_image = self._image
        else:
            try:
                generated = ViewProcessor.generate_xray_array(
                    self._image, self._display_mode
                )
                self._display_image = (
                    np.asarray(generated).copy()
                    if generated is not None
                    else self._image
                )
            except Exception as exc:
                logger.warning("Mask viewer X-Ray failed: %s", exc)
                self._display_image = self._image
        self._qimage_cache = None
        if update:
            self.update()

    def set_layer_overlays(
        self, enabled_layers: Dict[str, bool], opacity: float = 0.5
    ) -> None:
        """Render the selected diagnostic layers over the current image."""
        self._layer_overlays = dict(enabled_layers)
        self._layer_opacity = min(1.0, max(0.0, float(opacity)))
        self._qimage_cache = None
        self.update()

    def _compose_layer_overlays(self, source: np.ndarray) -> np.ndarray:
        if not self._layer_overlays or not HAS_CV2:
            return source
        if source.ndim == 2:
            base = cv2.cvtColor(source, cv2.COLOR_GRAY2RGB)
        elif source.shape[2] == 4:
            base = source[:, :, :3].copy()
        else:
            base = source.copy()
        if base.dtype != np.uint8:
            base = np.clip(base, 0, 255).astype(np.uint8)
        gray = cv2.cvtColor(base, cv2.COLOR_RGB2GRAY)
        masks: Dict[str, np.ndarray] = {}
        if self._layer_overlays.get("Sobel"):
            sobel = ViewProcessor.generate_xray_array(base, 1)
            masks["Sobel"] = cv2.cvtColor(sobel, cv2.COLOR_RGB2GRAY)
        if self._layer_overlays.get("Canny"):
            canny = ViewProcessor.generate_xray_array(base, 2)
            masks["Canny"] = cv2.cvtColor(canny, cv2.COLOR_RGB2GRAY)
        if self._layer_overlays.get("Threshold"):
            _, masks["Threshold"] = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        if self._layer_overlays.get("Watershed"):
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            masks["Watershed"] = cv2.Canny(binary, 50, 150)
        colors = {
            "Sobel": (0, 220, 255),
            "Canny": (255, 0, 180),
            "Threshold": (40, 255, 80),
            "Watershed": (255, 150, 0),
        }
        composed = base
        for layer, mask in masks.items():
            color = np.zeros_like(base)
            color[:, :] = colors[layer]
            active = mask > 0
            if not np.any(active):
                continue
            blended = cv2.addWeighted(
                composed, 1.0 - self._layer_opacity, color, self._layer_opacity, 0
            )
            composed[active] = blended[active]
        return composed

    def get_display_mode(self) -> int:
        return self._display_mode

    def get_numpy_image(self) -> Optional[np.ndarray]:
        """Get the current image as numpy array."""
        return self._image.copy() if self._image is not None else None

    def get_processing_image(
        self, use_active_view: bool = False
    ) -> Optional[np.ndarray]:
        """Return the explicit image source selected for a processing tool.

        The original scene image remains the default. When requested, the
        currently selected X-Ray result is returned without mutating the
        original scene image.
        """
        if (
            use_active_view
            and self._display_mode != 0
            and self._display_image is not None
        ):
            return self._display_image.copy()
        return self._image.copy() if self._image is not None else None

    def get_zoom(self) -> float:
        return self._zoom

    def get_pan(self) -> Tuple[float, float]:
        return self._pan_x, self._pan_y

    def set_zoom(self, zoom: float, center_view: Optional[QPointF] = None):
        """Set zoom level, optionally centered on a view point."""
        if center_view is not None:
            image_point = self.view_to_image(center_view)
            self._zoom = max(self._min_zoom, min(self._max_zoom, zoom))
            new_view_point = self.image_to_view(QPointF(*image_point))
            self._pan_x += center_view.x() - new_view_point.x()
            self._pan_y += center_view.y() - new_view_point.y()
        else:
            self._zoom = max(self._min_zoom, min(self._max_zoom, zoom))

        self.viewChanged.emit()
        self.update()

    def set_pan(self, pan_x: float, pan_y: float):
        self._pan_x = pan_x
        self._pan_y = pan_y
        self.viewChanged.emit()
        self.update()

    def get_view_transform(self) -> Tuple[float, float, float]:
        """Return the current ``(zoom, pan_x, pan_y)`` transform."""
        return self._zoom, self._pan_x, self._pan_y

    def set_view_transform(self, zoom: float, pan_x: float, pan_y: float) -> None:
        """Set zoom and pan atomically while preserving zoom limits."""
        self._zoom = max(self._min_zoom, min(self._max_zoom, float(zoom)))
        self._pan_x = float(pan_x)
        self._pan_y = float(pan_y)
        self.viewChanged.emit()
        self.update()

    def reset_view(self):
        if self._image is None:
            self._zoom = 1.0
            self._pan_x = 0.0
            self._pan_y = 0.0
        else:
            img_height, img_width = self._image.shape[:2]
            widget_width = self.width()
            widget_height = self.height()

            if img_width > 0 and img_height > 0:
                # Preencher completamente a tela (sem margem)
                zoom_x = widget_width / img_width
                zoom_y = widget_height / img_height
                self._zoom = max(
                    zoom_x, zoom_y
                )  # Usar o maior para preencher completamente

                # Centralizar a imagem
                self._pan_x = (widget_width - img_width * self._zoom) / 2
                self._pan_y = (widget_height - img_height * self._zoom) / 2

        self.viewChanged.emit()
        self.update()

    def zoom_by(self, factor: float, center_view: Optional[QPointF] = None):
        self.set_zoom(self._zoom * factor, center_view)

    @staticmethod
    def _point_xy(point) -> Tuple[float, float]:
        """Read coordinates from QPointF or a two-item sequence."""
        if hasattr(point, "x") and hasattr(point, "y"):
            return float(point.x()), float(point.y())
        x, y = point
        return float(x), float(y)

    def image_to_view(self, image_point) -> QPointF:
        """Convert image coordinates to view coordinates."""
        image_x, image_y = self._point_xy(image_point)
        view_x = image_x * self._zoom + self._pan_x
        view_y = image_y * self._zoom + self._pan_y
        return QPointF(view_x, view_y)

    def view_to_image(self, view_point) -> Tuple[float, float]:
        """Convert view coordinates to image coordinates."""
        view_x, view_y = self._point_xy(view_point)
        x = (view_x - self._pan_x) / self._zoom
        y = (view_y - self._pan_y) / self._zoom
        return x, y

    # Event handling
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self._panning = True
            self._pan_start_pos = event.position()
            self._pan_start_offset = QPointF(self._pan_x, self._pan_y)
            self._suppress_tool_events = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            if self._roi_mode:
                self._roi_start = event.position()
                self._roi_rect = None
                event.accept()
                return
            editing = self._find_vertex_at(event.position())
            if editing != (-1, -1):
                self._editing_polygon_index, self._editing_vertex_index = editing
                self.set_selected_polygon_index(self._editing_polygon_index)
                self.setCursor(Qt.CursorShape.CrossCursor)
                event.accept()
                return
            if not self._suppress_tool_events and self.tool_handler is not None:
                if self.tool_handler(event):
                    event.accept()
                    return

            # Check for polygon selection
            if self._image is not None:
                image_pos = self.view_to_image(event.position())
                polygon_index = self._find_polygon_at(QPointF(*image_pos))
                self.set_selected_polygon_index(polygon_index)
                if polygon_index >= 0:
                    event.accept()
                    return

            if self._image is not None:
                image_pos = self.view_to_image(event.position())
                self.imageClicked.emit(QPointF(*image_pos))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._roi_mode and self._roi_start is not None:
            self._update_roi(event.position())
            event.accept()
        elif self._editing_polygon_index >= 0:
            self._move_editing_vertex(event.position())
            event.accept()
        elif self._panning:
            delta = event.position() - self._pan_start_pos
            self._pan_x = self._pan_start_offset.x() + delta.x()
            self._pan_y = self._pan_start_offset.y() + delta.y()
            self.viewChanged.emit()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._roi_mode and self._roi_start is not None:
            self._update_roi(event.position())
            roi = self.get_roi()
            self._roi_start = None
            if roi is None or roi[2] < 2 or roi[3] < 2:
                self._roi_rect = None
                self.update()
                event.ignore()
                return
            self.roiSelected.emit(roi)
            event.accept()
        elif self._editing_polygon_index >= 0:
            self._editing_polygon_index = -1
            self._editing_vertex_index = -1
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif self._panning:
            self._panning = False
            self._suppress_tool_events = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = 1.15 if delta > 0 else 1.0 / 1.15
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.35 if delta > 0 else 1.0 / 1.35

        self.zoom_by(factor, event.position())
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_R:
            self.reset_view()
            event.accept()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # Painting
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(64, 64, 64))

        if self._image is None:
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "No image loaded"
            )
            return

        qimage = self._get_qimage()
        if qimage:
            painter.save()
            painter.translate(self._pan_x, self._pan_y)
            painter.scale(self._zoom, self._zoom)

            # Draw Image
            painter.drawImage(0, 0, qimage)

            if self._roi_rect is not None:
                x, y, width, height = self._roi_rect
                roi_pen = QPen(QColor(255, 165, 0), 2)
                roi_pen.setCosmetic(True)
                painter.setPen(roi_pen)
                painter.setBrush(QColor(255, 165, 0, 35))
                painter.drawRect(QRectF(x, y, width, height))

            # Draw Overlay Polygons
            if self._overlay_polygons:
                for i, poly_data in enumerate(self._overlay_polygons):
                    # Handle both dict and object formats
                    polygon = (
                        poly_data.get("polygon")
                        if isinstance(poly_data, dict)
                        else poly_data
                    )

                    if polygon and len(polygon) >= 3:
                        # Convert points to QPointF
                        qpoints = [QPointF(float(p[0]), float(p[1])) for p in polygon]
                        qpoly = QPolygonF(qpoints)

                        # Set style based on selection
                        invalid = (
                            isinstance(poly_data, dict)
                            and poly_data.get("is_valid") is False
                        )
                        if invalid:
                            pen = QPen(QColor(255, 50, 50), 3)
                            pen.setCosmetic(True)
                            painter.setPen(pen)
                            painter.setBrush(QColor(255, 0, 0, 70))
                        elif i == self._selected_polygon_index:
                            pen = QPen(
                                QColor(255, 255, 0), 3
                            )  # Yellow outline for selected
                            pen.setCosmetic(True)
                            painter.setPen(pen)
                            painter.setBrush(
                                QColor(255, 255, 0, 80)
                            )  # Semi-transparent yellow fill
                        else:
                            pen = QPen(QColor(0, 255, 0), 2)  # Green outline
                            pen.setCosmetic(True)
                            painter.setPen(pen)
                            painter.setBrush(
                                QColor(0, 255, 0, 50)
                            )  # Semi-transparent green fill

                        painter.drawPolygon(qpoly)
                        if i == self._selected_polygon_index:
                            handle_pen = QPen(QColor(255, 255, 255), 1)
                            handle_pen.setCosmetic(True)
                            painter.setPen(handle_pen)
                            painter.setBrush(
                                QColor(255, 50, 50, 220)
                                if invalid
                                else QColor(255, 255, 255, 220)
                            )
                            for point in qpoints:
                                painter.drawEllipse(point, 3.5 / self._zoom, 3.5 / self._zoom)

            painter.restore()

    def _get_qimage(self) -> Optional[QImage]:
        source = self._image if self._display_mode == 0 else self._display_image
        if source is None:
            return None
        if self._qimage_cache is not None:
            return self._qimage_cache

        try:
            source = self._compose_layer_overlays(np.asarray(source))
            source = np.asarray(source)
            if source.ndim == 2:
                fmt = QImage.Format.Format_Grayscale8
                display = source
            elif source.ndim == 3 and source.shape[2] == 3:
                display = cv2.cvtColor(source, cv2.COLOR_BGR2RGB) if HAS_CV2 else source
                fmt = QImage.Format.Format_RGB888
            elif source.ndim == 3 and source.shape[2] == 4:
                display = (
                    cv2.cvtColor(source, cv2.COLOR_BGRA2RGBA) if HAS_CV2 else source
                )
                fmt = QImage.Format.Format_RGBA8888
            else:
                raise ValueError(
                    f"unsupported image shape for Mask Viewer: {source.shape!r}"
                )

            display = np.ascontiguousarray(display)
            self._composed_image = display
            height, width = display.shape[:2]
            step = display.strides[0]

            self._qimage_cache = QImage(display.data, width, height, step, fmt).copy()
            return self._qimage_cache
        except Exception as e:
            logger.error(f"Image conversion error: {e}")
            return None


class MaskViewerDialog(QDialog):
    """Complete bilingual Mask Viewer dialog with stable preset identifiers."""

    TRANSLATIONS = {
        "en": {
            "window_title": "Mask Viewer - Auto Detection X-Ray",
            "toolbar": "Mask Viewer Toolbar",
            "view_mode": "View:",
            "view_original": "Original",
            "view_xray_1": "X-Ray Sobel",
            "processing_source": "Detection source:",
            "source_original": "Original image",
            "source_active_view": "Active view (X-Ray when selected)",
            "view_xray_2": "X-Ray Canny",
            "view_xray_3": "X-Ray Laplacian",
            "detection_action": "{preset} Detection",
            "performance_ready": "Performance: Ready",
            "performance": "Performance: {runtime}, Expected: {count} polygons",
            "layer_visualization": "Layer Visualization",
            "layer_sobel": "Sobel",
            "layer_canny": "Canny",
            "layer_threshold": "Threshold",
            "layer_watershed": "Watershed",
            "layer_polygons": "Polygons",
            "opacity": "Opacity:",
            "detection_parameters": "Detection Parameters",
            "min_area": "Min Area",
            "rdp_epsilon": "RDP Epsilon",
            "canny_threshold1": "Canny Thresh 1",
            "canny_threshold2": "Canny Thresh 2",
            "advanced": "Show Advanced Parameters",
            "block_size": "Block Size",
            "threshold_c": "Threshold C",
            "base_eps": "Base Eps",
            "curvature_factor": "Curvature Factor",
            "view_controls": "View Controls",
            "no_image_loaded": "No image loaded",
            "image_info": "Image: {width} x {height} pixels",
            "zoom_value": "Zoom: {value:.1%}",
            "pan_value": "Pan: ({x:.1f}, {y:.1f})",
            "fit_window": "Fit to Window",
            "zoom": "Zoom:",
            "pan_x": "Pan X:",
            "pan_y": "Pan Y:",
            "detection_controls": "Detection Controls",
            "preset": "Preset:",
            "preset_basic": "Basic",
            "preset_perfect": "Perfect",
            "preset_enhanced": "Enhanced",
            "preset_grabcut": "GrabCut (ROI)",
            "select_roi": "Select ROI",
            "roi_selected": "ROI: {x}, {y}, {width} x {height}",
            "detect": "Detect Polygons",
            "processing": "Processing...",
            "apply": "Apply to Scene",
            "ready": "Ready",
            "running": "Running detection algorithms...",
            "found": "Found {count} polygons",
            "detection_failed": "Detection Failed",
            "no_image_title": "No Image",
            "no_image_message": "No image loaded in scene.",
            "error": "Error",
            "detection_error": "Detection failed:\n{error}",
            "success": "Success",
            "added": "Added {count} polygons to scene.",
            "apply_error_title": "Apply Error",
            "apply_error": "Failed to apply polygons:\n{error}",
            "selected": "Selected polygon {index}",
            "validation_summary": "Detected {count} polygons: {valid} valid, {invalid} invalid.",
            "invalid_polygon": "Polygon {index}: {reason}",
            "invalid_hint": "Invalid polygons are shown in red. Drag their vertices until all are valid.",
            "valid_hint": "All detected polygons are valid and ready to apply.",
        },
        "pt": {
            "window_title": "Visualizador de Máscara - Raio-X de Detecção Automática",
            "toolbar": "Ferramentas do Visualizador de Máscara",
            "view_mode": "Visualização:",
            "view_original": "Original",
            "processing_source": "Fonte da detecção:",
            "source_original": "Imagem original",
            "source_active_view": "Visualização ativa (Raio-X quando selecionado)",
            "view_xray_1": "Raio-X Sobel",
            "view_xray_2": "Raio-X Canny",
            "view_xray_3": "Raio-X Laplaciano",
            "detection_action": "Detecção {preset}",
            "performance_ready": "Desempenho: Pronto",
            "performance": "Desempenho: {runtime}, esperado: {count} polígonos",
            "layer_visualization": "Visualização de Camadas",
            "layer_sobel": "Sobel",
            "layer_canny": "Canny",
            "layer_threshold": "Limiar",
            "layer_watershed": "Watershed",
            "layer_polygons": "Polígonos",
            "opacity": "Opacidade:",
            "detection_parameters": "Parâmetros de Detecção",
            "min_area": "Área Mínima",
            "rdp_epsilon": "Épsilon RDP",
            "canny_threshold1": "Limiar Canny 1",
            "canny_threshold2": "Limiar Canny 2",
            "advanced": "Mostrar Parâmetros Avançados",
            "block_size": "Tamanho do Bloco",
            "threshold_c": "Limiar C",
            "base_eps": "Épsilon Base",
            "curvature_factor": "Fator de Curvatura",
            "view_controls": "Controles de Visualização",
            "no_image_loaded": "Nenhuma imagem carregada",
            "image_info": "Imagem: {width} x {height} pixels",
            "zoom_value": "Zoom: {value:.1%}",
            "pan_value": "Deslocamento: ({x:.1f}, {y:.1f})",
            "fit_window": "Ajustar à Janela",
            "zoom": "Zoom:",
            "pan_x": "Deslocamento X:",
            "pan_y": "Deslocamento Y:",
            "detection_controls": "Controles de Detecção",
            "preset": "Predefinição:",
            "preset_basic": "Básico",
            "preset_perfect": "Perfeito",
            "preset_enhanced": "Aprimorado",
            "preset_grabcut": "GrabCut (ROI)",
            "select_roi": "Selecionar ROI",
            "roi_selected": "ROI: {x}, {y}, {width} x {height}",
            "detect": "Detectar Polígonos",
            "processing": "Processando...",
            "apply": "Aplicar à Cena",
            "ready": "Pronto",
            "running": "Executando algoritmos de detecção...",
            "found": "Encontrados {count} polígonos",
            "detection_failed": "Falha na Detecção",
            "no_image_title": "Sem Imagem",
            "no_image_message": "Nenhuma imagem foi carregada na cena.",
            "error": "Erro",
            "detection_error": "Falha na detecção:\n{error}",
            "success": "Sucesso",
            "added": "{count} polígonos adicionados à cena.",
            "apply_error_title": "Erro ao Aplicar",
            "apply_error": "Falha ao aplicar polígonos:\n{error}",
            "selected": "Polígono {index} selecionado",
            "validation_summary": "Detectados {count} polígonos: {valid} válidos, {invalid} inválidos.",
            "invalid_polygon": "Polígono {index}: {reason}",
            "invalid_hint": "Polígonos inválidos aparecem em vermelho. Arraste seus vértices até que todos sejam válidos.",
            "valid_hint": "Todos os polígonos detectados são válidos e podem ser aplicados.",
        },
    }

    PRESET_ORDER = ("Basic", "Perfect", "Enhanced", "GrabCut")
    PRESET_TEXT_KEYS = {
        "Basic": "preset_basic",
        "Perfect": "preset_perfect",
        "Enhanced": "preset_enhanced",
        "GrabCut": "preset_grabcut",
    }
    LAYER_TEXT_KEYS = {
        "Sobel": "layer_sobel",
        "Canny": "layer_canny",
        "Threshold": "layer_threshold",
        "Watershed": "layer_watershed",
        "Polygons": "layer_polygons",
    }

    def __init__(self, scene, parent=None, lang: Optional[str] = None):
        super().__init__(parent)
        self.scene = scene
        inherited_lang = getattr(parent, "current_lang", "en")
        self.current_lang = lang if lang in self.TRANSLATIONS else inherited_lang
        if self.current_lang not in self.TRANSLATIONS:
            self.current_lang = "en"

        self.params = {
            "downscale": 1.0,
            "canny_threshold1": 100,
            "canny_threshold2": 200,
            "rdp_epsilon": 2.0,
            "min_area": 100.0,
            "block_size": 11,
            "threshold_c": 2,
            "base_eps": 2.0,
            "curvature_factor": 1.0,
            "decompose_convex": False,
            "watershed_distance": 10,
            "separate_touching": False,
            "canny_thresh1": 50,
            "canny_thresh2": 150,
            "chaikin_iterations": 0,
            "fit_bezier": False,
            "morph_kernel_size": 1,
            "detect_holes": True,
        }

        self.resize(1200, 800)
        self.viewer = MaskViewer(self)
        self._last_polygons: List[Any] = []
        self._thread: Optional[QThread] = None
        self._worker: Optional[DetectionWorker] = None
        self._current_mask = None
        self._roi: Optional[Tuple[int, int, int, int]] = None
        self._layer_overlays: Dict[str, bool] = {}
        self.param_widgets: Dict[str, QSpinBox | QDoubleSpinBox] = {}
        self.param_labels: Dict[str, QLabel] = {}
        self.layer_checkboxes: Dict[str, QCheckBox] = {}
        self.preset_actions: Dict[str, QAction] = {}
        self.view_mode_buttons: list[QPushButton] = []
        self.view_mode_button_group: QButtonGroup | None = None

        self._setup_ui()
        self.update_language(self.current_lang)
        self._load_scene_image()

        if hasattr(self.scene, "image_changed"):
            self.scene.image_changed.connect(self._load_scene_image)

    @property
    def t(self):
        return self.TRANSLATIONS[self.current_lang]

    def _setup_ui(self):
        logger.debug("Setting up UI components")
        main_layout = QHBoxLayout(self)
        control_panel = QWidget()
        control_panel.setMinimumWidth(370)
        control_panel.setMaximumWidth(430)
        control_layout = QVBoxLayout(control_panel)

        self._setup_toolbar()
        control_layout.addWidget(self.toolbar)
        self._setup_explicit_view_modes()
        control_layout.addWidget(self.view_mode_group)
        self._setup_layer_controls()
        control_layout.addWidget(self.layer_controls)
        self._setup_parameter_controls()
        control_layout.addWidget(self.param_controls)

        self.view_group = QGroupBox()
        view_layout = QVBoxLayout(self.view_group)
        self.info_label = QLabel()
        self.zoom_label = QLabel()
        self.pan_label = QLabel()
        view_layout.addWidget(self.info_label)
        view_layout.addWidget(self.zoom_label)
        view_layout.addWidget(self.pan_label)

        self.fit_button = QPushButton()
        self.fit_button.clicked.connect(self._fit_to_window)
        view_layout.addWidget(self.fit_button)

        zoom_layout = QHBoxLayout()
        self.zoom_text_label = QLabel()
        zoom_layout.addWidget(self.zoom_text_label)
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(10, 800)
        self.zoom_spin.setValue(100.0)
        self.zoom_spin.setSingleStep(10.0)
        self.zoom_spin.valueChanged.connect(self._on_zoom_changed)
        zoom_layout.addWidget(self.zoom_spin)
        self.zoom_percent_label = QLabel("%")
        zoom_layout.addWidget(self.zoom_percent_label)
        view_layout.addLayout(zoom_layout)

        pan_x_layout = QHBoxLayout()
        self.pan_x_label = QLabel()
        pan_x_layout.addWidget(self.pan_x_label)
        self.pan_x_spin = QSpinBox()
        self.pan_x_spin.setRange(-10000, 10000)
        self.pan_x_spin.valueChanged.connect(self._on_pan_changed)
        pan_x_layout.addWidget(self.pan_x_spin)
        view_layout.addLayout(pan_x_layout)

        pan_y_layout = QHBoxLayout()
        self.pan_y_label = QLabel()
        pan_y_layout.addWidget(self.pan_y_label)
        self.pan_y_spin = QSpinBox()
        self.pan_y_spin.setRange(-10000, 10000)
        self.pan_y_spin.valueChanged.connect(self._on_pan_changed)
        pan_y_layout.addWidget(self.pan_y_spin)
        view_layout.addLayout(pan_y_layout)
        control_layout.addWidget(self.view_group)

        self.detection_group = QGroupBox()
        detection_layout = QVBoxLayout(self.detection_group)
        preset_layout = QHBoxLayout()
        self.preset_label = QLabel()
        preset_layout.addWidget(self.preset_label)
        self.preset_combo = QComboBox()
        for preset_id in self.PRESET_ORDER:
            self.preset_combo.addItem("", preset_id)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        detection_layout.addLayout(preset_layout)
        source_layout = QHBoxLayout()
        self.processing_source_label = QLabel()
        source_layout.addWidget(self.processing_source_label)
        self.processing_source_combo = QComboBox()
        self.processing_source_combo.setObjectName("mask_processing_source")
        self.processing_source_combo.addItem("", "original")
        self.processing_source_combo.addItem("", "active_view")
        source_layout.addWidget(self.processing_source_combo, 1)
        detection_layout.addLayout(source_layout)

        self.detect_button = QPushButton()
        self.detect_button.clicked.connect(self._run_detection)
        detection_layout.addWidget(self.detect_button)
        self.roi_button = QPushButton()
        self.roi_button.setCheckable(True)
        self.roi_button.clicked.connect(self._toggle_roi_mode)
        detection_layout.addWidget(self.roi_button)
        self.apply_button = QPushButton()
        self.apply_button.clicked.connect(self._apply_to_scene)
        self.apply_button.setEnabled(False)
        detection_layout.addWidget(self.apply_button)
        self.status_label = QLabel()
        detection_layout.addWidget(self.status_label)
        self.validation_label = QLabel()
        self.validation_label.setObjectName("mask_polygon_validation")
        self.validation_label.setWordWrap(True)
        detection_layout.addWidget(self.validation_label)
        control_layout.addWidget(self.detection_group)
        control_layout.addStretch()

        controls_scroll = QScrollArea(self)
        controls_scroll.setObjectName("mask_controls_scroll")
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        controls_scroll.setMinimumWidth(390)
        controls_scroll.setMaximumWidth(470)
        controls_scroll.setWidget(control_panel)
        main_layout.addWidget(controls_scroll, 0)
        viewer_container = QWidget()
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.addWidget(self.viewer)
        main_layout.addWidget(viewer_container, 1)

        self.viewer.viewChanged.connect(self._update_info_labels)
        self.viewer.polygonSelected.connect(self._on_polygon_selected)
        self.viewer.roiSelected.connect(self._on_roi_selected)
        self.viewer.polygonsChanged.connect(self._on_overlay_polygons_changed)
        logger.debug("UI setup completed")

    def _setup_explicit_view_modes(self) -> None:
        """Expose all X-Ray modes in the scrollable control panel."""
        self.view_mode_group = QGroupBox()
        self.view_mode_group.setObjectName("mask_view_mode_group")
        layout = QHBoxLayout(self.view_mode_group)
        group = QButtonGroup(self)
        group.setExclusive(True)
        self.view_mode_button_group = group
        for index in range(4):
            button = QPushButton()
            button.setObjectName(f"mask_view_mode_{index}")
            button.setCheckable(True)
            button.setAutoDefault(False)
            group.addButton(button, index)
            layout.addWidget(button)
            self.view_mode_buttons.append(button)
        group.idClicked.connect(self._on_explicit_view_mode)
        self.view_mode_buttons[0].setChecked(True)

    def _setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        for preset_id in self.PRESET_ORDER:
            action = self.toolbar.addAction("")
            action.setData(preset_id)
            action.triggered.connect(
                lambda checked=False, name=preset_id: self._apply_preset(name)
            )
            self.preset_actions[preset_id] = action
        self.toolbar.addSeparator()
        self.view_mode_label = QLabel()
        self.toolbar.addWidget(self.view_mode_label)
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItem("", 0)
        self.view_mode_combo.addItem("", 1)
        self.view_mode_combo.addItem("", 2)
        self.view_mode_combo.addItem("", 3)
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        self.toolbar.addWidget(self.view_mode_combo)
        self.perf_label = QLabel()
        self.toolbar.addWidget(self.perf_label)

    def _setup_layer_controls(self):
        self.layer_controls = QGroupBox()
        layout = QVBoxLayout(self.layer_controls)
        for layer_id in ("Sobel", "Canny", "Threshold", "Watershed", "Polygons"):
            checkbox = QCheckBox()
            checkbox.setChecked(layer_id == "Polygons")
            checkbox.stateChanged.connect(
                lambda state, layer=layer_id: self._on_layer_changed(layer, state)
            )
            self.layer_checkboxes[layer_id] = checkbox
            layout.addWidget(checkbox)
        opacity_layout = QHBoxLayout()
        self.opacity_label = QLabel()
        opacity_layout.addWidget(self.opacity_label)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        layout.addLayout(opacity_layout)

    def _setup_parameter_controls(self):
        self.param_controls = QGroupBox()
        layout = QVBoxLayout(self.param_controls)
        params = [
            ("min_area", 1.0, 1000.0, 100.0),
            ("rdp_epsilon", 0.1, 10.0, 2.0),
            ("canny_threshold1", 10, 500, 100),
            ("canny_threshold2", 10, 500, 200),
        ]
        for param_name, min_val, max_val, default in params:
            self._add_parameter_row(layout, param_name, min_val, max_val, default)

        self.advanced_toggle = QCheckBox()
        self.advanced_toggle.stateChanged.connect(self._toggle_advanced_params)
        layout.addWidget(self.advanced_toggle)
        self.advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_widget)
        advanced_params = [
            ("block_size", 3, 31, 11),
            ("threshold_c", -10, 10, 2),
            ("base_eps", 0.1, 5.0, 2.0),
            ("curvature_factor", 0.1, 2.0, 1.0),
        ]
        for param_name, min_val, max_val, default in advanced_params:
            self._add_parameter_row(
                advanced_layout, param_name, min_val, max_val, default
            )
        self.advanced_widget.setVisible(False)
        layout.addWidget(self.advanced_widget)

    def _add_parameter_row(self, parent_layout, name, minimum, maximum, default):
        row = QHBoxLayout()
        label = QLabel()
        self.param_labels[name] = label
        row.addWidget(label)
        widget: QSpinBox | QDoubleSpinBox
        if isinstance(minimum, float):
            widget = QDoubleSpinBox()
            widget.setSingleStep(0.1)
        else:
            widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setValue(default)
        widget.valueChanged.connect(
            lambda value, p=name: self._on_param_changed(p, value)
        )
        self.param_widgets[name] = widget
        row.addWidget(widget)
        parent_layout.addLayout(row)

    def _localized_polygon_reason(self, reason: str) -> str:
        if self.current_lang != "pt":
            return reason
        translations = {
            "fewer than 3 distinct vertices": "menos de 3 vértices distintos",
            "contains duplicate consecutive vertices": "contém vértices consecutivos duplicados",
            "has zero area": "tem área zero",
            "has self-intersecting edges": "possui arestas que se cruzam",
            "does not satisfy the scene polygon contract": "não atende ao contrato geométrico da cena",
        }
        return translations.get(reason, reason)

    def _update_polygon_validation_feedback(self) -> None:
        if self.viewer._overlay_polygons is not self._last_polygons:
            self.viewer.set_overlay_polygons(self._last_polygons)
        if not self._last_polygons:
            self.validation_label.clear()
            self.apply_button.setEnabled(False)
            return
        valid_count, invalid_count = self.viewer._refresh_polygon_validation()
        count = len(self._last_polygons)
        lines = [
            self.t["validation_summary"].format(
                count=count, valid=valid_count, invalid=invalid_count
            )
        ]
        if invalid_count:
            for index, polygon_data in enumerate(self._last_polygons):
                if isinstance(polygon_data, dict) and polygon_data.get("is_valid") is False:
                    reason = self._localized_polygon_reason(
                        str(polygon_data.get("validation_error", "invalid geometry"))
                    )
                    lines.append(self.t["invalid_polygon"].format(index=index + 1, reason=reason))
            lines.append(self.t["invalid_hint"])
        else:
            lines.append(self.t["valid_hint"])
        self.validation_label.setText("\n".join(lines))
        self.apply_button.setEnabled(invalid_count == 0)

    def _on_overlay_polygons_changed(self) -> None:
        self._update_polygon_validation_feedback()


    def update_language(self, lang: str):
        self.current_lang = lang if lang in self.TRANSLATIONS else "en"
        t = self.t
        self.setWindowTitle(t["window_title"])
        self.toolbar.setWindowTitle(t["toolbar"])
        for preset_id, action in self.preset_actions.items():
            label = t[self.PRESET_TEXT_KEYS[preset_id]]
            action.setText(t["detection_action"].format(preset=label))
        self.view_mode_label.setText(t["view_mode"])
        self.view_mode_group.setTitle(t["view_mode"])
        view_keys = (
            "view_original",
            "view_xray_1",
            "view_xray_2",
            "view_xray_3",
        )
        for index, key in enumerate(view_keys):
            self.view_mode_combo.setItemText(index, t[key])
            self.view_mode_buttons[index].setText(t[key])
        self.layer_controls.setTitle(t["layer_visualization"])
        for layer_id, checkbox in self.layer_checkboxes.items():
            checkbox.setText(t[self.LAYER_TEXT_KEYS[layer_id]])
        self.opacity_label.setText(t["opacity"])
        self.param_controls.setTitle(t["detection_parameters"])
        self.processing_source_label.setText(t["processing_source"])
        self.processing_source_combo.setItemText(0, t["source_original"])
        self.processing_source_combo.setItemText(1, t["source_active_view"])
        for param_name, label in self.param_labels.items():
            label.setText(t[param_name] + ":")
        self.advanced_toggle.setText(t["advanced"])
        self.view_group.setTitle(t["view_controls"])
        self.fit_button.setText(t["fit_window"])
        self.zoom_text_label.setText(t["zoom"])
        self.pan_x_label.setText(t["pan_x"])
        self.pan_y_label.setText(t["pan_y"])
        self.detection_group.setTitle(t["detection_controls"])
        self.preset_label.setText(t["preset"])
        current_id = self.preset_combo.currentData()
        for index, preset_id in enumerate(self.PRESET_ORDER):
            self.preset_combo.setItemText(index, t[self.PRESET_TEXT_KEYS[preset_id]])
        restore_index = self.preset_combo.findData(current_id)
        if restore_index >= 0:
            self.preset_combo.setCurrentIndex(restore_index)
        self.detect_button.setText(t["processing"] if self._thread else t["detect"])
        self.roi_button.setText(t["select_roi"])
        self.apply_button.setText(t["apply"])
        if not self._last_polygons and not self._thread:
            self.status_label.setText(t["ready"])
        self._refresh_image_info_label()
        self._update_info_labels()
        self._update_performance_label()
        self._update_polygon_validation_feedback()

    def _refresh_image_info_label(self):
        image = getattr(self.scene, "image", None)
        if image is not None:
            height, width = image.shape[:2]
            self.info_label.setText(
                self.t["image_info"].format(width=width, height=height)
            )
        else:
            self.info_label.setText(self.t["no_image_loaded"])

    def _load_scene_image(self):
        image = getattr(self.scene, "image", None)
        if image is not None:
            self.viewer.set_numpy_image(image)
            self._refresh_image_info_label()
            self.viewer.reset_view()
        else:
            self.viewer.set_numpy_image(None)
            self._refresh_image_info_label()

    def _fit_to_window(self):
        self.viewer.reset_view()
        self._update_info_labels()

    def _update_info_labels(self):
        zoom = self.viewer.get_zoom()
        pan_x, pan_y = self.viewer.get_pan()
        self.zoom_label.setText(self.t["zoom_value"].format(value=zoom))
        self.pan_label.setText(self.t["pan_value"].format(x=pan_x, y=pan_y))
        self.zoom_spin.blockSignals(True)
        self.zoom_spin.setValue(zoom * 100)
        self.zoom_spin.blockSignals(False)
        self.pan_x_spin.blockSignals(True)
        self.pan_x_spin.setValue(int(pan_x))
        self.pan_x_spin.blockSignals(False)
        self.pan_y_spin.blockSignals(True)
        self.pan_y_spin.setValue(int(pan_y))
        self.pan_y_spin.blockSignals(False)

    def _on_zoom_changed(self, value):
        self.viewer.set_zoom(value / 100.0)

    def _on_pan_changed(self, *_args):
        self.viewer.set_pan(
            float(self.pan_x_spin.value()), float(self.pan_y_spin.value())
        )

    def _selected_preset_id(self):
        preset_id = self.preset_combo.currentData()
        return preset_id if preset_id in DETECTION_PRESETS else "Basic"

    def _get_detection_image(self) -> Optional[np.ndarray]:
        use_active_view = self.processing_source_combo.currentData() == "active_view"
        return self.viewer.get_processing_image(use_active_view=use_active_view)

    def _on_preset_changed(self, *_args):
        preset_id = self._selected_preset_id()
        self._apply_preset_params(DETECTION_PRESETS[preset_id]["params"])
        self._update_performance_label()

    def _update_performance_label(self):
        if self._thread:
            return
        preset = DETECTION_PRESETS[self._selected_preset_id()]
        self.perf_label.setText(
            self.t["performance"].format(
                runtime=preset["estimated_runtime"], count=preset["expected_polygons"]
            )
        )

    def _apply_preset(self, preset_id):
        index = self.preset_combo.findData(preset_id)
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)
        self._on_preset_changed()

    def _apply_preset_params(self, params):
        for param_name, value in params.items():
            if param_name in self.param_widgets:
                self.param_widgets[param_name].setValue(value)
            self.params[param_name] = value

    def _on_view_mode_changed(self, index: int) -> None:
        self.viewer.set_display_mode(index)
        if 0 <= index < len(self.view_mode_buttons):
            self.view_mode_buttons[index].setChecked(True)

    def _on_explicit_view_mode(self, index: int) -> None:
        self.view_mode_combo.setCurrentIndex(index)

    def _on_layer_changed(self, layer_name, _state):
        self._update_layer_overlays()

    def _update_layer_overlays(self):
        enabled_layers = [
            layer
            for layer, checkbox in self.layer_checkboxes.items()
            if checkbox.isChecked()
        ]
        self._layer_overlays = {layer: True for layer in enabled_layers}
        self.viewer.set_layer_overlays(
            self._layer_overlays, self.opacity_slider.value() / 100.0
        )

    def _on_opacity_changed(self, value):
        self.viewer.set_layer_overlays(self._layer_overlays, value / 100.0)

    def _on_param_changed(self, param_name, value):
        self.params[param_name] = value

    def _toggle_advanced_params(self, state):
        self.advanced_widget.setVisible(state == Qt.CheckState.Checked.value)

    def _run_detection(self):
        image = self._get_detection_image()
        if image is None:
            QMessageBox.warning(
                self, self.t["no_image_title"], self.t["no_image_message"]
            )
            return
        preset_id = self._selected_preset_id()
        if preset_id == "GrabCut" and self._roi is None:
            QMessageBox.warning(self, self.t["error"], self.t["select_roi"])
            return
        self.detect_button.setEnabled(False)
        self.detect_button.setText(self.t["processing"])
        self.status_label.setText(self.t["running"])
        self.setCursor(Qt.CursorShape.WaitCursor)
        mode = DETECTION_PRESETS[preset_id]["mode"]
        thread = QThread()
        detection_params: Dict[str, Any] = dict(self.params)
        if preset_id == "GrabCut":
            detection_params["roi"] = self._roi
        worker = DetectionWorker(image, mode, detection_params)
        self._thread = thread
        self._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_detection_finished)
        worker.error.connect(self._on_detection_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_detection_thread)
        thread.start()

    def _clear_detection_thread(self):
        self._thread = None
        self._worker = None
        self._update_performance_label()

    def _on_detection_finished(self, polygons):
        self._last_polygons = polygons
        self.viewer.set_overlay_polygons(polygons)
        count = len(polygons)
        self.status_label.setText(self.t["found"].format(count=count))
        self._update_polygon_validation_feedback()
        self.detect_button.setEnabled(True)
        self.detect_button.setText(self.t["detect"])
        self.unsetCursor()

    def _on_detection_error(self, err_msg):
        self.status_label.setText(self.t["detection_failed"])
        QMessageBox.critical(
            self, self.t["error"], self.t["detection_error"].format(error=err_msg)
        )
        self.detect_button.setEnabled(True)
        self.detect_button.setText(self.t["detect"])
        self.unsetCursor()

    def _apply_to_scene(self):
        if not self._last_polygons:
            return

        self._update_polygon_validation_feedback()
        if not self.apply_button.isEnabled():
            return

        manager = getattr(self.scene, "cmd", None)
        if manager is None:
            QMessageBox.warning(
                self,
                self.t["apply_error_title"],
                self.t["apply_error"].format(
                    error="Undo/Redo command history is unavailable."
                ),
            )
            return

        try:
            from src.core.commands import (
                AddPolygonCommand,
                Command,
                CommandStatus,
                CompositeCommand,
            )

            commands: List[Command] = []
            for index, poly_data in enumerate(self._last_polygons):
                polygon = (
                    poly_data.get("polygon")
                    if isinstance(poly_data, dict)
                    else poly_data
                )
                if not polygon or len(polygon) < 3:
                    QMessageBox.warning(
                        self,
                        self.t["apply_error_title"],
                        self.t["apply_error"].format(
                            error=f"Detected polygon {index + 1} is invalid."
                        ),
                    )
                    return
                commands.append(AddPolygonCommand(polygon))

            composite = CompositeCommand(commands)
            result = manager.execute(composite, self.scene)
            if not result.changed:
                message = result.message or "The polygon batch was not applied."
                if result.status is CommandStatus.FAILED:
                    QMessageBox.critical(
                        self,
                        self.t["apply_error_title"],
                        self.t["apply_error"].format(error=message),
                    )
                else:
                    QMessageBox.warning(
                        self,
                        self.t["apply_error_title"],
                        self.t["apply_error"].format(error=message),
                    )
                return

            QMessageBox.information(
                self,
                self.t["success"],
                self.t["added"].format(count=len(commands)),
            )
            self.close()
        except Exception as exc:
            logger.error("Failed to apply polygons: %s", exc, exc_info=True)
            QMessageBox.critical(
                self,
                self.t["apply_error_title"],
                self.t["apply_error"].format(error=exc),
            )

    def _toggle_roi_mode(self, checked: bool) -> None:
        self.viewer.set_roi_mode(checked)
        if checked:
            self.status_label.setText(self.t["select_roi"])

    def _on_roi_selected(self, roi: Tuple[int, int, int, int]) -> None:
        self._roi = roi
        x, y, width, height = roi
        self.status_label.setText(
            self.t["roi_selected"].format(x=x, y=y, width=width, height=height)
        )
        self.roi_button.setChecked(False)
        self.viewer.set_roi_mode(False)

    def _on_polygon_selected(self, index: int):
        if index >= 0:
            self.status_label.setText(self.t["selected"].format(index=index + 1))
        else:
            self.status_label.setText(self.t["ready"])
