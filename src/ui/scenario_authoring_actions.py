"""MainWindow adapter for scenario authoring and sidecar persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_authoring_bridge import (
    preview_camera_from_professional_document,
    preview_layers_from_professional_document,
)
from src.persistence.p2d05_errors import user_error_message
from src.persistence.scene_authoring_io import load_scene_authoring_v2
from src.ui.scenario_editor_window import ScenarioEditorWindow


def _report(
    window: Any,
    title: str,
    exc: BaseException,
    *,
    operation: str | None = None,
) -> None:
    if operation is None:
        lowered_title = title.lower()
        operation = (
            "export"
            if "export" in lowered_title
            else (
                "load"
                if "load" in lowered_title
                else "save" if "save" in lowered_title else "edit"
            )
        )
    QMessageBox.critical(
        window,
        title,
        user_error_message(
            exc,
            operation=operation,
            language=getattr(window, "current_lang", "en"),
        ),
    )


def _save(window: Any) -> bool:
    editor = _open_professional_editor(window)
    if editor is not None and editor.professional_session is not None:
        if not editor._save_professional():
            return False
        window.statusBar().showMessage("Scenario saved successfully.", 5000)
        return True
    try:
        window.scenario_authoring.save()
    except Exception as exc:
        _report(window, "Scenario save failed", exc)
        return False
    window.statusBar().showMessage("Scenario saved successfully.", 5000)
    return True


def _load(window: Any) -> bool:
    editor = _open_professional_editor(window, only_if_canonical=True)
    if editor is not None and editor.professional_session is not None:
        if not editor._load_professional():
            return False
        window.statusBar().showMessage("Scenario loaded successfully.", 5000)
        return True
    try:
        window.scenario_authoring.load()
    except Exception as exc:
        _report(window, "Scenario load failed", exc)
        return False
    window.statusBar().showMessage("Scenario loaded successfully.", 5000)
    return True


def _reset(window: Any) -> bool:
    editor = getattr(window, "scenario_editor_window", None)
    professional_dirty = bool(
        editor is not None
        and getattr(editor, "professional_session", None) is not None
        and editor.professional_session.is_dirty
    )
    if window.scenario_authoring.is_dirty or professional_dirty:
        answer = QMessageBox.question(
            window,
            "Reset scenario",
            "Discard unsaved professional scenario authoring changes?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
    try:
        window.scenario_authoring.reset()
    except Exception as exc:
        _report(window, "Scenario reset failed", exc)
        return False
    editor = _open_professional_editor(window, only_if_canonical=True)
    if editor is not None and editor.professional_session is not None:
        if not editor._reset_professional(confirm=False):
            return False
    window.statusBar().showMessage("Scenario reset successfully.", 5000)
    return True


def _sync_preview(window: Any) -> None:
    state = window.scenario_authoring
    if not state.is_available:
        window.canvas.set_scenario_preview_layers(())
        return
    try:
        document = _professional_document(window)
    except Exception as exc:
        window.canvas.set_scenario_preview_layers(())
        window.statusBar().showMessage(
            "Scenario preview unavailable: "
            + user_error_message(
                exc,
                operation="preview",
                language=getattr(window, "current_lang", "en"),
            ),
            5000,
        )
        return
    if document is not None:
        viewport = (float(window.canvas.width()), float(window.canvas.height()))
        window.canvas.set_scenario_preview_layers(
            preview_layers_from_professional_document(document)
        )
        window.canvas.set_scenario_camera(
            preview_camera_from_professional_document(document, viewport)
        )
        window.canvas.update()
        return
    window.canvas.set_scenario_preview_layers(state.preview_layers())
    window.canvas.set_scenario_camera(
        state.preview_camera(
            (float(window.canvas.width()), float(window.canvas.height()))
        )
    )
    window.canvas.update()


def _professional_document(window: Any):
    """Return the active or persisted V2 document, if one exists."""

    state = window.scenario_authoring
    editor = getattr(window, "scenario_editor_window", None)
    session = getattr(editor, "professional_session", None)
    if (
        session is not None
        and getattr(editor, "_professional_project", None) == state.project_path
    ):
        return session.document
    if state.project_path is None:
        return None
    path = state.project_path.with_suffix(".ndtscene.json")
    if path.is_file():
        return load_scene_authoring_v2(path)
    return None


def _export(window: Any) -> bool:
    editor = _open_professional_editor(window, only_if_canonical=True)
    if editor is not None and editor.professional_session is not None:
        if not editor._export_professional():
            return False
        window.statusBar().showMessage("Scenario runtime export completed.", 5000)
        return True
    try:
        destination = window.scenario_authoring.export_runtime()
    except Exception as exc:
        _report(window, "Scenario export failed", exc)
        return False
    window.statusBar().showMessage(
        f"Scenario runtime export written to {destination.name}.", 5000
    )
    return True


def _open_professional_editor(
    window: Any,
    *,
    only_if_canonical: bool = False,
) -> Any:
    """Return the V2 editor, opening it when the canonical flow is available."""

    state = window.scenario_authoring
    if not state.is_available:
        return None
    canonical_path = state.project_path.with_suffix(".ndtscene.json")
    editor = getattr(window, "scenario_editor_window", None)
    if only_if_canonical and editor is None and not canonical_path.is_file():
        return None
    if editor is None:
        window.open_scenario_editor()
        editor = getattr(window, "scenario_editor_window", None)
    return editor


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
            editor.document_changed.connect(lambda: _sync_preview(window))
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
            _report(window, "Scenario load failed", exc)

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
