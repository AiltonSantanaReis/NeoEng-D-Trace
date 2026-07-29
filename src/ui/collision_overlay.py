# src/ui/collision_overlay.py
"""
Collision Overlay for Canvas View
Draws physics collision shapes and collision indicators on the canvas.
"""

from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen


class CollisionOverlay:
    """
    Overlay component for displaying physics collision shapes
    and collision indicators.
    """

    def __init__(self, scene):
        self.scene = scene
        self.visible = False
        self.collision_results: List[Dict[str, Any]] = []
        self.collision_colors = {
            "no_collision": QColor(0, 255, 0, 128),
            "collision": QColor(255, 0, 0, 128),
            "mtv": QColor(255, 255, 0, 200),
        }

    def set_visible(self, visible: bool):
        self.visible = visible

    def update_collision_results(self, results: List[Dict]):
        self.collision_results = results

    def draw(self, painter: QPainter, zoom: float, pan: Tuple[float, float]):
        if not self.visible:
            return

        painter.save()

        # Aplica transformação da câmera (Mundo -> Tela)
        painter.translate(pan[0], pan[1])
        painter.scale(zoom, zoom)

        self._draw_collision_shapes(painter, zoom)
        self._draw_collision_indicators(painter)

        painter.restore()

    def _draw_collision_shapes(self, painter: QPainter, zoom: float):
        # Ajusta fonte para manter tamanho legível independente do zoom
        font = painter.font()
        # Tamanho base 10 dividido pelo zoom mantém o tamanho visual constante
        scaled_font_size = max(1.0, 10.0 / zoom) if zoom > 0 else 10.0
        font.setPointSizeF(scaled_font_size)
        painter.setFont(font)

        for shape_id, shape in self.scene.collision_shapes.items():
            if len(shape) < 3:
                continue

            color = self._get_shape_color(shape_id)

            # Pen Cosmética: Mantém espessura visual de 2px independente do zoom
            pen = QPen(color.darker(150), 2)
            pen.setCosmetic(True)

            painter.setPen(pen)
            painter.setBrush(QBrush(color))

            points = [QPointF(x, y) for x, y in shape]
            if points:
                painter.drawPolygon(points)

            # Contorno preto fino
            outline_pen = QPen(QColor(0, 0, 0), 1)
            outline_pen.setCosmetic(True)
            painter.setPen(outline_pen)
            painter.setBrush(QBrush())  # No fill
            painter.drawPolygon(points)

            # Label do ID
            if points:
                # Desenha texto um pouco acima do primeiro ponto
                label_x, label_y = shape[0]
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                # Offset ajustado pelo zoom para não ficar colado
                offset = 5.0 / zoom
                painter.drawText(
                    QPointF(label_x + offset, label_y - offset), str(shape_id)[:8]
                )

    def _draw_collision_indicators(self, painter: QPainter):
        for result in self.collision_results:
            if not result.get("colliding", False):
                continue

            obj1_id = result.get("obj1_id")
            obj2_id = result.get("obj2_id")
            mtv = result.get("mtv")

            if (
                not all([obj1_id, obj2_id, mtv])
                or not isinstance(obj1_id, str)
                or not isinstance(obj2_id, str)
                or not isinstance(mtv, (list, tuple))
                or len(mtv) < 2
            ):
                continue

            center1 = self._get_shape_center(obj1_id)
            center2 = self._get_shape_center(obj2_id)

            if center1 and center2:
                # Desenha o vetor MTV a partir do centro do contato (aproximado)
                start_x = center1[0] + mtv[0] * 0.5
                start_y = center1[1] + mtv[1] * 0.5
                end_x = center1[0] + mtv[0]
                end_y = center1[1] + mtv[1]

                pen = QPen(self.collision_colors["mtv"], 3)
                pen.setCosmetic(True)
                painter.setPen(pen)

                painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

                self._draw_arrowhead(painter, start_x, start_y, end_x, end_y)

    def _get_shape_color(self, shape_id: str) -> QColor:
        for result in self.collision_results:
            if result.get("colliding") and shape_id in [
                result.get("obj1_id"),
                result.get("obj2_id"),
            ]:
                return self.collision_colors["collision"]
        return self.collision_colors["no_collision"]

    def _get_shape_center(self, shape_id: str) -> Optional[Tuple[float, float]]:
        shape = self.scene.collision_shapes.get(shape_id)
        if not shape:
            return None
        sum_x = sum(x for x, y in shape)
        sum_y = sum(y for x, y in shape)
        return (sum_x / len(shape), sum_y / len(shape))

    def _draw_arrowhead(
        self,
        painter: QPainter,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        size: float = 10.0,
    ):
        dx = end_x - start_x
        dy = end_y - start_y
        length = (dx**2 + dy**2) ** 0.5

        if length == 0:
            return

        dx /= length
        dy /= length

        # Vetor perpendicular
        px = -dy
        py = dx

        # Ajusta tamanho da seta relativo ao comprimento se for muito pequeno
        arrow_size = size

        # Coordenadas da ponta da seta
        ax1 = end_x - dx * arrow_size + px * arrow_size * 0.5
        ay1 = end_y - dy * arrow_size + py * arrow_size * 0.5
        ax2 = end_x - dx * arrow_size - px * arrow_size * 0.5
        ay2 = end_y - dy * arrow_size - py * arrow_size * 0.5

        painter.setBrush(QBrush(self.collision_colors["mtv"]))

        # Remove pen para a ponta ficar sólida
        painter.setPen(Qt.PenStyle.NoPen)

        points = [QPointF(end_x, end_y), QPointF(ax1, ay1), QPointF(ax2, ay2)]
        painter.drawPolygon(points)
