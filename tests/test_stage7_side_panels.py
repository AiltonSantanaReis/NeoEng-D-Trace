"""Regression coverage for the Stage 7 side-panel normalization."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.groups_panel import GroupsPanel
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
    scene.image = np.zeros((40, 40, 4), dtype=np.uint8)
    scene.add_object("A", [(4, 4), (24, 4), (24, 24), (4, 24)], select=True)
    scene.cmd.clear()
    return scene


def test_groups_panel_uses_compact_toolbar_without_removing_commands(qt_app):
    panel = GroupsPanel(_scene())
    panel.resize(QSize(460, 621))
    panel.show()
    qt_app.processEvents()
    try:
        assert panel.action_toolbar.objectName() == "groups_action_toolbar"
        assert panel.action_toolbar.isVisible()
        assert len(panel.action_toolbar.actions()) == 8
        assert panel.action_toolbar.iconSize() == QSize(16, 16)
        assert all(action.toolTip() for action in panel.action_toolbar.actions())
        assert not any(
            button.isVisible()
            for button in (
                panel.btn_new,
                panel.btn_delete,
                panel.btn_add,
                panel.btn_remove,
                panel.btn_up,
                panel.btn_down,
                panel.btn_vis,
                panel.btn_lock,
            )
        )
        assert panel.list.geometry().bottom() < panel.height()
        assert all(
            panel.action_toolbar.actionGeometry(action).bottom()
            <= panel.action_toolbar.rect().bottom()
            for action in panel.action_toolbar.actions()
        )
    finally:
        panel.close()


def test_groups_toolbar_preserves_action_handles_and_localized_labels(qt_app):
    scene = _scene()
    scene.create_group("Actors")
    panel = GroupsPanel(scene)
    panel.show()
    qt_app.processEvents()
    try:
        panel._select_group_id(scene.groups[0].id)
        visible_before = scene.groups[0].visible
        panel.action_toolbar.actions()[6].trigger()
        assert scene.groups[0].visible is not visible_before

        panel.update_language("pt")
        assert panel.action_toolbar.actions()[0].text() == panel.btn_new.text()
        assert panel.action_toolbar.actions()[7].text() == panel.btn_lock.text()
        assert all(action.toolTip() for action in panel.action_toolbar.actions())
    finally:
        panel.close()


def test_groups_panel_remains_reachable_in_main_window_compact_layout(qt_app):
    window = MainWindow(_scene(), _Config())
    window.resize(QSize(1280, 720))
    window.show()
    qt_app.processEvents()
    try:
        window.compact_panel_tabs.setCurrentWidget(window.groups)
        qt_app.processEvents()
        assert window.groups.isVisibleTo(window)
        assert window.groups.action_toolbar.isVisibleTo(window)
        assert window.groups.list.isVisibleTo(window)
        assert window.groups.action_toolbar.width() > 0
        assert window.groups.list.height() >= 58
    finally:
        window._mark_document_clean()
        window.close()
        qt_app.processEvents()
