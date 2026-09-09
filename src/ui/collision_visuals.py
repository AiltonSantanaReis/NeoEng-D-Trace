"""Shared collision geometry styling used by the mask viewer and viewport."""

from PySide6.QtGui import QColor, QPen


def collision_outline_pen() -> QPen:
    """Return the canonical green collision outline used in previews."""

    pen = QPen(QColor(0, 255, 0), 2)
    pen.setCosmetic(True)
    return pen


def collision_fill_brush() -> QColor:
    """Return the canonical translucent green collision fill."""

    return QColor(0, 255, 0, 50)
