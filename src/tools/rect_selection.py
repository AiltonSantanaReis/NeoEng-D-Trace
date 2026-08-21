# src/tools/rect_selection.py
"""
Rectangle selection tool for rectangular selections.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QMenu

from .base_tool import BaseTool


class RectSelectionTool(BaseTool):
    """
    Rectangular selection tool.
    Allows creating box-shaped polygons.
    """

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self._start_point = None  # Image coordinates
        self._end_point = None  # Image coordinates
        self._is_selecting = False

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
            self._start_point = (x, y)
            self._end_point = (x, y)
            self.canvas_view.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

    def on_mouse_move(self, event: QMouseEvent, position: tuple):
        if self._is_selecting and self._start_point:
            x, y = position

            # Shift modifier for square selection
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                dx = x - self._start_point[0]
                dy = y - self._start_point[1]
                size = max(abs(dx), abs(dy))

                sign_x = 1 if dx >= 0 else -1
                sign_y = 1 if dy >= 0 else -1

                self._end_point = (
                    self._start_point[0] + sign_x * size,
                    self._start_point[1] + sign_y * size,
                )
            else:
                self._end_point = (x, y)

            self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, position: tuple):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            object_id = self.commit_selection()
            if object_id is not None:
                self._start_point = None
                self._end_point = None
            self.canvas_view.update()

    def commit_selection(self):
        if not self._start_point or not self._end_point:
            return None

        x1, y1 = self._start_point
        x2, y2 = self._end_point

        # Avoid zero-area polygons
        if abs(x1 - x2) < 1 or abs(y1 - y2) < 1:
            return None

        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)

        # Create rectangle polygon (4 points)
        polygon = [
            (int(round(left)), int(round(top))),
            (int(round(right)), int(round(top))),
            (int(round(right)), int(round(bottom))),
            (int(round(left)), int(round(bottom))),
        ]

        return self.commit_polygon_command(
            polygon,
            action_name="Rectangle Creation",
        )

    def draw_overlay(self, painter: QPainter):
        """
        Draws the selection rectangle during drag.
        """
        if not self._start_point or not self._end_point:
            return

        # Transform to screen coordinates
        # Since CanvasView resets transform before calling overlay,
        # we need to apply the image transform
        transform = self.canvas_view.get_transform()

        painter.save()
        painter.setTransform(transform, combine=True)

        x1, y1 = self._start_point
        x2, y2 = self._end_point

        width = x2 - x1
        height = y2 - y1

        # Use cosmetic pen for consistent thickness regardless of zoom
        pen = QPen(QColor(0, 120, 255), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 120, 255, 50))

        # Draw in image space (transform handles the rest)
        painter.drawRect(QRectF(x1, y1, width, height))

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
        self._start_point = None
        self._end_point = None
        self._is_selecting = False
        self.canvas_view.update()

    def update_language(self, lang):
        self.current_lang = lang
