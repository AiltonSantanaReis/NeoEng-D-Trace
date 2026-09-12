"""Layer stack bound to the professional scene authoring session."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
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


class LayerFrameList(QListWidget):
    asset_dropped = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setIconSize(QSize(112, 64))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-neoeng-scene-asset"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is not None and event.mimeData().hasFormat(
            "application/x-neoeng-scene-asset"
        ):
            self.setCurrentItem(item)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is not None and event.mimeData().hasFormat(
            "application/x-neoeng-scene-asset"
        ):
            asset_id = bytes(
                event.mimeData().data("application/x-neoeng-scene-asset")
            ).decode("utf-8")
            self.asset_dropped.emit(asset_id, item.data(Qt.ItemDataRole.UserRole))
            event.acceptProposedAction()
        else:
            event.ignore()


class SceneAuthoringLayerStack(QWidget):
    """Selectable and undoable layer stack for the dedicated scenario editor."""

    status_message = Signal(str)
    active_layer_changed = Signal(str)
    asset_drop_requested = Signal(str, str)

    def __init__(self, session: SceneAuthoringSession, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.current_lang = "en"
        self.setObjectName("scenario_layer_stack")
        self.title = QLabel("Layer Stack", self)
        self.order_hint = QLabel("Render order: Back → Front", self)
        self.order_hint.setObjectName("scenario_layer_order_hint")
        self.order_hint.setToolTip(
            "Layers are rendered from the first row (back) to the last row (front)."
        )
        self.title.setObjectName("scenario_layer_stack_title")
        self.layer_list = LayerFrameList(self)
        self.layer_list.asset_dropped.connect(self.asset_drop_requested)
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
        self.move_selection_button = QPushButton("Move selection to frame", self)
        self.move_selection_button.setObjectName("scene_move_selection_to_frame")
        self.move_selection_button.clicked.connect(self._move_selection)
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
        self.name_label = QLabel("Name", self)
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)
        layout.addLayout(toggles)
        layout.addLayout(buttons)
        layout.addWidget(self.move_selection_button)
        self.session.subscribe(self.refresh)
        self.refresh()

    def update_language(self, language: str) -> None:
        is_pt = language == "pt"
        self.current_lang = language
        self.move_selection_button.setText(
            "Mover seleção para a moldura" if is_pt else "Move selection to frame"
        )
        self.title.setText("Pilha de Camadas" if is_pt else "Layer Stack")
        self.order_hint.setText(
            "Ordem de renderização: Trás → Frente"
            if is_pt
            else "Render order: Back → Front"
        )
        self.order_hint.setToolTip(
            "As camadas são renderizadas da primeira linha (trás) "
            "para a última (frente)."
            if is_pt
            else "Layers are rendered from the first row (back) "
            "to the last row (front)."
        )
        self.name_label.setText("Nome" if is_pt else "Name")
        self.visible_box.setText("Visível" if is_pt else "Visible")
        self.locked_box.setText("Bloqueada" if is_pt else "Locked")
        self.add_button.setText("Adicionar" if is_pt else "Add")
        self.remove_button.setText("Remover" if is_pt else "Remove")
        self.up_button.setText("Subir" if is_pt else "Up")
        self.down_button.setText("Descer" if is_pt else "Down")
        self.layer_list.setToolTip(
            "Selecione uma camada para editar visibilidade, bloqueio e ordem."
            if is_pt
            else "Select a layer to edit visibility, locking and order."
        )
        # The initial widget construction is English by design, so a language
        # switch must also rebuild the already-populated layer rows.
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
        self.active_layer_changed.emit(layer_id)
        self.refresh()

    def _move_selection(self):
        layer_id = self._current_id()
        if layer_id is None:
            return

        def operation():
            layer = next(
                item for item in self.session.document.layers if item.id == layer_id
            )
            if layer.locked:
                raise PermissionError(
                    "Desbloqueie a moldura de destino"
                    if self.current_lang == "pt"
                    else "Unlock the destination frame"
                )
            for object_id in self.session.selection.ids:
                self.session.model.assert_editable(object_id)
            self.session.model._replace(
                objects=[
                    (
                        item.model_copy(update={"layer_id": layer_id})
                        if item.id in self.session.selection.ids
                        else item
                    )
                    for item in self.session.document.objects
                ]
            )

        self._run(lambda: self.session.apply(operation, "Move objects to depth frame"))

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
                SceneLayerAuthoringRecord(
                    id=layer_id,
                    name=(
                        f"{'Moldura' if self.current_lang == 'pt' else 'Frame'} "
                        f"{index}"
                    ),
                )
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
            suffix = (
                ("  [bloqueada]" if self.current_lang == "pt" else "  [locked]")
                if layer.locked
                else ""
            )
            parallax = next(
                (
                    p
                    for p in getattr(self.session.document, "parallax_layers", ())
                    if p.layer_id == layer.id
                ),
                None,
            )
            count = sum(
                obj.layer_id == layer.id for obj in self.session.document.objects
            )
            depth = parallax.depth if parallax else 0
            if self.current_lang == "pt":
                object_label = "objeto" if count == 1 else "objetos"
                depth_label = "Profundidade"
                editability = "bloqueada" if layer.locked else "editável"
                order_tooltip = f"Ordem da camada Z{index:02d} · {editability}"
            else:
                object_label = "object(s)"
                depth_label = "Depth"
                editability = "locked" if layer.locked else "editable"
                order_tooltip = f"Layer order Z{index:02d} · {editability}"
            item = QListWidgetItem(
                f"Z{index:02d}  {layer.name}{suffix}\n"
                f"{depth_label} {depth:.2f} · {count} {object_label}"
            )
            item.setSizeHint(QSize(200, 64))
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
            item.setToolTip(order_tooltip)
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
