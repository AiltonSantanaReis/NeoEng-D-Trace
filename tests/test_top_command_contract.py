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
        assert contract.physical_toolbar_required is False
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
            window.export_collision_button,
        )
        assert contract.items("context") == (
            window.canvas.gizmo_toggle,
            window.focus_button,
            window.act_clean,
            window.language_button,
        )
        assert contract.items("render") == (
            window.act_lit,
            window.act_xray1,
            window.act_xray2,
            window.act_xray3,
        )
        assert window.top_command_groups == contract.as_mapping()
        assert window.top_toolbar_groups is window.top_command_groups
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
            "physical_toolbar_required": False,
        }
        assert all(
            not isinstance(item, QToolBar)
            for group in window.top_command_contract.groups
            for item in group.items
        )
    finally:
        window.close()
        qt_app.processEvents()
