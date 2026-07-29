# src/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QMenu,
    QPushButton,
)
from PySide6.QtGui import QAction, QShortcut, QKeySequence
from PySide6.QtCore import Qt
import os
import time

# Imports dos componentes da UI
from src.ui.side_panel import SidePanel
from src.ui.canvas_view import CanvasView
from src.ui.export_dialog import ExportDialog
from src.ui.groups_panel import GroupsPanel
from src.ui.tool_palette import ToolPalette
from src.ui.mask_viewer import MaskViewerDialog
from src.ui.collision_panel import CollisionPanel
from src.ui.collision_overlay import CollisionOverlay

# Imports de Lógica e Física
from src.physics.physics_manager import PhysicsManager
from src.core.logger import logger
from src.core.validation_events import (
    elapsed_ms,
    record_validation_event,
    record_validation_exception,
)
from src.core.app_identity import build_window_title


class MainWindow(QMainWindow):

    def export_collision_json(self):
        """Export collision shapes as JSON without changing their schema."""
        import json

        t = self.translations[self.current_lang]
        path, _ = QFileDialog.getSaveFileName(
            self,
            t["export_collision_json_dialog"],
            "collisions.json",
            t["json_files"],
        )
        if path:
            data = getattr(self.scene, "collision_shapes", {})
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)

    def export_collision_txt(self):
        """Export collision shapes as the existing plain-text format."""
        t = self.translations[self.current_lang]
        path, _ = QFileDialog.getSaveFileName(
            self,
            t["export_collision_txt_dialog"],
            "collisions.txt",
            t["text_files"],
        )
        if path:
            data = getattr(self.scene, "collision_shapes", {})
            with open(path, "w", encoding="utf-8") as handle:
                for object_id, shape in data.items():
                    handle.write(f"Object {object_id}:\n")
                    for point in shape:
                        handle.write(f"  {point}\n")
                    handle.write("\n")

    def __init__(self, scene, config):
        super().__init__()
        self.scene = scene
        self.config = config
        self._last_folder = config.get("last_folder")
        self._current_tool = config.get("tool", "polygonal_lasso")
        self._mask_viewer_dialog = None

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

        self.act_open = QAction("Open Image", self)
        self.act_open.triggered.connect(self.open_image)
        self.toolbar.addAction(self.act_open)

        self.act_export = QAction("Export...", self)
        self.act_export.triggered.connect(self.open_export)
        self.toolbar.addAction(self.act_export)

        # Adiciona menu de exportação de colisão
        export_menu = QMenu(self)
        self.act_export_collision_json = QAction(
            "Export Collision (JSON)", self
        )
        self.act_export_collision_json.triggered.connect(
            self.export_collision_json
        )
        export_menu.addAction(self.act_export_collision_json)
        self.act_export_collision_txt = QAction(
            "Export Collision (TXT)", self
        )
        self.act_export_collision_txt.triggered.connect(
            self.export_collision_txt
        )
        export_menu.addAction(self.act_export_collision_txt)
        self.export_collision_button = QPushButton("Export Collision", self)
        self.export_collision_button.setMenu(export_menu)
        self.toolbar.addWidget(self.export_collision_button)
        # 3. Componentes Centrais
        self.canvas = CanvasView(scene)
        self.tool_palette = ToolPalette(self.canvas)
        self.side_panel = SidePanel(scene, self.canvas)
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
        self.collision_panel.batch_test_requested.connect(
            self._on_collision_batch_test
        )
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
            "QPushButton:pressed { background-color: transparent; "
            "border: none; }"
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
                "open_image": "Open Image",
                "open_image_dialog": "Open Image",
                "image_files": "Images (*.png *.jpg *.jpeg *.bmp *.tiff)",
                "export": "Export...",
                "export_collision": "Export Collision",
                "export_collision_json": "Export Collision (JSON)",
                "export_collision_txt": "Export Collision (TXT)",
                "export_collision_json_dialog": "Export Collision JSON",
                "export_collision_txt_dialog": "Export Collision TXT",
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
                "open_image": "Abrir Imagem",
                "open_image_dialog": "Abrir Imagem",
                "image_files": "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff)",
                "export": "Exportar...",
                "export_collision": "Exportar Colisão",
                "export_collision_json": "Exportar Colisão (JSON)",
                "export_collision_txt": "Exportar Colisão (TXT)",
                "export_collision_json_dialog": "Exportar Colisão em JSON",
                "export_collision_txt_dialog": "Exportar Colisão em TXT",
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
                "failed_mask_viewer": "Falha ao abrir "
                "Visualizador de Máscara: ",
                "language": "Idioma",
                "english": "Inglês",
                "portuguese": "Português",
            },
        }
        self.update_language()

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
        QShortcut(QKeySequence("F"), self, activated=self.canvas.fit_to_window)
        QShortcut(
            QKeySequence("X"), self, activated=self.canvas.toggle_xray
        )  # Modo Raio-X
        QShortcut(
            QKeySequence("A"),
            self,
            activated=lambda: self.canvas.set_view_mode(0),
        )  # Modo Lit (Normal)

        # Tool Shortcuts (1-6)
        QShortcut(
            QKeySequence("1"),
            self,
            activated=lambda: self._select_tool("polygonal_lasso"),
        )
        QShortcut(
            QKeySequence("2"),
            self,
            activated=lambda: self._select_tool("lasso_tool"),
        )
        QShortcut(
            QKeySequence("3"),
            self,
            activated=lambda: self._select_tool("rect_selection"),
        )
        QShortcut(
            QKeySequence("4"),
            self,
            activated=lambda: self._select_tool("ellipse_selection"),
        )
        QShortcut(
            QKeySequence("5"),
            self,
            activated=lambda: self._select_tool("pen_tool"),
        )
        QShortcut(
            QKeySequence("6"),
            self,
            activated=lambda: self._select_tool("magnetic_lasso"),
        )

        # Undo/Redo Shortcuts
        # Nota: Mantemos isso para garantir o funcionamento do atalho,
        # mesmo que também exista no menu.
        QShortcut(QKeySequence.Undo, self, activated=self._undo)
        QShortcut(QKeySequence.Redo, self, activated=self._redo)

    def _undo(self):
        # Active drawing tools may consume Undo for their in-progress operation.
        if self.canvas.request_tool_undo():
            self.canvas.update()
            return
        if self.scene.cmd:
            self.scene.cmd.undo(self.scene)
        self.canvas.update()
        self.side_panel.refresh()

    def _redo(self):
        # Active drawing tools may consume Redo for their in-progress operation.
        if self.canvas.request_tool_redo():
            self.canvas.update()
            return
        if self.scene.cmd:
            self.scene.cmd.redo(self.scene)
        self.canvas.update()
        self.side_panel.refresh()

    def _select_tool(self, tool_name):
        if hasattr(self.tool_palette, "select_tool_by_name"):
            self.tool_palette.select_tool_by_name(tool_name)

    def _setup_menu_bar(self):
        menubar = self.menuBar()

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
        self.collision_overlay_action.triggered.connect(
            self._toggle_collision_overlay
        )
        self.view_menu.addAction(self.collision_overlay_action)

    def set_language(self, lang):
        started_at = time.perf_counter()
        previous = self.current_lang
        requested = lang
        try:
            self.current_lang = lang if lang in self.translations else "en"
            self.update_language()
            expected_title = build_window_title(
                self.current_lang, self._document_name
            )
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
        self.setWindowTitle(
            build_window_title(self.current_lang, self._document_name)
        )

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
        if (
            self._mask_viewer_dialog is not None
            and hasattr(self._mask_viewer_dialog, "update_language")
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
            self.language_button.mapToGlobal(
                self.language_button.rect().bottomLeft()
            )
        )

    def set_last_folder(self, folder):
        self._last_folder = folder

    def select_tool(self, tool_name):
        self._current_tool = tool_name

    def open_image(self):
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
            return
        self._last_folder = os.path.dirname(path)
        try:
            import cv2

            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError("Failed to load image")

            self.scene.load_image(img, path)
            self._document_name = os.path.basename(path)
            self.update_language()
            self.tool_palette.setEnabled(True)
            self.side_panel.setEnabled(True)
            self.canvas.fit_to_window()

            loaded = self.scene.image is not None
            record_validation_event(
                "image.opened",
                "SUCCESS" if loaded else "FAILURE",
                duration_ms=elapsed_ms(started_at),
                loaded=loaded,
                width=int(img.shape[1]),
                height=int(img.shape[0]),
                channels=int(img.shape[2]) if img.ndim == 3 else 1,
                suffix=os.path.splitext(path)[1].lower(),
                tools_enabled=self.tool_palette.isEnabled(),
                side_panel_enabled=self.side_panel.isEnabled(),
            )
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
                self.translations[self.current_lang]["error"],
                self.translations[self.current_lang]["failed_open_image"]
                + str(exc),
            )

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
                self.translations[self.current_lang]["failed_mask_viewer"]
                + str(e),
            )

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
        pass

    def _on_collision_auto_generate(self):
        if self.physics_manager:
            for shape_id, shape in self.scene.collision_shapes.items():
                self.physics_manager.register(shape_id, shape)
        self.canvas.update()