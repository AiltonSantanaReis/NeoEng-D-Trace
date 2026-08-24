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


def _toolbar_objects(toolbar):
    objects = []
    for action in toolbar.actions():
        if action.isSeparator():
            continue
        if isinstance(action, QWidgetAction):
            objects.append(action.defaultWidget())
        else:
            objects.append(action)
    return objects


def test_stage4_groups_are_native_and_action_backed(qt_app):
    window = _window(qt_app)
    try:
        contract = window.top_toolbar_contract
        assert contract == {
            "stage": 4,
            "native_separators": True,
            "action_identity_preserved": True,
            "toolbar_roles": {
                "main_toolbar": "commands",
                "navigation_toolbar": "context",
                "xray_toolbar": "render",
            },
        }

        groups = window.top_toolbar_groups
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
        assert groups["export"] == (window.act_export, window.export_collision_button)

        main_objects = _toolbar_objects(window.toolbar)
        assert main_objects == [
            item for name in ("file", "edit", "view", "export") for item in groups[name]
        ]
        assert sum(action.isSeparator() for action in window.toolbar.actions()) == 3
        assert sum(action.isSeparator() for action in window.nav_toolbar.actions()) == 0
        assert (
            sum(action.isSeparator() for action in window.xray_toolbar.actions()) == 0
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
        assert window.act_fit in window.toolbar.actions()
        assert window.act_100 in window.toolbar.actions()

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
        assert window.reference_menu_button.isVisible() is False
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


def test_stage4_toolbars_share_presentation_contract(qt_app):
    window = _window(qt_app)
    try:
        for toolbar in (window.toolbar, window.nav_toolbar, window.xray_toolbar):
            assert toolbar.objectName()
            assert toolbar.toolButtonStyle().name == "ToolButtonTextBesideIcon"
            assert toolbar.iconSize().width() == 18
            assert toolbar.iconSize().height() == 18
            assert toolbar.isMovable() is False
            assert toolbar.isFloatable() is False
            assert toolbar.property("toolbarStage") == "stage4"
            assert toolbar.property("toolbarGroupBoundaries") is True
        assert window.toolbar.property("toolbarRole") == "commands"
        assert window.nav_toolbar.property("toolbarRole") == "context"
        assert window.xray_toolbar.property("toolbarRole") == "render"
    finally:
        window.close()
        qt_app.processEvents()
