from __future__ import annotations

from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QTransform
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.lasso_tool import LassoTool
from src.tools.polygonal_lasso import PolygonalLassoTool
from src.tools.rect_selection import RectSelectionTool
from src.tools.selection_tool import SelectionTool
from src.ui.collision_overlay import CollisionOverlay
from src.ui.gizmo import TransformGizmo


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class CanvasProbe:
    def __init__(self):
        self.model = Scene()
        self.model.cmd = CommandManager()
        self.updated = 0
        self._zoom = 1.0
        self._pan = (0.0, 0.0)

    def update(self):
        self.updated += 1

    def get_transform(self):
        return QTransform()

    def image_to_widget(self, x, y):
        return QPointF(float(x), float(y))


def _event(button=Qt.MouseButton.LeftButton, modifiers=Qt.KeyboardModifier.NoModifier):
    event = Mock(spec=QMouseEvent)
    event.button.return_value = button
    event.modifiers.return_value = modifiers
    event.globalPos.return_value = QPoint(12, 14)
    return event


def _paint(callable_to_draw, size=240):
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    callable_to_draw(painter)
    painter.end()
    return image


def test_selection_tool_selects_topmost_object_and_clears_empty_click(qt_app):
    canvas = CanvasProbe()
    canvas.model.add_object("bottom", [(0, 0), (30, 0), (30, 30), (0, 30)])
    canvas.model.add_object("top", [(5, 5), (25, 5), (25, 25), (5, 25)])
    tool = SelectionTool(canvas)

    tool.on_mouse_press(_event(), (10, 10))
    assert canvas.model.selected_id == "top"

    tool.on_mouse_press(_event(), (100, 100))
    assert canvas.model.selected_id is None
    assert canvas.updated == 2
    assert tool._find_object_at(QPointF(-1, -1)) is None


def test_selection_tool_ignores_non_left_and_short_polygons(qt_app):
    canvas = CanvasProbe()
    canvas.model.objects = {"short": type("Record", (), {"polygon": [(0, 0)]})()}
    tool = SelectionTool(canvas)

    tool.on_mouse_press(_event(Qt.MouseButton.RightButton), (0, 0))
    tool.on_mouse_move(_event(), (0, 0))
    tool.on_mouse_release(_event(), (0, 0))
    tool.on_double_click(_event(), (0, 0))
    tool.on_cancel()
    tool.draw_overlay(Mock())

    assert canvas.updated == 0
    assert tool._find_object_at(QPointF(0, 0)) is None


def test_lasso_mouse_flow_sampling_commit_undo_redo_and_cancel(qt_app):
    canvas = CanvasProbe()
    tool = LassoTool(canvas)
    left = _event()

    tool.on_mouse_press(left, (2, 2))
    tool.on_mouse_move(left, (3, 2))
    tool.on_mouse_move(left, (30, 2))
    tool.on_mouse_move(left, (30, 30))
    tool.on_mouse_move(left, (2, 30))
    assert len(tool._points) == 4

    tool.on_mouse_release(left, (2, 30))
    assert len(canvas.model.objects) == 1
    assert tool._points == []
    assert canvas.model.cmd.undo_count == 1

    tool.undo_last_action()
    assert canvas.model.objects == {}
    tool.redo_last_action()
    assert len(canvas.model.objects) == 1

    tool._points = [(1, 1)]
    tool._last_point = None
    tool._is_drawing = True
    tool.on_mouse_move(left, (8, 8))
    assert tool._points[-1] == (8, 8)
    tool.cancel()
    tool.update_language("pt")
    assert tool.current_lang == "pt"
    assert tool._is_drawing is False


def test_lasso_incomplete_release_right_click_and_overlay(qt_app, monkeypatch):
    canvas = CanvasProbe()
    tool = LassoTool(canvas)
    left = _event()
    tool.on_mouse_press(left, (0, 0))
    tool.on_mouse_move(left, (10, 0))
    tool.on_mouse_release(left, (10, 0))
    assert tool._points == [(0, 0), (10, 0)]

    calls = []
    monkeypatch.setattr(tool, "show_context_menu", lambda event: calls.append(event))
    right = _event(Qt.MouseButton.RightButton)
    tool.on_mouse_press(right, (0, 0))
    assert calls == [right]

    _paint(lambda painter: tool.draw_overlay(painter))
    tool._points = []
    _paint(lambda painter: tool.draw_overlay(painter))


def test_polygonal_click_close_double_click_and_failure_preservation(
    qt_app, monkeypatch
):
    canvas = CanvasProbe()
    tool = PolygonalLassoTool(canvas)
    left = _event()
    for point in ((5, 5), (40, 5), (40, 40), (5, 40)):
        tool.on_mouse_press(left, point)
    tool.on_mouse_move(left, (7, 7))
    tool.on_mouse_press(left, (6, 6))

    assert len(canvas.model.objects) == 1
    assert tool._vertices == []
    assert tool._preview_point is None

    tool._vertices = [(0, 0), (20, 0)]
    tool.on_double_click(left, (20, 0))
    assert len(tool._vertices) == 2

    tool._vertices = [(0, 0), (20, 0), (10, 20)]
    monkeypatch.setattr(tool, "commit_selection", lambda: None)
    tool.on_double_click(left, (10, 20))
    assert len(tool._vertices) == 3

    tool.on_mouse_press(left, (object(), 2))
    assert len(tool._vertices) == 3


def test_polygonal_overlay_history_context_branch_and_cancel(qt_app, monkeypatch):
    canvas = CanvasProbe()
    tool = PolygonalLassoTool(canvas)
    tool._vertices = [(10, 10), (60, 10), (60, 60), (10, 60)]
    tool._preview_point = (12, 12)
    _paint(lambda painter: tool.draw_overlay(painter))

    object_id = tool.commit_selection()
    assert object_id in canvas.model.objects
    tool.undo_last_action()
    assert canvas.model.objects == {}
    tool.redo_last_action()
    assert object_id in canvas.model.objects

    calls = []
    monkeypatch.setattr(tool, "show_context_menu", lambda event: calls.append(event))
    right = _event(Qt.MouseButton.RightButton)
    tool.on_mouse_press(right, (0, 0))
    assert calls == [right]

    tool.cancel()
    tool.update_language("pt")
    assert tool._vertices == []
    assert tool._preview_point is None
    assert tool.current_lang == "pt"
    _paint(lambda painter: tool.draw_overlay(painter))


def test_rect_selection_drag_square_commit_and_history(qt_app):
    canvas = CanvasProbe()
    tool = RectSelectionTool(canvas)
    left = _event()
    shifted = _event(modifiers=Qt.KeyboardModifier.ShiftModifier)

    tool.on_mouse_press(left, (20, 20))
    tool.on_mouse_move(shifted, (5, 10))
    assert tool._end_point == (5, 5)
    _paint(lambda painter: tool.draw_overlay(painter))
    tool.on_mouse_release(left, (5, 10))

    assert len(canvas.model.objects) == 1
    object_id = next(iter(canvas.model.objects))
    assert canvas.model.objects[object_id].polygon == [
        (5, 5),
        (20, 5),
        (20, 20),
        (5, 20),
    ]
    tool.undo_last_action()
    assert canvas.model.objects == {}
    tool.redo_last_action()
    assert object_id in canvas.model.objects


def test_rect_selection_negative_drag_degenerate_cancel_and_right_click(
    qt_app, monkeypatch
):
    canvas = CanvasProbe()
    tool = RectSelectionTool(canvas)
    left = _event()
    tool.on_mouse_press(left, (20, 20))
    tool.on_mouse_move(left, (5, 8))
    assert tool._end_point == (5, 8)
    tool.on_mouse_release(left, (5, 8))
    assert len(canvas.model.objects) == 1

    tool._start_point = (1, 1)
    tool._end_point = (1.5, 8)
    assert tool.commit_selection() is None
    tool._end_point = None
    assert tool.commit_selection() is None

    calls = []
    monkeypatch.setattr(tool, "show_context_menu", lambda event: calls.append(event))
    right = _event(Qt.MouseButton.RightButton)
    tool.on_mouse_press(right, (0, 0))
    assert calls == [right]

    tool.cancel()
    tool.update_language("pt")
    assert tool._start_point is None
    assert tool._end_point is None
    assert tool._is_selecting is False
    assert tool.current_lang == "pt"
    _paint(lambda painter: tool.draw_overlay(painter))


@pytest.mark.parametrize(
    ("point", "expected"),
    [
        (QPointF(100, 100), TransformGizmo.CENTER),
        (QPointF(150, 100), TransformGizmo.AXIS_X),
        (QPointF(100, 150), TransformGizmo.AXIS_Y),
        (QPointF(20, 20), TransformGizmo.NONE),
    ],
)
def test_gizmo_hit_testing_and_hover_transitions(point, expected):
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(100, 100))
    assert gizmo.hit_test(point) == expected

    changed = gizmo.update_hover(point)
    assert changed is (expected != TransformGizmo.NONE)
    assert gizmo.update_hover(point) is False


@pytest.mark.parametrize(
    "active_axis",
    [TransformGizmo.NONE, TransformGizmo.AXIS_X, TransformGizmo.AXIS_Y],
)
def test_gizmo_draws_each_active_state_offscreen(qt_app, active_axis):
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(80, 80))
    gizmo.active_axis = active_axis
    gizmo.hover_axis = TransformGizmo.CENTER

    image = _paint(lambda painter: gizmo.draw(painter), size=220)

    assert image.pixelColor(80, 80).alpha() > 0


def test_collision_overlay_visibility_shapes_colors_and_centers(qt_app):
    scene = Scene()
    scene.collision_shapes = {
        "one": [(10, 10), (40, 10), (40, 40), (10, 40)],
        "two": [(50, 10), (80, 10), (80, 40), (50, 40)],
        "short": [(1, 1), (2, 2)],
    }
    overlay = CollisionOverlay(scene)
    overlay.update_collision_results(
        [
            {
                "obj1_id": "one",
                "obj2_id": "two",
                "colliding": True,
                "mtv": [12.0, 0.0],
            },
            {"obj1_id": "one", "obj2_id": "two", "colliding": False},
            {
                "obj1_id": 1,
                "obj2_id": "two",
                "colliding": True,
                "mtv": [1, 2],
            },
        ]
    )

    blank = _paint(lambda painter: overlay.draw(painter, 1.0, (0.0, 0.0)))
    assert blank.pixelColor(20, 20).alpha() == 0

    overlay.set_visible(True)
    rendered = _paint(lambda painter: overlay.draw(painter, 2.0, (4.0, 6.0)))
    assert rendered.pixelColor(54, 56).alpha() > 0
    assert overlay._get_shape_color("one") == overlay.collision_colors["collision"]
    no_collision = overlay.collision_colors["no_collision"]
    assert overlay._get_shape_color("missing") == no_collision
    assert overlay._get_shape_center("one") == (25.0, 25.0)
    assert overlay._get_shape_center("missing") is None


def test_collision_overlay_skips_invalid_indicators_and_zero_mtv(qt_app):
    scene = Scene()
    scene.collision_shapes = {
        "one": [(0, 0), (10, 0), (10, 10)],
        "two": [(20, 0), (30, 0), (30, 10)],
    }
    overlay = CollisionOverlay(scene)
    overlay.set_visible(True)
    overlay.update_collision_results(
        [
            {"colliding": True},
            {"obj1_id": "one", "obj2_id": "two", "colliding": True, "mtv": [0, 0]},
            {"obj1_id": "one", "obj2_id": "two", "colliding": True, "mtv": [1]},
        ]
    )

    _paint(lambda painter: overlay.draw(painter, 1.0, (0.0, 0.0)))
    _paint(lambda painter: overlay._draw_collision_shapes(painter, 0.0))
