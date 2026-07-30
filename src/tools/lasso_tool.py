# src/tools/lasso_tool.py
"""
Lasso selection tool for free-form selections.
"""

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QMenu

from .base_tool import BaseTool
from .mask_utils import rdp_simplify


class LassoTool(BaseTool):
    """
    Free-form lasso selection tool.
    Allows drawing arbitrary polygon shapes.
    """

    def __init__(self, canvas_view, model=None):
        super().__init__(canvas_view)
        # Handle optional model argument for compatibility
        self.model = model if model else getattr(canvas_view, "model", None)
        self._points = []
        self._is_drawing = False
        self._sample_dist = 3
        self._last_point = None
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
            self._is_drawing = True
            self._points = []
            x, y = position
            self._points.append((x, y))
            self._last_point = (x, y)
            self.canvas_view.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

    def on_mouse_move(self, event: QMouseEvent, position: tuple):
        if self._is_drawing:
            x, y = position
            # Evita duplicidade de pontos e melhora precisão
            if self._last_point:
                dist = math.hypot(x - self._last_point[0], y - self._last_point[1])
                if dist >= self._sample_dist:
                    # Só adiciona se não for igual ao último
                    if (x, y) != self._last_point:
                        self._points.append((x, y))
                        self._last_point = (x, y)
            else:
                self._points.append((x, y))
                self._last_point = (x, y)
            self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, position: tuple):
        if event.button() == Qt.MouseButton.LeftButton and self._is_drawing:
            self._is_drawing = False
            self.commit_selection()
            self._points = []
            self._last_point = None
            self.canvas_view.update()

    def commit_selection(self):
        if len(self._points) < 3:
            return None

        simplified = rdp_simplify(self._points, epsilon=2.0)
        polygon = [(int(round(x)), int(round(y))) for x, y in simplified]

        try:
            if (
                hasattr(self.canvas_view.model, "cmd")
                and self.canvas_view.model.cmd is not None
            ):
                from src.core.commands import AddPolygonCommand

                cmd = AddPolygonCommand(polygon)
                self.canvas_view.model.cmd.execute(cmd, self.canvas_view.model)
                return cmd.object_id
            else:
                oid = self.canvas_view.model.add_polygon(polygon)
                return oid
        except Exception as e:
            print(f"Error adding lasso: {e}")
            return None

    def draw_overlay(self, painter: QPainter):
        """
        Draws the lasso path in real-time.
        Uses view transform for performance.
        """
        if not self._points:
            return

        # Setup transform to draw in Image Space
        transform = self.canvas_view.get_transform()
        painter.save()
        painter.setTransform(transform, combine=True)

        pen = QPen(QColor(255, 0, 0), 2)
        pen.setCosmetic(True)  # Constant width
        painter.setPen(pen)

        if len(self._points) > 1:
            # Convert list of tuples to QPolygonF for efficient drawing
            qpoints = [QPointF(float(p[0]), float(p[1])) for p in self._points]
            painter.drawPolyline(QPolygonF(qpoints))

        painter.restore()

    def show_context_menu(self, event: QMouseEvent):
        menu = QMenu(self.canvas_view)
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d30; color: #e6e6e6;
            border: 1px solid #3f3f46; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #2a6f97; }
            QMenu::separator { height: 1px; background: #3f3f46;
            margin: 5px 0; }
        """)

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
        self._points = []
        self._is_drawing = False
        self._last_point = None
        self.canvas_view.update()

    def update_language(self, lang):
        self.current_lang = lang
