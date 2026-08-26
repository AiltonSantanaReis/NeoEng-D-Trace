"""Responsive panel layout controller for the main window."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.viewport_chrome import ViewportChrome


class ResponsivePanelLayout:
    """Switch between the desktop splitters and compact panel tabs."""

    BREAKPOINT = 1450
    COMPACT_PANEL_WIDTH = 460
    DESKTOP_PANEL_WIDTH = 540

    def __init__(
        self,
        owner,
        *,
        main_splitter,
        panel_stack,
        compact_panel_tabs,
        reference_panel_tabs,
        reference_tool_palette,
        desktop_panel_splitter,
        right_splitter,
        side_panel,
        layers,
        groups,
        collision_panel,
    ) -> None:
        self.owner = owner
        self.main_splitter = main_splitter
        self.panel_stack = panel_stack
        self.compact_panel_tabs = compact_panel_tabs
        self.reference_panel_tabs = reference_panel_tabs
        self.reference_tool_palette = reference_tool_palette
        self.desktop_panel_splitter = desktop_panel_splitter
        self.right_splitter = right_splitter
        self.side_panel = side_panel
        self.layers = layers
        self.groups = groups
        self.collision_panel = collision_panel
        self.is_compact = False
        self._geometry_update_pending = False

    def update(self, *, force: bool = False) -> None:
        compact = self.owner.width() < self.BREAKPOINT
        if not force and compact == self.is_compact:
            self._schedule_geometry_update()
            return

        if compact:
            self.owner.setMinimumSize(0, 0)
            self._move_panels_to_compact()
            self.panel_stack.setCurrentWidget(self.compact_panel_tabs)
            self.compact_panel_tabs.setMinimumWidth(self.COMPACT_PANEL_WIDTH)
        else:
            self._move_panels_to_desktop()
            self.panel_stack.setCurrentWidget(self.desktop_panel_splitter)

        self._set_reference_toolbar_mode(compact)
        self.is_compact = compact
        self.owner._compact_layout = compact
        self._apply_geometry()
        self._schedule_geometry_update()

    def _schedule_geometry_update(self) -> None:
        """Reapply splitter sizes after Qt completes a native resize pass.

        Windows can deliver the resize event before the central layout has
        received its final size. A second pass prevents QSplitter from
        collapsing the panel stack to zero after the mode switch.
        """

        if self._geometry_update_pending:
            return
        self._geometry_update_pending = True
        QTimer.singleShot(0, self._apply_scheduled_geometry)

    def _apply_scheduled_geometry(self) -> None:
        self._geometry_update_pending = False
        self._apply_geometry()
        self._set_reference_toolbar_mode(self.is_compact)

    def _set_reference_toolbar_mode(self, compact: bool) -> None:
        """Keep the visible reference toolbar usable at compact widths."""

        toolbar = getattr(self.owner, "reference_top_toolbar", None)
        if toolbar is None:
            return
        style = (
            Qt.ToolButtonStyle.ToolButtonIconOnly
            if compact
            else Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        toolbar.setToolButtonStyle(style)
        for button in toolbar.findChildren(QToolButton):
            if button.objectName() != "reference_menu_button":
                button.setToolButtonStyle(style)

        menu_button = getattr(self.owner, "reference_menu_button", None)
        if menu_button is not None:
            menu_button.setMinimumWidth(51)
            menu_button.setMaximumWidth(51)

        search = getattr(self.owner, "reference_command_search", None)
        if search is not None:
            search.setMinimumWidth(180 if compact else 260)
            search.setMaximumWidth(240 if compact else 440)

        focus_button = getattr(self.owner, "reference_focus_button", None)
        if focus_button is not None:
            focus_button.setText("Focus")

    def _apply_geometry(self) -> None:
        """Reserve the visible reference palette, viewport and inspector dock."""

        tool_width = self.reference_tool_palette.minimumWidth()
        total_width = max(1, self.main_splitter.width())
        requested_panel_width = (
            self.COMPACT_PANEL_WIDTH if self.is_compact else self.DESKTOP_PANEL_WIDTH
        )
        panel_width = min(
            requested_panel_width,
            max(1, total_width - tool_width - 1),
        )
        canvas_width = max(1, total_width - tool_width - panel_width)
        self.main_splitter.setSizes([tool_width, canvas_width, panel_width])

        if self.is_compact:
            self.compact_panel_tabs.setCurrentWidget(self.side_panel)
            self.compact_panel_tabs.show()
            self.side_panel.show()
            return

        self.reference_panel_tabs.show()
        self.reference_panel_tabs.setCurrentWidget(self.side_panel)
        self.desktop_panel_splitter.setSizes(
            [max(1, self.desktop_panel_splitter.width())]
        )

    def _detach_panels_from_tabs(self) -> None:
        panels = (self.side_panel, self.layers, self.groups, self.collision_panel)
        for tabs in (self.compact_panel_tabs, self.reference_panel_tabs):
            for widget in panels:
                index = tabs.indexOf(widget)
                if index >= 0:
                    tabs.removeTab(index)
                widget.setParent(None)

    def _add_panels_to_tabs(self, tabs: QTabWidget) -> None:
        panels = (
            (self.side_panel, "Objects"),
            (self.layers, "Layers"),
            (self.groups, "Groups"),
            (self.collision_panel, "Collision"),
        )
        for widget, title in panels:
            tabs.addTab(widget, title)
        tabs.setCurrentIndex(0)
        for index in range(tabs.count()):
            tabs.widget(index).setVisible(index == tabs.currentIndex())

    def _move_panels_to_compact(self) -> None:
        self._detach_panels_from_tabs()
        self._add_panels_to_tabs(self.compact_panel_tabs)
        self.update_titles(
            getattr(self.owner, "translations", {}).get(self.owner.current_lang, {})
        )

    def _move_panels_to_desktop(self) -> None:
        self._detach_panels_from_tabs()
        self._add_panels_to_tabs(self.reference_panel_tabs)
        self.update_titles(
            getattr(self.owner, "translations", {}).get(self.owner.current_lang, {})
        )

    def update_titles(self, translations: dict[str, Any]) -> None:
        titles = (
            translations.get("objects_panel", "Objects"),
            translations.get("layers_panel", "Layers"),
            translations.get("groups_panel", "Groups"),
            translations.get("collision_panel", "Collision"),
        )
        for tabs in (self.compact_panel_tabs, self.reference_panel_tabs):
            if tabs.count() != 4:
                continue
            for index, title in enumerate(titles):
                tabs.setTabText(index, title)


def build_responsive_layout(owner) -> ResponsivePanelLayout:
    """Build the panel layout and attach its public widgets to the owner."""

    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    main_splitter.setSizePolicy(
        QSizePolicy.Policy.Ignored,
        QSizePolicy.Policy.Ignored,
    )
    main_splitter.addWidget(owner.reference_tool_palette)
    owner.viewport_chrome = ViewportChrome(owner, owner.canvas)
    main_splitter.addWidget(owner.viewport_chrome)

    right_splitter = QSplitter(Qt.Orientation.Vertical)
    right_splitter.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    right_splitter.setChildrenCollapsible(False)
    # Retained as a non-rendered compatibility splitter for integrations.

    desktop_panel_splitter = QSplitter(Qt.Orientation.Horizontal)
    desktop_panel_splitter.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    desktop_panel_splitter.setChildrenCollapsible(False)
    reference_panel_tabs = QTabWidget()
    reference_panel_tabs.setObjectName("reference_panel_tabs")
    reference_panel_tabs.setDocumentMode(True)
    reference_panel_tabs.setTabPosition(QTabWidget.TabPosition.North)
    reference_panel_tabs.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    desktop_panel_splitter.addWidget(reference_panel_tabs)

    compact_panel_tabs = QTabWidget()
    compact_panel_tabs.setObjectName('compact_panel_tabs')
    compact_panel_tabs.setAccessibleName('Compact inspector panel tabs')
    compact_panel_tabs.setAccessibleDescription('Switch between objects, layers, groups and collision panels')
    compact_panel_tabs.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    compact_panel_tabs.tabBar().setAccessibleName('Compact inspector panel tabs')
    compact_panel_tabs.tabBar().setAccessibleDescription('Switch between objects, layers, groups and collision panels')
    compact_panel_tabs.tabBar().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    compact_panel_tabs.setDocumentMode(True)
    compact_panel_tabs.setElideMode(Qt.TextElideMode.ElideRight)
    compact_panel_tabs.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )

    panel_stack = QStackedWidget()
    panel_stack.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    panel_stack.addWidget(desktop_panel_splitter)
    panel_stack.addWidget(compact_panel_tabs)

    owner.main_splitter = main_splitter
    owner.right_splitter = right_splitter
    owner.desktop_panel_splitter = desktop_panel_splitter
    owner.reference_panel_tabs = reference_panel_tabs
    owner.compact_panel_tabs = compact_panel_tabs
    owner.panel_stack = panel_stack
    owner._compact_layout = False

    main_splitter.addWidget(panel_stack)
    main_splitter.setChildrenCollapsible(False)
    main_splitter.setSizes([owner.reference_tool_palette.minimumWidth(), 800, 460])
    main_splitter.setStretchFactor(1, 1)
    central_container = QWidget(owner)
    central_layout = QVBoxLayout(central_container)
    central_layout.setContentsMargins(0, 0, 0, 0)
    central_layout.setSpacing(0)
    central_layout.addWidget(owner.reference_top_toolbar)
    central_layout.addWidget(main_splitter, 1)
    owner.reference_central_container = central_container
    owner.setCentralWidget(central_container)
    # Keep the top-level window resizable below the desktop page hint so the
    # responsive controller can switch to the compact panel tabs.
    owner.setMinimumSize(0, 0)

    controller = ResponsivePanelLayout(
        owner,
        main_splitter=main_splitter,
        panel_stack=panel_stack,
        compact_panel_tabs=compact_panel_tabs,
        reference_panel_tabs=reference_panel_tabs,
        reference_tool_palette=owner.reference_tool_palette,
        desktop_panel_splitter=desktop_panel_splitter,
        right_splitter=right_splitter,
        side_panel=owner.side_panel,
        layers=owner.layers,
        groups=owner.groups,
        collision_panel=owner.collision_panel,
    )
    owner._responsive_layout = controller
    controller.update(force=True)
    return controller
