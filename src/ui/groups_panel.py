# src/ui/groups_panel.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt


class GroupsPanel(QWidget):
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
            },
        }
        self.list = QListWidget()
        self.btn_new = QPushButton(
            self.translations[self.current_lang]["new_group"]
        )
        self.btn_delete = QPushButton(
            self.translations[self.current_lang]["delete_group"]
        )
        self.btn_add = QPushButton(
            self.translations[self.current_lang]["add_selected"]
        )
        self.btn_remove = QPushButton(
            self.translations[self.current_lang]["remove_selected"]
        )
        self.btn_up = QPushButton(self.translations[self.current_lang]["up"])
        self.btn_down = QPushButton(
            self.translations[self.current_lang]["down"]
        )
        self.btn_vis = QPushButton(
            self.translations[self.current_lang]["toggle_vis"]
        )
        self.btn_lock = QPushButton(
            self.translations[self.current_lang]["toggle_lock"]
        )

        layout = QVBoxLayout()
        layout.addWidget(self.list)
        h = QHBoxLayout()
        h.addWidget(self.btn_new)
        h.addWidget(self.btn_delete)
        layout.addLayout(h)
        h2 = QHBoxLayout()
        h2.addWidget(self.btn_add)
        h2.addWidget(self.btn_remove)
        layout.addLayout(h2)
        h3 = QHBoxLayout()
        h3.addWidget(self.btn_up)
        h3.addWidget(self.btn_down)
        layout.addLayout(h3)
        h4 = QHBoxLayout()
        h4.addWidget(self.btn_vis)
        h4.addWidget(self.btn_lock)
        layout.addLayout(h4)
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
        # 1. Guarda o ID do grupo selecionado (user data), não o texto
        current_item = self.list.currentItem()
        current_gid = current_item.data(Qt.UserRole) if current_item else None

        # 2. Bloqueia sinais para evitar loops de evento
        self.list.blockSignals(True)
        self.list.clear()
        
        for g in getattr(self.scene, "groups", []):
            # Formatação visual do status
            status = []
            if g.locked:
                status.append("[LOCKED]")
            if not g.visible:
                status.append("[HIDDEN]")
            status_str = " ".join(status)
            
            item_text = f"{g.name} {status_str} ({len(g.members)} items)"
            item = QListWidgetItem(item_text)
            
            # Dados reais ficam seguros aqui
            item.setData(Qt.UserRole, g.id)
            self.list.addItem(item)

        # 3. Restaura a seleção baseada no ID
        if current_gid:
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item.data(Qt.UserRole) == current_gid:
                    self.list.setCurrentItem(item)
                    break
        
        self.list.blockSignals(False)

    def _get_selected_group(self):
        items = self.list.selectedItems()
        if not items:
            return None, None

        full_gid = items[0].data(Qt.UserRole)

        g = next(
            (x for x in getattr(self.scene, "groups", []) if x.id == full_gid),
            None,
        )
        return g, full_gid

    def _on_new(self):
        name, ok = QInputDialog.getText(
            self,
            self.translations[self.current_lang]["new_group_title"],
            self.translations[self.current_lang]["name"],
        )
        if not ok or not name:
            return
        try:
            from src.core.commands import CreateGroupCommand

            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(CreateGroupCommand(name), self.scene)
            else:
                self.scene.create_group(name)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_delete(self):
        g, gid = self._get_selected_group()
        if not g:
            QMessageBox.information(
                self,
                self.translations[self.current_lang]["info"],
                self.translations[self.current_lang]["no_group_selected"],
            )
            return
        try:
            from src.core.commands import RemoveGroupCommand

            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(RemoveGroupCommand(g.id), self.scene)
            else:
                self.scene.remove_group(g.id)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_add_selected(self):
        g, gid = self._get_selected_group()
        if not g:
            QMessageBox.information(
                self,
                self.translations[self.current_lang]["info"],
                self.translations[self.current_lang]["no_group_selected"],
            )
            return
        sid = getattr(self.scene, "selected_id", None)
        if not sid:
            QMessageBox.information(
                self,
                self.translations[self.current_lang]["info"],
                self.translations[self.current_lang]["no_object_selected"],
            )
            return
        try:
            from src.core.commands import AddToGroupCommand

            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(
                    AddToGroupCommand(g.id, sid), self.scene
                )
            else:
                self.scene.add_object_to_group(g.id, sid)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_remove_selected(self):
        g, gid = self._get_selected_group()
        if not g:
            QMessageBox.information(
                self,
                self.translations[self.current_lang]["info"],
                self.translations[self.current_lang]["no_group_selected"],
            )
            return
        sid = getattr(self.scene, "selected_id", None)
        if not sid:
            QMessageBox.information(
                self,
                self.translations[self.current_lang]["info"],
                self.translations[self.current_lang]["no_object_selected"],
            )
            return
        try:
            from src.core.commands import RemoveFromGroupCommand

            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(
                    RemoveFromGroupCommand(g.id, sid), self.scene
                )
            else:
                self.scene.remove_object_from_group(g.id, sid)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_up(self):
        g, gid = self._get_selected_group()
        if not g:
            return
        try:
            from src.core.commands import MoveGroupCommand

            idx = max(0, getattr(self.scene, "groups", []).index(g) - 1)
            
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(MoveGroupCommand(g.id, idx), self.scene)
            else:
                self.scene.move_group(g.id, idx)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_down(self):
        g, gid = self._get_selected_group()
        if not g:
            return
        try:
            from src.core.commands import MoveGroupCommand

            groups = getattr(self.scene, "groups", [])
            idx = min(len(groups) - 1, groups.index(g) + 1)
            
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(MoveGroupCommand(g.id, idx), self.scene)
            else:
                self.scene.move_group(g.id, idx)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_toggle_vis(self):
        g, gid = self._get_selected_group()
        if not g:
            return
        try:
            # Não há comando específico para toggle group vis em commands.py,
            # modificação direta é aceitável neste contexto ou exigiria criar o comando.
            g.visible = not g.visible
            self.scene._notify()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_toggle_lock(self):
        g, gid = self._get_selected_group()
        if not g:
            return
        try:
            g.locked = not g.locked
            self.scene._notify()
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def update_language(self, lang):
        self.current_lang = lang
        t = self.translations[self.current_lang]
        self.btn_new.setText(t["new_group"])
        self.btn_delete.setText(t["delete_group"])
        self.btn_add.setText(t["add_selected"])
        self.btn_remove.setText(t["remove_selected"])
        self.btn_up.setText(t["up"])
        self.btn_down.setText(t["down"])
        self.btn_vis.setText(t["toggle_vis"])
        self.btn_lock.setText(t["toggle_lock"])