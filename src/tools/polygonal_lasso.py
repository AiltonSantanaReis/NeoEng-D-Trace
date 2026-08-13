# src/tools/polygonal_lasso.py
"""
Polygonal lasso selection tool for straight-edged selections.

This tool creates selections by clicking to place vertices of a polygon.
Clicking on the first point or double-clicking completes the selection.
"""

import math
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QMenu

from src.core.operational_limits import MAX_POLYGON_POINTS

from .base_tool import BaseTool


class PolygonalLassoTool(BaseTool):
    """
    Polygonal lasso selection tool.

    Creates selections with straight edges by placing vertices.
    """

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self._vertices: List[Tuple[float, float]] = []
        self._preview_point: Optional[Tuple[float, float]] = None
        self._close_tolerance = 10.0  # Pixels de tolerância para fechar o polígono

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

    def on_mouse_press(self, event: QMouseEvent, position: Tuple[float, float]):
        """
        Add vertex on mouse press or close polygon if near start.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                x, y = float(position[0]), float(position[1])
            except Exception:
                return

            # Verifica se está fechando o polígono (clicando perto do início)
            if len(self._vertices) >= 3:
                start_x, start_y = self._vertices[0]

                # Converte para coordenadas da tela para verificar a
                # distância visual (pixels)
                screen_click_x, screen_click_y = self.image_to_screen(x, y)
                screen_start_x, screen_start_y = self.image_to_screen(start_x, start_y)

                dist = math.hypot(
                    screen_click_x - screen_start_x,
                    screen_click_y - screen_start_y,
                )

                if dist <= self._close_tolerance:
                    object_id = self.commit_selection()
                    if object_id is not None:
                        self._vertices = []
                        self._preview_point = None
                    self.canvas_view.update()
                    return

            if len(self._vertices) < MAX_POLYGON_POINTS:
                self._vertices.append((x, y))
            self.canvas_view.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

    def on_mouse_move(self, event: QMouseEvent, position: Tuple[float, float]):
        """
        Update preview line on mouse move.
        """
        if self._vertices:
            x, y = position
            self._preview_point = (x, y)
            self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, position: Tuple[float, float]):
        pass

    def on_double_click(self, event: QMouseEvent, position: Tuple[float, float]):
        """
        Complete polygon on double-click or cancel if not enough vertices.
        """
        if len(self._vertices) < 3:
            # Preserve the in-progress selection. A double-click must not erase
            # two valid points merely because the polygon is not closable yet.
            return

        object_id = self.commit_selection()
        if object_id is None:
            # Keep the vertices available when creation fails so the user can
            # retry or cancel explicitly instead of losing work silently.
            return

        self._vertices = []
        self._preview_point = None
        self.canvas_view.update()

    def commit_selection(self):
        """Commit the polygonal selection through CommandManager."""
        if len(self._vertices) < 3:
            return None

        polygon = [(int(round(x)), int(round(y))) for x, y in self._vertices]
        return self.commit_polygon_command(
            polygon,
            action_name="Polygonal Lasso Creation",
        )

    def draw_overlay(self, painter: QPainter):
        """
        Draw the polygonal selection overlay.
        """
        if not self._vertices:
            return

        pen = QPen(QColor(0, 255, 0), 2)
        pen.setCosmetic(True)  # Mantém a espessura da linha constante no zoom
        painter.setPen(pen)

        screen_vertices = []
        for x, y in self._vertices:
            sx, sy = self.image_to_screen(x, y)
            screen_vertices.append((sx, sy))

        if len(screen_vertices) > 1:
            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPolygonF

            qpoints = [QPointF(sx, sy) for sx, sy in screen_vertices]
            painter.drawPolyline(QPolygonF(qpoints))

        # Desenha os vértices (pontinhos amarelos)
        vertex_pen = QPen(QColor(255, 255, 0), 1)
        vertex_pen.setCosmetic(True)
        painter.setPen(vertex_pen)
        painter.setBrush(QColor(255, 255, 0))

        for i, (sx, sy) in enumerate(screen_vertices):
            # Desenha o primeiro ponto maior para indicar onde fechar
            radius = 5 if i == 0 else 3
            painter.drawEllipse(
                int(sx) - radius, int(sy) - radius, radius * 2, radius * 2
            )

        # Linha de preview (tracejada)
        if self._preview_point and len(self._vertices) >= 1:
            preview_pen = QPen(QColor(255, 255, 255), 1, Qt.PenStyle.DashLine)
            preview_pen.setCosmetic(True)
            painter.setPen(preview_pen)

            last_x, last_y = self._vertices[-1]
            prev_sx, prev_sy = self.image_to_screen(last_x, last_y)
            mouse_sx, mouse_sy = self.image_to_screen(
                self._preview_point[0], self._preview_point[1]
            )

            painter.drawLine(int(prev_sx), int(prev_sy), int(mouse_sx), int(mouse_sy))

            # Se tiver vértices suficientes, desenha uma "sugestão"
            # de fechamento se o mouse estiver perto do início
            if len(self._vertices) >= 3:
                start_sx, start_sy = screen_vertices[0]
                dist = math.hypot(mouse_sx - start_sx, mouse_sy - start_sy)
                if dist <= self._close_tolerance:
                    # Highlight visual para mostrar que vai fechar
                    painter.setPen(QPen(QColor(0, 255, 0), 2))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(int(start_sx) - 8, int(start_sy) - 8, 16, 16)

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
        self._vertices = []
        self._preview_point = None
        self.canvas_view.update()

    def update_language(self, lang):
        self.current_lang = lang
