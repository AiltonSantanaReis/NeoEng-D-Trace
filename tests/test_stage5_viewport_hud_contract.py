from __future__ import annotations

import sys

import numpy as np
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea

from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.main_window import MainWindow
from src.ui.mask_viewer import MaskViewer, MaskViewerDialog


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def _bgr_fixture() -> np.ndarray:
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    image[:, :] = (30, 20, 10)
    image[30:90, 40:120] = (0, 0, 255)
    return image


def test_stage5_viewport_status_has_live_pan_and_overlay_responsive_labels(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    try:
        window.show()
        window.resize(1280, 720)
        qt_app.processEvents()
        window.canvas.set_vertex_snapping(True, grid_size=16)
        window.canvas.set_grid_visible(False)
        window.canvas._pan.setX(12)
        window.canvas._pan.setY(-8)
        window.canvas._emit_viewport_state()
        state = window.canvas.viewport_state()
        assert state.pan_x == pytest.approx(12.0)
        assert state.pan_y == pytest.approx(-8.0)
        assert state.snap_enabled is True
        assert state.snap_grid_size == 16
        assert state.grid_visible is False
        assert window.viewport_status.toolTip()
        overlay = window.viewport_chrome.overlay
        assert overlay._compact is True
        assert overlay.view_button.text() == "Lit"
        assert overlay.zoom_button.text() == "1.00x"
        assert overlay.snap_button.text().startswith("Snap ")
        for child in (overlay.view_button, overlay.zoom_button, overlay.snap_button):
            assert overlay.rect().contains(child.geometry())
        top_position = overlay.pos().y()
        assert 0 <= top_position <= 16
        overlay.snap_button.click()
        qt_app.processEvents()
        assert overlay.pos().y() == top_position

        window.resize(1920, 1080)
        qt_app.processEvents()
        assert overlay._compact is False
        assert overlay.view_button.text().startswith("View: ")
        assert overlay.zoom_button.text().startswith("Zoom: ")
        assert 0 <= overlay.pos().y() <= 16
    finally:
        window.close()


@pytest.mark.parametrize("mode", [0, 1, 2, 3])
def test_stage5_mask_viewer_preserves_original_and_xray_modes(qt_app, mode):
    viewer = MaskViewer()
    try:
        viewer.resize(400, 300)
        viewer.show()
        viewer.set_numpy_image(_bgr_fixture())
        viewer.set_display_mode(mode)
        assert viewer.get_display_mode() == mode
        assert viewer._display_image is not None
        qimage = viewer._get_qimage()
        assert qimage is not None and not qimage.isNull()
        if mode == 0:
            color = qimage.pixelColor(0, 0)
            assert (color.red(), color.green(), color.blue()) == (10, 20, 30)
    finally:
        viewer.close()


def test_stage5_mask_viewer_supports_bgra_and_detached_qimage(qt_app):
    viewer = MaskViewer()
    try:
        image = np.zeros((4, 4, 4), dtype=np.uint8)
        image[:, :] = (30, 20, 10, 128)
        viewer.set_numpy_image(image)
        qimage = viewer._get_qimage()
        assert qimage is not None
        color = qimage.pixelColor(0, 0)
        assert (color.red(), color.green(), color.blue(), color.alpha()) == (
            10,
            20,
            30,
            128,
        )
        image[:, :] = 0
        color_after_source_mutation = qimage.pixelColor(0, 0)
        assert (
            color_after_source_mutation.red(),
            color_after_source_mutation.green(),
            color_after_source_mutation.blue(),
            color_after_source_mutation.alpha(),
        ) == (10, 20, 30, 128)
    finally:
        viewer.close()


def test_stage5_mask_viewer_mouse_keyboard_roi_and_limits(qt_app):
    viewer = MaskViewer()
    try:
        viewer.resize(400, 300)
        viewer.show()
        viewer.set_numpy_image(_bgr_fixture())
        viewer.set_view_transform(2.0, 10.0, 20.0)
        QTest.mousePress(viewer, Qt.MouseButton.MiddleButton, pos=QPoint(100, 100))
        QTest.mouseMove(viewer, QPoint(130, 125))
        QTest.mouseRelease(viewer, Qt.MouseButton.MiddleButton, pos=QPoint(130, 125))
        assert viewer.get_pan() == pytest.approx((40.0, 45.0))
        QTest.keyClick(viewer, Qt.Key.Key_R)
        assert viewer.get_pan() != (40.0, 45.0)
        viewer.set_zoom(0.001)
        assert viewer.get_zoom() == pytest.approx(0.1)
        viewer.set_zoom(100.0)
        assert viewer.get_zoom() == pytest.approx(8.0)
        viewer.set_roi_mode(True)
        QTest.mousePress(viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        QTest.mouseMove(viewer, QPoint(220, 180))
        QTest.mouseRelease(viewer, Qt.MouseButton.LeftButton, pos=QPoint(220, 180))
        assert viewer.get_roi() is not None
        assert viewer.focusPolicy().name == "StrongFocus"
    finally:
        viewer.close()


@pytest.mark.parametrize("size", [(1280, 720), (1366, 768), (1920, 1080)])
def test_stage5_mask_viewer_dialog_has_real_controls_and_no_clipping(qt_app, size):
    scene = Scene()
    scene.load_image(_bgr_fixture(), "stage5-mask-fixture.png")
    dialog = MaskViewerDialog(scene)
    try:
        dialog.resize(*size)
        dialog.show()
        qt_app.processEvents()
        scroll = dialog.findChild(QScrollArea, "mask_controls_scroll")
        assert scroll is not None and scroll.isVisibleTo(dialog)
        assert dialog.viewer.isVisibleTo(dialog)
        assert dialog.rect().contains(scroll.geometry())
        assert dialog.rect().contains(dialog.viewer.geometry())
        assert all(button.isEnabled() for button in dialog.view_mode_buttons)
        for index, button in enumerate(dialog.view_mode_buttons):
            button.click()
            assert dialog.viewer.get_display_mode() == index
    finally:
        dialog.close()


def test_stage5_mask_viewer_fits_after_layout_and_selects_processing_source(qt_app):
    viewer = MaskViewer()
    dialog = None
    try:
        viewer.resize(400, 300)
        viewer.show()
        viewer.set_numpy_image(np.zeros((80, 160, 3), dtype=np.uint8))
        qt_app.processEvents()

        center = viewer.image_to_view(QPointF(80, 40))
        assert center.x() == pytest.approx(200.0)
        assert center.y() == pytest.approx(150.0)
        assert viewer.get_zoom() == pytest.approx(3.75)

        viewer.set_numpy_image(_bgr_fixture())
        viewer.set_display_mode(2)
        original = viewer.get_processing_image()
        active = viewer.get_processing_image(use_active_view=True)
        assert original is not None and active is not None
        assert original.shape == active.shape
        assert not np.array_equal(original, active)

        scene = Scene()
        scene.load_image(_bgr_fixture(), "stage5-source-fixture.png")
        dialog = MaskViewerDialog(scene)
        dialog.view_mode_combo.setCurrentIndex(2)
        dialog.processing_source_combo.setCurrentIndex(1)
        selected = dialog._get_detection_image()
        assert selected is not None
        assert np.array_equal(selected, dialog.viewer.get_processing_image(True))
    finally:
        if dialog is not None:
            dialog.close()
        viewer.close()


def test_stage5_xray_mode_is_requeued_after_image_refresh(qt_app, monkeypatch):
    scene = Scene()
    canvas = CanvasView(scene)
    try:
        scene.image = _bgr_fixture()
        started = []
        monkeypatch.setattr(canvas.threadpool, "start", started.append)
        canvas.set_view_mode(canvas.VIEW_XRAY_2)
        assert len(started) == 1
        canvas.update_image()
        assert canvas._view_mode == canvas.VIEW_XRAY_2
        assert len(started) == 2
    finally:
        canvas.close()
