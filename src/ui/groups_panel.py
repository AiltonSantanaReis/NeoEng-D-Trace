# src/ui/groups_panel.py
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.commands import (
    AddToGroupCommand,
    CommandResult,
    CommandStatus,
    CreateGroupCommand,
    MoveGroupCommand,
    RemoveFromGroupCommand,
    RemoveGroupCommand,
    ToggleGroupLockCommand,
    ToggleGroupVisibilityCommand,
)


class GroupsPanel(QWidget):
    """Command-only editor for scene groups."""

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.current_lang = "en"
        self.translations = {
            "en": {
                "new_group": "New Group",
                "delete_group": "Delete Group",
                "add_selected": "Add Selected",
                "remove_selected": "Remove Selected",
                "up": "Up",
                "down": "Down",
                "toggle_vis": "Toggle Vis",
                "toggle_lock": "Toggle Lock",
                "new_group_title": "New Group",
                "name": "Name:",
                "error": "Error",
                "info": "Info",
                "no_group_selected": "No group selected",
                "no_object_selected": "No object selected",
                "history_unavailable": ("Undo/Redo command history is unavailable."),
                "operation_rejected": ("The group operation was rejected."),
                "operation_failed": "The group operation failed.",
            },
            "pt": {
                "new_group": "Novo Grupo",
                "delete_group": "Excluir Grupo",
                "add_selected": "Adicionar Selecionado",
                "remove_selected": "Remover Selecionado",
                "up": "Cima",
                "down": "Baixo",
                "toggle_vis": "Alternar Vis",
                "toggle_lock": "Alternar Bloq",
                "new_group_title": "Novo Grupo",
                "name": "Nome:",
                "error": "Erro",
                "info": "Info",
                "no_group_selected": "Nenhum grupo selecionado",
                "no_object_selected": "Nenhum objeto selecionado",
                "history_unavailable": (
                    "O histórico de Desfazer/Refazer está indisponível."
                ),
                "operation_rejected": ("A operação do grupo foi rejeitada."),
                "operation_failed": "A operação do grupo falhou.",
            },
        }
        self.list = QListWidget()
        self.btn_new = QPushButton(self.translations[self.current_lang]["new_group"])
        self.btn_delete = QPushButton(
            self.translations[self.current_lang]["delete_group"]
        )
        self.btn_add = QPushButton(self.translations[self.current_lang]["add_selected"])
        self.btn_remove = QPushButton(
            self.translations[self.current_lang]["remove_selected"]
        )
        self.btn_up = QPushButton(self.translations[self.current_lang]["up"])
        self.btn_down = QPushButton(self.translations[self.current_lang]["down"])
        self.btn_vis = QPushButton(self.translations[self.current_lang]["toggle_vis"])
        self.btn_lock = QPushButton(self.translations[self.current_lang]["toggle_lock"])

        layout = QVBoxLayout()
        layout.addWidget(self.list)
        row = QHBoxLayout()
        row.addWidget(self.btn_new)
        row.addWidget(self.btn_delete)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_remove)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.btn_up)
        row.addWidget(self.btn_down)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.btn_vis)
        row.addWidget(self.btn_lock)
        layout.addLayout(row)
        self.setLayout(layout)

        self.btn_new.clicked.connect(self._on_new)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_add.clicked.connect(self._on_add_selected)
        self.btn_remove.clicked.connect(self._on_remove_selected)
        self.btn_up.clicked.connect(self._on_up)
        self.btn_down.clicked.connect(self._on_down)
        self.btn_vis.clicked.connect(self._on_toggle_vis)
        self.btn_lock.clicked.connect(self._on_toggle_lock)

        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self.refresh)
        self.refresh()

    def refresh(self):
        current_item = self.list.currentItem()
        current_group_id = (
            current_item.data(Qt.ItemDataRole.UserRole)
            if current_item is not None
            else None
        )

        self.list.blockSignals(True)
        self.list.clear()
        for group in getattr(self.scene, "groups", []):
            status = []
            if group.locked:
                status.append("[LOCKED]")
            if not group.visible:
                status.append("[HIDDEN]")
            suffix = " ".join(status)
            text = f"{group.name} {suffix} ({len(group.members)} items)"
            item = QListWidgetItem(text.replace("  ", " ").strip())
            item.setData(Qt.ItemDataRole.UserRole, group.id)
            self.list.addItem(item)

        if current_group_id is not None:
            self._select_group_id(current_group_id)
        self.list.blockSignals(False)

    def _select_group_id(self, group_id: str) -> bool:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == group_id:
                self.list.setCurrentItem(item)
                return True
        return False

    def _get_selected_group(self):
        item = self.list.currentItem()
        if item is None:
            return None, None
        group_id = item.data(Qt.ItemDataRole.UserRole)
        group = next(
            (
                candidate
                for candidate in getattr(self.scene, "groups", [])
                if candidate.id == group_id
            ),
            None,
        )
        return group, group_id

    def _execute_edit_command(self, command) -> Optional[CommandResult]:
        manager = getattr(self.scene, "cmd", None)
        translation = self.translations[self.current_lang]
        if manager is None:
            QMessageBox.critical(
                self,
                translation["error"],
                translation["history_unavailable"],
            )
            return None

        result = manager.execute(command, self.scene)
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self,
                translation["error"],
                result.message or translation["operation_rejected"],
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self,
                translation["error"],
                result.message or translation["operation_failed"],
            )
        return result

    def _on_new(self):
        translation = self.translations[self.current_lang]
        name, accepted = QInputDialog.getText(
            self,
            translation["new_group_title"],
            translation["name"],
        )
        if not accepted or not name:
            return
        try:
            command = CreateGroupCommand(name)
            result = self._execute_edit_command(command)
            if result is not None and result.changed and command.group_id:
                self._select_group_id(command.group_id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                translation["error"],
                str(exc),
            )

    def _on_delete(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            self._show_no_group()
            return
        try:
            self._execute_edit_command(RemoveGroupCommand(group_id))
        except Exception as exc:
            self._show_error(exc)

    def _on_add_selected(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            self._show_no_group()
            return
        object_id = getattr(self.scene, "selected_id", None)
        if not object_id:
            self._show_no_object()
            return
        try:
            self._execute_edit_command(AddToGroupCommand(group_id, object_id))
        except Exception as exc:
            self._show_error(exc)

    def _on_remove_selected(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            self._show_no_group()
            return
        object_id = getattr(self.scene, "selected_id", None)
        if not object_id:
            self._show_no_object()
            return
        try:
            self._execute_edit_command(RemoveFromGroupCommand(group_id, object_id))
        except Exception as exc:
            self._show_error(exc)

    def _on_up(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            return
        try:
            index = self.scene.groups.index(group)
            if index <= 0:
                return
            self._execute_edit_command(MoveGroupCommand(group_id, index - 1))
        except Exception as exc:
            self._show_error(exc)

    def _on_down(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            return
        try:
            index = self.scene.groups.index(group)
            if index >= len(self.scene.groups) - 1:
                return
            self._execute_edit_command(MoveGroupCommand(group_id, index + 1))
        except Exception as exc:
            self._show_error(exc)

    def _on_toggle_vis(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            return
        try:
            self._execute_edit_command(ToggleGroupVisibilityCommand(group_id))
        except Exception as exc:
            self._show_error(exc)

    def _on_toggle_lock(self):
        group, group_id = self._get_selected_group()
        if group is None or group_id is None:
            return
        try:
            self._execute_edit_command(ToggleGroupLockCommand(group_id))
        except Exception as exc:
            self._show_error(exc)

    def _show_no_group(self):
        translation = self.translations[self.current_lang]
        QMessageBox.information(
            self,
            translation["info"],
            translation["no_group_selected"],
        )

    def _show_no_object(self):
        translation = self.translations[self.current_lang]
        QMessageBox.information(
            self,
            translation["info"],
            translation["no_object_selected"],
        )

    def _show_error(self, exc: BaseException):
        translation = self.translations[self.current_lang]
        QMessageBox.critical(
            self,
            translation["error"],
            str(exc),
        )

    def update_language(self, lang):
        self.current_lang = lang
        translation = self.translations[self.current_lang]
        self.btn_new.setText(translation["new_group"])
        self.btn_delete.setText(translation["delete_group"])
        self.btn_add.setText(translation["add_selected"])
        self.btn_remove.setText(translation["remove_selected"])
        self.btn_up.setText(translation["up"])
        self.btn_down.setText(translation["down"])
        self.btn_vis.setText(translation["toggle_vis"])
        self.btn_lock.setText(translation["toggle_lock"])
