"""Small coordination helpers for the main-window language refresh."""

from __future__ import annotations


ACTION_TOOLTIP_KEYS = {
    "open_project_action": "open_project",
    "open_image_action": "open_image",
    "save_project_action": "save_project",
    "save_project_as_action": "save_project_as",
    "close_application_action": "close_application",
    "act_export": "export",
    "act_export_collision_json": "export_collision_json",
    "act_export_collision_txt": "export_collision_txt",
    "act_fit": "fit_view",
    "act_100": "pixel_1",
    "act_lit": "lit",
    "act_xray1": "xray_1",
    "act_xray2": "xray_2",
    "act_xray3": "xray_3",
    "act_clean": "clean",
    "act_gizmo": "gizmo",
    "act_grid": "grid",
    "act_snap": "snap",
    "undo_action": "undo",
    "redo_action": "redo",
    "mask_viewer_action": "mask_viewer",
    "collision_overlay_action": "collision_overlay",
    "scenario_open_action": "scenario_open",
    "scenario_save_action": "scenario_save",
    "scenario_load_action": "scenario_load",
    "scenario_reset_action": "scenario_reset",
    "scenario_export_action": "scenario_export",
    "settings_action": "settings",
    "language_action": "language",
}


def apply_action_tooltips(window, translations: dict) -> None:
    for attribute, key in ACTION_TOOLTIP_KEYS.items():
        action = getattr(window, attribute, None)
        tooltip = translations["tooltips"].get(key)
        if action is not None and tooltip:
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)


def refresh_language_components(window) -> None:
    language = window.current_lang
    for component in (
        window.side_panel,
        window.layers,
        window.collision_panel,
        window.tool_palette,
        window.groups,
        window.canvas,
    ):
        updater = getattr(component, "update_language", None)
        if callable(updater):
            updater(language)
    rail = getattr(window, "reference_tool_palette", None)
    if rail is not None and hasattr(rail, "refresh_action_feedback"):
        rail.refresh_action_feedback()
    overlay = getattr(getattr(window, "viewport_chrome", None), "overlay", None)
    if overlay is not None and hasattr(overlay, "update_language"):
        overlay.update_language(language)
    status = getattr(window, "viewport_status", None)
    if status is not None and hasattr(status, "update_language"):
        status.update_language(language)
    tool = getattr(window.canvas, "_tool", None)
    if tool is not None and hasattr(tool, "update_language"):
        tool.update_language(language)
    dialog = getattr(window, "_mask_viewer_dialog", None)
    if dialog is not None and hasattr(dialog, "update_language"):
        dialog.update_language(language)
