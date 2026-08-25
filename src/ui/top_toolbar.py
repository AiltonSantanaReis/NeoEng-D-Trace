"""Compatibility composition for the historical MainWindow top toolbars.

Stage 4 command grouping now lives in :mod:`src.ui.top_command_contract` and is
independent of physical ``QToolBar`` hosts.  This module temporarily projects
that semantic contract onto the three historical toolbars so existing
integrations and audits keep working while their widget-level dependencies are
migrated away.
"""

from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QToolBar, QWidget

from src.ui.top_command_contract import build_top_command_contract

_TOOLBAR_ICON_SIZE = QSize(18, 18)
_TOOLBAR_STYLE = Qt.ToolButtonStyle.ToolButtonTextBesideIcon


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
    """Project one semantic group onto a legacy physical toolbar."""

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
    """Project the semantic Stage 4 contract onto legacy toolbar widgets.

    This operation remains idempotent and does not create or replace actions.
    Menus, shortcuts, signal connections and command IDs therefore retain the
    same object identities.  The semantic command contract is built first and
    is the canonical source of group membership; physical toolbars are now only
    compatibility hosts.
    """

    semantic_contract = build_top_command_contract(window)
    semantic_groups = semantic_contract.as_mapping()
    window.top_command_contract = semantic_contract
    window.top_command_groups = semantic_groups

    main_toolbar = window.toolbar
    navigation_toolbar = window.nav_toolbar
    render_toolbar = window.xray_toolbar

    for toolbar, role in (
        (main_toolbar, "commands"),
        (navigation_toolbar, "context"),
        (render_toolbar, "render"),
    ):
        _configure_toolbar(toolbar, role)

    # Rebuild only compatibility-host membership. QAction ownership and menu
    # membership remain unchanged because every object is reused, never
    # recreated.
    main_toolbar.clear()
    navigation_toolbar.clear()
    render_toolbar.clear()

    for group_name in ("file", "edit", "view", "export"):
        _add_group(main_toolbar, group_name, semantic_contract.items(group_name))
    _remove_trailing_separator(main_toolbar)

    _add_group(
        navigation_toolbar,
        "context",
        semantic_contract.items("context"),
    )
    _remove_trailing_separator(navigation_toolbar)

    _add_group(render_toolbar, "render", semantic_contract.items("render"))
    _remove_trailing_separator(render_toolbar)

    # Historical public surfaces remain intact during the migration window.
    # New consumers should use ``top_command_contract`` / ``top_command_groups``.
    window.top_toolbar_groups = semantic_groups
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
