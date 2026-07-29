import json
import os
import re
import time
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.core.logger import logger
from src.core.validation_events import (
    elapsed_ms,
    file_evidence,
    object_token,
    record_validation_event,
    record_validation_exception,
    validation_output_path,
)

# Protected imports keep the dialog available even if one exporter is missing.
try:
    from src.exporters.sprite_exporter import extract_masked_sprite, save_sprite

    HAS_SPRITE_EXPORTER = True
except ImportError:
    HAS_SPRITE_EXPORTER = False
    logger.error("Failed to import sprite_exporter")

try:
    from src.exporters.atlas_exporter import build_atlas

    HAS_ATLAS_EXPORTER = True
except ImportError:
    HAS_ATLAS_EXPORTER = False
    logger.error("Failed to import atlas_exporter")

try:
    from src.exporters.json_exporter import export_metadata

    HAS_METADATA_EXPORTER = True
except ImportError:
    HAS_METADATA_EXPORTER = False
    logger.error("Failed to import json_exporter")

try:
    from src.exporters.gltf_exporter import (
        export_object_to_gltf,
        export_scene_to_gltf,
    )

    HAS_GLTF_EXPORTER = True
except ImportError:
    HAS_GLTF_EXPORTER = False
    logger.error("Failed to import gltf_exporter")


class ExportDialog(QDialog):
    """Bilingual export dialog with stable exporter/profile identifiers."""

    TRANSLATIONS = {
        "en": {
            "window_title": "Export Options",
            "group_2d": "2D Sprites & Atlas",
            "single": "Export Selected Sprite",
            "batch": "Batch Export All Sprites",
            "atlas": "Build Texture Atlas",
            "metadata_heading": "Engine Metadata (JSON)",
            "target": "Target:",
            "profile_generic": "Generic JSON",
            "profile_godot": "Godot 4",
            "profile_unity": "Unity",
            "profile_phaser": "Phaser 3",
            "metadata_selected": "Export Selected Object Metadata",
            "metadata_tooltip": (
                "Exports JSON metadata for the selected 2D object. "
                "Sprite, atlas and GLTF exports are unchanged."
            ),
            "group_3d": "3D Models (GLTF)",
            "gltf_scene": "Export Full Scene to GLTF",
            "gltf_object": "Export Selected Object to GLTF",
            "close": "Close",
            "module_sprite_missing": "Module sprite_exporter missing",
            "module_atlas_missing": "Module atlas_exporter missing",
            "module_json_missing": "Module json_exporter missing",
            "module_gltf_missing": "Module gltf_exporter missing",
            "error": "Error",
            "info": "Info",
            "success": "Success",
            "warning": "Warning",
            "failed": "Failed",
            "cancel": "Cancel",
            "no_image": "No image loaded in scene.",
            "no_objects": "Scene has no objects to export.",
            "no_selection": "No object selected.",
            "save_metadata": "Save Object Metadata",
            "json_metadata_filter": "JSON Metadata (*.json)",
            "metadata_success": "{profile} metadata exported successfully.\n{path}",
            "metadata_failure": "Failed to export metadata:\n{error}",
            "invalid_polygon": "Selected object has invalid polygon.",
            "save_sprite": "Save Sprite",
            "png_filter": "PNG Image (*.png)",
            "sprite_success": "Sprite exported successfully.",
            "batch_directory": "Select Directory for Batch Export",
            "exporting_sprites": "Exporting sprites...",
            "batch_title": "Batch Export",
            "batch_summary": "Batch export completed.\nExported: {count}",
            "batch_errors": "\nErrors: {count} (check logs)",
            "atlas_directory": "Select Output Directory for Atlas",
            "preparing_atlas": "Preparing sprites for atlas...",
            "no_valid_sprites": "No valid sprites found to build atlas.",
            "packing_atlas": "Packing atlas (this may take a while)...",
            "atlas_success": "Atlas built successfully with {count} pages.",
            "atlas_failure": "Failed to build atlas:\n{error}",
            "save_scene_gltf": "Save Scene GLTF",
            "save_object_gltf": "Save Object GLTF",
            "gltf_filter": "GLTF Binary (*.glb)",
            "scene_success": "Scene exported to GLTF.",
            "object_success": "Object exported to GLTF.",
            "failure_status": "Export returned failure status.",
        },
        "pt": {
            "window_title": "Opções de Exportação",
            "group_2d": "Sprites 2D e Atlas",
            "single": "Exportar Sprite Selecionado",
            "batch": "Exportar Todos os Sprites em Lote",
            "atlas": "Criar Atlas de Texturas",
            "metadata_heading": "Metadados da Engine (JSON)",
            "target": "Destino:",
            "profile_generic": "JSON Genérico",
            "profile_godot": "Godot 4",
            "profile_unity": "Unity",
            "profile_phaser": "Phaser 3",
            "metadata_selected": "Exportar Metadados do Objeto Selecionado",
            "metadata_tooltip": (
                "Exporta metadados JSON do objeto 2D selecionado. "
                "As exportações de sprite, atlas e GLTF não são alteradas."
            ),
            "group_3d": "Modelos 3D (GLTF)",
            "gltf_scene": "Exportar Cena Completa para GLTF",
            "gltf_object": "Exportar Objeto Selecionado para GLTF",
            "close": "Fechar",
            "module_sprite_missing": "Módulo sprite_exporter ausente",
            "module_atlas_missing": "Módulo atlas_exporter ausente",
            "module_json_missing": "Módulo json_exporter ausente",
            "module_gltf_missing": "Módulo gltf_exporter ausente",
            "error": "Erro",
            "info": "Informação",
            "success": "Sucesso",
            "warning": "Aviso",
            "failed": "Falha",
            "cancel": "Cancelar",
            "no_image": "Nenhuma imagem foi carregada na cena.",
            "no_objects": "A cena não possui objetos para exportar.",
            "no_selection": "Nenhum objeto está selecionado.",
            "save_metadata": "Salvar Metadados do Objeto",
            "json_metadata_filter": "Metadados JSON (*.json)",
            "metadata_success": "Metadados {profile} exportados com sucesso.\n{path}",
            "metadata_failure": "Falha ao exportar metadados:\n{error}",
            "invalid_polygon": "O objeto selecionado possui um polígono inválido.",
            "save_sprite": "Salvar Sprite",
            "png_filter": "Imagem PNG (*.png)",
            "sprite_success": "Sprite exportado com sucesso.",
            "batch_directory": "Selecionar Pasta para Exportação em Lote",
            "exporting_sprites": "Exportando sprites...",
            "batch_title": "Exportação em Lote",
            "batch_summary": "Exportação em lote concluída.\nExportados: {count}",
            "batch_errors": "\nErros: {count} (consulte os logs)",
            "atlas_directory": "Selecionar Pasta de Saída do Atlas",
            "preparing_atlas": "Preparando sprites para o atlas...",
            "no_valid_sprites": "Nenhum sprite válido foi encontrado para criar o atlas.",
            "packing_atlas": "Montando o atlas (isso pode levar algum tempo)...",
            "atlas_success": "Atlas criado com sucesso em {count} página(s).",
            "atlas_failure": "Falha ao criar o atlas:\n{error}",
            "save_scene_gltf": "Salvar Cena GLTF",
            "save_object_gltf": "Salvar Objeto GLTF",
            "gltf_filter": "Binário GLTF (*.glb)",
            "scene_success": "Cena exportada para GLTF.",
            "object_success": "Objeto exportado para GLTF.",
            "failure_status": "O exportador retornou status de falha.",
        },
    }

    def __init__(self, scene, parent=None, lang: Optional[str] = None):
        super().__init__(parent)
        self.scene = scene
        inherited_lang = getattr(parent, "current_lang", "en")
        self.current_lang = lang if lang in self.TRANSLATIONS else inherited_lang
        if self.current_lang not in self.TRANSLATIONS:
            self.current_lang = "en"
        self.setMinimumWidth(470)
        self._setup_ui()
        self.update_language(self.current_lang)

    @property
    def t(self):
        return self.TRANSLATIONS[self.current_lang]

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.group_2d = QGroupBox()
        self.group_2d.setObjectName("export_group_2d")
        self.group_2d.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        l_2d = QVBoxLayout()
        l_2d.setContentsMargins(12, 18, 12, 12)
        l_2d.setSpacing(8)

        self.btn_single = QPushButton()
        self.btn_batch = QPushButton()
        self.btn_atlas = QPushButton()

        self.metadata_heading_label = QLabel()
        metadata_row = QHBoxLayout()
        self.metadata_target_label = QLabel()
        metadata_row.addWidget(self.metadata_target_label)

        self.metadata_profile = QComboBox()
        self.metadata_profile.setObjectName("metadata_profile")
        for profile_id in ("generic", "godot", "unity", "phaser"):
            self.metadata_profile.addItem("", profile_id)
        metadata_row.addWidget(self.metadata_profile, 1)

        self.btn_metadata_selected = QPushButton()
        self.btn_metadata_selected.setObjectName("btn_metadata_selected")

        l_2d.addWidget(self.btn_single)
        l_2d.addWidget(self.btn_batch)
        l_2d.addWidget(self.btn_atlas)
        l_2d.addWidget(self.metadata_heading_label)
        l_2d.addLayout(metadata_row)
        l_2d.addWidget(self.btn_metadata_selected)
        self.group_2d.setLayout(l_2d)
        layout.addWidget(self.group_2d)

        self.group_3d = QGroupBox()
        self.group_3d.setObjectName("export_group_3d")
        self.group_3d.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        l_3d = QVBoxLayout()
        l_3d.setContentsMargins(12, 18, 12, 12)
        l_3d.setSpacing(8)
        self.btn_gltf_scene = QPushButton()
        self.btn_gltf_object = QPushButton()
        l_3d.addWidget(self.btn_gltf_scene)
        l_3d.addWidget(self.btn_gltf_object)
        self.group_3d.setLayout(l_3d)
        layout.addWidget(self.group_3d)

        self.btn_close = QPushButton()
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)
        self.setLayout(layout)
        self._apply_compact_widget_policies()

        self.btn_single.clicked.connect(self.export_single)
        self.btn_batch.clicked.connect(self.export_batch)
        self.btn_atlas.clicked.connect(self.export_atlas)
        self.btn_metadata_selected.clicked.connect(self.export_selected_metadata)
        self.btn_gltf_scene.clicked.connect(self.export_gltf_scene)
        self.btn_gltf_object.clicked.connect(self.export_gltf_object)

        if not HAS_SPRITE_EXPORTER:
            self.btn_single.setEnabled(False)
            self.btn_batch.setEnabled(False)
        if not HAS_ATLAS_EXPORTER:
            self.btn_atlas.setEnabled(False)
        if not HAS_METADATA_EXPORTER:
            self.metadata_profile.setEnabled(False)
            self.btn_metadata_selected.setEnabled(False)
        if not HAS_GLTF_EXPORTER:
            self.btn_gltf_scene.setEnabled(False)
            self.btn_gltf_object.setEnabled(False)

    def update_language(self, lang: str):
        self.current_lang = lang if lang in self.TRANSLATIONS else "en"
        t = self.t
        self.setWindowTitle(t["window_title"])
        self.group_2d.setTitle(t["group_2d"])
        self.btn_single.setText(t["single"])
        self.btn_batch.setText(t["batch"])
        self.btn_atlas.setText(t["atlas"])
        self.metadata_heading_label.setText(t["metadata_heading"])
        self.metadata_target_label.setText(t["target"])
        profile_keys = ("profile_generic", "profile_godot", "profile_unity", "profile_phaser")
        for index, key in enumerate(profile_keys):
            self.metadata_profile.setItemText(index, t[key])
        self.btn_metadata_selected.setText(t["metadata_selected"])
        self.btn_metadata_selected.setToolTip(t["metadata_tooltip"])
        self.group_3d.setTitle(t["group_3d"])
        self.btn_gltf_scene.setText(t["gltf_scene"])
        self.btn_gltf_object.setText(t["gltf_object"])
        self.btn_close.setText(t["close"])

        if not HAS_SPRITE_EXPORTER:
            self.btn_single.setToolTip(t["module_sprite_missing"])
            self.btn_batch.setToolTip(t["module_sprite_missing"])
        if not HAS_ATLAS_EXPORTER:
            self.btn_atlas.setToolTip(t["module_atlas_missing"])
        if not HAS_METADATA_EXPORTER:
            self.btn_metadata_selected.setToolTip(t["module_json_missing"])
        if not HAS_GLTF_EXPORTER:
            self.btn_gltf_scene.setToolTip(t["module_gltf_missing"])
            self.btn_gltf_object.setToolTip(t["module_gltf_missing"])

    def _apply_compact_widget_policies(self):
        for button in (
            self.btn_single,
            self.btn_batch,
            self.btn_atlas,
            self.btn_metadata_selected,
            self.btn_gltf_scene,
            self.btn_gltf_object,
            self.btn_close,
        ):
            button.setMinimumHeight(36)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.metadata_profile.setMinimumHeight(34)
        self.metadata_profile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _check_prerequisites(self, require_selection=False, require_image=True) -> bool:
        if require_image and self.scene.image is None:
            QMessageBox.critical(self, self.t["error"], self.t["no_image"])
            return False
        if not self.scene.objects:
            QMessageBox.information(self, self.t["info"], self.t["no_objects"])
            return False
        if require_selection and (
            not self.scene.selected_id or self.scene.selected_id not in self.scene.objects
        ):
            QMessageBox.information(self, self.t["info"], self.t["no_selection"])
            return False
        return True

    @staticmethod
    def _safe_filename(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._")
        return cleaned or "object"

    def selected_metadata_profile(self) -> str:
        return str(self.metadata_profile.currentData() or "generic")

    @staticmethod
    def _json_file_is_valid(path: str) -> bool:
        evidence = file_evidence(path)
        if not evidence["exists"] or evidence["size"] <= 0:
            return False
        with open(path, "r", encoding="utf-8") as handle:
            json.load(handle)
        return True

    @staticmethod
    def _glb_file_is_valid(path: str) -> bool:
        evidence = file_evidence(path)
        if not evidence["exists"] or evidence["size"] < 12:
            return False
        with open(path, "rb") as handle:
            header = handle.read(8)
        return header[:4] == b"glTF" and int.from_bytes(header[4:8], "little") == 2

    @staticmethod
    def _validation_file(name: str) -> Optional[str]:
        target = validation_output_path(name)
        return str(target) if target is not None else None

    @staticmethod
    def _validation_directory(name: str) -> Optional[str]:
        target = validation_output_path(name, directory=True)
        return str(target) if target is not None else None

    def export_selected_metadata(self):
        started_at = time.perf_counter()
        if not self._check_prerequisites(require_selection=True, require_image=False):
            record_validation_event(
                "export.metadata", "BLOCKED", duration_ms=elapsed_ms(started_at)
            )
            return

        obj_id = self.scene.selected_id
        profile = self.selected_metadata_profile()
        default_name = f"{self._safe_filename(obj_id)}-{profile}-metadata.json"
        path = ""
        valid_json = None
        destination_mode = "user-dialog"
        try:
            validation_path = self._validation_file(
                f"selected-{profile}-metadata.json"
            )
            if validation_path is not None:
                path = validation_path
                destination_mode = "validation-sandbox"
            else:
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    self.t["save_metadata"],
                    default_name,
                    self.t["json_metadata_filter"],
                )
            if not path:
                record_validation_event(
                    "export.metadata",
                    "CANCELLED",
                    duration_ms=elapsed_ms(started_at),
                    profile=profile,
                    destination_mode=destination_mode,
                )
                return
            if not path.lower().endswith(".json"):
                path += ".json"

            export_metadata(obj_id, self.scene, path, profile=profile)
            valid_json = self._json_file_is_valid(path)
            evidence = file_evidence(path)
            if not valid_json:
                raise OSError("Metadata export postcondition failed")
            record_validation_event(
                "export.metadata",
                "SUCCESS",
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(obj_id),
                profile=profile,
                valid_json=valid_json,
                destination_mode=destination_mode,
                **evidence,
            )
            QMessageBox.information(
                self,
                self.t["success"],
                self.t["metadata_success"].format(
                    profile=self.metadata_profile.currentText(), path=path
                ),
            )
        except Exception as exc:
            logger.error(
                "Metadata export failed for %s with profile %s: %s",
                obj_id,
                profile,
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "export.metadata",
                exc,
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(obj_id),
                profile=profile,
                valid_json=valid_json,
                destination_mode=destination_mode,
                **file_evidence(path),
            )
            QMessageBox.critical(
                self, self.t["error"], self.t["metadata_failure"].format(error=exc)
            )

    def export_single(self):
        started_at = time.perf_counter()
        if not self._check_prerequisites(require_selection=True):
            record_validation_event(
                "export.sprite", "BLOCKED", duration_ms=elapsed_ms(started_at)
            )
            return

        obj_id = self.scene.selected_id
        obj = self.scene.objects[obj_id]
        if not obj.polygon or len(obj.polygon) < 3:
            record_validation_event(
                "export.sprite",
                "BLOCKED",
                duration_ms=elapsed_ms(started_at),
                reason="invalid-polygon",
            )
            QMessageBox.critical(self, self.t["error"], self.t["invalid_polygon"])
            return

        path = ""
        valid_output = None
        destination_mode = "user-dialog"
        try:
            validation_path = self._validation_file("selected-sprite.png")
            if validation_path is not None:
                path = validation_path
                destination_mode = "validation-sandbox"
            else:
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    self.t["save_sprite"],
                    f"{obj_id}.png",
                    self.t["png_filter"],
                )
            if not path:
                record_validation_event(
                    "export.sprite",
                    "CANCELLED",
                    duration_ms=elapsed_ms(started_at),
                    destination_mode=destination_mode,
                )
                return

            logger.info("Exporting sprite for %s", obj_id)
            img = extract_masked_sprite(self.scene.image, obj.polygon, padding=4)
            save_sprite(img, path)
            evidence = file_evidence(path)
            valid_output = bool(evidence["exists"] and evidence["size"] > 0)
            if not valid_output:
                raise OSError("Sprite export postcondition failed")
            record_validation_event(
                "export.sprite",
                "SUCCESS",
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(obj_id),
                width=int(img.width),
                height=int(img.height),
                destination_mode=destination_mode,
                **evidence,
            )
            QMessageBox.information(self, self.t["success"], self.t["sprite_success"])
        except Exception as exc:
            logger.error(
                "Export failed: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "export.sprite",
                exc,
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(obj_id),
                valid_output=valid_output,
                destination_mode=destination_mode,
                **file_evidence(path),
            )
            QMessageBox.critical(self, self.t["error"], str(exc))

    def export_batch(self):
        started_at = time.perf_counter()
        if not self._check_prerequisites():
            record_validation_event("export.sprite.batch", "BLOCKED", duration_ms=elapsed_ms(started_at))
            return
        dir_path = QFileDialog.getExistingDirectory(self, self.t["batch_directory"])
        if not dir_path:
            record_validation_event("export.sprite.batch", "CANCELLED", duration_ms=elapsed_ms(started_at))
            return
        objects = list(self.scene.objects.items())
        total = len(objects)
        progress = QProgressDialog(
            self.t["exporting_sprites"], self.t["cancel"], 0, total, self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        count = 0
        errors = 0
        cancelled = False
        for index, (object_id, obj) in enumerate(objects):
            if progress.wasCanceled():
                cancelled = True
                break
            progress.setValue(index)
            if not obj.polygon or len(obj.polygon) < 3:
                continue
            try:
                img = extract_masked_sprite(self.scene.image, obj.polygon, padding=4)
                output = os.path.join(dir_path, f"{object_id}.png")
                save_sprite(img, output)
                if file_evidence(output)["exists"]:
                    count += 1
                else:
                    errors += 1
            except Exception as exc:
                logger.error("Failed to export %s: %s", object_id, exc, exc_info=True)
                errors += 1
        progress.setValue(total)
        status = "CANCELLED" if cancelled else ("SUCCESS" if count > 0 and errors == 0 else "FAILURE")
        record_validation_event(
            "export.sprite.batch",
            status,
            duration_ms=elapsed_ms(started_at),
            requested=total,
            exported=count,
            errors=errors,
        )
        message = self.t["batch_summary"].format(count=count)
        if errors:
            message += self.t["batch_errors"].format(count=errors)
        QMessageBox.information(self, self.t["batch_title"], message)

    def export_atlas(self):
        started_at = time.perf_counter()
        if not self._check_prerequisites():
            record_validation_event(
                "export.atlas", "BLOCKED", duration_ms=elapsed_ms(started_at)
            )
            return

        dir_path = ""
        destination_mode = "user-dialog"
        progress = None
        items = []
        results = []
        extraction_errors = 0
        output_count = 0
        valid_outputs = None
        try:
            validation_path = self._validation_directory("atlas")
            if validation_path is not None:
                dir_path = validation_path
                destination_mode = "validation-sandbox"
            else:
                dir_path = QFileDialog.getExistingDirectory(
                    self, self.t["atlas_directory"]
                )
            if not dir_path:
                record_validation_event(
                    "export.atlas",
                    "CANCELLED",
                    duration_ms=elapsed_ms(started_at),
                    destination_mode=destination_mode,
                )
                return

            objects = list(self.scene.objects.items())
            total = len(objects)
            progress = QProgressDialog(
                self.t["preparing_atlas"], self.t["cancel"], 0, total, self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            for index, (object_id, obj) in enumerate(objects):
                if progress.wasCanceled():
                    progress.close()
                    record_validation_event(
                        "export.atlas",
                        "CANCELLED",
                        duration_ms=elapsed_ms(started_at),
                        destination_mode=destination_mode,
                    )
                    return
                progress.setValue(index)
                if not obj.polygon or len(obj.polygon) < 3:
                    continue
                try:
                    img = extract_masked_sprite(
                        self.scene.image, obj.polygon, padding=4
                    )
                    items.append((object_id, img))
                except Exception as exc:
                    extraction_errors += 1
                    logger.error(
                        "Failed to extract %s: %s",
                        object_id,
                        exc,
                        exc_info=True,
                    )

            if not items:
                progress.close()
                record_validation_event(
                    "export.atlas",
                    "BLOCKED",
                    duration_ms=elapsed_ms(started_at),
                    reason="no-valid-sprites",
                    extraction_errors=extraction_errors,
                    destination_mode=destination_mode,
                )
                QMessageBox.warning(
                    self, self.t["warning"], self.t["no_valid_sprites"]
                )
                return

            progress.setLabelText(self.t["packing_atlas"])
            progress.setRange(0, 0)
            results = build_atlas(items, dir_path, base_name="atlas")
            progress.close()
            valid_outputs = bool(results) and extraction_errors == 0
            for result in results:
                atlas_path = result.get("atlas_path")
                json_path = result.get("json_path")
                atlas_ok = file_evidence(atlas_path)["size"] > 0
                json_ok = self._json_file_is_valid(json_path)
                valid_outputs = valid_outputs and atlas_ok and json_ok
                output_count += int(atlas_ok) + int(json_ok)
            if not valid_outputs:
                raise OSError("Atlas export postcondition failed")
            record_validation_event(
                "export.atlas",
                "SUCCESS",
                duration_ms=elapsed_ms(started_at),
                atlas_count=len(results),
                output_file_count=output_count,
                item_count=len(items),
                extraction_errors=extraction_errors,
                destination_mode=destination_mode,
            )
            QMessageBox.information(
                self,
                self.t["success"],
                self.t["atlas_success"].format(count=len(results)),
            )
        except Exception as exc:
            if progress is not None:
                progress.close()
            logger.error(
                "Atlas build failed: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "export.atlas",
                exc,
                duration_ms=elapsed_ms(started_at),
                item_count=len(items),
                atlas_count=len(results),
                output_file_count=output_count,
                extraction_errors=extraction_errors,
                valid_outputs=valid_outputs,
                destination_mode=destination_mode,
            )
            QMessageBox.critical(
                self, self.t["error"], self.t["atlas_failure"].format(error=exc)
            )

    def export_gltf_scene(self):
        started_at = time.perf_counter()
        if not self._check_prerequisites():
            record_validation_event(
                "export.gltf.scene",
                "BLOCKED",
                duration_ms=elapsed_ms(started_at),
            )
            return

        path = ""
        valid_glb = None
        destination_mode = "user-dialog"
        try:
            validation_path = self._validation_file("scene.glb")
            if validation_path is not None:
                path = validation_path
                destination_mode = "validation-sandbox"
            else:
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    self.t["save_scene_gltf"],
                    "scene.glb",
                    self.t["gltf_filter"],
                )
            if not path:
                record_validation_event(
                    "export.gltf.scene",
                    "CANCELLED",
                    duration_ms=elapsed_ms(started_at),
                    destination_mode=destination_mode,
                )
                return

            success = export_scene_to_gltf(self.scene, path)
            valid_glb = bool(success and self._glb_file_is_valid(path))
            if not valid_glb:
                raise OSError("Scene GLB export postcondition failed")
            record_validation_event(
                "export.gltf.scene",
                "SUCCESS",
                duration_ms=elapsed_ms(started_at),
                object_count=len(self.scene.objects),
                valid_glb=valid_glb,
                destination_mode=destination_mode,
                **file_evidence(path),
            )
            QMessageBox.information(
                self, self.t["success"], self.t["scene_success"]
            )
        except Exception as exc:
            logger.error(
                "GLTF Scene export failed: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "export.gltf.scene",
                exc,
                duration_ms=elapsed_ms(started_at),
                valid_glb=valid_glb,
                destination_mode=destination_mode,
                **file_evidence(path),
            )
            QMessageBox.critical(self, self.t["error"], str(exc))

    def export_gltf_object(self):
        started_at = time.perf_counter()
        if not self._check_prerequisites(require_selection=True):
            record_validation_event(
                "export.gltf.object",
                "BLOCKED",
                duration_ms=elapsed_ms(started_at),
            )
            return

        obj_id = self.scene.selected_id
        path = ""
        valid_glb = None
        destination_mode = "user-dialog"
        try:
            validation_path = self._validation_file("selected-object.glb")
            if validation_path is not None:
                path = validation_path
                destination_mode = "validation-sandbox"
            else:
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    self.t["save_object_gltf"],
                    f"{obj_id}.glb",
                    self.t["gltf_filter"],
                )
            if not path:
                record_validation_event(
                    "export.gltf.object",
                    "CANCELLED",
                    duration_ms=elapsed_ms(started_at),
                    destination_mode=destination_mode,
                )
                return

            success = export_object_to_gltf(obj_id, self.scene, path)
            valid_glb = bool(success and self._glb_file_is_valid(path))
            if not valid_glb:
                raise OSError("Object GLB export postcondition failed")
            record_validation_event(
                "export.gltf.object",
                "SUCCESS",
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(obj_id),
                valid_glb=valid_glb,
                destination_mode=destination_mode,
                **file_evidence(path),
            )
            QMessageBox.information(
                self, self.t["success"], self.t["object_success"]
            )
        except Exception as exc:
            logger.error(
                "GLTF Object export failed: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "export.gltf.object",
                exc,
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(obj_id),
                valid_glb=valid_glb,
                destination_mode=destination_mode,
                **file_evidence(path),
            )
            QMessageBox.critical(self, self.t["error"], str(exc))

