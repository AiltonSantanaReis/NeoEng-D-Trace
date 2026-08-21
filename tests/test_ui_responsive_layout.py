"""Regression tests for the responsive MainWindow layout."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QSizePolicy

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


def test_compact_layout_fits_requested_resolutions_and_restores_desktop(qt_app):
    window = _window()
    window.show()
    qt_app.processEvents()

    try:
        for width, height in ((1366, 768), (1280, 720)):
            window.resize(QSize(width, height))
            qt_app.processEvents()

            assert (window.width(), window.height()) == (width, height)
            assert window._compact_layout is True
            assert window.panel_stack.currentWidget() is window.compact_panel_tabs
            assert window.toolbar.isVisible() is False
            assert window.main_splitter.sizes()[2] >= 450
            assert window.compact_panel_tabs.width() >= 450
            assert window.compact_panel_tabs.currentWidget() is window.side_panel
            assert window.side_panel.width() >= 440
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
        assert window.toolbar.isVisible() is True
        assert window.compact_panel_tabs.count() == 0
        assert window.right_splitter.count() == 3
        assert window.desktop_panel_splitter.count() == 2
        assert window.side_panel.parent() is window.right_splitter
        assert window.layers.parent() is window.right_splitter
        assert window.groups.parent() is window.right_splitter
        assert window.collision_panel.parent() is window.desktop_panel_splitter
        assert window.main_splitter.sizes()[2] >= 790
        assert all(size > 0 for size in window.desktop_panel_splitter.sizes())
        assert window.right_splitter.width() > 0
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
