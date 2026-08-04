"""Qt coverage for Stage 5 package 5A creation paths."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.ellipse_selection import EllipseSelectionTool
from src.tools.lasso_tool import LassoTool
from src.tools.magnetic_lasso import MagneticLassoTool
from src.tools.pen_tool import PenTool
from src.tools.polygonal_lasso import PolygonalLassoTool
from src.tools.rect_selection import RectSelectionTool
from src.ui.canvas_view import CanvasView

SQUARE = [(10, 10), (70, 10), (70, 70), (10, 70)]
TOOL_NAMES = (
    "lasso",
    "polygonal",
    "magnetic",
    "pen",
    "rectangle",
    "ellipse",
)


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def _canvas(with_manager: bool = True) -> CanvasView:
    scene = Scene()
    scene.cmd = CommandManager() if with_manager else None
    return CanvasView(scene)


def _configured_tool(name: str, canvas: CanvasView):
    if name == "lasso":
        tool = LassoTool(canvas)
        tool._points = list(SQUARE)
        return tool, tool.commit_selection
    if name == "polygonal":
        tool = PolygonalLassoTool(canvas)
        tool._vertices = list(SQUARE)
        return tool, tool.commit_selection
    if name == "magnetic":
        tool = MagneticLassoTool(canvas)
        return tool, lambda: tool.commit_selection(SQUARE)
    if name == "pen":
        tool = PenTool(canvas)
        tool._generate_curve_points = lambda: list(SQUARE)
        return tool, tool.commit_selection
    if name == "rectangle":
        tool = RectSelectionTool(canvas)
        tool._start_point = (10, 10)
        tool._end_point = (70, 70)
        return tool, tool.commit_selection
    if name == "ellipse":
        tool = EllipseSelectionTool(canvas)
        tool._center = (40, 40)
        tool._radius_x = 30
        tool._radius_y = 20
        return tool, tool.commit_selection
    raise AssertionError(name)


@pytest.mark.parametrize("tool_name", TOOL_NAMES)
def test_active_tool_creation_is_one_history_entry(qt_app, tool_name):
    canvas = _canvas(with_manager=True)
    _, commit = _configured_tool(tool_name, canvas)

    object_id = commit()

    assert object_id is not None
    assert object_id in canvas.model.objects
    assert canvas.model.selected_id == object_id
    assert canvas.model.cmd.undo_count == 1
    assert canvas.model.cmd.redo_count == 0


@pytest.mark.parametrize("tool_name", TOOL_NAMES)
def test_active_tool_blocks_creation_without_manager(
    qt_app,
    monkeypatch,
    tool_name,
):
    canvas = _canvas(with_manager=False)
    _, commit = _configured_tool(tool_name, canvas)
    critical = []
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.critical",
        lambda *args, **kwargs: critical.append(args),
    )

    object_id = commit()

    assert object_id is None
    assert canvas.model.objects == {}
    assert len(critical) == 1
    assert "Undo/Redo command history is unavailable" in critical[0][2]


def test_canvas_native_creation_uses_command_history(qt_app):
    canvas = _canvas(with_manager=True)

    object_id = canvas._commit_native_polygon(SQUARE)

    assert object_id is not None
    assert object_id in canvas.model.objects
    assert canvas.model.selected_id == object_id
    assert canvas.model.cmd.undo_count == 1


def test_canvas_native_creation_blocks_without_manager(qt_app, monkeypatch):
    canvas = _canvas(with_manager=False)
    critical = []
    monkeypatch.setattr(
        "src.ui.canvas_view.QMessageBox.critical",
        lambda *args, **kwargs: critical.append(args),
    )

    object_id = canvas._commit_native_polygon(SQUARE)

    assert object_id is None
    assert canvas.model.objects == {}
    assert len(critical) == 1
    assert "Undo/Redo command history is unavailable" in critical[0][2]


def test_canvas_native_creation_reports_failed_command(qt_app, monkeypatch):
    canvas = _canvas(with_manager=True)
    critical = []
    monkeypatch.setattr(
        "src.ui.canvas_view.QMessageBox.critical",
        lambda *args, **kwargs: critical.append(args),
    )

    object_id = canvas._commit_native_polygon([(0, 0), (0, 0), (0, 0)])

    assert object_id is None
    assert canvas.model.objects == {}
    assert canvas.model.cmd.undo_count == 0
    assert len(critical) == 1
    assert critical[0][1] == "Edit Failed"
