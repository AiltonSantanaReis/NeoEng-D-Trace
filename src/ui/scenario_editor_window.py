"""Dedicated scenario authoring window.

The main image editor remains focused on image, polygon and collision work.
Scenario authoring is hosted here so its layer stack and inspector cannot
compress or intercept the main editor panels.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_authoring_bridge import professional_document_from_scene
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.exporters.scene_authoring_export import (
    SceneExportTarget,
    save_scene_authoring_export,
)
from src.persistence.errors import ProjectPersistenceError
from src.persistence.p2d05_errors import user_error_message
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
    upgrade_scene_authoring_document,
)
from src.ui.scenario_panel import ScenarioPanel
from src.ui.scene_asset_panel import SceneAssetLibrary
from src.ui.scene_authoring_group_stack import SceneAuthoringGroupStack
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_layer_stack import SceneAuthoringLayerStack
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


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
        self.professional_viewport: SceneAuthoringViewport | None = None
        self._professional_initial_focus_applied = False
        self.professional_inspector: SceneAuthoringInspector | None = None
        self.professional_inspector_scroll: QScrollArea | None = None
        self._professional_project: Path | None = None
        self.professional_scene_path: Path | None = None
        self.layer_stack: SceneAuthoringLayerStack | None = None
        self.group_stack: SceneAuthoringGroupStack | None = None
        self.asset_library: SceneAssetLibrary | None = None
        self._pending_v1_document: SceneAuthoringDocumentV1 | None = None
        self._pending_recovery_path: Path | None = None
        self.canvas = self._build_canvas()
        self.legacy_canvas = self.canvas
        self.professional_pages = QStackedWidget(self)
        self.professional_pages.setObjectName("professional_viewport_pages")
        self.professional_empty = QLabel(self.professional_pages)
        self.professional_empty.setObjectName("professional_scene_viewport_empty")
        self.professional_empty.setWordWrap(True)
        self.professional_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.professional_empty.setText(
            "Professional scene viewport\n\n" "Load a saved project to begin authoring."
        )
        self.professional_pages.addWidget(self.professional_empty)
        self.professional_pages.addWidget(self.canvas)
        self.professional_pages.setCurrentWidget(self.professional_empty)
        self.scenario_panel = ScenarioPanel(authoring, scene, self)
        self.scenario_panel.setMinimumWidth(390)
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
            "Save a project to enable the professional scene inspector.\n\n"
            "Drag image assets into the viewport after the project is loaded."
        )
        empty_layout.addStretch(1)
        empty_layout.addWidget(empty_label)
        empty_layout.addStretch(1)
        self.right_pages.addWidget(empty_panel)
        self.right_pages.addWidget(scroll)
        self.right_pages.setCurrentWidget(empty_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("scenario_editor_splitter")
        splitter.addWidget(self.professional_pages)
        splitter.addWidget(self.right_pages)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([850, 430])
        self.setCentralWidget(splitter)

        self.toolbar = QToolBar("Scenario", self)
        self.toolbar.setObjectName("scenario_editor_toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.open_action = QAction(self)
        self.save_action = QAction(self)
        self.load_action = QAction(self)
        self.reset_action = QAction(self)
        self.export_action = QAction(self)
        self.undo_action = QAction(self)
        self.redo_action = QAction(self)
        self.overlay_action = QAction(self)
        self.preview_action = QAction(self)
        self.authoring_action = QAction(self)
        self.upgrade_action = QAction(self)
        self.recover_action = QAction(self)
        self.export_target_label = QLabel(self.toolbar)
        self.export_target_label.setObjectName("scenario_export_target_label")
        self.export_target_combo = QComboBox(self.toolbar)
        self.export_target_combo.setObjectName("scenario_export_target_combo")
        self.export_target_combo.addItem("Generic", "generic")
        self.export_target_combo.addItem("Godot 4.7", "godot")
        self.export_target_combo.addItem("Unity 6000.5.7f1", "unity")
        self.overlay_action.setCheckable(True)
        self.preview_action.setCheckable(True)
        self.authoring_action.setCheckable(True)
        self.preview_action.setChecked(False)
        self.authoring_action.setChecked(True)
        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addAction(self.authoring_action)
        self.mode_group.addAction(self.preview_action)
        for action in (
            self.open_action,
            self.save_action,
            self.load_action,
            self.reset_action,
            self.export_action,
            self.undo_action,
            self.redo_action,
            self.overlay_action,
            self.preview_action,
            self.authoring_action,
        ):
            self.toolbar.addAction(action)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.export_target_label)
        self.toolbar.addWidget(self.export_target_combo)
        self.toolbar.addAction(self.upgrade_action)
        self.toolbar.addAction(self.recover_action)
        self.status_label = QLabel(self)
        self.status_label.setObjectName("scenario_editor_status_label")
        self.statusBar().setObjectName("scenario_editor_status_bar")
        self.statusBar().addPermanentWidget(self.status_label)

        self.open_action.triggered.connect(self._open_project_hint)
        self.undo_action.triggered.connect(self._undo_professional)
        self.redo_action.triggered.connect(self._redo_professional)
        self.save_action.triggered.connect(self._save_professional)
        self.load_action.triggered.connect(self._load_professional)
        self.reset_action.triggered.connect(self._reset_professional)
        self.export_action.triggered.connect(self._export_professional)
        self.upgrade_action.triggered.connect(self._upgrade_professional)
        self.recover_action.triggered.connect(self._recover_professional)
        self.overlay_action.triggered.connect(self._toggle_overlays)
        self.preview_action.triggered.connect(self._toggle_professional_preview)
        self.authoring_action.triggered.connect(self._toggle_professional_authoring)
        self.authoring.subscribe(self.refresh)
        self.update_language(language)
        self.refresh()

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
        self.layer_stack = SceneAuthoringLayerStack(session)
        self.group_stack = SceneAuthoringGroupStack(session)
        self.asset_library = SceneAssetLibrary(
            session, project_path.parent, parent=inspector
        )
        self.asset_library.update_language(self.current_lang)
        inspector_layout = inspector.layout()
        if not isinstance(inspector_layout, QVBoxLayout):
            raise RuntimeError("professional inspector has no vertical layout")
        inspector_layout.insertWidget(0, self.layer_stack)
        inspector_layout.insertWidget(0, self.group_stack)
        inspector_layout.insertWidget(0, self.asset_library)
        self.layer_stack.status_message.connect(self._show_professional_status)
        self.group_stack.status_message.connect(self._show_professional_status)
        self.asset_library.status_message.connect(self._show_professional_status)
        inspector_scroll = QScrollArea(self.right_pages)
        inspector_scroll.setObjectName("professional_inspector_scroll")
        inspector_scroll.setWidgetResizable(True)
        inspector_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        inspector_scroll.setWidget(inspector)
        inspector.status_message.connect(self._show_professional_status)
        viewport.status_message.connect(self._show_professional_status)
        inspector.request_fit.connect(viewport.fit_selection)
        inspector.request_fit_all.connect(viewport.fit_all)
        inspector.status_message.connect(lambda _message: viewport.sync())
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
        self._configure_professional_tab_order(viewport, inspector)
        session.subscribe(self._update_professional_status)
        session.subscribe(self._emit_document_changed)

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
            inspector.parallax_apply_button,
            inspector.socket_combo,
            inspector.socket_type,
            inspector.socket_id,
            inspector.socket_x,
            inspector.socket_y,
            inspector.socket_z,
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
            self.status_label.setText("Save a project before saving the scenario")
            return False
        try:
            save_scene_authoring(
                self.professional_session.document, self.professional_scene_path
            )
            self.professional_session.mark_saved()
            self.status_label.setText("Scenario saved")
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
            self.status_label.setText("Scenario reloaded")
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
                self.status_label.setText(
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
                self.refresh()
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

    def _update_professional_status(self) -> None:
        if self.professional_session is None:
            return
        mode_status = (
            "Scenario preview — read-only"
            if self.preview_action.isChecked()
            else "Scenario authoring"
        )
        suffix = " — unsaved changes" if self.professional_session.is_dirty else ""
        self.status_label.setText(mode_status + suffix)

    def _show_professional_status(self, message: str) -> None:
        suffix = ""
        if (
            self.professional_session is not None
            and self.professional_session.is_dirty
            and "unsaved" not in message.lower()
        ):
            suffix = " — unsaved changes"
        self.status_label.setText(message + suffix)

    def _open_project_hint(self) -> None:
        self.status_label.setText(
            "Open and save a project in the main editor before authoring a scenario."
        )

    def _toggle_overlays(self) -> None:
        if self.professional_viewport is not None:
            self.professional_viewport.set_overlay_visible(
                self.overlay_action.isChecked()
            )

    def _toggle_professional_preview(self) -> None:
        self._set_editor_mode(preview=True)

    def _toggle_professional_authoring(self) -> None:
        self._set_editor_mode(preview=False)

    def _set_editor_mode(self, *, preview: bool) -> None:
        self.preview_action.setChecked(preview)
        self.authoring_action.setChecked(not preview)
        if self.professional_viewport is not None:
            self.professional_viewport.set_preview_enabled(preview)
            self.professional_viewport.set_authoring_enabled(not preview)
        if self.professional_inspector is not None:
            self.professional_inspector.setEnabled(not preview)
        self.status_label.setText(
            "Scenario preview — read-only" if preview else "Scenario authoring"
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
        self.export_target_combo.setEnabled(ready)
        self.upgrade_action.setEnabled(self._pending_v1_document is not None)
        self.recover_action.setEnabled(self._pending_recovery_path is not None)
        self.overlay_action.setEnabled(available)
        self.preview_action.setEnabled(available)
        self.authoring_action.setEnabled(available)
        if self.professional_inspector is not None:
            self.professional_inspector.setEnabled(
                available and not self.preview_action.isChecked()
            )
        session = self.professional_session
        self.undo_action.setEnabled(session is not None and session.can_undo)
        self.redo_action.setEnabled(session is not None and session.can_redo)
        if (
            available
            and self.professional_session is None
            and (
                self._pending_v1_document is not None
                or self._pending_recovery_path is not None
            )
        ):
            self.canvas.set_scenario_preview_layers(())
            self.status_label.setText("Scenario requires migration or recovery action")
        elif available:
            self.canvas.set_scenario_preview_layers(self.authoring.preview_layers())
            self.canvas.set_scenario_camera(
                self.authoring.preview_camera(
                    (float(self.canvas.width()), float(self.canvas.height()))
                )
            )
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
                mode_status + (" — unsaved changes" if session_dirty else "")
            )
        else:
            self.canvas.set_scenario_preview_layers(())
            self.status_label.setText(
                "Open and save a project to enable scenario authoring"
            )
        self.canvas.update()

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.setWindowTitle("Editor de Cenário — NeoEng-D-Trace")
            labels = (
                "Abrir Projeto",
                "Salvar Cenário",
                "Recarregar",
                "Redefinir",
                "Exportar Runtime",
                "Atualizar V1 para V2",
                "Recuperar Último Válido",
                "Desfazer",
                "Refazer",
                "Sobreposições",
                "Preview Parallax",
                "Autoria",
            )
        else:
            self.setWindowTitle("Scenario Editor — NeoEng-D-Trace")
            labels = (
                "Open Project",
                "Save Scenario",
                "Reload",
                "Reset",
                "Export Runtime",
                "Upgrade V1 to V2",
                "Recover Last Valid",
                "Undo",
                "Redo",
                "Overlays",
                "Parallax Preview",
                "Authoring",
            )
        for action, label in zip(
            (
                self.open_action,
                self.save_action,
                self.load_action,
                self.reset_action,
                self.export_action,
                self.upgrade_action,
                self.recover_action,
                self.undo_action,
                self.redo_action,
                self.overlay_action,
                self.preview_action,
                self.authoring_action,
            ),
            labels,
        ):
            action.setText(label)
        self.export_target_label.setText(
            "Alvo:" if self.current_lang == "pt" else "Target:"
        )
        self.export_target_combo.setItemText(
            0, "Genérico" if self.current_lang == "pt" else "Generic"
        )
        self.export_target_combo.setItemText(1, "Godot 4.7")
        self.export_target_combo.setItemText(2, "Unity 6000.5.7f1")
        self.scenario_panel.update_language(self.current_lang)
        if self.asset_library is not None:
            self.asset_library.update_language(self.current_lang)

    def closeEvent(self, event) -> None:
        self._professional_initial_focus_applied = False
        if self.professional_session is not None and self.professional_session.is_dirty:
            self.status_label.setText("Unsaved scenario changes preserved")
        self.hide()
        event.ignore()
