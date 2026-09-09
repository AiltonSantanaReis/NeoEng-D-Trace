"""Regression tests for the responsive MainWindow layout."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QSizePolicy, QToolButton

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default

    def set(self, key, value):
        del key, value

    def save(self):
        return None


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication([])


def _window() -> MainWindow:
    scene = Scene()
    scene.cmd = CommandManager()
    return MainWindow(scene, _ConfigStub())


def _assert_only_current_tab_visible(window, tabs):
    current_index = tabs.currentIndex()
    assert current_index >= 0
    for index in range(tabs.count()):
        page = tabs.widget(index)
        expected = index == current_index
        assert page.isVisible() is expected
        assert page.isVisibleTo(window) is expected


def test_initial_tab_pages_hide_inactive_pages(qt_app):
    window = _window()
    window.resize(QSize(1920, 1080))
    window.show()
    qt_app.processEvents()
    try:
        _assert_only_current_tab_visible(window, window.reference_panel_tabs)

        window.resize(QSize(1280, 720))
        qt_app.processEvents()
        _assert_only_current_tab_visible(window, window.compact_panel_tabs)

        window.resize(QSize(1920, 1080))
        qt_app.processEvents()
        _assert_only_current_tab_visible(window, window.reference_panel_tabs)
    finally:
        window._mark_document_clean()
        window.close()


def test_compact_layout_fits_requested_resolutions_and_restores_desktop(qt_app):
    window = _window()
    window.show()
    qt_app.processEvents()

    try:
        assert window.minimumWidth() < 1280
        assert window.minimumHeight() < 720
        for width, height in ((1366, 768), (1280, 720)):
            window.resize(QSize(width, height))
            qt_app.processEvents()

            assert (window.width(), window.height()) == (width, height)
            assert window._compact_layout is True
            assert window.panel_stack.currentWidget() is window.compact_panel_tabs
            assert window.reference_top_toolbar.isVisibleTo(window)
            assert (
                window.reference_top_toolbar.toolButtonStyle().name
                == "ToolButtonIconOnly"
            )
            assert window.main_splitter.sizes()[2] >= 380
            assert window.compact_panel_tabs.width() >= 380
            assert window.compact_panel_tabs.currentWidget() is window.side_panel
            assert window.side_panel.width() >= 360
            assert (
                window.panel_stack.sizePolicy().horizontalPolicy()
                == QSizePolicy.Policy.Expanding
            )
            assert window.compact_panel_tabs.count() == 4
            assert window.compact_panel_tabs.indexOf(window.collision_panel) >= 0
            assert window.compact_panel_tabs.indexOf(window.side_panel) >= 0
            assert window.compact_panel_tabs.indexOf(window.layers) >= 0
            assert window.compact_panel_tabs.indexOf(window.groups) >= 0
            assert window.compact_panel_tabs.indexOf(window.collision_panel) >= 0

        window.resize(QSize(1920, 1080))
        qt_app.processEvents()

        assert window._compact_layout is False
        assert window.panel_stack.currentWidget() is window.desktop_panel_splitter
        assert window.reference_top_toolbar.isVisibleTo(window)
        assert (
            window.reference_top_toolbar.toolButtonStyle().name
            == "ToolButtonTextUnderIcon"
        )
        desktop_buttons = window.reference_top_toolbar.findChildren(QToolButton)
        assert all(
            button.width() >= button.sizeHint().width()
            for button in desktop_buttons
            if button.objectName() != "reference_menu_button"
        )
        assert window.compact_panel_tabs.count() == 0
        assert window.reference_panel_tabs.count() == 4
        assert window.desktop_panel_splitter.count() == 1
        assert window.desktop_panel_splitter.widget(0) is window.reference_panel_tabs
        assert all(
            window.reference_panel_tabs.indexOf(panel) >= 0
            for panel in (
                window.side_panel,
                window.layers,
                window.groups,
                window.collision_panel,
            )
        )
        assert window.reference_tool_palette.isVisibleTo(window)
        assert window.reference_tool_palette.width() == 148
        assert window.main_splitter.sizes()[2] >= 400
        assert window.layers.width() >= window.layers.minimumSizeHint().width()
        assert window.desktop_panel_splitter.sizes()[0] > 0
        assert window.reference_panel_tabs.width() > 0
        assert window.collision_panel.width() > 0
    finally:
        window._mark_document_clean()
        window.close()


def test_compact_panel_titles_follow_language_and_exports_remain_accessible(
    qt_app,
):
    window = _window()
    window.show()
    qt_app.processEvents()

    try:
        window.resize(QSize(1280, 720))
        qt_app.processEvents()
        assert [window.compact_panel_tabs.tabText(i) for i in range(4)] == [
            "Objects",
            "Layers",
            "Groups",
            "Collision",
        ]

        window.set_language("pt")
        assert [window.compact_panel_tabs.tabText(i) for i in range(4)] == [
            "Objetos",
            "Camadas",
            "Grupos",
            "Colisão",
        ]

        menu_actions = set(window.file_menu.actions())
        assert {
            window.act_export,
            window.act_export_collision_json,
            window.act_export_collision_txt,
        }.issubset(menu_actions)
    finally:
        window._mark_document_clean()
        window.close()


def test_panel_splitters_cannot_collapse_during_responsive_switch(qt_app):
    window = _window()
    window.show()
    qt_app.processEvents()

    try:
        assert window.main_splitter.childrenCollapsible() is False
        assert window.desktop_panel_splitter.childrenCollapsible() is False
        assert window.right_splitter.childrenCollapsible() is False
        assert (
            window.panel_stack.sizePolicy().verticalPolicy()
            == QSizePolicy.Policy.Expanding
        )
    finally:
        window._mark_document_clean()
        window.close()


def test_compact_layout_constrains_toolbar_and_inspector_content(qt_app):
    window = _window()
    window.resize(QSize(1280, 720))
    window.show()
    qt_app.processEvents()

    try:
        toolbar_rect = window.reference_top_toolbar.geometry()
        panel_rect = window.compact_panel_tabs.geometry()
        content = window.side_panel.scroll_area.widget()
        viewport = window.side_panel.scroll_area.viewport()

        assert toolbar_rect.right() <= window.centralWidget().rect().right()
        assert panel_rect.right() <= window.main_splitter.rect().right()
        assert content.width() <= viewport.width()
        assert window.reference_top_toolbar.minimumWidth() == 0
    finally:
        window._mark_document_clean()
        window.close()


def test_compact_language_updates_search_prompts_and_scenario_menu(qt_app):
    window = _window()
    window.resize(QSize(1280, 720))
    window.show()
    qt_app.processEvents()

    try:
        window.set_language("pt")
        qt_app.processEvents()
        assert window.side_panel.search_input.placeholderText() == "Pesquisar objetos"
        assert window.layers.search_input.placeholderText() == "Pesquisar camadas"
        assert window.scenario_menu.title() == "Cenário"
        assert window.scenario_open_action.text() == "Abrir Editor de Cenário"
        assert window.reference_open_button.text() == "Abrir"
    finally:
        window._mark_document_clean()
        window.close()
