# src/tools/lasso_tool.py
from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF

from src.core.logger import logger

from .mask_utils import rdp_simplify


class LassoTool:
    """
    Ferramenta de Laço (Freehand) para seleção de polígonos.
    Permite desenhar livremente e simplifica a forma ao soltar o mouse.
    """

    def __init__(self, canvas_view, model, simplify_eps: float = 2.0):
        self.canvas_view = canvas_view
        self.model = model
        self._points: List[Tuple[int, int]] = []
        self._active = False
        self._eps = float(simplify_eps)

        # Configuração visual do rastro
        self._pen = QPen(QColor(0, 255, 0), 2)
        self._pen.setCosmetic(True)  # Mantém espessura visual constante no zoom

    def interface(self):
        from src.ui.canvas_view import ToolInterface

        return ToolInterface(
            on_mouse_press=self.on_mouse_press,
            on_mouse_move=self.on_mouse_move,
            on_mouse_release=self.on_mouse_release,
            on_double_click=self.on_double_click,
            on_cancel=self.on_cancel,
            draw_overlay=self.draw_overlay,
            update_language=self.update_language,
        )

    def update_language(self, lang: str):
        """Atualiza textos da ferramenta se necessário."""
        pass

    def draw_overlay(self, painter: QPainter):
        """
        Desenha o rastro do laço em tempo real.
        O CanvasView chama isso em coordenadas de tela (Screen Space).
        """
        if not self._active or not self._points:
            return

        # Como os pontos (_points) estão em coordenadas de IMAGEM,
        # e o CanvasView reseta o transform antes do overlay,
        # precisamos aplicar a transformação da view manualmente.
        transform = self.canvas_view.get_transform()

        painter.save()
        painter.setTransform(transform, combine=True)
        painter.setPen(self._pen)

        # Converte lista de tuplas para QPolygonF para desenho otimizado
        poly_points = [QPointF(float(p[0]), float(p[1])) for p in self._points]
        painter.drawPolyline(QPolygonF(poly_points))

        painter.restore()

    def on_mouse_press(self, event: QMouseEvent, pt: Tuple[int, int]):
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = True
            self._points = [pt]

    def on_mouse_move(self, event: QMouseEvent, pt: Tuple[int, int]):
        if not self._active:
            return

        # Otimização: Evitar adicionar pontos duplicados adjacentes
        if self._points and self._points[-1] == pt:
            return

        self._points.append(pt)

    def on_mouse_release(self, event: QMouseEvent, pt: Tuple[int, int]):
        if event.button() == Qt.MouseButton.LeftButton and self._active:
            # Finaliza o desenho
            if len(self._points) >= 3:
                try:
                    # Simplificação RDP para reduzir ruído do mouse
                    simplified = rdp_simplify(self._points, epsilon=self._eps)

                    # Garante inteiros para o modelo
                    polygon = [(int(round(x)), int(round(y))) for x, y in simplified]

                    # Adiciona ao modelo (suporta Undo via CommandManager interno da Scene)
                    self.model.add_polygon(polygon)

                except Exception as e:
                    logger.error(f"Erro ao adicionar polígono no Lasso: {e}")

            # Reset
            self._points = []
            self._active = False
            self.canvas_view.update()

    def on_double_click(self, event: QMouseEvent, pt: Tuple[int, int]):
        # Clique duplo força o fechamento
        self.on_mouse_release(event, pt)

    def on_cancel(self):
        self._points = []
        self._active = False
        self.canvas_view.update()
