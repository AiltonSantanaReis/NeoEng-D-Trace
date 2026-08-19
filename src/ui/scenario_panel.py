"""Qt panel for authoring the versioned scenario sidecar."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scenario_authoring import ScenarioAuthoringError, ScenarioAuthoringState


class ScenarioPanel(QWidget):
    """Scenario layer stack and inspector for the dedicated editor window."""

    def __init__(self, authoring: ScenarioAuthoringState, scene: Any, parent=None):
        super().__init__(parent)
        self.authoring = authoring
        self.scene = scene
        self._refreshing = False

        self.setObjectName("scenario_panel")
        self.setMinimumWidth(390)
        self.list = QListWidget()
        self.list.setObjectName("scenario_layer_list")
        self.list.setAccessibleName("Scenario layers")
        self.list.currentItemChanged.connect(self._on_selection_changed)

        self.empty_state = QLabel()
        self.empty_state.setObjectName("scenario_empty_state")
        self.empty_state.setWordWrap(True)
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_add = QPushButton("Add")
        self.btn_remove = QPushButton("Remove")
        self.btn_up = QPushButton("Up")
        self.btn_down = QPushButton("Down")
        self.btn_visible = QPushButton("Toggle Visible")
        self.btn_assign = QPushButton("Assign Selected Object")
        self.btn_save = QPushButton("Save Scenario")
        self.btn_load = QPushButton("Reload Scenario")
        self.btn_reset = QPushButton("Reset From Project")
        for button in (
            self.btn_add,
            self.btn_remove,
            self.btn_up,
            self.btn_down,
            self.btn_visible,
            self.btn_assign,
            self.btn_save,
            self.btn_load,
            self.btn_reset,
        ):
            button.setAutoDefault(False)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("scenario_layer_name")
        self.name_edit.editingFinished.connect(self._rename)
        self.visible_box = QCheckBox("Visible")
        self.visible_box.setObjectName("scenario_layer_visible")
        self.visible_box.toggled.connect(self._set_visible)
        self.depth_spin = self._spin(0.0, 1.0, 0.05)
        self.translation_spin = self._spin(0.0, 1.0, 0.05)
        self.zoom_strength_spin = self._spin(0.0, 1.0, 0.05)
        self.depth_spin.editingFinished.connect(self._set_parallax)
        self.translation_spin.editingFinished.connect(self._set_parallax)
        self.zoom_strength_spin.editingFinished.connect(self._set_parallax)
        self.object_ids = QLabel("Objects: —")
        self.object_ids.setWordWrap(True)

        self.camera_x_spin = self._spin(-1_000_000.0, 1_000_000.0, 1.0)
        self.camera_y_spin = self._spin(-1_000_000.0, 1_000_000.0, 1.0)
        self.camera_zoom_spin = self._spin(0.01, 1000.0, 0.05)
        self.camera_x_spin.editingFinished.connect(self._set_camera)
        self.camera_y_spin.editingFinished.connect(self._set_camera)
        self.camera_zoom_spin.editingFinished.connect(self._set_camera)

        layer_buttons = QVBoxLayout()
        for button in (self.btn_add, self.btn_remove, self.btn_up, self.btn_down):
            layer_buttons.addWidget(button)
        state_buttons = QVBoxLayout()
        for button in (self.btn_visible, self.btn_assign):
            state_buttons.addWidget(button)
        persistence_buttons = QVBoxLayout()
        for button in (self.btn_save, self.btn_load, self.btn_reset):
            persistence_buttons.addWidget(button)

        inspector = QFormLayout()
        inspector.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        inspector.addRow("Name", self.name_edit)
        inspector.addRow("Visible", self.visible_box)
        inspector.addRow("Depth", self.depth_spin)
        inspector.addRow("Translation", self.translation_spin)
        inspector.addRow("Zoom strength", self.zoom_strength_spin)
        inspector.addRow("Assignments", self.object_ids)

        camera = QFormLayout()
        camera.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        camera.addRow("Camera X", self.camera_x_spin)
        camera.addRow("Camera Y", self.camera_y_spin)
        camera.addRow("Camera Zoom", self.camera_zoom_spin)

        layout = QVBoxLayout(self)
        self.title_label = QLabel("Scenario Layer Stack")
        self.title_label.setObjectName("scenario_layer_stack_title")
        layout.addWidget(self.title_label)
        layout.addWidget(self.empty_state)
        layout.addWidget(self.list)
        layout.addLayout(layer_buttons)
        layout.addLayout(state_buttons)
        self.inspector_label = QLabel("Layer Inspector")
        self.camera_label = QLabel("Camera Inspector")
        layout.addWidget(self.inspector_label)
        layout.addLayout(inspector)
        layout.addWidget(self.camera_label)
        layout.addLayout(camera)
        layout.addStretch(1)
        layout.addLayout(persistence_buttons)

        self.btn_add.clicked.connect(self._add)
        self.btn_remove.clicked.connect(self._remove)
        self.btn_up.clicked.connect(self._up)
        self.btn_down.clicked.connect(self._down)
        self.btn_visible.clicked.connect(self._toggle_visible)
        self.btn_assign.clicked.connect(self._assign_selected)
        self.btn_save.clicked.connect(self.save)
        self.btn_load.clicked.connect(self.load)
        self.btn_reset.clicked.connect(self.reset)
        self.authoring.subscribe(self.refresh)
        self.refresh()

    @staticmethod
    def _spin(minimum: float, maximum: float, step: float) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setSingleStep(step)
        widget.setDecimals(4)
        widget.setKeyboardTracking(False)
        return widget

    def _selected_id(self) -> str | None:
        item = self.list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value is not None else None

    def _selected_layer(self):
        layer_id = self._selected_id()
        if layer_id is None or self.authoring.document is None:
            return None
        return next(
            (item for item in self.authoring.document.layers if item.id == layer_id),
            None,
        )

    def _run(self, callback) -> None:
        try:
            callback()
        except Exception as exc:
            QMessageBox.critical(self, "Scenario authoring error", str(exc))
            self.refresh()

    def refresh(self) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            document = self.authoring.document
            available = self.authoring.is_available
            for button in (
                self.btn_add,
                self.btn_remove,
                self.btn_up,
                self.btn_down,
                self.btn_visible,
                self.btn_assign,
                self.btn_save,
                self.btn_load,
                self.btn_reset,
            ):
                button.setEnabled(available)
            self.list.setEnabled(available)
            self.empty_state.setVisible(not available)
            self.empty_state.setText(
                "Save a project in the main editor to enable scenario authoring."
                if available is False
                else ""
            )
            self.name_edit.setEnabled(available)
            self.visible_box.setEnabled(available)
            for widget in (
                self.depth_spin,
                self.translation_spin,
                self.zoom_strength_spin,
                self.camera_x_spin,
                self.camera_y_spin,
                self.camera_zoom_spin,
            ):
                widget.setEnabled(available)

            selected = self._selected_id()
            self.list.blockSignals(True)
            self.list.clear()
            if document is not None:
                for layer in document.layers:
                    suffix = " [hidden]" if not layer.visible else ""
                    item = QListWidgetItem(f"{layer.name}{suffix}")
                    item.setData(Qt.ItemDataRole.UserRole, layer.id)
                    self.list.addItem(item)
            self.list.blockSignals(False)
            if selected is not None:
                self._select_id(selected)
            if self.list.currentItem() is None and self.list.count():
                self.list.setCurrentRow(0)
            self._refresh_inspector()
        finally:
            self._refreshing = False

    def _select_id(self, layer_id: str) -> bool:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == layer_id:
                self.list.setCurrentItem(item)
                return True
        return False

    def _on_selection_changed(self, *_args) -> None:
        self._refresh_inspector()

    def _refresh_inspector(self) -> None:
        layer = self._selected_layer()
        document = self.authoring.document
        widgets = (
            self.name_edit,
            self.visible_box,
            self.depth_spin,
            self.translation_spin,
            self.zoom_strength_spin,
            self.camera_x_spin,
            self.camera_y_spin,
            self.camera_zoom_spin,
        )
        blockers = [QSignalBlocker(widget) for widget in widgets]
        try:
            if layer is None or document is None:
                self.name_edit.clear()
                self.visible_box.setChecked(False)
                self.object_ids.setText("Objects: —")
            else:
                self.name_edit.setText(layer.name)
                self.visible_box.setChecked(layer.visible)
                self.depth_spin.setValue(float(layer.parallax.depth))
                self.translation_spin.setValue(
                    float(layer.parallax.translation_strength)
                )
                self.zoom_strength_spin.setValue(float(layer.parallax.zoom_strength))
                self.object_ids.setText(
                    "Objects: " + (", ".join(layer.object_ids) or "—")
                )
            if document is not None:
                self.camera_x_spin.setValue(float(document.camera.position.x))
                self.camera_y_spin.setValue(float(document.camera.position.y))
                self.camera_zoom_spin.setValue(float(document.camera.zoom))
            else:
                self.camera_x_spin.setValue(0.0)
                self.camera_y_spin.setValue(0.0)
                self.camera_zoom_spin.setValue(1.0)
        finally:
            del blockers

    def _on_result(self, result) -> None:
        if result is not None and not result.ok:
            raise ScenarioAuthoringError(
                result.message or "scenario operation rejected"
            )

    def _add(self) -> None:
        self._run(lambda: self._select_id(self.authoring.add_layer()))

    def _remove(self) -> None:
        layer_id = self._selected_id()
        if layer_id:
            self._run(lambda: self._on_result(self.authoring.remove_layer(layer_id)))

    def _up(self) -> None:
        self._move(-1)

    def _down(self) -> None:
        self._move(1)

    def _move(self, delta: int) -> None:
        layer_id = self._selected_id()
        if layer_id is None or self.authoring.document is None:
            return
        index = next(
            index
            for index, item in enumerate(self.authoring.document.layers)
            if item.id == layer_id
        )
        self._run(
            lambda: self._on_result(self.authoring.move_layer(layer_id, index + delta))
        )

    def _toggle_visible(self) -> None:
        layer_id = self._selected_id()
        if layer_id:
            layer = self._selected_layer()
            self._run(
                lambda: self._on_result(
                    self.authoring.set_layer_visible(layer_id, not layer.visible)
                )
            )

    def _set_visible(self, value: bool) -> None:
        if not self._refreshing:
            layer_id = self._selected_id()
            if layer_id:
                self._run(
                    lambda: self._on_result(
                        self.authoring.set_layer_visible(layer_id, value)
                    )
                )

    def _rename(self) -> None:
        layer_id = self._selected_id()
        if layer_id and not self._refreshing:
            self._run(
                lambda: self._on_result(
                    self.authoring.rename_layer(layer_id, self.name_edit.text())
                )
            )

    def _set_parallax(self) -> None:
        layer_id = self._selected_id()
        if layer_id and not self._refreshing:
            self._run(
                lambda: self._on_result(
                    self.authoring.set_layer_parallax(
                        layer_id,
                        depth=self.depth_spin.value(),
                        translation_strength=self.translation_spin.value(),
                        zoom_strength=self.zoom_strength_spin.value(),
                    )
                )
            )

    def _set_camera(self) -> None:
        if not self._refreshing:
            self._run(
                lambda: self._on_result(
                    self.authoring.set_camera(
                        x=self.camera_x_spin.value(),
                        y=self.camera_y_spin.value(),
                        zoom=self.camera_zoom_spin.value(),
                    )
                )
            )

    def _assign_selected(self) -> None:
        layer_id = self._selected_id()
        object_id = getattr(self.scene, "selected_id", None)
        if layer_id is not None and object_id is not None:
            self._run(
                lambda: self._on_result(
                    self.authoring.assign_object(object_id, layer_id)
                )
            )

    def save(self) -> None:
        self._run(lambda: self.authoring.save())

    def load(self) -> None:
        self._run(lambda: self.authoring.load())

    def reset(self) -> None:
        self._run(lambda: self.authoring.reset())

    def export_runtime(self):
        """Export the validated runtime manifest for the current scenario."""
        result = None
        try:
            result = self.authoring.export_runtime()
        except Exception as exc:
            QMessageBox.critical(self, "Scenario export failed", str(exc))
        return result

    def update_language(self, lang: str) -> None:
        translations = {
            "en": {
                "title": "Scenario Layer Stack",
                "inspector": "Layer Inspector",
                "camera": "Camera Inspector",
                "empty": (
                    "Save a project in the main " "editor to enable scenario authoring."
                ),
                "add": "Add",
                "remove": "Remove",
                "up": "Up",
                "down": "Down",
                "visible_toggle": "Toggle Visible",
                "assign": "Assign Selected Object",
                "save": "Save Scenario",
                "load": "Reload Scenario",
                "reset": "Reset From Project",
                "visible": "Visible",
            },
            "pt": {
                "title": "Camadas do Cenário",
                "inspector": "Inspetor da Camada",
                "camera": "Inspetor da Câmera",
                "empty": (
                    "Salve um projeto no editor principal "
                    "para habilitar a autoria de cenários."
                ),
                "add": "Adicionar",
                "remove": "Remover",
                "up": "Subir",
                "down": "Descer",
                "visible_toggle": "Alternar Visibilidade",
                "assign": "Atribuir Objeto Selecionado",
                "save": "Salvar Cenário",
                "load": "Recarregar Cenário",
                "reset": "Redefinir do Projeto",
                "visible": "Visível",
            },
        }
        t = translations.get(lang, translations["en"])
        self.title_label.setText(t["title"])
        self.inspector_label.setText(t["inspector"])
        self.camera_label.setText(t["camera"])
        self.empty_state.setText(t["empty"])
        for button, key in (
            (self.btn_add, "add"),
            (self.btn_remove, "remove"),
            (self.btn_up, "up"),
            (self.btn_down, "down"),
            (self.btn_visible, "visible_toggle"),
            (self.btn_assign, "assign"),
            (self.btn_save, "save"),
            (self.btn_load, "load"),
            (self.btn_reset, "reset"),
        ):
            button.setText(t[key])
        self.visible_box.setText(t["visible"])
