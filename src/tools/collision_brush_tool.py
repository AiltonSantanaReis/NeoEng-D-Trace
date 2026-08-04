# src/tools/collision_brush_tool.py
from typing import List, Optional, Sequence, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QMenu, QMessageBox

from src.core.commands import (
    CommandResult,
    CommandStatus,
    DeleteObjectCommand,
    ToggleCollisionCommand,
)
from src.core.object_geometry_gesture import (
    ObjectGeometryGestureTransaction,
)
from src.tools.base_tool import BaseTool


class CollisionBrushTool(BaseTool):
    """
    Tool for interacting with physics properties of polygons.
    Collision toggles, movement, and scale changes use command history.
    """

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self.selected_polygon_id: Optional[str] = None
        self.moving = False
        self.moving_oid: Optional[str] = None
        self.last_pos: Optional[Tuple[int, int]] = None
        self.scaling = False
        self.scaling_oid: Optional[str] = None
        self.scale_center: Optional[Tuple[float, float]] = None
        self.initial_scale = 1.0
        self.last_scale_pos: Optional[Tuple[int, int]] = None
        self._transform_transaction: Optional[ObjectGeometryGestureTransaction] = None
        self._transform_anchor_pos: Optional[Tuple[int, int]] = None
        self.current_lang = "en"
        self.translations = {
            "en": {
                "move": "🏃 Move",
                "edit": "✏️ Edit",
                "scale": "📏 Scale",
                "undo": "↶ Undo",
                "redo": "↷ Redo",
                "remove": "🗑️ Remove",
                "cancel": "❌ Cancel",
                "center": "🎯 Center",
                "increase": "➕ Increase",
                "decrease": "➖ Decrease",
                "remove_title": "Remove",
                "remove_question": "Remove object {oid}?",
            },
            "pt": {
                "move": "🏃 Mover",
                "edit": "✏️ Editar",
                "scale": "📏 Escalar",
                "undo": "↶ Desfazer",
                "redo": "↷ Refazer",
                "remove": "🗑️ Remover",
                "cancel": "❌ Cancelar",
                "center": "🎯 Centro",
                "increase": "➕ Aumentar",
                "decrease": "➖ Diminuir",
                "remove_title": "Remover",
                "remove_question": "Remover objeto {oid}?",
            },
        }

    def on_mouse_press(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self._transform_transaction is not None:
            if event.button() == Qt.MouseButton.LeftButton:
                self._finish_transform_gesture()
                return
            if event.button() == Qt.MouseButton.RightButton:
                if self.scaling and self.scaling_oid is not None:
                    self._show_scale_menu(
                        self.scaling_oid,
                        event.globalPos(),
                    )
                else:
                    self._cancel_transform_gesture()
                return

        if event.button() == Qt.MouseButton.LeftButton:
            oid = self._find_polygon_at(pos)
            if oid:
                try:
                    manager = getattr(
                        self.canvas_view.model,
                        "cmd",
                        None,
                    )
                    if manager is None:
                        QMessageBox.critical(
                            self.canvas_view,
                            "Collision Toggle Unavailable",
                            "Undo/Redo command history is unavailable.",
                        )
                        return
                    result = manager.execute(
                        ToggleCollisionCommand(oid),
                        self.canvas_view.model,
                    )
                    self._report_command_result(
                        result,
                        "Collision Toggle",
                    )
                    if result.changed:
                        self.canvas_view.update()
                except Exception as exc:
                    QMessageBox.critical(
                        self.canvas_view,
                        "Error",
                        f"Collision Toggle Error: {str(exc)}",
                    )
            return

        if event.button() == Qt.MouseButton.RightButton:
            oid = self._find_polygon_at(pos)
            if oid:
                self._show_hub_menu(
                    oid,
                    event.globalPos(),
                )

    def on_mouse_move(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self.moving and self.moving_oid:
            self._preview_move(pos)
        elif self.scaling and self.scaling_oid and self.scale_center:
            self._preview_scale(pos)

    def on_mouse_release(self, event: QMouseEvent, pos: Tuple[int, int]):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._transform_transaction is not None
        ):
            self._finish_transform_gesture()

    def on_cancel(self):
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
        else:
            self._reset_transform_state()
            self.canvas_view.update()

    def on_key_press(self, event) -> bool:
        if event.key() == Qt.Key.Key_Escape and self._transform_transaction is not None:
            self._cancel_transform_gesture()
            return True
        return False

    def on_undo(self) -> bool:
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
            return True
        return False

    def on_redo(self) -> bool:
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
            return True
        return False

    def _find_polygon_at(self, pos: Tuple[int, int]) -> Optional[str]:
        # pos is already in image coordinates
        img_pt = QPointF(pos[0], pos[1])
        objects = getattr(self.canvas_view.model, "objects", {})
        for oid, obj in reversed(list(objects.items())):
            poly = getattr(obj, "polygon", [])
            if len(poly) < 3:
                continue
            poly_float = [QPointF(float(p[0]), float(p[1])) for p in poly]
            qpoly = QPolygonF(poly_float)
            if qpoly.containsPoint(img_pt, Qt.FillRule.OddEvenFill):
                return oid
        return None

    def _show_hub_menu(self, oid: str, pos):
        menu = QMenu(self.canvas_view)
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d30; color: #e6e6e6;
            border: 1px solid #3f3f46; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #2a6f97; }
        """)

        main_window = self.canvas_view.parent()

        # Move
        act_move = menu.addAction(self.translations[self.current_lang]["move"])
        act_move.triggered.connect(lambda: self._start_move(oid, main_window))

        # Edit
        act_edit = menu.addAction(self.translations[self.current_lang]["edit"])
        act_edit.triggered.connect(lambda: self._start_edit(main_window))

        # Scale
        act_scale = menu.addAction(self.translations[self.current_lang]["scale"])
        act_scale.triggered.connect(lambda: self._start_scale(oid, main_window))

        menu.addSeparator()

        # Undo
        act_undo = menu.addAction(self.translations[self.current_lang]["undo"])
        act_undo.triggered.connect(self._undo)

        # Redo
        act_redo = menu.addAction(self.translations[self.current_lang]["redo"])
        act_redo.triggered.connect(self._redo)

        menu.addSeparator()

        # Remove
        act_remove = menu.addAction(self.translations[self.current_lang]["remove"])
        act_remove.triggered.connect(lambda: self._remove(oid))

        menu.exec(pos)

    def _show_scale_menu(self, oid: str, pos):
        menu = QMenu(self.canvas_view)
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d30; color: #e6e6e6;
            border: 1px solid #3f3f46; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #2a6f97; }
        """)

        # Cancel
        act_cancel = menu.addAction(self.translations[self.current_lang]["cancel"])
        act_cancel.triggered.connect(self._cancel_scale)

        # Center
        act_center = menu.addAction(self.translations[self.current_lang]["center"])
        act_center.triggered.connect(
            lambda: self.canvas_view.focus_on_object(oid)
        )  # type: ignore

        # Move
        act_move = menu.addAction(self.translations[self.current_lang]["move"])
        act_move.triggered.connect(lambda: self._switch_to_move(oid))

        menu.addSeparator()

        # Increase
        act_increase = menu.addAction(self.translations[self.current_lang]["increase"])
        act_increase.triggered.connect(lambda: self._scale_increase(oid))

        # Decrease
        act_decrease = menu.addAction(self.translations[self.current_lang]["decrease"])
        act_decrease.triggered.connect(lambda: self._scale_decrease(oid))

        menu.addSeparator()

        # Undo
        act_undo = menu.addAction(self.translations[self.current_lang]["undo"])
        act_undo.triggered.connect(self._undo)

        # Redo
        act_redo = menu.addAction(self.translations[self.current_lang]["redo"])
        act_redo.triggered.connect(self._redo)

        menu.exec(pos)

    def _reset_transform_state(self) -> None:
        self._transform_transaction = None
        self._transform_anchor_pos = None
        self.moving = False
        self.moving_oid = None
        self.last_pos = None
        self.scaling = False
        self.scaling_oid = None
        self.scale_center = None
        self.initial_scale = 1.0
        self.last_scale_pos = None

    def _begin_transform_gesture(
        self,
        oid: str,
        operation: str,
    ) -> bool:
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()

        manager = getattr(
            self.canvas_view.model,
            "cmd",
            None,
        )
        if manager is None:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return False

        obj = self.canvas_view.model.objects.get(oid)
        if obj is None or not obj.polygon:
            QMessageBox.warning(
                self.canvas_view,
                f"{operation} Rejected",
                "The selected object is no longer available.",
            )
            return False

        try:
            transaction = ObjectGeometryGestureTransaction(
                self.canvas_view.model,
                oid,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                str(exc),
            )
            return False

        self._transform_transaction = transaction
        self._transform_anchor_pos = None
        self.selected_polygon_id = oid

        if operation == "Move":
            self.moving = True
            self.moving_oid = oid
            self.last_pos = None
            self.scaling = False
            self.scaling_oid = None
            self.scale_center = None
            self.initial_scale = 1.0
            self.last_scale_pos = None
        else:
            origin = transaction.origin_polygon
            self.scale_center = (
                sum(point[0] for point in origin) / len(origin),
                sum(point[1] for point in origin) / len(origin),
            )
            self.scaling = True
            self.scaling_oid = oid
            self.initial_scale = 1.0
            self.last_scale_pos = None
            self.moving = False
            self.moving_oid = None
            self.last_pos = None
        self.canvas_view.update()
        return True

    def _preview_move(
        self,
        pos: Tuple[int, int],
    ) -> None:
        transaction = self._transform_transaction
        if (
            transaction is None
            or not transaction.active
            or self.moving_oid != transaction.object_id
        ):
            return

        if self._transform_anchor_pos is None:
            self._transform_anchor_pos = (pos[0], pos[1])
            self.last_pos = (pos[0], pos[1])
            return

        dx = pos[0] - self._transform_anchor_pos[0]
        dy = pos[1] - self._transform_anchor_pos[1]
        polygon = [
            (
                int(round(x + dx)),
                int(round(y + dy)),
            )
            for x, y in transaction.origin_polygon
        ]
        collision = (
            [
                (
                    float(x) + dx,
                    float(y) + dy,
                )
                for x, y in (transaction.origin_collision or [])
            ]
            if transaction.origin_has_collision
            else None
        )
        self._preview_transform_geometry(
            polygon,
            transaction.origin_has_collision,
            collision,
            "Move",
        )
        self.last_pos = (pos[0], pos[1])

    def _preview_scale(
        self,
        pos: Tuple[int, int],
    ) -> None:
        if self._transform_anchor_pos is None:
            self._transform_anchor_pos = (pos[0], pos[1])
            self.last_scale_pos = (pos[0], pos[1])
            return

        delta_y = pos[1] - self._transform_anchor_pos[1]
        self.initial_scale = max(
            0.05,
            1.0 + delta_y * 0.001,
        )
        self._apply_scale(self.scaling_oid)
        self.last_scale_pos = (pos[0], pos[1])

    def _preview_transform_geometry(
        self,
        polygon: Sequence[Tuple[float, float]],
        has_collision: bool,
        collision: Optional[Sequence[Tuple[float, float]]],
        operation: str,
    ) -> None:
        transaction = self._transform_transaction
        if transaction is None or not transaction.active:
            return
        try:
            transaction.preview(
                list(polygon),
                has_collision=has_collision,
                collision=(list(collision) if collision is not None else None),
            )
        except Exception as exc:
            try:
                if transaction.active:
                    transaction.cancel()
            except Exception:
                pass
            self._reset_transform_state()
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                str(exc),
            )
        self.canvas_view.update()

    def _finish_transform_gesture(
        self,
    ) -> Optional[CommandResult]:
        transaction = self._transform_transaction
        operation = "Scale" if self.scaling else "Move"
        result: Optional[CommandResult] = None
        try:
            if transaction is not None and transaction.active:
                result = transaction.commit(
                    getattr(
                        self.canvas_view.model,
                        "cmd",
                        None,
                    )
                )
                self._report_command_result(
                    result,
                    operation,
                )
        finally:
            self._reset_transform_state()
            self.canvas_view.update()
        return result

    def _cancel_transform_gesture(self) -> bool:
        transaction = self._transform_transaction
        restored = False
        try:
            if transaction is not None and transaction.active:
                restored = transaction.cancel()
        finally:
            self._reset_transform_state()
            self.canvas_view.update()
        return restored

    def _cancel_scale(self):
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
        else:
            self._reset_transform_state()
            self.canvas_view.update()

    def _switch_to_move(self, oid: str):
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
        self._start_move(oid, None)

    def _scale_increase(self, oid: str):
        if (
            self.scaling
            and self.scale_center
            and self.scaling_oid == oid
            and self._transform_transaction is not None
        ):
            self.initial_scale = max(
                0.05,
                self.initial_scale * 1.1,
            )
            self._apply_scale(oid)

    def _scale_decrease(self, oid: str):
        if (
            self.scaling
            and self.scale_center
            and self.scaling_oid == oid
            and self._transform_transaction is not None
        ):
            self.initial_scale = max(
                0.05,
                self.initial_scale * 0.9,
            )
            self._apply_scale(oid)

    def _apply_scale(self, oid: Optional[str]):
        transaction = self._transform_transaction
        center = self.scale_center
        if (
            transaction is None
            or not transaction.active
            or oid is None
            or oid != transaction.object_id
            or center is None
        ):
            return

        factor = self.initial_scale
        polygon = [
            (
                int(round(center[0] + (x - center[0]) * factor)),
                int(round(center[1] + (y - center[1]) * factor)),
            )
            for x, y in transaction.origin_polygon
        ]
        collision = (
            [
                (
                    center[0] + (float(x) - center[0]) * factor,
                    center[1] + (float(y) - center[1]) * factor,
                )
                for x, y in (transaction.origin_collision or [])
            ]
            if transaction.origin_has_collision
            else None
        )
        self._preview_transform_geometry(
            polygon,
            transaction.origin_has_collision,
            collision,
            "Scale",
        )

    def _start_move(self, oid: str, main_window):
        self._begin_transform_gesture(
            oid,
            "Move",
        )

    def _start_edit(self, main_window):
        if hasattr(main_window, "tool_palette"):
            main_window.tool_palette.select_tool_by_name("polygon_edit")

    def _start_scale(self, oid: str, main_window):
        self._begin_transform_gesture(
            oid,
            "Scale",
        )

    def _undo(self):
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
        manager = getattr(
            self.canvas_view.model,
            "cmd",
            None,
        )
        if manager is not None:
            manager.undo(self.canvas_view.model)
        self.canvas_view.update()

    def _redo(self):
        if self._transform_transaction is not None:
            self._cancel_transform_gesture()
        manager = getattr(
            self.canvas_view.model,
            "cmd",
            None,
        )
        if manager is not None:
            manager.redo(self.canvas_view.model)
        self.canvas_view.update()

    def _report_command_result(
        self,
        result: CommandResult,
        operation: str,
    ) -> None:
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self.canvas_view,
                f"{operation} Rejected",
                result.message or "The operation was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                result.message or "The operation failed.",
            )

    def _reset_interaction_for_object(self, oid: str) -> None:
        if self.moving_oid == oid:
            self.moving = False
            self.moving_oid = None
            self.last_pos = None
        if self.scaling_oid == oid:
            self.scaling = False
            self.scaling_oid = None
            self.scale_center = None
            self.initial_scale = 1.0
            self.last_scale_pos = None
        if self.selected_polygon_id == oid:
            self.selected_polygon_id = None

    def _remove(self, oid: str):
        response = QMessageBox.question(
            self.canvas_view,
            self.translations[self.current_lang]["remove_title"],
            self.translations[self.current_lang]["remove_question"].format(oid=oid),
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        manager = getattr(self.canvas_view.model, "cmd", None)
        if manager is None:
            QMessageBox.critical(
                self.canvas_view,
                "Remove Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return

        try:
            result = manager.execute(
                DeleteObjectCommand(oid),
                self.canvas_view.model,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.canvas_view,
                "Remove Failed",
                str(exc),
            )
            return

        self._report_command_result(result, "Remove")
        if result.changed:
            self._reset_interaction_for_object(oid)
            self.canvas_view.update()

    def draw_overlay(self, painter: QPainter):
        """Draws overlay using the view's transform for efficiency."""
        # 1. Setup Transform (Draw in Image Space)
        transform = self.canvas_view.get_transform()
        painter.save()
        painter.setTransform(transform, combine=True)

        # 2. Highlight polygons with collision (Static Green)
        if hasattr(self.canvas_view.model, "collision_shapes"):
            for oid in self.canvas_view.model.collision_shapes:
                obj = self.canvas_view.model.objects.get(oid)
                if obj and obj.polygon:
                    # Vermelho para colisão aplicada, azul se selecionado, verde padrão
                    if oid == self.selected_polygon_id:
                        pen_selected = QPen(QColor(0, 128, 255), 3)
                        pen_selected.setCosmetic(True)
                        painter.setPen(pen_selected)
                    elif self.canvas_view.model.has_collision(oid):
                        pen_collision = QPen(QColor(255, 0, 0), 3)
                        pen_collision.setCosmetic(True)
                        painter.setPen(pen_collision)
                    else:
                        pen = QPen(QColor(0, 255, 0), 2)
                        pen.setCosmetic(True)
                        painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                    painter.drawPolygon(QPolygonF(points))

        # 3. Highlight moving polygon (Yellow)
        if self.moving and self.moving_oid:
            obj = self.canvas_view.model.objects.get(self.moving_oid)
            if obj and obj.polygon:
                pen = QPen(QColor(255, 255, 0), 3)
                pen.setCosmetic(True)
                painter.setPen(pen)

                points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                painter.drawPolygon(QPolygonF(points))

        # 4. Highlight scaling polygon (Magenta)
        if self.scaling and self.scaling_oid:
            obj = self.canvas_view.model.objects.get(self.scaling_oid)
            if obj and obj.polygon:
                pen = QPen(QColor(255, 0, 255), 3)
                pen.setCosmetic(True)
                painter.setPen(pen)

                points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                painter.drawPolygon(QPolygonF(points))

        painter.restore()

    def update_language(self, lang):
        self.current_lang = lang
