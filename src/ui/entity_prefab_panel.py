"""Compact E07 entity, hierarchy and prefab authoring surface."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from src.core.prefab_authoring import (
    create_prefab,
    detach_prefab_instance,
    instantiate_prefab,
    revert_prefab_override,
    set_prefab_override,
    update_prefab_sources,
)
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.scene_authoring_schema import SceneAuthoringDocumentV2


class EntityPrefabPanel(QWidget):
    """Deterministic controls for the E07 acceptance flow."""

    status_message = Signal(str)

    def __init__(self, session: SceneAuthoringSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("entity_prefab_panel")
        self.title_label = QLabel(self)
        self.summary_label = QLabel(self)
        self.summary_label.setWordWrap(True)
        self.entity_list = QListWidget(self)
        self.prefab_list = QListWidget(self)
        self.instance_list = QListWidget(self)
        self.add_entity_button = QPushButton(self)
        self.parent_button = QPushButton(self)
        self.create_prefab_button = QPushButton(self)
        self.instantiate_button = QPushButton(self)
        self.override_button = QPushButton(self)
        self.revert_button = QPushButton(self)
        self.update_button = QPushButton(self)
        self.detach_button = QPushButton(self)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(QLabel("Entidades / parent espacial"))
        layout.addWidget(self.entity_list)
        entity_actions = QGridLayout()
        entity_actions.addWidget(self.add_entity_button, 0, 0)
        entity_actions.addWidget(self.parent_button, 0, 1)
        layout.addLayout(entity_actions)
        layout.addWidget(QLabel("Prefabs"))
        layout.addWidget(self.prefab_list)
        prefab_actions = QGridLayout()
        prefab_actions.addWidget(self.create_prefab_button, 0, 0)
        prefab_actions.addWidget(self.instantiate_button, 0, 1)
        prefab_actions.addWidget(self.update_button, 1, 0, 1, 2)
        layout.addLayout(prefab_actions)
        layout.addWidget(QLabel("Instâncias / overrides"))
        layout.addWidget(self.instance_list)
        instance_actions = QGridLayout()
        instance_actions.addWidget(self.override_button, 0, 0)
        instance_actions.addWidget(self.revert_button, 0, 1)
        instance_actions.addWidget(self.detach_button, 1, 0, 1, 2)
        layout.addLayout(instance_actions)
        layout.addWidget(self.status_label)

        self.add_entity_button.clicked.connect(self.add_entity)
        self.parent_button.clicked.connect(self.parent_selected)
        self.create_prefab_button.clicked.connect(self.create_prefab)
        self.instantiate_button.clicked.connect(self.instantiate)
        self.override_button.clicked.connect(self.override)
        self.revert_button.clicked.connect(self.revert)
        self.update_button.clicked.connect(self.update_prefab)
        self.detach_button.clicked.connect(self.detach)
        self.session.subscribe(self.refresh)
        self.update_language("pt")
        self.refresh()

    def _document(self) -> SceneAuthoringDocumentV2 | None:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            self._status("Entidades exigem documento V2 explícito")
            return None
        return document

    def _status(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_message.emit(message)

    def _apply(self, operation: Callable[[SceneAuthoringDocumentV2], SceneAuthoringDocumentV2], description: str) -> None:
        document = self._document()
        if document is None:
            return
        try:
            self.session.apply(
                lambda: setattr(self.session.model, "document", operation(document)),
                description,
            )
        except (KeyError, ValueError) as exc:
            self._status(f"Operação rejeitada: {exc}")

    def add_entity(self) -> None:
        document = self._document()
        if document is None:
            return
        source = next(
            (item for item in document.objects if item.id not in {entity.id for entity in document.entities}),
            None,
        )
        if source is None:
            self._status("Nenhum objeto disponível para nova entidade")
            return
        try:
            def operation() -> None:
                self.session.model.add_entity_from_object(source.id)

            self.session.apply(
                operation,
                "Create authored entity",
            )
            self._status(f"Entidade criada: {source.id}")
        except ValueError as exc:
            self._status(f"Entidade rejeitada: {exc}")

    def parent_selected(self) -> None:
        document = self._document()
        if document is None or len(document.entities) < 2:
            self._status("Crie duas entidades para definir parent")
            return
        child, parent = document.entities[1], document.entities[0]
        try:
            self.session.apply(
                lambda: self.session.model.set_entity_parent(child.id, parent.id),
                "Parent authored entity",
            )
            self._status(f"Parent definido: {child.id} → {parent.id}")
        except ValueError as exc:
            self._status(f"Parent rejeitado: {exc}")

    def create_prefab(self) -> None:
        document = self._document()
        if document is None or not document.entities:
            self._status("Crie uma entidade antes do prefab")
            return
        prefab_id = f"prefab-{len(document.prefabs) + 1}"
        self._apply(
            lambda current: create_prefab(
                current, prefab_id, f"Prefab {len(current.prefabs) + 1}", [current.entities[0].id]
            ),
            "Create prefab asset",
        )
        self._status(f"Prefab criado: {prefab_id}")

    def instantiate(self) -> None:
        document = self._document()
        if document is None or not document.prefabs:
            self._status("Crie um prefab antes da instância")
            return
        prefab = document.prefabs[0]
        instance_id = f"{prefab.id}-instance-{len(document.prefab_instances) + 1}"
        self._apply(
            lambda current: instantiate_prefab(
                current, prefab.id, instance_id, prefab.source_entity_ids[0]
            ),
            "Instantiate prefab",
        )
        self._status(f"Instância criada: {instance_id}")

    def override(self) -> None:
        document = self._document()
        if document is None or not document.prefab_instances:
            self._status("Crie uma instância antes do override")
            return
        instance = document.prefab_instances[0]
        self._apply(
            lambda current: set_prefab_override(
                current, instance.id, "components.demo.value", 1
            ),
            "Set prefab override",
        )
        self._status("Override aplicado: components.demo.value")

    def revert(self) -> None:
        document = self._document()
        if document is None or not document.prefab_instances:
            self._status("Nenhuma instância disponível")
            return
        instance = document.prefab_instances[0]
        if not instance.overrides:
            self._status("A instância não possui override")
            return
        self._apply(
            lambda current: revert_prefab_override(
                current, instance.id, instance.overrides[0].path
            ),
            "Revert prefab override",
        )
        self._status("Override revertido")

    def update_prefab(self) -> None:
        document = self._document()
        if document is None or not document.prefabs:
            self._status("Nenhum prefab disponível")
            return
        prefab = document.prefabs[0]
        self._apply(
            lambda current: update_prefab_sources(
                current, prefab.id, list(prefab.source_entity_ids)
            ),
            "Update prefab source",
        )
        self._status(f"Prefab atualizado: v{prefab.version + 1}")

    def detach(self) -> None:
        document = self._document()
        if document is None or not document.prefab_instances:
            self._status("Nenhuma instância disponível")
            return
        instance = document.prefab_instances[0]
        self._apply(
            lambda current: detach_prefab_instance(current, instance.id),
            "Detach prefab instance",
        )
        self._status("Instância desvinculada")

    def update_language(self, language: str) -> None:
        portuguese = language == "pt"
        self.title_label.setText("Entidades, Hierarquia e Prefabs" if portuguese else "Entities, Hierarchy & Prefabs")
        self.add_entity_button.setText("Adicionar entidade" if portuguese else "Add entity")
        self.parent_button.setText("Definir parent" if portuguese else "Set parent")
        self.create_prefab_button.setText("Criar prefab" if portuguese else "Create prefab")
        self.instantiate_button.setText("Instanciar" if portuguese else "Instantiate")
        self.override_button.setText("Override" if portuguese else "Override")
        self.revert_button.setText("Reverter" if portuguese else "Revert")
        self.update_button.setText("Atualizar" if portuguese else "Update")
        self.detach_button.setText("Desvincular" if portuguese else "Detach")
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        document = self._document()
        if document is None:
            return
        self.summary_label.setText(
            f"Entidades: {len(document.entities)} · Prefabs: {len(document.prefabs)} · Instâncias: {len(document.prefab_instances)}"
        )

    def refresh(self) -> None:
        document = self._document()
        if document is None:
            return
        self.entity_list.clear()
        self.entity_list.addItems(
            [
                f"{entity.id}"
                + (f" ← {entity.parent_entity_id}" if entity.parent_entity_id else "")
                for entity in document.entities
            ]
        )
        self.prefab_list.clear()
        self.prefab_list.addItems(
            [f"{prefab.id} v{prefab.version}" for prefab in document.prefabs]
        )
        self.instance_list.clear()
        self.instance_list.addItems(
            [
                f"{instance.id}"
                + (" · detached" if instance.detached else "")
                + f" · overrides={len(instance.overrides)}"
                for instance in document.prefab_instances
            ]
        )
        self._refresh_summary()


__all__ = ["EntityPrefabPanel"]
