"""Stage 3 contracts for the real command-palette UI and keyboard flow."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.ui.command_palette import CommandPaletteDialog
from src.ui.command_registry import CommandRegistry
from src.ui.main_window import MainWindow
from src.ui.main_window_translations import MAIN_WINDOW_TRANSLATIONS


def _app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv)


def _palette(*actions: tuple[str, QAction]) -> CommandPaletteDialog:
    registry = CommandRegistry()
    registry.register_many(list(actions))
    return CommandPaletteDialog(registry, translations=MAIN_WINDOW_TRANSLATIONS)


def test_palette_renders_live_registry_state_and_accessibility() -> None:
    _app()
    run = QAction("Run export")
    run.setShortcut("Ctrl+E")
    blocked = QAction("Blocked export")
    blocked.setEnabled(False)
    dialog = _palette(("export.run", run), ("export.blocked", blocked))
    try:
        dialog.show_palette()
        _app().processEvents()
        assert dialog.results.count() == 2
        assert dialog.results.item(0).text() == "Run export    Ctrl+E"
        assert bool(dialog.results.item(1).flags() & Qt.ItemFlag.ItemIsEnabled) is False
        assert dialog.accessibleName() == "Command Palette"
        assert dialog.search_input.accessibleName() == "Command search"
        assert dialog.results.accessibleName() == "Command results"
        assert dialog.search_input.hasFocus()
    finally:
        dialog.close()


def test_palette_filters_by_label_shortcut_and_stable_id() -> None:
    _app()
    dialog = _palette(
        ("file.open_project", QAction("Open Project")),
        ("export.run", QAction("Export")),
    )
    try:
        dialog.search_input.setText("project")
        assert dialog.results.count() == 1
        assert dialog.results.item(0).data(Qt.ItemDataRole.UserRole) == (
            "file.open_project"
        )

        dialog.search_input.setText("export.run")
        assert dialog.results.count() == 1
        assert dialog.results.item(0).data(Qt.ItemDataRole.UserRole) == "export.run"

        dialog.search_input.setText("missing")
        assert dialog.results.count() == 1
        assert dialog.results.item(0).text() == "No matching commands."
        assert dialog.results.currentRow() == -1
    finally:
        dialog.close()


def test_palette_keyboard_navigation_triggers_enabled_action_and_closes() -> None:
    _app()
    first = QAction("First")
    second = QAction("Second")
    triggered: list[str] = []
    first.triggered.connect(lambda: triggered.append("first"))
    second.triggered.connect(lambda: triggered.append("second"))
    dialog = _palette(("test.first", first), ("test.second", second))
    try:
        dialog.show_palette()
        QTest.keyClick(dialog.search_input, Qt.Key.Key_Down)
        QTest.keyClick(dialog.search_input, Qt.Key.Key_Return)
        _app().processEvents()
        assert triggered == ["second"]
        assert dialog.isVisible() is False
    finally:
        dialog.close()


def test_palette_covers_directional_and_results_keyboard_contracts() -> None:
    _app()
    first = QAction("First")
    second = QAction("Second")
    triggered: list[str] = []
    first.triggered.connect(lambda: triggered.append("first"))
    second.triggered.connect(lambda: triggered.append("second"))
    dialog = _palette(("test.first", first), ("test.second", second))
    try:
        dialog.show_palette()
        QTest.keyClick(dialog.search_input, Qt.Key.Key_Up)
        assert dialog.results.currentRow() == 1
        dialog.results.setFocus()
        QTest.keyClick(dialog.results, Qt.Key.Key_Return)
        assert triggered == ["second"]

        dialog.show_palette()
        dialog.results.setFocus()
        QTest.keyClick(dialog.results, Qt.Key.Key_Escape)
        assert dialog.isVisible() is False
    finally:
        dialog.close()


def test_palette_refreshes_visibility_and_disabled_selection_paths() -> None:
    _app()
    hidden = QAction("Hidden")
    hidden.setVisible(False)
    blocked = QAction("Blocked")
    blocked.setEnabled(False)
    enabled = QAction("Enabled")
    dialog = _palette(
        ("test.hidden", hidden),
        ("test.blocked", blocked),
        ("test.enabled", enabled),
    )
    try:
        dialog.search_input.setText("hidden")
        assert dialog.results.item(0).text() == "No matching commands."

        dialog.search_input.clear()
        dialog.results.setCurrentRow(0)
        dialog._move_selection(1)
        assert dialog.results.currentRow() == 1

        blocked.setEnabled(True)
        _app().processEvents()
        assert dialog.results.item(1).flags() & Qt.ItemFlag.ItemIsEnabled
    finally:
        dialog.close()


def test_palette_does_not_trigger_disabled_action() -> None:
    _app()
    blocked = QAction("Blocked")
    blocked.setEnabled(False)
    triggered: list[bool] = []
    blocked.triggered.connect(lambda: triggered.append(True))
    dialog = _palette(("test.blocked", blocked))
    try:
        dialog.show_palette()
        assert dialog.results.currentRow() == -1
        dialog._trigger_current()
        assert triggered == []
        assert dialog.isVisible() is True
    finally:
        dialog.close()


def test_palette_escape_restores_previous_focus_and_localizes_chrome() -> None:
    app = _app()
    dialog = _palette(("test.run", QAction("Executar")))
    host = MainWindow(Scene(), {})
    try:
        host.show()
        host.activateWindow()
        host.raise_()
        host.canvas.setFocus()
        app.processEvents()
        QTest.qWait(10)
        assert host.canvas.hasFocus()
        dialog.setParent(host)
        dialog.update_language("pt")
        dialog.show_palette()
        assert dialog.windowTitle() == "Paleta de Comandos"
        assert dialog.search_input.placeholderText().startswith("Pesquisar")
        QTest.keyClick(dialog.search_input, Qt.Key.Key_Escape)
        app.processEvents()
        assert dialog.isVisible() is False
        assert host.canvas.hasFocus()
    finally:
        dialog.close()
        host.close()
        app.processEvents()


def test_main_window_ctrl_k_opens_real_palette_and_language_updates() -> None:
    app = _app()
    window = MainWindow(Scene(), {})
    try:
        window.show()
        window.activateWindow()
        window.raise_()
        window.canvas.setFocus()
        QTest.qWait(10)
        QTest.keyClick(window.canvas, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()

        assert window.command_palette.isVisible() is True
        assert window.command_palette.search_input.hasFocus()
        assert window.command_palette.results.count() >= 1
        window.set_language("pt")
        assert window.command_palette.windowTitle() == "Paleta de Comandos"
        assert window.command_palette.search_input.placeholderText().startswith(
            "Pesquisar"
        )
        QTest.keyClick(window.command_palette.search_input, Qt.Key.Key_Escape)
        app.processEvents()
        assert window.command_palette.isVisible() is False
    finally:
        window.close()
        app.processEvents()
