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
from PySide6.QtWidgets import QWidget

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
        "fit view",
        '<path d="M8 4H4v4M16 4h4v4M8 20H4v-4M20 16v4h-4"/>',
    ),
    "zoom_100": (
        "one to one zoom",
        '<circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 5 5"/>'
        '<path d="M8 10.5h5M10.5 8v5"/>',
    ),
    "lit": (
        "lit view",
        '<circle cx="12" cy="12" r="3.5"/>'
        '<path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3'
        "M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M18.7 5.3l-2.1 2.1"
        'M7.4 16.6l-2.1 2.1"/>',
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
        "transform gizmo",
        '<circle cx="12" cy="12" r="2.2"/>'
        '<path d="M12 9.8V3M12 21v-6.8M9.8 12H3M21 12h-6.8"/>'
        '<path d="m9.5 5.5 2.5-2.5 2.5 2.5M5.5 9.5 3 12l2.5 2.5'
        'M18.5 9.5 21 12l-2.5 2.5M9.5 18.5 12 21l2.5-2.5"/>',
    ),
    "focus": (
        "focus selected",
        '<circle cx="12" cy="12" r="5"/>'
        '<path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4"/>',
    ),
    "language": (
        "language",
        '<circle cx="12" cy="12" r="8.5"/>'
        '<path d="M3.5 12h17M12 3.5c2.3 2.3 3.5 5.1 3.5 8.5s-1.2 6.2-3.5 8.5'
        'c-2.3-2.3-3.5-5.1-3.5-8.5S9.7 5.8 12 3.5z"/>',
    ),
    "view": (
        "view",
        '<rect x="4" y="5" width="16" height="14" rx="1"/><path d="M8 12h8M12 8v8"/>',
    ),
    "pan": (
        "pan",
        '<path d="M8 11V5a1.5 1.5 0 0 1 3 0v5-6a1.5 1.5 0 0 1 3 0'
        "v6-4a1.5 1.5 0 0 1 3 0v6-2a1.5 1.5 0 0 1 3 0"
        'v5c0 4-2 6-6 6h-2c-3 0-5-2-5-5l-2-2a1.5 1.5 0 0 1 2-2z"/>',
    ),
    "parallax": (
        "parallax",
        '<path d="M4 7h10M4 12h16M4 17h10"/><path d="m14 5 4 2-4 2M10 15l-4 2 4 2"/>',
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
        "selection tool",
        '<path d="m5 3 4 15 3-5 5 6 2-2-5-6 6-1z"/>',
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
) -> QWidget:
    """Apply icon metadata to an icon-capable widget without removing text."""

    spec = ICON_SPECS[key]
    widget.setToolTip(tooltip or spec.accessible_name)
    widget.setAccessibleName(accessible_name or spec.accessible_name)
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

    for toolbar in (window.toolbar, window.nav_toolbar, window.xray_toolbar):
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(18, 18))

    action_keys = {
        "open_project_action": "open",
        "open_image_action": "open_image",
        "save_project_action": "save",
        "save_project_as_action": "save_as",
        "act_export": "export",
        "act_export_collision_json": "collision",
        "act_export_collision_txt": "collision",
        "act_fit": "fit",
        "act_100": "zoom_100",
        "act_lit": "lit",
        "act_xray1": "xray_1",
        "act_xray2": "xray_2",
        "act_xray3": "xray_3",
        "act_clean": "clean",
    }
    for name, key in action_keys.items():
        configure_action(getattr(window, name), key)

    widget_keys = {
        "export_collision_button": "collision",
        "focus_button": "focus",
        "language_button": "language",
    }
    for name, key in widget_keys.items():
        configure_widget(getattr(window, name), key)
    configure_widget(window.canvas.gizmo_toggle, "gizmo")
    from src.ui.reference_chrome import (
        configure_reference_tool_palette,
        configure_reference_top_toolbar,
    )
    from src.ui.top_toolbar import configure_top_toolbars

    configure_top_toolbars(window)
    configure_reference_tool_palette(window)
    configure_reference_top_toolbar(window)
    window.reference_tool_palette.setEnabled(window.tool_palette.isEnabled())
    # Preserve the Stage 4 toolbar object/visibility contract. The reference
    # toolbar is the visible chrome; the legacy command bar remains a zero-height
    # compatibility surface so existing actions and tests retain their identity.
    window.toolbar.setMinimumHeight(0)
    window.toolbar.setMaximumHeight(0)
    # Keep the historical toolbar object/action contract without reserving
    # width beside the visible reference toolbar.
    window.toolbar.setMinimumWidth(0)
    window.toolbar.setMaximumWidth(0)

    window.nav_toolbar.setVisible(False)
    window.xray_toolbar.setVisible(False)
    from src.ui.viewport_status import configure_viewport_status

    configure_viewport_status(window)
