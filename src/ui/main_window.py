# src/ui/main_window.py
import hashlib
import json
import os
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
)

from src.core.app_identity import build_window_title
from src.core.logger import logger
from src.core.validation_events import (
    elapsed_ms,
    record_validation_event,
    record_validation_exception,
)
from src.exporters.collision_exporter import (
    export_collision_document,
    save_collision_text,
)
from src.exporters.json_exporter import save_json_metadata
from src.persistence import PROJECT_FILE_EXTENSION, build_project_document

# Imports de Lógica e Física
from src.physics.physics_manager import PhysicsManager
from src.ui.canvas_view import CanvasView
from src.ui.collision_overlay import CollisionOverlay
from src.ui.collision_panel import CollisionPanel
from src.ui.export_dialog import ExportDialog
from src.ui.groups_panel import GroupsPanel
from src.ui.layers_panel import LayersPanel
from src.ui.mask_viewer import MaskViewerDialog

# Imports dos componentes da UI
from src.ui.side_panel import SidePanel
from src.ui.tool_palette import ToolPalette


class MainWindow(QMainWindow):

    def _report_collision_export_error(self, exc):
        t = self.translations[self.current_lang]
        logger.error("Failed to export collision data: %s", exc, exc_info=True)
        QMessageBox.critical(
            self,
            t["error"],
            t["failed_export_collision"] + str(exc),
        )

    def _build_collision_document(self, *, results=None, statistics=None):
        try:
            return export_collision_document(
                self.scene,
                results=results,
                statistics=statistics,
            )
        except Exception as exc:
            self._report_collision_export_error(exc)
            return None

    def _save_collision_json(self, data, default_name="collisions.json"):
        t = self.translations[self.current_lang]
        path, _ = QFileDialog.getSaveFileName(
            self,
            t["export_collision_json_dialog"],
            default_name,
            t["json_files"],
        )
        if not path:
            return False

        try:
            save_json_metadata(data, path)
        except Exception as exc:
            self._report_collision_export_error(exc)
            return False

        QMessageBox.information(
            self,
            t["info"],
            t["export_collision_success"].format(path=path),
        )
        return True

    def export_collision_json(self):
        """Export collision shapes using the canonical versioned schema."""
        data = self._build_collision_document()
        if data is None:
            return False
        return self._save_collision_json(data)

    def export_collision_txt(self):
        """Export the text view derived from the canonical collision schema."""
        document = self._build_collision_document()
        if document is None:
            return False

        t = self.translations[self.current_lang]
        path, _ = QFileDialog.getSaveFileName(
            self,
            t["export_collision_txt_dialog"],
            "collisions.txt",
            t["text_files"],
        )
        if not path:
            return False

        try:
            save_collision_text(document, path)
        except Exception as exc:
            self._report_collision_export_error(exc)
            return False

        QMessageBox.information(
            self,
            t["info"],
            t["export_collision_success"].format(path=path),
        )
        return True

    def __init__(self, scene, config):
        super().__init__()
        self.scene = scene
        self.config = config
        self._last_folder = config.get("last_folder")
        self._current_tool = config.get("tool", "polygonal_lasso")
        self._mask_viewer_dialog = None
        self._project_path: Path | None = None
        self._clean_signature: str | None = None

        # Configuração da Janela Principal
        self.current_lang = "en"
        self._document_name = None
        self.setWindowTitle(build_window_title(self.current_lang))
        self.resize(1200, 800)

        # 1. Menu Bar (File, View, etc.)
        self._setup_menu_bar()

        # 2. Main Toolbar (Arquivo/Exportação)
        self.toolbar = QToolBar("Main")
        self.addToolBar(self.toolbar)

        self.act_open = self.open_image_action
        self.toolbar.addAction(self.open_project_action)
        self.toolbar.addAction(self.act_open)
        self.toolbar.addAction(self.save_project_action)

        self.act_export = QAction("Export...", self)
        self.act_export.triggered.connect(self.open_export)
        self.toolbar.addAction(self.act_export)

        # Adiciona menu de exportação de colisão
        export_menu = QMenu(self)
        self.act_export_collision_json = QAction("Export Collision (JSON)", self)
        self.act_export_collision_json.triggered.connect(self.export_collision_json)
        export_menu.addAction(self.act_export_collision_json)
        self.act_export_collision_txt = QAction("Export Collision (TXT)", self)
        self.act_export_collision_txt.triggered.connect(self.export_collision_txt)
        export_menu.addAction(self.act_export_collision_txt)
        self.export_collision_button = QPushButton("Export Collision", self)
        self.export_collision_button.setMenu(export_menu)
        self.toolbar.addWidget(self.export_collision_button)
        # 3. Componentes Centrais
        self.canvas = CanvasView(scene)
        self.tool_palette = ToolPalette(self.canvas)
        self.side_panel = SidePanel(scene, self.canvas)
        self.layers = LayersPanel(scene)
        self.groups = GroupsPanel(scene)

        # Disable tools until image is loaded
        self.tool_palette.setEnabled(False)
        self.side_panel.setEnabled(False)

        # 4. Configuração de Física
        self.physics_manager = PhysicsManager(grid_cell_size=64)
        self.collision_overlay = CollisionOverlay(scene)
        self.collision_panel = CollisionPanel(scene)

        # Conexão Física -> UI
        self.collision_panel.set_physics_manager(self.physics_manager)
        self.collision_panel.batch_test_requested.connect(self._on_collision_batch_test)
        self.collision_panel.export_collisions_requested.connect(
            self._on_collision_export
        )
        self.collision_panel.auto_generate_requested.connect(
            self._on_collision_auto_generate
        )

        # Adiciona Overlay ao Canvas
        self.canvas.set_collision_overlay(self.collision_overlay)

        # 5. NAVIGATION TOOLBAR
        # (Barra de Ferramentas de Navegação e Ações Rápidas)
        self.nav_toolbar = QToolBar("Navigation")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.nav_toolbar)

        # Botão: Ajustar à Tela
        self.act_fit = QAction("Fit View (F)", self)
        self.act_fit.triggered.connect(self.canvas.fit_to_window)
        self.nav_toolbar.addAction(self.act_fit)

        # Botão: Zoom 100%
        self.act_100 = QAction("1:1 Pixel", self)
        self.act_100.triggered.connect(lambda: self.canvas.set_zoom(1.0))
        self.nav_toolbar.addAction(self.act_100)

        self.nav_toolbar.addSeparator()

        # Barra de opções de Raio-X
        self.xray_toolbar = QToolBar("X-Ray Modes")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.xray_toolbar)

        self.act_lit = QAction("Lit", self)
        self.act_lit.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_LIT)
        )
        self.xray_toolbar.addAction(self.act_lit)

        self.act_xray1 = QAction("X-Ray 1", self)
        self.act_xray1.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_XRAY_1)
        )
        self.xray_toolbar.addAction(self.act_xray1)

        self.act_xray2 = QAction("X-Ray 2", self)
        self.act_xray2.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_XRAY_2)
        )
        self.xray_toolbar.addAction(self.act_xray2)

        self.act_xray3 = QAction("X-Ray 3", self)
        self.act_xray3.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_XRAY_3)
        )
        self.xray_toolbar.addAction(self.act_xray3)

        # Botão: Focar Seleção (Leva a câmera ao objeto selecionado)
        self.focus_button = QPushButton("Focus Selected", self)
        self.focus_button.setFlat(True)
        self.focus_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.focus_button.setStyleSheet(
            "QPushButton:pressed { background-color: transparent; " "border: none; }"
        )
        self.focus_button.clicked.connect(self._focus_selected)
        self.nav_toolbar.addWidget(self.focus_button)

        self.nav_toolbar.addSeparator()

        # Botão: Limpar Tudo (Com Undo)
        self.act_clean = QAction("🗑️ Clean All", self)
        self.act_clean.triggered.connect(self.canvas.clean_all)
        self.nav_toolbar.addAction(self.act_clean)

        self.nav_toolbar.addSeparator()

        self.language_button = QPushButton("Language", self)
        self.nav_toolbar.addWidget(self.language_button)
        self.language_button.clicked.connect(self.show_language_menu)

        # 6. Layout Principal (QSplitter para painéis redimensionáveis)
        # Esquerda: Ferramentas | Centro: Canvas | Direita: Propriedades/Física
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tool_palette)
        splitter.addWidget(self.canvas)

        # Painel Direito (Dividido Verticalmente)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.side_panel)
        right_splitter.addWidget(self.layers)
        right_splitter.addWidget(self.groups)

        splitter.addWidget(right_splitter)
        splitter.addWidget(self.collision_panel)

        # Define tamanhos iniciais para boa ergonomia
        # Collision panel começa colapsado (tamanho 0)
        splitter.setSizes([self.tool_palette.recommended_width(), 800, 250, 0])
        splitter.setStretchFactor(1, 1)  # Canvas estica

        self.setCentralWidget(splitter)

        # 7. Atalhos Globais
        self._setup_shortcuts()

        self.translations = {
            "en": {
                "window_title": build_window_title("en"),
                "file_menu": "File",
                "open_project": "Open Project...",
                "save_project": "Save",
                "save_project_as": "Save As...",
                "close_application": "Exit",
                "project_files": "NeoEng-D-Trace Projects (*.ndtproj)",
                "open_project_dialog": "Open Project",
                "save_project_dialog": "Save Project",
                "untitled_project": "Untitled",
                "unsaved_title": "Unsaved changes",
                "unsaved_message": "Save changes to the current project?",
                "project_saved": "Project saved successfully.",
                "failed_open_project": "Failed to open project: ",
                "failed_save_project": "Failed to save project: ",
                "project_warnings_title": "Project opened with warnings",
                "project_image_missing": "Referenced image was not found: {path}",
                "project_image_unreadable": (
                    "Referenced image could not be read: {path}"
                ),
                "project_image_hash_mismatch": (
                    "Referenced image differs from the saved SHA-256: {path}"
                ),
                "project_image_hash_unavailable": (
                    "Referenced image was loaded, but its SHA-256 could not be "
                    "verified: {path}"
                ),
                "open_image": "Open Image",
                "open_image_dialog": "Open Image",
                "image_files": "Images (*.png *.jpg *.jpeg *.bmp *.tiff)",
                "export": "Export...",
                "export_collision": "Export Collision",
                "export_collision_json": "Export Collision (JSON)",
                "export_collision_txt": "Export Collision (TXT)",
                "export_collision_json_dialog": "Export Collision JSON",
                "export_collision_txt_dialog": "Export Collision TXT",
                "export_collision_success": "Collision data exported to {path}",
                "failed_export_collision": "Failed to export collision data: ",
                "json_files": "JSON Files (*.json)",
                "text_files": "Text Files (*.txt)",
                "fit_view": "Fit View (F)",
                "pixel_1": "1:1 Pixel",
                "lit": "Lit",
                "xray_1": "X-Ray 1",
                "xray_2": "X-Ray 2",
                "xray_3": "X-Ray 3",
                "focus_selected": "Focus Selected",
                "clean_all": "🗑️ Clean All",
                "edit_menu": "Edit",
                "undo": "Undo",
                "redo": "Redo",
                "view_menu": "View",
                "mask_viewer": "Mask Viewer (Auto-Detect)",
                "collision_overlay": "Collision Overlay",
                "info": "Info",
                "select_object": "Select an object in the list first.",
                "error": "Error",
                "failed_open_image": "Failed to open image: ",
                "failed_mask_viewer": "Failed to open Mask Viewer: ",
                "language": "Language",
                "english": "English",
                "portuguese": "Portuguese",
            },
            "pt": {
                "window_title": build_window_title("pt"),
                "file_menu": "Arquivo",
                "open_project": "Abrir Projeto...",
                "save_project": "Salvar",
                "save_project_as": "Salvar Como...",
                "close_application": "Sair",
                "project_files": "Projetos NeoEng-D-Trace (*.ndtproj)",
                "open_project_dialog": "Abrir Projeto",
                "save_project_dialog": "Salvar Projeto",
                "untitled_project": "Sem título",
                "unsaved_title": "Alterações não salvas",
                "unsaved_message": "Deseja salvar as alterações do projeto atual?",
                "project_saved": "Projeto salvo com sucesso.",
                "failed_open_project": "Falha ao abrir projeto: ",
                "failed_save_project": "Falha ao salvar projeto: ",
                "project_warnings_title": "Projeto aberto com avisos",
                "project_image_missing": (
                    "A imagem referenciada não foi encontrada: {path}"
                ),
                "project_image_unreadable": (
                    "A imagem referenciada não pôde ser lida: {path}"
                ),
                "project_image_hash_mismatch": (
                    "A imagem referenciada difere do SHA-256 salvo: {path}"
                ),
                "project_image_hash_unavailable": (
                    "A imagem referenciada foi carregada, mas seu SHA-256 não "
                    "pôde ser verificado: {path}"
                ),
                "open_image": "Abrir Imagem",
                "open_image_dialog": "Abrir Imagem",
                "image_files": "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff)",
                "export": "Exportar...",
                "export_collision": "Exportar Colisão",
                "export_collision_json": "Exportar Colisão (JSON)",
                "export_collision_txt": "Exportar Colisão (TXT)",
                "export_collision_json_dialog": "Exportar Colisão em JSON",
                "export_collision_txt_dialog": "Exportar Colisão em TXT",
                "export_collision_success": "Dados de colisão exportados para {path}",
                "failed_export_collision": "Falha ao exportar dados de colisão: ",
                "json_files": "Arquivos JSON (*.json)",
                "text_files": "Arquivos de Texto (*.txt)",
                "fit_view": "Ajustar Visão (F)",
                "pixel_1": "Pixel 1:1",
                "lit": "Iluminado",
                "xray_1": "Raio-X 1",
                "xray_2": "Raio-X 2",
                "xray_3": "Raio-X 3",
                "focus_selected": "Focar Selecionado",
                "clean_all": "🗑️ Limpar Tudo",
                "edit_menu": "Editar",
                "undo": "Desfazer",
                "redo": "Refazer",
                "view_menu": "Visualizar",
                "mask_viewer": "Visualizador de Máscara (Auto-Detect)",
                "collision_overlay": "Sobreposição de Colisão",
                "info": "Info",
                "select_object": "Selecione um objeto na lista primeiro.",
                "error": "Erro",
                "failed_open_image": "Falha ao abrir imagem: ",
                "failed_mask_viewer": "Falha ao abrir " "Visualizador de Máscara: ",
                "language": "Idioma",
                "english": "Inglês",
                "portuguese": "Português",
            },
        }
        self.update_language()
        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self._on_scene_changed)
        self._connect_command_history()
        self._update_undo_redo_actions()
        self._mark_document_clean()

    def _focus_selected(self):
        """Foca a câmera no objeto selecionado na lista lateral."""
        if hasattr(self.side_panel, "_get_selected_obj"):
            oid, _ = self.side_panel._get_selected_obj()
            if oid:
                self.canvas.center_on_object(oid)
            else:
                QMessageBox.information(
                    self,
                    self.translations[self.current_lang]["info"],
                    self.translations[self.current_lang]["select_object"],
                )

    def _setup_shortcuts(self):
        # View Shortcuts
        QShortcut(QKeySequence("F"), self, self.canvas.fit_to_window)
        QShortcut(QKeySequence("X"), self, self.canvas.toggle_xray)
        QShortcut(QKeySequence("A"), self, lambda: self.canvas.set_view_mode(0))

        # Tool Shortcuts (1-6)
        QShortcut(
            QKeySequence("1"),
            self,
            lambda: self._select_tool("polygonal_lasso"),
        )
        QShortcut(
            QKeySequence("2"),
            self,
            lambda: self._select_tool("lasso_tool"),
        )
        QShortcut(
            QKeySequence("3"),
            self,
            lambda: self._select_tool("rect_selection"),
        )
        QShortcut(
            QKeySequence("4"),
            self,
            lambda: self._select_tool("ellipse_selection"),
        )
        QShortcut(
            QKeySequence("5"),
            self,
            lambda: self._select_tool("pen_tool"),
        )
        QShortcut(
            QKeySequence("6"),
            self,
            lambda: self._select_tool("magnetic_lasso"),
        )

        # Undo/Redo Shortcuts
        # Nota: Mantemos isso para garantir o funcionamento do atalho,
        # mesmo que também exista no menu.
        QShortcut(QKeySequence.StandardKey.Undo, self, self._undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self._redo)

    def _connect_command_history(self) -> None:
        manager = getattr(self.scene, "cmd", None)
        if manager is not None and hasattr(manager, "subscribe"):
            manager.subscribe(self._update_undo_redo_actions)

    def _update_undo_redo_actions(self) -> None:
        manager = getattr(self.scene, "cmd", None)
        can_undo = bool(manager is not None and getattr(manager, "can_undo", False))
        can_redo = bool(manager is not None and getattr(manager, "can_redo", False))
        self.undo_action.setEnabled(can_undo)
        self.redo_action.setEnabled(can_redo)

    def _undo(self):
        if self.canvas.request_tool_undo():
            self.canvas.update()
            self._update_undo_redo_actions()
            return None
        result = None
        if self.scene.cmd:
            result = self.scene.cmd.undo(self.scene)
        self.canvas.update()
        self.side_panel.refresh()
        self._on_scene_changed()
        self._update_undo_redo_actions()
        return result

    def _redo(self):
        if self.canvas.request_tool_redo():
            self.canvas.update()
            self._update_undo_redo_actions()
            return None
        result = None
        if self.scene.cmd:
            result = self.scene.cmd.redo(self.scene)
        self.canvas.update()
        self.side_panel.refresh()
        self._on_scene_changed()
        self._update_undo_redo_actions()
        return result

    def _select_tool(self, tool_name):
        if hasattr(self.tool_palette, "select_tool_by_name"):
            self.tool_palette.select_tool_by_name(tool_name)

    def _setup_menu_bar(self):
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu("File")

        self.open_project_action = QAction("Open Project...", self)
        self.open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_project_action.triggered.connect(self.open_project)
        self.file_menu.addAction(self.open_project_action)

        self.open_image_action = QAction("Open Image", self)
        self.open_image_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.open_image_action.triggered.connect(self.open_image)
        self.file_menu.addAction(self.open_image_action)

        self.file_menu.addSeparator()

        self.save_project_action = QAction("Save", self)
        self.save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_project_action.triggered.connect(self.save_project)
        self.file_menu.addAction(self.save_project_action)

        self.save_project_as_action = QAction("Save As...", self)
        self.save_project_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_project_as_action.triggered.connect(self.save_project_as)
        self.file_menu.addAction(self.save_project_as_action)

        self.file_menu.addSeparator()

        self.close_application_action = QAction("Exit", self)
        self.close_application_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.close_application_action.triggered.connect(self.close)
        self.file_menu.addAction(self.close_application_action)

        # --- Menu Editar (ADICIONADO) ---
        # Resolve o problema de falta de "self.undo_action"
        self.edit_menu = menubar.addMenu("Edit")

        self.undo_action = QAction("Undo", self)
        # Conecta diretamente à função _undo já existente e correta
        self.undo_action.triggered.connect(self._undo)
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        # Conecta diretamente à função _redo já existente e correta
        self.redo_action.triggered.connect(self._redo)
        self.edit_menu.addAction(self.redo_action)

        # --- Menu View (MODIFICADO para usar referências) ---
        self.view_menu = menubar.addMenu("View")

        self.mask_viewer_action = QAction("Mask Viewer (Auto-Detect)", self)
        self.mask_viewer_action.triggered.connect(self.open_mask_viewer)
        self.view_menu.addAction(self.mask_viewer_action)

        self.collision_overlay_action = QAction("Collision Overlay", self)
        self.collision_overlay_action.setCheckable(True)
        self.collision_overlay_action.setChecked(False)
        self.collision_overlay_action.triggered.connect(self._toggle_collision_overlay)
        self.view_menu.addAction(self.collision_overlay_action)

    def set_language(self, lang):
        started_at = time.perf_counter()
        previous = self.current_lang
        requested = lang
        try:
            self.current_lang = lang if lang in self.translations else "en"
            self.update_language()
            expected_title = self._expected_window_title()
            applied = (
                self.current_lang in self.translations
                and self.windowTitle() == expected_title
            )
            record_validation_event(
                "language.changed",
                "SUCCESS" if applied else "FAILURE",
                duration_ms=elapsed_ms(started_at),
                previous=previous,
                requested=requested,
                applied=self.current_lang,
                title_updated=applied,
            )
        except Exception as exc:
            record_validation_exception(
                "language.changed",
                exc,
                duration_ms=elapsed_ms(started_at),
                previous=previous,
                requested=requested,
            )
            raise

    def update_language(self):
        if self.current_lang not in self.translations:
            self.current_lang = "en"
        t = self.translations[self.current_lang]
        self._refresh_window_title()

        self.file_menu.setTitle(t["file_menu"])
        self.open_project_action.setText(t["open_project"])
        self.open_image_action.setText(t["open_image"])
        self.save_project_action.setText(t["save_project"])
        self.save_project_as_action.setText(t["save_project_as"])
        self.close_application_action.setText(t["close_application"])

        self.act_open.setText(t["open_image"])
        self.act_export.setText(t["export"])
        self.act_export_collision_json.setText(t["export_collision_json"])
        self.act_export_collision_txt.setText(t["export_collision_txt"])
        self.export_collision_button.setText(t["export_collision"])

        self.act_fit.setText(t["fit_view"])
        self.act_100.setText(t["pixel_1"])
        self.act_lit.setText(t["lit"])
        self.act_xray1.setText(t["xray_1"])
        self.act_xray2.setText(t["xray_2"])
        self.act_xray3.setText(t["xray_3"])
        self.act_clean.setText(t["clean_all"])
        self.focus_button.setText(t["focus_selected"])
        self.language_button.setText(t["language"])
        if hasattr(self, "act_english"):
            self.act_english.setText(t["english"])
        if hasattr(self, "act_portuguese"):
            self.act_portuguese.setText(t["portuguese"])

        # --- ATUALIZAÇÃO DO MENU (CORRIGIDA) ---
        # Edit Menu
        self.edit_menu.setTitle(t["edit_menu"])
        self.undo_action.setText(t["undo"])
        self.redo_action.setText(t["redo"])

        # View Menu
        self.view_menu.setTitle(t["view_menu"])
        self.mask_viewer_action.setText(t["mask_viewer"])
        self.collision_overlay_action.setText(t["collision_overlay"])

        # Update other components
        if hasattr(self.side_panel, "update_language"):
            self.side_panel.update_language(self.current_lang)
        if hasattr(self.tool_palette, "update_language"):
            self.tool_palette.update_language(self.current_lang)
        if hasattr(self.groups, "update_language"):
            self.groups.update_language(self.current_lang)
        if hasattr(self.canvas, "update_language"):
            self.canvas.update_language(self.current_lang)
        if (
            hasattr(self.canvas, "_tool")
            and self.canvas._tool
            and hasattr(self.canvas._tool, "update_language")
        ):
            self.canvas._tool.update_language(self.current_lang)
        if self._mask_viewer_dialog is not None and hasattr(
            self._mask_viewer_dialog, "update_language"
        ):
            self._mask_viewer_dialog.update_language(self.current_lang)

    def show_language_menu(self):
        menu = QMenu(self)
        self.act_english = menu.addAction(
            self.translations[self.current_lang]["english"]
        )
        self.act_portuguese = menu.addAction(
            self.translations[self.current_lang]["portuguese"]
        )
        self.act_english.triggered.connect(lambda: self.set_language("en"))
        self.act_portuguese.triggered.connect(lambda: self.set_language("pt"))
        menu.exec(
            self.language_button.mapToGlobal(self.language_button.rect().bottomLeft())
        )

    def set_last_folder(self, folder):
        self._last_folder = folder

    def select_tool(self, tool_name):
        self._current_tool = tool_name

    def _signature_path_hint(self) -> Path:
        if self._project_path is not None:
            return self._project_path
        image_path = getattr(self.scene, "image_path", None)
        if image_path:
            candidate = Path(os.fsdecode(image_path))
            if candidate.is_absolute():
                return candidate.parent / f"untitled{PROJECT_FILE_EXTENSION}"
        return Path.cwd() / f"untitled{PROJECT_FILE_EXTENSION}"

    def _compute_document_signature(self) -> str:
        document = build_project_document(self.scene, self._signature_path_hint())
        payload = json.dumps(
            document.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def is_document_modified(self) -> bool:
        if self._clean_signature is None:
            return bool(
                self._document_name
                or getattr(self.scene, "image_path", None)
                or self.scene.objects
                or self.scene.groups
                or self.scene.collision_shapes
            )
        try:
            return self._compute_document_signature() != self._clean_signature
        except Exception:
            return True

    def _expected_window_title(self) -> str:
        document_name = self._document_name
        if self.is_document_modified():
            t = self.translations[self.current_lang]
            document_name = f"{document_name or t['untitled_project']}*"
        return build_window_title(self.current_lang, document_name)

    def _refresh_window_title(self) -> None:
        self.setWindowTitle(self._expected_window_title())

    def _on_scene_changed(self) -> None:
        self._refresh_window_title()

    def _mark_document_clean(self) -> None:
        self._clean_signature = self._compute_document_signature()
        self._refresh_window_title()

    def _mark_document_unsaved(self) -> None:
        self._clean_signature = None
        self._refresh_window_title()

    def _reset_command_history(self) -> None:
        manager = getattr(self.scene, "cmd", None)
        if manager is None:
            self._update_undo_redo_actions()
            return
        if hasattr(manager, "clear"):
            manager.clear()
        else:
            if hasattr(manager, "_undo"):
                manager._undo.clear()
            if hasattr(manager, "_redo"):
                manager._redo.clear()
        self._update_undo_redo_actions()

    def _refresh_document_views(self, *, project_loaded: bool) -> None:
        has_image = self.scene.image is not None
        self.tool_palette.setEnabled(has_image)
        self.side_panel.setEnabled(project_loaded or has_image)
        self.side_panel.refresh()
        if hasattr(self.layers, "refresh"):
            self.layers.refresh()
        if hasattr(self.groups, "refresh"):
            self.groups.refresh()
        self.canvas.update()
        if has_image:
            self.canvas.fit_to_window()

    def _confirm_unsaved_changes(self) -> bool:
        if not self.is_document_modified():
            return True
        t = self.translations[self.current_lang]
        choice = QMessageBox.warning(
            self,
            t["unsaved_title"],
            t["unsaved_message"],
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self.save_project()
        if choice == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _normalized_project_path(self, path: str | os.PathLike[str]) -> Path:
        destination = Path(path)
        if destination.suffix.lower() != PROJECT_FILE_EXTENSION:
            destination = destination.with_suffix(PROJECT_FILE_EXTENSION)
        return destination

    def _project_dialog_start(self) -> str:
        if self._project_path is not None:
            return str(self._project_path)
        base = Path(self._last_folder) if self._last_folder else Path.cwd()
        stem = Path(self._document_name).stem if self._document_name else "project"
        return str(base / f"{stem}{PROJECT_FILE_EXTENSION}")

    def _rebase_image_reference_for_save(self, destination: Path) -> tuple[object, ...]:
        original = (
            getattr(self.scene, "image_path", None),
            getattr(self.scene, "image_path_kind", None),
            getattr(self.scene, "image_sha256", None),
            getattr(self.scene, "_image_reference_loaded", False),
        )
        if (
            self._project_path is None
            or getattr(self.scene, "image_path", None) is None
            or getattr(self.scene, "image_path_kind", None) != "relative"
        ):
            return original

        source = (
            self._project_path.parent / os.fsdecode(self.scene.image_path)
        ).resolve(strict=False)
        destination_parent = destination.parent.resolve(strict=False)
        try:
            relative = source.relative_to(destination_parent)
        except ValueError:
            self.scene.image_path = str(source)
            self.scene.image_path_kind = "absolute"
        else:
            self.scene.image_path = relative.as_posix()
            self.scene.image_path_kind = "relative"
        return original

    def _restore_image_reference(self, original: tuple[object, ...]) -> None:
        (
            self.scene.image_path,
            self.scene.image_path_kind,
            self.scene.image_sha256,
            self.scene._image_reference_loaded,
        ) = original

    def _resolved_project_image_path(
        self,
        project_path: Path,
        scene=None,
    ) -> Path | None:
        target_scene = scene if scene is not None else self.scene
        image_path = getattr(target_scene, "image_path", None)
        if image_path is None:
            return None
        candidate = Path(os.fsdecode(image_path))
        if getattr(target_scene, "image_path_kind", None) == "relative":
            return (project_path.parent / candidate).resolve(strict=False)
        return candidate.expanduser()

    def _attach_project_image(self, project_path: Path, scene=None) -> list[str]:
        target_scene = scene if scene is not None else self.scene
        resolved = self._resolved_project_image_path(project_path, target_scene)
        if resolved is None:
            return []

        t = self.translations[self.current_lang]
        if not resolved.is_file():
            return [t["project_image_missing"].format(path=resolved)]

        import cv2

        try:
            image = cv2.imread(str(resolved), cv2.IMREAD_UNCHANGED)
        except (OSError, cv2.error):
            image = None
        if image is None:
            return [t["project_image_unreadable"].format(path=resolved)]

        warnings: list[str] = []
        expected_hash = getattr(target_scene, "image_sha256", None)
        if expected_hash:
            digest = hashlib.sha256()
            try:
                with resolved.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError:
                warnings.append(
                    t["project_image_hash_unavailable"].format(path=resolved)
                )
            else:
                if digest.hexdigest() != expected_hash:
                    warnings.append(
                        t["project_image_hash_mismatch"].format(path=resolved)
                    )

        target_scene.attach_project_image(image)
        return warnings

    def _adopt_project_scene(self, staged_scene) -> None:
        """Replace document data only after every load phase has succeeded."""

        self.scene.image = staged_scene.image
        self.scene.image_path = staged_scene.image_path
        self.scene.image_path_kind = staged_scene.image_path_kind
        self.scene.image_sha256 = staged_scene.image_sha256
        self.scene._image_reference_loaded = staged_scene._image_reference_loaded
        self.scene.layers = staged_scene.layers
        self.scene.objects = staged_scene.objects
        self.scene.groups = staged_scene.groups
        self.scene.collision_shapes = staged_scene.collision_shapes
        self.scene.selected_id = None

    def _show_project_warnings(self, warnings: list[str]) -> None:
        if not warnings:
            return
        t = self.translations[self.current_lang]
        QMessageBox.warning(
            self,
            t["project_warnings_title"],
            "\n".join(f"• {warning}" for warning in warnings),
        )

    def open_project(self) -> bool:
        started_at = time.perf_counter()
        t = self.translations[self.current_lang]
        initial_dir = (
            str(self._project_path.parent)
            if self._project_path is not None
            else self._last_folder or ""
        )
        path, _ = QFileDialog.getOpenFileName(
            self,
            t["open_project_dialog"],
            initial_dir,
            t["project_files"],
        )
        if not path:
            record_validation_event(
                "project.opened",
                "CANCELLED",
                duration_ms=elapsed_ms(started_at),
            )
            return False
        if not self._confirm_unsaved_changes():
            record_validation_event(
                "project.opened",
                "CANCELLED",
                duration_ms=elapsed_ms(started_at),
                reason="unsaved_changes",
            )
            return False

        destination = Path(path).resolve(strict=False)
        try:
            staged_scene = type(self.scene)()
            migration_warnings = list(staged_scene.load_project(str(destination)))
            image_warnings = self._attach_project_image(
                destination,
                staged_scene,
            )
        except Exception as exc:
            logger.error(
                "Failed to open project: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "project.opened",
                exc,
                duration_ms=elapsed_ms(started_at),
                schema_extension=destination.suffix.lower(),
            )
            QMessageBox.critical(
                self,
                t["error"],
                t["failed_open_project"] + str(exc),
            )
            return False

        self._adopt_project_scene(staged_scene)
        self._project_path = destination
        self._document_name = destination.name
        self._last_folder = str(destination.parent)
        self._reset_command_history()
        self.scene._notify()
        self._refresh_document_views(project_loaded=True)
        self._mark_document_clean()
        warnings = migration_warnings + image_warnings
        self._show_project_warnings(warnings)
        record_validation_event(
            "project.opened",
            "SUCCESS",
            duration_ms=elapsed_ms(started_at),
            schema_extension=destination.suffix.lower(),
            object_count=len(self.scene.objects),
            warning_count=len(warnings),
            image_loaded=self.scene.image is not None,
        )
        return True

    def _save_project_to(self, path: str | os.PathLike[str]) -> bool:
        started_at = time.perf_counter()
        t = self.translations[self.current_lang]
        destination = self._normalized_project_path(path).resolve(strict=False)
        original_reference = self._rebase_image_reference_for_save(destination)
        try:
            self.scene.save_project(str(destination))
        except Exception as exc:
            self._restore_image_reference(original_reference)
            logger.error(
                "Failed to save project: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "project.saved",
                exc,
                duration_ms=elapsed_ms(started_at),
                schema_extension=destination.suffix.lower(),
            )
            QMessageBox.critical(
                self,
                t["error"],
                t["failed_save_project"] + str(exc),
            )
            return False

        self._project_path = destination
        self._document_name = destination.name
        self._last_folder = str(destination.parent)
        self._mark_document_clean()
        self.statusBar().showMessage(t["project_saved"], 5000)
        record_validation_event(
            "project.saved",
            "SUCCESS",
            duration_ms=elapsed_ms(started_at),
            schema_extension=destination.suffix.lower(),
            object_count=len(self.scene.objects),
        )
        return True

    def save_project(self) -> bool:
        if self._project_path is None:
            return self.save_project_as()
        return self._save_project_to(self._project_path)

    def save_project_as(self) -> bool:
        t = self.translations[self.current_lang]
        path, _ = QFileDialog.getSaveFileName(
            self,
            t["save_project_dialog"],
            self._project_dialog_start(),
            t["project_files"],
        )
        if not path:
            record_validation_event("project.saved", "CANCELLED")
            return False
        return self._save_project_to(path)

    def open_image(self) -> bool:
        started_at = time.perf_counter()
        initial_dir = self._last_folder or ""
        t = self.translations[self.current_lang]
        path, _ = QFileDialog.getOpenFileName(
            self,
            t["open_image_dialog"],
            initial_dir,
            t["image_files"],
        )
        if not path:
            record_validation_event(
                "image.opened",
                "CANCELLED",
                duration_ms=elapsed_ms(started_at),
            )
            return False
        try:
            import cv2

            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if image is None:
                raise ValueError("Failed to load image")
        except Exception as exc:
            logger.error(
                "Failed to open image: %s",
                exc,
                exc_info=True,
                extra={"validation_event_recorded": True},
            )
            record_validation_exception(
                "image.opened",
                exc,
                duration_ms=elapsed_ms(started_at),
                suffix=os.path.splitext(path)[1].lower(),
            )
            QMessageBox.critical(
                self,
                t["error"],
                t["failed_open_image"] + str(exc),
            )
            return False

        if not self._confirm_unsaved_changes():
            record_validation_event(
                "image.opened",
                "CANCELLED",
                duration_ms=elapsed_ms(started_at),
                reason="unsaved_changes",
            )
            return False

        self.scene.replace_with_image(image, path)
        self._project_path = None
        self._document_name = os.path.basename(path)
        self._last_folder = os.path.dirname(path)
        self._reset_command_history()
        self._refresh_document_views(project_loaded=False)
        self._mark_document_unsaved()

        loaded = self.scene.image is not None
        record_validation_event(
            "image.opened",
            "SUCCESS" if loaded else "FAILURE",
            duration_ms=elapsed_ms(started_at),
            loaded=loaded,
            width=int(image.shape[1]),
            height=int(image.shape[0]),
            channels=int(image.shape[2]) if image.ndim == 3 else 1,
            suffix=os.path.splitext(path)[1].lower(),
            tools_enabled=self.tool_palette.isEnabled(),
            side_panel_enabled=self.side_panel.isEnabled(),
        )
        return loaded

    def open_export(self):
        started_at = time.perf_counter()
        self.canvas.set_preview_mode(True)
        try:
            dlg = ExportDialog(self.scene, self, lang=self.current_lang)
            visible_contract = dlg.minimumWidth() >= 470
            record_validation_event(
                "export.dialog.opened",
                "SUCCESS" if visible_contract else "FAILURE",
                duration_ms=elapsed_ms(started_at),
                language=dlg.current_lang,
                minimum_width=dlg.minimumWidth(),
                compact_contract=visible_contract,
            )
            dlg.exec()
            record_validation_event(
                "export.dialog.closed",
                "SUCCESS",
                duration_ms=elapsed_ms(started_at),
            )
        except Exception as exc:
            record_validation_exception(
                "export.dialog.opened",
                exc,
                duration_ms=elapsed_ms(started_at),
            )
            raise
        finally:
            self.canvas.set_preview_mode(False)

    def _clear_mask_viewer_reference(self, *_args):
        self._mask_viewer_dialog = None

    def open_mask_viewer(self):
        try:
            if self._mask_viewer_dialog is not None:
                self._mask_viewer_dialog.update_language(self.current_lang)
                self._mask_viewer_dialog.show()
                self._mask_viewer_dialog.raise_()
                self._mask_viewer_dialog.activateWindow()
                return
            dlg = MaskViewerDialog(self.scene, self, lang=self.current_lang)
            dlg.setModal(False)  # Allow interaction with main window
            dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            dlg.destroyed.connect(self._clear_mask_viewer_reference)
            self._mask_viewer_dialog = dlg
            dlg.show()
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                self.translations[self.current_lang]["failed_mask_viewer"] + str(e),
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_unsaved_changes():
            record_validation_event(
                "document.close_requested",
                "SUCCESS",
                modified=False,
            )
            event.accept()
            return
        record_validation_event(
            "document.close_requested",
            "CANCELLED",
            modified=True,
        )
        event.ignore()

    def _toggle_collision_overlay(self):
        visible = self.collision_overlay_action.isChecked()
        self.collision_overlay.set_visible(visible)
        self.canvas.update()

    def _on_collision_batch_test(self):
        if self.physics_manager:
            results = self.physics_manager.batch_test()
            overlay_results = [
                {
                    "obj1_id": r.obj1_id,
                    "obj2_id": r.obj2_id,
                    "colliding": r.colliding,
                    "mtv": r.mtv,
                }
                for r in results
            ]
            self.collision_overlay.update_collision_results(overlay_results)
            self.canvas.update()

    def _on_collision_export(self):
        data = self._build_collision_document(
            results=self.collision_panel.collision_results,
            statistics=self.physics_manager.get_stats() if self.physics_manager else {},
        )
        if data is None:
            return False
        return self._save_collision_json(data, "collision-results.json")

    def _on_collision_auto_generate(self):
        if self.physics_manager:
            for shape_id, shape in self.scene.collision_shapes.items():
                self.physics_manager.register(shape_id, shape)
        self.canvas.update()
