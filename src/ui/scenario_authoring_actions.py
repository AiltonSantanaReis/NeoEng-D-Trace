"""MainWindow adapter for scenario authoring and sidecar persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from src.core.scenario_authoring import ScenarioAuthoringState
from src.ui.scenario_editor_window import ScenarioEditorWindow


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


def _export(window: Any) -> bool:
    try:
        destination = window.scenario_authoring.export_runtime()
    except Exception as exc:
        _report(window, "Scenario export failed", str(exc))
        return False
    window.statusBar().showMessage(
        f"Scenario runtime export written to {destination.name}.", 5000
    )
    return True


def install_scenario_authoring(window: Any) -> None:
    """Install scenario actions and a separate authoring window.

    The main editor keeps only the read-only preview. Authoring controls live
    in a dedicated window so they cannot compress or intercept image panels.
    """

    state = ScenarioAuthoringState(window.scene)
    window.scenario_authoring = state
    window.scenario_panel = None
    window.scenario_editor_window = None

    def open_editor() -> None:
        editor = window.scenario_editor_window
        if editor is None:
            editor = ScenarioEditorWindow(
                state,
                window.scene,
                language=window.current_lang,
                parent=window,
            )
            window.scenario_editor_window = editor
        editor.show()
        editor.raise_()
        editor.activateWindow()
        editor.refresh()

    def state_changed() -> None:
        _sync_preview(window)
        if hasattr(window, "scenario_save_action"):
            available = state.is_available
            window.scenario_save_action.setEnabled(available)
            window.scenario_load_action.setEnabled(available)
            window.scenario_reset_action.setEnabled(available)
            window.scenario_export_action.setEnabled(available)
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.refresh()

    menu = window.menuBar().addMenu("Scenario")
    window.scenario_open_action = QAction("Open Scenario Editor", window)
    window.scenario_open_action.triggered.connect(open_editor)
    window.scenario_save_action = QAction("Save Scenario", window)
    window.scenario_save_action.triggered.connect(lambda: _save(window))
    window.scenario_load_action = QAction("Reload Scenario", window)
    window.scenario_load_action.triggered.connect(lambda: _load(window))
    window.scenario_reset_action = QAction("Reset From Project", window)
    window.scenario_reset_action.triggered.connect(lambda: _reset(window))
    window.scenario_export_action = QAction("Export Runtime JSON", window)
    window.scenario_export_action.triggered.connect(lambda: _export(window))

    menu.addAction(window.scenario_open_action)
    window.view_menu.addSeparator()
    window.view_menu.addAction(window.scenario_open_action)
    menu.addSeparator()
    menu.addAction(window.scenario_save_action)
    menu.addAction(window.scenario_load_action)
    menu.addAction(window.scenario_reset_action)
    menu.addAction(window.scenario_export_action)
    window.scenario_menu = menu
    window.open_scenario_editor = open_editor
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
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.update_language(window.current_lang)

    window.update_language = update_language_with_scenario
