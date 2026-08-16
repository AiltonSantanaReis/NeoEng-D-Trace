from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication
import pytest

from src.ui.gizmo import TransformGizmo


def test_reference_gizmo_exposes_contextual_2d_handles():
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(100, 100))

    assert gizmo.hit_test(QPointF(100, 100)) == gizmo.CENTER
    assert gizmo.hit_test(QPointF(108, 100)) == gizmo.SCALE_UNIFORM
    assert gizmo.hit_test(QPointF(150, 100)) == gizmo.AXIS_X
    assert gizmo.hit_test(QPointF(100, 50)) == gizmo.AXIS_Y
    assert gizmo.hit_test(QPointF(100, 85)) == gizmo.TRANSLATE_XY
    assert gizmo.hit_test(QPointF(176, 100)) == gizmo.SCALE_X
    assert gizmo.hit_test(QPointF(100, 24)) == gizmo.SCALE_Y
    assert gizmo.hit_test(QPointF(136, 136)) == gizmo.ROTATE_Z


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_reference_gizmo_draws_without_transparent_collapse(qt_app):
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(110, 110))
    image = QImage(240, 240, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    gizmo.draw(painter)
    painter.end()

    assert image.pixelColor(110, 110).alpha() > 0
    assert image.pixelColor(186, 110).alpha() > 0
    assert image.pixelColor(110, 34).alpha() > 0
