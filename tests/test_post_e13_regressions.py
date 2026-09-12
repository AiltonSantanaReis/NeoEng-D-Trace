"""Focused regressions for the post-E13 interaction and visual contracts."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.ellipse_selection import EllipseSelectionTool
from src.tools.pen_tool import PenTool
from src.tools.polygonal_lasso import PolygonalLassoTool
from src.ui.collision_visuals import collision_fill_brush, collision_outline_pen


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _Canvas:
    def __init__(self, scene):
        self.model = scene
        self.updates = 0

    def update(self):
        self.updates += 1

    def get_zoom(self):
        return 1.0

    def get_transform(self):
        return QTransform()

    def setFocus(self, *_args):
        return None


class _MouseEvent:
    def __init__(self, button=Qt.MouseButton.LeftButton):
        self._button = button

    def button(self):
        return self._button


def _scene_canvas():
    scene = Scene()
    scene.cmd = CommandManager()
    return scene, _Canvas(scene)


def test_pen_undo_redo_is_local_to_uncommitted_anchors(qt_app):
    scene, canvas = _scene_canvas()
    tool = PenTool(canvas)
    event = _MouseEvent()

    tool.on_mouse_press(event, (10, 10))
    tool.on_mouse_press(event, (80, 10))
    tool.on_mouse_press(event, (80, 80))
    assert len(tool._nodes) == 3
    assert scene.cmd.undo_count == 0

    assert tool.on_undo() is True
    assert len(tool._nodes) == 2
    assert len(scene.objects) == 0
    assert tool.on_redo() is True
    assert len(tool._nodes) == 3
    assert len(scene.objects) == 0


def test_polygonal_close_consumes_the_first_post_commit_click(qt_app):
    scene, canvas = _scene_canvas()
    tool = PolygonalLassoTool(canvas)
    event = _MouseEvent()
    for point in ((10, 10), (80, 10), (80, 80)):
        tool.on_mouse_press(event, point)

    tool.on_double_click(event, (80, 80))
    assert len(scene.objects) == 1
    tool.on_mouse_press(event, (160, 160))
    assert tool._vertices == []
    tool.on_mouse_press(event, (180, 180))
    assert tool._vertices == [(180.0, 180.0)]


def test_thin_ellipse_is_promoted_to_the_smallest_valid_scene_polygon(qt_app):
    scene, canvas = _scene_canvas()
    tool = EllipseSelectionTool(canvas)
    tool._center = (100.0, 100.0)
    tool._radius_x = 40.0
    tool._radius_y = 0.25

    object_id = tool.commit_selection()
    assert object_id is not None
    assert len(scene.objects[object_id].polygon) >= 3


def test_collision_visual_style_is_shared_by_viewport_and_mask_contracts():
    pen = collision_outline_pen()
    brush = collision_fill_brush()
    assert pen.color().getRgb()[:3] == (0, 255, 0)
    assert pen.width() == 2
    assert brush.getRgb() == (0, 255, 0, 50)
