"""Stage 2 contracts for stable command IDs and the Ctrl+K request hook."""

from __future__ import annotations

import sys

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.ui.command_registry import CommandRegistrationError, CommandRegistry
from src.ui.main_window import MainWindow


def _app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv)


def test_registry_reuses_action_and_tracks_enabled_state() -> None:
    _app()
    action = QAction("Run")
    registry = CommandRegistry()
    observed: list[tuple[str, bool]] = []
    registry.state_changed.connect(
        lambda command_id, enabled: observed.append((command_id, enabled))
    )

    registry.register("test.run", action)
    triggered: list[bool] = []
    action.triggered.connect(lambda: triggered.append(True))

    assert registry.command_ids() == ("test.run",)
    assert registry.state("test.run").label == "Run"
    assert registry.trigger("test.run") is True
    assert triggered == [True]

    action.setEnabled(False)
    assert registry.is_enabled("test.run") is False
    assert registry.trigger("test.run") is False
    assert triggered == [True]
    assert observed[-1] == ("test.run", False)


@pytest.mark.parametrize("command_id", ["Run", "test", "test..run", "test/run"])
def test_registry_rejects_unstable_command_ids(command_id: str) -> None:
    _app()
    with pytest.raises(CommandRegistrationError):
        CommandRegistry().register(command_id, QAction("Run"))


def test_batch_registration_is_atomic_for_duplicate_input() -> None:
    _app()
    first = QAction("First")
    second = QAction("Second")
    registry = CommandRegistry()

    with pytest.raises(CommandRegistrationError):
        registry.register_many([("test.same", first), ("test.same", second)])

    assert registry.command_ids() == ()


def test_main_window_registers_existing_actions_with_stable_ids() -> None:
    app = _app()
    window = MainWindow(Scene(), {})
    try:
        expected = {
            "file.open_project",
            "file.open_image",
            "file.save",
            "file.save_as",
            "app.exit",
            "edit.undo",
            "edit.redo",
            "view.mask_viewer",
            "view.collision_overlay",
            "view.fit",
            "view.zoom_100",
            "view.lit",
            "view.xray_1",
            "view.xray_2",
            "view.xray_3",
            "view.clean_all",
            "export.open",
            "collision.export_json",
            "collision.export_txt",
        }
        assert set(window.command_registry.command_ids()) == expected
        assert window.command_registry.action("file.save") is window.save_project_action
        assert window.command_registry.is_enabled("edit.undo") is False
        assert window.command_registry.is_enabled("file.save") is True

        state_events: list[tuple[str, bool]] = []
        window.command_registry.state_changed.connect(
            lambda command_id, enabled: state_events.append((command_id, enabled))
        )
        window.save_project_action.setEnabled(False)
        assert state_events[-1] == ("file.save", False)
        assert window.command_registry.state("file.save").enabled is False
    finally:
        window.close()
        app.processEvents()


def test_ctrl_k_emits_request_without_creating_palette_ui() -> None:
    app = _app()
    window = MainWindow(Scene(), {})
    try:
        requests: list[bool] = []
        window.command_palette_requested.connect(lambda: requests.append(True))
        window.show()
        window.activateWindow()
        window.raise_()
        window.canvas.setFocus()
        QTest.qWait(10)
        QTest.keyClick(window.canvas, Qt.Key_K, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()

        assert requests == [True]
        assert window.command_palette_shortcut.key().toString() == "Ctrl+K"
    finally:
        window.close()
        app.processEvents()
