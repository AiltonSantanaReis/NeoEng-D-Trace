# src/ui/layers_panel.py
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
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
        self.list = QListWidget()
        self.main_layout.addWidget(self.list)

        buttons = QHBoxLayout()
        self.btn_new = QPushButton("New")
        self.btn_delete = QPushButton("Delete")
        self.btn_up = QPushButton("Up")
        self.btn_down = QPushButton("Down")
        self.btn_vis = QPushButton("Toggle Vis")
        self.btn_lock = QPushButton("Toggle Lock")

        for button in (
            self.btn_new,
            self.btn_delete,
            self.btn_up,
            self.btn_down,
            self.btn_vis,
            self.btn_lock,
        ):
            buttons.addWidget(button)

        self.main_layout.addLayout(buttons)
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

    def refresh(self):
        current_item = self.list.currentItem()
        current_layer_id = (
            current_item.data(Qt.ItemDataRole.UserRole)
            if current_item is not None
            else None
        )

        self.list.blockSignals(True)
        self.list.clear()
        for layer in self.scene.layers:
            status = []
            if layer.locked:
                status.append("[LOCKED]")
            if not layer.visible:
                status.append("[HIDDEN]")
            suffix = " ".join(status)
            item = QListWidgetItem(f"{layer.name} {suffix}".rstrip())
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
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
