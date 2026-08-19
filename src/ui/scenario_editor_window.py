"""Dedicated scenario authoring window.

The main image editor remains focused on image, polygon and collision work.
Scenario authoring is hosted here so its layer stack and inspector cannot
compress or intercept the main editor panels.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QScrollArea,
    QSplitter,
    QToolBar,
    QLabel,
    QWidget,
)

from src.core.scenario_authoring import ScenarioAuthoringState
from src.ui.scenario_panel import ScenarioPanel


class ScenarioEditorWindow(QMainWindow):
    """Interactive authoring surface for the versioned scenario sidecar."""

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

        self.canvas = self._build_canvas()
        self.scenario_panel = ScenarioPanel(authoring, scene, self)
        self.scenario_panel.setMinimumWidth(390)
        self.scenario_panel.setMaximumWidth(520)

        scroll = QScrollArea(self)
        scroll.setObjectName("scenario_inspector_scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.scenario_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("scenario_editor_splitter")
        splitter.addWidget(self.canvas)
        splitter.addWidget(scroll)
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
        self.overlay_action = QAction(self)
        self.overlay_action.setCheckable(True)
        for action in (
            self.open_action,
            self.save_action,
            self.load_action,
            self.reset_action,
            self.export_action,
            self.overlay_action,
        ):
            self.toolbar.addAction(action)
        self.toolbar.addSeparator()
        self.status_label = QLabel(self)
        self.toolbar.addWidget(self.status_label)

        self.open_action.triggered.connect(self._open_project_hint)
        self.save_action.triggered.connect(self.scenario_panel.save)
        self.load_action.triggered.connect(self.scenario_panel.load)
        self.reset_action.triggered.connect(self.scenario_panel.reset)
        self.export_action.triggered.connect(self.scenario_panel.export_runtime)
        self.overlay_action.triggered.connect(self._toggle_overlays)
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
        canvas.gizmo_toggle.setVisible(False)
        return canvas

    def _open_project_hint(self) -> None:
        self.status_label.setText(
            "Open and save a project in the main editor before authoring a scenario."
        )

    def _toggle_overlays(self) -> None:
        self.canvas.set_scenario_overlays_visible(self.overlay_action.isChecked())

    def refresh(self) -> None:
        available = self.authoring.is_available
        self.save_action.setEnabled(available)
        self.load_action.setEnabled(available)
        self.reset_action.setEnabled(available)
        self.export_action.setEnabled(available)
        self.overlay_action.setEnabled(available)
        if available:
            self.canvas.set_scenario_preview_layers(self.authoring.preview_layers())
            self.canvas.set_scenario_camera(
                self.authoring.preview_camera(
                    (float(self.canvas.width()), float(self.canvas.height()))
                )
            )
            self.status_label.setText(
                "Unsaved scenario changes"
                if self.authoring.is_dirty
                else "Scenario ready"
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
                "Sobreposições",
            )
        else:
            self.setWindowTitle("Scenario Editor — NeoEng-D-Trace")
            labels = (
                "Open Project",
                "Save Scenario",
                "Reload",
                "Reset",
                "Export Runtime",
                "Overlays",
            )
        for action, label in zip(
            (
                self.open_action,
                self.save_action,
                self.load_action,
                self.reset_action,
                self.export_action,
                self.overlay_action,
            ),
            labels,
        ):
            action.setText(label)
        self.scenario_panel.update_language(self.current_lang)

    def closeEvent(self, event) -> None:
        if self.authoring.is_dirty:
            self.status_label.setText("Unsaved scenario changes preserved")
        self.hide()
        event.ignore()
