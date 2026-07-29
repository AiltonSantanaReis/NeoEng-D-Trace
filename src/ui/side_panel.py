# src/ui/side_panel.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import logger
from src.core.validation_events import object_token, record_validation_event
from src.utils.selection_tools import (
    expand_contract_polygon,
    invert_selection,
    polygon_to_mask,
)


class SidePanel(QWidget):
    def __init__(self, scene, canvas, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.canvas = canvas
        self._last_validation_selection_marker = None

        self.list = QListWidget()

        # --- Botões ---
        self.btn_rename = QPushButton("Rename")
        self.btn_delete = QPushButton("Delete")

        self.btn_expand = QPushButton("Expand")
        self.btn_contract = QPushButton("Contract")
        self.btn_invert = QPushButton("Invert")

        # Botão de Física (Toggle)
        self.btn_physics = QPushButton("Physics: OFF")
        self.btn_physics.setCheckable(True)
        # Estilo para destacar quando ativo (Azul)
        self.btn_physics.setStyleSheet("""
            QPushButton { background-color: #3c3c3c; color: #aaaaaa; }
            QPushButton:checked { background-color: #007acc; color: white;
            border: 1px solid #0099ff; font-weight: bold; }
        """)

        self.slider_label = QLabel("Expand/Contract: 0 px")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(-50)
        self.slider.setMaximum(50)
        self.slider.setValue(0)
        self.btn_apply = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_export = QPushButton("Export Mask")
        self.btn_export_now = QPushButton("Export Sprite")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Scene Objects:"))
        layout.addWidget(self.list)

        # Grupo 1: Edição e Física
        g_edit = QGroupBox("Properties")
        l_edit = QVBoxLayout()
        h_basic = QHBoxLayout()
        h_basic.addWidget(self.btn_rename)
        h_basic.addWidget(self.btn_delete)
        l_edit.addLayout(h_basic)
        l_edit.addWidget(self.btn_physics)  # Adicionando o botão ao layout
        g_edit.setLayout(l_edit)
        layout.addWidget(g_edit)

        # Grupo 2: Modificadores
        g_tools = QGroupBox("Modify Shape")
        l_tools = QVBoxLayout()
        h_mod = QHBoxLayout()
        h_mod.addWidget(self.btn_expand)
        h_mod.addWidget(self.btn_contract)
        h_mod.addWidget(self.btn_invert)
        l_tools.addLayout(h_mod)
        l_tools.addWidget(self.slider_label)
        l_tools.addWidget(self.slider)
        h_apply = QHBoxLayout()
        h_apply.addWidget(self.btn_apply)
        h_apply.addWidget(self.btn_cancel)
        l_tools.addLayout(h_apply)
        g_tools.setLayout(l_tools)
        layout.addWidget(g_tools)

        # Grupo 3: Exportação
        g_export = QGroupBox("Export")
        l_export = QVBoxLayout()
        l_export.addWidget(self.btn_export)
        l_export.addWidget(self.btn_export_now)
        g_export.setLayout(l_export)
        layout.addWidget(g_export)

        self.setLayout(layout)

        # Conexões
        self.list.itemSelectionChanged.connect(self._on_select)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_rename.clicked.connect(self._on_rename)
        self.btn_physics.clicked.connect(self._on_toggle_physics)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_expand.clicked.connect(self._on_expand)
        self.btn_contract.clicked.connect(self._on_contract)
        self.btn_invert.clicked.connect(self._on_invert)
        self.slider.valueChanged.connect(self._on_slider_change)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_cancel.clicked.connect(self._on_cancel_preview)
        self.btn_export_now.clicked.connect(self._on_export_now)

        self.current_lang = "en"
        self.translations = {
            "en": {
                "scene_objects": "Scene Objects:",
                "rename": "Rename",
                "delete": "Delete",
                "expand": "Expand",
                "contract": "Contract",
                "invert": "Invert",
                "physics_off": "Physics: OFF",
                "physics_on": "Physics: ON",
                "physics_dash": "Physics: --",
                "apply": "Apply",
                "cancel": "Cancel",
                "export_mask": "Export Mask",
                "export_sprite": "Export Sprite",
                "properties": "Properties",
                "modify_shape": "Modify Shape",
                "export": "Export",
                "expand_contract": "Expand/Contract: 0 px",
                "preview": "Preview: ",
                "delete_title": "Delete",
                "delete_object": "Delete object ",
                "rename_title": "Rename",
                "new_id": "New id:",
                "error": "Error",
                "physics_toggle_error": "Physics Toggle Error: ",
                "expand_title": "Expand",
                "pixels": "Pixels:",
                "contract_title": "Contract",
                "save_mask": "Save mask",
                "png_image": "PNG Image (*.png)",
                "save_sprite": "Save sprite",
            },
            "pt": {
                "scene_objects": "Objetos da Cena:",
                "rename": "Renomear",
                "delete": "Excluir",
                "expand": "Expandir",
                "contract": "Contrair",
                "invert": "Inverter",
                "physics_off": "Física: DESLIGADA",
                "physics_on": "Física: LIGADA",
                "physics_dash": "Física: --",
                "apply": "Aplicar",
                "cancel": "Cancelar",
                "export_mask": "Exportar Máscara",
                "export_sprite": "Exportar Sprite",
                "properties": "Propriedades",
                "modify_shape": "Modificar Forma",
                "export": "Exportar",
                "expand_contract": "Expandir/Contrair: 0 px",
                "preview": "Prévia: ",
                "delete_title": "Excluir",
                "delete_object": "Excluir objeto ",
                "rename_title": "Renomear",
                "new_id": "Novo id:",
                "error": "Erro",
                "physics_toggle_error": "Erro ao Alternar Física: ",
                "expand_title": "Expandir",
                "pixels": "Pixels:",
                "contract_title": "Contrair",
                "save_mask": "Salvar máscara",
                "png_image": "Imagem PNG (*.png)",
                "save_sprite": "Salvar sprite",
            },
        }

        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self.refresh)
        self.refresh()
        self._last_preview_poly = None

    def refresh(self):
        """Rebuild the object list and mirror the scene selection exactly."""
        selected_id = getattr(self.scene, "selected_id", None)

        self.list.blockSignals(True)
        try:
            self.list.clear()
            selected_item = None

            for oid, obj in sorted(self.scene.objects.items()):
                suffix = " [P]" if oid in self.scene.collision_shapes else ""
                self.list.addItem(f"{oid}{suffix}")
                if oid == selected_id:
                    selected_item = self.list.item(self.list.count() - 1)

            if selected_item is not None:
                self.list.setCurrentItem(selected_item)
            else:
                self.list.clearSelection()
                self.list.setCurrentRow(-1)
        finally:
            self.list.blockSignals(False)

        actual_id, _ = self._get_selected_obj()
        marker = (selected_id, actual_id)
        if selected_id is not None and marker != self._last_validation_selection_marker:
            synchronized = selected_id == actual_id
            record_validation_event(
                "selection.synced",
                "SUCCESS" if synchronized else "FAILURE",
                scene_object_token=object_token(selected_id),
                list_object_token=object_token(actual_id),
                synchronized=synchronized,
                list_count=self.list.count(),
            )
        self._last_validation_selection_marker = marker
        self._update_button_states()

    def _get_selected_obj(self):
        items = self.list.selectedItems()
        if not items:
            return None, None
        full_text = items[0].text()
        oid = full_text.replace(" [P]", "")
        obj = self.scene.objects.get(oid)
        return oid, obj

    def _update_button_states(self):
        oid, obj = self._get_selected_obj()
        if obj:
            has_physics = oid in self.scene.collision_shapes
            self.btn_physics.setChecked(has_physics)
            self.btn_physics.setText(
                self.translations[self.current_lang][
                    "physics_on" if has_physics else "physics_off"
                ]
            )
            self.btn_physics.setEnabled(True)
        else:
            self.btn_physics.setChecked(False)
            self.btn_physics.setText(
                self.translations[self.current_lang]["physics_dash"]
            )
            self.btn_physics.setEnabled(False)

    def _on_select(self):
        self._update_button_states()
        oid, obj = self._get_selected_obj()
        # Avisa a cena (opcional, se a cena tiver conceito de seleção)
        if oid and hasattr(self.scene, "select_object"):
            try:
                self.scene.select_object(oid)
            except Exception:
                pass

    def _on_toggle_physics(self):
        oid, obj = self._get_selected_obj()
        if not oid:
            return

        try:
            # Tenta usar comando para Undo/Redo
            try:
                from src.core.commands import ToggleCollisionCommand

                if hasattr(self.scene, "cmd") and self.scene.cmd:
                    self.scene.cmd.execute(ToggleCollisionCommand(oid), self.scene)
                    return
            except ImportError:
                pass

            # Fallback manual
            curr = self.scene.has_collision(oid)
            self.scene.set_object_collision(oid, not curr)
            self.canvas.update()

        except Exception as e:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                self.translations[self.current_lang]["physics_toggle_error"] + str(e),
            )

    def _on_delete(self):
        oid, obj = self._get_selected_obj()
        if oid is None:
            return
        resp = QMessageBox.question(
            self,
            self.translations[self.current_lang]["delete_title"],
            self.translations[self.current_lang]["delete_object"] + oid + "?",
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        # Tenta usar comando para Undo/Redo
        try:
            from src.core.commands import DeleteObjectCommand

            if hasattr(self.scene, "cmd") and self.scene.cmd:
                self.scene.cmd.execute(DeleteObjectCommand(oid), self.scene)
                return
        except ImportError:
            pass

        # Fallback manual
        try:
            self.scene.remove_object(oid)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_rename(self):
        oid, obj = self._get_selected_obj()
        if oid is None:
            return
        new, ok = QInputDialog.getText(
            self,
            self.translations[self.current_lang]["rename_title"],
            self.translations[self.current_lang]["new_id"],
            text=oid,
        )
        if not ok or not new:
            return
        try:
            # Renomeia na cena e migra colisão
            self.scene.objects[new] = self.scene.objects.pop(oid)
            self.scene.objects[new].id = new
            if oid in self.scene.collision_shapes:
                self.scene.collision_shapes[new] = self.scene.collision_shapes.pop(oid)
            self.scene._notify()
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_export(self):
        import cv2
        import numpy as np
        from PIL import Image

        oid, obj = self._get_selected_obj()
        if obj is None:
            logger.info("Export mask: No object selected")
            return
        logger.info(f"Export mask: Starting for object {oid}")
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations[self.current_lang]["save_mask"],
            oid + ".png",
            self.translations[self.current_lang]["png_image"],
        )
        if not path:
            logger.info("Export mask: User canceled save dialog")
            return
        if self.scene.image is None:
            logger.error("Export mask: No image loaded in scene")
            return
        logger.info("Export mask: Creating mask")
        h, w = self.scene.image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        pts = np.array(obj.polygon, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        pil = Image.fromarray(mask, "L")
        try:
            pil.save(path)
            logger.info(f"Export mask: Mask saved successfully to {path}")
        except Exception as e:
            logger.error(f"Export mask: Failed to save mask to {path}: {e}")

    def _on_expand(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        val, ok = QInputDialog.getInt(
            self,
            self.translations[self.current_lang]["expand_title"],
            self.translations[self.current_lang]["pixels"],
            value=4,
            minValue=1,
        )
        if ok:
            self._modify_poly(oid, obj, val)

    def _on_contract(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        val, ok = QInputDialog.getInt(
            self,
            self.translations[self.current_lang]["contract_title"],
            self.translations[self.current_lang]["pixels"],
            value=4,
            minValue=1,
        )
        if ok:
            self._modify_poly(oid, obj, -val)

    def _modify_poly(self, oid, obj, delta):
        try:
            h, w = self.scene.image.shape[:2]
            new_poly = expand_contract_polygon(obj.polygon, (h, w), delta)
            if new_poly:
                self.scene.update_polygon(oid, new_poly)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_invert(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        try:
            h, w = self.scene.image.shape[:2]
            new_poly = invert_selection(obj.polygon, (h, w))
            if new_poly:
                self.scene.update_polygon(oid, new_poly)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_slider_change(self, value):
        self.slider_label.setText(
            self.translations[self.current_lang]["preview"] + f"{value} px"
        )
        oid, obj = self._get_selected_obj()
        if not obj:
            self.canvas.clear_temp_mask()
            return
        try:
            h, w = self.scene.image.shape[:2]
            poly = expand_contract_polygon(obj.polygon, (h, w), int(value))
            if poly:
                mask = polygon_to_mask(poly, (h, w))
                self.canvas.show_temp_mask(mask)
                self._last_preview_poly = poly
            else:
                self.canvas.clear_temp_mask()
                self._last_preview_poly = None
        except Exception:
            self.canvas.clear_temp_mask()

    def _on_apply(self):
        if not self._last_preview_poly:
            return
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        try:
            from src.core.commands import ExpandContractCommand

            cmd = ExpandContractCommand(
                oid, list(obj.polygon), list(self._last_preview_poly)
            )
            self.scene.cmd.execute(cmd, self.scene)
            self.canvas.clear_temp_mask()
            self._last_preview_poly = None
            self.slider.setValue(0)
        except Exception as e:
            QMessageBox.critical(
                self, self.translations[self.current_lang]["error"], str(e)
            )

    def _on_cancel_preview(self):
        self._last_preview_poly = None
        self.slider.setValue(0)
        self.canvas.clear_temp_mask()

    def _on_export_now(self):
        from src.exporters.sprite_exporter import (
            extract_masked_sprite,
            save_sprite,
        )

        oid, obj = self._get_selected_obj()
        if not obj:
            logger.info("Export sprite: No object selected")
            return
        logger.info(f"Export sprite: Starting for object {oid}")
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations[self.current_lang]["save_sprite"],
            oid + ".png",
            self.translations[self.current_lang]["png_image"],
        )
        if path:
            logger.info("Export sprite: Extracting masked sprite")
            try:
                img = extract_masked_sprite(self.scene.image, obj.polygon, padding=4)
                logger.info("Export sprite: Sprite extracted, saving")
                save_sprite(img, path)
                logger.info(f"Export sprite: Sprite saved successfully to {path}")
            except Exception as e:
                logger.error(f"Export sprite: Failed to export sprite for {oid}: {e}")
                QMessageBox.critical(
                    self, self.translations[self.current_lang]["error"], str(e)
                )

    def update_language(self, lang):
        self.current_lang = lang
        t = self.translations[self.current_lang]
        # Update labels
        self.layout().itemAt(0).widget().setText(
            t["scene_objects"]
        )  # QLabel "Scene Objects:"
        # Buttons
        self.btn_rename.setText(t["rename"])
        self.btn_delete.setText(t["delete"])
        self.btn_expand.setText(t["expand"])
        self.btn_contract.setText(t["contract"])
        self.btn_invert.setText(t["invert"])
        # Groups
        self.layout().itemAt(2).widget().setTitle(t["properties"])  # g_edit
        self.layout().itemAt(3).widget().setTitle(t["modify_shape"])  # g_tools
        self.layout().itemAt(4).widget().setTitle(t["export"])  # g_export
        self.slider_label.setText(t["expand_contract"])
        self.btn_apply.setText(t["apply"])
        self.btn_cancel.setText(t["cancel"])
        self.btn_export.setText(t["export_mask"])
        self.btn_export_now.setText(t["export_sprite"])
        # Update physics button state
        self._update_button_states()
