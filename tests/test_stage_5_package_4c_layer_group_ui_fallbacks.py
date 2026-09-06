"""Stage 5 package 4C: layer/group UI without direct fallbacks."""

from __future__ import annotations

import copy
import inspect

import pytest
from PySide6.QtWidgets import QApplication

from src.core.commands import (
    AddToGroupCommand,
    CommandManager,
    CommandStatus,
    CreateGroupCommand,
    CreateLayerCommand,
    MoveGroupCommand,
    MoveLayerCommand,
    RemoveFromGroupCommand,
    RemoveGroupCommand,
    RemoveLayerCommand,
    ToggleGroupLockCommand,
    ToggleGroupVisibilityCommand,
    ToggleLayerLockCommand,
    ToggleLayerVisibilityCommand,
)
from src.models.scene import Scene
from src.ui.groups_panel import GroupsPanel
from src.ui.layers_panel import LayersPanel


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=50)
    return scene


def _add_object(scene: Scene, object_id: str = "A") -> None:
    scene.add_object(
        object_id,
        [(10, 10), (110, 10), (110, 90), (10, 90)],
        select=True,
    )


def _layer_state(scene: Scene):
    return [
        (layer.id, layer.name, layer.visible, layer.locked) for layer in scene.layers
    ]


def _group_state(scene: Scene):
    return [
        (
            group.id,
            group.name,
            group.visible,
            group.locked,
            tuple(group.members),
        )
        for group in scene.groups
    ]


def test_create_layer_undo_redo_preserves_identity_and_index():
    scene = _scene()
    command = CreateLayerCommand("Gameplay")

    assert scene.cmd.execute(command, scene).status is CommandStatus.APPLIED
    layer_id = command.layer_id
    assert layer_id is not None
    created = _layer_state(scene)
    assert scene.layers[-1].id == layer_id

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert all(layer.id != layer_id for layer in scene.layers)
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert _layer_state(scene) == created


def test_remove_layer_undo_restores_exact_index_state_and_assignments():
    scene = _scene()
    first = scene.create_layer("First")
    removed = scene.create_layer("Removed")
    scene.create_layer("Last")
    removed.visible = False
    removed.locked = True
    _add_object(scene)
    scene.objects["A"].layer_id = removed.id
    scene.cmd.clear()
    origin = (_layer_state(scene), scene.objects["A"].layer_id)

    assert scene.cmd.execute(RemoveLayerCommand(removed.id), scene).changed
    assert scene.objects["A"].layer_id == "layer_default"
    assert scene.cmd.undo(scene).changed
    assert (_layer_state(scene), scene.objects["A"].layer_id) == origin
    assert scene.layers[1].id == first.id
    assert scene.layers[2].id == removed.id


def test_remove_default_layer_is_rejected_without_history():
    scene = _scene()
    origin = _layer_state(scene)

    result = scene.cmd.execute(
        RemoveLayerCommand("layer_default"),
        scene,
    )

    assert result.status is CommandStatus.REJECTED
    assert _layer_state(scene) == origin
    assert scene.cmd.undo_count == 0


def test_move_layer_undo_redo_restores_exact_order():
    scene = _scene()
    first = scene.create_layer("First")
    second = scene.create_layer("Second")
    scene.cmd.clear()
    origin = [layer.id for layer in scene.layers]

    assert scene.cmd.execute(MoveLayerCommand(second.id, 1), scene).changed
    moved = [layer.id for layer in scene.layers]
    assert moved == ["layer_default", second.id, first.id]
    assert scene.cmd.undo(scene).changed
    assert [layer.id for layer in scene.layers] == origin
    assert scene.cmd.redo(scene).changed
    assert [layer.id for layer in scene.layers] == moved


def test_toggle_layer_visibility_notifies_and_is_exact():
    scene = _scene()
    layer = scene.create_layer("Visible")
    scene.cmd.clear()
    notices = []
    scene.subscribe(lambda: notices.append(_layer_state(scene)))

    assert scene.cmd.execute(
        ToggleLayerVisibilityCommand(layer.id),
        scene,
    ).changed
    assert layer.visible is False
    assert scene.cmd.undo(scene).changed
    assert layer.visible is True
    assert scene.cmd.redo(scene).changed
    assert layer.visible is False
    assert len(notices) == 3


def test_toggle_layer_lock_notifies_and_is_exact():
    scene = _scene()
    layer = scene.create_layer("Unlocked")
    scene.cmd.clear()
    notices = []
    scene.subscribe(lambda: notices.append(_layer_state(scene)))

    assert scene.cmd.execute(
        ToggleLayerLockCommand(layer.id),
        scene,
    ).changed
    assert layer.locked is True
    assert scene.cmd.undo(scene).changed
    assert layer.locked is False
    assert scene.cmd.redo(scene).changed
    assert layer.locked is True
    assert len(notices) == 3


def test_create_group_undo_redo_preserves_identity_and_index():
    scene = _scene()
    command = CreateGroupCommand("Actors")

    assert scene.cmd.execute(command, scene).changed
    group_id = command.group_id
    assert group_id is not None
    created = _group_state(scene)
    assert scene.cmd.undo(scene).changed
    assert scene.groups == []
    assert scene.cmd.redo(scene).changed
    assert _group_state(scene) == created


def test_remove_group_undo_restores_exact_index_state_and_members():
    scene = _scene()
    _add_object(scene)
    scene.create_group("First")
    removed = scene.create_group("Removed")
    scene.create_group("Last")
    removed.visible = False
    removed.locked = True
    removed.members = ["A"]
    scene.cmd.clear()
    origin = _group_state(scene)

    assert scene.cmd.execute(RemoveGroupCommand(removed.id), scene).changed
    assert scene.cmd.undo(scene).changed
    assert _group_state(scene) == origin


def test_move_group_undo_redo_restores_exact_order():
    scene = _scene()
    first = scene.create_group("First")
    second = scene.create_group("Second")
    scene.cmd.clear()
    origin = [group.id for group in scene.groups]

    assert scene.cmd.execute(MoveGroupCommand(second.id, 0), scene).changed
    moved = [group.id for group in scene.groups]
    assert moved == [second.id, first.id]
    assert scene.cmd.undo(scene).changed
    assert [group.id for group in scene.groups] == origin
    assert scene.cmd.redo(scene).changed
    assert [group.id for group in scene.groups] == moved


def test_add_to_group_undo_redo_is_exact():
    scene = _scene()
    _add_object(scene)
    group = scene.create_group("Actors")
    scene.cmd.clear()

    assert scene.cmd.execute(
        AddToGroupCommand(group.id, "A"),
        scene,
    ).changed
    assert group.members == ["A"]
    assert scene.cmd.undo(scene).changed
    assert group.members == []
    assert scene.cmd.redo(scene).changed
    assert group.members == ["A"]


def test_add_existing_membership_is_no_change_without_history():
    scene = _scene()
    _add_object(scene)
    group = scene.create_group("Actors")
    group.members = ["A"]
    scene.cmd.clear()

    result = scene.cmd.execute(
        AddToGroupCommand(group.id, "A"),
        scene,
    )

    assert result.status is CommandStatus.NO_CHANGE
    assert group.members == ["A"]
    assert scene.cmd.undo_count == 0


def test_remove_from_group_undo_redo_is_exact():
    scene = _scene()
    _add_object(scene)
    group = scene.create_group("Actors")
    group.members = ["A"]
    scene.cmd.clear()

    command = RemoveFromGroupCommand(group.id, "A")
    assert scene.cmd.execute(command, scene).changed
    assert group.members == []
    assert scene.cmd.undo(scene).changed
    assert group.members == ["A"]
    assert scene.cmd.redo(scene).changed
    assert group.members == []


def test_remove_absent_membership_is_no_change_without_history():
    scene = _scene()
    _add_object(scene)
    group = scene.create_group("Actors")
    scene.cmd.clear()

    result = scene.cmd.execute(
        RemoveFromGroupCommand(group.id, "A"),
        scene,
    )

    assert result.status is CommandStatus.NO_CHANGE
    assert group.members == []
    assert scene.cmd.undo_count == 0


def test_toggle_group_visibility_notifies_and_is_exact():
    scene = _scene()
    group = scene.create_group("Visible")
    scene.cmd.clear()
    notices = []
    scene.subscribe(lambda: notices.append(_group_state(scene)))

    assert scene.cmd.execute(
        ToggleGroupVisibilityCommand(group.id),
        scene,
    ).changed
    assert group.visible is False
    assert scene.cmd.undo(scene).changed
    assert group.visible is True
    assert scene.cmd.redo(scene).changed
    assert group.visible is False
    assert len(notices) == 3


def test_toggle_group_lock_notifies_and_is_exact():
    scene = _scene()
    group = scene.create_group("Unlocked")
    scene.cmd.clear()
    notices = []
    scene.subscribe(lambda: notices.append(_group_state(scene)))

    assert scene.cmd.execute(
        ToggleGroupLockCommand(group.id),
        scene,
    ).changed
    assert group.locked is True
    assert scene.cmd.undo(scene).changed
    assert group.locked is False
    assert scene.cmd.redo(scene).changed
    assert group.locked is True
    assert len(notices) == 3


@pytest.mark.parametrize(
    "action",
    ("create", "delete", "up", "down", "visibility", "lock"),
)
def test_layers_panel_blocks_every_action_without_command_manager(
    qt_app,
    monkeypatch,
    action,
):
    scene = Scene()
    first = scene.create_layer("First")
    second = scene.create_layer("Second")
    scene.cmd = None
    panel = LayersPanel(scene)
    presentations = []
    monkeypatch.setattr(
        "src.ui.layers_panel.show_p2d05_error",
        lambda *args, **kwargs: presentations.append(kwargs) or None,
    )

    if action == "create":
        invoke = panel._create
    elif action == "delete":
        panel._select_layer_id(first.id)
        invoke = panel._delete
    elif action == "up":
        panel._select_layer_id(second.id)
        invoke = panel._up
    elif action == "down":
        panel._select_layer_id(first.id)
        invoke = panel._down
    elif action == "visibility":
        panel._select_layer_id(first.id)
        invoke = panel._toggle_vis
    else:
        panel._select_layer_id(first.id)
        invoke = panel._toggle_lock

    origin = copy.deepcopy(_layer_state(scene))
    invoke()

    assert _layer_state(scene) == origin
    assert len(presentations) == 1
    assert presentations[0]["severity"] == "critical"
    assert presentations[0]["channel"] == "modal"
    assert presentations[0]["operation"] == "edit"
    panel.close()


@pytest.mark.parametrize(
    "action",
    (
        "new",
        "delete",
        "add",
        "remove",
        "up",
        "down",
        "visibility",
        "lock",
    ),
)
def test_groups_panel_blocks_every_action_without_command_manager(
    qt_app,
    monkeypatch,
    action,
):
    scene = Scene()
    _add_object(scene)
    first = scene.create_group("First")
    second = scene.create_group("Second")
    first.members = ["A"]
    scene.cmd = None
    panel = GroupsPanel(scene)
    panel._select_group_id(first.id)
    messages = []
    monkeypatch.setattr(
        "src.ui.groups_panel.QMessageBox.critical",
        lambda *args, **kwargs: messages.append(args),
    )
    monkeypatch.setattr(
        "src.ui.groups_panel.QInputDialog.getText",
        lambda *args, **kwargs: ("Third", True),
    )

    if action == "new":
        invoke = panel._on_new
    elif action == "delete":
        invoke = panel._on_delete
    elif action == "add":
        first.members = []
        invoke = panel._on_add_selected
    elif action == "remove":
        first.members = ["A"]
        invoke = panel._on_remove_selected
    elif action == "up":
        panel._select_group_id(second.id)
        invoke = panel._on_up
    elif action == "down":
        panel._select_group_id(first.id)
        invoke = panel._on_down
    elif action == "visibility":
        invoke = panel._on_toggle_vis
    else:
        invoke = panel._on_toggle_lock

    origin = copy.deepcopy(_group_state(scene))
    invoke()

    assert _group_state(scene) == origin
    assert len(messages) == 1
    assert "hist" in str(messages[0]).lower()
    panel.close()


def test_layer_group_panels_have_no_direct_scene_mutation_fallbacks():
    layer_source = inspect.getsource(LayersPanel)
    group_source = inspect.getsource(GroupsPanel)

    for forbidden in (
        "scene.create_layer(",
        "scene.remove_layer(",
        "scene.move_layer(",
        "scene.set_layer_visibility(",
        "scene.set_layer_lock(",
    ):
        assert forbidden not in layer_source

    for forbidden in (
        "scene.create_group(",
        "scene.remove_group(",
        "scene.add_object_to_group(",
        "scene.remove_object_from_group(",
        "scene.move_group(",
        "g.visible =",
        "g.locked =",
        "scene._notify(",
    ):
        assert forbidden not in group_source

    for required in (
        "CreateLayerCommand",
        "RemoveLayerCommand",
        "MoveLayerCommand",
        "ToggleLayerVisibilityCommand",
        "ToggleLayerLockCommand",
    ):
        assert required in layer_source

    for required in (
        "CreateGroupCommand",
        "RemoveGroupCommand",
        "AddToGroupCommand",
        "RemoveFromGroupCommand",
        "MoveGroupCommand",
        "ToggleGroupVisibilityCommand",
        "ToggleGroupLockCommand",
    ):
        assert required in group_source
