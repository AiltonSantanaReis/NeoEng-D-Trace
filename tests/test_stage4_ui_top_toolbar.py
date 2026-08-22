"""Functional gates for the Stage 4 top-toolbar contract."""

from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication, QWidgetAction

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
        assert groups["edit"] == (window.undo_action, window.redo_action)
        assert groups["view"] == (
            window.mask_viewer_action,
            window.collision_overlay_action,
            window.act_fit,
            window.act_100,
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
