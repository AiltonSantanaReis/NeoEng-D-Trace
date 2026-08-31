"""Layer stack bound to the professional scene authoring session."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.scene_authoring_schema import SceneLayerAuthoringRecord


class SceneAuthoringLayerStack(QWidget):
    """Selectable and undoable layer stack for the dedicated scenario editor."""

    status_message = Signal(str)

    def __init__(self, session: SceneAuthoringSession, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("scenario_layer_stack")
        self.title = QLabel("Layer Stack", self)
        self.order_hint = QLabel("Render order: Back → Front", self)
        self.order_hint.setObjectName("scenario_layer_order_hint")
        self.order_hint.setToolTip(
            "Layers are rendered from the first row (back) to the last row (front)."
        )
        self.title.setObjectName("scenario_layer_stack_title")
        self.layer_list = QListWidget(self)
        self.layer_list.setObjectName("scenario_layer_stack_list")
        self.layer_list.currentRowChanged.connect(self._selection_changed)
        self.name_edit = QLineEdit(self)
        self.name_edit.setObjectName("scenario_layer_name")
        self.name_edit.editingFinished.connect(self._rename_current)
        self.visible_box = QCheckBox("Visible", self)
        self.locked_box = QCheckBox("Locked", self)
        self.visible_box.toggled.connect(self._set_visible)
        self.locked_box.toggled.connect(self._set_locked)
        self.add_button = QPushButton("Add", self)
        self.remove_button = QPushButton("Remove", self)
        self.up_button = QPushButton("Up", self)
        self.down_button = QPushButton("Down", self)
        self.add_button.clicked.connect(self._add)
        self.remove_button.clicked.connect(self._remove)
        self.up_button.clicked.connect(lambda: self._move(-1))
        self.down_button.clicked.connect(lambda: self._move(1))
        buttons = QHBoxLayout()
        for button in (
            self.add_button,
            self.remove_button,
            self.up_button,
            self.down_button,
        ):
            buttons.addWidget(button)
        toggles = QHBoxLayout()
        toggles.addWidget(self.visible_box)
        toggles.addWidget(self.locked_box)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.order_hint)
        layout.addWidget(self.layer_list)
        layout.addWidget(QLabel("Name", self))
        layout.addWidget(self.name_edit)
        layout.addLayout(toggles)
        layout.addLayout(buttons)
        self.session.subscribe(self.refresh)
        self.refresh()

    def _current_id(self) -> str | None:
        item = self.layer_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _run(self, operation) -> bool:
        try:
            operation()
            return True
        except (KeyError, ValueError, PermissionError) as exc:
            self.status_message.emit(str(exc))
            return False

    def _selection_changed(self, _row: int) -> None:
        layer_id = self._current_id()
        if layer_id is None:
            return

        ids = list(
            item.id
            for item in self.session.document.objects
            if item.layer_id == layer_id
        )
        self.session.set_selection(ids, ids[0] if ids else None)

    def _rename_current(self) -> None:
        layer_id = self._current_id()
        name = self.name_edit.text().strip()
        if layer_id and name:
            self._run(lambda: self.session.rename_layer(layer_id, name))

    def _set_visible(self, visible: bool) -> None:
        layer_id = self._current_id()
        if layer_id is not None:
            self._run(lambda: self.session.set_layer_visibility(layer_id, visible))

    def _set_locked(self, locked: bool) -> None:
        layer_id = self._current_id()
        if layer_id is not None:
            self._run(lambda: self.session.set_layer_locked(layer_id, locked))

    def _add(self) -> None:
        ids = {item.id for item in self.session.document.layers}
        index = 1
        layer_id = "scenario_layer"
        while layer_id in ids:
            index += 1
            layer_id = f"scenario_layer_{index}"
        self._run(
            lambda: self.session.add_layer(
                SceneLayerAuthoringRecord(id=layer_id, name=f"Layer {index}")
            )
        )

    def _remove(self) -> None:
        layer_id = self._current_id()
        if layer_id is not None:
            self._run(lambda: self.session.remove_layer(layer_id))

    def _move(self, delta: int) -> None:
        layer_id = self._current_id()
        if layer_id is None:
            return
        index = next(
            index
            for index, item in enumerate(self.session.document.layers)
            if item.id == layer_id
        )
        self._run(lambda: self.session.reorder_layer(layer_id, index + delta))

    def refresh(self) -> None:
        selected = self._current_id()
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        selected_row = -1
        for index, layer in enumerate(self.session.document.layers):
            suffix = "  [locked]" if layer.locked else ""
            item = QListWidgetItem(f"{layer.name}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
            self.layer_list.addItem(item)
            if layer.id == selected:
                selected_row = index
        self.layer_list.setCurrentRow(max(0, selected_row))
        self.layer_list.blockSignals(False)
        layer_id = self._current_id()
        selected_layer = next(
            (item for item in self.session.document.layers if item.id == layer_id),
            None,
        )
        enabled = selected_layer is not None
        self.name_edit.setEnabled(enabled)
        self.visible_box.setEnabled(enabled)
        self.locked_box.setEnabled(enabled)
        self.remove_button.setEnabled(enabled and len(self.session.document.layers) > 1)
        self.up_button.setEnabled(enabled)
        self.down_button.setEnabled(enabled)
        if selected_layer is not None:
            self.name_edit.blockSignals(True)
            self.name_edit.setText(selected_layer.name)
            self.name_edit.blockSignals(False)
            self.visible_box.blockSignals(True)
            self.visible_box.setChecked(selected_layer.visible)
            self.visible_box.blockSignals(False)
