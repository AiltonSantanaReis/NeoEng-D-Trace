"""Keyboard-first command palette backed by the MainWindow command registry."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from src.ui.command_registry import CommandRegistry, CommandState


class _PaletteSearchInput(QLineEdit):
    """Search input with explicit navigation and cancellation contracts."""

    navigation_requested = Signal(int)
    escape_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Up:
            self.navigation_requested.emit(-1)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Down:
            self.navigation_requested.emit(1)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.escape_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class _PaletteResults(QListWidget):
    """Results list that gives Enter and Escape deterministic meaning."""

    activate_requested = Signal()
    escape_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.activate_requested.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.escape_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class CommandPaletteDialog(QDialog):
    """Search and invoke registered QActions without duplicating execution."""

    command_triggered = Signal(str)

    def __init__(
        self,
        registry: CommandRegistry,
        parent=None,
        *,
        translations: dict[str, dict[str, str]] | None = None,
    ) -> None:
        super().__init__(parent)
        if translations is None:
            from src.ui.main_window_translations import MAIN_WINDOW_TRANSLATIONS

            translations = MAIN_WINDOW_TRANSLATIONS
        self.registry = registry
        self.translations = translations
        self.current_lang = "en"
        self._previous_focus = None

        self.setObjectName("command_palette_dialog")
        self.setModal(False)
        self.setMinimumSize(520, 320)
        self.resize(620, 420)

        self.title_label = QLabel(self)
        self.title_label.setObjectName("command_palette_title")

        self.search_input = _PaletteSearchInput(self)
        self.search_input.setObjectName("command_palette_search")
        self.search_input.textChanged.connect(self.refresh)
        self.search_input.returnPressed.connect(self._trigger_current)
        self.search_input.navigation_requested.connect(self._move_selection)
        self.search_input.escape_requested.connect(self.hide)

        self.results = _PaletteResults(self)
        self.results.setObjectName("command_palette_results")
        self.results.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.results.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.results.itemActivated.connect(lambda _item: self._trigger_current())
        self.results.activate_requested.connect(self._trigger_current)
        self.results.escape_requested.connect(self.hide)

        self.hint_label = QLabel(self)
        self.hint_label.setObjectName("command_palette_hint")
        self.hint_label.setTextFormat(Qt.TextFormat.PlainText)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.results, 1)
        layout.addWidget(self.hint_label)
        self.setTabOrder(self.search_input, self.results)

        self.registry.state_changed.connect(self._registry_state_changed)
        self.update_language(self.current_lang)

    def update_language(self, lang: str) -> None:
        """Update palette chrome while command labels come from live QActions."""

        self.current_lang = lang if lang in self.translations else "en"
        text = self.translations[self.current_lang]
        self.setWindowTitle(text["command_palette_title"])
        self.title_label.setText(text["command_palette_title"])
        self.search_input.setPlaceholderText(text["command_palette_placeholder"])
        self.hint_label.setText(text["command_palette_hint"])
        self.setAccessibleName(text["command_palette_title"])
        self.search_input.setAccessibleName(text["command_palette_search_name"])
        self.search_input.setAccessibleDescription(
            text["command_palette_search_description"]
        )
        self.results.setAccessibleName(text["command_palette_results_name"])
        self.results.setAccessibleDescription(
            text["command_palette_results_description"]
        )
        self.refresh()

    def show_palette(self) -> None:
        """Show the palette, focus search, and preserve the previous widget focus."""

        if not self.isVisible():
            from PySide6.QtWidgets import QApplication

            self._previous_focus = QApplication.focusWidget()
        self.refresh()
        self._center_over_parent()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_input.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_input.selectAll()

    def refresh(self) -> None:
        """Render a deterministic filtered snapshot of the registry state."""

        query = self.search_input.text().strip().casefold()
        selected_id = self._current_command_id()
        self.results.clear()
        states = self.registry.states()
        matching = [state for state in states if self._matches(state, query)]
        for state in matching:
            item = QListWidgetItem(self._display_text(state))
            item.setData(Qt.ItemDataRole.UserRole, state.command_id)
            item.setToolTip(state.command_id)
            item.setWhatsThis(state.command_id)
            if not state.enabled:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.results.addItem(item)

        if not matching:
            empty = QListWidgetItem(
                self.translations[self.current_lang]["command_palette_no_results"]
            )
            empty.setFlags(empty.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.results.addItem(empty)
            self.results.setCurrentRow(-1)
            return

        restored_row = self._row_for_command(selected_id)
        if restored_row >= 0 and self._item_enabled(self.results.item(restored_row)):
            self.results.setCurrentRow(restored_row)
        else:
            self._select_first_enabled()

    def _matches(self, state: CommandState, query: str) -> bool:
        if not state.visible:
            return False
        if not query:
            return True
        haystack = " ".join((state.label, state.command_id, state.shortcut)).casefold()
        return query in haystack

    @staticmethod
    def _display_text(state: CommandState) -> str:
        shortcut = f"    {state.shortcut}" if state.shortcut else ""
        return f"{state.label}{shortcut}"

    def _current_command_id(self) -> str | None:
        item = self.results.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) else None

    def _row_for_command(self, command_id: str | None) -> int:
        if command_id is None:
            return -1
        for row in range(self.results.count()):
            if self.results.item(row).data(Qt.ItemDataRole.UserRole) == command_id:
                return row
        return -1

    @staticmethod
    def _item_enabled(item: QListWidgetItem) -> bool:
        return bool(item.flags() & Qt.ItemFlag.ItemIsEnabled)

    def _select_first_enabled(self) -> None:
        for row in range(self.results.count()):
            if self._item_enabled(self.results.item(row)):
                self.results.setCurrentRow(row)
                return
        self.results.setCurrentRow(-1)

    def _move_selection(self, delta: int) -> None:
        enabled_rows = [
            row
            for row in range(self.results.count())
            if self._item_enabled(self.results.item(row))
        ]
        if not enabled_rows:
            self.results.setCurrentRow(-1)
            return
        current = self.results.currentRow()
        if current not in enabled_rows:
            self.results.setCurrentRow(enabled_rows[0 if delta > 0 else -1])
            return
        index = enabled_rows.index(current)
        self.results.setCurrentRow(enabled_rows[(index + delta) % len(enabled_rows)])

    def _trigger_current(self) -> None:
        command_id = self._current_command_id()
        if command_id is None or not self.registry.trigger(command_id):
            return
        self.command_triggered.emit(command_id)
        self.hide()

    def _registry_state_changed(self, _command_id: str, _enabled: bool) -> None:
        if self.isVisible():
            self.refresh()

    def _center_over_parent(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        center = parent.mapToGlobal(parent.rect().center())
        self.move(center - QPoint(self.width() // 2, self.height() // 2))

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        previous = self._previous_focus
        self._previous_focus = None
        if previous is not None and previous.isVisible() and previous.isEnabled():
            previous.setFocus(Qt.FocusReason.OtherFocusReason)
