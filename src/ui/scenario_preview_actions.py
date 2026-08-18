"""MainWindow adapter for the read-only scenario preview controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction


def _toggle_preview(window: Any) -> None:
    enabled = window.scenario_preview_action.isChecked()
    window.canvas.set_scenario_preview_enabled(enabled)
    window.scenario_overlays_action.setEnabled(enabled)
    if not enabled:
        window.scenario_overlays_action.setChecked(False)
        window.canvas.set_scenario_overlays_visible(False)


def _toggle_overlays(window: Any) -> None:
    window.canvas.set_scenario_overlays_visible(
        window.scenario_overlays_action.isChecked()
    )


def install_scenario_preview_actions(window: Any) -> None:
    """Install preview actions without expanding MainWindow's adapter surface."""

    window.scenario_preview_action = QAction("Scenario Preview (Read-Only)", window)
    window.scenario_preview_action.setCheckable(True)
    window.scenario_preview_action.setChecked(False)
    window.scenario_preview_action.triggered.connect(lambda: _toggle_preview(window))
    window.view_menu.addAction(window.scenario_preview_action)

    window.scenario_overlays_action = QAction("Safe Frames and Crop Overlay", window)
    window.scenario_overlays_action.setCheckable(True)
    window.scenario_overlays_action.setChecked(False)
    window.scenario_overlays_action.setEnabled(False)
    window.scenario_overlays_action.triggered.connect(lambda: _toggle_overlays(window))
    window.view_menu.addAction(window.scenario_overlays_action)

    original_update_language = window.update_language

    def update_language_with_preview() -> None:
        original_update_language()
        translations = window.translations[window.current_lang]
        window.scenario_preview_action.setText(translations["scenario_preview"])
        window.scenario_overlays_action.setText(translations["scenario_overlays"])

    window.update_language = update_language_with_preview
