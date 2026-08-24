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
            if item.objectName() == "focus_button":
                item.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        else:
            toolbar.addAction(item)
            button = toolbar.widgetForAction(item)
            if button is not None:
                action_id = item.property("iconKey") or item.objectName() or item.text()
                button.setObjectName(
                    f"reference_top_action_{str(action_id).replace(' ', '_').lower()}"
                )
                button.setAccessibleName(item.text().replace("\n", " "))
                button.setToolTip(item.toolTip())
                button.setStatusTip(item.statusTip())
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                button.setProperty("iconKey", item.property("iconKey"))
                button.setProperty("uiRole", "reference_top_action")
    toolbar.addSeparator()


def _style_action_button(
    toolbar: QToolBar,
    action: Any,
    *,
    display_text: str,
    width: int,
) -> QToolButton:
    """Give an action-backed button a bounded, reference-safe presentation."""

    button = toolbar.widgetForAction(action)
    if not isinstance(button, QToolButton):
        raise RuntimeError(
            f"reference action did not create a QToolButton: {action.objectName()}"
        )
    button.setText(display_text)
    button.setProperty("referenceShortText", display_text)
    button.setMinimumWidth(width)
    button.setMaximumWidth(width)
    button.setMinimumHeight(58)
    button.setMaximumHeight(66)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    button.setAccessibleName(action.text().replace("\n", " "))
    button.setToolTip(action.toolTip())
    button.setStatusTip(action.statusTip())
    return button


def _command_button(
    window: Any, key: str, text: str, accessible_name: str
) -> QToolButton:
    button = QToolButton(window)
    button.setObjectName(f"reference_command_button_{key}")
    button.setText(text)
    button.setAccessibleName(accessible_name)
    button.setToolTip(text)
    button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    button.setProperty("uiRole", "reference_command_button")
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    configure_widget(button, key, accessible_name=accessible_name)
    return button


def _menu_button(button: QToolButton, actions: tuple[Any, ...]) -> None:
    menu = QMenu(button)
    for action in actions:
        menu.addAction(action)
    button.setMenu(menu)
    button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
    # The command buttons have no standalone action in their body; keep
    # both the main surface and the native arrow wired to the same menu.
    button.clicked.connect(button.showMenu)


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
    toolbar.setMinimumWidth(72)
    toolbar.setMaximumWidth(84)
    toolbar.setProperty("uiRole", "reference_tool_palette")
    for action in window.tool_palette.actions():
        if action.isSeparator():
            toolbar.addSeparator()
        else:
            toolbar.addAction(action)
            button = toolbar.widgetForAction(action)
            if isinstance(button, QToolButton):
                button.setMinimumSize(QSize(44, 32))
                button.setMaximumSize(QSize(56, 36))
                button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                button.setIconSize(QSize(18, 18))
                # The visible rail creates a new QToolButton for the shared
                # QAction. QAction metadata is not guaranteed to populate
                # the widget's accessibility/focus surface, so copy the
                # public feedback explicitly to the button that users see.
                action_id = action.data() or action.objectName()
                button.setObjectName(f"reference_tool_button_{action_id}")
                button.setAccessibleName(action.text().replace("\n", " "))
                button.setToolTip(action.toolTip())
                button.setStatusTip(action.statusTip())
                button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                button.setProperty("iconKey", action.property("iconKey"))
                button.setProperty("uiRole", "reference_tool")
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

    # The reference shell presents one short file command per button. The
    # original project/image/save-as/export actions stay intact in menus; the
    # visible buttons only compose those canonical actions.
    open_button = _command_button(window, "open", "Open", "Open project or image")
    _menu_button(open_button, (window.open_project_action, window.open_image_action))
    save_button = _command_button(window, "save", "Save", "Save project")
    _menu_button(
        save_button, (window.save_project_action, window.save_project_as_action)
    )
    export_button = _command_button(window, "export", "Export", "Export project data")
    _menu_button(
        export_button,
        (
            window.act_export,
            window.act_export_collision_json,
            window.act_export_collision_txt,
        ),
    )
    _add_action_group(toolbar, (open_button, save_button, export_button))

    fit_action = window.tool_palette.navigation_actions["fit_view"]
    focus_action = window.tool_palette.navigation_actions["focus_selected"]
    _add_action_group(toolbar, (fit_action, focus_action))
    fit_button = _style_action_button(
        toolbar, fit_action, display_text="Fit View", width=82
    )
    reference_focus_button = _style_action_button(
        toolbar, focus_action, display_text="Focus", width=72
    )
    fit_button.setObjectName("reference_fit_button")
    reference_focus_button.setObjectName("reference_focus_button")

    view_button = _command_button(window, "view", "View", "View and navigation menu")
    _menu_button(
        view_button,
        (
            window.act_grid,
            window.act_snap,
            window.act_lit,
            window.act_xray1,
            window.act_xray2,
            window.act_xray3,
            window.mask_viewer_action,
            window.settings_action,
        ),
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
    view_button.setProperty("referenceActive", True)
    _add_action_group(toolbar, (view_button, collision_button, parallax_button))

    pan_action = window.tool_palette.navigation_actions["move_viewport"]
    select_action = window.tool_palette._tool_actions["selection"]
    _add_action_group(toolbar, (pan_action, select_action))
    pan_button = _style_action_button(toolbar, pan_action, display_text="Pan", width=64)
    select_button = _style_action_button(
        toolbar, select_action, display_text="Select", width=72
    )
    pan_button.setObjectName("reference_pan_button")
    select_button.setObjectName("reference_select_button")

    _add_action_group(toolbar, (window.undo_action, window.redo_action))
    undo_button = _style_action_button(
        toolbar, window.undo_action, display_text="Undo", width=68
    )
    redo_button = _style_action_button(
        toolbar, window.redo_action, display_text="Redo", width=68
    )
    undo_button.setObjectName("reference_undo_button")
    redo_button.setObjectName("reference_redo_button")

    # Keep the complete application menu available to integrations and
    # keyboard/menu consumers without adding a control absent from the reference.
    menu_button = QToolButton(toolbar)
    menu_button.setObjectName("reference_menu_button")
    menu_button.setText("≡")
    menu_button.setAccessibleName("Application menu")
    menu_button.setToolTip("Application menu")
    menu_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    menu_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
    menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
    menu = QMenu(menu_button)
    application_submenus = []
    for source in (window.file_menu, window.edit_menu, window.view_menu):
        submenu = menu.addMenu(source.title())
        for action in source.actions():
            submenu.addAction(action)
        application_submenus.append((submenu, source))
    menu_button.setMenu(menu)
    menu_button.clicked.connect(menu_button.showMenu)
    menu_button.setVisible(False)
    window.reference_menu_button = menu_button
    window.reference_application_submenus = tuple(application_submenus)
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
    window.reference_open_button = open_button
    window.reference_save_button = save_button
    window.reference_export_button = export_button
    window.reference_fit_button = fit_button
    window.reference_pixel_button = None
    window.reference_pan_button = pan_button
    window.reference_select_button = select_button
    window.reference_focus_button = reference_focus_button
    window.reference_view_button = view_button
    # Compatibility alias: rendering/mask controls now belong to the View menu.
    window.reference_render_button = view_button
    window.reference_collision_button = collision_button
    window.reference_parallax_button = parallax_button
    window.reference_edit_button = None
    window.reference_undo_button = undo_button
    window.reference_redo_button = redo_button

    # QAction remains the source of truth for localization. Refresh the short
    # visible labels whenever any source command changes, without enlarging
    # MainWindow or duplicating command state there.
    source_actions = (
        window.open_project_action,
        window.open_image_action,
        window.save_project_action,
        window.save_project_as_action,
        window.act_export,
        window.act_fit,
        focus_action,
        window.act_grid,
        window.act_snap,
        window.act_lit,
        window.act_xray1,
        window.act_xray2,
        window.act_xray3,
        window.mask_viewer_action,
        window.collision_overlay_action,
        pan_action,
        select_action,
        window.undo_action,
        window.redo_action,
    )
    for action in source_actions:
        action.changed.connect(lambda: refresh_reference_top_toolbar_labels(window))
    refresh_reference_top_toolbar_labels(window)

    return toolbar


def refresh_reference_top_toolbar_labels(window: Any) -> None:
    """Refresh short visible labels after a language change."""

    labels = {
        "en": {
            "open": "Open",
            "save": "Save",
            "export": "Export",
            "fit": "Fit View",
            "pixel": "1:1",
            "focus": "Focus",
            "view": "View",
            "collision": "Collision",
            "parallax": "Parallax",
            "pan": "Pan",
            "select": "Select",
            "undo": "Undo",
            "redo": "Redo",
            "edit": "Edit",
        },
        "pt": {
            "open": "Abrir",
            "save": "Salvar",
            "export": "Exportar",
            "fit": "Ajustar",
            "pixel": "1:1",
            "focus": "Focar",
            "view": "Visualizar",
            "collision": "Colisão",
            "parallax": "Parallax",
            "pan": "Mover",
            "select": "Selecionar",
            "undo": "Desfazer",
            "redo": "Refazer",
            "edit": "Editar",
        },
    }.get(getattr(window, "current_lang", "en"), None)
    if labels is None:
        labels = {
            "open": "Open",
            "save": "Save",
            "export": "Export",
            "fit": "Fit View",
            "pixel": "1:1",
            "focus": "Focus",
            "view": "View",
            "collision": "Collision",
            "parallax": "Parallax",
            "pan": "Pan",
            "select": "Select",
            "undo": "Undo",
            "redo": "Redo",
            "edit": "Edit",
        }

    for submenu, source in getattr(window, "reference_application_submenus", ()):
        submenu.setTitle(source.title())

    for name, key in (
        ("reference_open_button", "open"),
        ("reference_save_button", "save"),
        ("reference_export_button", "export"),
        ("reference_fit_button", "fit"),
        ("reference_pixel_button", "pixel"),
        ("reference_focus_button", "focus"),
        ("reference_view_button", "view"),
        ("reference_collision_button", "collision"),
        ("reference_parallax_button", "parallax"),
        ("reference_edit_button", "edit"),
        ("reference_pan_button", "pan"),
        ("reference_select_button", "select"),
        ("reference_undo_button", "undo"),
        ("reference_redo_button", "redo"),
    ):
        button = getattr(window, name, None)
        if button is not None:
            button.setText(labels[key])
            button.setProperty("referenceShortText", labels[key])


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
    "refresh_reference_top_toolbar_labels",
]
