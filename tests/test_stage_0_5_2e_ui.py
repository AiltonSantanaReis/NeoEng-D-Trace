import pytest

pytest.importorskip("PySide6")

from unittest.mock import Mock

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.base_tool import BaseTool
from src.tools.pen_tool import BezierNode, PenTool
from src.tools.polygonal_lasso import PolygonalLassoTool


class FakeCanvas:
    def __init__(self):
        self._zoom = 2.0
        self._pan = [10.0, 20.0]
        self.model = Scene()
        self.model.cmd = CommandManager()
        self.updated = 0

    def get_zoom(self):
        return Mock()

    def image_to_widget(self, x, y):
        return Mock()

    def update(self):
        self.updated += 1


def test_base_tool_uses_numeric_zoom_fallback():
    tool = BaseTool(FakeCanvas())
    assert tool.get_canvas_zoom() == 2.0
    assert tool.image_to_screen(5.0, 7.0) == (20.0, 34.0)


def test_pen_hit_testing_survives_invalid_zoom_provider():
    canvas = FakeCanvas()
    tool = PenTool(canvas)
    node = BezierNode((100.0, 200.0))
    tool._nodes = [node]
    assert tool._get_anchor_at_point((100.0, 200.0)) is node


def test_polygonal_double_click_commits_and_clears_successful_polygon():
    canvas = FakeCanvas()
    tool = PolygonalLassoTool(canvas)
    tool._vertices = [(0.0, 0.0), (100.0, 0.0), (50.0, 100.0)]
    tool._preview_point = (60.0, 60.0)
    event = Mock(spec=QMouseEvent)

    tool.on_double_click(event, (50.0, 100.0))

    assert len(canvas.model.objects) == 1
    assert tool._vertices == []
    assert tool._preview_point is None
    assert canvas.updated == 1


def test_polygonal_double_click_preserves_incomplete_selection():
    canvas = FakeCanvas()
    tool = PolygonalLassoTool(canvas)
    tool._vertices = [(0.0, 0.0), (100.0, 0.0)]
    event = Mock(spec=QMouseEvent)

    tool.on_double_click(event, (100.0, 0.0))

    assert tool._vertices == [(0.0, 0.0), (100.0, 0.0)]
    assert canvas.model.objects == {}
