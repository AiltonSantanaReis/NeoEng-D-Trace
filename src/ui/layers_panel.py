# src/ui/layers_panel.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QHBoxLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt


class LayersPanel(QWidget):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setMinimumWidth(200)
        
        self.layout = QVBoxLayout()
        self.list = QListWidget()
        self.layout.addWidget(self.list)
        
        btns = QHBoxLayout()
        self.btn_new = QPushButton("New")
        self.btn_delete = QPushButton("Delete")
        self.btn_up = QPushButton("Up")
        self.btn_down = QPushButton("Down")
        self.btn_vis = QPushButton("Toggle Vis")
        self.btn_lock = QPushButton("Toggle Lock")
        
        for b in (
            self.btn_new,
            self.btn_delete,
            self.btn_up,
            self.btn_down,
            self.btn_vis,
            self.btn_lock,
        ):
            btns.addWidget(b)
            
        self.layout.addLayout(btns)
        self.setLayout(self.layout)
        
        # Conexões
        self.btn_new.clicked.connect(self._create)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_up.clicked.connect(self._up)
        self.btn_down.clicked.connect(self._down)
        self.btn_vis.clicked.connect(self._toggle_vis)
        self.btn_lock.clicked.connect(self._toggle_lock)
        
        # Integração com o sistema de notificação da cena (Observer)
        # Isso garante que Undo/Redo atualize a lista automaticamente
        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self.refresh)
            
        self.refresh()

    def refresh(self):
        # Tenta preservar a seleção atual
        current_row = self.list.currentRow()
        
        self.list.clear()
        for layer in self.scene.layers:
            # Formatação visual do estado da camada
            status = []
            if layer.locked:
                status.append("[LOCKED]")
            if not layer.visible:
                status.append("[HIDDEN]")
            
            status_str = " ".join(status)
            name = f"{layer.name} {status_str}"
            self.list.addItem(name)
            
        # Restaura seleção se possível
        if 0 <= current_row < self.list.count():
            self.list.setCurrentRow(current_row)

    def _create(self):
        try:
            # Verifica se o CommandManager existe e está pronto
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                from src.core.commands import CreateLayerCommand
                # CORREÇÃO: Passando self.scene como argumento
                self.scene.cmd.execute(CreateLayerCommand("New Layer"), self.scene)
            else:
                # Fallback direto
                self.scene.create_layer("New Layer")
                # Se for fallback manual, precisamos chamar refresh manual
                # (Se for via comando, o subscribe cuida disso)
                self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _delete(self):
        idx = self.list.currentRow()
        if idx < 0:
            return
        
        # Proteção contra índice fora de limites
        if idx >= len(self.scene.layers):
            return

        lid = self.scene.layers[idx].id
        try:
            from src.core.commands import RemoveLayerCommand
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                # CORREÇÃO: Passando self.scene como argumento
                self.scene.cmd.execute(RemoveLayerCommand(lid), self.scene)
            else:
                self.scene.remove_layer(lid)
                self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _up(self):
        idx = self.list.currentRow()
        if idx <= 0:
            return
        
        lid = self.scene.layers[idx].id
        try:
            from src.core.commands import MoveLayerCommand
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                # Move para cima significa diminuir o índice
                self.scene.cmd.execute(MoveLayerCommand(lid, idx - 1), self.scene)
            else:
                self.scene.move_layer(lid, idx - 1)
                self.refresh()
                
            # Ajusta seleção para seguir o item movido
            self.list.setCurrentRow(idx - 1)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _down(self):
        idx = self.list.currentRow()
        if idx < 0 or idx >= len(self.scene.layers) - 1:
            return
            
        lid = self.scene.layers[idx].id
        try:
            from src.core.commands import MoveLayerCommand
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                # Move para baixo significa aumentar o índice
                self.scene.cmd.execute(MoveLayerCommand(lid, idx + 1), self.scene)
            else:
                self.scene.move_layer(lid, idx + 1)
                self.refresh()
                
            # Ajusta seleção para seguir o item movido
            self.list.setCurrentRow(idx + 1)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _toggle_vis(self):
        idx = self.list.currentRow()
        if idx < 0:
            return
        lid = self.scene.layers[idx].id
        try:
            from src.core.commands import ToggleLayerVisibilityCommand
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(ToggleLayerVisibilityCommand(lid), self.scene)
            else:
                curr = self.scene.layers[idx].visible
                self.scene.set_layer_visibility(lid, not curr)
                self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _toggle_lock(self):
        idx = self.list.currentRow()
        if idx < 0:
            return
        lid = self.scene.layers[idx].id
        try:
            from src.core.commands import ToggleLayerLockCommand
            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(ToggleLayerLockCommand(lid), self.scene)
            else:
                curr = self.scene.layers[idx].locked
                self.scene.set_layer_lock(lid, not curr)
                self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))