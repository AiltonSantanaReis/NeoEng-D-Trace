# src/ui/layers_panel.py
from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.commands import (
    CommandResult,
    CommandStatus,
    CreateLayerCommand,
    MoveLayerCommand,
    RemoveLayerCommand,
    ToggleLayerLockCommand,
    ToggleLayerVisibilityCommand,
)


class LayersPanel(QWidget):
    """Command-only editor for scene layers."""

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setMinimumWidth(200)

        self.main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.project_layers_page = QWidget()
        self.project_layers_layout = QVBoxLayout(self.project_layers_page)
        self.list = QListWidget()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("layers_search")
        self.search_input.setPlaceholderText("Search layers")
        self.search_input.setAccessibleName("Search project layers")
        self.search_input.setToolTip("Filter layers by name or ID")
        self.search_input.textChanged.connect(self.refresh)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        self.project_layers_layout.addWidget(self.search_input)
        self.project_layers_layout.addWidget(self.list)

        buttons = QGridLayout()
        self.btn_new = QPushButton("New")
        self.btn_delete = QPushButton("Delete")
        self.btn_up = QPushButton("Up")
        self.btn_down = QPushButton("Down")
        self.btn_vis = QPushButton("Toggle Vis")
        self.btn_lock = QPushButton("Toggle Lock")

        # Keep the legacy QPushButtons as stable public command handles, but
        # present the actions through a compact, reference-aligned toolbar.
        for button in (
            self.btn_new,
            self.btn_delete,
            self.btn_up,
            self.btn_down,
            self.btn_vis,
            self.btn_lock,
        ):
            button.setVisible(False)
            button.setAccessibleName(button.text())

        self.action_toolbar = QToolBar()
        self.action_toolbar.setObjectName("layers_action_toolbar")
        self.action_toolbar.setMovable(False)
        self.action_toolbar.setFloatable(False)
        self.action_toolbar.setIconSize(QSize(16, 16))
        self.action_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        from src.ui.icon_library import configure_action

        self._toolbar_actions = {}
        for key, button in (
            ("add", self.btn_new),
            ("remove", self.btn_delete),
            ("up", self.btn_up),
            ("down", self.btn_down),
            ("visible", self.btn_vis),
            ("lock", self.btn_lock),
        ):
            action = self.action_toolbar.addAction(button.text())
            configure_action(action, key, text=button.text(), tooltip=button.text())
            action.setProperty("commandKey", key)
            action.triggered.connect(button.click)
            self._toolbar_actions[button] = action
        self.project_layers_layout.addWidget(self.action_toolbar)
        self.project_layers_layout.removeWidget(self.action_toolbar)
        self.project_layers_layout.insertWidget(0, self.action_toolbar)
        self.project_layers_layout.addLayout(buttons)
        self.tabs.addTab(self.project_layers_page, "Project Layers")
        self.tabs.tabBar().setVisible(False)
        self.main_layout.addWidget(self.tabs)
        self.setLayout(self.main_layout)

        self.btn_new.clicked.connect(self._create)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_up.clicked.connect(self._up)
        self.btn_down.clicked.connect(self._down)
        self.btn_vis.clicked.connect(self._toggle_vis)
        self.btn_lock.clicked.connect(self._toggle_lock)

        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self.refresh)
        self.refresh()

    def attach_scenario_panel(self, panel: QWidget) -> None:
        if self.tabs.indexOf(panel) < 0:
            self.tabs.addTab(panel, "Scenario")

    def update_language(self, lang: str) -> None:
        del lang
        if self.tabs.count() >= 2:
            self.tabs.setTabText(0, "Project Layers")
            self.tabs.setTabText(1, "Scenario")

    def refresh(self):
        current_item = self.list.currentItem()
        current_layer_id = (
            current_item.data(Qt.ItemDataRole.UserRole)
            if current_item is not None
            else None
        )

        self.list.blockSignals(True)
        self.list.clear()
        query = self.search_input.text().strip().casefold()
        for layer in self.scene.layers:
            if query and query not in layer.name.casefold() and query not in layer.id.casefold():
                continue
            status = []
            if layer.locked:
                status.append("[LOCKED]")
            if not layer.visible:
                status.append("[HIDDEN]")
            suffix = " ".join(status)
            item = QListWidgetItem(f"{layer.name} {suffix}".rstrip())
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
            # Pin the list delegate to the application UI font so layer names
            # remain readable in native and captured Windows backends.
            item.setFont(QFont("Segoe UI", 10))
            self.list.addItem(item)

        if current_layer_id is not None:
            self._select_layer_id(current_layer_id)
        self.list.blockSignals(False)

    def _select_layer_id(self, layer_id: str) -> bool:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == layer_id:
                self.list.setCurrentItem(item)
                return True
        return False

    def _selected_layer(self):
        item = self.list.currentItem()
        if item is None:
            return None, None, None
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        for index, layer in enumerate(self.scene.layers):
            if layer.id == layer_id:
                return layer, layer_id, index
        return None, layer_id, None

    def _build_context_menu(self) -> QMenu:
        menu = QMenu(self.list)
        for button, toolbar_action in self._toolbar_actions.items():
            action = menu.addAction(toolbar_action.icon(), button.text())
            action.setToolTip(button.toolTip() or button.text())
            action.setProperty("commandKey", toolbar_action.property("commandKey"))
            action.setEnabled(toolbar_action.isEnabled())
            action.triggered.connect(toolbar_action.trigger)
        return menu

    def _show_context_menu(self, position) -> None:
        item = self.list.itemAt(position)
        if item is None:
            return
        self.list.setCurrentRow(self.list.row(item))
        self._build_context_menu().exec(self.list.mapToGlobal(position))

    def _execute_edit_command(self, command) -> Optional[CommandResult]:
        manager = getattr(self.scene, "cmd", None)
        if manager is None:
            QMessageBox.critical(
                self,
                "Layer Edit Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return None

        result = manager.execute(command, self.scene)
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self,
                "Layer Edit Rejected",
                result.message or "The layer operation was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self,
                "Layer Edit Failed",
                result.message or "The layer operation failed.",
            )
        return result

    def _create(self):
        try:
            command = CreateLayerCommand("New Layer")
            result = self._execute_edit_command(command)
            if result is not None and result.changed and command.layer_id:
                self._select_layer_id(command.layer_id)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _delete(self):
        _, layer_id, _ = self._selected_layer()
        if layer_id is None:
            return
        try:
            self._execute_edit_command(RemoveLayerCommand(layer_id))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _up(self):
        _, layer_id, index = self._selected_layer()
        if layer_id is None or index is None or index <= 0:
            return
        try:
            self._execute_edit_command(MoveLayerCommand(layer_id, index - 1))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _down(self):
        _, layer_id, index = self._selected_layer()
        if layer_id is None or index is None or index >= len(self.scene.layers) - 1:
            return
        try:
            self._execute_edit_command(MoveLayerCommand(layer_id, index + 1))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _toggle_vis(self):
        _, layer_id, _ = self._selected_layer()
        if layer_id is None:
            return
        try:
            self._execute_edit_command(ToggleLayerVisibilityCommand(layer_id))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _toggle_lock(self):
        _, layer_id, _ = self._selected_layer()
        if layer_id is None:
            return
        try:
            self._execute_edit_command(ToggleLayerLockCommand(layer_id))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
