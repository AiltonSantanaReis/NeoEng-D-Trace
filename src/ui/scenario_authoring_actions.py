"""MainWindow adapter for scenario authoring and sidecar persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from src.core.scenario_authoring import ScenarioAuthoringState
from src.ui.scenario_panel import ScenarioPanel


def _report(window: Any, title: str, message: str) -> None:
    QMessageBox.critical(window, title, message)


def _save(window: Any) -> bool:
    try:
        window.scenario_authoring.save()
    except Exception as exc:
        _report(window, "Scenario save failed", str(exc))
        return False
    window.statusBar().showMessage("Scenario saved successfully.", 5000)
    return True


def _load(window: Any) -> bool:
    try:
        window.scenario_authoring.load()
    except Exception as exc:
        _report(window, "Scenario load failed", str(exc))
        return False
    window.statusBar().showMessage("Scenario loaded successfully.", 5000)
    return True


def _reset(window: Any) -> bool:
    if window.scenario_authoring.is_dirty:
        answer = QMessageBox.question(
            window,
            "Reset scenario",
            "Discard unsaved scenario authoring changes?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
    try:
        window.scenario_authoring.reset()
    except Exception as exc:
        _report(window, "Scenario reset failed", str(exc))
        return False
    return True


def _sync_preview(window: Any) -> None:
    state = window.scenario_authoring
    if not state.is_available:
        window.canvas.set_scenario_preview_layers(())
        return
    window.canvas.set_scenario_preview_layers(state.preview_layers())
    window.canvas.set_scenario_camera(
        state.preview_camera(
            (float(window.canvas.width()), float(window.canvas.height()))
        )
    )
    window.canvas.update()


def install_scenario_authoring(window: Any) -> None:
    """Install the scenario tab and actions without changing Scene history."""

    state = ScenarioAuthoringState(window.scene)
    panel = ScenarioPanel(state, window.scene, window)
    window.scenario_authoring = state
    window.scenario_panel = panel
    window.layers.attach_scenario_panel(panel)

    def state_changed() -> None:
        _sync_preview(window)
        if hasattr(window, "scenario_save_action"):
            available = state.is_available
            window.scenario_save_action.setEnabled(available)
            window.scenario_load_action.setEnabled(available)
            window.scenario_reset_action.setEnabled(available)

    menu = window.menuBar().addMenu("Scenario")
    window.scenario_save_action = QAction("Save Scenario", window)
    window.scenario_save_action.triggered.connect(lambda: _save(window))
    window.scenario_load_action = QAction("Reload Scenario", window)
    window.scenario_load_action.triggered.connect(lambda: _load(window))
    window.scenario_reset_action = QAction("Reset From Project", window)
    window.scenario_reset_action.triggered.connect(lambda: _reset(window))
    menu.addAction(window.scenario_save_action)
    menu.addAction(window.scenario_load_action)
    menu.addAction(window.scenario_reset_action)
    window.scenario_menu = menu
    state.subscribe(state_changed)
    state_changed()

    original_refresh = window._refresh_document_views

    def refresh_document_views(*, project_loaded: bool) -> None:
        original_refresh(project_loaded=project_loaded)
        try:
            state.bind_project(window._project_path if project_loaded else None)
        except Exception as exc:
            state.bind_project(None)
            _report(window, "Scenario load failed", str(exc))

    window._refresh_document_views = refresh_document_views

    original_save = window._save_project_to

    def save_project_to(path: str | Path) -> bool:
        saved = original_save(path)
        if saved:
            state.bind_project(window._project_path)
        return saved

    window._save_project_to = save_project_to

    original_update_language = window.update_language

    def update_language_with_scenario() -> None:
        original_update_language()
        window.scenario_panel.update_language(window.current_lang)

    window.update_language = update_language_with_scenario
