from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from scripts.audit_ui_capture import (
    CAPTURE_SCHEMA_VERSION,
    AuditConfig,
    _main_window_widgets,
)
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_capture_schema_uses_visible_chrome_and_semantic_commands(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    window = MainWindow(scene, AuditConfig())
    window.show()
    qt_app.processEvents()
    try:
        snapshot = _main_window_widgets(window)

        assert CAPTURE_SCHEMA_VERSION == 4
        assert "reference_top_toolbar" in snapshot
        assert (
            snapshot["reference_top_toolbar"]["object_name"]
            == "reference_top_toolbar"
        )
        assert {"toolbar", "nav_toolbar", "xray_toolbar"}.isdisjoint(snapshot)

        contract = snapshot["top_command_contract"]
        assert contract["stage"] == 4
        assert tuple(contract["group_order"]) == (
            "file",
            "edit",
            "view",
            "export",
            "context",
            "render",
        )
        assert contract["action_identity_preserved"] is True
        assert "physical_toolbar_required" not in contract
    finally:
        window._mark_document_clean()
        window.close()
