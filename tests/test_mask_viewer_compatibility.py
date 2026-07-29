import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from src.ui.mask_viewer import MaskViewer


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_mask_viewer_view_transform_compatibility(qt_app):
    viewer = MaskViewer()

    viewer.set_view_transform(1.5, 5.0, 15.0)

    assert viewer.get_view_transform() == (1.5, 5.0, 15.0)


def test_mask_viewer_coordinate_methods_accept_tuple_and_qpointf(qt_app):
    viewer = MaskViewer()
    viewer.set_view_transform(2.0, 10.0, 20.0)

    view_point = viewer.image_to_view((50.0, 75.0))
    assert isinstance(view_point, QPointF)

    image_point = viewer.view_to_image(view_point)
    assert image_point == pytest.approx((50.0, 75.0))

    from_qpoint = viewer.image_to_view(QPointF(*image_point))
    assert from_qpoint.x() == pytest.approx(view_point.x())
    assert from_qpoint.y() == pytest.approx(view_point.y())
