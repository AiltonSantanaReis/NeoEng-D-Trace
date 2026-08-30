"""Stage 10 accessibility and usability contracts on the real Qt editor."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QLineEdit,
    QSlider,
    QTabBar,
    QWidget,
)

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_tokens import token_contrast_ratios


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    instance = MainWindow(scene, _ConfigStub())
    instance.show()
    qt_app.processEvents()
    yield instance
    instance.close()
    qt_app.processEvents()


def _visible_interactive(root: QWidget) -> list[QWidget]:
    classes = (
        QAbstractButton,
        QAbstractSpinBox,
        QLineEdit,
        QSlider,
        QCheckBox,
        QTabBar,
    )
    return [
        widget
        for widget in root.findChildren(QWidget)
        if widget.isVisibleTo(root) and isinstance(widget, classes)
    ]


def test_visible_controls_have_real_accessibility_metadata_and_focus(window):
    controls = _visible_interactive(window)
    assert controls
    for widget in controls:
        assert widget.accessibleName(), widget.objectName()
        assert widget.accessibleDescription(), widget.objectName()
        if isinstance(widget, QAbstractButton):
            assert widget.toolTip(), widget.objectName()
            assert widget.focusPolicy() != Qt.FocusPolicy.NoFocus, widget.objectName()

    assert window.reference_open_button.accessibleName() == "Open"
    assert window.side_panel.position_x.accessibleName() == "Position X"
    assert window.side_panel.position_x.lineEdit().accessibleName() == "Position X"
    assert (
        window.viewport_chrome.overlay.view_button.accessibleName()
        == "Viewport view menu"
    )
    assert (
        window.viewport_chrome.overlay.snap_button.accessibleName()
        == "Toggle vertex snapping"
    )


def test_keyboard_shortcuts_and_tab_order_drive_real_commands(window, qt_app):
    window.tool_palette.setEnabled(True)
    window.reference_tool_palette.setEnabled(True)
    window.setFocus()

    QTest.keyClick(window, Qt.Key.Key_1)
    qt_app.processEvents()
    assert window.tool_palette.btn_polygonal_lasso.isChecked()

    window.canvas.set_view_mode(window.canvas.VIEW_LIT)
    QTest.keyClick(window, Qt.Key.Key_X)
    qt_app.processEvents()
    assert window.canvas._view_mode == window.canvas.VIEW_XRAY_1

    expected_tab_order = (
        (window.reference_open_button, window.reference_save_button),
        (window.reference_save_button, window.reference_export_button),
        (window.reference_export_button, window.reference_fit_button),
        (window.reference_fit_button, window.reference_focus_button),
    )
    for source, target in expected_tab_order:
        source.setFocus()
        QTest.keyClick(source, Qt.Key.Key_Tab)
        qt_app.processEvents()
        assert QApplication.focusWidget() is target


def test_mouse_interactions_and_state_feedback_are_independent_of_keyboard(
    window, qt_app
):
    QTest.mouseClick(window.reference_pan_button, Qt.MouseButton.LeftButton)
    qt_app.processEvents()
    assert window.canvas.is_pan_mode() is True
    assert window.reference_pan_button.isChecked() is True

    window.reference_select_button.menu().actions()[0].trigger()
    qt_app.processEvents()
    assert window.canvas.is_pan_mode() is False
    assert window.tool_palette._tool_actions["selection"].isChecked() is True

    snap_button = window.viewport_chrome.overlay.snap_button
    before = snap_button.isChecked()
    QTest.mouseClick(snap_button, Qt.MouseButton.LeftButton)
    qt_app.processEvents()
    assert snap_button.isChecked() is not before
    assert "current state:" in snap_button.accessibleDescription()
    assert snap_button.text()


def test_error_path_is_actionable_when_focus_has_no_selection(window, monkeypatch):
    messages: list[str] = []
    from src.ui import main_window as main_window_module

    monkeypatch.setattr(
        main_window_module.QMessageBox,
        "information",
        lambda _parent, _title, message: messages.append(str(message)),
    )
    window._focus_selected()
    assert messages
    assert "select" in messages[0].lower()


def test_theme_contrast_and_focus_states_are_preserved():
    ratios = token_contrast_ratios()
    assert ratios["primary_on_window"] >= 4.5
    assert ratios["secondary_on_surface"] >= 4.5
    assert ratios["focus_on_window"] >= 3.0
