"""Command ID bindings for the existing MainWindow actions."""

from __future__ import annotations

from typing import Any

from src.ui.command_registry import CommandRegistry


def register_main_window_commands(registry: CommandRegistry, window: Any) -> None:
    """Bind stable IDs to the existing QAction instances on the main window."""

    registry.register_many(
        [
            ("file.open_project", window.open_project_action),
            ("file.open_image", window.open_image_action),
            ("file.save", window.save_project_action),
            ("file.save_as", window.save_project_as_action),
            ("app.exit", window.close_application_action),
            ("app.language_en", window.act_english),
            ("app.language_pt", window.act_portuguese),
            ("edit.undo", window.undo_action),
            ("edit.redo", window.redo_action),
            ("view.settings", window.settings_action),
            ("view.mask_viewer", window.mask_viewer_action),
            ("view.collision_overlay", window.collision_overlay_action),
            ("view.fit", window.act_fit),
            ("view.zoom_100", window.act_100),
            ("view.grid", window.act_grid),
            ("view.snap", window.act_snap),
            ("view.gizmo", window.act_gizmo),
            ("view.lit", window.act_lit),
            ("view.xray_1", window.act_xray1),
            ("view.xray_2", window.act_xray2),
            ("view.xray_3", window.act_xray3),
            ("view.clean_all", window.act_clean),
            ("export.open", window.act_export),
            ("collision.export_json", window.act_export_collision_json),
            ("collision.export_txt", window.act_export_collision_txt),
            ("scenario.open", window.scenario_open_action),
            ("scenario.save", window.scenario_save_action),
            ("scenario.load", window.scenario_load_action),
            ("scenario.reset", window.scenario_reset_action),
            ("scenario.export", window.scenario_export_action),
            ("tool.validation", window.tool_palette.navigation_actions["validation"]),
            (
                "tool.move_viewport",
                window.tool_palette.navigation_actions["move_viewport"],
            ),
            (
                "tool.zoom_viewport",
                window.tool_palette.navigation_actions["zoom_viewport"],
            ),
            ("tool.fit_view", window.tool_palette.navigation_actions["fit_view"]),
            (
                "tool.focus_selected",
                window.tool_palette.navigation_actions["focus_selected"],
            ),
        ]
    )
    for tool_name, action in window.tool_palette._tool_actions.items():
        registry.register(f"tool.{tool_name}", action)
