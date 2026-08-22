from __future__ import annotations

import pytest
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
    states: list[str] = []
    canvas.viewport_state_changed.connect(states.append)

    assert canvas.viewport_state_text() == "VIEW: LIT  |  ZOOM: 1.00x"
    canvas.set_zoom(1.5)
    assert states[-1] == "VIEW: LIT  |  ZOOM: 1.50x"

    monkeypatch.setattr(canvas, "update", lambda: None)
    canvas.set_view_mode(canvas.VIEW_XRAY_2)
    assert states[-1] == "VIEW: X-RAY 2  |  ZOOM: 1.50x"

    canvas.set_zoom(0.001)
    assert states[-1] == "VIEW: X-RAY 2  |  ZOOM: 1.50x"
    canvas.close()


def test_main_window_uses_status_bar_without_canvas_hud_widget(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    status = window.findChild(QLabel, "viewport_status")

    assert status is window.viewport_status
    assert status.text() == "VIEW: LIT  |  ZOOM: 1.00x"
    assert status.window() is window
    assert status in window.statusBar().findChildren(QLabel)
    assert not window.canvas.findChildren(QLabel)

    window.canvas.set_zoom(2.25)
    assert status.text() == "VIEW: LIT  |  ZOOM: 2.25x"
    window.canvas.set_view_mode(window.canvas.VIEW_XRAY_1)
    assert status.text() == "VIEW: X-RAY 1  |  ZOOM: 2.25x"
    window.close()


def test_status_indicator_fits_resolutions_without_legacy_hud(qt_app, monkeypatch):
    window = MainWindow(Scene(), _ConfigStub())
    calls: list[bool] = []
    monkeypatch.setattr(window.canvas, "_draw_hud", lambda _painter: calls.append(True))

    for width, height in ((1920, 1080), (1366, 768), (1280, 720)):
        window.resize(width, height)
        window.show()
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
    assert window.reference_tool_palette.width() <= 84

    labels = {
        button.text()
        for button in window.reference_top_toolbar.findChildren(QToolButton)
    }
    expected = {"Open Project", "Save", "Export", "View", "Collision", "Parallax"}
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

    window.reference_select_button.click()
    assert window.canvas.is_pan_mode() is False
    assert window.reference_pan_button.isChecked() is False
    window.close()
