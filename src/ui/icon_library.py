"""Internal, deterministic icon library for the NeoEng-D-Trace UI.

The glyphs are small SVGs embedded in source code.  They do not depend on a
machine-local path, a desktop theme, a downloaded font, or a third-party icon
set.  Every presentation helper deliberately keeps the textual label so an
icon failure degrades to an accessible text action instead of hiding it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QAbstractButton, QWidget

from src.core.logger import logger
from src.ui.theme_tokens import THEME_TOKENS


@dataclass(frozen=True)
class IconSpec:
    key: str
    accessible_name: str
    svg_body: str


def _svg(body: str, color: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f'<g fill="none" stroke="{color}" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</g></svg>"
    )


_ICON_BODIES: Final[dict[str, tuple[str, str]]] = {
    "open": (
        "folder",
        '<path d="M3.5 6.5h6l2 2h9v9.5h-17z"/><path d="M3.5 6.5v-2h6l2 2"/>',
    ),
    "open_image": (
        "open image",
        '<rect x="3.5" y="4.5" width="17" height="15" rx="1.5"/>'
        '<circle cx="9" cy="9" r="1.3"/><path d="m4.5 17 4.5-4 3 2.5 2-2 5.5 4"/>',
    ),
    "save": (
        "save",
        '<path d="M4 3.5h13l3 3v14H4z"/><path d="M7 3.5v6h9v-6"/>'
        '<path d="M7 20.5v-7h10v7"/>',
    ),
    "save_as": (
        "save as",
        '<path d="M4 3.5h13l3 3v14H4z"/><path d="M7 3.5v6h9v-6"/>'
        '<path d="m14 16 4.5-4.5 2 2L16 18z"/>',
    ),
    "export": (
        "export",
        '<path d="M12 3.5v11"/><path d="m7.5 8 4.5-4.5L16.5 8"/>'
        '<path d="M5 13.5v6h14v-6"/>',
    ),
    "undo": (
        "undo",
        '<path d="M9 7 4 12l5 5"/><path d="M4 12h9a7 7 0 0 1 7 7"/>',
    ),
    "redo": (
        "redo",
        '<path d="m15 7 5 5-5 5"/><path d="M20 12h-9a7 7 0 0 0-7 7"/>',
    ),
    "collision": (
        "collision export",
        '<path d="m12 3.5 7.5 4.25v8.5L12 20.5l-7.5-4.25v-8.5z"/>'
        '<path d="m4.5 7.75 7.5 4.25 7.5-4.25M12 12v8.5"/>',
    ),
    "collision_test": (
        "batch collision test",
        '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>'
        '<path d="m7.5 10.5 2 2 4-4"/>',
    ),
    "collision_auto_generate": (
        "auto-generate collision",
        '<path d="m5 16 5-5 6 6-5 5z"/><path d="m10 11 5-5 4 4-5 5z"/>'
        '<path d="M17 3.5v4M15 5.5h4"/>',
    ),
    "clean": (
        "clean",
        '<path d="M5 7h14M9 4h6l1 3H8zM7 7l1 13h8l1-13"/>'
        '<path d="M10 10v7M14 10v7"/>',
    ),
    "fit": (
        'fit view',
        '<path d="M8 4H4v4M16 4h4v4M4 16v4h4M20 16v4h-4"/><path d="M9 9h6v6H9z"/>',
    ),
    "zoom_100": (
        "one to one zoom",
        '<circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 5 5"/>'
        '<path d="M8 10.5h5M10.5 8v5"/>',
    ),
    "lit": (
        'lit view',
        '<circle cx="12" cy="12" r="3.25"/><path d="M12 3v2.25M12 18.75V21M3 12h2.25M18.75 12H21"/><path d="m5.65 5.65 1.6 1.6M16.75 16.75l1.6 1.6M18.35 5.65l-1.6 1.6M7.25 16.75l-1.6 1.6"/>',
    ),
    "xray_1": (
        "x-ray one",
        '<path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z"/>'
        '<circle cx="12" cy="12" r="2.5"/>',
    ),
    "xray_2": (
        "x-ray two",
        '<path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z"/>'
        '<circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1.2"/>',
    ),
    "xray_3": (
        "x-ray three",
        '<path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z"/>'
        '<path d="m9 9 6 6M15 9l-6 6"/>',
    ),
    "gizmo": (
        'transform gizmo',
        '<circle cx="12" cy="12" r="1.75"/><path d="M12 10.25V4M12 13.75V20M10.25 12H4M13.75 12H20"/><path d="m9.75 6.25 2.25-2.25 2.25 2.25M9.75 17.75 12 20l2.25-2.25M6.25 9.75 4 12l2.25 2.25M17.75 9.75 20 12l-2.25 2.25"/>',
    ),
    "focus": (
        'focus selected',
        '<circle cx="12" cy="12" r="3.25"/><circle cx="12" cy="12" r=".75"/><path d="M12 3.5V7M12 17v3.5M3.5 12H7M17 12h3.5"/>',
    ),
    "language": (
        'language',
        '<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2 2.15 3 4.8 3 8s-1 5.85-3 8c-2-2.15-3-4.8-3-8s1-5.85 3-8z"/>',
    ),
    "view": (
        'view',
        '<path d="M3.5 12s3.25-5 8.5-5 8.5 5 8.5 5-3.25 5-8.5 5-8.5-5-8.5-5z"/><circle cx="12" cy="12" r="2.25"/>',
    ),
    "pan": (
        'pan',
        '<path d="M8.25 12V7.25a1.5 1.5 0 0 1 3 0V11M11.25 11V5.75a1.5 1.5 0 0 1 3 0V11M14.25 11V7a1.5 1.5 0 0 1 3 0v5M17.25 12v-2a1.5 1.5 0 0 1 3 0v4.25c0 4-2.5 6.25-6.25 6.25h-1.5c-3.25 0-5.5-1.75-6.5-4.5l-1.25-2.5a1.5 1.5 0 0 1 2.4-1.7l1.1.95z"/>',
    ),
    "parallax": (
        "parallax",
        '<path d="M4 7h10M4 12h16M4 17h10"/><path d="m14 5 4 2-4 2M10 15l-4 2 4 2"/>',
    ),
    "settings": (
        'view settings',
        '<path d="M5 7h8M17 7h2M5 12h2M11 12h8M5 17h10M19 17h0"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="17" r="2"/>',
    ),
    "move": (
        'move viewport',
        '<path d="M12 3v18M3 12h18"/><path d="m9 6 3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3M18 9l3 3-3 3"/>',
    ),
    "zoom": (
        'zoom viewport',
        '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5M7.75 10.5h5.5M10.5 7.75v5.5"/>',
    ),
    "grid": (
        'toggle grid',
        '<rect x="4" y="4" width="16" height="16" rx="1"/><path d="M9.33 4v16M14.67 4v16M4 9.33h16M4 14.67h16"/>',
    ),
    "snap": (
        "toggle snapping",
        '<path d="M6 4v6a6 6 0 0 0 12 0V4"/>'
        '<path d="M6 4h4M14 4h4M8 20h8M12 16v4"/>',
    ),
    "scenario": (
        "scenario editor",
        '<path d="M4 6h10v12H4zM10 9h10v10H10z"/><path d="M7 9v5M13 12h4"/>',
    ),
    "validation": (
        "validate collision geometry",
        '<circle cx="12" cy="12" r="8.5"/><path d="m8 12 2.5 2.5L16.5 9"/>',
    ),
    "collider_edit": (
        "edit collider vertices",
        '<path d="m5 5 14 3-3 12-11-5z"/><circle cx="5" cy="5" r="1.8"/>'
        '<circle cx="19" cy="8" r="1.8"/><circle cx="16" cy="20" r="1.8"/>'
        '<path d="m8 17 8-8"/>',
    ),
    "add": (
        "add layer",
        '<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8M8 12h8"/>',
    ),
    "remove": (
        "remove layer",
        '<circle cx="12" cy="12" r="8.5"/><path d="M8 12h8"/>',
    ),
    "up": (
        "move layer up",
        '<path d="M12 19V5M7 10l5-5 5 5"/>',
    ),
    "down": (
        "move layer down",
        '<path d="M12 5v14M7 14l5 5 5-5"/>',
    ),
    "visible": (
        "toggle layer visibility",
        '<path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z"/>'
        '<circle cx="12" cy="12" r="2.5"/>',
    ),
    "lock": (
        "toggle layer lock",
        '<rect x="5" y="10" width="14" height="10" rx="1.5"/>'
        '<path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    ),
    "lasso": (
        "lasso tool",
        '<path d="M7 5.5c-3 2-3.4 7.4.6 9.6 4.8 2.7 10.7-1.2 9.4-5.6'
        '-1-3.5-5.9-3.8-7.7-1.3-1.5 2.2.2 4.8 2.5 4.8"/>'
        '<circle cx="7" cy="18.5" r="2"/>',
    ),
    "polygon": (
        "polygon tool",
        '<path d="m5 5 14 3-3 12-11-5z"/>'
        '<circle cx="5" cy="5" r="1"/><circle cx="19" cy="8" r="1"/>'
        '<circle cx="16" cy="20" r="1"/><circle cx="5" cy="15" r="1"/>',
    ),
    "magnetic": (
        "magnetic lasso tool",
        '<path d="M5 5v8a7 7 0 0 0 14 0V5"/>'
        '<path d="M5 9h4M15 9h4"/>'
        '<circle cx="5" cy="5" r="1"/><circle cx="19" cy="5" r="1"/>',
    ),
    "pen": (
        "pen tool",
        '<path d="m5 19 1.5-5.5L16.8 3.2a2 2 0 0 1 2.8 2.8L9.3 16.5z"/>'
        '<path d="m14 6 4 4M5 19l4-1"/>',
    ),
    "rect": (
        "rectangle tool",
        '<rect x="4" y="5" width="16" height="14" rx="1"/>',
    ),
    "ellipse": (
        "ellipse tool",
        '<ellipse cx="12" cy="12" rx="8" ry="5.5"/>',
    ),
    "polygon_edit": (
        "polygon edit tool",
        '<path d="m5 5 14 3-3 12-11-5z"/>'
        '<circle cx="5" cy="5" r="1.6"/>'
        '<circle cx="19" cy="8" r="1.6"/>'
        '<circle cx="16" cy="20" r="1.6"/><circle cx="5" cy="15" r="1.6"/>',
    ),
    "collision_brush": (
        "collision brush tool",
        '<path d="m5 19 4-4 6 6-4 1z"/><path d="m9 15 5-5 5 5-4 4z"/>'
        '<path d="M17 3.5v4M15 5.5h4"/>',
    ),
    "selection": (
        'selection tool',
        '<path d="m5 3.5 4.1 15 3-5.1 4.8 5.7 2.1-1.8-4.8-5.7 5.8-1.5z"/>',
    ),
}

ICON_SPECS: Final[dict[str, IconSpec]] = {
    key: IconSpec(key, accessible_name, body)
    for key, (accessible_name, body) in _ICON_BODIES.items()
}
TOOL_ICON_KEYS: Final[dict[str, str]] = {
    "lasso_tool": "lasso",
    "polygonal_lasso": "polygon",
    "magnetic_lasso": "magnetic",
    "pen_tool": "pen",
    "rect_selection": "rect",
    "ellipse_selection": "ellipse",
    "polygon_edit": "polygon_edit",
    "collision_brush": "collision_brush",
    "selection": "selection",
}

_ICON_CACHE: dict[tuple[str, str], QIcon] = {}


def icon_for(key: str, *, color: str = THEME_TOKENS.text_primary) -> QIcon:
    """Return a cached deterministic vector icon for ``key``."""

    if key not in ICON_SPECS:
        raise KeyError(f"Unknown NeoEng-D-Trace icon key: {key}")
    cache_key = (key, color)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    spec = ICON_SPECS[key]
    svg = _svg(spec.svg_body, color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid embedded SVG for icon: {key}")

    icon = QIcon()
    for size in (16, 20, 24, 32):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.Off)
    if icon.isNull():
        raise RuntimeError(f"Unable to render embedded SVG icon: {key}")
    _ICON_CACHE[cache_key] = icon
    return icon


def _keep_textual_fallback(action_or_widget, key: str, exc: Exception) -> None:
    logger.warning("Icon %s unavailable; preserving textual fallback: %s", key, exc)
    action_or_widget.setIcon(QIcon())
    action_or_widget.setProperty("iconFallback", True)


def configure_action(
    action: QAction,
    key: str,
    *,
    text: str | None = None,
    tooltip: str | None = None,
    accessible_name: str | None = None,
) -> QAction:
    """Apply icon metadata while retaining an accessible textual action."""

    if text is not None:
        action.setText(text)
    spec = ICON_SPECS[key]
    action.setToolTip(tooltip or spec.accessible_name)
    action.setStatusTip(tooltip or spec.accessible_name)
    action.setProperty("accessibleName", accessible_name or spec.accessible_name)
    action.setProperty("iconKey", key)
    try:
        action.setIcon(icon_for(key))
        action.setProperty("iconFallback", False)
    except Exception as exc:  # pragma: no cover - defensive rendering boundary
        _keep_textual_fallback(action, key, exc)
    return action


def configure_widget(
    widget: QWidget,
    key: str,
    *,
    tooltip: str | None = None,
    accessible_name: str | None = None,
    accessible_description: str | None = None,
) -> QWidget:
    """Apply icon metadata to an icon-capable widget without removing text."""

    spec = ICON_SPECS[key]
    resolved_name = accessible_name or spec.accessible_name
    resolved_tooltip = tooltip or spec.accessible_name
    widget.setToolTip(resolved_tooltip)
    widget.setAccessibleName(resolved_name)
    widget.setAccessibleDescription(
        accessible_description or ('Activate ' + resolved_name)
    )
    if isinstance(widget, QAbstractButton):
        widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    widget.setProperty("iconKey", key)
    try:
        icon_setter = getattr(widget, "setIcon")
        if not callable(icon_setter):
            raise TypeError(f"Widget does not support icons: {type(widget).__name__}")
        icon_setter(icon_for(key))
        widget.setProperty("iconFallback", False)
    except Exception as exc:  # pragma: no cover - defensive rendering boundary
        _keep_textual_fallback(widget, key, exc)
    return widget


def configure_main_window_controls(window: Any) -> None:
    """Configure the MainWindow icon contract after all controls are created."""

    action_keys = {
        "open_project_action": "open",
        "open_image_action": "open_image",
        "save_project_action": "save",
        "save_project_as_action": "save_as",
        "act_export": "export",
        "undo_action": "undo",
        "redo_action": "redo",
        "act_export_collision_json": "collision",
        "act_export_collision_txt": "collision",
        "act_fit": "fit",
        "act_100": "zoom_100",
        "act_grid": "grid",
        "act_snap": "snap",
        "act_gizmo": "gizmo",
        "settings_action": "settings",
        "act_lit": "lit",
        "act_xray1": "xray_1",
        "act_xray2": "xray_2",
        "act_xray3": "xray_3",
        "act_clean": "clean",
        "language_action": "language",
    }
    for name, key in action_keys.items():
        configure_action(getattr(window, name), key)

    from src.ui.reference_chrome import (
        configure_reference_tool_palette,
        configure_reference_top_toolbar,
    )
    from src.ui.top_command_contract import build_top_command_contract

    window.top_command_contract = build_top_command_contract(window)
    configure_reference_tool_palette(window)
    configure_reference_top_toolbar(window)
    window.reference_tool_palette.setEnabled(window.tool_palette.isEnabled())
    from src.ui.viewport_status import configure_viewport_status

    configure_viewport_status(window)
