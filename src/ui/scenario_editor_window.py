"""Dedicated scenario authoring window.

The main image editor remains focused on image, polygon and collision work.
Scenario authoring is hosted here so its layer stack and inspector cannot
compress or intercept the main editor panels.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_asset_library import prepare_scene_asset, resolve_scene_asset
from src.core.scene_authoring_bridge import professional_document_from_scene
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_render_plan import build_scene_render_plan
from src.exporters.composition_export import (
    CompositionExportError,
    CompositionInputs,
    build_composition_package,
)
from src.exporters.scene_authoring_export import (
    SceneExportTarget,
    save_scene_authoring_export,
)
from src.persistence.errors import ProjectPersistenceError
from src.persistence.p2d05_errors import user_error_message
from src.persistence.scenario_io import project_reference_for
from src.persistence.scene_authoring_io import (
    SceneAuthoringAssetError,
    SceneAuthoringFormatError,
    SceneAuthoringReadError,
    SceneAuthoringValidationError,
    load_scene_authoring,
    load_scene_authoring_recovery,
    load_scene_authoring_v2,
    save_scene_authoring,
    scene_authoring_recovery_path,
)
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneLayerAuthoringRecord,
    SceneParallaxLayerRecord,
    upgrade_scene_authoring_document,
)
from src.ui.entity_prefab_panel import EntityPrefabPanel
from src.ui.hybrid_scene_viewport import HybridSceneViewport
from src.ui.navmesh_panel import NavMeshPanel
from src.ui.scenario_collider_panel import ScenarioColliderPanel
from src.ui.scenario_panel import ScenarioPanel
from src.ui.scene_asset_panel import SceneAssetLibrary
from src.ui.scene_authoring_group_stack import SceneAuthoringGroupStack
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_layer_stack import SceneAuthoringLayerStack
from src.ui.scene_authoring_viewport import SceneAuthoringViewport
from src.ui.scene_sequence_panel import SceneSequencePanel
from src.ui.tilemap_authoring_panel import TileMapAuthoringPanel
from src.ui.tileset_authoring_panel import TilesetAuthoringPanel
from src.ui.vector_contour_panel import VectorContourPanel


class ScenarioEditorWindow(QMainWindow):
    """Interactive authoring surface for the versioned scenario sidecar."""

    document_changed = Signal()

    def __init__(
        self,
        authoring: ScenarioAuthoringState,
        scene: Any,
        *,
        language: str = "en",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.authoring = authoring
        self.scene = scene
        self.current_lang = language
        self.setObjectName("scenario_editor_window")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setMinimumSize(980, 640)
        self.resize(1280, 820)

        self.professional_session: SceneAuthoringSession | None = None
        self.sequence_panel = None
        self.studio_docks = []
        self.professional_viewport: SceneAuthoringViewport | None = None
        self.hybrid_viewport: HybridSceneViewport | None = None
        self._professional_initial_focus_applied = False
        self.professional_inspector: SceneAuthoringInspector | None = None
        self.professional_inspector_scroll: QScrollArea | None = None
        self._professional_project: Path | None = None
        self._temporary_project_dir: tempfile.TemporaryDirectory[str] | None = None
        self._temporary_project_path: Path | None = None
        self.professional_scene_path: Path | None = None
        self.layer_stack: SceneAuthoringLayerStack | None = None
        self.group_stack: SceneAuthoringGroupStack | None = None
        self.asset_library: SceneAssetLibrary | None = None
        self.tilemap_panel: TileMapAuthoringPanel | None = None
        self.tileset_panel: TilesetAuthoringPanel | None = None
        self.collider_panel: ScenarioColliderPanel | None = None
        self.navmesh_panel: NavMeshPanel | None = None
        self.entity_prefab_panel: EntityPrefabPanel | None = None
        self.vector_contour_panel: VectorContourPanel | None = None
        self._pending_v1_document: SceneAuthoringDocumentV1 | None = None
        self._pending_recovery_path: Path | None = None
        self.canvas = self._build_canvas()
        self.legacy_canvas = self.canvas
        self.professional_pages = QStackedWidget(self)
        self.professional_pages.setObjectName("professional_viewport_pages")
        self.professional_empty = QLabel(self.professional_pages)
        self.professional_empty.setObjectName("professional_scene_viewport_empty")
        self.professional_empty.setWordWrap(True)
        self.professional_empty.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.professional_empty.setMinimumSize(0, 0)
        # A word-wrapped QLabel reports the longest unwrapped line as its
        # size hint.  Bound the recovery page so a long localized message
        # cannot expand the splitter beyond the native window and hide the
        # inspector.  The label still expands vertically and wraps within
        # the available viewport.
        self.professional_empty.setMaximumWidth(720)
        self.professional_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.professional_empty.setText(
            "Professional scene viewport\n\n"
            "Choose New Scenario to start from an empty scene, or load a saved project."
        )
        self.professional_pages.addWidget(self.professional_empty)
        self.professional_pages.addWidget(self.canvas)
        self.professional_pages.setCurrentWidget(self.professional_empty)
        self.scenario_panel = ScenarioPanel(authoring, scene, self)
        self.scenario_panel.setMinimumWidth(280)
        self.scenario_panel.setMaximumWidth(520)

        scroll = QScrollArea(self)
        scroll.setObjectName("scenario_inspector_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.scenario_panel)
        self.scenario_inspector_scroll = scroll

        self.right_pages = QStackedWidget(self)
        self.right_pages.setObjectName("scenario_right_pages")
        empty_panel = QWidget(self.right_pages)
        empty_layout = QVBoxLayout(empty_panel)
        empty_label = QLabel(empty_panel)
        empty_label.setObjectName("professional_scene_inspector_empty")
        empty_label.setWordWrap(True)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setText(
            "No scene selected yet.\n\n"
            "Choose New Scenario or open a project to populate the inspector."
        )
        self.professional_inspector_empty = empty_label
        empty_layout.addStretch(1)
        empty_layout.addWidget(empty_label)
        empty_layout.addStretch(1)
        self.right_pages.addWidget(empty_panel)
        self.right_pages.addWidget(scroll)
        self.right_pages.setCurrentWidget(empty_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("scenario_editor_splitter")
        self.professional_pages.setMinimumWidth(420)
        self.right_pages.setMinimumWidth(340)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.addWidget(self.professional_pages)
        splitter.addWidget(self.right_pages)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([650, 300])
        self.editor_splitter = splitter
        self._last_splitter_width = 0
        self.setCentralWidget(splitter)

        self.toolbar = QToolBar("Scenario", self)
        self.toolbar.setObjectName("scenario_editor_toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.open_action = QAction(self)
        self.save_project_action = QAction(self)
        self.save_action = QAction(self)
        self.save_action.setShortcut(QKeySequence("Ctrl+Alt+Shift+S"))
        self.load_action = QAction(self)
        self.load_action.setShortcut(QKeySequence("Ctrl+Alt+Shift+L"))
        self.reset_action = QAction(self)
        self.export_action = QAction(self)
        self.composition_action = QAction(self)
        self.composition_action.setShortcut(QKeySequence("Ctrl+Alt+Shift+E"))
        self.undo_action = QAction(self)
        self.redo_action = QAction(self)
        self.overlay_action = QAction(self)
        self.preview_action = QAction(self)
        self.authoring_action = QAction(self)
        self.hybrid_action = QAction(self)
        self.upgrade_action = QAction(self)
        self.recover_action = QAction(self)
        self.recover_action.setShortcut(QKeySequence("Ctrl+Alt+Shift+R"))
        for persistence_action in (
            self.save_action,
            self.load_action,
            self.recover_action,
        ):
            persistence_action.setShortcutContext(
                Qt.ShortcutContext.ApplicationShortcut
            )
        self.export_target_label = QLabel(self.toolbar)
        self.export_target_label.setObjectName("scenario_export_target_label")
        self.export_target_combo = QComboBox(self.toolbar)
        self.export_target_combo.setObjectName("scenario_export_target_combo")
        self.export_target_combo.addItem("Generic", "generic")
        self.export_target_combo.addItem("Godot 4.7", "godot")
        self.export_target_combo.addItem("Unity 6000.5.7f1", "unity")
        self._toolbar_menu_buttons: dict[str, QToolButton] = {}
        self.overlay_action.setCheckable(True)
        self.preview_action.setCheckable(True)
        self.authoring_action.setCheckable(True)
        self.hybrid_action.setCheckable(True)
        self.preview_action.setChecked(False)
        self.authoring_action.setChecked(True)
        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addAction(self.authoring_action)
        self.mode_group.addAction(self.preview_action)
        for action in (
            self.open_action,
            self.save_project_action,
            self.save_action,
            self.load_action,
            self.reset_action,
        ):
            self.toolbar.addAction(action)
        self._add_toolbar_menu(
            "export",
            "Exportar",
            (self.export_action, self.composition_action),
        )
        self._add_toolbar_menu(
            "edit",
            "Editar",
            (self.undo_action, self.redo_action),
        )
        self._add_toolbar_menu(
            "view",
            "Visualizar",
            (
                self.overlay_action,
                self.preview_action,
                self.authoring_action,
                self.hybrid_action,
            ),
        )
        self._add_toolbar_menu(
            "more",
            "Mais",
            (self.upgrade_action, self.recover_action),
        )
        self.toolbar.addSeparator()
        export_menu = self._toolbar_menu_buttons["export"].menu()
        if export_menu is None:
            raise RuntimeError("Export toolbar menu was not created")
        target_widget = QWidget(export_menu)
        target_layout = QHBoxLayout(target_widget)
        target_layout.setContentsMargins(8, 6, 8, 6)
        target_layout.addWidget(self.export_target_label)
        target_layout.addWidget(self.export_target_combo)
        target_action = QWidgetAction(export_menu)
        target_action.setDefaultWidget(target_widget)
        export_menu.addSeparator()
        export_menu.addAction(target_action)
        self.status_label = QLabel(self)
        self.status_label.setObjectName("scenario_editor_status_label")
        self.statusBar().setObjectName("scenario_editor_status_bar")
        self.statusBar().addPermanentWidget(self.status_label)

        self.open_action.triggered.connect(self._new_professional)
        self.save_project_action.triggered.connect(self._save_new_project_as)
        self.undo_action.triggered.connect(self._undo_professional)
        self.redo_action.triggered.connect(self._redo_professional)
        self.save_action.triggered.connect(self._save_professional)
        self.load_action.triggered.connect(self._load_professional)
        self.reset_action.triggered.connect(self._reset_professional)
        self.export_action.triggered.connect(self._export_professional)
        self.composition_action.triggered.connect(self._export_composition)
        self.upgrade_action.triggered.connect(self._upgrade_professional)
        self.recover_action.triggered.connect(self._recover_professional)
        self.overlay_action.triggered.connect(self._toggle_overlays)
        self.preview_action.triggered.connect(self._toggle_professional_preview)
        self.authoring_action.triggered.connect(self._toggle_professional_authoring)
        self.hybrid_action.triggered.connect(self._toggle_hybrid_view)
        self.authoring.subscribe(self.refresh)
        self.update_language(language)
        self.refresh()

    def _add_toolbar_menu(
        self, key: str, label: str, actions: tuple[QAction, ...]
    ) -> None:
        button = QToolButton(self.toolbar)
        button.setObjectName(f"scenario_toolbar_menu_{key}")
        button.setText(label)
        button.setToolTip(label)
        button.setAccessibleName(label)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        # The command surface follows the project's flat-button pattern; the
        # complete button opens its menu without an extra arrow affordance.
        button.setArrowType(Qt.ArrowType.NoArrow)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(button)
        for action in actions:
            menu.addAction(action)
        button.setMenu(menu)
        self.toolbar.addWidget(button)
        self._toolbar_menu_buttons[key] = button

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        width = self.width()
        if width <= 0 or width == self._last_splitter_width:
            return
        self._last_splitter_width = width
        inspector_width = min(460, max(340, int(width * 0.28)))
        viewport_width = max(420, width - inspector_width)
        self.editor_splitter.setSizes([viewport_width, inspector_width])

    def _build_canvas(self):
        # Local import avoids making MainWindow and the scenario surface depend
        # on each other's construction order.
        from src.ui.canvas_view import CanvasView

        canvas = CanvasView(self.scene, self)
        canvas.set_scenario_preview_enabled(True)
        canvas.set_scenario_overlays_visible(True)
        return canvas

    def _load_professional_document(self, path: Path):
        """Load V2, while exposing asset and migration failures to the UI."""

        try:
            return load_scene_authoring_v2(path)
        except SceneAuthoringAssetError:
            # Asset problems remain editable for relink/replace diagnostics.
            return load_scene_authoring_v2(path, verify_assets=False)

    def _show_pending_document(self, message: str) -> None:
        self.professional_pages.setCurrentWidget(self.professional_empty)
        self.professional_empty.setText(message)
        self.upgrade_action.setEnabled(self._pending_v1_document is not None)
        self.recover_action.setEnabled(self._pending_recovery_path is not None)

    def _build_professional_viewport(
        self,
        document: SceneAuthoringDocumentV2 | None = None,
        *,
        mark_unsaved: bool = False,
    ) -> None:
        project_path = self.authoring.project_path
        if project_path is None:
            return
        scene_path = project_path.with_suffix(".ndtscene.json")
        hybrid_path = project_path.with_suffix(".hybrid3d.json")
        if (
            self.hybrid_viewport is not None
            and self.hybrid_viewport.scene_path != hybrid_path
        ):
            self.professional_pages.removeWidget(self.hybrid_viewport)
            self.hybrid_viewport.deleteLater()
            self.hybrid_viewport = None
        self.hybrid_action.blockSignals(True)
        self.hybrid_action.setChecked(False)
        self.hybrid_action.blockSignals(False)
        self._professional_project = project_path
        self.professional_scene_path = scene_path
        if document is None and scene_path.is_file():
            try:
                document = self._load_professional_document(scene_path)
            except (
                ValueError,
                SceneAuthoringFormatError,
                SceneAuthoringReadError,
                SceneAuthoringValidationError,
            ):
                try:
                    candidate = load_scene_authoring(scene_path, verify_assets=False)
                except (
                    OSError,
                    ValueError,
                    SceneAuthoringFormatError,
                    SceneAuthoringReadError,
                    SceneAuthoringValidationError,
                ):
                    recovery = scene_authoring_recovery_path(scene_path)
                    self._pending_v1_document = None
                    self._pending_recovery_path = (
                        recovery if recovery.is_file() else None
                    )
                    self._show_pending_document(
                        "Saved scene could not be validated. "
                        + (
                            "Use Recover Last Valid."
                            if self._pending_recovery_path
                            else "Repair the scene file before reopening."
                        )
                    )
                    self.status_label.setText(
                        "Scenario unavailable: invalid saved document"
                    )
                    return
                if isinstance(candidate, SceneAuthoringDocumentV1):
                    self._pending_v1_document = candidate
                    recovery = scene_authoring_recovery_path(scene_path)
                    self._pending_recovery_path = (
                        recovery if recovery.is_file() else None
                    )
                    self._show_pending_document(
                        "Schema V1 detected. Choose Upgrade V1 to V2 to edit. "
                        "The V1 file remains unchanged until Save."
                    )
                    self.status_label.setText("Scenario requires explicit V1 upgrade")
                    return
                raise
        if document is None:
            document = professional_document_from_scene(
                self.scene,
                project_path,
                self.authoring.document,
            )
        if not isinstance(document, SceneAuthoringDocumentV2):
            raise SceneAuthoringValidationError(
                "professional viewport requires schema V2"
            )
        self._pending_v1_document = None
        self._pending_recovery_path = None
        session = SceneAuthoringSession(SceneAuthoringModel(document))
        viewport = SceneAuthoringViewport(
            session,
            project_root=project_path.parent,
            parent=self.professional_pages,
        )
        viewport.update_language(self.current_lang)
        viewport.set_preview_enabled(self.preview_action.isChecked())
        viewport.set_authoring_enabled(self.authoring_action.isChecked())
        viewport.set_overlay_visible(self.overlay_action.isChecked())
        for object_id, scene_object in self.scene.objects.items():
            record = next(
                (item for item in document.objects if item.id == object_id),
                None,
            )
            if record is None:
                continue
            origin_x = record.transform.position.x
            origin_y = record.transform.position.y
            viewport.set_geometry(
                object_id,
                (
                    (float(x) - origin_x, float(y) - origin_y)
                    for x, y in scene_object.polygon
                ),
            )
        inspector = SceneAuthoringInspector(session)
        inspector.update_language(self.current_lang)
        self.layer_stack = SceneAuthoringLayerStack(session)
        self.group_stack = SceneAuthoringGroupStack(session)
        self.asset_library = SceneAssetLibrary(
            session, project_path.parent, parent=inspector
        )
        self.asset_library.update_language(self.current_lang)
        self.tilemap_panel = TileMapAuthoringPanel(
            project_path.parent, parent=inspector
        )
        self.tilemap_panel.update_language(self.current_lang)
        self.tileset_panel = TilesetAuthoringPanel(
            project_path.parent, parent=inspector
        )
        self.tileset_panel.update_language(self.current_lang)
        self.collider_panel = ScenarioColliderPanel(
            project_path.parent, parent=inspector
        )
        self.collider_panel.update_language(self.current_lang)
        self.navmesh_panel = NavMeshPanel(project_path.parent, parent=inspector)
        self.navmesh_panel.update_language(self.current_lang)
        self.entity_prefab_panel = EntityPrefabPanel(session, parent=inspector)
        self.entity_prefab_panel.update_language(self.current_lang)
        self.vector_contour_panel = VectorContourPanel(
            session, project_path.parent, parent=inspector
        )
        self.vector_contour_panel.update_language(self.current_lang)
        self.asset_library.asset_selected.connect(
            self.vector_contour_panel.set_selected_asset
        )
        inspector_layout = inspector.layout()
        if not isinstance(inspector_layout, QVBoxLayout):
            raise RuntimeError("professional inspector has no vertical layout")
        # Keep independent tools out of the numeric inspector. Existing panels
        # retain their implementations, signals, history and persistence.
        if self.sequence_panel is not None:
            self.sequence_panel.stop()
        for old_dock in self.studio_docks:
            self.removeDockWidget(old_dock)
            old_dock.deleteLater()
        self.studio_docks = []
        self.layer_stack.status_message.connect(self._show_professional_status)
        self.group_stack.status_message.connect(self._show_professional_status)
        self.asset_library.status_message.connect(self._show_professional_status)
        self.tilemap_panel.status_message.connect(self._show_professional_status)
        self.tileset_panel.status_message.connect(self._show_professional_status)
        self.collider_panel.status_message.connect(self._show_professional_status)
        self.navmesh_panel.status_message.connect(self._show_professional_status)
        self.entity_prefab_panel.status_message.connect(self._show_professional_status)
        self.vector_contour_panel.status_message.connect(self._show_professional_status)
        inspector_scroll = QScrollArea(self.right_pages)
        inspector_scroll.setObjectName("professional_inspector_scroll")
        inspector_scroll.setWidgetResizable(True)
        inspector_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        inspector_scroll.setWidget(inspector)
        inspector.status_message.connect(self._show_professional_status)
        viewport.status_message.connect(self._show_professional_status)
        inspector.particle_preview_command.connect(
            lambda command: (
                viewport.play_particle_preview()
                if command == "play"
                else viewport.reset_particle_preview()
            )
        )
        inspector.request_fit.connect(viewport.fit_selection)
        inspector.request_fit_all.connect(viewport.fit_all)
        inspector.status_message.connect(lambda _message: viewport.sync())
        self.group_stack.asset_drop_requested.connect(
            lambda asset_id, group_id: viewport.place_asset_from_library(
                asset_id, group_id
            )
        )
        self.right_pages.addWidget(inspector_scroll)
        self.right_pages.setCurrentWidget(inspector_scroll)
        self.professional_pages.addWidget(viewport)
        self.professional_pages.setCurrentWidget(viewport)
        self.professional_session = session
        if mark_unsaved:
            session.mark_unsaved()
        self.professional_viewport = viewport
        self.professional_inspector = inspector
        self.professional_inspector_scroll = inspector_scroll
        self._professional_project = project_path
        self.professional_scene_path = scene_path
        self._build_studio_panels(
            session, viewport, inspector_scroll, project_path.parent
        )
        self._configure_professional_tab_order(viewport, inspector)
        session.subscribe(self._update_professional_status)
        session.subscribe(self._emit_document_changed)
        if document.objects:
            QTimer.singleShot(0, viewport.frame_loaded_content)

    def _ensure_hybrid_viewport(self) -> HybridSceneViewport | None:
        project_path = self._professional_project or self.authoring.project_path
        if project_path is None:
            return None
        scene_path = project_path.with_suffix(".hybrid3d.json")
        if self.hybrid_viewport is not None:
            if self.hybrid_viewport.scene_path == scene_path:
                return self.hybrid_viewport
            self.professional_pages.removeWidget(self.hybrid_viewport)
            self.hybrid_viewport.deleteLater()
            self.hybrid_viewport = None
        viewport = HybridSceneViewport(
            scene_path,
            language=self.current_lang,
            parent=self.professional_pages,
        )
        viewport.status_message.connect(self._show_professional_status)
        self.professional_pages.addWidget(viewport)
        self.hybrid_viewport = viewport
        return viewport

    def _build_studio_panels(self, session, viewport, inspector_scroll, project_root):
        pt = self.current_lang == "pt"

        def scroll_for(panel):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(panel)
            return scroll

        self.studio_library_tabs = QTabWidget()
        self.studio_library_tabs.setObjectName("scene_studio_library_tabs")
        for panel, title in (
            (self.layer_stack, "Molduras" if pt else "Frames"),
            (self.group_stack, "Hierarquia" if pt else "Hierarchy"),
            (self.asset_library, "Biblioteca" if pt else "Library"),
        ):
            self.studio_library_tabs.addTab(scroll_for(panel), title)
        dock = QDockWidget("Composição" if pt else "Composition", self)
        dock.setObjectName("scene_studio_composition_dock")
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        dock.setWidget(self.studio_library_tabs)
        dock.setMinimumWidth(270)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.studio_docks.append(dock)
        self.resizeDocks([dock], [290], Qt.Orientation.Horizontal)
        self.layer_stack.update_language(self.current_lang)
        self.group_stack.update_language(self.current_lang)
        self.layer_stack.active_layer_changed.connect(viewport.set_active_layer)
        self.layer_stack.active_layer_changed.connect(
            lambda layer_id: self.professional_inspector.layer_combo.setCurrentIndex(
                self.professional_inspector.layer_combo.findData(layer_id)
            )
        )

        def place(asset_id, layer_id):
            viewport.set_active_layer(layer_id)
            viewport.place_asset_from_library(asset_id)

        self.layer_stack.asset_drop_requested.connect(place)
        self.asset_library.asset_place_requested.connect(
            viewport.place_asset_from_library
        )
        self.sequence_panel = SceneSequencePanel(
            session,
            viewport,
            self.professional_pages,
            project_root,
            self.current_lang,
            self,
        )
        self.sequence_panel.status_message.connect(self._show_professional_status)
        self.studio_inspector_tabs = QTabWidget()
        self.studio_inspector_tabs.setObjectName("scene_studio_inspector_tabs")
        self.studio_inspector_tabs.addTab(
            self.sequence_panel.editor, "Clipe" if pt else "Clip"
        )
        advanced = QTabWidget()
        advanced.setTabPosition(QTabWidget.TabPosition.West)
        for panel, title in (
            (self.vector_contour_panel, "Formas" if pt else "Shapes"),
            (self.tileset_panel, "Tileset"),
            (self.tilemap_panel, "Tilemap"),
            (self.collider_panel, "Colisão" if pt else "Collision"),
            (self.navmesh_panel, "Navegação" if pt else "Navigation"),
            (self.entity_prefab_panel, "Entidades" if pt else "Entities"),
        ):
            advanced.addTab(scroll_for(panel), title)
        self.studio_inspector_tabs.addTab(advanced, "Ferramentas" if pt else "Tools")
        inspector_bridge = QWidget()
        inspector_bridge_layout = QVBoxLayout(inspector_bridge)
        inspector_bridge_layout.addWidget(
            QLabel(
                "O inspetor numérico permanece na página principal."
                if pt
                else "The numeric inspector remains on the main page."
            )
        )
        inspector_bridge_button = QPushButton(
            "Abrir inspetor" if pt else "Open inspector"
        )
        inspector_bridge_button.clicked.connect(
            lambda: self.right_pages.setCurrentWidget(inspector_scroll)
        )
        inspector_bridge_layout.addWidget(inspector_bridge_button)
        inspector_bridge_layout.addStretch(1)
        self.studio_inspector_tabs.insertTab(
            0, inspector_bridge, "Inspetor" if pt else "Inspector"
        )
        self.right_pages.addWidget(self.studio_inspector_tabs)
        # Preserve the initial inspector page contract while keeping the
        # integrated tabs available when a timeline clip is selected.
        self.right_pages.setCurrentWidget(inspector_scroll)
        self.sequence_panel.editor_requested.connect(
            lambda: (
                self.studio_inspector_tabs.setCurrentIndex(1),
                self.right_pages.setCurrentWidget(self.studio_inspector_tabs),
            )
        )
        timeline_dock = QDockWidget("Linha do tempo" if pt else "Timeline", self)
        timeline_dock.setObjectName("scene_studio_timeline_dock")
        timeline_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        timeline_dock.setWidget(self.sequence_panel)
        self.setCorner(
            Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setCorner(
            Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, timeline_dock)
        self.studio_docks.append(timeline_dock)
        self.resizeDocks([timeline_dock], [220], Qt.Orientation.Vertical)

    def _configure_professional_tab_order(
        self,
        viewport: SceneAuthoringViewport,
        inspector: SceneAuthoringInspector,
    ) -> None:
        """Keep keyboard navigation deterministic across the professional surface."""

        focus_chain = (
            viewport,
            inspector.fit_button,
            inspector.fit_all_button,
            inspector.apply_button,
            inspector.undo_button,
            inspector.redo_button,
            inspector.delete_button,
            inspector.position_x,
            inspector.position_y,
            inspector.position_z,
            inspector.rotation_x,
            inspector.rotation_y,
            inspector.rotation_z,
            inspector.scale_x,
            inspector.scale_y,
            inspector.scale_z,
            inspector.pivot_x,
            inspector.pivot_y,
            inspector.flip_x,
            inspector.flip_y,
            inspector.snap_enabled,
            inspector.snap_spacing_x,
            inspector.snap_spacing_y,
            inspector.camera_x,
            inspector.camera_y,
            inspector.camera_zoom,
            inspector.camera_apply_button,
            inspector.layer_combo,
            inspector.parallax_depth,
            inspector.parallax_translation,
            inspector.parallax_zoom,
            inspector.parallax_scroll_x,
            inspector.parallax_scroll_y,
            inspector.parallax_offset_x,
            inspector.parallax_offset_y,
            inspector.parallax_repeat_x,
            inspector.parallax_repeat_y,
            inspector.parallax_mirror_x,
            inspector.parallax_mirror_y,
            inspector.parallax_apply_button,
            inspector.socket_combo,
            inspector.socket_type,
            inspector.socket_id,
            inspector.socket_x,
            inspector.socket_y,
            inspector.socket_z,
            inspector.socket_rotation_z,
            inspector.socket_effect_id,
            inspector.socket_scale,
            inspector.socket_enabled,
            inspector.particle_emitter_combo,
            inspector.particle_emitter_id,
            inspector.particle_seed,
            inspector.particle_emission_rate,
            inspector.particle_lifetime,
            inspector.particle_max_particles,
            inspector.particle_burst_count,
            inspector.particle_velocity_x,
            inspector.particle_velocity_y,
            inspector.particle_spread_x,
            inspector.particle_spread_y,
            inspector.particle_acceleration_x,
            inspector.particle_acceleration_y,
            inspector.particle_loop,
            inspector.particle_duration,
            inspector.add_emitter_button,
            inspector.remove_emitter_button,
            inspector.particle_preview_button,
            inspector.particle_reset_button,
            inspector.add_socket_button,
            inspector.update_socket_button,
            inspector.remove_socket_button,
        )
        for previous, current in zip(focus_chain, focus_chain[1:]):
            self.setTabOrder(previous, current)
        self.setTabOrder(focus_chain[-1], focus_chain[0])

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if (
            self.professional_viewport is not None
            and not self._professional_initial_focus_applied
        ):
            self.professional_viewport.setFocus(Qt.FocusReason.OtherFocusReason)
            self._professional_initial_focus_applied = True

    def _emit_document_changed(self) -> None:
        self.document_changed.emit()

    def _upgrade_professional(self) -> bool:
        if self._pending_v1_document is None:
            self.status_label.setText("No V1 scenario is waiting for upgrade")
            return False
        answer = QMessageBox.question(
            self,
            "Upgrade scenario schema",
            "Upgrade this V1 scenario to V2 in memory? "
            "The V1 file will remain unchanged until you save.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        candidate = self._pending_v1_document
        upgraded = upgrade_scene_authoring_document(candidate)
        self._build_professional_viewport(upgraded, mark_unsaved=True)
        self.status_label.setText("Scenario upgraded to V2 — save to persist")
        return True

    def _recover_professional(self) -> bool:
        if self.professional_scene_path is None or self._pending_recovery_path is None:
            self.status_label.setText("No recoverable scenario is available")
            return False
        try:
            candidate = load_scene_authoring_recovery(
                self.professional_scene_path, verify_assets=False
            )
        except (OSError, ValueError, ProjectPersistenceError) as exc:
            self.status_label.setText(
                "Scenario recovery failed: "
                + user_error_message(
                    exc, operation="recovery", language=self.current_lang
                )
            )
            return False
        if isinstance(candidate, SceneAuthoringDocumentV1):
            self._pending_v1_document = candidate
            self._pending_recovery_path = None
            self._show_pending_document(
                "Recovered V1 scenario is ready. Choose Upgrade V1 to V2; "
                "the recovered file will not replace the damaged file until Save."
            )
            self.status_label.setText(
                "Recovered V1 scenario — explicit upgrade required"
            )
            return True
        self._build_professional_viewport(candidate, mark_unsaved=True)
        self.status_label.setText(
            "Last valid scenario recovered — save to replace the damaged file"
        )
        return True

    def _save_professional(self) -> bool:
        if self.professional_session is None or self.professional_scene_path is None:
            self.status_label.setText("Create a scenario before saving")
            return False
        if self._temporary_project_path is not None:
            return self._save_new_project_as()
        try:
            save_scene_authoring(
                self.professional_session.document, self.professional_scene_path
            )
            self.professional_session.mark_saved()
            self.status_label.setText(
                "Cenário salvo" if self.current_lang == "pt" else "Scenario saved"
            )
            return True
        except (OSError, ValueError, ProjectPersistenceError) as exc:
            self.status_label.setText(
                "Scenario save failed: "
                + user_error_message(exc, operation="save", language=self.current_lang)
            )
            return False

    def _load_professional(self) -> bool:
        if self.professional_session is None or self.professional_scene_path is None:
            self.status_label.setText("Save a project before reloading the scenario")
            return False
        if not self.professional_scene_path.is_file():
            self.status_label.setText("No saved scenario exists yet")
            return False
        try:
            document = self._load_professional_document(self.professional_scene_path)
            self.professional_session.model.document = document
            self.professional_session.clear_isolation()
            self.professional_session.clear_history()
            self.professional_session.clear_selection()
            self.professional_session.mark_saved()
            if self.professional_viewport is not None:
                self.professional_viewport.sync()
            self.status_label.setText(
                "Cenário recarregado"
                if self.current_lang == "pt"
                else "Scenario reloaded"
            )
            return True
        except (
            OSError,
            ValueError,
            SceneAuthoringFormatError,
            SceneAuthoringReadError,
            SceneAuthoringValidationError,
        ) as exc:
            try:
                candidate = load_scene_authoring(
                    self.professional_scene_path, verify_assets=False
                )
            except (
                OSError,
                ValueError,
                SceneAuthoringFormatError,
                SceneAuthoringReadError,
                SceneAuthoringValidationError,
            ):
                recovery = scene_authoring_recovery_path(self.professional_scene_path)
                failure_status = (
                    "Scenario reload failed: "
                    + user_error_message(
                        exc, operation="reload", language=self.current_lang
                    )
                    + " "
                    + (
                        "Use Recover Last Valid."
                        if recovery.is_file()
                        else "Repair the saved scenario before reloading."
                    )
                )
                self._pending_recovery_path = recovery if recovery.is_file() else None
                recovery_hint = (
                    "Use Recuperar Último Válido\n"
                    "para restaurar a última cópia válida."
                    if self.current_lang == "pt"
                    else "Use Recover Last Valid\n" "to restore the last valid copy."
                )
                repair_hint = (
                    "Corrija o arquivo do cenário\nantes de recarregar."
                    if self.current_lang == "pt"
                    else "Repair the scenario file\nbefore reloading."
                )
                self._show_pending_document(
                    (
                        "O cenário salvo não pôde ser recarregado.\n\n"
                        if self.current_lang == "pt"
                        else "The saved scenario could not be reloaded.\n\n"
                    )
                    + (recovery_hint if self._pending_recovery_path else repair_hint)
                )
                self.refresh()
                self.status_label.setText(failure_status)
                return False
            if isinstance(candidate, SceneAuthoringDocumentV1):
                self._pending_v1_document = candidate
                self.status_label.setText(
                    "Scenario reload requires explicit V1 upgrade; "
                    "the saved V1 file remains unchanged."
                )
                self.refresh()
                return False
            self.status_label.setText(
                "Scenario reload failed: "
                + user_error_message(
                    exc, operation="reload", language=self.current_lang
                )
            )
            return False

    def _reset_professional(self, *, confirm: bool = True) -> bool:
        if self._professional_project is None or self.professional_session is None:
            self.status_label.setText("Save a project before resetting the scenario")
            return False
        if confirm and self.professional_session.is_dirty:
            answer = QMessageBox.question(
                self,
                "Reset scenario",
                "Discard unsaved professional scenario changes?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False
        document = upgrade_scene_authoring_document(
            professional_document_from_scene(self.scene, self._professional_project)
        )
        self.professional_session.model.document = document
        self.professional_session.clear_isolation()
        self.professional_session.clear_history()
        self.professional_session.clear_selection()
        if self.professional_viewport is not None:
            self.professional_viewport.sync()
        self.status_label.setText("Scenario reset from project")
        return True

    def _export_professional(self) -> bool:
        if self.professional_session is None or self._professional_project is None:
            self.status_label.setText("Save a project before exporting the scenario")
            return False
        target_value = self.export_target_combo.currentData()
        target: SceneExportTarget = (
            target_value if target_value in {"generic", "godot", "unity"} else "generic"
        )
        destination = self._professional_project.with_suffix(
            ".ndtscene.runtime.json"
            if target == "generic"
            else f".ndtscene.{target}.runtime.json"
        )
        try:
            save_scene_authoring_export(
                upgrade_scene_authoring_document(self.professional_session.document),
                destination,
                target=target,
                source_document_path=self.professional_scene_path,
            )
            self.status_label.setText(
                f"Scenario {target} export written from active document: "
                f"{destination.name}"
            )
            return True
        except (OSError, ValueError, ProjectPersistenceError) as exc:
            self.status_label.setText(
                "Scenario export failed: "
                + user_error_message(
                    exc, operation="export", language=self.current_lang
                )
            )
            return False

    def _export_composition(self) -> bool:
        """Export one validated package for the complete authored composition."""

        if self.professional_session is None or self._professional_project is None:
            self.status_label.setText("Save a project before exporting the composition")
            return False
        scene_path = self.professional_scene_path
        project_root = self._professional_project.parent
        if scene_path is None or not scene_path.is_file():
            self.status_label.setText(
                "Save the scenario before exporting the composition"
            )
            return False
        runtime_bundle = project_root / "assets" / "runtime" / "adapters.json"
        inputs = CompositionInputs(
            scene=scene_path,
            tilemap=project_root / "assets" / "tilemaps" / "scenario.tilemap.json",
            colliders=project_root / "assets" / "colliders" / "scenario.colliders.json",
            navmesh=project_root / "assets" / "navmesh" / "scenario.navmesh.json",
            runtime_bundle=runtime_bundle if runtime_bundle.is_file() else None,
            auto_tilemap_runtime=True,
        )
        exports_root = project_root / "exports"
        exports_root.mkdir(parents=True, exist_ok=True)
        destination = exports_root / "composition-e11"
        suffix = 2
        while destination.exists():
            destination = exports_root / f"composition-e11-r{suffix}"
            suffix += 1
        try:
            manifest = build_composition_package(inputs, destination)
        except (CompositionExportError, OSError, ValueError) as exc:
            self.status_label.setText(
                "Composition export failed: "
                + user_error_message(
                    exc, operation="export", language=self.current_lang
                )
            )
            return False
        runtime_note = (
            " + runtime adapters"
            if any(
                item["kind"] == "runtime-adapters" for item in manifest["components"]
            )
            else ""
        )
        self.status_label.setText(
            "Composition exported ("
            f"{len(manifest['components'])} components{runtime_note}): "
            f"{destination.name}"
        )
        return True

    def _update_professional_status(self) -> None:
        if self.professional_session is None:
            return
        mode_status = (
            "Prévia do cenário — somente leitura"
            if self.preview_action.isChecked()
            else "Autoria de cenário"
        )
        if self.current_lang != "pt":
            mode_status = (
                "Scenario preview — read-only"
                if self.preview_action.isChecked()
                else "Scenario authoring"
            )
        suffix = (
            " — alterações não salvas"
            if self.current_lang == "pt" and self.professional_session.is_dirty
            else " — unsaved changes" if self.professional_session.is_dirty else ""
        )
        self.status_label.setText(mode_status + suffix)

    def _show_professional_status(self, message: str) -> None:
        suffix = ""
        if (
            self.professional_session is not None
            and self.professional_session.is_dirty
            and "unsaved" not in message.lower()
        ):
            suffix = (
                " — alterações não salvas"
                if self.current_lang == "pt"
                else " — unsaved changes"
            )
        self.status_label.setText(message + suffix)

    def _open_project_hint(self) -> None:
        self.status_label.setText(
            (
                "Abra e salve um projeto no editor principal antes de editar um "
                "cenário, ou escolha Novo Cenário para começar sem um projeto."
                if self.current_lang == "pt"
                else "Open and save a project in the main editor before authoring "
                "a scenario, or choose New Scenario to start without one."
            )
        )

    def _new_professional(self) -> bool:
        """Start an editable professional scene without requiring a project file."""

        if self.professional_session is not None and self.professional_session.is_dirty:
            answer = QMessageBox.question(
                self,
                "Novo cenário" if self.current_lang == "pt" else "New scene",
                (
                    "Descartar alterações não salvas do cenário atual?"
                    if self.current_lang == "pt"
                    else "Discard unsaved changes in the current scene?"
                ),
                QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Discard:
                return False
        try:
            if self.sequence_panel is not None:
                self.sequence_panel.stop()
            if self._temporary_project_dir is not None:
                self._temporary_project_dir.cleanup()
            self._temporary_project_dir = tempfile.TemporaryDirectory(
                prefix="neoeng-d-trace-scenario-"
            )
            project_path = Path(self._temporary_project_dir.name) / "Untitled.ndtproj"
            from src.models.scene import Scene

            empty_scene = Scene()
            empty_scene.save_project(str(project_path))
            document = professional_document_from_scene(empty_scene, project_path)
            document = document.model_copy(
                update={
                    "layers": [
                        SceneLayerAuthoringRecord(id=key, name=name)
                        for key, name in zip(
                            ("background", "midground", "foreground"),
                            (
                                ("Fundo", "Meio", "Frente")
                                if self.current_lang == "pt"
                                else ("Background", "Midground", "Foreground")
                            ),
                        )
                    ],
                    "parallax_layers": [
                        SceneParallaxLayerRecord(
                            layer_id=key, depth=depth, scroll_x=ratio, scroll_y=ratio
                        )
                        for key, depth, ratio in (
                            ("background", 0.8, 0.2),
                            ("midground", 0.4, 0.6),
                            ("foreground", 0.0, 1.0),
                        )
                    ],
                }
            )
            self._temporary_project_path = project_path
            self.authoring.bind_project(project_path)
            self._build_professional_viewport(document=document, mark_unsaved=True)
            self._set_editor_mode(preview=False)
            self.refresh()
            self.status_label.setText(
                (
                    "Novo cenário não salvo — use Salvar Projeto para escolher o local"
                    if self.current_lang == "pt"
                    else "New unsaved scenario — use Save Project to choose a location"
                )
            )
            return True
        except (OSError, ValueError, ProjectPersistenceError) as exc:
            self.status_label.setText(
                (
                    "Falha ao criar cenário: "
                    if self.current_lang == "pt"
                    else "New scenario failed: "
                )
                + user_error_message(exc, operation="save", language=self.current_lang)
            )
            return False

    def _save_new_project_as(self) -> bool:
        """Persist a newly authored scene and its professional sidecar."""

        if self.professional_session is None:
            self.status_label.setText(
                "Crie um cenário antes de salvar"
                if self.current_lang == "pt"
                else "Create a scenario before saving"
            )
            return False
        path_text, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Projeto Como" if self.current_lang == "pt" else "Save Project As",
            "SemNome.ndtproj" if self.current_lang == "pt" else "Untitled.ndtproj",
            (
                "Projeto NeoEng (*.ndtproj)"
                if self.current_lang == "pt"
                else "NeoEng project (*.ndtproj)"
            ),
        )
        if not path_text:
            return False
        destination = Path(path_text)
        if destination.suffix.lower() != ".ndtproj":
            destination = destination.with_suffix(".ndtproj")
        try:
            document = self.professional_session.document
            source_root = self._professional_project.parent
            relocated_assets = []
            for asset in document.assets:
                source, issue = resolve_scene_asset(asset, source_root)
                if source is None:
                    raise ValueError(issue)
                prepared = prepare_scene_asset(
                    source, destination.parent, allow_audio=True
                )
                relocated_assets.append(
                    asset.model_copy(
                        update={"path": prepared.path, "sha256": prepared.sha256}
                    )
                )
            document = document.model_copy(update={"assets": relocated_assets})
            self.scene.save_project(str(destination))
            if isinstance(document, SceneAuthoringDocumentV2):
                document = document.model_copy(
                    update={"project": project_reference_for(destination)}
                )
            scene_path = destination.with_suffix(".ndtscene.json")
            save_scene_authoring(document, scene_path)
            self.authoring.bind_project(destination)
            self._temporary_project_path = None
            self._build_professional_viewport(document=document)
            self.professional_scene_path = scene_path
            self.status_label.setText(
                (
                    f"Projeto salvo: {destination.name}"
                    if self.current_lang == "pt"
                    else f"Project saved: {destination.name}"
                )
            )
            return True
        except (OSError, ValueError, ProjectPersistenceError) as exc:
            self.status_label.setText(
                (
                    "Falha ao salvar projeto: "
                    if self.current_lang == "pt"
                    else "Project save failed: "
                )
                + user_error_message(exc, operation="save", language=self.current_lang)
            )
            return False

    def _toggle_overlays(self) -> None:
        if self.professional_viewport is not None:
            self.professional_viewport.set_overlay_visible(
                self.overlay_action.isChecked()
            )

    def _toggle_professional_preview(self) -> None:
        self._set_editor_mode(preview=True)

    def _toggle_professional_authoring(self) -> None:
        self._set_editor_mode(preview=False)

    def _toggle_hybrid_view(self) -> None:
        if self.hybrid_action.isChecked():
            viewport = self._ensure_hybrid_viewport()
            if viewport is None:
                self.hybrid_action.blockSignals(True)
                self.hybrid_action.setChecked(False)
                self.hybrid_action.blockSignals(False)
                self.status_label.setText(
                    "Abra ou crie um projeto antes do viewport 3D"
                    if self.current_lang == "pt"
                    else "Open or create a project before using the 3D viewport"
                )
                return
            self.professional_pages.setCurrentWidget(viewport)
            self.status_label.setText(
                "Viewport 3D/híbrido — alterações salvas no sidecar"
                if self.current_lang == "pt"
                else "3D/hybrid viewport — changes are saved in a sidecar"
            )
            return
        if self.professional_viewport is not None:
            self.professional_pages.setCurrentWidget(self.professional_viewport)
            self.status_label.setText(
                "Viewport 2D profissional"
                if self.current_lang == "pt"
                else "Professional 2D viewport"
            )

    def _set_editor_mode(self, *, preview: bool) -> None:
        self.preview_action.setChecked(preview)
        self.authoring_action.setChecked(not preview)
        if self.professional_viewport is not None:
            self.professional_viewport.set_preview_enabled(preview)
            self.professional_viewport.set_authoring_enabled(not preview)
        if self.professional_inspector is not None:
            self.professional_inspector.setEnabled(not preview)
        if self.tilemap_panel is not None:
            self.tilemap_panel.setEnabled(not preview)
        if self.tileset_panel is not None:
            self.tileset_panel.setEnabled(not preview)
        if self.collider_panel is not None:
            self.collider_panel.setEnabled(not preview)
        if self.entity_prefab_panel is not None:
            self.entity_prefab_panel.setEnabled(not preview)
        if self.vector_contour_panel is not None:
            self.vector_contour_panel.setEnabled(not preview)
        self.status_label.setText(
            ("Prévia do cenário — somente leitura" if preview else "Autoria de cenário")
            if self.current_lang == "pt"
            else ("Scenario preview — read-only" if preview else "Scenario authoring")
        )

    def _undo_professional(self) -> None:
        if self.professional_viewport is not None and self.professional_viewport.undo():
            self.status_label.setText("Undo applied")

    def _redo_professional(self) -> None:
        if self.professional_viewport is not None and self.professional_viewport.redo():
            self.status_label.setText("Redo applied")

    def refresh(self) -> None:
        available = self.authoring.is_available
        if available and self._professional_project != self.authoring.project_path:
            self._build_professional_viewport()
        ready = available and self.professional_session is not None
        self.save_action.setEnabled(ready)
        self.load_action.setEnabled(ready)
        self.reset_action.setEnabled(ready)
        self.export_action.setEnabled(ready)
        self.composition_action.setEnabled(ready)
        self.export_target_combo.setEnabled(ready)
        self.upgrade_action.setEnabled(self._pending_v1_document is not None)
        self.recover_action.setEnabled(self._pending_recovery_path is not None)
        self.overlay_action.setEnabled(available)
        self.preview_action.setEnabled(available)
        self.authoring_action.setEnabled(available)
        self.hybrid_action.setEnabled(available)
        if not available and self.hybrid_action.isChecked():
            self.hybrid_action.blockSignals(True)
            self.hybrid_action.setChecked(False)
            self.hybrid_action.blockSignals(False)
        if self.professional_inspector is not None:
            self.professional_inspector.setEnabled(
                available and not self.preview_action.isChecked()
            )
        if self.tilemap_panel is not None:
            self.tilemap_panel.setEnabled(
                available and not self.preview_action.isChecked()
            )
        if self.tileset_panel is not None:
            self.tileset_panel.setEnabled(
                available and not self.preview_action.isChecked()
            )
        if self.collider_panel is not None:
            self.collider_panel.setEnabled(
                available and not self.preview_action.isChecked()
            )
        if self.entity_prefab_panel is not None:
            self.entity_prefab_panel.setEnabled(
                available and not self.preview_action.isChecked()
            )
        if self.vector_contour_panel is not None:
            self.vector_contour_panel.setEnabled(
                available and not self.preview_action.isChecked()
            )
        session = self.professional_session
        self.undo_action.setEnabled(session is not None and session.can_undo)
        self.redo_action.setEnabled(session is not None and session.can_redo)
        render_plan = None
        if (
            available
            and self.professional_session is None
            and (
                self._pending_v1_document is not None
                or self._pending_recovery_path is not None
            )
        ):
            self.canvas.set_scenario_preview_layers(())
            self.status_label.setText(
                "O cenário requer migração ou recuperação"
                if self.current_lang == "pt"
                else "Scenario requires migration or recovery action"
            )
        elif available:
            self.canvas.set_scenario_preview_layers(self.authoring.preview_layers())
            self.canvas.set_scenario_camera(
                self.authoring.preview_camera(
                    (float(self.canvas.width()), float(self.canvas.height()))
                )
            )
            if self.professional_session is not None and isinstance(
                self.professional_session.document, SceneAuthoringDocumentV2
            ):
                render_plan = build_scene_render_plan(
                    self.professional_session.document,
                    (
                        (
                            max(1, self.professional_viewport.width())
                            if self.professional_viewport is not None
                            else max(1, self.canvas.width())
                        ),
                        (
                            max(1, self.professional_viewport.height())
                            if self.professional_viewport is not None
                            else max(1, self.canvas.height())
                        ),
                    ),
                )
                self.canvas.set_scenario_render_plan(render_plan)
            else:
                self.canvas.set_scenario_render_plan(None)
            mode_status = (
                "Prévia do cenário — somente leitura"
                if self.preview_action.isChecked()
                else "Autoria de cenário"
            )
            if self.current_lang != "pt":
                mode_status = (
                    "Scenario preview — read-only"
                    if self.preview_action.isChecked()
                    else "Scenario authoring"
                )
            session_dirty = (
                self.professional_session.is_dirty
                if self.professional_session is not None
                else False
            )
            self.status_label.setText(
                mode_status
                + (
                    " — alterações não salvas"
                    if self.current_lang == "pt" and session_dirty
                    else " — unsaved changes" if session_dirty else ""
                )
            )
        else:
            self.canvas.set_scenario_preview_layers(())
            self.status_label.setText(
                "Escolha Novo Cenário para começar a autoria"
                if self.current_lang == "pt"
                else "Choose New Scenario to begin authoring"
            )
        if self.professional_viewport is not None:
            self.professional_viewport.set_scene_render_plan(render_plan)
        self.canvas.update()

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.professional_empty.setText(
                "Viewport profissional de cenários\n\n"
                "Escolha Novo Cenário para começar em uma cena vazia ou abra um "
                "projeto salvo."
            )
            self.professional_inspector_empty.setText(
                "Nenhuma cena selecionada.\n\n"
                "Escolha Novo Cenário ou abra um projeto para preencher o inspetor."
            )
        else:
            self.professional_empty.setText(
                "Professional scene viewport\n\n"
                "Choose New Scenario to start from an empty scene, or load a saved "
                "project."
            )
            self.professional_inspector_empty.setText(
                "No scene selected yet.\n\n"
                "Choose New Scenario or open a project to populate the inspector."
            )
        self.setProperty("language", self.current_lang)
        if self.sequence_panel is not None:
            self.sequence_panel.update_language(self.current_lang)
        if hasattr(self, "studio_library_tabs"):
            for index, label in enumerate(
                ("Molduras", "Hierarquia", "Biblioteca")
                if self.current_lang == "pt"
                else ("Frames", "Hierarchy", "Library")
            ):
                self.studio_library_tabs.setTabText(index, label)
            for index, label in enumerate(
                ("Inspetor", "Clipe", "Ferramentas")
                if self.current_lang == "pt"
                else ("Inspector", "Clip", "Tools")
            ):
                self.studio_inspector_tabs.setTabText(index, label)
        if self.current_lang == "pt":
            self.setWindowTitle("Editor de Cenário — NeoEng-D-Trace")
            labels = (
                "Novo Cenário",
                "Salvar Projeto",
                "Salvar",
                "Recarregar",
                "Redefinir",
                "Exportar Runtime",
                "Exportar Composição",
                "Atualizar V1 para V2",
                "Recuperar Último Válido",
                "Desfazer",
                "Refazer",
                "Sobreposições",
                "Pré-visualização de Paralaxe",
                "Autoria",
                "Viewport 3D/Híbrido",
            )
        else:
            self.setWindowTitle("Scenario Editor — NeoEng-D-Trace")
            labels = (
                "New Scenario",
                "Save Project",
                "Save",
                "Reload",
                "Reset",
                "Export Runtime",
                "Export Composition",
                "Upgrade V1 to V2",
                "Recover Last Valid",
                "Undo",
                "Redo",
                "Overlays",
                "Parallax Preview",
                "Authoring",
                "3D/Hybrid Viewport",
            )
        tooltips = (
            (
                "Novo Cenário",
                "Salvar Projeto Como",
                "Salvar Cenário",
                "Recarregar Cenário",
                "Redefinir Cenário",
                "Exportar Runtime",
                "Exportar Composição",
                "Atualizar V1 para V2",
                "Recuperar Último Válido",
                "Desfazer",
                "Refazer",
                "Sobreposições",
                "Pré-visualização de Paralaxe",
                "Autoria",
                "Viewport 3D/Híbrido",
            )
            if self.current_lang == "pt"
            else (
                "New Scenario",
                "Save Project As",
                "Save Scenario",
                "Reload Scenario",
                "Reset Scenario",
                "Export Runtime",
                "Export Composition",
                "Upgrade V1 to V2",
                "Recover Last Valid",
                "Undo",
                "Redo",
                "Overlays",
                "Parallax Preview",
                "Authoring",
                "3D/Hybrid Viewport",
            )
        )
        for action, label in zip(
            (
                self.open_action,
                self.save_project_action,
                self.save_action,
                self.load_action,
                self.reset_action,
                self.export_action,
                self.composition_action,
                self.upgrade_action,
                self.recover_action,
                self.undo_action,
                self.redo_action,
                self.overlay_action,
                self.preview_action,
                self.authoring_action,
                self.hybrid_action,
            ),
            labels,
        ):
            action.setText(label)
        for action, tooltip in zip(
            (
                self.open_action,
                self.save_project_action,
                self.save_action,
                self.load_action,
                self.reset_action,
                self.export_action,
                self.composition_action,
                self.upgrade_action,
                self.recover_action,
                self.undo_action,
                self.redo_action,
                self.overlay_action,
                self.preview_action,
                self.authoring_action,
                self.hybrid_action,
            ),
            tooltips,
        ):
            action.setToolTip(tooltip)
        menu_labels = (
            ("export", "Exportar" if self.current_lang == "pt" else "Export"),
            ("edit", "Editar" if self.current_lang == "pt" else "Edit"),
            (
                "view",
                "Ver" if self.current_lang == "pt" else "View",
            ),
            ("more", "Mais" if self.current_lang == "pt" else "More"),
        )
        for key, label in menu_labels:
            button = self._toolbar_menu_buttons.get(key)
            if button is not None:
                button.setText(label)
                button.setToolTip(label)
                button.setAccessibleName(label)
        self.export_target_label.setText(
            "Alvo:" if self.current_lang == "pt" else "Target:"
        )
        self.export_target_combo.setItemText(
            0, "Genérico" if self.current_lang == "pt" else "Generic"
        )
        self.export_target_combo.setItemText(1, "Godot 4.7")
        self.export_target_combo.setItemText(2, "Unity 6000.5.7f1")
        self.scenario_panel.update_language(self.current_lang)
        if self.professional_viewport is not None:
            self.professional_viewport.update_language(self.current_lang)
        if self.hybrid_viewport is not None:
            self.hybrid_viewport.update_language(self.current_lang)
        if self.professional_inspector is not None:
            self.professional_inspector.update_language(self.current_lang)
        if self.layer_stack is not None:
            self.layer_stack.setProperty("language", self.current_lang)
            self.layer_stack.update_language(self.current_lang)
        if self.group_stack is not None:
            self.group_stack.setProperty("language", self.current_lang)
            self.group_stack.update_language(self.current_lang)
        if self.asset_library is not None:
            self.asset_library.update_language(self.current_lang)
        if self.tilemap_panel is not None:
            self.tilemap_panel.update_language(self.current_lang)
        if self.tileset_panel is not None:
            self.tileset_panel.update_language(self.current_lang)
        if self.collider_panel is not None:
            self.collider_panel.update_language(self.current_lang)
        if self.entity_prefab_panel is not None:
            self.entity_prefab_panel.update_language(self.current_lang)
        if self.vector_contour_panel is not None:
            self.vector_contour_panel.update_language(self.current_lang)
        self.refresh()

    def closeEvent(self, event) -> None:
        if self.sequence_panel is not None:
            self.sequence_panel.stop()
        self._professional_initial_focus_applied = False
        if self.professional_session is not None and self.professional_session.is_dirty:
            self.status_label.setText("Unsaved scenario changes preserved")
        self.hide()
        event.ignore()
