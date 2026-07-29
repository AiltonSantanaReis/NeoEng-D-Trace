"""Qt regression contracts for Etapa 0.6N1A.

Execute on Windows with Python 3.11 and PySide6.  The tests run offscreen and
cover both supported languages, palette sizing and non-blocking lasso preview.
"""

from __future__ import annotations

import os
import time
from unittest.mock import Mock, patch

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QApplication, QWidget

from src.models.scene import Scene
from src.tools.magnetic_lasso import MagneticLassoTool
from src.tools.magnetic_lasso_engine import (
    MagneticLassoSettings,
    build_edge_features,
)
from src.ui.export_dialog import ExportDialog
from src.ui.export_preview import ExportPreviewDialog
from src.ui.mask_viewer import MaskViewerDialog
from src.ui.tool_palette import ToolPalette


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


class _CanvasStub(QWidget):
    def __init__(self, image):
        super().__init__()
        self.scene = Mock()
        self.scene.get_image.return_value = image
        self.model = self.scene
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._tool = None

    def get_zoom(self):
        return 1.0

    def get_transform(self):
        return QTransform()

    def set_tool(self, tool):
        self._tool = tool


def _wait_until(app, predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    app.processEvents()
    return bool(predicate())


def test_export_dialog_is_bilingual_without_changing_profile_ids(qt_app):
    dialog = ExportDialog(Scene(), lang="pt")
    assert dialog.windowTitle() == "Opções de Exportação"
    assert dialog.btn_single.text() == "Exportar Sprite Selecionado"
    assert dialog.btn_gltf_scene.text() == "Exportar Cena Completa para GLTF"
    assert [
        dialog.metadata_profile.itemData(index)
        for index in range(dialog.metadata_profile.count())
    ] == ["generic", "godot", "unity", "phaser"]

    dialog.update_language("en")
    assert dialog.windowTitle() == "Export Options"
    assert dialog.btn_single.text() == "Export Selected Sprite"
    dialog.close()


def test_mask_viewer_is_bilingual_and_language_change_preserves_view(qt_app):
    scene = Scene()
    scene.image = np.zeros((64, 96, 4), dtype=np.uint8)
    dialog = MaskViewerDialog(scene, lang="pt")
    dialog.viewer.set_view_transform(1.75, 12.0, -8.0)

    assert dialog.windowTitle() == "Visualizador de Máscara - Raio-X de Detecção Automática"
    assert dialog.detect_button.text() == "Detectar Polígonos"
    assert dialog.preset_combo.itemData(0) == "Basic"
    assert dialog.preset_combo.itemText(0) == "Básico"

    dialog.update_language("en")
    assert dialog.windowTitle() == "Mask Viewer - Auto Detection X-Ray"
    assert dialog.preset_combo.itemData(0) == "Basic"
    assert dialog.preset_combo.itemText(0) == "Basic"
    assert dialog.viewer.get_view_transform() == pytest.approx((1.75, 12.0, -8.0))
    dialog.close()


def test_export_preview_is_bilingual(qt_app):
    pytest.importorskip("PIL")
    from PIL import Image

    dialog = ExportPreviewDialog(
        Image.new("RGBA", (16, 16), (255, 0, 0, 255)),
        {"id": "sprite", "pivot": {"x": 0.5, "y": 0.5}},
        lang="pt",
    )
    assert dialog.windowTitle() == "Pré-visualização da Exportação"
    assert dialog.export_button.text() == "Exportar"
    dialog.update_language("en")
    assert dialog.windowTitle() == "Export Preview"
    dialog.close()


def test_tool_palette_resizes_for_every_label_in_both_languages(qt_app):
    canvas = _CanvasStub(np.zeros((32, 32), dtype=np.uint8))
    palette = ToolPalette(canvas)
    palette.show()

    for language in ("pt", "en"):
        palette.update_language(language)
        qt_app.processEvents()
        for button in palette.tool_buttons.values():
            widest = max(
                button.fontMetrics().horizontalAdvance(line)
                for line in button.text().splitlines()
            )
            # 16 px custom padding + 6 px borders. The actual button width must
            # contain the complete widest line at the active font/DPI.
            assert button.width() >= widest + 22, (language, button.text())
            assert button.width() <= palette.width() - 16

    palette.close()
    canvas.close()


def test_magnetic_preview_returns_immediately_and_completes_in_worker(qt_app):
    image = np.zeros((160, 220), dtype=np.uint8)
    image[:, 110:] = 255
    canvas = _CanvasStub(image)
    settings = MagneticLassoSettings(mode="precise")
    tool = MagneticLassoTool(canvas, settings=settings)
    features = build_edge_features(image)
    tool._edge_features = features
    tool._edge_map = features.strength
    tool._last_image_token = tool._current_image_token()
    tool._anchors = [(109, 20)]
    tool._path = [(109, 20)]

    def deliberately_slow_preview(_features, start, end, _settings):
        time.sleep(0.25)
        return [tuple(start), tuple(end)]

    with patch(
        "src.tools.magnetic_lasso.live_wire_preview_path",
        side_effect=deliberately_slow_preview,
    ):
        started = time.perf_counter()
        tool.on_mouse_move(Mock(), (109, 130))
        elapsed = time.perf_counter() - started
        assert elapsed < 0.10
        assert _wait_until(qt_app, lambda: bool(tool._preview_path), timeout=2.0)

    assert tool._preview_path == [(109, 20), (109, 130)]
    canvas.close()

def test_magnetic_confirmed_segment_also_runs_outside_gui_thread(qt_app):
    image = np.zeros((160, 220), dtype=np.uint8)
    image[:, 110:] = 255
    canvas = _CanvasStub(image)
    settings = MagneticLassoSettings(mode="precise")
    tool = MagneticLassoTool(canvas, settings=settings)
    features = build_edge_features(image)
    tool._edge_features = features
    tool._edge_map = features.strength
    tool._last_image_token = tool._current_image_token()
    tool._anchors = [(109, 20)]
    tool._path = [(109, 20)]

    def deliberately_slow_commit(_features, start, end, _settings):
        time.sleep(0.25)
        return [tuple(start), tuple(end)]

    event = Mock()
    event.button.return_value = Qt.MouseButton.LeftButton
    with patch(
        "src.tools.magnetic_lasso.live_wire_path",
        side_effect=deliberately_slow_commit,
    ):
        started = time.perf_counter()
        tool.on_mouse_press(event, (109, 130))
        elapsed = time.perf_counter() - started
        assert elapsed < 0.10
        assert tool._segment_pending is True
        assert _wait_until(qt_app, lambda: len(tool._anchors) == 2, timeout=2.0)

    assert tool._anchors[-1] == (109, 130)
    assert tool._segment_pending is False
    canvas.close()

