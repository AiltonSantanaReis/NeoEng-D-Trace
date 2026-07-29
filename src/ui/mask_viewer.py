# src/ui/mask_viewer.py
"""
Mask Viewer widget with pan/zoom capabilities for visualizing images and masks.
"""

import numpy as np
import logging
from typing import Optional, Tuple, Callable

from PySide6.QtWidgets import (
    QWidget,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QToolBar,
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QThread, QObject
from PySide6.QtGui import (
    QPainter,
    QImage,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
    QColor,
    QPen,
    QPolygonF,
)

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
        },
        "estimated_runtime": "0.1-0.5s",
        "expected_polygons": "10-50",
    },
    "Perfect": {
        "mode": "perfect",
        "params": {
            "downscale": 1.0,
            "base_eps": 2.0,
            "curvature_factor": 1.0,
            "min_area": 100.0,
            "decompose_convex": False,
            "watershed_distance": 10,
        },
        "estimated_runtime": "0.5-2.0s",
        "expected_polygons": "5-20",
    },
    "Enhanced": {
        "mode": "enhanced",
        "params": {
            "downscale": 1.0,
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
    from PIL import Image as PILImage
    from PIL.ImageQt import ImageQt

    HAS_PIL = True
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
        self._qimage_cache: Optional[QImage] = None
        
        # Overlay Polygons (Visualization)
        self._overlay_polygons = []
        self._selected_polygon_index = -1  # Index of selected polygon, -1 for none

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
            polygon = poly_data.get("polygon") if isinstance(poly_data, dict) else poly_data
            if polygon and len(polygon) >= 3:
                qpoints = [QPointF(float(p[0]), float(p[1])) for p in polygon]
                qpoly = QPolygonF(qpoints)
                if qpoly.containsPoint(image_point, Qt.FillRule.OddEvenFill):
                    return i
        return -1

    def set_numpy_image(self, image: np.ndarray):
        """Set the image to display from numpy array."""
        self._image = image.copy() if image is not None else None
        self._qimage_cache = None  # Invalidate cache
        self.update()
    
    def get_numpy_image(self) -> Optional[np.ndarray]:
        """Get the current image as numpy array."""
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

    def set_view_transform(
        self, zoom: float, pan_x: float, pan_y: float
    ) -> None:
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
                self._zoom = max(zoom_x, zoom_y)  # Usar o maior para preencher completamente

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
             if (not self._suppress_tool_events and self.tool_handler is not None):
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
        if self._panning:
            delta = event.position() - self._pan_start_pos
            self._pan_x = self._pan_start_offset.x() + delta.x()
            self._pan_y = self._pan_start_offset.y() + delta.y()
            self.viewChanged.emit()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._panning:
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
            
            # Draw Overlay Polygons
            if self._overlay_polygons:
                for i, poly_data in enumerate(self._overlay_polygons):
                    # Handle both dict and object formats
                    polygon = poly_data.get("polygon") if isinstance(poly_data, dict) else poly_data
                    
                    if polygon and len(polygon) >= 3:
                        # Convert points to QPointF
                        qpoints = [QPointF(float(p[0]), float(p[1])) for p in polygon]
                        qpoly = QPolygonF(qpoints)
                        
                        # Set style based on selection
                        if i == self._selected_polygon_index:
                            pen = QPen(QColor(255, 255, 0), 3)  # Yellow outline for selected
                            pen.setCosmetic(True)
                            painter.setPen(pen)
                            painter.setBrush(QColor(255, 255, 0, 80))  # Semi-transparent yellow fill
                        else:
                            pen = QPen(QColor(0, 255, 0), 2)  # Green outline
                            pen.setCosmetic(True)
                            painter.setPen(pen)
                            painter.setBrush(QColor(0, 255, 0, 50))  # Semi-transparent green fill
                        
                        painter.drawPolygon(qpoly)
            
            painter.restore()

    def _get_qimage(self) -> Optional[QImage]:
        if self._image is None:
            return None
        if self._qimage_cache is not None:
            return self._qimage_cache

        try:
            if HAS_CV2:
                # Ensure RGB
                if len(self._image.shape) == 3 and self._image.shape[2] == 3:
                    rgb = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
                else:
                    rgb = self._image
            else:
                rgb = self._image

            height, width = rgb.shape[:2]
            
            if len(rgb.shape) == 2:
                fmt = QImage.Format.Format_Grayscale8
                step = rgb.strides[0]
            else:
                fmt = QImage.Format.Format_RGB888
                step = rgb.strides[0]

            self._qimage_cache = QImage(rgb.data, width, height, step, fmt)
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
        },
        "pt": {
            "window_title": "Visualizador de Máscara - Raio-X de Detecção Automática",
            "toolbar": "Ferramentas do Visualizador de Máscara",
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
        },
    }

    PRESET_ORDER = ("Basic", "Perfect", "Enhanced")
    PRESET_TEXT_KEYS = {
        "Basic": "preset_basic",
        "Perfect": "preset_perfect",
        "Enhanced": "preset_enhanced",
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
            "canny_thresh1": 50,
            "canny_thresh2": 150,
            "chaikin_iterations": 0,
            "fit_bezier": False,
            "morph_kernel_size": 1,
            "detect_holes": False,
        }

        self.resize(1200, 800)
        self.viewer = MaskViewer(self)
        self._last_polygons = []
        self._thread = None
        self._worker = None
        self._current_mask = None
        self._layer_overlays = {}
        self.param_widgets = {}
        self.param_labels = {}
        self.layer_checkboxes = {}
        self.preset_actions = {}

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

        self.detect_button = QPushButton()
        self.detect_button.clicked.connect(self._run_detection)
        detection_layout.addWidget(self.detect_button)
        self.apply_button = QPushButton()
        self.apply_button.clicked.connect(self._apply_to_scene)
        self.apply_button.setEnabled(False)
        detection_layout.addWidget(self.apply_button)
        self.status_label = QLabel()
        detection_layout.addWidget(self.status_label)
        control_layout.addWidget(self.detection_group)
        control_layout.addStretch()

        main_layout.addWidget(control_panel, 0)
        viewer_container = QWidget()
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.addWidget(self.viewer)
        main_layout.addWidget(viewer_container, 1)

        self.viewer.viewChanged.connect(self._update_info_labels)
        self.viewer.polygonSelected.connect(self._on_polygon_selected)
        logger.debug("UI setup completed")

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
            self._add_parameter_row(advanced_layout, param_name, min_val, max_val, default)
        self.advanced_widget.setVisible(False)
        layout.addWidget(self.advanced_widget)

    def _add_parameter_row(self, parent_layout, name, minimum, maximum, default):
        row = QHBoxLayout()
        label = QLabel()
        self.param_labels[name] = label
        row.addWidget(label)
        if isinstance(minimum, float):
            widget = QDoubleSpinBox()
            widget.setSingleStep(0.1)
        else:
            widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setValue(default)
        widget.valueChanged.connect(lambda value, p=name: self._on_param_changed(p, value))
        self.param_widgets[name] = widget
        row.addWidget(widget)
        parent_layout.addLayout(row)

    def update_language(self, lang: str):
        self.current_lang = lang if lang in self.TRANSLATIONS else "en"
        t = self.t
        self.setWindowTitle(t["window_title"])
        self.toolbar.setWindowTitle(t["toolbar"])
        for preset_id, action in self.preset_actions.items():
            label = t[self.PRESET_TEXT_KEYS[preset_id]]
            action.setText(t["detection_action"].format(preset=label))
        self.layer_controls.setTitle(t["layer_visualization"])
        for layer_id, checkbox in self.layer_checkboxes.items():
            checkbox.setText(t[self.LAYER_TEXT_KEYS[layer_id]])
        self.opacity_label.setText(t["opacity"])
        self.param_controls.setTitle(t["detection_parameters"])
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
        self.apply_button.setText(t["apply"])
        if not self._last_polygons and not self._thread:
            self.status_label.setText(t["ready"])
        self._refresh_image_info_label()
        self._update_info_labels()
        self._update_performance_label()

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
        self.viewer.set_pan(float(self.pan_x_spin.value()), float(self.pan_y_spin.value()))

    def _selected_preset_id(self):
        preset_id = self.preset_combo.currentData()
        return preset_id if preset_id in DETECTION_PRESETS else "Basic"

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

    def _on_layer_changed(self, layer_name, _state):
        self._update_layer_overlays()

    def _update_layer_overlays(self):
        enabled_layers = [
            layer for layer, checkbox in self.layer_checkboxes.items() if checkbox.isChecked()
        ]
        self._layer_overlays = {layer: True for layer in enabled_layers}
        self.viewer.update()

    def _on_opacity_changed(self, _value):
        self.viewer.update()

    def _on_param_changed(self, param_name, value):
        self.params[param_name] = value

    def _toggle_advanced_params(self, state):
        self.advanced_widget.setVisible(state == Qt.CheckState.Checked.value)

    def _run_detection(self):
        image = getattr(self.scene, "image", None)
        if image is None:
            QMessageBox.warning(self, self.t["no_image_title"], self.t["no_image_message"])
            return
        self.detect_button.setEnabled(False)
        self.detect_button.setText(self.t["processing"])
        self.status_label.setText(self.t["running"])
        self.setCursor(Qt.CursorShape.WaitCursor)
        preset_id = self._selected_preset_id()
        mode = DETECTION_PRESETS[preset_id]["mode"]
        self._thread = QThread()
        self._worker = DetectionWorker(image, mode, dict(self.params))
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_detection_finished)
        self._worker.error.connect(self._on_detection_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.error.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_detection_thread)
        self._thread.start()

    def _clear_detection_thread(self):
        self._thread = None
        self._worker = None
        self._update_performance_label()

    def _on_detection_finished(self, polygons):
        self._last_polygons = polygons
        self.viewer.set_overlay_polygons(polygons)
        count = len(polygons)
        self.status_label.setText(self.t["found"].format(count=count))
        self.apply_button.setEnabled(count > 0)
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
        try:
            from src.core.commands import AddPolygonCommand

            added_count = 0
            for index, poly_data in enumerate(self._last_polygons):
                polygon = poly_data.get("polygon") if isinstance(poly_data, dict) else poly_data
                if polygon and len(polygon) >= 3:
                    command = AddPolygonCommand(polygon)
                    if hasattr(self.scene, "cmd") and self.scene.cmd:
                        self.scene.cmd.execute(command, self.scene)
                    else:
                        self.scene.add_polygon(polygon)
                    added_count += 1
                else:
                    logger.warning("Skipping invalid polygon %s", index)
            QMessageBox.information(
                self, self.t["success"], self.t["added"].format(count=added_count)
            )
            self.close()
        except Exception as exc:
            logger.error("Failed to apply polygons: %s", exc, exc_info=True)
            QMessageBox.critical(
                self,
                self.t["apply_error_title"],
                self.t["apply_error"].format(error=exc),
            )

    def _on_polygon_selected(self, index: int):
        if index >= 0:
            self.status_label.setText(self.t["selected"].format(index=index + 1))
        else:
            self.status_label.setText(self.t["ready"])
