from __future__ import annotations

import math
from dataclasses import dataclass

# src/ui/canvas_view.py
from typing import Any, Callable, Optional, Tuple

from PySide6.QtCore import QObject, QPointF, QRectF, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPolygonF,
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import QMenu, QMessageBox, QPushButton, QWidget

from src.core.commands import (
    AddPolygonCommand,
    ClearSceneCommand,
    CommandStatus,
    DeleteObjectCommand,
    ToggleCollisionCommand,
)
from src.core.logger import logger
from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scenario_preview import (
    ScenarioOverlayGeometry,
    ScenarioPreviewLayer,
    build_overlay_geometry,
    project_layer_points,
)
from src.core.snapping import SnapSettings
from src.core.transform_gesture import TransformGestureTransaction
from src.ui.image_conversion import to_qimage

# Proteção de importação caso ViewProcessor não esteja implementado ainda
VIEW_PROCESSOR_CLASS: Optional[type[Any]]
try:
    from src.core.view_processor import ViewProcessor as _ViewProcessor

    VIEW_PROCESSOR_CLASS = _ViewProcessor
except ImportError:
    VIEW_PROCESSOR_CLASS = None

# Tenta importar o Gizmo, mas define fallback se não existir
TRANSFORM_GIZMO_CLASS: Optional[type[Any]]
try:
    from src.ui.gizmo import TransformGizmo as _TransformGizmo

    TRANSFORM_GIZMO_CLASS = _TransformGizmo
except ImportError:
    TRANSFORM_GIZMO_CLASS = None


class XrayWorkerSignals(QObject):
    finished = Signal(QImage, int)  # QImage and mode
    progress = Signal(int)  # Progresso da geração do raio-x


class XrayWorker(QRunnable):
    def __init__(self, image_array, mode):
        super().__init__()
        self.image_array = image_array.copy() if image_array is not None else None
        self.mode = mode
        self.signals = XrayWorkerSignals()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        if VIEW_PROCESSOR_CLASS is None:
            return

        # Simulate progress for demonstration
        self.signals.progress.emit(10)
        if self._cancelled:
            return

        try:
            # Map view modes to xray modes
            xray_mode = 1  # default
            if self.mode == CanvasView.VIEW_XRAY_1:
                xray_mode = 1
            elif self.mode == CanvasView.VIEW_XRAY_2:
                xray_mode = 2
            elif self.mode == CanvasView.VIEW_XRAY_3:
                xray_mode = 3

            array_generator = getattr(
                VIEW_PROCESSOR_CLASS,
                "generate_xray_array",
                None,
            )
            if array_generator is None:
                qimage = VIEW_PROCESSOR_CLASS.generate_xray(
                    self.image_array,
                    xray_mode,
                )
            else:
                qimage = to_qimage(array_generator(self.image_array, xray_mode))
        except Exception as e:
            logger.error(f"XRay generation failed: {e}")
            return

        self.signals.progress.emit(90)
        if self._cancelled:
            return

        self.signals.progress.emit(100)
        self.signals.finished.emit(qimage, self.mode)


@dataclass
class ToolInterface:
    on_mouse_press: Optional[Callable] = None
    on_mouse_move: Optional[Callable] = None
    on_mouse_release: Optional[Callable] = None
    on_double_click: Optional[Callable] = None
    on_cancel: Optional[Callable] = None
    on_key_press: Optional[Callable] = None
    on_undo: Optional[Callable] = None
    on_redo: Optional[Callable] = None
    draw_overlay: Optional[Callable] = None
    update_language: Optional[Callable] = None


class CanvasView(QWidget):
    viewport_state_changed = Signal(str)

    VIEW_LIT = 0
    VIEW_XRAY_1 = 1  # Sobel gradients
    VIEW_XRAY_2 = 2  # Canny edges
    VIEW_XRAY_3 = 3  # Laplacian edges
    VIEW_COLLISION = 4

    def _selected_object_ids(self):
        selected_id = getattr(self.model, "selected_id", None)
        if selected_id is None:
            return []
        selected_ids = list(getattr(self.model, "selected_ids", []) or [])
        if selected_ids:
            valid = [
                oid for oid in selected_ids if oid in getattr(self.model, "objects", {})
            ]
            return valid if selected_id in valid else []
        return (
            [selected_id] if selected_id in getattr(self.model, "objects", {}) else []
        )

    def _selection_anchor_image(self, object_ids=None):
        object_ids = (
            object_ids if object_ids is not None else self._selected_object_ids()
        )
        if len(object_ids) == 1:
            position = getattr(self.model.objects[object_ids[0]], "position", None)
            if position is not None and len(position) >= 2:
                return QPointF(float(position[0]), float(position[1]))
        polygons = [
            getattr(self.model.objects[oid], "polygon", []) for oid in object_ids
        ]
        points = [point for polygon in polygons for point in polygon]
        if not points:
            return None
        min_x = min(float(point[0]) for point in points)
        max_x = max(float(point[0]) for point in points)
        min_y = min(float(point[1]) for point in points)
        max_y = max(float(point[1]) for point in points)
        return QPointF((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)

    def _get_image_center_screen(self):
        anchor = self._selection_anchor_image()
        return (
            self.image_to_widget(anchor.x(), anchor.y()) if anchor is not None else None
        )

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self._view_mode = self.VIEW_LIT
        self._qimage_lit = None
        self._qimage_xray_1 = None
        self._qimage_xray_2 = None
        self._qimage_xray_3 = None
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._dragging = False
        self._last_mouse = QPointF()

        # Flags de Estado
        self._preview_mode = False  # Modo de exportação (esconde UI helpers)
        self._scenario_preview_enabled = False
        self._scenario_overlays_visible = False
        self._scenario_overlay_aspect = (16, 9)
        self._scenario_safe_fraction = 0.9
        self._scenario_camera: Optional[OrthographicCamera] = None
        self._scenario_layers: tuple[ScenarioPreviewLayer, ...] = ()
        self._scenario_overlay_geometry: Optional[ScenarioOverlayGeometry] = None

        # --- Configurações Críticas de Interação ---
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setMinimumSize(400, 300)

        # Gizmo System
        self.gizmo = None  # Lazy loaded
        self._gizmo_active = False
        self._gizmo_start_mouse = QPointF()
        self._gizmo_enabled = False
        self._gizmo_transaction: Optional[TransformGestureTransaction] = None
        self._gizmo_total_delta = QPointF()
        self._gizmo_operation = 0
        self._gizmo_anchor_image = None
        self._gizmo_y_screen_direction = -1.0
        self._gizmo_press_vector = QPointF()
        self._gizmo_feedback = ""

        self._tool = None
        self._current_polygon = []
        # Vertex snapping is opt-in so existing pixel coordinates remain unchanged.
        self._vertex_snap_settings = SnapSettings()

        # Estilos de Desenho
        self._pen_poly = QPen(QColor(0, 255, 0), 2)
        self._pen_poly.setCosmetic(True)
        self._brush_poly = QColor(0, 255, 0, 50)

        self._pen_selected = QPen(QColor(255, 100, 100), 3)
        self._pen_selected.setCosmetic(True)
        self._brush_selected = QColor(255, 100, 100, 60)

        self._pen_preview = QPen(QColor(0, 255, 255), 2)
        self._pen_preview.setCosmetic(True)

        self._collision_overlay = None
        self._temp_mask = None
        self._flash_color = None
        self.current_lang = "en"
        self.translations = {"en": {"gizmo": "Gizmo"}, "pt": {"gizmo": "Eixo"}}

        # Gizmo Toggle Button
        self.gizmo_toggle = QPushButton(
            self.translations[self.current_lang]["gizmo"], self
        )
        self.gizmo_toggle.setCheckable(True)
        self.gizmo_toggle.setChecked(False)
        self.gizmo_toggle.clicked.connect(self._toggle_gizmo)
        self.gizmo_toggle.setObjectName("gizmo_toggle")
        self.gizmo_toggle.setMinimumWidth(92)
        self.gizmo_toggle.setToolTip("Toggle interactive transform gizmo")

        self.threadpool = QThreadPool()

        if hasattr(self.model, "subscribe"):
            self.model.subscribe(self.update_image)

        if getattr(self.model, "image", None) is not None:
            self.update_image()

    def contextMenuEvent(self, event):
        if self._scenario_preview_enabled:
            event.accept()
            return
        if self._tool or len(self._current_polygon) > 0:
            return

        pos = event.pos()
        transform_inv, ok = self.get_transform().inverted()
        if not ok:
            return
        img_pt = transform_inv.map(QPointF(pos))

        clicked_obj_id = self._find_object_at(img_pt)

        menu = QMenu(self)

        if clicked_obj_id:
            label = menu.addAction(f"Selected: {clicked_obj_id[:8]}...")
            label.setEnabled(False)
            menu.addSeparator()

            act_focus = menu.addAction("🔍 Focus Object")
            act_focus.triggered.connect(lambda: self.focus_on_object(clicked_obj_id))

            # Forma de colisão
            has_collision = hasattr(
                self.model, "has_collision"
            ) and self.model.has_collision(clicked_obj_id)
            collision_text = (
                "Disable Collision Shape" if has_collision else "Enable Collision Shape"
            )
            collision_action = menu.addAction(f"⚛️ {collision_text}")
            collision_action.triggered.connect(
                lambda: self._toggle_collision(clicked_obj_id)
            )

            menu.addSeparator()

            act_del = menu.addAction("❌ Delete Object")
            act_del.triggered.connect(lambda: self._delete_object(clicked_obj_id))

            menu.addSeparator()

        act_fit = menu.addAction("Fit Image (F)")
        act_fit.triggered.connect(self.fit_to_window)

        act_100 = menu.addAction("Zoom 100%")
        act_100.triggered.connect(lambda: self.set_zoom(1.0))

        menu.addSeparator()

        act_clean = menu.addAction("🗑️ Clean All Polygons")
        act_clean.triggered.connect(self.clean_all)

        menu.exec(event.globalPos())

    def _find_object_at(self, point: QPointF) -> Optional[str]:
        objects = getattr(self.model, "objects", {})
        for oid, obj in reversed(list(objects.items())):
            poly = getattr(obj, "polygon", [])
            if len(poly) < 3:
                continue
            poly_float = [QPointF(float(p[0]), float(p[1])) for p in poly]
            qpoly = QPolygonF(poly_float)
            if qpoly.containsPoint(point, Qt.FillRule.OddEvenFill):
                return oid
        return None

    def center_on_object(self, oid: str):
        obj = self.model.objects.get(oid)
        if obj and obj.polygon:
            self.center_on_polygon(obj.polygon, margin=50)

    def focus_on_object(self, oid: str):
        obj = self.model.objects.get(oid)
        if obj and obj.polygon:
            self.center_on_polygon(obj.polygon, margin=50)
            self.flash_effect(QColor(0, 255, 255, 100), 300)

    def _execute_edit_command(self, command):
        manager = getattr(self.model, "cmd", None)
        if manager is None:
            raise RuntimeError("Undo/Redo command history is unavailable.")

        result = manager.execute(command, self.model)
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self,
                "Edit Rejected",
                result.message or "The edit operation was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self,
                "Edit Failed",
                result.message or "The edit operation failed.",
            )
        return result

    def _commit_native_polygon(self, polygon) -> Optional[str]:
        command = AddPolygonCommand(list(polygon))
        try:
            result = self._execute_edit_command(command)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Polygon Creation Unavailable",
                str(exc),
            )
            return None
        if result.changed and command.object_id is not None:
            return str(command.object_id)
        return None

    def _toggle_collision(self, oid: str):
        try:
            result = self._execute_edit_command(ToggleCollisionCommand(oid))
            if result.changed:
                self.update()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Collision Toggle Error",
                str(exc),
            )

    def _toggle_physics(self, oid: str):
        """Compatibility adapter for historical callers."""
        self._toggle_collision(oid)

    def _delete_object(self, oid: str):
        try:
            result = self._execute_edit_command(DeleteObjectCommand(oid))
            if result.changed:
                self.update()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Delete Error",
                str(exc),
            )

    def _toggle_gizmo(self):
        self._gizmo_enabled = self.gizmo_toggle.isChecked()
        self.update()

    def set_vertex_snapping(
        self,
        enabled: bool,
        grid_size: int = 1,
        origin: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        """Enable pixel/grid snapping for manual vertex edits."""

        self._vertex_snap_settings = SnapSettings(
            enabled=bool(enabled), grid_size=grid_size, origin=origin
        )

    def snap_vertex_position(self, position: tuple[float, float]) -> tuple[int, int]:
        """Apply the current vertex snap settings to an image-space point."""

        return self._vertex_snap_settings.apply(position)

    def _distance_to_last_point(self, x: int, y: int) -> float:
        """Calculate distance from (x, y) to the last point in current polygon."""
        if not self._current_polygon:
            return float("inf")
        last_x, last_y = self._current_polygon[-1]
        return ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5

    def _reset_gizmo_interaction(self):
        self._gizmo_active = False
        self._gizmo_transaction = None
        self._gizmo_total_delta = QPointF()
        self._gizmo_operation = getattr(self.gizmo, "NONE", 0) if self.gizmo else 0
        self._gizmo_anchor_image = None
        self._gizmo_feedback = ""
        if self.gizmo:
            self.gizmo.active_axis = self.gizmo.NONE

    def _report_gizmo_result(self, result):
        if result is None:
            return
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self,
                "Gizmo Movement Rejected",
                result.message or "The movement was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self,
                "Gizmo Movement Failed",
                result.message or "The movement failed.",
            )

    def _begin_gizmo_object_gesture(self) -> bool:
        object_ids = self._selected_object_ids()
        if not object_ids:
            return False
        if getattr(self.model, "cmd", None) is None:
            QMessageBox.critical(
                self,
                "Gizmo Movement Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return False
        anchor = self._selection_anchor_image(object_ids)
        if anchor is None:
            return False
        try:
            self._gizmo_transaction = TransformGestureTransaction(
                self.model, object_ids
            )
            self._gizmo_anchor_image = (anchor.x(), anchor.y())
            self._gizmo_total_delta = QPointF()
            return True
        except Exception as exc:
            self._gizmo_transaction = None
            QMessageBox.critical(self, "Gizmo Movement Failed", str(exc))
            return False

    def _set_gizmo_feedback(
        self, translation=(0.0, 0.0), rotation=0.0, scale=(1.0, 1.0)
    ):
        ids = self._selected_object_ids()
        if not ids:
            self._gizmo_feedback = ""
            return
        obj = self.model.objects[ids[0]]
        position = getattr(obj, "position", (0.0, 0.0, 0.0))
        values = getattr(obj, "scale", (1.0, 1.0, 1.0))
        angles = getattr(obj, "rotation", (0.0, 0.0, 0.0))
        self._gizmo_feedback = (
            f"T: ({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f})  "
            f"Rz: {angles[2]:.1f}°  "
            f"S: ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})  "
            f"Z-Depth: {position[2]:.1f}"
        )

    def _preview_gizmo_transform(
        self, *, translation=(0.0, 0.0), rotation=0.0, scale=(1.0, 1.0)
    ):
        transaction = self._gizmo_transaction
        if transaction is None or not transaction.active:
            return
        try:
            transaction.preview_transform(
                translation=translation,
                rotation_degrees=rotation,
                scale=scale,
                anchor_override=self._gizmo_anchor_image,
            )
            self._set_gizmo_feedback(translation, rotation, scale)
        except Exception as exc:
            try:
                if transaction.active:
                    transaction.cancel()
            finally:
                self._reset_gizmo_interaction()
                self.update()
            QMessageBox.critical(self, "Gizmo Movement Failed", str(exc))

    def _move_selected_object(self, dx, dy):
        """Compatibility path for callers that submit incremental XY motion."""
        self._gizmo_total_delta += QPointF(float(dx), float(dy))
        self._preview_gizmo_transform(
            translation=(
                float(round(self._gizmo_total_delta.x())),
                float(round(self._gizmo_total_delta.y())),
            )
        )

    def _finish_gizmo_gesture(self):
        transaction = self._gizmo_transaction
        result = None
        try:
            if transaction is not None and transaction.active:
                result = transaction.commit(getattr(self.model, "cmd", None))
                self._report_gizmo_result(result)
        finally:
            self._reset_gizmo_interaction()
            self.update()
        return result

    def _cancel_gizmo_gesture(self) -> bool:
        transaction = self._gizmo_transaction
        restored = False
        try:
            if transaction is not None and transaction.active:
                restored = transaction.cancel()
        finally:
            self._reset_gizmo_interaction()
            self.update()
        return restored

    def clean_all(self):
        response = QMessageBox.question(
            self,
            "Clean Scene",
            "Are you sure you want to remove ALL polygons? " "This supports Undo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            result = self._execute_edit_command(ClearSceneCommand())
            if result.ok:
                self._after_clean()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Clean Scene Error",
                str(exc),
            )

    def _after_clean(self):
        self.clear_temp_mask()
        self._current_polygon = []
        self._flash_color = None
        # self.flash_effect(QColor(255, 0, 0, 50), 400)
        self.update()

    # --- Métodos de Visualização e Utilitários ---
    def fit_to_window(self):
        img = getattr(self.model, "image", None)
        if img is None:
            return
        h, w = img.shape[:2]
        if w == 0 or h == 0:
            return
        scale_x = self.width() / w
        scale_y = self.height() / h
        self._zoom = min(scale_x, scale_y) * 0.95
        new_pan_x = (self.width() - w * self._zoom) / 2.0
        new_pan_y = (self.height() - h * self._zoom) / 2.0
        self._pan = QPointF(new_pan_x, new_pan_y)
        self.update()
        self._emit_viewport_state()

    def flash_effect(self, color: QColor, duration: int = 300):
        self._flash_color = color
        self.update()
        from PySide6.QtCore import QTimer

        QTimer.singleShot(duration, lambda: self._clear_flash())

    def _clear_flash(self):
        self._flash_color = None
        self.update()

    def center_on_polygon(self, polygon: list, margin: int = 50):
        if not polygon:
            return
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        obj_width = max_x - min_x
        obj_height = max_y - min_y
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2

        view_w = self.width() - 2 * margin
        view_h = self.height() - 2 * margin

        if obj_width > 0 and obj_height > 0:
            scale_x = view_w / obj_width
            scale_y = view_h / obj_height
            new_zoom = min(scale_x, scale_y) * 0.9
            self._zoom = max(0.01, min(new_zoom, 10.0))

        pan_x = (self.width() / 2) - (cx * self._zoom)
        pan_y = (self.height() / 2) - (cy * self._zoom)
        self._pan = QPointF(pan_x, pan_y)
        self.update()
        self._emit_viewport_state()

    def viewport_state_text(self) -> str:
        """Return the canonical, human-readable viewport status."""

        modes = {
            self.VIEW_LIT: "LIT",
            self.VIEW_XRAY_1: "X-RAY 1",
            self.VIEW_XRAY_2: "X-RAY 2",
            self.VIEW_XRAY_3: "X-RAY 3",
            self.VIEW_COLLISION: "COLLISION",
        }
        return f"VIEW: {modes.get(self._view_mode, '?')}  |  ZOOM: {self._zoom:.2f}x"

    def _emit_viewport_state(self) -> None:
        self.viewport_state_changed.emit(self.viewport_state_text())

    def set_view_mode(self, mode: int):
        self._view_mode = mode
        # Inicia worker de XRay se necessário
        if (
            mode >= self.VIEW_XRAY_1 and mode <= self.VIEW_XRAY_3
        ) and VIEW_PROCESSOR_CLASS is not None:
            img = getattr(self.model, "image", None)
            if img is not None:
                # Check if we already have this xray mode cached
                cache_attr = f"_qimage_xray_{mode}"
                if getattr(self, cache_attr, None) is None:
                    worker = XrayWorker(img, mode)
                    worker.signals.finished.connect(self._on_xray_finished)
                    self.threadpool.start(worker)
        self.update()
        self._emit_viewport_state()

    def _on_xray_finished(self, qimage: QImage, mode: int):
        cache_attr = f"_qimage_xray_{mode}"
        setattr(self, cache_attr, qimage)
        self.update()

    def toggle_xray(self):
        if self._view_mode == self.VIEW_LIT:
            self.set_view_mode(self.VIEW_XRAY_1)
        else:
            self.set_view_mode(self.VIEW_LIT)

    def update_image(self):
        if VIEW_PROCESSOR_CLASS is None:
            return

        img = getattr(self.model, "image", None)
        if img is None:
            self._qimage_lit = None
            self._qimage_xray_1 = None
            self._qimage_xray_2 = None
            self._qimage_xray_3 = None
            self._gizmo_enabled = False
            self.gizmo_toggle.setChecked(False)
            self.update()
            return

        # Lazy load gizmo se disponível
        if self.gizmo is None and TRANSFORM_GIZMO_CLASS is not None:
            self.gizmo = TRANSFORM_GIZMO_CLASS()

        self._qimage_lit = to_qimage(img)
        self._qimage_xray_1 = None
        self._qimage_xray_2 = None
        self._qimage_xray_3 = None
        self._gizmo_enabled = bool(self._selected_object_ids())
        self.gizmo_toggle.setChecked(self._gizmo_enabled)
        self.update()

    def get_transform(self) -> QTransform:
        t = QTransform()
        t.translate(self._pan.x(), self._pan.y())
        t.scale(self._zoom, self._zoom)
        return t

    def widget_to_image(self, pos: QPointF) -> Tuple[int, int]:
        t = self.get_transform()
        inv, ok = t.inverted()
        if ok:
            pt = inv.map(pos)
            return int(pt.x()), int(pt.y())
        return 0, 0

    def image_to_widget(self, x: float, y: float) -> QPointF:
        return self.get_transform().map(QPointF(x, y))

    def set_zoom(self, zoom: float):
        if 0.01 < zoom < 100.0:
            self._zoom = zoom
            self.update()
            self._emit_viewport_state()

    def get_zoom(self) -> float:
        """Retorna o nível de zoom atual."""
        return self._zoom

    def set_tool(self, tool):
        if self._gizmo_active:
            self._cancel_gizmo_gesture()
        if self._tool and self._tool.on_cancel:
            self._tool.on_cancel()
        self._tool = tool
        self.update()

    def set_collision_overlay(self, overlay):
        self._collision_overlay = overlay

    def show_temp_mask(self, mask):
        self._temp_mask = mask
        self.update()

    def clear_temp_mask(self):
        self._temp_mask = None
        self.update()

    def set_preview_mode(self, mode: bool):
        """Ativa/Desativa modo de preview (para exportação)."""
        if mode and self._gizmo_active:
            self._cancel_gizmo_gesture()
        if mode and self._tool and self._tool.on_cancel:
            self._tool.on_cancel()
        if mode and self._scenario_preview_enabled:
            self._scenario_preview_enabled = False
        self._preview_mode = mode
        # Esconde/Mostra botão do gizmo
        self.gizmo_toggle.setVisible(not mode)
        self.update()

    def _scenario_camera_from_current_view(self) -> OrthographicCamera:
        width = max(1.0, float(self.width()))
        height = max(1.0, float(self.height()))
        zoom = max(0.01, float(self._zoom))
        return OrthographicCamera(
            (width, height),
            position=(
                (width / 2.0 - self._pan.x()) / zoom,
                (height / 2.0 - self._pan.y()) / zoom,
            ),
            zoom=zoom,
        )

    def _scenario_camera_for_viewport(self) -> OrthographicCamera:
        width = max(1.0, float(self.width()))
        height = max(1.0, float(self.height()))
        camera = self._scenario_camera or self._scenario_camera_from_current_view()
        if camera.viewport_size != (width, height):
            camera = OrthographicCamera(
                (width, height), position=camera.position, zoom=camera.zoom
            )
            self._scenario_camera = camera
        return camera

    @staticmethod
    def _scenario_qtransform(
        camera: OrthographicCamera, layer: ParallaxLayer | None = None
    ) -> QTransform:
        resolved = layer or ParallaxLayer()
        zoom = camera.effective_zoom(resolved)
        center_x, center_y = camera.viewport_center
        translation_factor = resolved.translation_factor
        transform = QTransform()
        transform.translate(
            center_x - camera.position[0] * translation_factor * zoom,
            center_y - camera.position[1] * translation_factor * zoom,
        )
        transform.scale(zoom, zoom)
        return transform

    def set_scenario_preview_enabled(self, enabled: bool) -> None:
        """Toggle the read-only scenario preview without changing the scene."""

        enabled = bool(enabled)
        if enabled and not self._scenario_preview_enabled:
            if self._gizmo_active:
                self._cancel_gizmo_gesture()
            if self._tool and self._tool.on_cancel:
                self._tool.on_cancel()
            self._scenario_camera = self._scenario_camera_from_current_view()
        self._scenario_preview_enabled = enabled
        if not enabled:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def is_scenario_preview_enabled(self) -> bool:
        return self._scenario_preview_enabled

    def set_scenario_preview_layers(
        self, layers: tuple[ScenarioPreviewLayer, ...] | list[ScenarioPreviewLayer]
    ) -> None:
        """Set runtime-only layer bindings; persistence belongs to Etapa 4B.3."""

        resolved = tuple(layers)
        if any(not isinstance(layer, ScenarioPreviewLayer) for layer in resolved):
            raise ValueError("scenario preview layers must be ScenarioPreviewLayer")
        layer_ids = [layer.id for layer in resolved]
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("scenario preview layer IDs must be unique")
        object_ids = [object_id for layer in resolved for object_id in layer.object_ids]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("scenario preview object bindings must be unique")
        self._scenario_layers = resolved
        self.update()

    def set_scenario_camera(self, camera: OrthographicCamera) -> None:
        """Install a runtime camera without persisting or mutating the scene."""

        if not isinstance(camera, OrthographicCamera):
            raise ValueError("scenario camera must be an OrthographicCamera")
        self._scenario_camera = camera
        self.update()

    def set_scenario_overlays_visible(
        self,
        visible: bool,
        *,
        aspect_ratio: tuple[int, int] | None = None,
        safe_fraction: float | None = None,
    ) -> None:
        """Toggle safe-frame/crop overlays with validated runtime geometry."""

        resolved_aspect = aspect_ratio or self._scenario_overlay_aspect
        resolved_safe_fraction = (
            self._scenario_safe_fraction if safe_fraction is None else safe_fraction
        )
        geometry = build_overlay_geometry(
            (max(1.0, float(self.width())), max(1.0, float(self.height()))),
            aspect_ratio=resolved_aspect,
            safe_fraction=resolved_safe_fraction,
        )
        self._scenario_overlay_aspect = resolved_aspect
        self._scenario_safe_fraction = geometry.safe_fraction
        self._scenario_overlay_geometry = geometry
        self._scenario_overlays_visible = bool(visible)
        self.update()

    def is_scenario_overlays_visible(self) -> bool:
        return self._scenario_overlays_visible

    # --- Eventos de Input ---
    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        if self._scenario_preview_enabled:
            camera = self._scenario_camera_for_viewport()
            self._scenario_camera = OrthographicCamera(
                camera.viewport_size,
                position=camera.position,
                zoom=max(0.01, min(50.0, camera.zoom * factor)),
            )
            self.update()
            event.accept()
            return
        t = self.get_transform()
        inv, _ = t.inverted()
        mouse_in_img = inv.map(event.position())
        self._zoom *= factor
        self._zoom = max(0.01, min(self._zoom, 50.0))
        new_pan_x = event.position().x() - mouse_in_img.x() * self._zoom
        new_pan_y = event.position().y() - mouse_in_img.y() * self._zoom
        self._pan = QPointF(new_pan_x, new_pan_y)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()

        if self._scenario_preview_enabled:
            if event.button() == Qt.MouseButton.MiddleButton:
                self._dragging = True
                self._last_mouse = pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # 1. Gizmo contextual da seleção (sempre em coordenadas de tela)
        if (
            not self._preview_mode
            and self._qimage_lit
            and self._gizmo_enabled
            and self.gizmo
        ):
            center_screen = self._get_image_center_screen()
            if center_screen is not None:
                self.gizmo.set_screen_position(center_screen)
                hit = self.gizmo.hit_test(pos)
                if hit != self.gizmo.NONE and self._selected_object_ids():
                    self.gizmo.active_axis = hit
                    self._gizmo_operation = hit
                    self._gizmo_start_mouse = pos
                    self._gizmo_press_vector = pos - center_screen
                    self._gizmo_total_delta = QPointF()
                    if hit == self.gizmo.AXIS_Y:
                        self._gizmo_y_screen_direction = (
                            1.0 if self._gizmo_press_vector.y() > 0 else -1.0
                        )
                    if not self._begin_gizmo_object_gesture():
                        self.gizmo.active_axis = self.gizmo.NONE
                        return
                    self._gizmo_active = True
                    return
        # 2. Reset de Visão (Botão Gizmo "C")
        # if not self._preview_mode:
        #     size = 40
        #     gizmo_x = (self.width() - size) // 2
        #     gizmo_y = 30
        #     dx = event.position().x() - gizmo_x
        #     dy = event.position().y() - gizmo_y
        #     if dx * dx + dy * dy <= 64:
        #         self.fit_to_window()
        #         return

        # 3. Pan (Botão do Meio)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = True
            self._last_mouse = pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        ix, iy = self.widget_to_image(pos)

        # 4. Tool Ativa
        if self._tool and self._tool.on_mouse_press:
            self._tool.on_mouse_press(event, (ix, iy))
            self.update()
            return

        # 5. Seleção de Objeto (Clique Esquerdo)
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_id = self._find_object_at(QPointF(ix, iy))
            if clicked_id:
                try:
                    additive = bool(
                        event.modifiers() & Qt.KeyboardModifier.ControlModifier
                    )
                except TypeError:
                    additive = False
                if additive and hasattr(self.model, "select_objects"):
                    current = self._selected_object_ids()
                    if clicked_id in current:
                        current = [oid for oid in current if oid != clicked_id]
                    else:
                        current.append(clicked_id)
                    self.model.select_objects(
                        current, primary=clicked_id if clicked_id in current else None
                    )
                elif hasattr(self.model, "select_object"):
                    self.model.select_object(clicked_id)
                self.update()
            else:
                self.model.select_object(None)  # Deseleciona
                # Require enough distance from the last point to avoid
                # duplicates.
                if (
                    not self._current_polygon
                    or self._distance_to_last_point(ix, iy) >= 5
                ):
                    self._current_polygon.append((ix, iy))
                self.update()

        # 6. Menu / Cancelar (Clique Direito)
        if event.button() == Qt.MouseButton.RightButton:
            if len(self._current_polygon) > 0:
                if len(self._current_polygon) >= 3:
                    object_id = self._commit_native_polygon(self._current_polygon)
                    if object_id is not None:
                        self._current_polygon = []
                else:
                    self._current_polygon = []
                self.update()
            else:
                super().mousePressEvent(event)  # Context Menu

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()

        if self._scenario_preview_enabled:
            if self._dragging:
                delta = pos - self._last_mouse
                self._last_mouse = pos
                camera = self._scenario_camera_for_viewport()
                zoom = max(camera.zoom, 0.01)
                self._scenario_camera = OrthographicCamera(
                    camera.viewport_size,
                    position=(
                        camera.position[0] - delta.x() / zoom,
                        camera.position[1] - delta.y() / zoom,
                    ),
                    zoom=camera.zoom,
                )
                self.update()
            event.accept()
            return

        # 1. Movimento via Gizmo: o preview sempre parte do estado inicial.
        if self._gizmo_active and self.gizmo and not self._preview_mode:
            delta_screen = pos - self._gizmo_start_mouse
            dx = delta_screen.x() / max(self._zoom, 0.01)
            dy = delta_screen.y() / max(self._zoom, 0.01)
            operation = self._gizmo_operation
            if operation == self.gizmo.AXIS_X:
                self._preview_gizmo_transform(translation=(dx, 0.0))
            elif operation == self.gizmo.AXIS_Y:
                self._preview_gizmo_transform(
                    translation=(0.0, dy * self._gizmo_y_screen_direction)
                )
            elif operation in (
                getattr(self.gizmo, "CENTER", -1),
                getattr(self.gizmo, "TRANSLATE_XY", -2),
            ):
                self._preview_gizmo_transform(translation=(dx, dy))
            elif operation == self.gizmo.ROTATE_Z:
                center_screen = self.gizmo.screen_pos
                start_angle = math.degrees(
                    math.atan2(
                        -self._gizmo_press_vector.y(), self._gizmo_press_vector.x()
                    )
                )
                current_vector = pos - center_screen
                current_angle = math.degrees(
                    math.atan2(-current_vector.y(), current_vector.x())
                )
                angle = current_angle - start_angle
                while angle > 180.0:
                    angle -= 360.0
                while angle < -180.0:
                    angle += 360.0
                self._preview_gizmo_transform(rotation=angle)
            elif operation == self.gizmo.SCALE_UNIFORM:
                start_radius = max(
                    math.hypot(
                        self._gizmo_press_vector.x(), self._gizmo_press_vector.y()
                    ),
                    1.0,
                )
                current_radius = max(
                    math.hypot(
                        (pos - self.gizmo.screen_pos).x(),
                        (pos - self.gizmo.screen_pos).y(),
                    ),
                    1.0,
                )
                factor = max(0.05, min(20.0, current_radius / start_radius))
                self._preview_gizmo_transform(scale=(factor, factor))
            elif operation == self.gizmo.SCALE_X:
                factor = max(0.05, min(20.0, 1.0 + dx / self.gizmo.arm_length))
                self._preview_gizmo_transform(scale=(factor, 1.0))
            elif operation == self.gizmo.SCALE_Y:
                factor = max(
                    0.05,
                    min(
                        20.0,
                        1.0
                        - dy * self._gizmo_y_screen_direction / self.gizmo.arm_length,
                    ),
                )
                self._preview_gizmo_transform(scale=(1.0, factor))
            self.update()
            return
        # 2. Hover do Gizmo
        if (
            not self._preview_mode
            and self._qimage_lit
            and self._gizmo_enabled
            and self.gizmo
            and not self._dragging
        ):
            center_screen = self._get_image_center_screen()
            if center_screen:
                self.gizmo.set_screen_position(center_screen)
                if self.gizmo.update_hover(pos):
                    self.update()

        # 3. Pan Manual
        if self._dragging:
            delta = pos - self._last_mouse
            self._last_mouse = pos
            self._pan += delta
            self.update()
            return

        # 4. Tool
        ix, iy = self.widget_to_image(pos)
        if self._tool and self._tool.on_mouse_move:
            self._tool.on_mouse_move(event, (ix, iy))
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._scenario_preview_enabled:
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if self._gizmo_active:
            self._finish_gizmo_gesture()
            return

        if self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        ix, iy = self.widget_to_image(event.position())
        if self._tool and self._tool.on_mouse_release:
            self._tool.on_mouse_release(event, (ix, iy))

    def request_tool_undo(self) -> bool:
        """Give the active tool first chance to consume Undo."""
        if self._tool and self._tool.on_undo:
            try:
                return bool(self._tool.on_undo())
            except Exception as exc:
                logger.error(f"Tool undo failed: {exc}")
        return False

    def request_tool_redo(self) -> bool:
        """Give the active tool first chance to consume Redo."""
        if self._tool and self._tool.on_redo:
            try:
                return bool(self._tool.on_redo())
            except Exception as exc:
                logger.error(f"Tool redo failed: {exc}")
        return False

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape and self._gizmo_active:
            self._cancel_gizmo_gesture()
            event.accept()
            return
        if self._tool and self._tool.on_key_press:
            try:
                if self._tool.on_key_press(event):
                    event.accept()
                    self.update()
                    return
            except Exception as exc:
                logger.error(f"Tool key handler failed: {exc}")
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        ix, iy = self.widget_to_image(event.position())
        if self._tool and self._tool.on_double_click:
            self._tool.on_double_click(event, (ix, iy))
            return
        if len(self._current_polygon) >= 3:
            object_id = self._commit_native_polygon(self._current_polygon)
            if object_id is not None:
                self._current_polygon = []
        else:
            self._current_polygon = []
        self.update()

    def _draw_scenario_scene_objects(
        self, painter: QPainter, camera: OrthographicCamera
    ) -> None:
        selected_oids = set(self._selected_object_ids())
        object_layers = {
            object_id: layer
            for layer in self._scenario_layers
            for object_id in layer.object_ids
        }
        for oid, obj in getattr(self.model, "objects", {}).items():
            poly = getattr(obj, "polygon", [])
            if len(poly) <= 1:
                continue
            layer = object_layers.get(oid)
            if layer is not None and not layer.visible:
                continue
            resolved_layer = layer or ScenarioPreviewLayer(
                id="__unassigned__", parallax=ParallaxLayer()
            )
            projected = project_layer_points(camera, resolved_layer, poly)
            if len(projected) <= 1:
                continue
            if oid in selected_oids:
                painter.setPen(self._pen_selected)
                painter.setBrush(self._brush_selected)
            else:
                painter.setPen(self._pen_poly)
                painter.setBrush(self._brush_poly)
            painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in projected]))

    def _draw_scenario_overlays(self, painter: QPainter) -> None:
        viewport_size = (
            max(1.0, float(self.width())),
            max(1.0, float(self.height())),
        )
        geometry = self._scenario_overlay_geometry
        if geometry is None or geometry.viewport_size != viewport_size:
            geometry = build_overlay_geometry(
                viewport_size,
                aspect_ratio=self._scenario_overlay_aspect,
                safe_fraction=self._scenario_safe_fraction,
            )
            self._scenario_overlay_geometry = geometry
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 150))
        for x, y, width, height in geometry.crop_regions:
            if width > 0.0 and height > 0.0:
                painter.drawRect(QRectF(x, y, width, height))
        x, y, width, height = geometry.frame
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(62, 236, 255, 220), 2))
        painter.drawRect(QRectF(x, y, width, height))
        x, y, width, height = geometry.safe_area
        safe_pen = QPen(QColor(255, 220, 80, 220), 1)
        safe_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(safe_pen)
        painter.drawRect(QRectF(x, y, width, height))
        painter.setPen(QColor(190, 245, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        ratio = f"{geometry.aspect_ratio[0]}:{geometry.aspect_ratio[1]}"
        painter.drawText(10, self.height() - 12, f"SAFE FRAME {ratio}")
        painter.restore()

    def _paint_scenario_preview(self, painter: QPainter) -> None:
        camera = self._scenario_camera_for_viewport()
        image = self._qimage_lit
        if image is not None:
            painter.save()
            painter.setTransform(self._scenario_qtransform(camera))
            painter.drawImage(0, 0, image)
            painter.restore()
        painter.save()
        self._draw_scenario_scene_objects(painter, camera)
        painter.restore()
        if self._scenario_overlays_visible:
            self._draw_scenario_overlays(painter)
        self._draw_hud(painter)
        painter.setPen(QColor(170, 245, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        painter.drawText(10, 62, "SCENARIO PREVIEW | READ-ONLY")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        if self._scenario_preview_enabled:
            self._paint_scenario_preview(painter)
            painter.end()
            return

        # 1. Transformação para Mundo
        t = self.get_transform()
        painter.setTransform(t)

        # Desenha Imagem
        img = None
        if self._view_mode == self.VIEW_LIT:
            img = self._qimage_lit
        elif self._view_mode == self.VIEW_XRAY_1:
            img = (
                self._qimage_xray_1
                if self._qimage_xray_1 is not None
                else self._qimage_lit
            )
        elif self._view_mode == self.VIEW_XRAY_2:
            img = (
                self._qimage_xray_2
                if self._qimage_xray_2 is not None
                else self._qimage_lit
            )
        elif self._view_mode == self.VIEW_XRAY_3:
            img = (
                self._qimage_xray_3
                if self._qimage_xray_3 is not None
                else self._qimage_lit
            )
        elif self._view_mode == self.VIEW_COLLISION:
            img = self._qimage_lit  # Use lit image for collision view

        if img and self._view_mode != self.VIEW_COLLISION:
            painter.drawImage(0, 0, img)
            if not self._preview_mode:
                self._draw_grid(painter, img.width(), img.height())
        elif self._view_mode == self.VIEW_COLLISION and img:
            painter.drawImage(0, 0, img)
            if not self._preview_mode:
                self._draw_grid(painter, img.width(), img.height())
        elif self._qimage_lit is None:
            # Placeholder se não houver imagem
            painter.setPen(QColor(80, 80, 80))
            painter.drawRect(0, 0, 1000, 800)

        # Desenha Objetos da Cena
        self._draw_scene_objects(painter)

        # --- Camada de Tela (Interface) ---
        painter.setTransform(QTransform())

        # O estado persistente do viewport vive na status bar da MainWindow.
        # Isso mantém o canvas livre para conteúdo, overlays e gizmo.
        if not self._preview_mode:
            # Gizmo Interativo
            if self._qimage_lit and self._gizmo_enabled and self.gizmo:
                center_screen = self._get_image_center_screen()
                if center_screen:
                    self.gizmo.set_screen_position(center_screen)
                    self.gizmo.draw(painter)
            self._draw_gizmo_feedback(painter)

        # Overlays de Ferramenta
        if self._tool and self._tool.draw_overlay:
            painter.save()
            self._tool.draw_overlay(painter)
            painter.restore()

        # Polígono Manual em Construção (Transformado)
        if self._current_polygon:
            painter.setTransform(t)
            painter.setPen(self._pen_preview)
            pts = [QPointF(float(p[0]), float(p[1])) for p in self._current_polygon]
            painter.drawPolyline(QPolygonF(pts))
            painter.setTransform(QTransform())

        # Overlay de Colisão (Se existir)
        if self._collision_overlay and not self._preview_mode:
            self._collision_overlay.draw(
                painter, self._zoom, (self._pan.x(), self._pan.y())
            )

        if self._flash_color:
            painter.fillRect(self.rect(), self._flash_color)

        painter.end()

    def _draw_scene_objects(self, painter: QPainter):
        selected_oids = set(self._selected_object_ids())

        # Otimização: Itera apenas objetos visíveis se possível, mas aqui iteramos tudo
        for oid, obj in getattr(self.model, "objects", {}).items():
            poly = getattr(obj, "polygon", [])
            if len(poly) > 1:
                # Estilo
                if oid in selected_oids:
                    painter.setPen(self._pen_selected)
                    painter.setBrush(self._brush_selected)
                else:
                    painter.setPen(self._pen_poly)
                    painter.setBrush(self._brush_poly)

                qpoly = QPolygonF([QPointF(x, y) for x, y in poly])
                painter.drawPolygon(qpoly)

    def _draw_grid(self, painter: QPainter, w: int, h: int):
        # Grid leve para referência
        step = 64
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        # Linhas Verticais
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        # Linhas Horizontais
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)
        # Borda
        painter.setPen(QPen(QColor(255, 255, 0, 100), 2))
        painter.drawRect(0, 0, w, h)

    def _draw_hud(self, painter):
        """Draw the legacy opt-in overlay for isolated canvas callers.

        MainWindow does not invoke this helper anymore: the live viewport state
        is exposed through viewport_state_changed and rendered by the permanent
        status-bar indicator. Keeping the explicit helper preserves compatibility
        for tools that intentionally request a canvas overlay.
        """
        header_height = 45
        painter.setBrush(QColor(20, 20, 20, 200))
        painter.setPen(QPen(QColor(150, 150, 150), 2))
        painter.drawRect(0, 0, self.width(), header_height)

        txt = self.viewport_state_text()
        painter.setPen(QColor(0, 255, 255))
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(txt)
        center_x = (self.width() - text_width) // 2
        painter.drawText(center_x, 28, txt)

    def _gizmo_feedback_rect(self, painter: QPainter) -> QRectF:
        """Return a feedback rectangle that does not cover the interactive gizmo."""
        if not self._gizmo_feedback:
            return QRectF()
        parts = self._gizmo_feedback.split("  S:", 1)
        lines = [parts[0]]
        if len(parts) == 2:
            lines.append("S:" + parts[1])
        metrics = painter.fontMetrics()
        line_height = metrics.height()
        width = min(
            max(metrics.horizontalAdvance(line) for line in lines) + 18,
            max(120, self.width() - 16),
        )
        height = line_height * len(lines) + 12
        margin = 8.0
        candidates = (
            QRectF(margin, 52.0, width, height),
            QRectF(self.width() - width - margin, 52.0, width, height),
            QRectF(margin, self.height() - height - 12.0, width, height),
            QRectF(
                self.width() - width - margin,
                self.height() - height - 12.0,
                width,
                height,
            ),
        )
        gizmo_rect = QRectF()
        if self.gizmo is not None and self._gizmo_enabled:
            radius = (
                max(
                    float(getattr(self.gizmo, "arm_length", 76.0))
                    + float(getattr(self.gizmo, "arrow_size", 14.0)),
                    float(getattr(self.gizmo, "rotation_radius", 51.0))
                    + float(getattr(self.gizmo, "rotation_tolerance", 10.0)),
                )
                + 12.0
            )
            center = self.gizmo.screen_pos
            gizmo_rect = QRectF(
                center.x() - radius, center.y() - radius, radius * 2, radius * 2
            )
        for candidate in candidates:
            if candidate.left() < margin or candidate.top() < 45.0:
                continue
            if (
                candidate.right() > self.width() - margin
                or candidate.bottom() > self.height() - margin
            ):
                continue
            if gizmo_rect.isNull() or not candidate.intersects(gizmo_rect):
                return candidate
        return candidates[-1]

    def _draw_gizmo_feedback(self, painter):
        if not self._gizmo_feedback:
            return
        painter.save()
        painter.setPen(QPen(QColor(62, 236, 255, 180), 1))
        painter.setBrush(QColor(8, 22, 27, 225))
        painter.setFont(QFont("Consolas", 9))
        parts = self._gizmo_feedback.split("  S:", 1)
        lines = [parts[0]]
        if len(parts) == 2:
            lines.append("S:" + parts[1])
        rect = self._gizmo_feedback_rect(painter)
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QColor(170, 245, 255))
        for index, line in enumerate(lines):
            painter.drawText(
                rect.left() + 9,
                rect.top() + 7 + (index + 1) * painter.fontMetrics().height() - 2,
                line,
            )
        painter.restore()

    def _draw_axis_gizmo(self, painter):
        # Pequeno helper visual no topo
        painter.save()
        painter.setTransform(QTransform())
        size = 40
        gizmo_x = (self.width() - size) // 2
        gizmo_y = 30

        # X axis
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(gizmo_x, gizmo_y, gizmo_x + size, gizmo_y)
        # Y axis
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawLine(gizmo_x, gizmo_y, gizmo_x, gizmo_y + size)

        # Botão C (Center)
        painter.setPen(QPen(QColor(192, 192, 192), 2))
        painter.setBrush(QColor(128, 128, 128))
        painter.drawEllipse(gizmo_x - 8, gizmo_y - 8, 16, 16)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(gizmo_x - 4, gizmo_y + 4, "C")

        painter.restore()

    def update_language(self, lang):
        self.current_lang = lang
        self.gizmo_toggle.setText(self.translations[self.current_lang]["gizmo"])
        if self._tool and self._tool.update_language:
            self._tool.update_language(lang)
