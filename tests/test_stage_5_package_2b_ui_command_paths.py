# Stage 5 package 2B: UI command paths have no manual fallback.

from __future__ import annotations

import inspect

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.commands import (
    CommandManager,
    CommandStatus,
    RenameObjectCommand,
)
from src.models.scene import Scene
from src.ui import canvas_view as canvas_view_module
from src.ui import side_panel as side_panel_module
from src.ui.canvas_view import CanvasView
from src.ui.side_panel import SidePanel


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


def _build_ui(qt_app):
    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    scene.add_object("object", _square(), select=True)
    canvas = CanvasView(scene)
    panel = SidePanel(scene, canvas)
    panel.list.setCurrentRow(0)
    qt_app.processEvents()
    return scene, canvas, panel


def _close_ui(canvas, panel):
    panel.close()
    canvas.close()


def test_included_ui_methods_have_no_manual_fallbacks():
    side_methods = (
        SidePanel._on_toggle_collision,
        SidePanel._on_delete,
        SidePanel._on_rename,
        SidePanel._modify_poly,
        SidePanel._on_invert,
        SidePanel._on_apply,
    )
    canvas_methods = (
        CanvasView._toggle_collision,
        CanvasView._delete_object,
        CanvasView.clean_all,
    )

    side_source = "\n".join(inspect.getsource(method) for method in side_methods)
    canvas_source = "\n".join(inspect.getsource(method) for method in canvas_methods)

    for forbidden in (
        "self.scene.objects[new] =",
        "self.scene.remove_object(",
        "self.scene.set_object_collision(",
        "self.scene.update_polygon(",
        "from src.core.commands import",
        "except ImportError",
    ):
        assert forbidden not in side_source

    for forbidden in (
        "self.model.remove_object(",
        "self.model.objects.clear(",
        "self.model.collision_shapes.clear(",
        "self.model.set_object_collision(",
        "from src.core.commands import",
        "except ImportError",
    ):
        assert forbidden not in canvas_source

    side_module = inspect.getsource(side_panel_module)
    canvas_module = inspect.getsource(canvas_view_module)
    for required in (
        "RenameObjectCommand",
        "DeleteObjectCommand",
        "ToggleCollisionCommand",
        "UpdatePolygonCommand",
        "CommandStatus",
    ):
        assert required in side_module
    for required in (
        "ClearSceneCommand",
        "DeleteObjectCommand",
        "ToggleCollisionCommand",
        "CommandStatus",
    ):
        assert required in canvas_module


def test_side_panel_identity_collision_and_delete_use_history(
    qt_app,
    monkeypatch,
):
    scene, canvas, panel = _build_ui(qt_app)

    monkeypatch.setattr(
        side_panel_module.QInputDialog,
        "getText",
        lambda *args, **kwargs: ("renamed", True),
    )
    panel._on_rename()
    assert "renamed" in scene.objects
    assert scene.cmd.undo_count == 1

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    qt_app.processEvents()
    panel.list.setCurrentRow(0)

    panel._on_toggle_collision()
    assert scene.has_collision("object")
    assert scene.cmd.undo_count == 1

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    qt_app.processEvents()
    panel.list.setCurrentRow(0)

    monkeypatch.setattr(
        side_panel_module.QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    panel._on_delete()
    assert "object" not in scene.objects
    assert scene.cmd.undo_count == 1

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert "object" in scene.objects
    _close_ui(canvas, panel)


def test_side_panel_shape_actions_and_preview_use_history(
    qt_app,
    monkeypatch,
):
    scene, canvas, panel = _build_ui(qt_app)
    scene.image = np.zeros((100, 100, 4), dtype=np.uint8)

    expanded = _square(5)
    monkeypatch.setattr(
        side_panel_module,
        "expand_contract_polygon",
        lambda polygon, shape, delta: list(expanded),
    )
    oid, obj = panel._get_selected_obj()
    panel._modify_poly(oid, obj, 5)
    assert scene.objects["object"].polygon == expanded
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED

    inverted = _square(10)
    monkeypatch.setattr(
        side_panel_module,
        "invert_selection",
        lambda polygon, shape: list(inverted),
    )
    panel._on_invert()
    assert scene.objects["object"].polygon == inverted
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED

    preview = _square(12)
    monkeypatch.setattr(
        side_panel_module,
        "expand_contract_polygon",
        lambda polygon, shape, delta: list(preview),
    )
    panel.slider.setValue(4)
    assert panel._last_preview_poly == preview
    assert canvas._temp_mask is not None

    panel._on_apply()
    assert scene.objects["object"].polygon == preview
    assert panel._last_preview_poly is None
    assert panel.slider.value() == 0
    assert canvas._temp_mask is None
    assert scene.cmd.undo_count == 1

    panel.slider.setValue(3)
    assert panel._last_preview_poly == preview
    panel._on_cancel_preview()
    assert panel._last_preview_poly is None
    assert panel.slider.value() == 0
    assert canvas._temp_mask is None
    _close_ui(canvas, panel)


def test_canvas_context_actions_use_history(
    qt_app,
    monkeypatch,
):
    scene, canvas, panel = _build_ui(qt_app)

    canvas._toggle_collision("object")
    assert scene.has_collision("object")
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED

    canvas._delete_object("object")
    assert "object" not in scene.objects
    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert "object" in scene.objects

    group = scene.create_group("group")
    group.members = ["object"]
    custom_collision = [
        (1.0, 1.0),
        (18.0, 1.0),
        (9.0, 18.0),
    ]
    scene.collision_shapes["object"] = list(custom_collision)
    scene.select_object("object")

    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    canvas.clean_all()
    assert scene.objects == {}
    assert scene.groups == []
    assert scene.collision_shapes == {}
    assert scene.selected_id is None

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["object"]
    assert scene.groups[0].members == ["object"]
    assert scene.collision_shapes["object"] == custom_collision
    assert scene.selected_id == "object"
    _close_ui(canvas, panel)


def test_missing_manager_blocks_side_panel_mutation(
    qt_app,
    monkeypatch,
):
    scene, canvas, panel = _build_ui(qt_app)
    scene.cmd = None
    critical_calls = []

    monkeypatch.setattr(
        side_panel_module.QInputDialog,
        "getText",
        lambda *args, **kwargs: ("renamed", True),
    )
    monkeypatch.setattr(
        side_panel_module.QMessageBox,
        "critical",
        lambda *args, **kwargs: critical_calls.append(args),
    )

    panel._on_rename()
    assert list(scene.objects) == ["object"]
    assert critical_calls
    _close_ui(canvas, panel)


def test_missing_manager_blocks_canvas_mutation(
    qt_app,
    monkeypatch,
):
    scene, canvas, panel = _build_ui(qt_app)
    scene.cmd = None
    critical_calls = []

    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "critical",
        lambda *args, **kwargs: critical_calls.append(args),
    )

    canvas._delete_object("object")
    assert "object" in scene.objects
    assert critical_calls
    _close_ui(canvas, panel)


def test_rejected_command_is_reported_without_history(
    qt_app,
    monkeypatch,
):
    scene, canvas, panel = _build_ui(qt_app)
    scene.add_object("other", _square(40))
    warning_calls = []

    monkeypatch.setattr(
        side_panel_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: warning_calls.append(args),
    )

    result = panel._execute_edit_command(RenameObjectCommand("object", "other"))
    assert result.status is CommandStatus.REJECTED
    assert list(scene.objects) == ["object", "other"]
    assert scene.cmd.undo_count == 0
    assert warning_calls
    _close_ui(canvas, panel)
