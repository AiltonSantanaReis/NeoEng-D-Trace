"""Reference-aligned application chrome adapters.

This module composes existing actions and panels into the reference shell. It
never replaces command objects, shortcuts, canvas rendering, or persistence.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QLineEdit,
    QMenu,
    QSizePolicy,
    QTabWidget,
    QToolBar,
    QToolButton,
    QWidget,
)

from src.ui.icon_library import configure_widget


def _add_action_group(toolbar: QToolBar, actions: tuple[Any, ...]) -> None:
    for item in actions:
        if isinstance(item, QWidget):
            toolbar.addWidget(item)
        else:
            toolbar.addAction(item)
    toolbar.addSeparator()


def _command_button(
    window: Any, key: str, text: str, accessible_name: str
) -> QToolButton:
    button = QToolButton(window)
    button.setText(text)
    button.setAccessibleName(accessible_name)
    button.setToolTip(text)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    configure_widget(button, key, accessible_name=accessible_name)
    return button


def _menu_button(button: QToolButton, actions: tuple[Any, ...]) -> None:
    menu = QMenu(button)
    for action in actions:
        menu.addAction(action)
    button.setMenu(menu)
    button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)


def configure_reference_tool_palette(window: Any) -> QToolBar:
    """Expose the existing tool actions in the narrow reference palette."""

    toolbar = QToolBar("Reference tool palette", window)
    toolbar.setObjectName("reference_tool_palette")
    toolbar.setOrientation(Qt.Orientation.Vertical)
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    toolbar.setIconSize(QSize(24, 24))
    # Keep the rail within the reference contract while leaving room for QSS.
    toolbar.setMinimumWidth(56)
    toolbar.setMaximumWidth(72)
    toolbar.setProperty("uiRole", "reference_tool_palette")
    for action in window.tool_palette.actions():
        if action.isSeparator():
            toolbar.addSeparator()
        else:
            toolbar.addAction(action)
            button = toolbar.widgetForAction(action)
            if button is not None:
                button.setMinimumSize(QSize(44, 32))
                button.setMaximumSize(QSize(56, 36))
                button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                button.setIconSize(QSize(18, 18))
    window.reference_tool_palette = toolbar
    return toolbar


def configure_reference_top_toolbar(window: Any) -> QToolBar:
    """Install the single visible top toolbar used by the reference shell."""

    toolbar = QToolBar("Reference top toolbar", window)
    toolbar.setObjectName("reference_top_toolbar")
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    toolbar.setIconSize(QSize(24, 24))
    toolbar.setProperty("uiRole", "reference_top_toolbar")

    _add_action_group(
        toolbar,
        (window.open_project_action, window.save_project_action, window.act_export),
    )
    _add_action_group(toolbar, (window.act_fit, window.focus_button))

    view_button = _command_button(window, "view", "View", "View mode menu")
    _menu_button(
        view_button,
        (window.act_lit, window.act_xray1, window.act_xray2, window.act_xray3, window.act_grid, window.act_snap),
    )
    collision_button = _command_button(
        window, "collision", "Collision", "Collision menu"
    )
    _menu_button(
        collision_button,
        (
            window.collision_overlay_action,
            window.act_export_collision_json,
            window.act_export_collision_txt,
        ),
    )
    parallax_button = _command_button(
        window, "parallax", "Parallax", "Open scenario editor"
    )
    parallax_button.clicked.connect(window.open_scenario_editor)
    _add_action_group(toolbar, (view_button, collision_button, parallax_button))

    pan_button = _command_button(window, "pan", "Pan", "Pan viewport")
    pan_button.setCheckable(True)
    pan_button.toggled.connect(window.canvas.set_pan_mode)
    window.canvas.pan_mode_changed.connect(pan_button.setChecked)
    select_button = _command_button(window, "selection", "Select", "Select objects")
    select_button.clicked.connect(
        lambda: (
            window.canvas.set_pan_mode(False),
            window.tool_palette.select_tool_by_name("selection"),
        )
    )
    _add_action_group(toolbar, (pan_button, select_button))

    _add_action_group(toolbar, (window.undo_action, window.redo_action))

    menu_button = QToolButton(toolbar)
    menu_button.setObjectName("reference_menu_button")
    menu_button.setText("≡")
    menu_button.setAccessibleName("Application menu")
    menu_button.setToolTip("Application menu")
    menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    menu = QMenu(menu_button)
    for source in (window.file_menu, window.edit_menu, window.view_menu):
        submenu = menu.addMenu(source.title())
        for action in source.actions():
            submenu.addAction(action)
    menu_button.setMenu(menu)
    first_action = toolbar.actions()[0]
    toolbar.insertWidget(first_action, menu_button)
    window.reference_menu_button = menu_button
    window.menuBar().setVisible(False)

    spacer = QWidget(toolbar)
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    toolbar.addWidget(spacer)
    search = QLineEdit(toolbar)
    search.setObjectName("reference_command_search")
    search.setPlaceholderText("Ctrl+K")
    search.setAccessibleName("Command search")
    search.setToolTip("Search commands (Ctrl+K)")
    search.setMinimumWidth(260)
    search.setMaximumWidth(440)
    toolbar.addWidget(search)

    window.reference_top_toolbar = toolbar
    window.reference_command_search = search
    window.reference_pan_button = pan_button
    window.reference_select_button = select_button

    return toolbar


def configure_reference_panel_tabs(window: Any) -> None:
    """Expose the existing panels as one dock with stable reference tabs."""

    tabs = window.reference_panel_tabs
    tabs.clear()
    tabs.setObjectName("reference_panel_tabs")
    tabs.setDocumentMode(True)
    tabs.setTabPosition(QTabWidget.TabPosition.North)
    tabs.addTab(window.side_panel, "Objects")
    tabs.addTab(window.layers, "Layers")
    tabs.addTab(window.groups, "Groups")
    tabs.addTab(window.collision_panel, "Collision")
    window.reference_panel_tabs = tabs


def connect_reference_search(window: Any) -> None:
    """Connect the inline search to the existing command palette when ready."""

    search = getattr(window, "reference_command_search", None)
    palette = getattr(window, "command_palette", None)
    if search is None or palette is None:
        return

    def open_palette() -> None:
        search.clear()
        palette.show()
        palette.raise_()
        palette.activateWindow()

    search.returnPressed.connect(open_palette)


__all__ = [
    "configure_reference_panel_tabs",
    "configure_reference_tool_palette",
    "configure_reference_top_toolbar",
    "connect_reference_search",
]
