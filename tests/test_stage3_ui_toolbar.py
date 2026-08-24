"""Characterization and interaction gates for the Stage 3 tool toolbar."""

from __future__ import annotations

import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolBar

from scripts.audit_ui_capture import AuditConfig
from src.models.scene import Scene
from src.ui.main_window import MainWindow


def _window(qt_app: QApplication) -> MainWindow:
    window = MainWindow(Scene(), AuditConfig())
    window._refresh_document_views(project_loaded=False)
    window.show()
    qt_app.processEvents()
    return window


def test_stage3_toolbar_is_vertical_action_backed_and_grouped(qt_app):
    window = _window(qt_app)
    try:
        toolbar = window.tool_palette
        assert isinstance(toolbar, QToolBar)
        assert toolbar.objectName() == "left_tool_toolbar"
        assert toolbar.orientation() == Qt.Orientation.Vertical
        assert toolbar.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonIconOnly
        assert toolbar.isMovable() is False
        assert toolbar.isFloatable() is False

        actions = toolbar.actions()
        tool_actions = [action for action in actions if action.objectName().startswith("tool_action_")]
        assert len(tool_actions) == 9
        rail_actions = [action for action in actions if action.objectName().startswith("rail_action_")]
        assert len(rail_actions) == 5
        assert sum(action.isSeparator() for action in actions) == 4
        assert all(action in toolbar.action_group.actions() for action in tool_actions)
        assert toolbar.action_group.isExclusive() is True
        assert toolbar.button_group.exclusive() is True
        assert set(toolbar.navigation_actions) == {
            "validation", "move_viewport", "zoom_viewport", "fit_view", "focus_selected"
        }
        assert all(action.icon().isNull() is False for action in toolbar.navigation_actions.values())
    finally:
        window.close()
        qt_app.processEvents()


def test_stage3_toolbar_preserves_real_selection_and_feedback(qt_app):
    window = _window(qt_app)
    try:
        toolbar = window.tool_palette
        toolbar.setEnabled(True)
        for name, button in toolbar.tool_buttons.items():
            assert button.icon().isNull() is False, name
            assert button.text(), name
            assert button.toolTip(), name
            assert button.accessibleName(), name
            assert button.focusPolicy() != Qt.FocusPolicy.NoFocus
            button.click()
            qt_app.processEvents()
            assert button.isChecked(), name
            assert toolbar.button_group.checkedButton() is button
            assert window.canvas._tool is not None, name

        toolbar.setEnabled(False)
        qt_app.processEvents()
        assert all(not button.isEnabled() for button in toolbar.tool_buttons.values())
        assert all(
            "Open an image" in button.toolTip()
            for button in toolbar.tool_buttons.values()
        )
        toolbar.setEnabled(True)
        toolbar.update_language("pt")
        qt_app.processEvents()
        assert toolbar.btn_lasso.text() == "Laço"
        assert "ferramenta" in toolbar.btn_lasso.toolTip().casefold()
    finally:
        window.close()
        qt_app.processEvents()


def test_stage3_preserves_global_tool_shortcuts(qt_app):
    window = _window(qt_app)
    try:
        shortcuts = {
            shortcut.key().toString()
            for shortcut in window.findChildren(type(window.command_palette_shortcut))
        }
        assert {"1", "2", "3", "4", "5", "6"} <= shortcuts
        window.tool_palette.setEnabled(True)
        window.setFocus()
        QTest.keyClick(window, Qt.Key.Key_1)
        qt_app.processEvents()
        assert window.tool_palette.btn_polygonal_lasso.isChecked()
    finally:
        window.close()
        qt_app.processEvents()


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)
