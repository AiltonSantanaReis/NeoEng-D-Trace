from types import SimpleNamespace

from PySide6.QtCore import Qt

from src.ui.collision_overlay import CollisionOverlay


class _PainterProbe:
    def __init__(self) -> None:
        self.brush = None
        self.pen = None
        self.polygon = None

    def setBrush(self, brush) -> None:
        self.brush = brush

    def setPen(self, pen) -> None:
        self.pen = pen

    def drawPolygon(self, points) -> None:
        self.polygon = points


def test_arrowhead_uses_no_pen_and_draws_triangle() -> None:
    overlay = CollisionOverlay(SimpleNamespace(collision_shapes={}))
    painter = _PainterProbe()

    overlay._draw_arrowhead(painter, 0.0, 0.0, 10.0, 0.0)

    assert painter.pen == Qt.PenStyle.NoPen
    assert painter.polygon is not None
    assert len(painter.polygon) == 3


def test_arrowhead_skips_zero_length_vector() -> None:
    overlay = CollisionOverlay(SimpleNamespace(collision_shapes={}))
    painter = _PainterProbe()

    overlay._draw_arrowhead(painter, 5.0, 5.0, 5.0, 5.0)

    assert painter.pen is None
    assert painter.polygon is None
