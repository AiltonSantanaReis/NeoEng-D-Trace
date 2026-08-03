"""Implementation of :mod:`src.core.commands`.

Implementation preserved in the single ``src`` source tree.
"""

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.logger import logger


class CommandStatus(str, Enum):
    """Observable outcome of one command operation."""

    APPLIED = "applied"
    NO_CHANGE = "no_change"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True)
class CommandResult:
    """Explicit command outcome returned to every manager caller."""

    status: CommandStatus
    command_name: str
    operation: str
    message: str = ""
    error_type: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status in {
            CommandStatus.APPLIED,
            CommandStatus.NO_CHANGE,
        }

    @property
    def changed(self) -> bool:
        return self.status is CommandStatus.APPLIED

    @classmethod
    def applied(
        cls,
        command: "Command",
        operation: str,
        message: str = "",
    ) -> "CommandResult":
        return cls(
            CommandStatus.APPLIED,
            type(command).__name__,
            operation,
            message,
        )

    @classmethod
    def no_change(
        cls,
        command: "Command",
        operation: str,
        message: str = "",
    ) -> "CommandResult":
        return cls(
            CommandStatus.NO_CHANGE,
            type(command).__name__,
            operation,
            message,
        )

    @classmethod
    def rejected(
        cls,
        command: "Command",
        operation: str,
        message: str,
    ) -> "CommandResult":
        return cls(
            CommandStatus.REJECTED,
            type(command).__name__,
            operation,
            message,
        )

    @classmethod
    def failed(
        cls,
        command: "Command",
        operation: str,
        error_type: str,
        message: str = "",
    ) -> "CommandResult":
        return cls(
            CommandStatus.FAILED,
            type(command).__name__,
            operation,
            message,
            error_type,
        )


class Command:
    def execute(self, scene: Any):
        raise NotImplementedError()

    def undo(self, scene: Any):
        raise NotImplementedError()

    def _snapshot_state(self) -> Any:
        """Capture mutable command state before one operation."""

        return copy.deepcopy(vars(self))

    def _restore_state(self, state: Any) -> None:
        """Restore mutable command state after a rejected operation."""

        vars(self).clear()
        vars(self).update(copy.deepcopy(state))


_STATE_ATTRIBUTES = (
    "objects",
    "layers",
    "groups",
    "collision_shapes",
    "selected_id",
)


def _freeze_state(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, dict):
        return tuple(
            sorted(
                (
                    _freeze_state(key),
                    _freeze_state(item),
                )
                for key, item in value.items()
            )
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_state(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze_state(item) for item in value))
    if hasattr(value, "__dict__"):
        return (
            type(value).__name__,
            _freeze_state(
                {
                    key: item
                    for key, item in vars(value).items()
                    if key not in {"cmd", "_listeners"}
                }
            ),
        )
    return repr(value)


@dataclass
class _SceneCheckpoint:
    values: Dict[str, Any]

    @classmethod
    def capture(cls, scene: Any) -> "_SceneCheckpoint":
        return cls(
            {
                name: copy.deepcopy(getattr(scene, name))
                for name in _STATE_ATTRIBUTES
                if hasattr(scene, name)
            }
        )

    def token(self) -> Any:
        return _freeze_state(self.values)

    def restore(self, scene: Any) -> None:
        for name, value in self.values.items():
            setattr(scene, name, copy.deepcopy(value))
        if hasattr(scene, "_notify"):
            scene._notify()


@dataclass
class _CommandCheckpoint:
    state: Any

    @classmethod
    def capture(cls, command: Command) -> "_CommandCheckpoint":
        return cls(command._snapshot_state())

    def restore(self, command: Command) -> None:
        command._restore_state(self.state)


def _restore_operation_state(
    *,
    command: Command,
    command_checkpoint: _CommandCheckpoint,
    scene: Any,
    scene_checkpoint: _SceneCheckpoint,
) -> None:
    command_checkpoint.restore(command)
    scene_checkpoint.restore(scene)


def _sanitize_operation_failure(
    command: Command,
    operation: str,
    exc: BaseException,
) -> CommandResult:
    error_type = type(exc).__name__
    logger.error(
        "Command %s %s failed (%s)",
        type(command).__name__,
        operation,
        error_type,
    )
    return CommandResult.failed(
        command,
        operation,
        error_type,
        "The operation failed and its state was restored.",
    )


def _run_command_operation(
    command: Command,
    operation: str,
    scene: Any,
) -> CommandResult:
    try:
        command_checkpoint = _CommandCheckpoint.capture(command)
    except Exception as exc:
        return _sanitize_operation_failure(command, operation, exc)

    scene_checkpoint = _SceneCheckpoint.capture(scene)
    before = scene_checkpoint.token()

    try:
        raw_result = getattr(command, operation)(scene)
    except Exception as exc:
        _restore_operation_state(
            command=command,
            command_checkpoint=command_checkpoint,
            scene=scene,
            scene_checkpoint=scene_checkpoint,
        )
        return _sanitize_operation_failure(command, operation, exc)

    after = _SceneCheckpoint.capture(scene).token()
    changed = after != before

    if isinstance(raw_result, CommandResult):
        if raw_result.status in {
            CommandStatus.REJECTED,
            CommandStatus.FAILED,
        }:
            _restore_operation_state(
                command=command,
                command_checkpoint=command_checkpoint,
                scene=scene,
                scene_checkpoint=scene_checkpoint,
            )
            return raw_result
        if raw_result.changed and not changed:
            command_checkpoint.restore(command)
            return CommandResult.no_change(
                command,
                operation,
                "The command reported a change, but the scene was unchanged.",
            )
        if not raw_result.changed and changed:
            _restore_operation_state(
                command=command,
                command_checkpoint=command_checkpoint,
                scene=scene,
                scene_checkpoint=scene_checkpoint,
            )
            logger.error(
                "Command %s %s returned an inconsistent result",
                type(command).__name__,
                operation,
            )
            return CommandResult.failed(
                command,
                operation,
                "CommandContractError",
                "The command result did not match the observed scene state.",
            )
        if not raw_result.changed:
            command_checkpoint.restore(command)
        return raw_result

    if changed:
        return CommandResult.applied(command, operation)

    command_checkpoint.restore(command)
    return CommandResult.no_change(
        command,
        operation,
        "The command completed without changing editable scene state.",
    )


class CompositeCommand(Command):
    """Execute multiple commands as one repeatable transaction."""

    def __init__(self, commands: List[Command]):
        self.commands = list(commands)
        self._executed: List[Command] = []

    def _snapshot_state(self) -> Any:
        return {
            "commands": list(self.commands),
            "executed": list(self._executed),
            "subcommands": [
                (command, command._snapshot_state()) for command in self.commands
            ],
        }

    def _restore_state(self, state: Any) -> None:
        self.commands = list(state["commands"])
        self._executed = list(state["executed"])
        for command, command_state in state["subcommands"]:
            command._restore_state(command_state)

    def _rollback_execute(self, scene: Any) -> Optional[CommandResult]:
        for executed in reversed(self._executed):
            result = _run_command_operation(executed, "undo", scene)
            if not result.changed:
                return CommandResult.failed(
                    self,
                    "execute",
                    result.error_type or "CompositeRollbackError",
                    "Composite execute rollback could not restore the scene.",
                )
        return None

    def execute(self, scene: Any) -> CommandResult:
        self._executed = []
        if not self.commands:
            return CommandResult.no_change(
                self,
                "execute",
                "The composite command has no subcommands.",
            )

        for command in self.commands:
            result = _run_command_operation(command, "execute", scene)
            if not result.changed:
                rollback_failure = self._rollback_execute(scene)
                if rollback_failure is not None:
                    return rollback_failure
                if result.status is CommandStatus.FAILED:
                    return CommandResult.failed(
                        self,
                        "execute",
                        result.error_type or "CompositeCommandError",
                        "A composite subcommand failed; applied changes were rolled back.",
                    )
                return CommandResult.rejected(
                    self,
                    "execute",
                    "A composite subcommand made no editable change; "
                    "applied changes were rolled back.",
                )
            self._executed.append(command)

        return CommandResult.applied(self, "execute")

    def undo(self, scene: Any) -> CommandResult:
        if not self._executed:
            return CommandResult.no_change(
                self,
                "undo",
                "The composite command has no executed subcommands.",
            )

        undone: List[Command] = []
        for command in reversed(self._executed):
            result = _run_command_operation(command, "undo", scene)
            if not result.changed:
                compensation_failed = False
                for reverted in reversed(undone):
                    compensation = _run_command_operation(
                        reverted,
                        "execute",
                        scene,
                    )
                    if not compensation.changed:
                        compensation_failed = True
                        break
                error_type = (
                    "CompositeCompensationError"
                    if compensation_failed
                    else result.error_type or "CompositeUndoError"
                )
                return CommandResult.failed(
                    self,
                    "undo",
                    error_type,
                    "Composite undo failed; the pre-undo state was restored "
                    "when compensation succeeded.",
                )
            undone.append(command)

        return CommandResult.applied(self, "undo")


class CommandManager:
    """Manage command history with explicit, observable outcomes."""

    def __init__(self, max_history: int = 50):
        if max_history < 1:
            raise ValueError("max_history must be at least 1")
        self.max_history = int(max_history)
        self._undo: List[Command] = []
        self._redo: List[Command] = []
        self._listeners: List[Callable[[], None]] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    @property
    def undo_count(self) -> int:
        return len(self._undo)

    @property
    def redo_count(self) -> int:
        return len(self._redo)

    def subscribe(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_history_changed(self) -> None:
        for callback in list(self._listeners):
            try:
                callback()
            except Exception as exc:
                logger.warning(
                    "Command history listener failed (%s)",
                    type(exc).__name__,
                )

    def clear(self) -> None:
        had_history = bool(self._undo or self._redo)
        self._undo.clear()
        self._redo.clear()
        if had_history:
            self._notify_history_changed()

    def execute(self, command: Command, scene: Any) -> CommandResult:
        result = _run_command_operation(command, "execute", scene)
        if not result.changed:
            return result

        self._undo.append(command)
        if len(self._undo) > self.max_history:
            del self._undo[: len(self._undo) - self.max_history]
        self._redo.clear()
        self._notify_history_changed()
        return result

    def undo(self, scene: Any) -> CommandResult:
        if not self._undo:
            return CommandResult.no_change(
                _EmptyHistoryCommand(),
                "undo",
                "Undo history is empty.",
            )

        command = self._undo[-1]
        result = _run_command_operation(command, "undo", scene)
        if not result.changed:
            return result

        self._undo.pop()
        self._redo.append(command)
        self._notify_history_changed()
        return result

    def redo(self, scene: Any) -> CommandResult:
        if not self._redo:
            return CommandResult.no_change(
                _EmptyHistoryCommand(),
                "redo",
                "Redo history is empty.",
            )

        command = self._redo[-1]
        result = _run_command_operation(command, "execute", scene)
        if not result.changed:
            return result

        self._redo.pop()
        self._undo.append(command)
        if len(self._undo) > self.max_history:
            del self._undo[: len(self._undo) - self.max_history]
        self._notify_history_changed()
        return result


class _EmptyHistoryCommand(Command):
    def execute(self, scene: Any):
        return None

    def undo(self, scene: Any):
        return None


class RemoveLayerCommand(Command):
    def __init__(self, layer_id: str):
        self.layer_id = layer_id
        self._backup_layer: Optional[Dict[str, Any]] = None
        self._backup_assignments: Optional[Dict[str, str]] = None

    def execute(self, scene: Any):
        layer = next(
            (layer for layer in scene.layers if layer.id == self.layer_id),
            None,
        )
        if layer is None:
            return
        self._backup_layer = {
            "id": layer.id,
            "name": layer.name,
            "visible": layer.visible,
            "locked": layer.locked,
        }
        self._backup_assignments = {
            oid: obj.layer_id
            for oid, obj in scene.objects.items()
            if obj.layer_id == self.layer_id
        }
        scene.remove_layer(self.layer_id)

    def undo(self, scene: Any):
        if self._backup_layer is None:
            return
        from src.models.scene import Layer

        layer = Layer(
            id=self._backup_layer["id"],
            name=self._backup_layer["name"],
            visible=self._backup_layer["visible"],
            locked=self._backup_layer["locked"],
        )
        scene.layers.append(layer)
        if self._backup_assignments:
            for oid, old in self._backup_assignments.items():
                if oid in scene.objects:
                    scene.objects[oid].layer_id = layer.id


class CreateLayerCommand(Command):
    def __init__(self, name: str):
        self.name = name
        self.layer_id: Optional[str] = None

    def execute(self, scene: Any):
        layer = scene.create_layer(self.name)
        self.layer_id = layer.id

    def undo(self, scene: Any):
        if self.layer_id:
            scene.remove_layer(self.layer_id)


class MoveLayerCommand(Command):
    def __init__(self, layer_id: str, new_index: int):
        self.layer_id = layer_id
        self.new_index = new_index
        self._old_index: Optional[int] = None

    def execute(self, scene: Any):
        ids = [layer.id for layer in scene.layers]
        if self.layer_id in ids:
            self._old_index = ids.index(self.layer_id)
        scene.move_layer(self.layer_id, self.new_index)

    def undo(self, scene: Any):
        if self._old_index is not None:
            scene.move_layer(self.layer_id, self._old_index)


class ToggleLayerVisibilityCommand(Command):
    def __init__(self, layer_id: str):
        self.layer_id = layer_id
        self._old: Optional[bool] = None

    def execute(self, scene: Any):
        for layer in scene.layers:
            if layer.id == self.layer_id:
                self._old = layer.visible
                layer.visible = not layer.visible
                return

    def undo(self, scene: Any):
        for layer in scene.layers:
            if layer.id == self.layer_id and self._old is not None:
                layer.visible = self._old


class ToggleLayerLockCommand(Command):
    def __init__(self, layer_id: str):
        self.layer_id = layer_id
        self._old: Optional[bool] = None

    def execute(self, scene: Any):
        for layer in scene.layers:
            if layer.id == self.layer_id:
                self._old = layer.locked
                layer.locked = not layer.locked
                return

    def undo(self, scene: Any):
        for layer in scene.layers:
            if layer.id == self.layer_id and self._old is not None:
                layer.locked = self._old


class HandleMoveCommand(Command):
    def __init__(
        self,
        object_id: str,
        seg_index: int,
        handle_index: int,
        old_pos: Tuple[float, float],
        new_pos: Tuple[float, float],
    ):
        self.object_id = object_id
        self.seg_index = seg_index
        self.handle_index = handle_index
        self.old_pos = tuple(old_pos)
        self.new_pos = tuple(new_pos)

    def execute(self, scene: Any):
        obj = scene.objects.get(self.object_id)
        if not obj or not hasattr(obj, "beziers"):
            return
        seg = list(obj.beziers[self.seg_index])
        seg[self.handle_index] = tuple(self.new_pos)
        obj.beziers[self.seg_index] = tuple(seg)
        scene.set_object_beziers(self.object_id, obj.beziers)

    def undo(self, scene: Any):
        obj = scene.objects.get(self.object_id)
        if not obj or not hasattr(obj, "beziers"):
            return
        seg = list(obj.beziers[self.seg_index])
        seg[self.handle_index] = tuple(self.old_pos)
        obj.beziers[self.seg_index] = tuple(seg)
        scene.set_object_beziers(self.object_id, obj.beziers)


class UpdatePolygonCommand(Command):
    # Replace one polygon and restore exact prior collision state on undo.
    def __init__(
        self,
        object_id: str,
        old_polygon: List[Tuple[int, int]],
        new_polygon: List[Tuple[int, int]],
    ):
        self.object_id = object_id
        self.old_polygon = [tuple(point) for point in old_polygon]
        self.new_polygon = [tuple(point) for point in new_polygon]
        self._had_collision = False
        self._old_collision: Optional[List[Tuple[float, float]]] = None

    def execute(self, scene: Any):
        obj = scene.objects.get(self.object_id)
        if obj is None:
            return CommandResult.rejected(
                self, "execute", "The object no longer exists."
            )
        if [tuple(point) for point in obj.polygon] != self.old_polygon:
            return CommandResult.rejected(
                self,
                "execute",
                "The object changed before this edit could be applied.",
            )
        if self.old_polygon == self.new_polygon:
            return CommandResult.no_change(
                self,
                "execute",
                "The polygon is already in the requested state.",
            )

        self._had_collision = self.object_id in scene.collision_shapes
        self._old_collision = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if self._had_collision
            else None
        )
        scene.update_polygon(self.object_id, self.new_polygon)

    def undo(self, scene: Any):
        obj = scene.objects.get(self.object_id)
        if obj is None:
            return CommandResult.rejected(self, "undo", "The object no longer exists.")
        if self._had_collision and self._old_collision is None:
            return CommandResult.failed(
                self,
                "undo",
                "CollisionBackupError",
                "The previous collision shape is unavailable.",
            )

        obj.polygon = copy.deepcopy(self.old_polygon)
        if self._had_collision:
            scene.collision_shapes[self.object_id] = copy.deepcopy(self._old_collision)
        else:
            scene.collision_shapes.pop(self.object_id, None)
        scene._notify()


class ExpandContractCommand(UpdatePolygonCommand):
    # Backward-compatible name for polygon replacement.
    pass


class CreateGroupCommand(Command):
    def __init__(self, name: str):
        self.name = name
        self.group_id: Optional[str] = None

    def execute(self, scene: Any):
        g = scene.create_group(self.name)
        self.group_id = g.id

    def undo(self, scene: Any):
        if self.group_id:
            scene.remove_group(self.group_id)


class RemoveGroupCommand(Command):
    def __init__(self, group_id: str):
        self.group_id = group_id
        self._backup: Optional[Dict[str, Any]] = None

    def execute(self, scene: Any):
        g = next(
            (x for x in getattr(scene, "groups", []) if x.id == self.group_id),
            None,
        )
        if g is None:
            return
        self._backup = {
            "id": g.id,
            "name": g.name,
            "visible": g.visible,
            "locked": g.locked,
            "members": list(g.members),
        }
        scene.remove_group(self.group_id)

    def undo(self, scene: Any):
        if self._backup:
            try:
                from src.models.scene import Group

                g = Group(
                    id=self._backup["id"],
                    name=self._backup["name"],
                    visible=self._backup["visible"],
                    locked=self._backup["locked"],
                )
                g.members = list(self._backup["members"])
                if not hasattr(scene, "groups"):
                    scene.groups = []
                scene.groups.append(g)
            except Exception:
                pass


class AddToGroupCommand(Command):
    def __init__(self, group_id: str, object_id: str):
        self.group_id = group_id
        self.object_id = object_id
        self._added = False

    def execute(self, scene: Any):
        scene.add_object_to_group(self.group_id, self.object_id)
        self._added = True

    def undo(self, scene: Any):
        if self._added:
            scene.remove_object_from_group(self.group_id, self.object_id)


class RemoveFromGroupCommand(Command):
    def __init__(self, group_id: str, object_id: str):
        self.group_id = group_id
        self.object_id = object_id
        self._removed = False

    def execute(self, scene: Any):
        scene.remove_object_from_group(self.group_id, self.object_id)
        self._removed = True

    def undo(self, scene: Any):
        if self._removed:
            scene.add_object_to_group(self.group_id, self.object_id)


class AddPolygonCommand(Command):
    def __init__(self, polygon: List[Tuple[int, int]], layer_id: Optional[str] = None):
        self.polygon = [tuple(p) for p in polygon]
        self.layer_id = layer_id
        self.object_id: Optional[str] = None

    def execute(self, scene: Any):
        self.object_id = scene.add_polygon(self.polygon, self.layer_id)

    def undo(self, scene: Any):
        if self.object_id and self.object_id in scene.objects:
            scene.remove_object(self.object_id)


class CreateObjectCommand(Command):
    def __init__(
        self,
        polygon: List[Tuple[int, int]],
        layer_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ):
        self.polygon = [tuple(p) for p in polygon]
        self.layer_id = layer_id
        self.object_id = object_id

    def execute(self, scene: Any):
        if self.object_id is None:
            self.object_id = scene.add_polygon(self.polygon, self.layer_id)
        else:
            if self.object_id in scene.objects:
                scene.update_polygon(self.object_id, self.polygon)
            else:
                scene.add_object(
                    self.object_id,
                    self.polygon,
                    self.layer_id,
                    select=True,
                )

    def undo(self, scene: Any):
        if self.object_id and self.object_id in scene.objects:
            scene.remove_object(self.object_id)


class MoveGroupCommand(Command):
    def __init__(self, group_id: str, new_index: int):
        self.group_id = group_id
        self.new_index = new_index
        self._old_index: Optional[int] = None

    def execute(self, scene: Any):
        ids = [g.id for g in getattr(scene, "groups", [])]
        if self.group_id in ids:
            self._old_index = ids.index(self.group_id)
        scene.move_group(self.group_id, self.new_index)

    def undo(self, scene: Any):
        if self._old_index is not None:
            scene.move_group(self.group_id, self._old_index)


class ToggleCollisionCommand(Command):
    # Toggle collision and restore the exact previous shape on undo.
    def __init__(self, object_id: str):
        self.object_id = object_id
        self._was_enabled = False
        self._old_shape: Optional[List[Tuple[float, float]]] = None

    def execute(self, scene: Any):
        if self.object_id not in scene.objects:
            return CommandResult.rejected(
                self, "execute", "The object no longer exists."
            )

        self._was_enabled = scene.has_collision(self.object_id)
        self._old_shape = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if self._was_enabled
            else None
        )
        scene.set_object_collision(
            self.object_id,
            not self._was_enabled,
        )

    def undo(self, scene: Any):
        if self.object_id not in scene.objects:
            return CommandResult.rejected(self, "undo", "The object no longer exists.")

        if self._was_enabled:
            if self._old_shape is None:
                return CommandResult.failed(
                    self,
                    "undo",
                    "CollisionBackupError",
                    "The previous collision shape is unavailable.",
                )
            scene.collision_shapes[self.object_id] = copy.deepcopy(self._old_shape)
            scene._notify()
        else:
            scene.set_object_collision(self.object_id, False)


class ClearSceneCommand(Command):
    # Clear editable collections as one reversible operation.
    def __init__(self):
        self._backup_objects: Dict[str, Any] = {}
        self._backup_groups: List[Any] = []
        self._backup_collisions: Dict[str, List[Tuple[float, float]]] = {}
        self._backup_selected_id: Optional[str] = None

    def execute(self, scene: Any):
        if not (
            scene.objects
            or scene.groups
            or scene.collision_shapes
            or scene.selected_id is not None
        ):
            return CommandResult.no_change(
                self, "execute", "The scene is already empty."
            )

        self._backup_objects = copy.deepcopy(scene.objects)
        self._backup_groups = copy.deepcopy(scene.groups)
        self._backup_collisions = copy.deepcopy(scene.collision_shapes)
        self._backup_selected_id = scene.selected_id
        scene.clear()

    def undo(self, scene: Any):
        scene.objects = copy.deepcopy(self._backup_objects)
        scene.groups = copy.deepcopy(self._backup_groups)
        scene.collision_shapes = copy.deepcopy(self._backup_collisions)
        scene.selected_id = self._backup_selected_id
        scene._notify()


# --- NOVO COMANDO PARA CORRIGIR ERROS DE IMPORTAÇÃO ---


class RenameObjectCommand(Command):
    # Rename through the scene service.
    def __init__(self, old_id: str, new_id: str):
        self.old_id = old_id
        self.new_id = new_id.strip()

    def execute(self, scene: Any):
        if not self.new_id:
            return CommandResult.rejected(
                self,
                "execute",
                "The new object id must not be empty.",
            )
        if self.old_id == self.new_id:
            return CommandResult.no_change(
                self,
                "execute",
                "The object already has this id.",
            )
        if self.old_id not in scene.objects:
            return CommandResult.rejected(
                self, "execute", "The object no longer exists."
            )
        if self.new_id in scene.objects:
            return CommandResult.rejected(
                self,
                "execute",
                "Another object already uses this id.",
            )
        scene.rename_object(self.old_id, self.new_id)

    def undo(self, scene: Any):
        scene.rename_object(self.new_id, self.old_id)


class DeleteObjectCommand(Command):
    # Delete and restore object-owned relationships.
    def __init__(self, object_id: str):
        self.object_id = object_id
        self._backup_obj: Optional[Any] = None
        self._backup_object_index: Optional[int] = None
        self._backup_group_members: Optional[Dict[str, List[str]]] = None
        self._backup_selected_id: Optional[str] = None
        self._had_collision = False
        self._backup_collision: Optional[List[Tuple[float, float]]] = None

    def execute(self, scene: Any):
        if self.object_id not in scene.objects:
            return CommandResult.rejected(
                self, "execute", "The object no longer exists."
            )

        self._backup_object_index = list(scene.objects).index(self.object_id)
        self._backup_obj = copy.deepcopy(scene.objects[self.object_id])
        self._backup_group_members = {
            group.id: list(group.members) for group in scene.groups
        }
        self._backup_selected_id = scene.selected_id
        self._had_collision = self.object_id in scene.collision_shapes
        self._backup_collision = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if self._had_collision
            else None
        )
        scene.remove_object(self.object_id)

    def undo(self, scene: Any):
        if (
            self._backup_obj is None
            or self._backup_object_index is None
            or self._backup_group_members is None
        ):
            return CommandResult.rejected(
                self,
                "undo",
                "The deleted object backup is unavailable.",
            )
        if self.object_id in scene.objects:
            return CommandResult.rejected(
                self,
                "undo",
                "The object id is already in use.",
            )

        items = list(scene.objects.items())
        insert_at = min(self._backup_object_index, len(items))
        items.insert(
            insert_at,
            (
                self.object_id,
                copy.deepcopy(self._backup_obj),
            ),
        )
        scene.objects = dict(items)

        if self._had_collision:
            if self._backup_collision is None:
                return CommandResult.failed(
                    self,
                    "undo",
                    "CollisionBackupError",
                    "The collision backup is unavailable.",
                )
            scene.collision_shapes[self.object_id] = copy.deepcopy(
                self._backup_collision
            )
        else:
            scene.collision_shapes.pop(self.object_id, None)

        groups_by_id = {group.id: group for group in scene.groups}
        for group_id, members in self._backup_group_members.items():
            group = groups_by_id.get(group_id)
            if group is None:
                return CommandResult.failed(
                    self,
                    "undo",
                    "GroupRelationshipError",
                    "A required group is missing.",
                )
            group.members = list(members)

        scene.selected_id = self._backup_selected_id
        scene._notify()
