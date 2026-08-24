"""Main-window action installation for the viewport/reference contract."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction

from src.ui.tool_palette_commands import handle_auxiliary_action
from src.ui.viewport_settings import open_view_settings


def install_viewport_actions(window: Any) -> None:
    """Install Grid, Snap, Settings and auxiliary rail dispatch once."""

    window.tool_palette.auxiliary_action_requested.connect(
        lambda name: handle_auxiliary_action(window, name)
    )

    window.act_grid = QAction("Grid", window)
    window.act_grid.setCheckable(True)
    window.act_grid.setChecked(True)
    window.act_grid.triggered.connect(window.canvas.set_grid_visible)
    window.view_menu.addAction(window.act_grid)

    window.act_snap = QAction("Snap", window)
    window.act_snap.setCheckable(True)
    window.act_snap.triggered.connect(
        lambda enabled: window.canvas.set_vertex_snapping(enabled, grid_size=16)
    )
    window.view_menu.addAction(window.act_snap)

    window.settings_action = QAction("View Settings", window)
    window.settings_action.triggered.connect(lambda: open_view_settings(window))
    window.edit_menu.addAction(window.settings_action)