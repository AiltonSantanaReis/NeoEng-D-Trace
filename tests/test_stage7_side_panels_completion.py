"""Real Qt regression coverage for the complete Stage 7 side-panel contract."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _Config:
    def get(self, key, default=None):
        del key
        return default

    def set(self, key, value):
        del key, value

    def save(self):
        return None


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication([])


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = np.zeros((120, 160, 4), dtype=np.uint8)
    scene.add_object("A", [(8, 8), (44, 8), (44, 44), (8, 44)], select=True)
    scene.add_object("B", [(32, 32), (72, 32), (72, 72), (32, 72)])
    scene.cmd.clear()
    return scene


def _show_window(qt_app, scene):
    window = MainWindow(scene, _Config())
    window.resize(QSize(1280, 720))
    window.show()
    window._refresh_document_views(project_loaded=True)
    qt_app.processEvents()
    return window


def _assert_toolbar_contract(toolbar, expected_count):
    assert toolbar.isVisible()
    assert len(toolbar.actions()) == expected_count
    assert toolbar.iconSize() == QSize(16, 16)
    for action in toolbar.actions():
        rect = toolbar.actionGeometry(action)
        assert toolbar.rect().contains(rect)
        assert not action.icon().isNull()
        assert action.toolTip()
        assert action.property("commandKey")


def _assert_context_menu_contract(menu, expected_count):
    actions = menu.actions()
    assert len(actions) == expected_count
    for action in actions:
        assert action.text()
        assert action.toolTip()
        assert action.property("commandKey")


def test_objects_panel_has_compact_commands_and_real_selection(qt_app):
    scene = _scene()
    window = _show_window(qt_app, scene)
    try:
        window.compact_panel_tabs.setCurrentWidget(window.side_panel)
        panel = window.side_panel
        qt_app.processEvents()

        _assert_toolbar_contract(panel.properties_action_toolbar, 3)
        _assert_toolbar_contract(panel.modify_action_toolbar, 5)
        _assert_toolbar_contract(panel.export_action_toolbar, 2)
        assert panel.scroll_area.verticalScrollBar().maximum() >= 0
        assert panel.list.count() == 2

        scene.selected_id = None
        panel.refresh()
        assert not panel.transform_group.isEnabled()
        assert not panel.btn_apply_transform.isEnabled()
        assert not panel.properties_action_toolbar.actions()[2].isEnabled()

        item_rect = panel.list.visualItemRect(panel.list.item(0))
        QTest.mouseClick(
            panel.list.viewport(), Qt.MouseButton.LeftButton, pos=item_rect.center()
        )
        qt_app.processEvents()
        assert scene.selected_id == "A"
        assert panel.transform_group.isEnabled()
        assert panel.btn_apply_transform.isEnabled()
        assert panel.properties_action_toolbar.actions()[2].isEnabled()
        assert panel.list.contextMenuPolicy() is Qt.ContextMenuPolicy.CustomContextMenu
        context_menu = panel._build_context_menu()
        assert [action.text() for action in context_menu.actions()] == [
            "Properties",
            "Modify Shape",
            "Export",
        ]
        expected_context_sizes = {
            "Properties": 3,
            "Modify Shape": 5,
            "Export": 2,
        }
        for section in context_menu.actions():
            submenu = section.menu()
            assert submenu is not None
            _assert_context_menu_contract(
                submenu, expected_context_sizes[section.text()]
            )

        collision_action = panel.properties_action_toolbar.actions()[2]
        collision_action.trigger()
        assert "A" in scene.collision_shapes
        assert collision_action.isChecked()
        collision_action.trigger()
        assert "A" not in scene.collision_shapes
        assert not collision_action.isChecked()
    finally:
        window._mark_document_clean()
        window.close()
        qt_app.processEvents()


def test_layers_panel_toolbar_and_selection_are_live(qt_app):
    scene = _scene()
    window = _show_window(qt_app, scene)
    try:
        window.compact_panel_tabs.setCurrentWidget(window.layers)
        panel = window.layers
        qt_app.processEvents()

        _assert_toolbar_contract(panel.action_toolbar, 6)
        assert panel.list.count() == len(scene.layers)
        panel.list.setCurrentRow(0)
        assert panel.list.currentItem() is not None
        layer_id = panel.list.currentItem().data(0x0100)
        assert layer_id == scene.layers[0].id
        assert panel.list.contextMenuPolicy() is Qt.ContextMenuPolicy.CustomContextMenu
        _assert_context_menu_contract(panel._build_context_menu(), 6)

        before = len(scene.layers)
        context_menu = panel._build_context_menu()
        context_menu.actions()[0].trigger()
        qt_app.processEvents()
        assert len(scene.layers) == before + 1
        assert panel.list.count() == len(scene.layers)

        before = len(scene.layers)
        panel.action_toolbar.actions()[0].trigger()
        qt_app.processEvents()
        assert len(scene.layers) == before + 1
        assert panel.list.count() == len(scene.layers)
    finally:
        window._mark_document_clean()
        window.close()
        qt_app.processEvents()


def test_collision_panel_toolbar_and_real_batch_action(qt_app):
    scene = _scene()
    scene.collision_shapes = {
        "A": [(8.0, 8.0), (44.0, 8.0), (44.0, 44.0), (8.0, 44.0)],
        "B": [(32.0, 32.0), (72.0, 32.0), (72.0, 72.0), (32.0, 72.0)],
    }
    window = _show_window(qt_app, scene)
    try:
        window.compact_panel_tabs.setCurrentWidget(window.collision_panel)
        panel = window.collision_panel
        qt_app.processEvents()

        _assert_toolbar_contract(panel.action_toolbar, 3)
        assert panel.strategy_combo.isVisible()
        assert panel.strategy_combo.count() == 3
        assert panel.batch_test_btn.isHidden()
        assert panel.export_btn.isHidden()
        assert panel.auto_gen_btn.isHidden()

        assert panel._sync_collision_manager_from_scene()
        panel.action_toolbar.actions()[0].trigger()
        qt_app.processEvents()
        assert "Collision Test Results" in panel.results_text.toPlainText()
        assert panel.stats_text.isVisibleTo(panel)
        assert panel.contextMenuPolicy() is Qt.ContextMenuPolicy.CustomContextMenu
        _assert_context_menu_contract(panel._build_context_menu(), 3)
    finally:
        window._mark_document_clean()
        window.close()
        qt_app.processEvents()


def test_all_stage7_panels_are_reachable_at_compact_resolution(qt_app):
    scene = _scene()
    window = _show_window(qt_app, scene)
    try:
        for panel in (
            window.side_panel,
            window.layers,
            window.groups,
            window.collision_panel,
        ):
            window.compact_panel_tabs.setCurrentWidget(panel)
            qt_app.processEvents()
            assert panel.isVisibleTo(window)
            assert panel.width() > 0
            assert panel.height() > 0
            assert window.compact_panel_tabs.currentWidget() is panel
        assert (
            window.groups.list.contextMenuPolicy()
            is Qt.ContextMenuPolicy.CustomContextMenu
        )
        _assert_context_menu_contract(window.groups._build_context_menu(), 8)
    finally:
        window._mark_document_clean()
        window.close()
        qt_app.processEvents()
