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
            ("edit.undo", window.undo_action),
            ("edit.redo", window.redo_action),
            ("view.mask_viewer", window.mask_viewer_action),
            ("view.collision_overlay", window.collision_overlay_action),
            ("view.fit", window.act_fit),
            ("view.zoom_100", window.act_100),
            ("view.lit", window.act_lit),
            ("view.xray_1", window.act_xray1),
            ("view.xray_2", window.act_xray2),
            ("view.xray_3", window.act_xray3),
            ("view.clean_all", window.act_clean),
            ("export.open", window.act_export),
            ("collision.export_json", window.act_export_collision_json),
            ("collision.export_txt", window.act_export_collision_txt),
            ("scenario.save", window.scenario_save_action),
            ("scenario.load", window.scenario_load_action),
            ("scenario.reset", window.scenario_reset_action),
        ]
    )
