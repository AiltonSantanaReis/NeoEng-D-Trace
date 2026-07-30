# src/tools/selection_tool.py
"""
Selection tool for selecting polygons and vertices.
"""

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent, QPainter, QPolygonF

from .base_tool import BaseTool


class SelectionTool(BaseTool):
    """
    Selection tool for polygons and vertices.
    """

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self.current_lang = "en"
        self.translations = {
            "en": {
                "select_object": "Select Object",
                "select_vertex": "Select Vertex",
            },
            "pt": {
                "select_object": "Selecionar Objeto",
                "select_vertex": "Selecionar Vértice",
            },
        }

    def on_mouse_press(self, event: QMouseEvent, position: tuple):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = position
            # Find object at position
            clicked_id = self._find_object_at(QPointF(x, y))
            if clicked_id:
                if hasattr(self.canvas_view.model, "select_object"):
                    self.canvas_view.model.select_object(clicked_id)
                self.canvas_view.update()
            else:
                # Deselect if clicked on empty
                if hasattr(self.canvas_view.model, "select_object"):
                    self.canvas_view.model.select_object(None)
                self.canvas_view.update()

    def on_mouse_move(self, event: QMouseEvent, position: tuple):
        pass

    def on_mouse_release(self, event: QMouseEvent, position: tuple):
        pass

    def on_double_click(self, event: QMouseEvent, position: tuple):
        pass

    def on_cancel(self):
        pass

    def draw_overlay(self, painter: QPainter):
        pass

    def _find_object_at(self, point):
        objects = getattr(self.canvas_view.model, "objects", {})
        for oid, obj in reversed(list(objects.items())):
            poly = getattr(obj, "polygon", [])
            if len(poly) < 3:
                continue
            poly_float = [QPointF(float(p[0]), float(p[1])) for p in poly]
            qpoly = QPolygonF(poly_float)
            if qpoly.containsPoint(point, Qt.FillRule.OddEvenFill):
                return oid
        return None
