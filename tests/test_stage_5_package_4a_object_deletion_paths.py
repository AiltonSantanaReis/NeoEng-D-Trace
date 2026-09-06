"""Stage 5 package 4A: transactional object deletion paths."""

from __future__ import annotations

import inspect

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.tools.collision_brush_tool import CollisionBrushTool
from src.tools.polygon_edit_tool import PolygonEditTool


class _CanvasStub:
    def __init__(self, scene):
        self.model = scene
        self.update_count = 0

    def update(self):
        self.update_count += 1

    def get_zoom(self):
        return 1.0

    def parent(self):
        return None


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def _scene():
    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    polygons = {
        "A": [(10, 10), (70, 10), (70, 70), (10, 70)],
        "B": [(90, 10), (150, 10), (150, 70), (90, 70)],
        "C": [(170, 10), (230, 10), (230, 70), (170, 70)],
        "D": [(250, 10), (310, 10), (310, 70), (250, 70)],
    }
    for object_id, polygon in polygons.items():
        scene.add_object(object_id, polygon, select=False)

    scene.collision_shapes["B"] = [
        (91.25, 11.5),
        (151.25, 11.5),
        (151.25, 71.5),
        (91.25, 71.5),
    ]
    scene.collision_shapes["C"] = [
        (171.25, 11.5),
        (231.25, 11.5),
        (231.25, 71.5),
        (171.25, 71.5),
    ]
    group = scene.create_group("Deletion Group")
    scene.add_object_to_group(group.id, "A")
    scene.add_object_to_group(group.id, "B")
    scene.add_object_to_group(group.id, "C")
    scene.select_object("B")
    scene.cmd.clear()
    return scene


def _snapshot(scene):
    return {
        "object_ids": list(scene.objects),
        "objects": {
            object_id: list(obj.polygon) for object_id, obj in scene.objects.items()
        },
        "collisions": {
            object_id: list(shape)
            for object_id, shape in scene.collision_shapes.items()
        },
        "groups": {group.id: list(group.members) for group in scene.groups},
        "selected_id": scene.selected_id,
    }


def _polygon_tool(scene):
    return PolygonEditTool(_CanvasStub(scene))


def _brush_tool(scene):
    return CollisionBrushTool(_CanvasStub(scene))


def test_single_polygon_delete_round_trips_exact_relations():
    scene = _scene()
    tool = _polygon_tool(scene)
    before = _snapshot(scene)
    tool.selected_polygon_id = "B"
    tool.selected_polygon_ids = {"B"}
    tool.selected_vertex = 1

    tool.delete_selected_polygon()

    assert "B" not in scene.objects
    assert scene.cmd.undo_count == 1
    assert tool.selected_polygon_id is None
    assert tool.selected_polygon_ids == set()
    assert tool.selected_vertex is None

    undo = scene.cmd.undo(scene)
    assert undo.status is CommandStatus.APPLIED
    assert _snapshot(scene) == before

    redo = scene.cmd.redo(scene)
    assert redo.status is CommandStatus.APPLIED
    assert "B" not in scene.objects
    assert "B" not in scene.collision_shapes
    assert all("B" not in group.members for group in scene.groups)


def test_multi_polygon_delete_is_one_history_entry_and_round_trips():
    scene = _scene()
    tool = _polygon_tool(scene)
    before = _snapshot(scene)
    tool.multi_select = True
    tool.selected_polygon_ids = {"C", "B"}
    tool.selected_polygon_id = "C"

    tool.delete_selected_polygon()

    assert list(scene.objects) == ["A", "D"]
    assert scene.cmd.undo_count == 1
    assert tool.selected_polygon_ids == set()

    undo = scene.cmd.undo(scene)
    assert undo.status is CommandStatus.APPLIED
    assert _snapshot(scene) == before

    redo = scene.cmd.redo(scene)
    assert redo.status is CommandStatus.APPLIED
    assert list(scene.objects) == ["A", "D"]
    assert scene.cmd.undo_count == 1
    assert scene.cmd.redo_count == 0


def test_multi_delete_uses_scene_order_not_set_order():
    scene = _scene()
    tool = _polygon_tool(scene)
    tool.multi_select = True
    tool.selected_polygon_ids = {"C", "B"}

    result = tool._execute_object_deletion(
        list(tool.selected_polygon_ids),
        "Delete Polygons",
    )

    assert result is not None
    assert result.status is CommandStatus.APPLIED
    assert list(scene.objects) == ["A", "D"]
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["A", "B", "C", "D"]


def test_polygon_delete_blocks_when_history_is_unavailable(monkeypatch):
    scene = _scene()
    scene.cmd = None
    tool = _polygon_tool(scene)
    tool.multi_select = True
    tool.selected_polygon_ids = {"B", "C"}
    tool.selected_polygon_id = "B"
    before = _snapshot(scene)
    messages = []

    monkeypatch.setattr(
        "src.tools.polygon_edit_tool.QMessageBox.critical",
        lambda *args, **kwargs: messages.append(args),
    )

    tool.delete_selected_polygon()

    assert _snapshot(scene) == before
    assert tool.selected_polygon_ids == {"B", "C"}
    assert "P2D05-OPERATION" in tool._last_error
    assert "No change was applied" in tool._last_error


def test_stale_polygon_selection_is_rejected_without_history(monkeypatch):
    scene = _scene()
    tool = _polygon_tool(scene)
    tool.selected_polygon_id = "missing"
    tool.selected_polygon_ids = {"missing"}
    messages = []

    monkeypatch.setattr(
        "src.tools.polygon_edit_tool.QMessageBox.warning",
        lambda *args, **kwargs: messages.append(args),
    )

    tool.delete_selected_polygon()

    assert list(scene.objects) == ["A", "B", "C", "D"]
    assert scene.cmd.undo_count == 0
    assert tool.selected_polygon_id == "missing"
    assert "P2D05-REFERENCE" in tool._last_error
    assert "No change was applied" in tool._last_error


def test_mixed_stale_multi_selection_is_rejected_atomically(monkeypatch):
    scene = _scene()
    tool = _polygon_tool(scene)
    before = _snapshot(scene)
    tool.multi_select = True
    tool.selected_polygon_id = "B"
    tool.selected_polygon_ids = {"B", "missing"}
    messages = []

    monkeypatch.setattr(
        "src.tools.polygon_edit_tool.QMessageBox.warning",
        lambda *args, **kwargs: messages.append(args),
    )

    tool.delete_selected_polygon()

    assert _snapshot(scene) == before
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0
    assert tool.selected_polygon_id == "B"
    assert tool.selected_polygon_ids == {"B", "missing"}
    assert "P2D05-REFERENCE" in tool._last_error
    assert "No change was applied" in tool._last_error


def test_collision_brush_remove_round_trips_exact_relations(monkeypatch):
    scene = _scene()
    tool = _brush_tool(scene)
    before = _snapshot(scene)

    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    tool._remove("B")

    assert "B" not in scene.objects
    assert scene.cmd.undo_count == 1
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert _snapshot(scene) == before
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert "B" not in scene.objects


def test_collision_brush_cancel_remove_changes_nothing(monkeypatch):
    scene = _scene()
    tool = _brush_tool(scene)
    before = _snapshot(scene)

    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    tool._remove("B")

    assert _snapshot(scene) == before
    assert scene.cmd.undo_count == 0


def test_collision_brush_remove_blocks_without_history(monkeypatch):
    scene = _scene()
    scene.cmd = None
    tool = _brush_tool(scene)
    before = _snapshot(scene)
    messages = []

    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.critical",
        lambda *args, **kwargs: messages.append(args),
    )

    tool._remove("B")

    assert _snapshot(scene) == before
    assert messages
    assert "history is unavailable" in str(messages[-1])


def test_collision_brush_remove_clears_active_target_state(monkeypatch):
    scene = _scene()
    tool = _brush_tool(scene)
    tool.selected_polygon_id = "B"
    tool.moving = True
    tool.moving_oid = "B"
    tool.last_pos = (100, 30)
    tool.scaling = True
    tool.scaling_oid = "B"
    tool.scale_center = (120.0, 40.0)
    tool.initial_scale = 1.25
    tool.last_scale_pos = (100, 35)

    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    tool._remove("B")

    assert tool.selected_polygon_id is None
    assert tool.moving is False
    assert tool.moving_oid is None
    assert tool.last_pos is None
    assert tool.scaling is False
    assert tool.scaling_oid is None
    assert tool.scale_center is None
    assert tool.initial_scale == 1.0
    assert tool.last_scale_pos is None


def test_deletion_and_toggle_paths_have_no_direct_mutation_fallbacks():
    polygon_delete = inspect.getsource(PolygonEditTool.delete_selected_polygon)
    polygon_execute = inspect.getsource(PolygonEditTool._execute_object_deletion)
    brush_remove = inspect.getsource(CollisionBrushTool._remove)
    brush_press = inspect.getsource(CollisionBrushTool.on_mouse_press)

    assert "remove_object(" not in polygon_delete
    assert "remove_object(" not in polygon_execute
    assert "DeleteObjectCommand" in polygon_execute
    assert "CompositeCommand" in polygon_execute
    assert "remove_object(" not in brush_remove
    assert "DeleteObjectCommand" in brush_remove
    assert "set_object_collision(" not in brush_press
    assert "ToggleCollisionCommand" in brush_press
    assert "history is unavailable" in brush_press
