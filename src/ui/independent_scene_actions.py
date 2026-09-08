"""Install the independent-scene entry point without growing MainWindow."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction

from src.ui.independent_scene_window import IndependentSceneWindow


def install_independent_scene(window: Any) -> None:
    """Add the independent-scene command to the existing Scenario menu."""

    window._independent_scene_window = None
    action = QAction(window)
    window.open_independent_scene_action = action
    window.scenario_menu.addSeparator()
    window.scenario_menu.addAction(action)

    def open_independent_scene() -> bool:
        if window._independent_scene_window is None:
            window._independent_scene_window = IndependentSceneWindow(
                language=window.current_lang,
                parent=window,
            )
        child = window._independent_scene_window
        child.show()
        child.raise_()
        child.activateWindow()
        return True

    original_update_language = window.update_language

    def update_language() -> None:
        original_update_language()
        action.setText(
            "Novo Cenário Independente..."
            if window.current_lang == "pt"
            else "New Independent Scene..."
        )
        if window._independent_scene_window is not None:
            window._independent_scene_window.update_language(window.current_lang)

    window.open_independent_scene = open_independent_scene
    window.update_language = update_language
    action.setText(
        "Novo Cenário Independente..."
        if window.current_lang == "pt"
        else "New Independent Scene..."
    )


__all__ = ["install_independent_scene"]
