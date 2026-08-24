"""Command adapters for the auxiliary actions in the reference tool rail."""

from __future__ import annotations

from typing import Any


def show_panel(window: Any, panel: Any) -> None:
    """Select a panel in whichever responsive tab stack is visible."""

    for tabs in (
        getattr(window, "compact_panel_tabs", None),
        getattr(window, "reference_panel_tabs", None),
    ):
        if tabs is None:
            continue
        index = tabs.indexOf(panel)
        if index >= 0:
            tabs.setCurrentIndex(index)
            panel.setVisible(True)


def handle_auxiliary_action(window: Any, action_name: str) -> None:
    """Execute auxiliary rail actions through canonical MainWindow APIs."""

    action = window.tool_palette.navigation_actions.get(action_name)
    if action_name == "move_viewport":
        window.canvas.set_pan_mode(bool(action and action.isChecked()))
    elif action_name == "zoom_viewport":
        window.canvas.set_zoom(min(50.0, window.canvas.get_zoom() * 1.25))
    elif action_name == "fit_view":
        window.canvas.fit_to_window()
    elif action_name == "focus_selected":
        window._focus_selected()
    elif action_name == "validation":
        show_panel(window, window.collision_panel)
        window.collision_panel._sync_collision_manager_from_scene()