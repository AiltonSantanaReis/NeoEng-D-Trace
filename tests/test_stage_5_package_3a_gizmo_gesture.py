"""Stage 5 package 3A: transactional gizmo movement."""

from __future__ import annotations

import inspect
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager, CommandStatus
from src.core.polygon_gesture import PolygonGestureTransaction
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView


def _square(offset=0):
    return [
        (offset, offset),
        (offset + 20, offset),
        (offset + 20, offset + 20),
        (offset, offset + 20),
    ]


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def _scene(with_collision=True):
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.add_object("object", _square(), select=True)
    if with_collision:
        scene.collision_shapes["object"] = [
            (1.0, 1.0),
            (18.0, 2.0),
            (10.0, 17.0),
        ]
    return scene


def test_gesture_commit_creates_one_history_entry_and_round_trips():
    scene = _scene()
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    moved = [(x + 7, y + 4) for x, y in original_polygon]

    gesture = PolygonGestureTransaction(scene, "object")
    gesture.preview(moved)
    assert scene.cmd.undo_count == 0

    result = gesture.commit(scene.cmd)
    assert result.status is CommandStatus.APPLIED
    assert scene.cmd.undo_count == 1
    assert scene.objects["object"].polygon == moved

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == moved
    assert scene.collision_shapes["object"] == [(float(x), float(y)) for x, y in moved]


def test_gesture_cancel_restores_exact_collision_without_history():
    scene = _scene()
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])

    gesture = PolygonGestureTransaction(scene, "object")
    gesture.preview([(x + 5, y) for x, y in original_polygon])
    assert gesture.cancel() is True

    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0


def test_noop_gesture_restores_custom_collision_without_history():
    scene = _scene()
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])

    gesture = PolygonGestureTransaction(scene, "object")
    gesture.preview(list(original_polygon))
    result = gesture.commit(scene.cmd)

    assert result.status is CommandStatus.NO_CHANGE
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0


def test_missing_manager_rolls_back_preview_and_returns_failure():
    scene = _scene()
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])

    gesture = PolygonGestureTransaction(scene, "object")
    gesture.preview([(x + 8, y + 2) for x, y in original_polygon])
    result = gesture.commit(None)

    assert result.status is CommandStatus.FAILED
    assert result.error_type == "CommandManagerUnavailable"
    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0


def test_canvas_accumulates_subpixel_deltas_and_commits_once(qt_app):
    scene = _scene(with_collision=False)
    canvas = CanvasView(scene)
    qt_app.processEvents()

    assert canvas._begin_gizmo_object_gesture() is True
    canvas._gizmo_active = True
    canvas._move_selected_object(0.4, 0.0)
    canvas._move_selected_object(0.4, 0.0)
    canvas._move_selected_object(0.4, 0.0)

    result = canvas._finish_gizmo_gesture()
    assert result.status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == [(x + 1, y) for x, y in _square()]
    assert scene.cmd.undo_count == 1

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == _square()
    canvas.close()


def test_canvas_cancel_restores_preview_without_history(qt_app):
    scene = _scene()
    original_polygon = list(scene.objects["object"].polygon)
    original_collision = list(scene.collision_shapes["object"])
    canvas = CanvasView(scene)
    qt_app.processEvents()

    assert canvas._begin_gizmo_object_gesture() is True
    canvas._gizmo_active = True
    canvas._move_selected_object(6.0, 3.0)
    assert canvas._cancel_gizmo_gesture() is True

    assert scene.objects["object"].polygon == original_polygon
    assert scene.collision_shapes["object"] == original_collision
    assert scene.cmd.undo_count == 0
    assert canvas._gizmo_transaction is None
    assert canvas._gizmo_active is False
    canvas.close()


def test_canvas_blocks_gizmo_when_history_is_unavailable(
    qt_app,
    monkeypatch,
):
    scene = _scene()
    scene.cmd = None
    canvas = CanvasView(scene)
    qt_app.processEvents()
    critical_calls = []

    monkeypatch.setattr(
        "src.ui.canvas_view.QMessageBox.critical",
        lambda *args, **kwargs: critical_calls.append(args),
    )

    assert canvas._begin_gizmo_object_gesture() is False
    assert canvas._gizmo_transaction is None
    assert scene.objects["object"].polygon == _square()
    assert critical_calls
    canvas.close()


def test_canvas_gizmo_paths_are_transactional_and_todo_is_removed():
    move_source = inspect.getsource(CanvasView._move_selected_object)
    release_source = inspect.getsource(CanvasView.mouseReleaseEvent)
    press_source = inspect.getsource(CanvasView.mousePressEvent)
    key_source = inspect.getsource(CanvasView.keyPressEvent)

    assert "model.update_polygon" not in move_source
    assert "PolygonGestureTransaction" in inspect.getsource(
        CanvasView._begin_gizmo_object_gesture
    )
    assert "_finish_gizmo_gesture" in release_source
    assert "_begin_gizmo_object_gesture" in press_source
    assert "_cancel_gizmo_gesture" in key_source
    assert "Aqui seria o local para commitar" not in release_source
