import sys

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from src.ui.mask_viewer import MaskViewer, MaskViewerDialog


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


def test_mask_detection_presets_are_visible_and_keep_active_state(qt_app):
    dialog = MaskViewerDialog(_scene_for_dialog(), lang="en")
    try:
        dialog.show()
        qt_app.processEvents()
        assert len(dialog.preset_actions) == 4
        assert all(action.isVisible() for action in dialog.preset_actions.values())
        assert dialog.preset_actions["Basic"].isChecked()
        dialog.preset_actions["Enhanced"].trigger()
        qt_app.processEvents()
        assert dialog.preset_combo.currentData() == "Enhanced"
        assert dialog.preset_actions["Enhanced"].isChecked()
        assert not dialog.preset_actions["Basic"].isChecked()
        assert dialog.view_mode_toolbar_row.isVisible()
    finally:
        dialog.close()


def _scene_for_dialog():
    from src.core.commands import CommandManager
    from src.models.scene import Scene

    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.image = np.zeros((32, 48, 4), dtype=np.uint8)
    scene.image[:, :, 3] = 255
    return scene
