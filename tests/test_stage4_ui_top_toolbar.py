"""Functional gates for the Stage 4 top-toolbar contract."""

from __future__ import annotations

import sys

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QToolButton,
    QWidgetAction,
)

from scripts.audit_ui_capture import AuditConfig
from src.models.scene import Scene
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def _window(qt_app: QApplication) -> MainWindow:
    window = MainWindow(Scene(), AuditConfig())
    window.show()
    qt_app.processEvents()
    return window


def test_stage4_groups_are_semantic_and_action_backed(qt_app):
    window = _window(qt_app)
    try:
        contract = window.top_command_contract
        assert contract.descriptor() == {
            "stage": 4,
            "group_order": ("file", "edit", "view", "export", "context", "render"),
            "group_roles": {
                "file": "commands",
                "edit": "commands",
                "view": "commands",
                "export": "commands",
                "context": "context",
                "render": "render",
            },
            "action_identity_preserved": True,
        }

        groups = contract.as_mapping()
        assert tuple(groups) == ("file", "edit", "view", "export", "context", "render")
        assert groups["file"] == (
            window.open_project_action,
            window.open_image_action,
            window.save_project_action,
            window.save_project_as_action,
        )
        assert groups["edit"] == (
            window.undo_action,
            window.redo_action,
            window.settings_action,
        )
        assert groups["view"] == (
            window.mask_viewer_action,
            window.collision_overlay_action,
            window.act_fit,
            window.act_100,
            window.act_grid,
            window.act_snap,
        )
        assert groups["export"] == (
            window.act_export,
            window.act_export_collision_json,
            window.act_export_collision_txt,
        )

        assert contract.items("context") == (
            window.act_gizmo,
            window.tool_palette.navigation_actions["focus_selected"],
            window.act_clean,
            window.language_action,
        )
        assert contract.items("render") == (
            window.act_lit,
            window.act_xray1,
            window.act_xray2,
            window.act_xray3,
        )
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_preserves_menu_identity_and_shortcut_targets(qt_app):
    window = _window(qt_app)
    try:
        assert window.undo_action in window.edit_menu.actions()
        assert window.redo_action in window.edit_menu.actions()
        assert window.settings_action in window.edit_menu.actions()
        assert window.mask_viewer_action in window.view_menu.actions()
        assert window.collision_overlay_action in window.view_menu.actions()
        assert window.language_action in window.view_menu.actions()
        assert window.act_fit in window.top_command_contract.items("view")
        assert window.act_100 in window.top_command_contract.items("view")

        for action in (
            window.undo_action,
            window.redo_action,
            window.mask_viewer_action,
            window.collision_overlay_action,
        ):
            assert not action.icon().isNull()
            assert action.text()
            assert action.toolTip()
            assert action.statusTip()
            assert action.property("accessibleName")
            assert action.property("iconFallback") is False

        original = (window.undo_action, window.mask_viewer_action, window.act_fit)
        window.set_language("pt")
        qt_app.processEvents()
        assert (
            window.undo_action,
            window.mask_viewer_action,
            window.act_fit,
        ) == original
        assert window.undo_action in window.edit_menu.actions()
        assert window.mask_viewer_action in window.view_menu.actions()
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_visible_reference_toolbar_preserves_accessibility_focus_and_modes(
    qt_app,
):
    window = _window(qt_app)
    try:
        toolbar = window.reference_top_toolbar
        assert toolbar.isVisibleTo(window)
        assert toolbar.toolButtonStyle().name == "ToolButtonIconOnly"
        for action in toolbar.actions():
            if action.isSeparator():
                continue
            button = toolbar.widgetForAction(action)
            if isinstance(button, QToolButton):
                assert button.accessibleName(), action.text()
                assert button.toolTip(), action.text()
                assert button.focusPolicy().name != "NoFocus", action.text()
                if button.objectName() == "reference_menu_button":
                    continue
                if isinstance(action, QWidgetAction):
                    assert button.property("uiRole") == "reference_command_button"
                    assert button.property("iconKey")
                else:
                    assert button.property("uiRole") == "reference_top_action"
                    assert button.property("iconKey") == action.property("iconKey")
        assert window.reference_focus_button.isVisibleTo(window)
        assert window.reference_focus_button.focusPolicy().name != "NoFocus"
        assert window.reference_focus_button.accessibleName()
        assert all(ord(character) <= 0xFFFF for character in window.act_clean.text())
        assert not window.act_clean.icon().isNull()
        window.resize(1920, 1080)
        qt_app.processEvents()
        assert toolbar.toolButtonStyle().name == "ToolButtonTextUnderIcon"
        assert window.reference_focus_button.text() == "Focus"
        desktop_buttons = [
            toolbar.widgetForAction(action)
            for action in toolbar.actions()
            if not action.isSeparator()
        ]
        desktop_buttons = [
            button
            for button in desktop_buttons
            if isinstance(button, QToolButton)
            and button.objectName() != "qt_toolbar_ext_button"
        ]
        assert {(button.width(), button.height()) for button in desktop_buttons} == {
            (140, 78)
        }
        window.resize(1280, 720)
        qt_app.processEvents()
        assert toolbar.toolButtonStyle().name == "ToolButtonIconOnly"
        assert window.reference_focus_button.text() == "Focus"
        compact_buttons = [
            toolbar.widgetForAction(action)
            for action in toolbar.actions()
            if not action.isSeparator()
        ]
        compact_buttons = [
            button
            for button in compact_buttons
            if isinstance(button, QToolButton)
            and button.objectName() != "qt_toolbar_ext_button"
        ]
        assert {(button.width(), button.height()) for button in compact_buttons} == {
            (76, 78)
        }
    finally:
        window.close()
        qt_app.processEvents()


def test_reference_toolbar_uses_short_labels_and_preserves_composite_menus(qt_app):
    window = _window(qt_app)
    try:
        window.resize(1920, 1080)
        window.show()
        qt_app.processEvents()

        visible = (
            window.reference_open_button,
            window.reference_save_button,
            window.reference_export_button,
            window.reference_fit_button,
            window.reference_focus_button,
            window.reference_view_button,
            window.reference_collision_button,
            window.reference_parallax_button,
            window.reference_pan_button,
            window.reference_select_button,
            window.reference_undo_button,
            window.reference_redo_button,
        )
        assert [button.text() for button in visible] == [
            "Open",
            "Save",
            "Export",
            "Fit View",
            "Focus",
            "View",
            "Collision",
            "Scenario",
            "Pan",
            "Select",
            "Undo",
            "Redo",
        ]
        assert all("..." not in button.text() for button in visible)
        assert all(button.width() >= button.minimumWidth() for button in visible)

        assert [
            action.text() for action in window.reference_open_button.menu().actions()
        ] == [
            "Open Project...",
            "Open Image",
        ]
        assert [
            action.text() for action in window.reference_save_button.menu().actions()
        ] == [
            "Save",
            "Save As...",
        ]
        assert [
            action.text() for action in window.reference_export_button.menu().actions()
        ] == [
            "Export...",
            "Export Collision (JSON)",
            "Export Collision (TXT)",
        ]
        assert [
            action.text() for action in window.reference_select_button.menu().actions()
        ] == [
            "Selection",
            "Rect",
            "Ellipse",
            "Lasso",
            "Polygonal\nLasso",
            "Magnetic\nLasso",
        ]
        # The complete application menu is the isolated control at the bottom
        # of the visible left rail because the native menu bar is hidden.
        assert window.reference_menu_button.isVisibleTo(window) is True
        assert window.reference_menu_button.parent() is window.reference_tool_palette
        rail = window.reference_tool_palette
        menu_geometry = window.reference_menu_button.geometry()
        assert rail.height() - (menu_geometry.y() + menu_geometry.height()) == 4
        rail_tool_button = next(
            rail.widgetForAction(action)
            for action in rail.actions()
            if not action.isSeparator() and rail.widgetForAction(action) is not None
        )
        assert window.reference_menu_button.size() == rail_tool_button.size()
        assert window.reference_menu_button.size().width() == 88
        assert window.reference_menu_button.size().height() == 32
        assert window.reference_menu_button.accessibleName() == "Application menu"
        assert window.reference_menu_button.popupMode().name == "InstantPopup"
        submenus = [
            submenu for submenu, _source in window.reference_application_submenus
        ]
        assert [menu.title() for menu in submenus] == [
            "File",
            "Edit",
            "View",
            "Scenario",
        ]
        assert [
            action.text()
            for action in submenus[0].actions()
            if not action.isSeparator()
        ] == [
            "Open Project...",
            "Open Image",
            "Save",
            "Save As...",
            "Exit",
            "Export...",
            "Export Collision (JSON)",
            "Export Collision (TXT)",
        ]
        assert window.undo_action.shortcut().toString() == "Ctrl+Z"
        assert window.redo_action.shortcut().toString() == "Ctrl+Y"
        assert window.act_fit.shortcut().toString() == "F"
        assert window.undo_action in submenus[1].actions()
        assert window.redo_action in submenus[1].actions()
        assert window.act_fit in submenus[2].actions()
        assert window.scenario_open_action in submenus[3].actions()
        for button in (
            window.reference_open_button,
            window.reference_save_button,
            window.reference_export_button,
            window.reference_view_button,
            window.reference_collision_button,
            window.reference_select_button,
        ):
            assert button.popupMode().name == "InstantPopup"
            assert button.toolTip()
        assert "scenario" in window.reference_parallax_button.toolTip().casefold()
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_command_search_remains_visible_when_toolbar_overflows(qt_app):
    window = _window(qt_app)
    try:
        search = window.reference_command_search
        container = window.reference_top_toolbar_container
        for width in (1024, 1152, 1280, 1366, 1440, 1450, 1600, 1920):
            window.resize(width, 720)
            qt_app.processEvents()
            geometry = search.geometry()
            assert search.isVisibleTo(window), width
            assert geometry.width() > 0, width
            assert geometry.left() >= 0, width
            assert geometry.right() < container.width(), width
            assert search.placeholderText() == "Ctrl+K"
            assert search.toolTip() == "Search commands (Ctrl+K)"
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_rail_buttons_keep_button_affordance(qt_app):
    window = _window(qt_app)
    try:
        rail_buttons = window.reference_tool_palette._tool_buttons
        assert rail_buttons
        assert all(not button.autoRaise() for button in rail_buttons)
        assert all(button.size().width() == 88 for button in rail_buttons)
        assert all(button.size().height() == 32 for button in rail_buttons)
        assert window.reference_menu_button.autoRaise() is False
        assert window.reference_menu_button.size() == rail_buttons[0].size()
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_history_actions_remain_visible_outside_toolbar_overflow(qt_app):
    window = _window(qt_app)
    try:
        for width in (800, 1024, 1280, 1366, 1450, 1600, 1920):
            window.resize(width, 720)
            qt_app.processEvents()
            for button, action in (
                (window.reference_undo_button, window.undo_action),
                (window.reference_redo_button, window.redo_action),
            ):
                assert button.isVisibleTo(window), width
                assert button.defaultAction() is action
                assert button.parent() is window.reference_history_container
                expected_width = 76 if width < 1450 else 140
                assert button.size() == QSize(expected_width, 78)
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_settings_dialog_commits_grid_and_snap(qt_app, monkeypatch):
    window = _window(qt_app)
    try:

        def accept_with_changes(dialog):
            dialog.findChild(QCheckBox, "view_settings_grid").setChecked(False)
            dialog.findChild(QCheckBox, "view_settings_snap").setChecked(True)
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(QDialog, "exec", accept_with_changes)
        window.settings_action.trigger()
        assert window.canvas.is_grid_visible() is False
        assert window.act_grid.isChecked() is False
        assert window.canvas._vertex_snap_settings.enabled is True
        assert window.act_snap.isChecked() is True
    finally:
        window.close()
        qt_app.processEvents()


def test_stage4_command_families_define_roles_without_physical_toolbar_contract(qt_app):
    window = _window(qt_app)
    try:
        contract = window.top_command_contract
        assert contract.role("file") == "commands"
        assert contract.role("edit") == "commands"
        assert contract.role("view") == "commands"
        assert contract.role("export") == "commands"
        assert contract.role("context") == "context"
        assert contract.role("render") == "render"
    finally:
        window.close()
        qt_app.processEvents()
