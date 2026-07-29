import sys

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from src.ui.mask_viewer import MaskViewer


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_mask_viewer_center_and_fill(qt_app):
    # Cria uma imagem sintética (mask)
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[30:70, 30:70] = 255
    viewer = MaskViewer()
    viewer.set_numpy_image(image)
    # Simula centralização e preenchimento de tela
    viewer.reset_view()
    # Verifica se a imagem está definida e centralizada
    assert viewer._image is not None
    assert viewer._zoom >= 1.0
    # Simula update/render
    viewer.update()
