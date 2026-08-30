"""Gates for the toolbar-independent Stage 4 command-family contract."""

from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication, QToolBar

from scripts.audit_ui_capture import AuditConfig
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.top_command_contract import (
    TOP_COMMAND_GROUP_ORDER,
    TopCommandContract,
    build_top_command_contract,
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


class _NoLegacyToolbarAccess:
    """Forward MainWindow attributes while rejecting legacy-toolbar reads."""

    _FORBIDDEN = {"toolbar", "nav_toolbar", "xray_toolbar"}

    def __init__(self, window: MainWindow) -> None:
        self._window = window

    def __getattr__(self, name: str):
        if name in self._FORBIDDEN:
            raise AssertionError(f"semantic contract read legacy toolbar: {name}")
        return getattr(self._window, name)


def _window(qt_app: QApplication) -> MainWindow:
    window = MainWindow(Scene(), AuditConfig())
    window.show()
    qt_app.processEvents()
    return window


def test_semantic_contract_builds_without_reading_legacy_toolbars(qt_app):
    window = _window(qt_app)
    try:
        contract = build_top_command_contract(_NoLegacyToolbarAccess(window))
        assert isinstance(contract, TopCommandContract)
        assert contract.group_names() == TOP_COMMAND_GROUP_ORDER
        assert contract.action_identity_preserved is True
    finally:
        window.close()
        qt_app.processEvents()


def test_semantic_groups_preserve_existing_command_and_control_identity(qt_app):
    window = _window(qt_app)
    try:
        contract = window.top_command_contract
        assert contract.items("file") == (
            window.open_project_action,
            window.open_image_action,
            window.save_project_action,
            window.save_project_as_action,
        )
        assert contract.items("edit") == (
            window.undo_action,
            window.redo_action,
            window.settings_action,
        )
        assert contract.items("view") == (
            window.mask_viewer_action,
            window.collision_overlay_action,
            window.act_fit,
            window.act_100,
            window.act_grid,
            window.act_snap,
        )
        assert contract.items("export") == (
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


def test_semantic_descriptor_contains_no_physical_toolbar_contract(qt_app):
    window = _window(qt_app)
    try:
        descriptor = window.top_command_contract.descriptor()
        assert descriptor == {
            "stage": 4,
            "group_order": TOP_COMMAND_GROUP_ORDER,
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
        assert all(
            not isinstance(item, QToolBar)
            for group in window.top_command_contract.groups
            for item in group.items
        )
    finally:
        window.close()
        qt_app.processEvents()


def test_main_window_exposes_only_canonical_top_command_contract(qt_app):
    window = _window(qt_app)
    try:
        assert window.top_command_contract.group_names() == TOP_COMMAND_GROUP_ORDER
        assert not hasattr(window, "top_command_groups")
        assert not hasattr(window, "top_toolbar_groups")
        assert not hasattr(window, "top_toolbar_contract")
    finally:
        window.close()
        qt_app.processEvents()


def test_legacy_toolbar_hosts_are_physically_removed(qt_app):
    window = _window(qt_app)
    try:
        assert not hasattr(window, "toolbar")
        assert not hasattr(window, "nav_toolbar")
        assert not hasattr(window, "xray_toolbar")

        assert not hasattr(window, "_legacy_control_host")
        assert not hasattr(window, "export_collision_button")
        assert not hasattr(window, "focus_button")
        assert not hasattr(window, "language_button")
        assert not hasattr(window.canvas, "gizmo_toggle")
        assert window.act_gizmo.objectName() == "gizmo_action"
        assert window.act_gizmo.isCheckable()
        assert window.act_gizmo in window.top_command_contract.items("context")

        window.canvas.set_preview_mode(True)
        window.canvas.set_preview_mode(False)
        qt_app.processEvents()
        assert window.act_gizmo.isChecked() == window.canvas.is_gizmo_enabled()

        window.canvas.set_gizmo_enabled(True)
        assert window.act_gizmo.isChecked() is True
        window.act_gizmo.trigger()
        assert window.canvas.is_gizmo_enabled() is False

    finally:
        window.close()
        qt_app.processEvents()


def test_duplicate_widget_controls_use_canonical_actions(qt_app):
    window = _window(qt_app)
    try:
        assert not hasattr(window, "export_collision_button")
        assert not hasattr(window, "focus_button")

        assert window.top_command_contract.items("export") == (
            window.act_export,
            window.act_export_collision_json,
            window.act_export_collision_txt,
        )
        focus_action = window.tool_palette.navigation_actions["focus_selected"]
        assert focus_action in window.top_command_contract.items("context")
        assert window.language_action in window.top_command_contract.items("context")
        assert window.language_action is window.language_menu.menuAction()
        assert window.command_registry.action("tool.focus_selected") is focus_action
        assert window.command_registry.action("app.language_en") is window.act_english
        assert (
            window.command_registry.action("app.language_pt") is window.act_portuguese
        )
        assert window.act_english in window.language_menu.actions()
        assert window.act_portuguese in window.language_menu.actions()
        assert window.act_export_collision_json in window.file_menu.actions()
        assert window.act_export_collision_txt in window.file_menu.actions()
    finally:
        window.close()
        qt_app.processEvents()
