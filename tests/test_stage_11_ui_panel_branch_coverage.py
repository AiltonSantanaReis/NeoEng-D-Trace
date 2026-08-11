"""Stage 11 package 5: observable layer, group and side-panel branches."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.commands import CommandManager, CommandResult, CreateGroupCommand
from src.models.scene import Scene
from src.ui import groups_panel as groups_module
from src.ui import layers_panel as layers_module
from src.ui import side_panel as side_module
from src.ui.groups_panel import GroupsPanel
from src.ui.layers_panel import LayersPanel
from src.ui.side_panel import SidePanel

SQUARE = [(4, 4), (24, 4), (24, 24), (4, 24)]
SHIFTED = [(8, 8), (28, 8), (28, 28), (8, 28)]


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


class _CanvasStub:
    def __init__(self):
        self.updated = 0
        self.cleared = 0
        self.masks = []

    def update(self):
        self.updated += 1

    def clear_temp_mask(self):
        self.cleared += 1

    def show_temp_mask(self, mask):
        self.masks.append(np.array(mask, copy=True))


class _ResultManager:
    def __init__(self, result):
        self.result = result

    def execute(self, command, scene):
        return self.result


def _scene(*, with_object: bool = False) -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=50)
    if with_object:
        scene.image = np.zeros((40, 40, 4), dtype=np.uint8)
        scene.add_object("A", SQUARE, select=True)
        scene.cmd.clear()
    return scene


def _messages(monkeypatch, module):
    captured = []
    for name in ("critical", "warning", "information"):
        monkeypatch.setattr(
            module.QMessageBox,
            name,
            lambda *args, _name=name, **kwargs: captured.append((_name, args[1:])),
        )
    return captured


def test_layers_panel_refresh_selection_and_all_real_actions(qt_app):
    scene = _scene()
    first = scene.create_layer("First")
    second = scene.create_layer("Second")
    first.locked = True
    first.visible = False
    panel = LayersPanel(scene)

    assert panel._select_layer_id(first.id)
    panel.refresh()
    assert "[LOCKED]" in panel.list.currentItem().text()
    assert "[HIDDEN]" in panel.list.currentItem().text()
    assert panel._select_layer_id("missing") is False

    panel.list.clearSelection()
    panel.list.setCurrentRow(-1)
    assert panel._selected_layer() == (None, None, None)
    panel._delete()
    panel._up()
    panel._down()
    panel._toggle_vis()
    panel._toggle_lock()

    panel._create()
    created_id = panel.list.currentItem().data(layers_module.Qt.ItemDataRole.UserRole)
    assert created_id not in {first.id, second.id}
    panel._toggle_vis()
    panel._toggle_lock()
    created = next(layer for layer in scene.layers if layer.id == created_id)
    assert created.visible is False
    assert created.locked is True

    panel._up()
    panel._down()
    assert next(layer for layer in scene.layers if layer.id == created_id)
    panel._delete()
    assert all(layer.id != created_id for layer in scene.layers)
    panel.close()


def test_layers_panel_status_and_exception_messages(qt_app, monkeypatch):
    scene = _scene()
    layer = scene.create_layer("Layer")
    panel = LayersPanel(scene)
    panel._select_layer_id(layer.id)
    messages = _messages(monkeypatch, layers_module)
    command = CreateGroupCommand("unused")

    scene.cmd = _ResultManager(CommandResult.rejected(command, "execute", "rejected"))
    panel._execute_edit_command(command)
    scene.cmd = _ResultManager(
        CommandResult.failed(command, "execute", "Failure", "failed")
    )
    panel._execute_edit_command(command)
    assert [kind for kind, _ in messages] == ["warning", "critical"]

    monkeypatch.setattr(
        panel,
        "_execute_edit_command",
        lambda command: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    for action in (panel._create, panel._delete, panel._toggle_vis, panel._toggle_lock):
        action()
    scene.create_layer("Another")
    panel.refresh()
    panel._select_layer_id(scene.layers[-1].id)
    panel._up()
    panel._select_layer_id(scene.layers[0].id)
    panel._down()
    assert sum(kind == "critical" for kind, _ in messages) == 7
    panel.close()


def test_groups_panel_real_actions_language_and_boundaries(qt_app, monkeypatch):
    scene = _scene(with_object=True)
    first = scene.create_group("First")
    second = scene.create_group("Second")
    first.locked = True
    first.visible = False
    panel = GroupsPanel(scene)
    panel._select_group_id(first.id)
    panel.refresh()
    assert "[LOCKED]" in panel.list.currentItem().text()
    assert "[HIDDEN]" in panel.list.currentItem().text()
    assert panel._select_group_id("missing") is False

    monkeypatch.setattr(
        groups_module.QInputDialog, "getText", lambda *a, **k: ("Third", True)
    )
    panel._on_new()
    third_id = panel.list.currentItem().data(groups_module.Qt.ItemDataRole.UserRole)
    panel._on_add_selected()
    assert scene.groups[-1].members == ["A"]
    panel._on_remove_selected()
    assert scene.groups[-1].members == []
    panel._on_toggle_vis()
    panel._on_toggle_lock()
    panel._on_up()
    panel._on_down()
    panel._on_delete()
    assert all(group.id != third_id for group in scene.groups)

    panel._select_group_id(first.id)
    panel._on_up()
    panel._select_group_id(second.id)
    panel._on_down()
    panel.update_language("pt")
    assert panel.btn_new.text() == "Novo Grupo"
    panel.close()


def test_groups_panel_empty_selection_messages_and_exceptions(qt_app, monkeypatch):
    scene = _scene(with_object=True)
    group = scene.create_group("Actors")
    panel = GroupsPanel(scene)
    messages = _messages(monkeypatch, groups_module)

    panel.list.clearSelection()
    panel.list.setCurrentRow(-1)
    assert panel._get_selected_group() == (None, None)
    panel._on_delete()
    panel._on_add_selected()
    panel._on_remove_selected()
    panel._on_up()
    panel._on_down()
    panel._on_toggle_vis()
    panel._on_toggle_lock()
    assert sum(kind == "information" for kind, _ in messages) == 3

    panel._select_group_id(group.id)
    scene.selected_id = None
    panel._on_add_selected()
    panel._on_remove_selected()
    assert sum(kind == "information" for kind, _ in messages) == 5

    monkeypatch.setattr(
        groups_module.QInputDialog, "getText", lambda *a, **k: ("", False)
    )
    panel._on_new()
    monkeypatch.setattr(
        panel,
        "_execute_edit_command",
        lambda command: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        groups_module.QInputDialog, "getText", lambda *a, **k: ("New", True)
    )
    scene.selected_id = "A"
    for action in (
        panel._on_new,
        panel._on_delete,
        panel._on_add_selected,
        panel._on_remove_selected,
        panel._on_toggle_vis,
        panel._on_toggle_lock,
    ):
        action()
    scene.create_group("Second")
    panel.refresh()
    panel._select_group_id(scene.groups[-1].id)
    panel._on_up()
    panel._select_group_id(scene.groups[0].id)
    panel._on_down()
    assert sum(kind == "critical" for kind, _ in messages) == 8
    panel.close()


def test_groups_panel_status_messages(qt_app, monkeypatch):
    scene = _scene()
    panel = GroupsPanel(scene)
    messages = _messages(monkeypatch, groups_module)
    command = CreateGroupCommand("unused")

    scene.cmd = _ResultManager(CommandResult.rejected(command, "execute", "rejected"))
    panel._execute_edit_command(command)
    scene.cmd = _ResultManager(
        CommandResult.failed(command, "execute", "Failure", "failed")
    )
    panel._execute_edit_command(command)
    assert [kind for kind, _ in messages] == ["warning", "critical"]
    panel.close()


def _side_panel(qt_app):
    scene = _scene(with_object=True)
    canvas = _CanvasStub()
    panel = SidePanel(scene, canvas)
    panel.list.setCurrentRow(0)
    qt_app.processEvents()
    return scene, canvas, panel


def test_side_panel_selection_buttons_status_and_compatibility(qt_app, monkeypatch):
    scene, canvas, panel = _side_panel(qt_app)
    messages = _messages(monkeypatch, side_module)

    panel._on_toggle_physics()
    assert scene.has_collision("A")
    assert canvas.updated == 1
    assert panel.btn_collision.isChecked()

    command = CreateGroupCommand("unused")
    scene.cmd = _ResultManager(CommandResult.rejected(command, "execute", "rejected"))
    panel._execute_edit_command(command)
    scene.cmd = _ResultManager(
        CommandResult.failed(command, "execute", "Failure", "failed")
    )
    panel._execute_edit_command(command)
    assert [kind for kind, _ in messages] == ["warning", "critical"]

    scene.cmd = None
    panel._on_toggle_collision()
    assert messages[-1][0] == "critical"

    panel.list.clearSelection()
    panel._update_button_states()
    assert panel.btn_collision.isEnabled() is False
    assert panel._get_selected_obj() == (None, None)
    panel._on_toggle_collision()
    panel._on_delete()
    panel._on_rename()
    panel._on_expand()
    panel._on_contract()
    panel._on_invert()
    panel._on_apply()
    panel.close()


def test_side_panel_dialog_cancellations_and_selection_failure(qt_app, monkeypatch):
    scene, _, panel = _side_panel(qt_app)
    messages = _messages(monkeypatch, side_module)
    monkeypatch.setattr(
        scene,
        "select_object",
        lambda object_id: (_ for _ in ()).throw(RuntimeError("select")),
    )
    panel._on_select()

    monkeypatch.setattr(
        side_module.QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )
    panel._on_delete()
    monkeypatch.setattr(
        side_module.QInputDialog, "getText", lambda *a, **k: ("", False)
    )
    panel._on_rename()
    monkeypatch.setattr(side_module.QInputDialog, "getInt", lambda *a, **k: (4, False))
    panel._on_expand()
    panel._on_contract()
    assert "A" in scene.objects
    assert messages == []
    panel.close()


def test_side_panel_mask_export_paths(qt_app, monkeypatch, tmp_path):
    scene, _, panel = _side_panel(qt_app)
    panel.list.clearSelection()
    panel._on_export()

    panel.list.setCurrentRow(0)
    monkeypatch.setattr(
        side_module.QFileDialog, "getSaveFileName", lambda *a, **k: ("", "")
    )
    panel._on_export()

    target = tmp_path / "mask.png"
    monkeypatch.setattr(
        side_module.QFileDialog, "getSaveFileName", lambda *a, **k: (str(target), "")
    )
    scene.image = None
    panel._on_export()
    scene.image = np.zeros((40, 40, 4), dtype=np.uint8)
    panel._on_export()
    assert target.is_file()
    assert target.stat().st_size > 0

    invalid = tmp_path / "missing" / "mask.png"
    monkeypatch.setattr(
        side_module.QFileDialog, "getSaveFileName", lambda *a, **k: (str(invalid), "")
    )
    panel._on_export()
    assert invalid.exists() is False
    panel.close()


def test_side_panel_shape_preview_success_empty_and_failure(qt_app, monkeypatch):
    scene, canvas, panel = _side_panel(qt_app)
    messages = _messages(monkeypatch, side_module)
    calls = []
    real_modify_poly = panel._modify_poly
    monkeypatch.setattr(
        panel, "_modify_poly", lambda oid, obj, delta: calls.append(delta)
    )
    monkeypatch.setattr(side_module.QInputDialog, "getInt", lambda *a, **k: (6, True))
    panel._on_expand()
    panel._on_contract()
    assert calls == [6, -6]
    monkeypatch.setattr(panel, "_modify_poly", real_modify_poly)

    obj = scene.objects["A"]
    monkeypatch.setattr(side_module, "expand_contract_polygon", lambda *a, **k: [])
    panel._modify_poly("A", obj, 2)
    monkeypatch.setattr(side_module, "invert_selection", lambda *a, **k: [])
    panel._on_invert()

    monkeypatch.setattr(side_module, "expand_contract_polygon", lambda *a, **k: SHIFTED)
    panel._on_slider_change(3)
    assert panel._last_preview_poly == SHIFTED
    assert canvas.masks
    monkeypatch.setattr(side_module, "expand_contract_polygon", lambda *a, **k: [])
    panel._on_slider_change(2)
    assert panel._last_preview_poly is None

    monkeypatch.setattr(
        side_module,
        "expand_contract_polygon",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("shape")),
    )
    panel._on_slider_change(1)
    panel._modify_poly("A", obj, 1)
    assert messages[-1][0] == "critical"

    panel.list.clearSelection()
    panel._on_slider_change(1)
    panel._last_preview_poly = SHIFTED
    panel._on_apply()
    panel.close()


def test_side_panel_apply_and_sprite_export_paths(qt_app, monkeypatch, tmp_path):
    scene, canvas, panel = _side_panel(qt_app)
    messages = _messages(monkeypatch, side_module)
    panel._last_preview_poly = SHIFTED
    panel._on_apply()
    assert scene.objects["A"].polygon == SHIFTED
    assert panel._last_preview_poly is None
    assert canvas.cleared >= 1

    panel.list.clearSelection()
    panel._on_export_now()
    panel.list.setCurrentRow(0)
    monkeypatch.setattr(
        side_module.QFileDialog, "getSaveFileName", lambda *a, **k: ("", "")
    )
    panel._on_export_now()

    from src.exporters import sprite_exporter

    calls = []
    monkeypatch.setattr(
        sprite_exporter,
        "extract_masked_sprite",
        lambda *a, **k: np.ones((2, 2, 4), dtype=np.uint8),
    )
    monkeypatch.setattr(
        sprite_exporter,
        "save_sprite",
        lambda image, path: calls.append((image.shape, path)),
    )
    target = tmp_path / "sprite.png"
    monkeypatch.setattr(
        side_module.QFileDialog, "getSaveFileName", lambda *a, **k: (str(target), "")
    )
    panel._on_export_now()
    assert calls == [((2, 2, 4), str(target))]

    monkeypatch.setattr(
        sprite_exporter,
        "extract_masked_sprite",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sprite")),
    )
    panel._on_export_now()
    assert messages[-1][0] == "critical"
    panel.update_language("pt")
    assert panel.btn_export_now.text() == "Exportar Sprite"
    panel.close()
