# src/tools/collision_brush_tool.py
from typing import Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QMenu, QMessageBox

from src.tools.base_tool import BaseTool


class CollisionBrushTool(BaseTool):
    """
    Tool for interacting with physics properties of polygons.
    Allows toggling collision, moving, and scaling objects directly.
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
        if event.button() == Qt.MouseButton.LeftButton:
            if self.moving or self.scaling:
                # Commit or Cancel logic could go here
                self.moving = False
                self.moving_oid = None
                self.last_pos = None
                self.scaling = False
                self.scaling_oid = None
                self.scale_center = None
                self.initial_scale = 1.0
                self.last_scale_pos = None
            else:
                # Toggle collision for polygon at pos
                oid = self._find_polygon_at(pos)
                if oid:
                    try:
                        from src.core.commands import ToggleCollisionCommand

                        if (
                            hasattr(self.canvas_view.model, "cmd")
                            and self.canvas_view.model.cmd
                        ):
                            self.canvas_view.model.cmd.execute(
                                ToggleCollisionCommand(oid),
                                self.canvas_view.model,
                            )
                        else:
                            curr = self.canvas_view.model.has_collision(oid)
                            self.canvas_view.model.set_object_collision(oid, not curr)
                        self.canvas_view.update()
                    except Exception as e:
                        QMessageBox.critical(
                            self.canvas_view,
                            "Error",
                            f"Collision Toggle Error: {str(e)}",
                        )
        elif event.button() == Qt.MouseButton.RightButton:
            if self.moving or self.scaling:
                if self.scaling:
                    self._show_scale_menu(
                        self.scaling_oid, event.globalPos()
                    )  # type: ignore
                else:
                    self.moving = False
                    self.moving_oid = None
                    self.last_pos = None
            else:
                # Show hub menu for polygon at pos
                oid = self._find_polygon_at(pos)
                if oid:
                    self._show_hub_menu(oid, event.globalPos())

    def on_mouse_move(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self.moving and self.moving_oid:
            if self.last_pos is None:
                self.last_pos = pos
            else:
                dx = pos[0] - self.last_pos[0]
                dy = pos[1] - self.last_pos[1]
                obj = self.canvas_view.model.objects.get(self.moving_oid)
                if obj and obj.polygon:
                    obj.polygon = [(x + dx, y + dy) for x, y in obj.polygon]
                    # Update collision if exists
                    if self.moving_oid in self.canvas_view.model.collision_shapes:
                        self.canvas_view.model.collision_shapes[self.moving_oid] = [
                            (x + dx, y + dy)
                            for x, y in self.canvas_view.model.collision_shapes[
                                self.moving_oid
                            ]
                        ]
                    self.canvas_view.model._notify()
                self.last_pos = pos
        elif self.scaling and self.scaling_oid and self.scale_center:
            if self.last_scale_pos is None:
                self.last_scale_pos = pos
            else:
                dy = pos[1] - self.last_scale_pos[1]
                # Scale sensitivity
                scale_factor = 1.0 + dy * 0.001
                self.initial_scale *= scale_factor

                obj = self.canvas_view.model.objects.get(self.scaling_oid)
                if obj and obj.polygon:
                    scaled_polygon = []
                    for x, y in obj.polygon:
                        dx = x - self.scale_center[0]
                        dy = y - self.scale_center[1]
                        new_x = self.scale_center[0] + dx * self.initial_scale
                        new_y = self.scale_center[1] + dy * self.initial_scale
                        scaled_polygon.append((new_x, new_y))

                    obj.polygon = scaled_polygon
                    if self.scaling_oid in self.canvas_view.model.collision_shapes:
                        self.canvas_view.model.collision_shapes[self.scaling_oid] = [
                            (x, y) for x, y in scaled_polygon
                        ]

                    self.canvas_view.model._notify()
                self.last_scale_pos = pos

    def on_mouse_release(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self.moving:
            self.moving = False
            self.moving_oid = None
            self.last_pos = None
        if self.scaling:
            self.scaling = False
            self.scaling_oid = None
            self.scale_center = None
            self.initial_scale = 1.0
            self.last_scale_pos = None

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

    def _cancel_scale(self):
        self.scaling = False
        self.scaling_oid = None
        self.scale_center = None
        self.initial_scale = 1.0
        self.last_scale_pos = None

    def _switch_to_move(self, oid: str):
        self._cancel_scale()
        self.moving = True
        self.moving_oid = oid
        self.last_pos = None

    def _scale_increase(self, oid: str):
        if self.scaling and self.scale_center:
            self.initial_scale *= 1.1
            self._apply_scale(oid)

    def _scale_decrease(self, oid: str):
        if self.scaling and self.scale_center:
            self.initial_scale *= 0.9
            self._apply_scale(oid)

    def _apply_scale(self, oid: str):
        obj = self.canvas_view.model.objects.get(oid)
        if obj and obj.polygon:
            scaled_polygon = []
            for x, y in obj.polygon:
                dx = x - self.scale_center[0]  # type: ignore
                dy = y - self.scale_center[1]  # type: ignore
                new_x = self.scale_center[0] + dx * self.initial_scale  # type: ignore
                new_y = self.scale_center[1] + dy * self.initial_scale  # type: ignore
                scaled_polygon.append((new_x, new_y))
            obj.polygon = scaled_polygon
            if oid in self.canvas_view.model.collision_shapes:
                self.canvas_view.model.collision_shapes[oid] = [
                    (x, y) for x, y in scaled_polygon
                ]
            self.canvas_view.model._notify()

    def _start_move(self, oid: str, main_window):
        self.moving = True
        self.moving_oid = oid
        self.last_pos = None

    def _start_edit(self, main_window):
        if hasattr(main_window, "tool_palette"):
            main_window.tool_palette.select_tool_by_name("polygon_edit")

    def _start_scale(self, oid: str, main_window):
        obj = self.canvas_view.model.objects.get(oid)
        if obj and obj.polygon:
            xs = [p[0] for p in obj.polygon]
            ys = [p[1] for p in obj.polygon]
            self.scale_center = (sum(xs) / len(xs), sum(ys) / len(ys))
            self.scaling = True
            self.scaling_oid = oid
            self.initial_scale = 1.0
            self.last_scale_pos = None

    def _undo(self):
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.undo(self.canvas_view.model)
        self.canvas_view.update()

    def _redo(self):
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.redo(self.canvas_view.model)
        self.canvas_view.update()

    def _remove(self, oid: str):
        res = QMessageBox.question(
            self.canvas_view,
            self.translations[self.current_lang]["remove_title"],
            self.translations[self.current_lang]["remove_question"].format(oid=oid),
        )
        if res == QMessageBox.StandardButton.Yes:
            self.canvas_view.model.remove_object(oid)

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
