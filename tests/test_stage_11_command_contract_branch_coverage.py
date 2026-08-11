"""Stage 11 package 5: command transaction and precondition branches."""

from __future__ import annotations

import math

import pytest

from src.core.commands import (
    AddToGroupCommand,
    AutoGenerateCollisionShapesCommand,
    ClearSceneCommand,
    Command,
    CommandManager,
    CommandResult,
    CommandStatus,
    CompositeCommand,
    CreateGroupCommand,
    CreateLayerCommand,
    CreateObjectCommand,
    DeleteObjectCommand,
    MoveGroupCommand,
    MoveLayerCommand,
    RemoveFromGroupCommand,
    RemoveGroupCommand,
    RemoveLayerCommand,
    RenameObjectCommand,
    ToggleCollisionCommand,
    ToggleGroupLockCommand,
    ToggleGroupVisibilityCommand,
    ToggleLayerLockCommand,
    ToggleLayerVisibilityCommand,
    UpdateObjectGeometryCommand,
    UpdatePolygonCommand,
    _EmptyHistoryCommand,
    _freeze_state,
)
from src.models.scene import Scene

SQUARE = [(0, 0), (20, 0), (20, 20), (0, 20)]
SHIFTED = [(2, 2), (22, 2), (22, 22), (2, 22)]


def _scene(*, with_object: bool = False) -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    if with_object:
        scene.add_object("A", SQUARE, select=True)
        scene.cmd.clear()
    return scene


def _status(result: CommandResult, expected: CommandStatus) -> None:
    assert result.status is expected
    assert result.command_name
    assert result.operation in {"execute", "undo", "redo"}


class _SnapshotFailure(Command):
    def _snapshot_state(self):
        raise RuntimeError("snapshot failed")

    def execute(self, scene):
        scene.selected_id = "unreachable"


class _ExplodingCommand(Command):
    def execute(self, scene):
        scene.selected_id = "mutated"
        raise RuntimeError("operation failed")


class _ReportedAppliedWithoutMutation(Command):
    def execute(self, scene):
        return CommandResult.applied(self, "execute")


class _ReportedNoChangeWithMutation(Command):
    def execute(self, scene):
        scene.selected_id = "mutated"
        return CommandResult.no_change(self, "execute")


class _ImplicitNoChange(Command):
    def execute(self, scene):
        return None


class _SelectionCommand(Command):
    def __init__(
        self,
        old_value,
        new_value,
        *,
        fail_undo: bool = False,
        fail_second_execute: bool = False,
    ):
        self.old_value = old_value
        self.new_value = new_value
        self.fail_undo = fail_undo
        self.fail_second_execute = fail_second_execute
        self.execute_count = 0

    def execute(self, scene):
        self.execute_count += 1
        if self.fail_second_execute and self.execute_count > 1:
            return CommandResult.no_change(self, "execute", "compensation blocked")
        scene.selected_id = self.new_value

    def undo(self, scene):
        if self.fail_undo:
            return CommandResult.no_change(self, "undo", "rollback blocked")
        scene.selected_id = self.old_value


class _ExplicitFailure(Command):
    def execute(self, scene):
        return CommandResult.failed(self, "execute", "ExpectedFailure", "blocked")


def test_command_base_helpers_and_empty_history_adapter():
    with pytest.raises(NotImplementedError):
        Command().execute(None)
    with pytest.raises(NotImplementedError):
        Command().undo(None)

    assert _freeze_state({"values": {3, 1, 2}}) == (("values", (1, 2, 3)),)
    assert "object" in _freeze_state(object())
    assert _EmptyHistoryCommand().execute(None) is None
    assert _EmptyHistoryCommand().undo(None) is None


def test_manager_restores_snapshot_execution_and_contract_failures():
    scene = _scene()

    snapshot = scene.cmd.execute(_SnapshotFailure(), scene)
    _status(snapshot, CommandStatus.FAILED)
    assert snapshot.error_type == "RuntimeError"
    assert scene.selected_id is None

    exploded = scene.cmd.execute(_ExplodingCommand(), scene)
    _status(exploded, CommandStatus.FAILED)
    assert scene.selected_id is None

    reported_change = scene.cmd.execute(_ReportedAppliedWithoutMutation(), scene)
    _status(reported_change, CommandStatus.NO_CHANGE)

    inconsistent = scene.cmd.execute(_ReportedNoChangeWithMutation(), scene)
    _status(inconsistent, CommandStatus.FAILED)
    assert inconsistent.error_type == "CommandContractError"
    assert scene.selected_id is None

    implicit = scene.cmd.execute(_ImplicitNoChange(), scene)
    _status(implicit, CommandStatus.NO_CHANGE)
    assert scene.cmd.undo_count == 0


def test_manager_listener_isolation_limits_and_clear():
    scene = _scene()
    manager = CommandManager(max_history=1)
    notices = []

    def broken_listener():
        raise RuntimeError("listener failed")

    manager.subscribe(broken_listener)
    manager.subscribe(broken_listener)
    manager.subscribe(lambda: notices.append((manager.undo_count, manager.redo_count)))

    _status(manager.execute(CreateGroupCommand("one"), scene), CommandStatus.APPLIED)
    _status(manager.execute(CreateGroupCommand("two"), scene), CommandStatus.APPLIED)
    assert manager.undo_count == 1
    _status(manager.undo(scene), CommandStatus.APPLIED)
    _status(manager.redo(scene), CommandStatus.APPLIED)
    assert manager.undo_count == 1
    manager.unsubscribe(broken_listener)
    manager.unsubscribe(broken_listener)
    manager.clear()
    assert notices[-1] == (0, 0)
    assert manager.can_undo is False
    assert manager.can_redo is False

    with pytest.raises(ValueError):
        CommandManager(max_history=0)


def test_composite_rollbacks_and_compensation_failures_are_atomic():
    scene = _scene()
    _status(CompositeCommand([]).execute(scene), CommandStatus.NO_CHANGE)
    _status(CompositeCommand([]).undo(scene), CommandStatus.NO_CHANGE)

    rejected = scene.cmd.execute(
        CompositeCommand([_SelectionCommand(None, "first"), _ImplicitNoChange()]),
        scene,
    )
    _status(rejected, CommandStatus.REJECTED)
    assert scene.selected_id is None

    failed = scene.cmd.execute(
        CompositeCommand([_SelectionCommand(None, "first"), _ExplicitFailure()]),
        scene,
    )
    _status(failed, CommandStatus.FAILED)
    assert failed.error_type == "ExpectedFailure"
    assert scene.selected_id is None

    rollback_failed = scene.cmd.execute(
        CompositeCommand(
            [
                _SelectionCommand(None, "first", fail_undo=True),
                _ImplicitNoChange(),
            ]
        ),
        scene,
    )
    _status(rollback_failed, CommandStatus.FAILED)
    assert rollback_failed.error_type == "CompositeRollbackError"
    assert scene.selected_id is None

    first = _SelectionCommand(None, "first", fail_undo=True)
    second = _SelectionCommand("first", "second")
    composite = CompositeCommand([first, second])
    _status(scene.cmd.execute(composite, scene), CommandStatus.APPLIED)
    undo_failed = scene.cmd.undo(scene)
    _status(undo_failed, CommandStatus.FAILED)
    assert undo_failed.error_type == "CompositeUndoError"
    assert scene.selected_id == "second"

    scene = _scene()
    first = _SelectionCommand(None, "first", fail_undo=True)
    second = _SelectionCommand("first", "second", fail_second_execute=True)
    composite = CompositeCommand([first, second])
    _status(scene.cmd.execute(composite, scene), CommandStatus.APPLIED)
    compensation_failed = scene.cmd.undo(scene)
    _status(compensation_failed, CommandStatus.FAILED)
    assert compensation_failed.error_type == "CompositeCompensationError"
    assert scene.selected_id == "second"


def test_layer_commands_reject_missing_backups_and_stale_state():
    scene = _scene(with_object=True)
    layer = scene.create_layer("Gameplay")
    scene.objects["A"].layer_id = layer.id

    cases = [
        RemoveLayerCommand("missing"),
        MoveLayerCommand("missing", 0),
        ToggleLayerVisibilityCommand("missing"),
        ToggleLayerLockCommand("missing"),
        CreateLayerCommand(" "),
    ]
    for command in cases:
        _status(scene.cmd.execute(command, scene), CommandStatus.REJECTED)

    undo_cases = [
        RemoveLayerCommand(layer.id),
        CreateLayerCommand("new"),
        MoveLayerCommand(layer.id, 0),
        ToggleLayerVisibilityCommand(layer.id),
        ToggleLayerLockCommand(layer.id),
    ]
    for command in undo_cases:
        _status(command.undo(scene), CommandStatus.REJECTED)

    remove = RemoveLayerCommand(layer.id)
    _status(scene.cmd.execute(remove, scene), CommandStatus.APPLIED)
    scene.objects.pop("A")
    _status(scene.cmd.undo(scene), CommandStatus.FAILED)
    assert all(candidate.id != layer.id for candidate in scene.layers)


@pytest.mark.parametrize(
    ("factory", "attribute"),
    [
        (ToggleLayerVisibilityCommand, "visible"),
        (ToggleLayerLockCommand, "locked"),
    ],
)
def test_layer_toggle_commands_reject_tampered_undo_and_redo(factory, attribute):
    scene = _scene()
    layer = scene.create_layer("Gameplay")
    command = factory(layer.id)
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    setattr(layer, attribute, getattr(command, "_old"))
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)

    layer = next(candidate for candidate in scene.layers if candidate.id == layer.id)
    setattr(layer, attribute, getattr(command, "_new"))
    _status(scene.cmd.undo(scene), CommandStatus.APPLIED)
    setattr(layer, attribute, getattr(command, "_new"))
    _status(scene.cmd.redo(scene), CommandStatus.REJECTED)


def test_group_commands_reject_invalid_and_broken_relationships():
    scene = _scene(with_object=True)
    group = scene.create_group("Actors")
    group.members = ["A"]

    cases = [
        CreateGroupCommand(" "),
        RemoveGroupCommand("missing"),
        AddToGroupCommand("missing", "A"),
        AddToGroupCommand(group.id, "missing"),
        RemoveFromGroupCommand("missing", "A"),
        MoveGroupCommand("missing", 0),
        ToggleGroupVisibilityCommand("missing"),
        ToggleGroupLockCommand("missing"),
    ]
    for command in cases:
        _status(scene.cmd.execute(command, scene), CommandStatus.REJECTED)

    undo_cases = [
        CreateGroupCommand("new"),
        RemoveGroupCommand(group.id),
        AddToGroupCommand(group.id, "A"),
        RemoveFromGroupCommand(group.id, "A"),
        MoveGroupCommand(group.id, 0),
        ToggleGroupVisibilityCommand(group.id),
        ToggleGroupLockCommand(group.id),
    ]
    for command in undo_cases:
        _status(command.undo(scene), CommandStatus.REJECTED)

    remove = RemoveGroupCommand(group.id)
    _status(scene.cmd.execute(remove, scene), CommandStatus.APPLIED)
    scene.objects.pop("A")
    _status(scene.cmd.undo(scene), CommandStatus.FAILED)
    assert scene.groups == []


def test_group_membership_commands_reject_tampered_undo():
    scene = _scene(with_object=True)
    group = scene.create_group("Actors")

    add = AddToGroupCommand(group.id, "A")
    _status(scene.cmd.execute(add, scene), CommandStatus.APPLIED)
    group.members.clear()
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)

    group = next(candidate for candidate in scene.groups if candidate.id == group.id)
    group.members = ["A"]
    remove = RemoveFromGroupCommand(group.id, "A")
    _status(scene.cmd.execute(remove, scene), CommandStatus.APPLIED)
    scene.objects.pop("A")
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)

    scene.objects["A"] = _scene(with_object=True).objects["A"]
    group = next(candidate for candidate in scene.groups if candidate.id == group.id)
    group.members = ["A"]
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)


@pytest.mark.parametrize(
    ("factory", "attribute"),
    [
        (ToggleGroupVisibilityCommand, "visible"),
        (ToggleGroupLockCommand, "locked"),
    ],
)
def test_group_toggle_commands_reject_tampered_undo_and_redo(factory, attribute):
    scene = _scene()
    group = scene.create_group("Actors")
    command = factory(group.id)
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    setattr(group, attribute, getattr(command, "_old"))
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)

    group = next(candidate for candidate in scene.groups if candidate.id == group.id)
    setattr(group, attribute, getattr(command, "_new"))
    _status(scene.cmd.undo(scene), CommandStatus.APPLIED)
    setattr(group, attribute, getattr(command, "_new"))
    _status(scene.cmd.redo(scene), CommandStatus.REJECTED)


def test_polygon_commands_reject_missing_stale_and_inconsistent_backups():
    scene = _scene(with_object=True)

    _status(
        scene.cmd.execute(UpdatePolygonCommand("missing", SQUARE, SHIFTED), scene),
        CommandStatus.REJECTED,
    )
    _status(
        scene.cmd.execute(UpdatePolygonCommand("A", SHIFTED, SQUARE), scene),
        CommandStatus.REJECTED,
    )
    _status(
        scene.cmd.execute(UpdatePolygonCommand("A", SQUARE, SQUARE), scene),
        CommandStatus.NO_CHANGE,
    )
    _status(
        UpdatePolygonCommand("A", SQUARE, SHIFTED).undo(scene), CommandStatus.REJECTED
    )

    scene.set_object_collision("A", True)
    command = UpdatePolygonCommand("A", SQUARE, SHIFTED)
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    command._old_collision = None
    _status(scene.cmd.undo(scene), CommandStatus.FAILED)


def test_object_geometry_command_validates_each_exact_state():
    scene = _scene(with_object=True)

    missing = UpdateObjectGeometryCommand(
        "missing",
        SQUARE,
        SHIFTED,
        old_has_collision=False,
        old_collision=None,
        new_has_collision=False,
        new_collision=None,
    )
    _status(scene.cmd.execute(missing, scene), CommandStatus.REJECTED)

    stale = UpdateObjectGeometryCommand(
        "A",
        SHIFTED,
        SQUARE,
        old_has_collision=False,
        old_collision=None,
        new_has_collision=False,
        new_collision=None,
    )
    _status(scene.cmd.execute(stale, scene), CommandStatus.REJECTED)

    no_change = UpdateObjectGeometryCommand(
        "A",
        SQUARE,
        SQUARE,
        old_has_collision=False,
        old_collision=None,
        new_has_collision=False,
        new_collision=None,
    )
    _status(scene.cmd.execute(no_change, scene), CommandStatus.NO_CHANGE)

    unavailable = UpdateObjectGeometryCommand(
        "A",
        SQUARE,
        SHIFTED,
        old_has_collision=False,
        old_collision=None,
        new_has_collision=True,
        new_collision=None,
    )
    _status(scene.cmd.execute(unavailable, scene), CommandStatus.FAILED)


@pytest.mark.parametrize(
    ("point", "message"),
    [
        ((1, 2, 3), "invalid polygon point"),
        ((True, 2), "non-numeric x"),
        ((1, False), "non-numeric y"),
        ((math.inf, 2), "non-finite"),
    ],
)
def test_collision_generation_rejects_malformed_coordinates(point, message):
    scene = _scene(with_object=True)
    scene.objects["A"].polygon = [point, (1, 2), (2, 3)]
    result = scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene)
    _status(result, CommandStatus.REJECTED)
    assert message in result.message
    assert scene.collision_shapes == {}


def test_collision_generation_no_change_and_stale_state_paths():
    scene = _scene()
    _status(
        scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene),
        CommandStatus.NO_CHANGE,
    )

    scene.add_object("A", SQUARE)
    scene.collision_shapes["A"] = [(float(x), float(y)) for x, y in SQUARE]
    _status(
        scene.cmd.execute(AutoGenerateCollisionShapesCommand(), scene),
        CommandStatus.NO_CHANGE,
    )

    scene.collision_shapes.clear()
    command = AutoGenerateCollisionShapesCommand()
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    scene.objects["A"].polygon = SHIFTED
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)
    scene.objects["A"].polygon = SQUARE
    scene.collision_shapes.clear()
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)


def test_collision_clear_rename_and_delete_failure_contracts():
    scene = _scene(with_object=True)
    _status(
        scene.cmd.execute(ToggleCollisionCommand("missing"), scene),
        CommandStatus.REJECTED,
    )
    _status(ToggleCollisionCommand("missing").undo(scene), CommandStatus.REJECTED)
    _status(scene.cmd.execute(ClearSceneCommand(), scene), CommandStatus.APPLIED)
    _status(scene.cmd.undo(scene), CommandStatus.APPLIED)

    empty = _scene()
    _status(empty.cmd.execute(ClearSceneCommand(), empty), CommandStatus.NO_CHANGE)

    scene.add_object("B", SHIFTED)
    for command, expected in [
        (RenameObjectCommand("A", " "), CommandStatus.REJECTED),
        (RenameObjectCommand("A", "A"), CommandStatus.NO_CHANGE),
        (RenameObjectCommand("missing", "C"), CommandStatus.REJECTED),
        (RenameObjectCommand("A", "B"), CommandStatus.REJECTED),
        (DeleteObjectCommand("missing"), CommandStatus.REJECTED),
    ]:
        _status(scene.cmd.execute(command, scene), expected)

    _status(DeleteObjectCommand("A").undo(scene), CommandStatus.REJECTED)


def test_delete_undo_rejects_duplicate_and_missing_group_relationship():
    scene = _scene(with_object=True)
    group = scene.create_group("Actors")
    group.members = ["A"]
    command = DeleteObjectCommand("A")
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    scene.add_object("A", SHIFTED)
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)

    scene = _scene(with_object=True)
    group = scene.create_group("Actors")
    group.members = ["A"]
    command = DeleteObjectCommand("A")
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    scene.groups.clear()
    _status(scene.cmd.undo(scene), CommandStatus.FAILED)
    assert "A" not in scene.objects


def test_create_object_rejects_invalid_target_identity_and_stale_collection():
    scene = _scene(with_object=True)
    _status(
        scene.cmd.execute(CreateObjectCommand(SQUARE, layer_id="missing"), scene),
        CommandStatus.REJECTED,
    )
    _status(
        scene.cmd.execute(CreateObjectCommand(SQUARE, object_id="A"), scene),
        CommandStatus.REJECTED,
    )
    _status(CreateObjectCommand(SQUARE).undo(scene), CommandStatus.REJECTED)

    command = CreateObjectCommand(SHIFTED, object_id="B")
    _status(scene.cmd.execute(command, scene), CommandStatus.APPLIED)
    scene.add_object("C", SQUARE)
    _status(scene.cmd.undo(scene), CommandStatus.REJECTED)
