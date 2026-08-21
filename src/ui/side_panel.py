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

from src.core.commands import (
    CommandStatus,
    DeleteObjectCommand,
    RenameObjectCommand,
    ToggleCollisionCommand,
    UpdatePolygonCommand,
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

        # Botão de forma de colisão
        self.btn_collision = QPushButton("Collision: OFF")
        self.btn_collision.setCheckable(True)
        self.btn_collision.setObjectName("collision_toggle")

        self.slider_label = QLabel("Expand/Contract: 0 px")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-50)
        self.slider.setMaximum(50)
        self.slider.setValue(0)
        self.btn_apply = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_export = QPushButton("Export Mask")
        self.btn_export_now = QPushButton("Export Sprite")

        # Layout
        layout = QVBoxLayout()
        self.scene_objects_label = QLabel("Scene Objects:")
        layout.addWidget(self.scene_objects_label)
        layout.addWidget(self.list)

        # Grupo 1: edição e colisão
        self.properties_group = QGroupBox("Properties")
        l_edit = QVBoxLayout()
        h_basic = QHBoxLayout()
        h_basic.addWidget(self.btn_rename)
        h_basic.addWidget(self.btn_delete)
        l_edit.addLayout(h_basic)
        l_edit.addWidget(self.btn_collision)  # Adicionando o botão ao layout
        self.properties_group.setLayout(l_edit)
        layout.addWidget(self.properties_group)

        # Grupo 2: Modificadores
        self.modify_shape_group = QGroupBox("Modify Shape")
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
        self.modify_shape_group.setLayout(l_tools)
        layout.addWidget(self.modify_shape_group)

        # Grupo 3: Exportação
        self.export_group = QGroupBox("Export")
        l_export = QVBoxLayout()
        l_export.addWidget(self.btn_export)
        l_export.addWidget(self.btn_export_now)
        self.export_group.setLayout(l_export)
        layout.addWidget(self.export_group)

        self.setLayout(layout)

        # Conexões
        self.list.itemSelectionChanged.connect(self._on_select)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_rename.clicked.connect(self._on_rename)
        self.btn_collision.clicked.connect(self._on_toggle_collision)
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
                "collision_off": "Collision: OFF",
                "collision_on": "Collision: ON",
                "collision_dash": "Collision: --",
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
                "collision_toggle_error": "Collision Toggle Error: ",
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
                "collision_off": "Colisão: DESLIGADA",
                "collision_on": "Colisão: LIGADA",
                "collision_dash": "Colisão: --",
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
                "collision_toggle_error": "Erro ao Alternar Colisão: ",
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
            has_collision = oid in self.scene.collision_shapes
            self.btn_collision.setChecked(has_collision)
            self.btn_collision.setText(
                self.translations[self.current_lang][
                    "collision_on" if has_collision else "collision_off"
                ]
            )
            self.btn_collision.setEnabled(True)
        else:
            self.btn_collision.setChecked(False)
            self.btn_collision.setText(
                self.translations[self.current_lang]["collision_dash"]
            )
            self.btn_collision.setEnabled(False)

    def _on_select(self):
        self._update_button_states()
        oid, obj = self._get_selected_obj()
        # Avisa a cena (opcional, se a cena tiver conceito de seleção)
        if oid and hasattr(self.scene, "select_object"):
            try:
                self.scene.select_object(oid)
            except Exception:
                pass

    def _execute_edit_command(self, command):
        manager = getattr(self.scene, "cmd", None)
        if manager is None:
            raise RuntimeError("Undo/Redo command history is unavailable.")

        result = manager.execute(command, self.scene)
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self,
                self.translations[self.current_lang]["error"],
                result.message or "The edit operation was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                result.message or "The edit operation failed.",
            )
        return result

    def _on_toggle_collision(self):
        oid, _ = self._get_selected_obj()
        if not oid:
            return

        try:
            result = self._execute_edit_command(ToggleCollisionCommand(oid))
            if result.changed:
                self.canvas.update()
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                self.translations[self.current_lang]["collision_toggle_error"]
                + str(exc),
            )

    def _on_toggle_physics(self):
        """Compatibility adapter for historical callers."""
        self._on_toggle_collision()

    def _on_delete(self):
        oid, _ = self._get_selected_obj()
        if oid is None:
            return
        response = QMessageBox.question(
            self,
            self.translations[self.current_lang]["delete_title"],
            self.translations[self.current_lang]["delete_object"] + oid + "?",
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            self._execute_edit_command(DeleteObjectCommand(oid))
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_rename(self):
        oid, _ = self._get_selected_obj()
        if oid is None:
            return
        new_id, accepted = QInputDialog.getText(
            self,
            self.translations[self.current_lang]["rename_title"],
            self.translations[self.current_lang]["new_id"],
            text=oid,
        )
        if not accepted or not new_id:
            return

        try:
            self._execute_edit_command(RenameObjectCommand(oid, new_id))
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
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
            height, width = self.scene.image.shape[:2]
            new_polygon = expand_contract_polygon(
                obj.polygon,
                (height, width),
                delta,
            )
            if new_polygon:
                self._execute_edit_command(
                    UpdatePolygonCommand(
                        oid,
                        list(obj.polygon),
                        list(new_polygon),
                    )
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_invert(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        try:
            height, width = self.scene.image.shape[:2]
            new_polygon = invert_selection(
                obj.polygon,
                (height, width),
            )
            if new_polygon:
                self._execute_edit_command(
                    UpdatePolygonCommand(
                        oid,
                        list(obj.polygon),
                        list(new_polygon),
                    )
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
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

    def _reset_shape_preview(self):
        self._last_preview_poly = None
        self.slider.blockSignals(True)
        try:
            self.slider.setValue(0)
        finally:
            self.slider.blockSignals(False)
        self.slider_label.setText(
            self.translations[self.current_lang]["expand_contract"]
        )
        self.canvas.clear_temp_mask()

    def _on_apply(self):
        if not self._last_preview_poly:
            return
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        try:
            result = self._execute_edit_command(
                UpdatePolygonCommand(
                    oid,
                    list(obj.polygon),
                    list(self._last_preview_poly),
                )
            )
            if result.ok:
                self._reset_shape_preview()
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_cancel_preview(self):
        self._reset_shape_preview()

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
        self.scene_objects_label.setText(t["scene_objects"])
        # Buttons
        self.btn_rename.setText(t["rename"])
        self.btn_delete.setText(t["delete"])
        self.btn_expand.setText(t["expand"])
        self.btn_contract.setText(t["contract"])
        self.btn_invert.setText(t["invert"])
        # Groups
        self.properties_group.setTitle(t["properties"])
        self.modify_shape_group.setTitle(t["modify_shape"])
        self.export_group.setTitle(t["export"])
        self.slider_label.setText(t["expand_contract"])
        self.btn_apply.setText(t["apply"])
        self.btn_cancel.setText(t["cancel"])
        self.btn_export.setText(t["export_mask"])
        self.btn_export_now.setText(t["export_sprite"])
        # Update collision button state
        self._update_button_states()
