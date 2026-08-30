import ast
import copy
import inspect
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QMessageBox

from src.collision import StaticCollisionManager
from src.core.commands import (
    CommandManager,
    CommandResult,
)
from src.models.scene import Scene
from src.ui.collision_panel import CollisionPanel
from src.ui.mask_viewer import MaskViewerDialog

TRIANGLE_A = [(0, 0), (20, 0), (20, 20)]
TRIANGLE_B = [(40, 0), (60, 0), (60, 20)]


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture
def messages(monkeypatch):
    calls = {"information": [], "warning": [], "critical": []}
    for name in calls:
        monkeypatch.setattr(
            QMessageBox,
            name,
            lambda *args, _name=name, **kwargs: calls[_name].append((args, kwargs)),
        )
    return calls


def make_mask_dialog(qt_app, monkeypatch, scene):
    dialog = MaskViewerDialog(scene)
    close = MagicMock()
    monkeypatch.setattr(dialog, "close", close)
    return dialog, close


def test_mask_viewer_applies_batch_as_one_history_entry(qt_app, monkeypatch, messages):
    scene = Scene()
    scene.cmd = CommandManager()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [
        {"polygon": TRIANGLE_A},
        {"polygon": TRIANGLE_B},
    ]

    dialog._apply_to_scene()

    assert len(scene.objects) == 2
    assert scene.cmd.undo_count == 1
    assert close.call_count == 1
    assert len(messages["information"]) == 1
    ids = tuple(scene.objects)
    assert scene.cmd.undo(scene).changed
    assert scene.objects == {}
    assert scene.cmd.redo(scene).changed
    assert tuple(scene.objects) == ids


def test_mask_viewer_blocks_without_command_manager(qt_app, monkeypatch, messages):
    scene = Scene()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [{"polygon": TRIANGLE_A}]

    dialog._apply_to_scene()

    assert scene.objects == {}
    assert close.call_count == 0
    assert len(messages["warning"]) == 1


def test_mask_viewer_invalid_polygon_rolls_back_entire_batch(
    qt_app, monkeypatch, messages
):
    scene = Scene()
    scene.cmd = CommandManager()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [
        {"polygon": TRIANGLE_A},
        {"polygon": [(0, 0), (1, 1), (2, 2)]},
    ]

    dialog._apply_to_scene()

    assert scene.objects == {}
    assert scene.cmd.undo_count == 0
    assert close.call_count == 0
    assert not messages["critical"]
    assert "invalid" in dialog.validation_label.text().lower()


def test_mask_viewer_reports_exact_crossing_location(qt_app, monkeypatch, messages):
    scene = Scene()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [
        {"polygon": [(0, 0), (10, 10), (0, 10), (10, 0)]},
    ]

    dialog._update_polygon_validation_feedback()

    details = dialog._last_polygons[0]["validation_details"]
    assert details["invalid_edges"] == [[0, 2]]
    assert details["invalid_intersections"] == [[5.0, 5.0]]
    assert "1-2" in dialog.validation_label.text()
    assert "3-4" in dialog.validation_label.text()
    assert "5.0" in dialog.validation_label.text()


def test_mask_viewer_allows_vertex_edit_until_all_polygons_are_valid(
    qt_app, monkeypatch, messages
):
    scene = Scene()
    scene.cmd = CommandManager()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [
        {"polygon": TRIANGLE_A},
        {"polygon": [(20, 20), (80, 20), (80, 20), (20, 80)]},
    ]

    dialog.viewer.set_overlay_polygons(dialog._last_polygons)
    dialog._update_polygon_validation_feedback()
    assert dialog.apply_button.isEnabled() is False
    assert dialog._last_polygons[1]["is_valid"] is False
    assert "duplicate" in dialog.validation_label.text().lower()

    dialog.viewer._editing_polygon_index = 1
    dialog.viewer._editing_vertex_index = 2
    dialog.viewer._move_editing_vertex(QPointF(80, 80))

    assert dialog._last_polygons[1]["is_valid"] is True
    assert dialog.apply_button.isEnabled() is True
    dialog._apply_to_scene()

    assert len(scene.objects) == 2
    assert scene.cmd.undo_count == 1
    assert close.call_count == 1
    assert len(messages["information"]) == 1


def test_mask_viewer_context_edits_are_local_and_undoable(
    qt_app, monkeypatch, messages
):
    scene = Scene()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [
        {"polygon": [(20, 20), (80, 20), (80, 80), (20, 80)]},
    ]
    viewer = dialog.viewer
    viewer.set_overlay_polygons(dialog._last_polygons)
    viewer._context_polygon_index = 0
    viewer._context_vertex_index = 1
    viewer._context_image_point = QPointF(50, 20)

    viewer.add_context_vertex()
    assert len(dialog._last_polygons[0]["polygon"]) == 5
    viewer.undo_polygon_edit()
    assert len(dialog._last_polygons[0]["polygon"]) == 4
    viewer.redo_polygon_edit()
    assert len(dialog._last_polygons[0]["polygon"]) == 5

    viewer.set_selected_polygon_index(0)
    viewer.set_gizmo_enabled(True)
    assert set(viewer._gizmo_handle_positions()) == {"move", "scale", "rotate"}
    viewer._begin_gizmo_drag("move", QPointF(0, 0))
    viewer._move_gizmo(QPointF(10, 5))
    viewer._finish_gizmo_drag()
    assert dialog._last_polygons[0]["polygon"][0] == (30, 25)
    viewer.undo_polygon_edit()
    assert dialog._last_polygons[0]["polygon"][0] == (20, 20)
    assert scene.objects == {}
    assert close.call_count == 0


def test_mask_viewer_rejected_result_does_not_claim_success(
    qt_app, monkeypatch, messages
):
    scene = Scene()
    scene.cmd = SimpleNamespace(
        execute=lambda command, _scene: CommandResult.rejected(
            command, "execute", "controlled rejection"
        )
    )
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [{"polygon": TRIANGLE_A}]

    dialog._apply_to_scene()

    assert close.call_count == 0
    assert not messages["information"]
    assert len(messages["warning"]) == 1


def test_mask_viewer_failed_result_does_not_claim_success(
    qt_app, monkeypatch, messages
):
    scene = Scene()
    scene.cmd = SimpleNamespace(
        execute=lambda command, _scene: CommandResult.failed(
            command, "execute", "ControlledError", "controlled failure"
        )
    )
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)
    dialog._last_polygons = [{"polygon": TRIANGLE_A}]

    dialog._apply_to_scene()

    assert close.call_count == 0
    assert not messages["information"]
    assert len(messages["critical"]) == 1


def test_mask_viewer_empty_result_does_nothing(qt_app, monkeypatch, messages):
    scene = Scene()
    scene.cmd = CommandManager()
    dialog, close = make_mask_dialog(qt_app, monkeypatch, scene)

    dialog._apply_to_scene()

    assert close.call_count == 0
    assert scene.cmd.undo_count == 0
    assert not any(messages.values())


def make_collision_scene():
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("A", TRIANGLE_A)
    scene.add_object("B", TRIANGLE_B)
    return scene


def test_collision_panel_auto_generation_uses_one_history_entry(qt_app, messages):
    scene = make_collision_scene()
    panel = CollisionPanel(scene)
    physics = StaticCollisionManager()
    panel.set_collision_manager(physics)

    panel._on_auto_generate()

    assert scene.cmd.undo_count == 1
    assert set(scene.collision_shapes) == {"A", "B"}
    assert set(physics.objects) == {"A", "B"}
    assert len(messages["information"]) == 1


def test_collision_panel_syncs_cache_on_undo_and_redo(qt_app, messages):
    scene = make_collision_scene()
    old = {"legacy": [(1.0, 1.0), (2.0, 1.0), (2.0, 2.0)]}
    scene.collision_shapes = copy.deepcopy(old)
    panel = CollisionPanel(scene)
    physics = StaticCollisionManager()
    panel.set_collision_manager(physics)

    panel._on_auto_generate()
    assert set(physics.objects) == {"A", "B"}
    assert scene.cmd.undo(scene).changed
    assert set(physics.objects) == {"legacy"}
    assert scene.cmd.redo(scene).changed
    assert set(physics.objects) == {"A", "B"}


def test_collision_panel_blocks_without_command_manager(qt_app, messages):
    scene = make_collision_scene()
    scene.cmd = None
    panel = CollisionPanel(scene)
    panel._on_auto_generate()
    assert scene.collision_shapes == {}
    assert len(messages["warning"]) == 1


def test_collision_panel_no_valid_polygons_creates_no_history(qt_app, messages):
    scene = Scene()
    scene.cmd = CommandManager()
    panel = CollisionPanel(scene)
    panel._on_auto_generate()
    assert scene.cmd.undo_count == 0
    assert scene.collision_shapes == {}
    assert len(messages["information"]) == 1


def test_collision_panel_existing_shapes_are_noop_but_cache_is_synchronized(
    qt_app, messages
):
    scene = make_collision_scene()
    scene.collision_shapes = {
        "A": [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)],
        "B": [(40.0, 0.0), (60.0, 0.0), (60.0, 20.0)],
    }
    panel = CollisionPanel(scene)
    physics = StaticCollisionManager()
    panel.set_collision_manager(physics)
    physics.clear()

    panel._on_auto_generate()

    assert scene.cmd.undo_count == 0
    assert set(physics.objects) == {"A", "B"}
    assert len(messages["information"]) == 1


def test_collision_batch_test_syncs_cache_without_creating_history(qt_app, messages):
    scene = make_collision_scene()
    scene.collision_shapes = {
        "A": [(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)],
        "B": [(40.0, 0.0), (60.0, 0.0), (60.0, 20.0)],
    }
    panel = CollisionPanel(scene)
    physics = StaticCollisionManager()
    panel.set_collision_manager(physics)
    physics.clear()

    panel._on_batch_test()

    assert set(physics.objects) == {"A", "B"}
    assert scene.cmd.undo_count == 0


def test_package5b_paths_have_no_direct_batch_mutation_fallbacks():
    from src.tools import auto_detect
    from src.ui import collision_panel, mask_viewer

    mask_source = inspect.getsource(mask_viewer.MaskViewerDialog._apply_to_scene)
    auto_source = inspect.getsource(auto_detect.detect_and_create_objects)
    collision_source = inspect.getsource(
        collision_panel.CollisionPanel._on_auto_generate
    )

    assert "scene.add_polygon" not in mask_source
    assert ".execute(scene)" not in auto_source
    assert "CompositeCommand" in mask_source
    assert "CompositeCommand" in auto_source
    assert "collision_shapes =" not in collision_source
    assert "AutoGenerateCollisionShapesCommand" in collision_source

    for source in (mask_source, auto_source, collision_source):
        ast.parse(source.lstrip())
