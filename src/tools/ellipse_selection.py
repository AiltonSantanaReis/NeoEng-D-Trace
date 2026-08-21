# src/tools/ellipse_selection.py
"""
Ellipse selection tool for elliptical selections.
"""

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QMenu

from .base_tool import BaseTool


class EllipseSelectionTool(BaseTool):
    """
    Elliptical selection tool.
    Creates a polygon approximation of an ellipse.
    """

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self._center = None
        self._radius_x = 0
        self._radius_y = 0
        self._is_selecting = False
        self._segments = 64  # Resolution of the ellipse
        self.current_lang = "en"
        self.translations = {
            "en": {
                "cancel_selection": "Cancel Selection",
                "undo": "Undo",
                "redo": "Redo",
            },
            "pt": {
                "cancel_selection": "Cancelar Seleção",
                "undo": "Desfazer",
                "redo": "Refazer",
            },
        }

    def on_mouse_press(self, event: QMouseEvent, position: tuple):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_selecting = True
            x, y = position
            self._center = (x, y)
            self._radius_x = 0
            self._radius_y = 0
            self.canvas_view.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

    def on_mouse_move(self, event: QMouseEvent, position: tuple):
        if self._is_selecting and self._center:
            x, y = position
            dx = x - self._center[0]
            dy = y - self._center[1]

            # Shift modifier for circular selection
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                radius = max(abs(dx), abs(dy))
                self._radius_x = radius
                self._radius_y = radius
            else:
                self._radius_x = abs(dx)
                self._radius_y = abs(dy)

            self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, position: tuple):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            object_id = self.commit_selection()
            if object_id is not None:
                self._center = None
                self._radius_x = 0
                self._radius_y = 0
            self.canvas_view.update()

    def commit_selection(self):
        if not self._center or self._radius_x <= 0 or self._radius_y <= 0:
            return None

        cx, cy = self._center
        rx, ry = self._radius_x, self._radius_y

        # Generate polygon points approximating the ellipse
        polygon = []
        for i in range(self._segments):
            angle = 2 * math.pi * i / self._segments
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            polygon.append((int(round(x)), int(round(y))))

        return self.commit_polygon_command(
            polygon,
            action_name="Ellipse Creation",
        )

    def draw_overlay(self, painter: QPainter):
        """
        Draws the ellipse overlay during selection.
        """
        if not self._center or self._radius_x <= 0 or self._radius_y <= 0:
            return

        # Use CanvasView transform to draw in Image Space
        transform = self.canvas_view.get_transform()

        painter.save()
        painter.setTransform(transform, combine=True)

        pen = QPen(QColor(255, 165, 0), 2)
        pen.setCosmetic(True)  # Width stays constant regardless of zoom
        painter.setPen(pen)
        painter.setBrush(QColor(255, 165, 0, 50))

        cx, cy = self._center
        # Draw ellipse using center point and radii (Image Coordinates)
        painter.drawEllipse(QPointF(cx, cy), self._radius_x, self._radius_y)

        painter.restore()

    def show_context_menu(self, event: QMouseEvent):
        menu = QMenu(self.canvas_view)

        act_cancel = menu.addAction(
            self.translations[self.current_lang]["cancel_selection"]
        )
        act_cancel.triggered.connect(self.cancel)

        menu.addSeparator()

        act_undo = menu.addAction(self.translations[self.current_lang]["undo"])
        act_undo.triggered.connect(self.undo_last_action)

        act_redo = menu.addAction(self.translations[self.current_lang]["redo"])
        act_redo.triggered.connect(self.redo_last_action)

        menu.exec(event.globalPos())

    def undo_last_action(self):
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.undo(self.canvas_view.model)

    def redo_last_action(self):
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.redo(self.canvas_view.model)

    def cancel(self):
        self._center = None
        self._radius_x = 0
        self._radius_y = 0
        self._is_selecting = False
        self.canvas_view.update()

    def update_language(self, lang):
        self.current_lang = lang
