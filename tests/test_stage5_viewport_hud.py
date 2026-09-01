from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QToolButton

from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_canvas_state_contract_is_live_for_zoom_fit_and_xray(qt_app, monkeypatch):
    canvas = CanvasView(Scene())
    states = []
    canvas.viewport_state_model_changed.connect(states.append)

    assert canvas.viewport_state().view_mode == "LIT"
    assert canvas.viewport_state().zoom == pytest.approx(1.0)
    canvas.set_zoom(1.5)
    assert states[-1].view_mode == "LIT"
    assert states[-1].zoom == pytest.approx(1.5)

    monkeypatch.setattr(canvas, "update", lambda: None)
    canvas.set_view_mode(canvas.VIEW_XRAY_2)
    assert states[-1].view_mode == "X-RAY 2"
    assert states[-1].zoom == pytest.approx(1.5)

    # Out-of-contract zoom input must leave the structured state unchanged.
    canvas.set_zoom(0.001)
    assert states[-1].view_mode == "X-RAY 2"
    assert states[-1].zoom == pytest.approx(1.5)
    canvas.close()


def test_main_window_uses_status_bar_without_canvas_hud_widget(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    status = window.findChild(QLabel, "viewport_status")

    assert status is window.viewport_status
    initial_text = status.text()
    state = window.canvas.viewport_state()
    assert state.view_mode == "LIT"
    assert state.zoom == pytest.approx(1.0)
    assert state.snap_enabled is False
    assert state.grid_visible is True
    assert state.gizmo_enabled is False
    assert state.selection_count == 0
    assert (state.cursor_x, state.cursor_y) == (0, 0)
    assert status.window() is window
    assert status in window.statusBar().findChildren(QLabel)
    assert not window.canvas.findChildren(QLabel)

    window.canvas.set_zoom(2.25)
    assert window.canvas.viewport_state().zoom == pytest.approx(2.25)
    assert status.text() != initial_text
    zoom_text = status.text()
    window.canvas.set_view_mode(window.canvas.VIEW_XRAY_1)
    assert window.canvas.viewport_state().view_mode == "X-RAY 1"
    assert status.text() != zoom_text
    window.close()


@pytest.mark.skipif(
    sys.platform == "win32" and os.environ.get("CI") == "true",
    reason="Qt offscreen QMainWindow crashes natively on the hosted Windows runner",
)
def test_status_indicator_fits_resolutions_without_legacy_hud(qt_app, monkeypatch):
    window = MainWindow(Scene(), _ConfigStub())
    calls: list[bool] = []
    monkeypatch.setattr(window.canvas, "_draw_hud", lambda _painter: calls.append(True))

    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.show()
    qt_app.processEvents()
    for width, height in ((1920, 1080), (1366, 768), (1280, 720)):
        window.resize(width, height)
        window.layout().activate()
        window.statusBar().layout().activate()
        qt_app.processEvents()
        status_rect = window.viewport_status.geometry()
        status_parent_rect = window.statusBar().rect()
        assert status_rect.isValid()
        assert status_parent_rect.contains(status_rect)
        assert window.canvas.geometry().isValid()
        window.canvas.update()
        qt_app.processEvents()

    assert calls == []
    window.close()


def test_reference_shell_exposes_real_commands_and_stable_regions(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    window.resize(1920, 1080)
    window.show()
    qt_app.processEvents()

    assert window.reference_top_toolbar.isVisibleTo(window)
    assert window.reference_command_search.placeholderText() == "Ctrl+K"
    assert not window.menuBar().isVisibleTo(window)
    assert window.reference_panel_tabs.count() == 4
    assert window.reference_panel_tabs.isVisibleTo(window)
    assert window.reference_tool_palette.width() <= 96

    labels = {
        button.text()
        for button in window.reference_top_toolbar.findChildren(QToolButton)
    }
    expected = {"Open", "Save", "Export", "View", "Collision", "Scenario"}
    assert expected <= labels

    window.resize(1280, 720)
    qt_app.processEvents()
    assert window._compact_layout is True
    assert [
        window.compact_panel_tabs.tabText(i)
        for i in range(window.compact_panel_tabs.count())
    ] == ["Objects", "Layers", "Groups", "Collision"]
    window.compact_panel_tabs.setCurrentWidget(window.layers)
    qt_app.processEvents()
    assert window.layers.action_toolbar.isVisibleTo(window)
    assert window.layers.action_toolbar.actions()
    assert not any(
        button.isVisible()
        for button in (
            window.layers.btn_new,
            window.layers.btn_delete,
            window.layers.btn_up,
            window.layers.btn_down,
            window.layers.btn_vis,
            window.layers.btn_lock,
        )
    )
    assert window.layers.list.count() == len(window.scene.layers)
    assert window.layers.list.item(0).font().family() == "Segoe UI"
    window.close()


def test_reference_pan_and_select_controls_drive_existing_canvas_contract(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    window.show()
    qt_app.processEvents()

    window.reference_pan_button.click()
    assert window.canvas.is_pan_mode() is True
    assert window.reference_pan_button.isChecked() is True

    window.reference_select_button.menu().actions()[0].trigger()
    assert window.canvas.is_pan_mode() is False
    assert window.reference_pan_button.isChecked() is False
    window.close()
