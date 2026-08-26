"""Functional gates for the Stage 4 top-toolbar contract."""

from __future__ import annotations

import sys

import pytest
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
            "physical_toolbar_required": False,
        }

        groups = window.top_command_groups
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
            window.canvas.gizmo_toggle,
            window.tool_palette.navigation_actions["focus_selected"],
            window.act_clean,
            window.language_button,
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
        window.resize(1280, 720)
        qt_app.processEvents()
        assert toolbar.toolButtonStyle().name == "ToolButtonIconOnly"
        assert window.reference_focus_button.text() == "Focus"
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
            "Parallax",
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
        # The complete application menu remains constructed for integrations,
        # while the visible chrome follows the supplied reference exactly.
        assert window.reference_menu_button.isVisibleTo(window) is False
        submenus = [
            submenu for submenu, _source in window.reference_application_submenus
        ]
        assert [menu.title() for menu in submenus] == ["File", "Edit", "View"]
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
        for button in (
            window.reference_open_button,
            window.reference_save_button,
            window.reference_export_button,
            window.reference_view_button,
            window.reference_collision_button,
        ):
            assert button.popupMode().name == "MenuButtonPopup"
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
        assert contract.physical_toolbar_required is False
        assert contract.role("file") == "commands"
        assert contract.role("edit") == "commands"
        assert contract.role("view") == "commands"
        assert contract.role("export") == "commands"
        assert contract.role("context") == "context"
        assert contract.role("render") == "render"
        assert window.top_command_groups == contract.as_mapping()
    finally:
        window.close()
        qt_app.processEvents()
