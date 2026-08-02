"""Stage 5 package 1: command manager contract and transactions."""

from __future__ import annotations

import os

import pytest

from src.core.commands import (
    AddPolygonCommand,
    Command,
    CommandManager,
    CommandResult,
    CommandStatus,
    CompositeCommand,
)
from src.models.scene import Scene


class _SetSelection(Command):
    def __init__(self, value: str):
        self.value = value
        self.previous = None

    def execute(self, scene):
        self.previous = scene.selected_id
        scene.selected_id = self.value
        scene._notify()

    def undo(self, scene):
        scene.selected_id = self.previous
        scene._notify()


class _NoChange(Command):
    def execute(self, scene):
        return None

    def undo(self, scene):
        return None


class _PartialExecuteFailure(Command):
    def execute(self, scene):
        scene.selected_id = "partial"
        scene._notify()
        raise RuntimeError("private path must not be logged")

    def undo(self, scene):
        scene.selected_id = None
        scene._notify()


class _UndoFailure(Command):
    def execute(self, scene):
        scene.selected_id = "applied"
        scene._notify()

    def undo(self, scene):
        scene.selected_id = None
        scene._notify()
        raise RuntimeError("undo failed after mutation")


class _RedoFailure(Command):
    def __init__(self):
        self.executions = 0

    def execute(self, scene):
        self.executions += 1
        scene.selected_id = f"execution-{self.executions}"
        scene._notify()
        if self.executions > 1:
            raise RuntimeError("redo failed after mutation")

    def undo(self, scene):
        scene.selected_id = None
        scene._notify()


class _ObjectCommand(Command):
    def __init__(self, object_id: str):
        self.object_id = object_id

    def execute(self, scene):
        scene.objects[self.object_id] = object()
        scene._notify()

    def undo(self, scene):
        del scene.objects[self.object_id]
        scene._notify()


class _FailingObjectCommand(Command):
    def execute(self, scene):
        scene.objects["partial"] = object()
        scene._notify()
        raise RuntimeError("composite failure")

    def undo(self, scene):
        scene.objects.pop("partial", None)
        scene._notify()


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager()
    return scene


def test_execute_returns_explicit_result_and_updates_history():
    scene = _scene()
    result = scene.cmd.execute(_SetSelection("selected"), scene)

    assert isinstance(result, CommandResult)
    assert result.status is CommandStatus.APPLIED
    assert result.ok is True
    assert result.changed is True
    assert scene.cmd.can_undo is True
    assert scene.cmd.can_redo is False
    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0


def test_no_change_operation_does_not_enter_history():
    scene = _scene()
    result = scene.cmd.execute(_NoChange(), scene)

    assert result.status is CommandStatus.NO_CHANGE
    assert result.changed is False
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_execute_failure_restores_scene_and_does_not_enter_history():
    scene = _scene()
    scene.selected_id = "before"

    result = scene.cmd.execute(_PartialExecuteFailure(), scene)

    assert result.status is CommandStatus.FAILED
    assert result.error_type == "RuntimeError"
    assert "private path" not in result.message
    assert scene.selected_id == "before"
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_undo_failure_restores_scene_and_preserves_stacks():
    scene = _scene()
    command = _UndoFailure()
    assert scene.cmd.execute(command, scene).changed

    result = scene.cmd.undo(scene)

    assert result.status is CommandStatus.FAILED
    assert scene.selected_id == "applied"
    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0


def test_redo_failure_restores_scene_and_preserves_stacks():
    scene = _scene()
    command = _RedoFailure()
    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id is None

    result = scene.cmd.redo(scene)

    assert result.status is CommandStatus.FAILED
    assert scene.selected_id is None
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 1


def test_failed_new_edit_does_not_invalidate_redo():
    scene = _scene()
    assert scene.cmd.execute(_SetSelection("original"), scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.cmd.can_redo

    failed = scene.cmd.execute(_PartialExecuteFailure(), scene)

    assert failed.status is CommandStatus.FAILED
    assert scene.cmd.can_redo is True
    assert scene.cmd.redo_count == 1


def test_successful_new_edit_invalidates_redo():
    scene = _scene()
    assert scene.cmd.execute(_SetSelection("original"), scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.cmd.can_redo

    assert scene.cmd.execute(_SetSelection("replacement"), scene).changed

    assert scene.cmd.can_redo is False
    assert scene.cmd.redo_count == 0
    assert scene.cmd.undo_count == 1


def test_history_limit_discards_only_oldest_successful_command():
    scene = Scene()
    scene.cmd = CommandManager(max_history=2)

    assert scene.cmd.execute(_SetSelection("one"), scene).changed
    assert scene.cmd.execute(_SetSelection("two"), scene).changed
    assert scene.cmd.execute(_NoChange(), scene).changed is False
    assert scene.cmd.execute(_SetSelection("three"), scene).changed

    assert scene.cmd.undo_count == 2
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "two"
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "one"
    assert scene.cmd.undo(scene).status is CommandStatus.NO_CHANGE


def test_composite_failure_rolls_back_and_creates_no_history():
    scene = _scene()
    command = CompositeCommand(
        [_ObjectCommand("complete-only"), _FailingObjectCommand()]
    )

    result = scene.cmd.execute(command, scene)

    assert result.status is CommandStatus.FAILED
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_composite_is_repeatable_across_undo_redo_cycles():
    scene = _scene()
    command = CompositeCommand([_ObjectCommand("a"), _ObjectCommand("b")])

    assert scene.cmd.execute(command, scene).changed
    assert set(scene.objects) == {"a", "b"}
    assert len(command._executed) == 2

    assert scene.cmd.undo(scene).changed
    assert scene.objects == {}

    assert scene.cmd.redo(scene).changed
    assert set(scene.objects) == {"a", "b"}
    assert len(command._executed) == 2

    assert scene.cmd.undo(scene).changed
    assert scene.objects == {}


def test_history_listener_observes_only_stack_changes():
    scene = _scene()
    states = []
    scene.cmd.subscribe(lambda: states.append((scene.cmd.can_undo, scene.cmd.can_redo)))

    scene.cmd.execute(_NoChange(), scene)
    scene.cmd.execute(_SetSelection("one"), scene)
    scene.cmd.undo(scene)
    scene.cmd.redo(scene)
    scene.cmd.clear()

    assert states == [
        (True, False),
        (False, True),
        (True, False),
        (False, False),
    ]


def test_existing_add_polygon_flow_returns_results():
    scene = _scene()
    command = AddPolygonCommand([(0, 0), (20, 0), (20, 20), (0, 20)])

    assert scene.cmd.execute(command, scene).status is CommandStatus.APPLIED
    assert command.object_id in scene.objects
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert command.object_id not in scene.objects
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert len(scene.objects) == 1


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_actions_follow_history_state(qt_app):
    scene = _scene()
    window = MainWindow(scene, _ConfigStub())

    assert window.undo_action.isEnabled() is False
    assert window.redo_action.isEnabled() is False

    scene.cmd.execute(_SetSelection("selected"), scene)
    qt_app.processEvents()
    assert window.undo_action.isEnabled() is True
    assert window.redo_action.isEnabled() is False

    window._undo()
    qt_app.processEvents()
    assert window.undo_action.isEnabled() is False
    assert window.redo_action.isEnabled() is True

    window._redo()
    qt_app.processEvents()
    assert window.undo_action.isEnabled() is True
    assert window.redo_action.isEnabled() is False

    scene.cmd.clear()
    qt_app.processEvents()
    assert window.undo_action.isEnabled() is False
    assert window.redo_action.isEnabled() is False

    window._mark_document_clean()
    window.close()
