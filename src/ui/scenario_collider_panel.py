"""Professional inspector panel for the independent E05 collider flow."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scenario_collider_commands import ColliderEditHistory
from src.core.scenario_colliders import Collider, ColliderDocument, ColliderKind
from src.persistence.scenario_collider_io import load_colliders, save_colliders


class ScenarioColliderPanel(QWidget):
    """Create, inspect, persist and undo independent collider records."""

    status_message = Signal(str)

    def __init__(self, project_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_root = project_root
        self.current_lang = "en"
        self.document: ColliderDocument | None = None
        self.history: ColliderEditHistory | None = None
        self.title_label = QLabel(self)
        self.summary_label = QLabel(self)
        self.kind_combo = QComboBox(self)
        self.kind_combo.setObjectName("scenario_collider_kind")
        self._kind_values = tuple(ColliderKind)
        self.collider_list = QListWidget(self)
        self.collider_list.setObjectName("scenario_collider_list")
        self.overlay_check = QCheckBox(self)
        self.new_button = QPushButton(self)
        self.remove_button = QPushButton(self)
        self.save_button = QPushButton(self)
        self.open_button = QPushButton(self)
        self.undo_button = QPushButton(self)
        self.redo_button = QPushButton(self)
        for kind in self._kind_values:
            self.kind_combo.addItem(kind.value.title(), kind.value)
        self.new_button.clicked.connect(self.create_collider)
        self.remove_button.clicked.connect(self.remove_selected)
        self.save_button.clicked.connect(self.save_document)
        self.open_button.clicked.connect(self.open_document)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self._build_layout()
        self.update_language("pt")

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.summary_label)
        layout.addLayout(header)
        controls = QHBoxLayout()
        controls.addWidget(self.kind_combo)
        controls.addWidget(self.new_button)
        controls.addWidget(self.remove_button)
        layout.addLayout(controls)
        actions = QHBoxLayout()
        for button in (
            self.open_button,
            self.save_button,
            self.undo_button,
            self.redo_button,
        ):
            actions.addWidget(button)
        layout.addLayout(actions)
        layout.addWidget(self.overlay_check)
        layout.addWidget(self.collider_list)

    @property
    def document_path(self) -> Path:
        return self.project_root / "assets" / "colliders" / "scenario.colliders.json"

    def _ensure_document(self) -> ColliderEditHistory:
        if self.history is None or self.document is None:
            self.document = ColliderDocument()
            self.history = ColliderEditHistory(self.document)
        return self.history

    def _refresh(self) -> None:
        history = self._ensure_document()
        self.collider_list.clear()
        for collider_id in sorted(history.document.colliders):
            collider = history.document.colliders[collider_id]
            suffix = " · trigger" if collider.is_trigger else ""
            self.collider_list.addItem(f"{collider.id} · {collider.kind.value}{suffix}")
        self.summary_label.setText(
            f"{len(history.document.colliders)} collider(es)"
            if self.current_lang == "en"
            else f"{len(history.document.colliders)} colisor(es)"
        )
        self.remove_button.setEnabled(self.collider_list.currentRow() >= 0)
        self.undo_button.setEnabled(history.can_undo)
        self.redo_button.setEnabled(history.can_redo)

    def create_collider(self) -> None:
        history = self._ensure_document()
        kind = ColliderKind(self.kind_combo.currentData())
        number = len(history.document.colliders) + 1
        collider_id = f"{kind.value}-{number}"
        if kind is ColliderKind.BOX:
            collider = Collider(collider_id, kind, size=(64, 32))
        elif kind is ColliderKind.CIRCLE:
            collider = Collider(collider_id, kind, radius=24)
        elif kind is ColliderKind.POLYGON:
            collider = Collider(collider_id, kind, points=((0, 0), (64, 0), (0, 32)))
        elif kind is ColliderKind.SEGMENT:
            collider = Collider(collider_id, kind, points=((0, 0), (64, 0)))
        else:
            collider = Collider(collider_id, kind, points=((0, 0), (32, 0), (64, 32)))
        history.create(collider)
        self._refresh()
        self.status_message.emit(
            "Colisor criado" if self.current_lang == "pt" else "Collider created"
        )

    def remove_selected(self) -> None:
        if self.history is None:
            return
        row = self.collider_list.currentRow()
        if row < 0:
            return
        collider_id = self.collider_list.item(row).text().split(" · ", 1)[0]
        self.history.remove(collider_id)
        self._refresh()
        self.status_message.emit(
            "Colisor removido" if self.current_lang == "pt" else "Collider removed"
        )

    def save_document(self) -> None:
        if self.document is None:
            self.status_message.emit("Crie um colisor antes de salvar")
            return
        save_colliders(self.document, self.document_path)
        self.status_message.emit(
            f"Colisores salvos: {self.document_path.name}"
            if self.current_lang == "pt"
            else f"Colliders saved: {self.document_path.name}"
        )

    def open_document(self) -> None:
        self.document = load_colliders(self.document_path)
        self.history = ColliderEditHistory(self.document)
        self._refresh()
        self.status_message.emit(
            "Colisores reabertos" if self.current_lang == "pt" else "Colliders reopened"
        )

    def undo(self) -> None:
        if self.history is not None:
            self.history.undo()
            self._refresh()

    def redo(self) -> None:
        if self.history is not None:
            self.history.redo()
            self._refresh()

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.title_label.setText("Colisores / Física")
            self.new_button.setText("Criar")
            self.remove_button.setText("Remover")
            self.open_button.setText("Reabrir")
            self.save_button.setText("Salvar")
            self.undo_button.setText("Desfazer")
            self.redo_button.setText("Refazer")
            self.overlay_check.setText("Mostrar overlay de colisão")
        else:
            self.title_label.setText("Colliders / Physics")
            self.new_button.setText("Create")
            self.remove_button.setText("Remove")
            self.open_button.setText("Reopen")
            self.save_button.setText("Save")
            self.undo_button.setText("Undo")
            self.redo_button.setText("Redo")
            self.overlay_check.setText("Show collision overlay")
        self._refresh()


__all__ = ["ScenarioColliderPanel"]
