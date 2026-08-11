"""Stage 11 branch contracts for the persistent Bézier pen tool."""

from __future__ import annotations

import copy
import math
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QMessageBox

import src.tools.pen_tool as pen_module
from src.core.commands import CommandManager, CommandStatus, CreateBezierObjectCommand
from src.models.scene import Scene
from src.tools.pen_tool import BezierNode, PenTool, _HandleEditState

BEZIERS = [((0.0, 0.0), (0.0, -20.0), (20.0, -20.0), (20.0, 0.0))]


class _Canvas:
    def __init__(self, model=None):
        self.model = model
        self.updates = 0
        self._zoom = 1.0

    def update(self):
        self.updates += 1

    def get_zoom(self):
        return self._zoom

    def get_transform(self):
        return QTransform()


class _Event:
    def __init__(self, *, button=None, key=None):
        self._button = button
        self._key = key

    def button(self):
        return self._button

    def key(self):
        return self._key

    def globalPos(self):
        return QPoint(0, 0)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def quiet_messages(monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)


def _scene_tool(*, manager=True):
    scene = Scene()
    scene.cmd = CommandManager() if manager else None
    return scene, PenTool(_Canvas(scene))


def _create_selected_curve(scene: Scene) -> str:
    result = scene.cmd.execute(
        CreateBezierObjectCommand(BEZIERS, object_id="CURVE"), scene
    )
    assert result.changed
    return "CURVE"


def _edit_state(scene: Scene) -> _HandleEditState:
    obj = scene.objects["CURVE"]
    return _HandleEditState(
        object_id="CURVE",
        segment_index=0,
        handle_index=1,
        old_pos=BEZIERS[0][1],
        old_beziers=copy.deepcopy(obj.beziers),
        old_polygon=copy.deepcopy(obj.polygon),
        preview_beziers=copy.deepcopy(obj.beziers),
        preview_polygon=copy.deepcopy(obj.polygon),
    )


def test_compatibility_helpers_nodes_and_state_fallbacks(monkeypatch) -> None:
    assert pen_module.bezier_point(0.0, *BEZIERS[0]) == BEZIERS[0][0]
    assert len(pen_module.bezier_curve(*BEZIERS[0], segments=4)) == 5
    node = BezierNode((1, 2))
    assert node.anchor == (1.0, 2.0) and node.handle_in == node.anchor

    tool = PenTool(_Canvas(None))
    assert tool._model() is None
    assert tool._object_bezier_state(None) is None
    plain = SimpleNamespace(beziers=BEZIERS, polygon=[(0, 0), (1, 0), (0, 1)])
    state = tool._object_bezier_state(plain)
    assert state[0][0][0] == (0.0, 0.0)
    plain.beziers = "invalid"
    assert tool._object_bezier_state(plain) is None

    monkeypatch.setattr(
        tool,
        "_nodes_to_beziers",
        lambda: (_ for _ in ()).throw(ValueError("invalid nodes")),
    )
    assert tool._nodes_beziers() is None
    assert tool._active_preview_matches_model() is False


def test_load_clear_discard_and_synchronize_branches(monkeypatch) -> None:
    scene, tool = _scene_tool()
    assert tool._load_selected_bezier_object() is False
    _create_selected_curve(scene)
    assert tool._load_selected_bezier_object() is True
    assert tool._editing_object_id == "CURVE"

    tool._active_handle_edit = _edit_state(scene)
    assert tool._active_preview_matches_model() is True
    assert tool._discard_active_handle_edit(restore_preview=False) is True
    assert tool._discard_active_handle_edit(restore_preview=True) is False
    assert tool._cancel_active_handle_edit() is False

    tool._active_handle_edit = _edit_state(scene)
    tool._active_handle_edit.preview_polygon = [(9, 9), (10, 9), (9, 10)]
    assert tool._active_preview_matches_model() is False
    tool._clear_loaded_bezier_object(restore_preview=False)
    assert tool._editing_object_id is None and tool._nodes == []

    tool._editing_object_id = "CURVE"
    scene.selected_id = None
    assert tool._synchronize_selected_bezier_object() is False
    scene.selected_id = "CURVE"
    assert tool._load_selected_bezier_object() is True
    scene.objects["CURVE"].beziers = None
    assert tool._synchronize_selected_bezier_object() is False


def test_node_conversion_index_mapping_and_hit_detection() -> None:
    _, tool = _scene_tool()
    with pytest.raises(ValueError, match="At least two"):
        tool._nodes_to_beziers()
    first = BezierNode((0, 0))
    second = BezierNode((20, 0))
    first.handle_out = (5, -5)
    second.handle_in = (15, -5)
    tool._nodes = [first, second]
    assert tool._nodes_to_beziers()[0][3] == (20.0, 0.0)
    assert tool._node_index(first) == 0
    assert tool._node_index(BezierNode((0, 0))) is None
    assert tool._handle_mapping(first, "out") == (0, 1)
    assert tool._handle_mapping(second, "in") == (0, 2)
    assert tool._handle_mapping(first, "in") is None
    assert tool._handle_mapping(second, "out") is None
    assert tool._handle_mapping(BezierNode((1, 1)), "out") is None
    assert tool._get_anchor_at_point((0, 0)) is first
    assert tool._get_anchor_at_point((100, 100)) is None
    assert tool._get_handle_at_point((5, -5)) == (first, "out")
    assert tool._get_handle_at_point((15, -5)) == (second, "in")
    assert tool._get_handle_at_point((100, 100)) is None


def test_mouse_press_anchor_handle_right_click_and_move_failures(monkeypatch) -> None:
    _, tool = _scene_tool()
    left = _Event(button=Qt.MouseButton.LeftButton)
    right = _Event(button=Qt.MouseButton.RightButton)
    tool.on_mouse_press(left, (0, 0))
    tool.on_mouse_press(left, (20, 0))
    tool.on_mouse_press(left, (40, 0))
    assert len(tool._nodes) == 3
    for node in tool._nodes:
        node.handle_in = node.anchor
        node.handle_out = node.anchor
    tool.on_mouse_press(left, (20, 0))
    assert tool._selected_node is tool._nodes[1] and tool._selected_handle is None
    tool._nodes[0].handle_out = (5, -5)
    tool.on_mouse_press(left, (5, -5))
    assert tool._selected_handle == "out"

    contexts = []
    monkeypatch.setattr(tool, "show_context_menu", contexts.append)
    tool.on_mouse_press(right, (0, 0))
    assert contexts == [right]
    tool.on_mouse_move(left, (7, -7))
    assert tool._nodes[0].handle_out == (7.0, -7.0)
    tool._selected_handle = "in"
    tool.on_mouse_move(left, (-3, -3))
    assert tool._selected_node.handle_in == (-3.0, -3.0)

    scene, editing = _scene_tool()
    _create_selected_curve(scene)
    editing._load_selected_bezier_object()
    editing._active_handle_edit = _edit_state(scene)
    editing._selected_node = editing._nodes[0]
    editing._selected_handle = "out"
    monkeypatch.setattr(editing, "_synchronize_selected_bezier_object", lambda: True)
    monkeypatch.setattr(
        scene,
        "prepare_bezier_geometry",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad preview")),
    )
    editing.on_mouse_move(left, (8, -8))
    assert editing._last_error == "bad preview"


def test_restore_finish_release_key_and_double_click_branches(monkeypatch) -> None:
    scene, tool = _scene_tool()
    _create_selected_curve(scene)
    tool._load_selected_bezier_object()
    tool._restore_handle_preview()
    tool._finish_handle_edit()
    assert tool.on_key_press(_Event(key=Qt.Key.Key_Escape)) is False

    edit = _edit_state(scene)
    tool._active_handle_edit = edit
    tool._selected_node = tool._nodes[0]
    tool._selected_handle = "out"
    scene.objects["CURVE"].polygon = [(0, 0), (1, 0), (0, 1)]
    tool._finish_handle_edit()
    assert tool._active_handle_edit is None

    tool._active_handle_edit = _edit_state(scene)
    scene.objects.pop("CURVE")
    tool._restore_handle_preview()
    scene.selected_id = None
    tool.on_mouse_release(_Event(button=Qt.MouseButton.RightButton), (0, 0))
    tool.on_mouse_release(_Event(button=Qt.MouseButton.LeftButton), (0, 0))

    fresh_scene, fresh = _scene_tool()
    fresh._load_nodes_from_beziers(BEZIERS)
    committed = []
    monkeypatch.setattr(fresh, "commit_selection", lambda: committed.append(True))
    fresh.on_double_click(_Event(button=Qt.MouseButton.LeftButton), (0, 0))
    assert committed == [True]
    fresh._editing_object_id = "CURVE"
    fresh.on_double_click(_Event(button=Qt.MouseButton.LeftButton), (0, 0))
    assert committed == [True]


def test_finish_handle_edit_manager_and_status_branches(monkeypatch) -> None:
    scene, tool = _scene_tool()
    _create_selected_curve(scene)
    tool._load_selected_bezier_object()

    def prepare_edit():
        tool._active_handle_edit = _edit_state(scene)
        tool._selected_node = tool._nodes[0]
        tool._selected_node.handle_out = (8.0, -8.0)
        tool._selected_handle = "out"
        state = scene.prepare_bezier_geometry(tool._nodes_to_beziers())
        scene.objects["CURVE"].beziers = copy.deepcopy(state[0])
        scene.objects["CURVE"].polygon = copy.deepcopy(state[1])
        tool._active_handle_edit.preview_beziers = copy.deepcopy(state[0])
        tool._active_handle_edit.preview_polygon = copy.deepcopy(state[1])

    prepare_edit()
    scene.cmd = None
    tool._finish_handle_edit()
    assert "unavailable" in tool._last_error

    for status in (
        CommandStatus.REJECTED,
        CommandStatus.FAILED,
        CommandStatus.NO_CHANGE,
    ):
        scene.cmd = SimpleNamespace(
            execute=lambda command, model, status=status: SimpleNamespace(
                status=status, message=f"{status.value} result"
            )
        )
        tool._load_selected_bezier_object()
        prepare_edit()
        tool._finish_handle_edit()
        assert status.value in tool._last_error


@pytest.mark.parametrize(
    "points",
    [
        [(0, 0), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (0, 0)],
        [(0, 0), (0, 0), (1, 0), (0, 1)],
    ],
)
def test_sampled_point_conversion_boundaries(points) -> None:
    if len({tuple(point) for point in points}) < 3:
        with pytest.raises(ValueError, match="three distinct"):
            PenTool._beziers_from_sampled_points(points)
    else:
        segments = PenTool._beziers_from_sampled_points(points)
        assert segments and segments[0][0] == (0.0, 0.0)


@pytest.mark.parametrize(
    "points, message",
    [
        ([(0, 0), (1,), (0, 1)], "exactly two"),
        ([(0, 0), (True, 1), (0, 1)], "numeric"),
        ([(0, 0), (math.inf, 1), (0, 1)], "finite"),
        ([(0, 0), (10**400, 1), (0, 1)], "representable"),
    ],
)
def test_sampled_point_conversion_rejects_invalid_values(points, message) -> None:
    with pytest.raises(ValueError, match=message):
        PenTool._beziers_from_sampled_points(points)


def test_commit_selection_all_result_contracts(monkeypatch) -> None:
    scene, tool = _scene_tool()
    tool._load_nodes_from_beziers(BEZIERS)
    tool._editing_object_id = "existing"
    assert tool.commit_selection() == "existing"
    tool._editing_object_id = None

    monkeypatch.setattr(
        tool,
        "_nodes_to_beziers",
        lambda: (_ for _ in ()).throw(ValueError("invalid curve")),
    )
    assert tool.commit_selection() is None
    assert tool._last_error == "invalid curve"

    for status, changed, object_id in (
        (CommandStatus.REJECTED, False, None),
        (CommandStatus.FAILED, False, None),
        (CommandStatus.NO_CHANGE, False, None),
        (CommandStatus.APPLIED, True, None),
    ):
        _, current = _scene_tool()
        current._load_nodes_from_beziers(BEZIERS)

        class _Manager:
            def execute(self, command, model):
                command.object_id = object_id
                return SimpleNamespace(
                    status=status,
                    changed=changed,
                    message=f"{status.value} result",
                )

        current.canvas_view.model.cmd = _Manager()
        assert current.commit_selection() is None
        assert current._last_error


def test_curve_generation_render_context_history_cancel_and_language(
    qt_app, monkeypatch
) -> None:
    scene, tool = _scene_tool()
    assert tool._generate_curve_points() == []
    tool._load_nodes_from_beziers(BEZIERS)
    assert tool._generate_curve_points()
    monkeypatch.setattr(
        tool,
        "_nodes_to_beziers",
        lambda: (_ for _ in ()).throw(ValueError("invalid")),
    )
    assert tool._generate_curve_points() == []
    tool._load_nodes_from_beziers(BEZIERS)

    image = QImage(32, 32, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    tool.draw_overlay(painter)
    painter.end()

    class _Signal:
        def connect(self, callback):
            self.callback = callback

    class _Action:
        def __init__(self):
            self.triggered = _Signal()

    class _Menu:
        def __init__(self, parent):
            self.actions = []

        def setStyleSheet(self, value):
            self.style = value

        def addAction(self, text):
            action = _Action()
            self.actions.append(action)
            return action

        def addSeparator(self):
            return None

        def exec(self, position):
            self.position = position

    monkeypatch.setattr(pen_module, "QMenu", _Menu)
    tool.show_context_menu(_Event(button=Qt.MouseButton.RightButton))

    history = []
    scene.cmd = SimpleNamespace(
        undo=lambda model: history.append("undo"),
        redo=lambda model: history.append("redo"),
    )
    monkeypatch.setattr(tool, "on_undo", lambda: False)
    monkeypatch.setattr(tool, "on_redo", lambda: False)
    monkeypatch.setattr(tool, "_load_selected_bezier_object", lambda: True)
    tool.undo_last_action()
    tool.redo_last_action()
    monkeypatch.setattr(tool, "on_undo", lambda: True)
    monkeypatch.setattr(tool, "on_redo", lambda: True)
    tool.undo_last_action()
    tool.redo_last_action()
    assert history == ["undo", "redo"]
    tool.cancel()
    tool.on_cancel()
    tool.update_language("pt")
    assert tool.current_lang == "pt" and tool._nodes == []
