"""Phase 3 replacement contracts for the legacy creation/history cases.

These tests deliberately use the production ``Scene``, ``CommandManager`` and
``CanvasView`` together with native Qt events.  The historical snapshots are
not edited; this file is the executable substitute for the obsolete fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication

from src.core.commands import AddPolygonCommand, CommandStatus
from src.models.scene import SceneObject
from src.tools.ellipse_selection import EllipseSelectionTool
from src.tools.lasso_tool import LassoTool
from src.tools.pen_tool import PenTool
from src.tools.polygonal_lasso import PolygonalLassoTool
from src.tools.rect_selection import RectSelectionTool
from tests.legacy_phase1_fixtures import (
    mouse_event,
    real_canvas,
    real_scene,
    scene_state_token,
)


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    """Use one concrete QApplication for the native event contracts."""

    return QApplication.instance() or QApplication([])


@pytest.fixture()
def scene_canvas(qt_app: QApplication):
    """Create and dispose of a real scene/canvas pair for one contract."""

    scene = real_scene()
    canvas = real_canvas(scene)
    canvas.resize(640, 480)
    canvas.show()
    qt_app.processEvents()
    try:
        yield scene, canvas
    finally:
        canvas.close()
        canvas.deleteLater()
        qt_app.processEvents()


def _press(canvas, point: tuple[float, float]) -> None:
    canvas.mousePressEvent(
        mouse_event(
            QEvent.Type.MouseButtonPress,
            *point,
            button=Qt.MouseButton.LeftButton,
            buttons=Qt.MouseButton.LeftButton,
        )
    )


def _move(canvas, point: tuple[float, float]) -> None:
    canvas.mouseMoveEvent(
        mouse_event(
            QEvent.Type.MouseMove,
            *point,
            button=Qt.MouseButton.NoButton,
            buttons=Qt.MouseButton.LeftButton,
        )
    )


def _release(canvas, point: tuple[float, float]) -> None:
    canvas.mouseReleaseEvent(
        mouse_event(
            QEvent.Type.MouseButtonRelease,
            *point,
            button=Qt.MouseButton.LeftButton,
            buttons=Qt.MouseButton.NoButton,
        )
    )


def _double_click(canvas, point: tuple[float, float]) -> None:
    canvas.mouseDoubleClickEvent(
        mouse_event(
            QEvent.Type.MouseButtonDblClick,
            *point,
            button=Qt.MouseButton.LeftButton,
            buttons=Qt.MouseButton.LeftButton,
        )
    )


def _assert_create_undo_redo(scene, object_id: str, before, expected) -> None:
    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0
    assert scene.selected_id == object_id
    assert scene_state_token(scene) == expected

    undo_result = scene.cmd.undo(scene)
    assert undo_result.status is CommandStatus.APPLIED
    assert scene_state_token(scene) == before
    assert scene.selected_id is None

    redo_result = scene.cmd.redo(scene)
    assert redo_result.status is CommandStatus.APPLIED
    assert scene_state_token(scene) == expected
    assert scene.selected_id == object_id


def test_phase3_case_06_lasso_native_gesture_is_one_reversible_creation(
    scene_canvas,
):
    """#6: release commits through the real command history and clears preview."""

    scene, canvas = scene_canvas
    before = scene_state_token(scene)
    tool = LassoTool(canvas)
    canvas.set_tool(tool)

    _press(canvas, (20, 20))
    _move(canvas, (90, 20))
    _move(canvas, (90, 90))
    _move(canvas, (20, 90))
    _release(canvas, (20, 90))

    assert len(scene.objects) == 1
    object_id = scene.selected_id
    assert object_id is not None
    assert tool._points == []
    assert tool._last_point is None
    expected = scene_state_token(scene)
    _assert_create_undo_redo(scene, object_id, before, expected)


def test_phase3_case_06_lasso_rejection_preserves_preview_and_history(
    scene_canvas,
    monkeypatch: pytest.MonkeyPatch,
):
    """#6: invalid native geometry is rejected without partial mutation."""

    scene, canvas = scene_canvas
    tool = LassoTool(canvas)
    canvas.set_tool(tool)
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.critical", lambda *args, **kwargs: None
    )
    before = scene_state_token(scene)

    _press(canvas, (20, 20))
    _move(canvas, (100, 100))
    _move(canvas, (20, 100))
    _move(canvas, (100, 20))
    _release(canvas, (100, 20))

    assert scene_state_token(scene) == before
    assert scene.cmd.undo_count == 0
    assert tool._points
    assert tool._last_command_result.status in {
        CommandStatus.REJECTED,
        CommandStatus.FAILED,
    }


def test_phase3_cases_07_08_pen_native_double_click_preserves_bezier_history(
    scene_canvas,
):
    """#7/#8: native pen anchors commit one Bézier command and keep nodes."""

    scene, canvas = scene_canvas
    before = scene_state_token(scene)
    tool = PenTool(canvas)
    canvas.set_tool(tool)

    _press(canvas, (20, 30))
    _press(canvas, (100, 30))
    _press(canvas, (100, 110))
    _double_click(canvas, (100, 110))

    object_id = scene.selected_id
    assert object_id is not None
    assert tool._last_command_result.status is CommandStatus.APPLIED
    assert scene.objects[object_id].beziers is not None
    assert tool._editing_object_id == object_id
    assert len(tool._nodes) == 3
    expected = scene_state_token(scene)
    _assert_create_undo_redo(scene, object_id, before, expected)

    # A malformed/incomplete finish does not discard the user's in-progress
    # nodes and cannot create a history entry.
    scene.cmd.clear()
    tool.on_cancel()
    scene.select_object(None)
    _press(canvas, (200, 200))
    assert len(tool._nodes) == 1
    _double_click(canvas, (200, 200))
    assert len(tool._nodes) == 1
    assert scene.cmd.undo_count == 0
    assert scene.selected_id is None


def test_phase3_cases_09_10_polygonal_lasso_closes_and_rejects_without_loss(
    scene_canvas, monkeypatch: pytest.MonkeyPatch
):
    """#9/#10: close with real events; invalid geometry stays retryable."""

    scene, canvas = scene_canvas
    tool = PolygonalLassoTool(canvas)
    dialog_events = []
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.warning",
        lambda *args, **kwargs: dialog_events.append(("warning", args)),
    )
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.critical",
        lambda *args, **kwargs: dialog_events.append(("critical", args)),
    )
    canvas.set_tool(tool)
    _press(canvas, (20, 20))
    _press(canvas, (100, 20))
    _press(canvas, (100, 100))
    _double_click(canvas, (20, 100))

    object_id = scene.selected_id
    assert object_id is not None
    assert all(
        isinstance(coordinate, int)
        for point in scene.objects[object_id].polygon
        for coordinate in point
    )
    assert tool._vertices == []
    assert scene.cmd.undo_count == 1

    scene.cmd.clear()
    scene.select_object(object_id)
    before = scene_state_token(scene)
    rejected = []
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.warning",
        lambda *args, **kwargs: rejected.append(args),
    )
    tool._vertices = [(200.0, 200.0)] * 3
    _double_click(canvas, (200, 200))
    assert tool._vertices == [(200.0, 200.0)] * 3
    assert scene_state_token(scene) == before
    assert scene.cmd.undo_count == 0
    assert scene.selected_id == object_id
    assert len(rejected) == 0
    assert len(dialog_events) == 1
    assert dialog_events[0][0] == "critical"


@pytest.mark.parametrize(
    ("tool_type", "start", "end", "state_attribute", "polygon_points"),
    [
        (RectSelectionTool, (20, 20), (120, 90), "_start_point", 4),
        (EllipseSelectionTool, (180, 120), (300, 220), "_center", 64),
    ],
)
def test_phase3_cases_11_12_shape_native_gesture_is_reversible(
    scene_canvas, tool_type, start, end, state_attribute, polygon_points
):
    """#11/#12: rectangle and ellipse use real mouse press/move/release."""

    scene, canvas = scene_canvas
    before = scene_state_token(scene)
    tool = tool_type(canvas)
    canvas.set_tool(tool)
    _press(canvas, start)
    _move(canvas, end)
    _release(canvas, end)

    object_id = scene.selected_id
    assert object_id is not None
    assert len(scene.objects[object_id].polygon) == polygon_points
    assert getattr(tool, state_attribute) is None
    expected = scene_state_token(scene)
    _assert_create_undo_redo(scene, object_id, before, expected)


@pytest.mark.parametrize(
    ("tool_type", "point", "state_attribute"),
    [
        (RectSelectionTool, (20, 20), "_start_point"),
        (EllipseSelectionTool, (180, 120), "_center"),
    ],
)
def test_phase3_cases_11_12_degenerate_gesture_is_fail_closed(
    scene_canvas, tool_type, point, state_attribute
):
    """#11/#12: zero-area gestures do not mutate scene or history."""

    scene, canvas = scene_canvas
    tool = tool_type(canvas)
    canvas.set_tool(tool)
    before = scene_state_token(scene)

    _press(canvas, point)
    _release(canvas, point)

    assert scene_state_token(scene) == before
    assert scene.cmd.undo_count == 0
    assert getattr(tool, state_attribute) == point


def test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order(
    scene_canvas, tmp_path: Path
):
    """#13–#16: concrete tools produce one command each and stack correctly."""

    scene, canvas = scene_canvas
    before = scene_state_token(scene)
    object_ids: list[str] = []

    lasso = LassoTool(canvas)
    canvas.set_tool(lasso)
    _press(canvas, (10, 10))
    _move(canvas, (70, 10))
    _move(canvas, (70, 70))
    _move(canvas, (10, 70))
    _release(canvas, (10, 70))
    object_ids.append(str(scene.selected_id))

    polygonal = PolygonalLassoTool(canvas)
    canvas.set_tool(polygonal)
    for point in ((100, 10), (160, 10), (160, 70), (100, 70)):
        _press(canvas, point)
    _double_click(canvas, (100, 70))
    object_ids.append(str(scene.selected_id))

    rectangle = RectSelectionTool(canvas)
    canvas.set_tool(rectangle)
    _press(canvas, (200, 10))
    _move(canvas, (270, 80))
    _release(canvas, (270, 80))
    object_ids.append(str(scene.selected_id))

    ellipse = EllipseSelectionTool(canvas)
    canvas.set_tool(ellipse)
    _press(canvas, (320, 40))
    _move(canvas, (420, 120))
    _release(canvas, (420, 120))
    object_ids.append(str(scene.selected_id))

    assert len(set(object_ids)) == 4
    assert scene.cmd.undo_count == 4
    final = scene_state_token(scene)
    for _ in object_ids:
        assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene_state_token(scene) == before
    assert scene.selected_id is None
    for _ in object_ids:
        assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene_state_token(scene) == final

    project_path = tmp_path / "phase3-sequence.ndtproj"
    scene.save_project(str(project_path))
    loaded = real_scene()
    assert loaded.load_project(str(project_path)) == ()
    loaded_token = scene_state_token(loaded)
    assert loaded_token[0] == final[0]
    assert loaded_token[1] == final[1]
    assert loaded_token[4:] == final[4:]
    assert loaded.selected_id is None

    # A subsequent invalid gesture must not change the committed sequence.
    lasso = LassoTool(canvas)
    canvas.set_tool(lasso)
    _press(canvas, (500, 400))
    _move(canvas, (540, 440))
    _release(canvas, (540, 440))
    assert scene_state_token(scene) == final
    assert scene.cmd.undo_count == 4
    assert scene.selected_id == object_ids[-1]
    assert scene.selected_id == object_ids[-1]


def test_phase3_case_25_cycle_safe_snapshot_works_with_real_scene_and_manager(
    scene_canvas,
):
    """#25: a cyclic diagnostic attribute cannot recurse through history."""

    scene, _ = scene_canvas
    cycle: dict[str, object] = {}
    cycle["self"] = cycle
    cyclic_object = SceneObject(
        "cyclic",
        [(0, 0), (20, 0), (20, 20), (0, 20)],
    )
    cyclic_object.diagnostic_metadata = cycle
    scene.objects[cyclic_object.id] = cyclic_object
    scene.select_object(cyclic_object.id)
    scene.cmd.clear()

    command = AddPolygonCommand([(40, 40), (80, 40), (80, 80), (40, 80)])
    result = scene.cmd.execute(command, scene)
    assert result.status is CommandStatus.APPLIED
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert command.object_id in scene.objects
    assert scene.objects["cyclic"].diagnostic_metadata["self"] is (
        scene.objects["cyclic"].diagnostic_metadata
    )


def test_phase3_case_26_rectangle_round_trip_and_history_use_real_scene(
    scene_canvas, tmp_path: Path
):
    """#26: creation, project round-trip, undo and redo retain the geometry."""

    scene, canvas = scene_canvas
    tool = RectSelectionTool(canvas)
    canvas.set_tool(tool)
    _press(canvas, (30, 40))
    _move(canvas, (130, 140))
    _release(canvas, (130, 140))
    object_id = str(scene.selected_id)
    polygon = list(scene.objects[object_id].polygon)

    project_path = tmp_path / "phase3-rectangle.ndtproj"
    scene.save_project(str(project_path))
    loaded = real_scene()
    assert loaded.load_project(str(project_path)) == ()
    assert list(loaded.objects[object_id].polygon) == polygon
    assert loaded.selected_id is None

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert object_id not in scene.objects
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects[object_id].polygon) == polygon
    assert scene.selected_id == object_id
