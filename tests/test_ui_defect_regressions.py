"""Regression tests for the scenario/UI defects reproduced in real captures."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.gizmo import TransformGizmo
from src.ui.main_window import MainWindow
from src.ui.mask_viewer import MaskViewerDialog


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _Config:
    def get(self, key, default=None):
        del key
        return default

    def set(self, key, value):
        del key, value

    def save(self):
        return None


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = np.zeros((180, 260, 4), dtype=np.uint8)
    scene.image[:, :, :3] = (32, 38, 48)
    scene.image[:, :, 3] = 255
    scene.add_object(
        "object_a", [(40, 35), (180, 35), (180, 140), (40, 140)], select=True
    )
    scene.cmd.clear()
    return scene


def test_scenario_editor_has_explained_empty_state(qt_app):
    window = MainWindow(_scene(), _Config())
    try:
        window.open_scenario_editor()
        qt_app.processEvents()
        editor = window.scenario_editor_window
        assert editor is not None and editor.isVisible()
        empty = editor.professional_pages.currentWidget()
        assert empty is not None and empty.isVisible()
        assert empty.objectName() == "professional_scene_viewport_empty"
        assert "project" in empty.text().lower()
        inspector_empty = editor.right_pages.currentWidget().findChild(
            type(editor.scenario_panel.empty_state),
            "professional_scene_inspector_empty",
        )
        assert inspector_empty is not None
        assert editor.scenario_panel.btn_add.isEnabled() is False
        assert window.layers.tabs.count() == 1
        assert window.scenario_open_action in window.view_menu.actions()
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        qt_app.processEvents()


def test_scenario_editor_is_scrollable_and_interactive_after_binding(tmp_path, qt_app):
    project = tmp_path / "ui-scenario.ndtproj"
    project.write_bytes(b"ui scenario fixture\n")
    window = MainWindow(_scene(), _Config())
    try:
        window._project_path = project
        window.scenario_authoring.bind_project(project)
        window.open_scenario_editor()
        editor = window.scenario_editor_window
        assert editor is not None
        editor.resize(QSize(980, 640))
        editor.show()
        qt_app.processEvents()
        panel = editor.scenario_panel
        scroll = editor.scenario_inspector_scroll
        assert scroll is not None
        assert editor.professional_viewport is not None
        assert editor.professional_inspector is not None
        assert editor.right_pages.currentWidget() is editor.professional_inspector
        assert (
            editor.professional_viewport.objectName() == "professional_scene_viewport"
        )
        assert panel.list.isEnabled()
        assert panel.list.count() == 1
        assert panel.name_edit.height() >= 20
        before = len(window.scenario_authoring.document.layers)
        panel.btn_add.click()
        assert len(window.scenario_authoring.document.layers) == before + 1
        panel.btn_remove.click()
        assert len(window.scenario_authoring.document.layers) == before
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        qt_app.processEvents()


def test_gizmo_is_toolbar_control_and_feedback_avoids_gizmo(qt_app):
    window = MainWindow(_scene(), _Config())
    try:
        window.show()
        qt_app.processEvents()
        assert window.canvas.gizmo_toggle.parent() is window.nav_toolbar
        assert window.canvas.gizmo_toggle.geometry().height() >= 20

        canvas = CanvasView(_scene())
        canvas.resize(640, 480)
        canvas.gizmo = TransformGizmo()
        canvas.gizmo.screen_pos.setX(530)
        canvas.gizmo.screen_pos.setY(360)
        canvas._gizmo_enabled = True
        canvas._gizmo_feedback = "T: (10.0, -2.0, 0.0)  S: (1.0, 1.0, 1.0)"
        image = QImage(640, 480, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        try:
            rect = canvas._gizmo_feedback_rect(painter)
        finally:
            painter.end()
        gizmo_radius = canvas.gizmo.arm_length + canvas.gizmo.arrow_size + 12
        center = canvas.gizmo.screen_pos
        gizmo_rect = QRectF(
            center.x() - gizmo_radius,
            center.y() - gizmo_radius,
            gizmo_radius * 2,
            gizmo_radius * 2,
        )
        assert not rect.intersects(gizmo_rect)
        assert rect.width() > 0 and rect.height() > 0
    finally:
        window.close()
        qt_app.processEvents()


def test_mask_viewer_exposes_and_switches_all_xray_modes(qt_app):
    dialog = MaskViewerDialog(_scene())
    try:
        assert len(dialog.view_mode_buttons) == 4
        assert (
            dialog.findChild(type(dialog.view_mode_group), "mask_view_mode_group")
            is dialog.view_mode_group
        )
        for index, button in enumerate(dialog.view_mode_buttons):
            button.click()
            qt_app.processEvents()
            assert dialog.viewer.get_display_mode() == index
            assert button.isChecked()
    finally:
        dialog.close()
        qt_app.processEvents()
