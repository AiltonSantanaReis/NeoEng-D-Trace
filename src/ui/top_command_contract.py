"""Semantic Stage 4 command grouping for visible chrome and dispatch.

The application chrome and command dispatch consume stable command families
without depending on presentation-widget ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from src.ui.icon_library import ICON_SPECS, icon_for
from src.ui.theme_tokens import THEME_TOKENS

TOP_COMMAND_GROUP_ORDER = (
    "file",
    "edit",
    "view",
    "export",
    "context",
    "render",
)

_ACTION_ICON_BODIES = {
    "mask": (
        "mask viewer",
        '<path d="M4 5h16v14H4z"/><path d="m7 15 3-3 2 2 2-3 3 4"/>'
        '<circle cx="8" cy="9" r="1"/>',
    ),
    "overlay": (
        "collision overlay",
        '<rect x="4" y="4" width="11" height="11" rx="1"/>'
        '<path d="M9 9h11v11H9z"/>',
    ),
}


@dataclass(frozen=True, slots=True)
class TopCommandGroup:
    """One ordered semantic family of existing UI command/control objects."""

    name: str
    role: str
    items: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class TopCommandContract:
    """Immutable semantic contract for command-family consumers."""

    stage: int
    groups: tuple[TopCommandGroup, ...]
    action_identity_preserved: bool = True

    def group_names(self) -> tuple[str, ...]:
        return tuple(group.name for group in self.groups)

    def items(self, group_name: str) -> tuple[Any, ...]:
        for group in self.groups:
            if group.name == group_name:
                return group.items
        raise KeyError(group_name)

    def role(self, group_name: str) -> str:
        for group in self.groups:
            if group.name == group_name:
                return group.role
        raise KeyError(group_name)

    def as_mapping(self) -> dict[str, tuple[Any, ...]]:
        """Return the semantic command groups without mutable source state."""

        return {group.name: group.items for group in self.groups}

    def descriptor(self) -> dict[str, Any]:
        """Return an inspectable, object-free description for audits and logs."""

        return {
            "stage": self.stage,
            "group_order": self.group_names(),
            "group_roles": {group.name: group.role for group in self.groups},
            "action_identity_preserved": self.action_identity_preserved,
        }


def _action_icon(key: str) -> QIcon:
    if key in {"undo", "redo"}:
        return icon_for(key)
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


def configure_semantic_action_icons(window: Any) -> None:
    """Apply Stage 4 semantic metadata to canonical actions."""

    for name, key in (
        ("undo_action", "undo"),
        ("redo_action", "redo"),
        ("mask_viewer_action", "mask"),
        ("collision_overlay_action", "overlay"),
    ):
        action = getattr(window, name)
        action.setIcon(_action_icon(key))
        label = (
            ICON_SPECS[key].accessible_name
            if key in ICON_SPECS
            else _ACTION_ICON_BODIES[key][0]
        )
        action.setToolTip(label)
        action.setStatusTip(label)
        action.setProperty("accessibleName", label)
        action.setProperty("iconKey", f"stage4_{key}")
        action.setProperty("iconFallback", False)


def build_top_command_contract(window: Any) -> TopCommandContract:
    """Build the canonical command-family contract from existing controls.

    The function references only the already-created canonical actions and
    controls; presentation-widget ownership is outside this contract.
    """

    configure_semantic_action_icons(window)
    groups = (
        TopCommandGroup(
            "file",
            "commands",
            (
                window.open_project_action,
                window.open_image_action,
                window.save_project_action,
                window.save_project_as_action,
            ),
        ),
        TopCommandGroup(
            "edit",
            "commands",
            (window.undo_action, window.redo_action, window.settings_action),
        ),
        TopCommandGroup(
            "view",
            "commands",
            (
                window.mask_viewer_action,
                window.collision_overlay_action,
                window.act_fit,
                window.act_100,
                window.act_grid,
                window.act_snap,
            ),
        ),
        TopCommandGroup(
            "export",
            "commands",
            (
                window.act_export,
                window.act_export_collision_json,
                window.act_export_collision_txt,
            ),
        ),
        TopCommandGroup(
            "context",
            "context",
            (
                window.act_gizmo,
                window.tool_palette.navigation_actions["focus_selected"],
                window.act_clean,
                window.language_action,
            ),
        ),
        TopCommandGroup(
            "render",
            "render",
            (
                window.act_lit,
                window.act_xray1,
                window.act_xray2,
                window.act_xray3,
            ),
        ),
    )
    contract = TopCommandContract(stage=4, groups=groups)
    if contract.group_names() != TOP_COMMAND_GROUP_ORDER:
        raise RuntimeError("top command group order drifted from canonical contract")
    return contract


__all__ = [
    "TOP_COMMAND_GROUP_ORDER",
    "TopCommandContract",
    "TopCommandGroup",
    "build_top_command_contract",
    "configure_semantic_action_icons",
]
