"""Responsive panel layout controller for the main window."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QSizePolicy, QSplitter, QStackedWidget, QTabWidget


class ResponsivePanelLayout:
    """Switch between the desktop splitters and compact panel tabs."""

    BREAKPOINT = 1450
    COMPACT_PANEL_WIDTH = 460
    DESKTOP_PANEL_WIDTH = 800

    def __init__(
        self,
        owner,
        *,
        main_splitter,
        panel_stack,
        compact_panel_tabs,
        desktop_panel_splitter,
        right_splitter,
        toolbar,
        side_panel,
        layers,
        groups,
        collision_panel,
    ) -> None:
        self.owner = owner
        self.main_splitter = main_splitter
        self.panel_stack = panel_stack
        self.compact_panel_tabs = compact_panel_tabs
        self.desktop_panel_splitter = desktop_panel_splitter
        self.right_splitter = right_splitter
        self.toolbar = toolbar
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

        self.toolbar.setVisible(not compact)
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

    def _apply_geometry(self) -> None:
        """Reserve a visible panel region for the current responsive mode."""

        tool_width = self.owner.tool_palette.recommended_width()
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

        available_width = max(2, self.desktop_panel_splitter.width())
        collision_minimum = max(
            1,
            self.collision_panel.minimumSizeHint().width(),
        )
        collision_width = min(collision_minimum, available_width - 1)
        right_width = max(1, available_width - collision_width)
        self.desktop_panel_splitter.setSizes([right_width, collision_width])
        for widget in (
            self.side_panel,
            self.layers,
            self.groups,
            self.collision_panel,
        ):
            widget.show()

    def _move_panels_to_compact(self) -> None:
        for widget in (
            self.side_panel,
            self.layers,
            self.groups,
            self.collision_panel,
        ):
            widget.setParent(None)
        self.compact_panel_tabs.addTab(self.side_panel, "Objects")
        self.compact_panel_tabs.addTab(self.layers, "Layers")
        self.compact_panel_tabs.addTab(self.groups, "Groups")
        self.compact_panel_tabs.addTab(self.collision_panel, "Collision")
        self.update_titles(
            getattr(self.owner, "translations", {}).get(self.owner.current_lang, {})
        )

    def _move_panels_to_desktop(self) -> None:
        for widget in (
            self.side_panel,
            self.layers,
            self.groups,
            self.collision_panel,
        ):
            index = self.compact_panel_tabs.indexOf(widget)
            if index >= 0:
                self.compact_panel_tabs.removeTab(index)
            widget.setParent(None)
        self.right_splitter.addWidget(self.side_panel)
        self.right_splitter.addWidget(self.layers)
        self.right_splitter.addWidget(self.groups)
        self.desktop_panel_splitter.addWidget(self.collision_panel)
        for widget in (self.side_panel, self.layers, self.groups, self.collision_panel):
            widget.show()
        self.right_splitter.setMaximumSize(16777215, 16777215)
        self.desktop_panel_splitter.setMaximumSize(16777215, 16777215)
        self.right_splitter.setSizes([250, 250, 250])

    def update_titles(self, translations: dict[str, Any]) -> None:
        if self.compact_panel_tabs.count() != 4:
            return
        titles = (
            translations.get("objects_panel", "Objects"),
            translations.get("layers_panel", "Layers"),
            translations.get("groups_panel", "Groups"),
            translations.get("collision_panel", "Collision"),
        )
        for index, title in enumerate(titles):
            self.compact_panel_tabs.setTabText(index, title)


def build_responsive_layout(owner) -> ResponsivePanelLayout:
    """Build the panel layout and attach its public widgets to the owner."""

    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    main_splitter.setSizePolicy(
        QSizePolicy.Policy.Ignored,
        QSizePolicy.Policy.Ignored,
    )
    main_splitter.addWidget(owner.tool_palette)
    main_splitter.addWidget(owner.canvas)

    right_splitter = QSplitter(Qt.Orientation.Vertical)
    right_splitter.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    right_splitter.setChildrenCollapsible(False)
    right_splitter.addWidget(owner.side_panel)
    right_splitter.addWidget(owner.layers)
    right_splitter.addWidget(owner.groups)

    desktop_panel_splitter = QSplitter(Qt.Orientation.Horizontal)
    desktop_panel_splitter.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding,
    )
    desktop_panel_splitter.setChildrenCollapsible(False)
    desktop_panel_splitter.addWidget(right_splitter)
    desktop_panel_splitter.addWidget(owner.collision_panel)

    compact_panel_tabs = QTabWidget()
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
    owner.compact_panel_tabs = compact_panel_tabs
    owner.panel_stack = panel_stack
    owner._compact_layout = False

    main_splitter.addWidget(panel_stack)
    main_splitter.setChildrenCollapsible(False)
    main_splitter.setSizes([owner.tool_palette.recommended_width(), 800, 460])
    main_splitter.setStretchFactor(1, 1)
    owner.setCentralWidget(main_splitter)
    # Keep the top-level window resizable below the desktop page hint so the
    # responsive controller can switch to the compact panel tabs.
    owner.setMinimumSize(0, 0)

    controller = ResponsivePanelLayout(
        owner,
        main_splitter=main_splitter,
        panel_stack=panel_stack,
        compact_panel_tabs=compact_panel_tabs,
        desktop_panel_splitter=desktop_panel_splitter,
        right_splitter=right_splitter,
        toolbar=owner.toolbar,
        side_panel=owner.side_panel,
        layers=owner.layers,
        groups=owner.groups,
        collision_panel=owner.collision_panel,
    )
    owner._responsive_layout = controller
    controller.update(force=True)
    return controller
