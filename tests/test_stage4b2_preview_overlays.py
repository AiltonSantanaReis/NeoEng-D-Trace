from __future__ import annotations

import hashlib

import numpy as np
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scenario_preview import ScenarioPreviewLayer
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = np.zeros((96, 96, 4), dtype=np.uint8)
    scene.image[:, :, 3] = 255
    scene.add_object(
        "object_a",
        [(10, 10), (50, 10), (50, 50), (10, 50)],
        select=True,
    )
    scene.cmd.clear()
    return scene


def _png_hash(widget: CanvasView) -> str:
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert widget.grab().save(buffer, "PNG")
    buffer.close()
    return hashlib.sha256(bytes(data)).hexdigest()


def test_canvas_preview_is_read_only_and_restores_normal_editing(qt_app: QApplication):
    scene = _scene()
    original_polygon = list(scene.objects["object_a"].polygon)
    original_position = scene.objects["object_a"].position
    canvas = CanvasView(scene)
    canvas.resize(640, 480)
    canvas.show()
    qt_app.processEvents()
    try:
        normal_hash = _png_hash(canvas)
        canvas.set_scenario_preview_layers(
            [
                ScenarioPreviewLayer(
                    "far_background",
                    ("object_a",),
                    ParallaxLayer(depth=0.8, translation_strength=1.0),
                )
            ]
        )
        canvas.set_scenario_camera(
            OrthographicCamera((640, 480), position=(8.0, 6.0), zoom=1.5)
        )
        canvas.set_scenario_preview_enabled(True)
        assert canvas.is_scenario_preview_enabled() is True
        assert canvas._tool is None
        preview_hash = _png_hash(canvas)
        assert preview_hash != normal_hash

        QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(30, 30))
        QTest.mousePress(canvas, Qt.MouseButton.MiddleButton, pos=QPoint(300, 220))
        QTest.mouseMove(canvas, QPoint(340, 250), 20)
        QTest.mouseRelease(canvas, Qt.MouseButton.MiddleButton, pos=QPoint(340, 250))
        qt_app.processEvents()

        assert scene.objects["object_a"].polygon == original_polygon
        assert scene.objects["object_a"].position == original_position
        assert scene.selected_id == "object_a"
        assert scene.cmd.undo_count == 0
        assert canvas._scenario_camera is not None
        assert canvas._scenario_camera.position != (8.0, 6.0)

        canvas.resize(800, 600)
        qt_app.processEvents()
        canvas.set_scenario_overlays_visible(True, aspect_ratio=(16, 9))
        overlay_hash = _png_hash(canvas)
        assert overlay_hash != preview_hash
        assert canvas._scenario_overlay_geometry is not None
        assert canvas._scenario_overlay_geometry.viewport_size == (800.0, 600.0)

        canvas.set_scenario_preview_enabled(False)
        assert canvas.is_scenario_preview_enabled() is False
        scene.select_object(None)
        QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
        assert scene.selected_id == "object_a"
        assert scene.objects["object_a"].polygon == original_polygon
    finally:
        canvas.close()


def test_main_window_exposes_preview_and_overlay_actions_without_side_effects(
    qt_app: QApplication,
):
    window = MainWindow(Scene(), {})
    try:
        window.show()
        qt_app.processEvents()
        assert window.scenario_preview_action.isCheckable()
        assert window.scenario_preview_action.isChecked() is False
        assert window.scenario_overlays_action.isCheckable()
        assert window.scenario_overlays_action.isChecked() is False
        assert window.scenario_overlays_action.isEnabled() is False

        window.scenario_preview_action.trigger()
        qt_app.processEvents()
        assert window.canvas.is_scenario_preview_enabled() is True
        assert window.scenario_overlays_action.isEnabled() is True

        window.scenario_overlays_action.trigger()
        qt_app.processEvents()
        assert window.canvas.is_scenario_overlays_visible() is True

        window.set_language("pt")
        assert window.scenario_preview_action.text() == (
            "Preview de Cenário (Somente Leitura)"
        )
        assert window.scenario_overlays_action.text() == (
            "Molduras Seguras e Máscara de Corte"
        )

        window.scenario_preview_action.trigger()
        qt_app.processEvents()
        assert window.canvas.is_scenario_preview_enabled() is False
        assert window.canvas.is_scenario_overlays_visible() is False
        assert window.scenario_overlays_action.isEnabled() is False
        assert window.scenario_overlays_action.isChecked() is False
    finally:
        window.close()
        qt_app.processEvents()
