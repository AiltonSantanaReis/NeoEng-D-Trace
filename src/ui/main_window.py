# src/ui/main_window.py
import os
import time
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

# Imports de lógica e colisão estática
from src.collision import StaticCollisionManager
from src.core.app_identity import build_window_title
from src.core.document_session import DocumentSession
from src.core.image_input import (
    hash_validated_image_file,
    inspect_image_file,
    validate_decoded_image,
)
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
from src.persistence.autosave import AutosaveStore
from src.ui.app_icon import application_icon
from src.ui.autosave_coordinator import AutosaveCoordinator
from src.ui.canvas_view import CanvasView
from src.ui.collision_overlay import CollisionOverlay
from src.ui.collision_panel import CollisionPanel
from src.ui.command_bindings import register_main_window_commands
from src.ui.command_palette import CommandPaletteDialog
from src.ui.command_registry import CommandRegistry
from src.ui.export_dialog import ExportDialog
from src.ui.groups_panel import GroupsPanel
from src.ui.icon_library import configure_main_window_controls
from src.ui.layers_panel import LayersPanel
from src.ui.main_window_translations import MAIN_WINDOW_TRANSLATIONS
from src.ui.mask_viewer import MaskViewerDialog
from src.ui.reference_chrome import connect_reference_search
from src.ui.responsive_layout import build_responsive_layout
from src.ui.scenario_authoring_actions import install_scenario_authoring
from src.ui.scenario_preview_actions import install_scenario_preview_actions
from src.ui.side_panel import SidePanel
from src.ui.tool_palette import ToolPalette
from src.ui.viewport_actions import install_viewport_actions


class MainWindow(QMainWindow):

    command_palette_requested = Signal()

    @property
    def _project_path(self) -> Path | None:
        return self.document_session.project_path

    @_project_path.setter
    def _project_path(self, value: Path | None) -> None:
        self.document_session.project_path = value

    @property
    def _document_name(self) -> str | None:
        return self.document_session.document_name

    @_document_name.setter
    def _document_name(self, value: str | None) -> None:
        self.document_session.document_name = value

    @property
    def _last_folder(self) -> str | None:
        return self.document_session.last_folder

    @_last_folder.setter
    def _last_folder(self, value: str | None) -> None:
        self.document_session.last_folder = value

    @property
    def _clean_signature(self) -> str | None:
        return self.document_session.clean_signature

    @_clean_signature.setter
    def _clean_signature(self, value: str | None) -> None:
        self.document_session.clean_signature = value

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

    def __init__(self, scene, config, *, autosave_store: AutosaveStore | None = None):
        super().__init__()
        self.setWindowIcon(application_icon())
        self.scene = scene
        self.config = config
        self.document_session = DocumentSession(
            scene,
            last_folder=config.get("last_folder"),
        )
        self._current_tool = config.get("tool", "polygonal_lasso")
        self._mask_viewer_dialog: MaskViewerDialog | None = None
        self._autosave_store = autosave_store
        self._autosave_coordinator: AutosaveCoordinator | None = None
        self.autosave_timer = None

        # Configuração da Janela Principal
        self.current_lang = "en"
        self.setWindowTitle(build_window_title(self.current_lang))
        self.resize(1200, 800)

        self._setup_menu_bar()
        self.command_registry = CommandRegistry(self)

        self.act_open = self.open_image_action

        self.act_export = QAction("Export...", self)
        self.act_export.triggered.connect(self.open_export)

        self.act_export_collision_json = QAction("Export Collision (JSON)", self)
        self.act_export_collision_json.triggered.connect(self.export_collision_json)
        self.act_export_collision_txt = QAction("Export Collision (TXT)", self)
        self.act_export_collision_txt.triggered.connect(self.export_collision_txt)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.act_export)
        self.file_menu.addAction(self.act_export_collision_json)
        self.file_menu.addAction(self.act_export_collision_txt)
        self.canvas = CanvasView(scene)
        self.tool_palette = ToolPalette(self.canvas)
        install_viewport_actions(self)
        self.side_panel = SidePanel(scene, self.canvas)
        self.layers = LayersPanel(scene)
        self.groups = GroupsPanel(scene)

        self.tool_palette.setEnabled(False)
        self.side_panel.setEnabled(False)

        self.collision_manager = StaticCollisionManager(grid_cell_size=64)
        self.collision_overlay = CollisionOverlay(scene)
        self.collision_panel = CollisionPanel(scene)

        self.collision_panel.set_collision_manager(self.collision_manager)
        self.collision_panel.batch_test_requested.connect(self._on_collision_batch_test)
        self.collision_panel.export_collisions_requested.connect(
            self._on_collision_export
        )
        self.collision_panel.auto_generate_requested.connect(
            self._on_collision_auto_generate
        )

        self.canvas.set_collision_overlay(self.collision_overlay)
        install_scenario_authoring(self)
        # Navigation/render commands remain stable canonical QActions.
        self.act_fit = QAction("Fit View", self)
        self.act_fit.setShortcut(QKeySequence("F"))
        self.act_fit.triggered.connect(self.canvas.fit_to_window)

        # Botão: Zoom 100%
        self.act_100 = QAction("1:1 Pixel", self)
        self.act_100.triggered.connect(lambda: self.canvas.set_zoom(1.0))

        self.act_lit = QAction("Lit", self)
        self.act_lit.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_LIT)
        )

        self.act_xray1 = QAction("X-Ray 1", self)
        self.act_xray1.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_XRAY_1)
        )

        self.act_xray2 = QAction("X-Ray 2", self)
        self.act_xray2.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_XRAY_2)
        )

        self.act_xray3 = QAction("X-Ray 3", self)
        self.act_xray3.triggered.connect(
            lambda: self.canvas.set_view_mode(self.canvas.VIEW_XRAY_3)
        )

        # Keep navigation and rendering commands available from the complete
        # application menu. The same QAction instances remain the source of
        # truth for toolbar, command registry and keyboard behavior.
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.act_fit)
        self.view_menu.addAction(self.act_100)
        self.view_menu.addAction(self.act_grid)
        self.view_menu.addAction(self.act_snap)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.act_lit)
        self.view_menu.addAction(self.act_xray1)
        self.view_menu.addAction(self.act_xray2)
        self.view_menu.addAction(self.act_xray3)

        # Botão: Limpar Tudo (Com Undo)
        self.act_clean = QAction("Clean All", self)
        self.act_clean.triggered.connect(self.canvas.clean_all)

        self.reference_tool_palette: QToolBar
        configure_main_window_controls(self)
        self._responsive_layout = build_responsive_layout(self)
        self._setup_shortcuts()
        register_main_window_commands(self.command_registry, self)
        self.translations = MAIN_WINDOW_TRANSLATIONS
        self.command_palette = CommandPaletteDialog(self.command_registry, self)
        connect_reference_search(self)
        self.update_language()
        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self._on_scene_changed)
        self._connect_command_history()
        self._update_undo_redo_actions()
        self._mark_document_clean()
        if self._autosave_store is not None:
            self.enable_autosave(self._autosave_store)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._responsive_layout.update()

    def _update_compact_panel_titles(self, translations) -> None:
        self._responsive_layout.update_titles(translations)

    def enable_autosave(self, store: AutosaveStore) -> None:
        if self._autosave_coordinator is not None:
            return
        self._autosave_store = store
        self._autosave_coordinator = AutosaveCoordinator(
            self,
            scene=self.scene,
            session=self.document_session,
            store=store,
            interval_seconds=self.config.get("autosave_interval_seconds", 60),
            translations=lambda: self.translations[self.current_lang],
            recover=self._recover_autosave_snapshot,
            show_status=self.statusBar().showMessage,
        )
        self.autosave_timer = self._autosave_coordinator.timer

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

        self.command_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.command_palette_shortcut.setObjectName("command_palette_shortcut")
        self.command_palette_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.command_palette_shortcut.activated.connect(self._request_command_palette)

    def _request_command_palette(self) -> None:
        """Open the integrated palette while preserving the public request signal."""

        self.command_palette_requested.emit()
        self.command_palette.show_palette()

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
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        # Conecta diretamente à função _undo já existente e correta
        self.undo_action.triggered.connect(self._undo)
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
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

        # Language selection is a persistent QAction contract, not a hidden
        # QPushButton.  The submenu action provides one semantic command-family
        # item while the concrete locale actions remain directly triggerable
        # from menus, the command registry and the command palette.
        self.language_menu = self.view_menu.addMenu("Language")
        self.language_action = self.language_menu.menuAction()
        self.language_action.setObjectName("language_action")
        self.act_english = QAction("English", self)
        self.act_english.setCheckable(True)
        self.act_english.triggered.connect(lambda: self.set_language("en"))
        self.language_menu.addAction(self.act_english)
        self.act_portuguese = QAction("Portuguese", self)
        self.act_portuguese.setCheckable(True)
        self.act_portuguese.triggered.connect(lambda: self.set_language("pt"))
        self.language_menu.addAction(self.act_portuguese)

        install_scenario_preview_actions(self)

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

        self.act_fit.setText(t["fit_view"])
        self.act_100.setText(t["pixel_1"])
        self.act_lit.setText(t["lit"])
        self.act_xray1.setText(t["xray_1"])
        self.act_xray2.setText(t["xray_2"])
        self.act_xray3.setText(t["xray_3"])
        self.act_clean.setText(t["clean_all"])
        self.act_gizmo.setText(t["gizmo"])
        self.language_menu.setTitle(t["language"])
        self.act_english.setText(t["english"])
        self.act_portuguese.setText(t["portuguese"])
        self.act_english.setChecked(self.current_lang == "en")
        self.act_portuguese.setChecked(self.current_lang == "pt")
        self._update_compact_panel_titles(t)

        self.edit_menu.setTitle(t["edit_menu"])
        self.undo_action.setText(t["undo"])
        self.redo_action.setText(t["redo"])
        getattr(self, "settings_action").setText(t["view_settings"])

        # View Menu
        self.view_menu.setTitle(t["view_menu"])
        self.mask_viewer_action.setText(t["mask_viewer"])
        self.collision_overlay_action.setText(t["collision_overlay"])

        self.command_palette.update_language(self.current_lang)
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

    def set_last_folder(self, folder):
        self._last_folder = folder

    def select_tool(self, tool_name):
        self._current_tool = tool_name

    def _signature_path_hint(self) -> Path:
        return self.document_session.signature_path_hint()

    def _compute_document_signature(self) -> str:
        return self.document_session.compute_signature()

    def _compute_unvalidated_document_signature(self) -> str:
        return self.document_session.compute_unvalidated_signature()

    def is_document_modified(self) -> bool:
        return self.document_session.is_modified()

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
        self.document_session.mark_clean()
        self._refresh_window_title()

    def _mark_document_unsaved(self) -> None:
        self.document_session.mark_unsaved()
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
        self.reference_tool_palette.setEnabled(has_image)
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
            self._discard_autosave()
            return True
        return False

    def _normalized_project_path(self, path: str | os.PathLike[str]) -> Path:
        return self.document_session.normalized_project_path(path)

    def _project_dialog_start(self) -> str:
        return self.document_session.project_dialog_start()

    def _rebase_image_reference_for_save(self, destination: Path) -> tuple[object, ...]:
        return self.document_session.rebase_image_reference_for_save(destination)

    def _restore_image_reference(self, original: tuple[object, ...]) -> None:
        self.document_session.restore_image_reference(original)

    def _discard_autosave(self) -> bool:
        if self._autosave_coordinator is None:
            return True
        return self._autosave_coordinator.discard_current_session()

    def perform_autosave(self) -> bool:
        if self._autosave_coordinator is None:
            return False
        return self._autosave_coordinator.perform()

    def offer_autosave_recovery(self) -> bool:
        if self._autosave_coordinator is None:
            return False
        return self._autosave_coordinator.offer_recovery()

    def _recover_autosave_snapshot(self, snapshot) -> None:
        staged_scene = type(self.scene)()
        snapshot.apply_to(staged_scene)
        image_warnings = self._attach_project_image(
            snapshot.reference_project_path,
            staged_scene,
        )
        self._adopt_project_scene(staged_scene)
        source_changed = snapshot.source_project_changed()
        self._project_path = None if source_changed else snapshot.source_project_path
        translations = self.translations[self.current_lang]
        self._document_name = snapshot.document_name or (
            snapshot.source_project_path.name
            if snapshot.source_project_path is not None
            else translations["recovered_project"]
        )
        base_path = snapshot.source_project_path or snapshot.reference_project_path
        self._last_folder = str(base_path.parent)
        self._reset_command_history()
        self.scene._notify()
        self._refresh_document_views(project_loaded=True)
        self._mark_document_unsaved()
        if source_changed:
            image_warnings.append(translations["autosave_source_changed"])
        self._show_project_warnings(image_warnings)

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
            image_info = inspect_image_file(resolved)
            image = cv2.imread(str(resolved), cv2.IMREAD_UNCHANGED)
            if image is None:
                raise ValueError("decoder returned no pixels")
            validate_decoded_image(image, image_info)
        except (OSError, ValueError, cv2.error) as exc:
            return [t["project_image_unreadable"].format(path=resolved) + f" ({exc})"]

        warnings: list[str] = []
        expected_hash = getattr(target_scene, "image_sha256", None)
        if expected_hash:
            try:
                actual_hash = hash_validated_image_file(image_info)
            except (OSError, ValueError):
                warnings.append(
                    t["project_image_hash_unavailable"].format(path=resolved)
                )
            else:
                if actual_hash != expected_hash:
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
        self._discard_autosave()
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
        self._discard_autosave()
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

            image_info = inspect_image_file(path)
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if image is None:
                raise ValueError("decoder returned no pixels")
            validate_decoded_image(image, image_info)
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
        self._discard_autosave()

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
            if self._autosave_coordinator is not None:
                self._autosave_coordinator.stop()
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
        if self.collision_manager:
            results = self.collision_manager.batch_test()
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
            statistics=(
                self.collision_manager.get_stats() if self.collision_manager else {}
            ),
        )
        if data is None:
            return False
        return self._save_collision_json(data, "collision-results.json")

    def _on_collision_auto_generate(self):
        if self.collision_manager:
            if self.collision_panel.collision_manager is self.collision_manager:
                self.collision_panel._sync_collision_manager_from_scene()
            else:
                for shape_id, shape in self.scene.collision_shapes.items():
                    parts = getattr(self.scene, "collision_parts", {}).get(shape_id, [])
                    if parts:
                        for part_index, part in enumerate(parts):
                            self.collision_manager.register(
                                f"{shape_id}#part{part_index}", part
                            )
                    else:
                        self.collision_manager.register(shape_id, shape)
        self.canvas.update()
