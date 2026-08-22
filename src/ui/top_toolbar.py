"""Deterministic coordination for the MainWindow top toolbars.

The application keeps three public ``QToolBar`` instances for backwards
compatibility with existing UI integrations and visual auditors. This module
owns their Stage 4 arrangement: command groups use the existing ``QAction``
objects, native separators mark group boundaries, and the contextual/render
bars retain their stable object names.
"""

from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QToolBar, QWidget

from src.ui.theme_tokens import THEME_TOKENS

_TOOLBAR_ICON_SIZE = QSize(18, 18)
_TOOLBAR_STYLE = Qt.ToolButtonStyle.ToolButtonTextBesideIcon

_ACTION_ICON_BODIES = {
    "undo": (
        "undo",
        '<path d="M9 7 4 12l5 5"/><path d="M4 12h9a7 7 0 0 1 7 7"/>',
    ),
    "redo": (
        "redo",
        '<path d="m15 7 5 5-5 5"/><path d="M20 12h-9a7 7 0 0 0-7 7"/>',
    ),
    "mask": (
        "mask viewer",
        '<path d="M4 5h16v14H4z"/><path d="m7 15 3-3 2 2 2-3 3 4"/>'
        '<circle cx="8" cy="9" r="1"/>',
    ),
    "overlay": (
        "collision overlay",
        '<rect x="4" y="4" width="11" height="11" rx="1"/>' '<path d="M9 9h11v11H9z"/>',
    ),
}


def _action_icon(key: str) -> QIcon:
    accessible_name, body = _ACTION_ICON_BODIES[key]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f'<g fill="none" stroke="{THEME_TOKENS.text_primary}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    icon = QIcon(pixmap)
    if icon.isNull():
        raise RuntimeError(
            f"stage4 icon renderer returned null icon: {accessible_name}"
        )
    return icon


def _configure_semantic_action_icons(window: Any) -> None:
    for name, key in (
        ("undo_action", "undo"),
        ("redo_action", "redo"),
        ("mask_viewer_action", "mask"),
        ("collision_overlay_action", "overlay"),
    ):
        action = getattr(window, name)
        action.setIcon(_action_icon(key))
        action.setToolTip(_ACTION_ICON_BODIES[key][0])
        action.setStatusTip(_ACTION_ICON_BODIES[key][0])
        action.setProperty("accessibleName", _ACTION_ICON_BODIES[key][0])
        action.setProperty("iconKey", f"stage4_{key}")
        action.setProperty("iconFallback", False)


def _configure_toolbar(toolbar: QToolBar, role: str) -> None:
    """Apply the shared, inspectable presentation contract to a toolbar."""

    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setToolButtonStyle(_TOOLBAR_STYLE)
    toolbar.setIconSize(_TOOLBAR_ICON_SIZE)
    toolbar.setProperty("toolbarStage", "stage4")
    toolbar.setProperty("toolbarRole", role)
    toolbar.setProperty("toolbarGroupBoundaries", True)


def _add_group(
    toolbar: QToolBar, group_name: str, items: Iterable[Any]
) -> tuple[Any, ...]:
    """Add one semantic group and return its original objects for auditing."""

    group_items = tuple(items)
    for item in group_items:
        if isinstance(item, QWidget):
            toolbar.addWidget(item)
        else:
            toolbar.addAction(item)
    toolbar.addSeparator()
    toolbar.actions()[-1].setProperty("toolbarGroupBoundary", group_name)
    return group_items


def _remove_trailing_separator(toolbar: QToolBar) -> None:
    actions = toolbar.actions()
    if actions and actions[-1].isSeparator():
        toolbar.removeAction(actions[-1])


def configure_top_toolbars(window: Any) -> None:
    """Arrange the existing top controls into the Stage 4 toolbar contract.

    This operation is intentionally idempotent. It does not create or replace
    actions, so menus, shortcuts, signal connections and command IDs continue
    to refer to the same objects.
    """

    _configure_semantic_action_icons(window)
    main_toolbar = window.toolbar
    navigation_toolbar = window.nav_toolbar
    render_toolbar = window.xray_toolbar

    for toolbar, role in (
        (main_toolbar, "commands"),
        (navigation_toolbar, "context"),
        (render_toolbar, "render"),
    ):
        _configure_toolbar(toolbar, role)

    # Rebuild only toolbar membership. QAction ownership and menu membership
    # remain unchanged because every object is reused, never recreated.
    main_toolbar.clear()
    navigation_toolbar.clear()
    render_toolbar.clear()

    groups: dict[str, tuple[Any, ...]] = {}
    groups["file"] = _add_group(
        main_toolbar,
        "file",
        (
            window.open_project_action,
            window.open_image_action,
            window.save_project_action,
            window.save_project_as_action,
        ),
    )
    groups["edit"] = _add_group(
        main_toolbar,
        "edit",
        (window.undo_action, window.redo_action),
    )
    groups["view"] = _add_group(
        main_toolbar,
        "view",
        (
            window.mask_viewer_action,
            window.collision_overlay_action,
            window.act_fit,
            window.act_100,
        ),
    )
    groups["export"] = _add_group(
        main_toolbar,
        "export",
        (window.act_export, window.export_collision_button),
    )
    _remove_trailing_separator(main_toolbar)

    groups["context"] = _add_group(
        navigation_toolbar,
        "context",
        (
            window.canvas.gizmo_toggle,
            window.focus_button,
            window.act_clean,
            window.language_button,
        ),
    )
    _remove_trailing_separator(navigation_toolbar)

    groups["render"] = _add_group(
        render_toolbar,
        "render",
        (
            window.act_lit,
            window.act_xray1,
            window.act_xray2,
            window.act_xray3,
        ),
    )
    _remove_trailing_separator(render_toolbar)

    # Public audit surface: object identity proves menus and toolbars share
    # the same actions after language changes and shortcut dispatch.
    window.top_toolbar_groups = groups
    window.top_toolbar_contract = {
        "stage": 4,
        "native_separators": True,
        "action_identity_preserved": True,
        "toolbar_roles": {
            "main_toolbar": "commands",
            "navigation_toolbar": "context",
            "xray_toolbar": "render",
        },
    }


__all__ = ["configure_top_toolbars"]
