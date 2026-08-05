"""Implementation of :mod:`src.core.commands`.

Implementation preserved in the single ``src`` source tree.
"""

import copy
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.bezier_geometry import (
    BezierSegments,
    canonical_point,
    canonicalize_beziers,
    replace_handle,
    sample_beziers_to_polygon,
)
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


def _layer_index(scene: Any, layer_id: str) -> Optional[int]:
    for index, layer in enumerate(scene.layers):
        if layer.id == layer_id:
            return index
    return None


def _group_index(scene: Any, group_id: str) -> Optional[int]:
    for index, group in enumerate(getattr(scene, "groups", [])):
        if group.id == group_id:
            return index
    return None


class RemoveLayerCommand(Command):
    """Remove one layer and restore its exact index and assignments."""

    def __init__(self, layer_id: str):
        self.layer_id = str(layer_id)
        self._backup_layer: Optional[Dict[str, Any]] = None
        self._backup_assignments: Optional[Dict[str, str]] = None
        self._backup_index: Optional[int] = None

    def execute(self, scene: Any):
        if self.layer_id == "layer_default":
            return CommandResult.rejected(
                self,
                "execute",
                "The default layer cannot be removed.",
            )
        index = _layer_index(scene, self.layer_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer no longer exists.",
            )
        layer = scene.layers[index]
        self._backup_index = index
        self._backup_layer = {
            "id": layer.id,
            "name": layer.name,
            "visible": bool(layer.visible),
            "locked": bool(layer.locked),
        }
        self._backup_assignments = {
            object_id: obj.layer_id
            for object_id, obj in scene.objects.items()
            if obj.layer_id == self.layer_id
        }
        scene.remove_layer(self.layer_id)

    def undo(self, scene: Any):
        if (
            self._backup_layer is None
            or self._backup_assignments is None
            or self._backup_index is None
        ):
            return CommandResult.rejected(
                self,
                "undo",
                "The removed layer backup is unavailable.",
            )
        if _layer_index(scene, self.layer_id) is not None:
            return CommandResult.rejected(
                self,
                "undo",
                "The layer id is already in use.",
            )
        if any(
            object_id not in scene.objects for object_id in self._backup_assignments
        ):
            return CommandResult.failed(
                self,
                "undo",
                "LayerRelationshipError",
                "An object required by the removed layer is missing.",
            )

        from src.models.scene import Layer

        layer = Layer(
            id=self._backup_layer["id"],
            name=self._backup_layer["name"],
            visible=self._backup_layer["visible"],
            locked=self._backup_layer["locked"],
        )
        insert_at = min(self._backup_index, len(scene.layers))
        scene.layers.insert(insert_at, layer)
        for object_id, layer_id in self._backup_assignments.items():
            scene.objects[object_id].layer_id = layer_id
        scene._notify()


class CreateLayerCommand(Command):
    """Create one layer with stable identity across Undo and Redo."""

    def __init__(self, name: str):
        self.name = str(name).strip()
        self.layer_id: Optional[str] = None
        self._index: Optional[int] = None

    def execute(self, scene: Any):
        if not self.name:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer name must not be empty.",
            )
        if self.layer_id is None:
            layer = scene.create_layer(self.name)
            self.layer_id = layer.id
            self._index = len(scene.layers) - 1
            return None
        if _layer_index(scene, self.layer_id) is not None:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer id is already in use.",
            )

        from src.models.scene import Layer

        insert_at = min(
            self._index if self._index is not None else len(scene.layers),
            len(scene.layers),
        )
        scene.layers.insert(
            insert_at,
            Layer(id=self.layer_id, name=self.name),
        )
        scene._notify()

    def undo(self, scene: Any):
        if self.layer_id is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The created layer id is unavailable.",
            )
        index = _layer_index(scene, self.layer_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The created layer no longer exists.",
            )
        self._index = index
        scene.remove_layer(self.layer_id)


class MoveLayerCommand(Command):
    """Move one layer and restore its exact previous index."""

    def __init__(self, layer_id: str, new_index: int):
        self.layer_id = str(layer_id)
        self.new_index = int(new_index)
        self._old_index: Optional[int] = None

    def execute(self, scene: Any):
        old_index = _layer_index(scene, self.layer_id)
        if old_index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer no longer exists.",
            )
        target = max(0, min(self.new_index, len(scene.layers) - 1))
        if target == old_index:
            return CommandResult.no_change(
                self,
                "execute",
                "The layer is already at the requested index.",
            )
        self._old_index = old_index
        scene.move_layer(self.layer_id, target)

    def undo(self, scene: Any):
        if self._old_index is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The previous layer index is unavailable.",
            )
        if _layer_index(scene, self.layer_id) is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The moved layer no longer exists.",
            )
        scene.move_layer(self.layer_id, self._old_index)


class ToggleLayerVisibilityCommand(Command):
    """Toggle layer visibility with exact state preconditions."""

    def __init__(self, layer_id: str):
        self.layer_id = str(layer_id)
        self._old: Optional[bool] = None
        self._new: Optional[bool] = None

    def execute(self, scene: Any):
        index = _layer_index(scene, self.layer_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer no longer exists.",
            )
        current = bool(scene.layers[index].visible)
        if self._old is None:
            self._old = current
            self._new = not current
        elif current != self._old:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer visibility changed before Redo.",
            )
        scene.set_layer_visibility(self.layer_id, bool(self._new))

    def undo(self, scene: Any):
        index = _layer_index(scene, self.layer_id)
        if index is None or self._old is None or self._new is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The previous layer visibility is unavailable.",
            )
        if bool(scene.layers[index].visible) != self._new:
            return CommandResult.rejected(
                self,
                "undo",
                "The layer visibility changed before Undo.",
            )
        scene.set_layer_visibility(self.layer_id, self._old)


class ToggleLayerLockCommand(Command):
    """Toggle layer lock with exact state preconditions."""

    def __init__(self, layer_id: str):
        self.layer_id = str(layer_id)
        self._old: Optional[bool] = None
        self._new: Optional[bool] = None

    def execute(self, scene: Any):
        index = _layer_index(scene, self.layer_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer no longer exists.",
            )
        current = bool(scene.layers[index].locked)
        if self._old is None:
            self._old = current
            self._new = not current
        elif current != self._old:
            return CommandResult.rejected(
                self,
                "execute",
                "The layer lock changed before Redo.",
            )
        scene.set_layer_lock(self.layer_id, bool(self._new))

    def undo(self, scene: Any):
        index = _layer_index(scene, self.layer_id)
        if index is None or self._old is None or self._new is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The previous layer lock is unavailable.",
            )
        if bool(scene.layers[index].locked) != self._new:
            return CommandResult.rejected(
                self,
                "undo",
                "The layer lock changed before Undo.",
            )
        scene.set_layer_lock(self.layer_id, self._old)


class HandleMoveCommand(Command):
    """Move one cubic handle while preserving sampled and collision state."""

    def __init__(
        self,
        object_id: str,
        seg_index: int,
        handle_index: int,
        old_pos: Tuple[float, float],
        new_pos: Tuple[float, float],
        *,
        steps_per_segment: int = 20,
    ):
        self.object_id = str(object_id)
        self.seg_index = seg_index
        self.handle_index = handle_index
        self.old_pos = tuple(old_pos)
        self.new_pos = tuple(new_pos)
        self.steps_per_segment = steps_per_segment
        self._old_beziers: Optional[BezierSegments] = None
        self._new_beziers: Optional[BezierSegments] = None
        self._old_polygon: Optional[List[Tuple[int, int]]] = None
        self._new_polygon: Optional[List[Tuple[int, int]]] = None
        self._had_collision: Optional[bool] = None
        self._collision_snapshot: Optional[List[Tuple[float, float]]] = None
        self._executed_once = False

    def _validate_request(self) -> Optional[CommandResult]:
        try:
            old_pos = canonical_point(self.old_pos, label="old handle position")
            new_pos = canonical_point(self.new_pos, label="new handle position")
        except ValueError as exc:
            return CommandResult.rejected(self, "execute", str(exc))
        if isinstance(self.seg_index, bool) or not isinstance(self.seg_index, int):
            return CommandResult.rejected(
                self, "execute", "segment_index must be an integer."
            )
        if self.handle_index not in {1, 2}:
            return CommandResult.rejected(
                self,
                "execute",
                "handle_index must identify control point 1 or 2.",
            )
        if isinstance(self.steps_per_segment, bool) or not isinstance(
            self.steps_per_segment, int
        ):
            return CommandResult.rejected(
                self, "execute", "steps_per_segment must be an integer."
            )
        if self.steps_per_segment < 1:
            return CommandResult.rejected(
                self, "execute", "steps_per_segment must be at least 1."
            )
        self.old_pos = old_pos
        self.new_pos = new_pos
        return None

    def _current_state(self, scene: Any) -> Optional[Tuple[Any, ...]]:
        obj = scene.objects.get(self.object_id)
        if obj is None:
            return None
        try:
            beziers = canonicalize_beziers(obj.beziers)
        except (TypeError, ValueError):
            return None
        has_collision = self.object_id in scene.collision_shapes
        collision = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if has_collision
            else None
        )
        return (
            beziers,
            copy.deepcopy(obj.polygon),
            has_collision,
            collision,
        )

    def _old_state(self) -> Optional[Tuple[Any, ...]]:
        if (
            self._old_beziers is None
            or self._old_polygon is None
            or self._had_collision is None
        ):
            return None
        return (
            copy.deepcopy(self._old_beziers),
            copy.deepcopy(self._old_polygon),
            self._had_collision,
            copy.deepcopy(self._collision_snapshot),
        )

    def _new_state(self) -> Optional[Tuple[Any, ...]]:
        if (
            self._new_beziers is None
            or self._new_polygon is None
            or self._had_collision is None
        ):
            return None
        return (
            copy.deepcopy(self._new_beziers),
            copy.deepcopy(self._new_polygon),
            self._had_collision,
            copy.deepcopy(self._collision_snapshot),
        )

    def _apply(
        self,
        scene: Any,
        beziers: BezierSegments,
        polygon: List[Tuple[int, int]],
    ) -> None:
        obj = scene.objects[self.object_id]
        obj.beziers = copy.deepcopy(beziers)
        obj.polygon = copy.deepcopy(polygon)
        if self._had_collision:
            scene.collision_shapes[self.object_id] = copy.deepcopy(
                self._collision_snapshot
            )
        else:
            scene.collision_shapes.pop(self.object_id, None)
        scene._notify()

    def execute(self, scene: Any):
        validation = self._validate_request()
        if validation is not None:
            return validation
        obj = scene.objects.get(self.object_id)
        if obj is None:
            return CommandResult.rejected(
                self, "execute", "The object no longer exists."
            )
        if getattr(obj, "beziers", None) is None:
            return CommandResult.rejected(
                self, "execute", "The object has no Bézier geometry."
            )

        if not self._executed_once:
            try:
                old_beziers = canonicalize_beziers(obj.beziers)
            except ValueError as exc:
                return CommandResult.rejected(self, "execute", str(exc))
            if self.seg_index < 0 or self.seg_index >= len(old_beziers):
                return CommandResult.rejected(
                    self, "execute", "segment_index is outside the Bézier geometry."
                )
            if old_beziers[self.seg_index][self.handle_index] != self.old_pos:
                return CommandResult.rejected(
                    self,
                    "execute",
                    "The handle changed before this edit could be applied.",
                )
            if self.old_pos == self.new_pos:
                return CommandResult.no_change(
                    self, "execute", "The handle is already at the requested position."
                )
            try:
                new_beziers = replace_handle(
                    old_beziers,
                    self.seg_index,
                    self.handle_index,
                    self.new_pos,
                )
                new_polygon = sample_beziers_to_polygon(
                    new_beziers,
                    steps_per_segment=self.steps_per_segment,
                )
            except ValueError as exc:
                return CommandResult.rejected(self, "execute", str(exc))

            self._old_beziers = copy.deepcopy(old_beziers)
            self._new_beziers = copy.deepcopy(new_beziers)
            self._old_polygon = copy.deepcopy(obj.polygon)
            self._new_polygon = copy.deepcopy(new_polygon)
            self._had_collision = self.object_id in scene.collision_shapes
            self._collision_snapshot = (
                copy.deepcopy(scene.collision_shapes[self.object_id])
                if self._had_collision
                else None
            )
            self._executed_once = True
        elif self._current_state(scene) != self._old_state():
            return CommandResult.rejected(
                self,
                "execute",
                "Bézier, polygon or collision state changed before Redo.",
            )

        if self._new_beziers is None or self._new_polygon is None:
            return CommandResult.failed(
                self,
                "execute",
                "BezierBackupError",
                "The target Bézier state is unavailable.",
            )
        self._apply(scene, self._new_beziers, self._new_polygon)
        return None

    def undo(self, scene: Any):
        if self._old_state() is None or self._new_state() is None:
            return CommandResult.rejected(
                self, "undo", "The previous Bézier state is unavailable."
            )
        if self._current_state(scene) != self._new_state():
            return CommandResult.rejected(
                self, "undo", "Bézier, polygon or collision state changed before Undo."
            )
        if self._old_beziers is None or self._old_polygon is None:
            return CommandResult.failed(
                self,
                "undo",
                "BezierBackupError",
                "The previous Bézier state is unavailable.",
            )
        self._apply(scene, self._old_beziers, self._old_polygon)
        return None


class UpdatePolygonCommand(Command):
    """Replace one polygon with exact stale-state and collision checks."""

    def __init__(
        self,
        object_id: str,
        old_polygon: List[Tuple[int, int]],
        new_polygon: List[Tuple[int, int]],
    ):
        self.object_id = str(object_id)
        self.old_polygon: List[Tuple[int, int]] = [
            (point[0], point[1]) for point in old_polygon
        ]
        self.new_polygon: List[Tuple[int, int]] = [
            (point[0], point[1]) for point in new_polygon
        ]
        self._had_collision: Optional[bool] = None
        self._old_collision: Optional[List[Tuple[float, float]]] = None
        self._new_collision: Optional[List[Tuple[float, float]]] = None
        self._executed_once = False

    def _state(self, scene: Any) -> Optional[Tuple[Any, ...]]:
        obj = scene.objects.get(self.object_id)
        if obj is None:
            return None
        has_collision = self.object_id in scene.collision_shapes
        collision = (
            copy.deepcopy(scene.collision_shapes[self.object_id])
            if has_collision
            else None
        )
        return (
            [tuple(point) for point in obj.polygon],
            has_collision,
            collision,
        )

    def _old_state(self) -> Optional[Tuple[Any, ...]]:
        if self._had_collision is None:
            return None
        return (
            copy.deepcopy(self.old_polygon),
            self._had_collision,
            copy.deepcopy(self._old_collision),
        )

    def _new_state(self) -> Optional[Tuple[Any, ...]]:
        if self._had_collision is None:
            return None
        return (
            copy.deepcopy(self.new_polygon),
            self._had_collision,
            copy.deepcopy(self._new_collision),
        )

    def _apply(
        self,
        scene: Any,
        polygon: List[Tuple[int, int]],
        collision: Optional[List[Tuple[float, float]]],
    ) -> None:
        obj = scene.objects[self.object_id]
        obj.polygon = copy.deepcopy(polygon)
        if self._had_collision:
            scene.collision_shapes[self.object_id] = copy.deepcopy(collision)
        else:
            scene.collision_shapes.pop(self.object_id, None)
        scene._notify()

    def execute(self, scene: Any):
        current = self._state(scene)
        if current is None:
            return CommandResult.rejected(
                self, "execute", "The object no longer exists."
            )
        if self.old_polygon == self.new_polygon:
            return CommandResult.no_change(
                self, "execute", "The polygon is already in the requested state."
            )

        if not self._executed_once:
            if current[0] != self.old_polygon:
                return CommandResult.rejected(
                    self,
                    "execute",
                    "The object changed before this edit could be applied.",
                )
            self._had_collision = bool(current[1])
            self._old_collision = copy.deepcopy(current[2])
            self._new_collision = (
                [(float(x), float(y)) for x, y in self.new_polygon]
                if self._had_collision
                else None
            )
            self._executed_once = True
        elif current != self._old_state():
            return CommandResult.rejected(
                self, "execute", "Polygon or collision state changed before Redo."
            )

        self._apply(scene, self.new_polygon, self._new_collision)
        return None

    def undo(self, scene: Any):
        if self._old_state() is None or self._new_state() is None:
            return CommandResult.rejected(
                self, "undo", "The previous polygon state is unavailable."
            )
        if self._state(scene) != self._new_state():
            return CommandResult.rejected(
                self, "undo", "Polygon or collision state changed before Undo."
            )
        if self._had_collision and self._old_collision is None:
            return CommandResult.failed(
                self,
                "undo",
                "CollisionBackupError",
                "The previous collision shape is unavailable.",
            )
        self._apply(scene, self.old_polygon, self._old_collision)
        return None


class UpdateObjectGeometryCommand(Command):
    """Replace polygon and collision geometry as one exact transaction."""

    def __init__(
        self,
        object_id: str,
        old_polygon: List[Tuple[float, float]],
        new_polygon: List[Tuple[float, float]],
        *,
        old_has_collision: bool,
        old_collision: Optional[List[Tuple[float, float]]],
        new_has_collision: bool,
        new_collision: Optional[List[Tuple[float, float]]],
    ):
        self.object_id = str(object_id)
        self.old_polygon: List[Tuple[float, float]] = [
            (point[0], point[1]) for point in old_polygon
        ]
        self.new_polygon: List[Tuple[float, float]] = [
            (point[0], point[1]) for point in new_polygon
        ]
        self.old_has_collision = bool(old_has_collision)
        self.old_collision = copy.deepcopy(old_collision) if old_has_collision else None
        self.new_has_collision = bool(new_has_collision)
        self.new_collision = copy.deepcopy(new_collision) if new_has_collision else None

    @staticmethod
    def _geometry(
        scene: Any,
        object_id: str,
    ) -> Optional[
        Tuple[
            List[Tuple[float, float]],
            bool,
            Optional[List[Tuple[float, float]]],
        ]
    ]:
        obj = scene.objects.get(object_id)
        if obj is None:
            return None
        has_collision = object_id in scene.collision_shapes
        collision = (
            copy.deepcopy(scene.collision_shapes[object_id]) if has_collision else None
        )
        return (
            [(point[0], point[1]) for point in obj.polygon],
            has_collision,
            collision,
        )

    @staticmethod
    def _apply(
        scene: Any,
        object_id: str,
        polygon: List[Tuple[float, float]],
        has_collision: bool,
        collision: Optional[List[Tuple[float, float]]],
    ) -> CommandResult | None:
        obj = scene.objects.get(object_id)
        if obj is None:
            return None
        if has_collision and collision is None:
            return CommandResult.failed(
                UpdateObjectGeometryCommand(
                    object_id,
                    polygon,
                    polygon,
                    old_has_collision=False,
                    old_collision=None,
                    new_has_collision=False,
                    new_collision=None,
                ),
                "execute",
                "CollisionGeometryUnavailable",
                "Collision geometry is required for this state.",
            )

        obj.polygon = copy.deepcopy(polygon)
        if has_collision:
            scene.collision_shapes[object_id] = copy.deepcopy(collision)
        else:
            scene.collision_shapes.pop(object_id, None)
        scene._notify()
        return None

    def _expected_old_geometry(
        self,
    ) -> Tuple[
        List[Tuple[float, float]],
        bool,
        Optional[List[Tuple[float, float]]],
    ]:
        return (
            copy.deepcopy(self.old_polygon),
            self.old_has_collision,
            copy.deepcopy(self.old_collision),
        )

    def _expected_new_geometry(
        self,
    ) -> Tuple[
        List[Tuple[float, float]],
        bool,
        Optional[List[Tuple[float, float]]],
    ]:
        return (
            copy.deepcopy(self.new_polygon),
            self.new_has_collision,
            copy.deepcopy(self.new_collision),
        )

    def execute(self, scene: Any):
        current = self._geometry(scene, self.object_id)
        if current is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The object no longer exists.",
            )
        if current != self._expected_old_geometry():
            return CommandResult.rejected(
                self,
                "execute",
                "The object geometry changed before this edit " "could be applied.",
            )
        if self._expected_old_geometry() == self._expected_new_geometry():
            return CommandResult.no_change(
                self,
                "execute",
                "The geometry is already in the requested state.",
            )
        if self.new_has_collision and self.new_collision is None:
            return CommandResult.failed(
                self,
                "execute",
                "CollisionGeometryUnavailable",
                "The target collision geometry is unavailable.",
            )

        obj = scene.objects[self.object_id]
        obj.polygon = copy.deepcopy(self.new_polygon)
        if self.new_has_collision:
            scene.collision_shapes[self.object_id] = copy.deepcopy(self.new_collision)
        else:
            scene.collision_shapes.pop(self.object_id, None)
        scene._notify()

    def undo(self, scene: Any):
        current = self._geometry(scene, self.object_id)
        if current is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The object no longer exists.",
            )
        if current != self._expected_new_geometry():
            return CommandResult.rejected(
                self,
                "undo",
                "The object geometry changed before Undo.",
            )
        if self.old_has_collision and self.old_collision is None:
            return CommandResult.failed(
                self,
                "undo",
                "CollisionGeometryUnavailable",
                "The previous collision geometry is unavailable.",
            )

        obj = scene.objects[self.object_id]
        obj.polygon = copy.deepcopy(self.old_polygon)
        if self.old_has_collision:
            scene.collision_shapes[self.object_id] = copy.deepcopy(self.old_collision)
        else:
            scene.collision_shapes.pop(self.object_id, None)
        scene._notify()


class ExpandContractCommand(UpdatePolygonCommand):
    # Backward-compatible name for polygon replacement.
    pass


class CreateGroupCommand(Command):
    """Create one group with stable identity across Undo and Redo."""

    def __init__(self, name: str):
        self.name = str(name).strip()
        self.group_id: Optional[str] = None
        self._index: Optional[int] = None

    def execute(self, scene: Any):
        if not self.name:
            return CommandResult.rejected(
                self,
                "execute",
                "The group name must not be empty.",
            )
        if self.group_id is None:
            group = scene.create_group(self.name)
            self.group_id = group.id
            self._index = len(scene.groups) - 1
            return None
        if _group_index(scene, self.group_id) is not None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group id is already in use.",
            )

        from src.models.scene import Group

        insert_at = min(
            self._index if self._index is not None else len(scene.groups),
            len(scene.groups),
        )
        scene.groups.insert(
            insert_at,
            Group(id=self.group_id, name=self.name),
        )
        scene._notify()

    def undo(self, scene: Any):
        if self.group_id is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The created group id is unavailable.",
            )
        index = _group_index(scene, self.group_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The created group no longer exists.",
            )
        self._index = index
        scene.remove_group(self.group_id)


class RemoveGroupCommand(Command):
    """Remove one group and restore its exact state and index."""

    def __init__(self, group_id: str):
        self.group_id = str(group_id)
        self._backup: Optional[Dict[str, Any]] = None
        self._backup_index: Optional[int] = None

    def execute(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group no longer exists.",
            )
        group = scene.groups[index]
        self._backup_index = index
        self._backup = {
            "id": group.id,
            "name": group.name,
            "visible": bool(group.visible),
            "locked": bool(group.locked),
            "members": list(group.members),
        }
        scene.remove_group(self.group_id)

    def undo(self, scene: Any):
        if self._backup is None or self._backup_index is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The removed group backup is unavailable.",
            )
        if _group_index(scene, self.group_id) is not None:
            return CommandResult.rejected(
                self,
                "undo",
                "The group id is already in use.",
            )
        if any(object_id not in scene.objects for object_id in self._backup["members"]):
            return CommandResult.failed(
                self,
                "undo",
                "GroupRelationshipError",
                "An object required by the removed group is missing.",
            )

        from src.models.scene import Group

        group = Group(
            id=self._backup["id"],
            name=self._backup["name"],
            visible=self._backup["visible"],
            locked=self._backup["locked"],
        )
        group.members = list(self._backup["members"])
        insert_at = min(self._backup_index, len(scene.groups))
        scene.groups.insert(insert_at, group)
        scene._notify()


class AddToGroupCommand(Command):
    """Add one existing object to one existing group."""

    def __init__(self, group_id: str, object_id: str):
        self.group_id = str(group_id)
        self.object_id = str(object_id)
        self._added = False

    def execute(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group no longer exists.",
            )
        if self.object_id not in scene.objects:
            return CommandResult.rejected(
                self,
                "execute",
                "The object no longer exists.",
            )
        if self.object_id in scene.groups[index].members:
            return CommandResult.no_change(
                self,
                "execute",
                "The object already belongs to this group.",
            )
        scene.add_object_to_group(self.group_id, self.object_id)
        self._added = True

    def undo(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None or not self._added:
            return CommandResult.rejected(
                self,
                "undo",
                "The added group membership is unavailable.",
            )
        if self.object_id not in scene.groups[index].members:
            return CommandResult.rejected(
                self,
                "undo",
                "The group membership changed before Undo.",
            )
        scene.remove_object_from_group(self.group_id, self.object_id)


class RemoveFromGroupCommand(Command):
    """Remove one object from one group and restore it on Undo."""

    def __init__(self, group_id: str, object_id: str):
        self.group_id = str(group_id)
        self.object_id = str(object_id)
        self._removed = False

    def execute(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group no longer exists.",
            )
        if self.object_id not in scene.groups[index].members:
            return CommandResult.no_change(
                self,
                "execute",
                "The object is not a member of this group.",
            )
        scene.remove_object_from_group(self.group_id, self.object_id)
        self._removed = True

    def undo(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None or not self._removed:
            return CommandResult.rejected(
                self,
                "undo",
                "The removed group membership is unavailable.",
            )
        if self.object_id not in scene.objects:
            return CommandResult.rejected(
                self,
                "undo",
                "The object no longer exists.",
            )
        if self.object_id in scene.groups[index].members:
            return CommandResult.rejected(
                self,
                "undo",
                "The group membership changed before Undo.",
            )
        scene.add_object_to_group(self.group_id, self.object_id)


class ToggleGroupVisibilityCommand(Command):
    """Toggle group visibility with exact state preconditions."""

    def __init__(self, group_id: str):
        self.group_id = str(group_id)
        self._old: Optional[bool] = None
        self._new: Optional[bool] = None

    def execute(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group no longer exists.",
            )
        current = bool(scene.groups[index].visible)
        if self._old is None:
            self._old = current
            self._new = not current
        elif current != self._old:
            return CommandResult.rejected(
                self,
                "execute",
                "The group visibility changed before Redo.",
            )
        scene.set_group_visibility(self.group_id, bool(self._new))

    def undo(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None or self._old is None or self._new is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The previous group visibility is unavailable.",
            )
        if bool(scene.groups[index].visible) != self._new:
            return CommandResult.rejected(
                self,
                "undo",
                "The group visibility changed before Undo.",
            )
        scene.set_group_visibility(self.group_id, self._old)


class ToggleGroupLockCommand(Command):
    """Toggle group lock with exact state preconditions."""

    def __init__(self, group_id: str):
        self.group_id = str(group_id)
        self._old: Optional[bool] = None
        self._new: Optional[bool] = None

    def execute(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group no longer exists.",
            )
        current = bool(scene.groups[index].locked)
        if self._old is None:
            self._old = current
            self._new = not current
        elif current != self._old:
            return CommandResult.rejected(
                self,
                "execute",
                "The group lock changed before Redo.",
            )
        scene.set_group_lock(self.group_id, bool(self._new))

    def undo(self, scene: Any):
        index = _group_index(scene, self.group_id)
        if index is None or self._old is None or self._new is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The previous group lock is unavailable.",
            )
        if bool(scene.groups[index].locked) != self._new:
            return CommandResult.rejected(
                self,
                "undo",
                "The group lock changed before Undo.",
            )
        scene.set_group_lock(self.group_id, self._old)


class _CreatePolygonCommandBase(Command):
    """Create one polygon object with stable identity and exact selection."""

    def __init__(
        self,
        polygon: List[Tuple[int, int]],
        layer_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ):
        self.polygon: List[Tuple[int, int]] = [
            (point[0], point[1]) for point in polygon
        ]
        self.layer_id = layer_id
        self.object_id = object_id
        self._previous_selected_id: Optional[str] = None
        self._object_snapshot: Optional[Any] = None
        self._object_ids_before: Optional[Tuple[str, ...]] = None
        self._executed_once = False

    def _stored_layer_exists(self, scene: Any) -> bool:
        if self._object_snapshot is None:
            return False
        layer_id = getattr(self._object_snapshot, "layer_id", None)
        return layer_id in {layer.id for layer in scene.layers}

    def _previous_selection_is_available(self, scene: Any) -> bool:
        return (
            self._previous_selected_id is None
            or self._previous_selected_id in scene.objects
        )

    def _object_matches_snapshot(self, scene: Any) -> bool:
        if self.object_id is None or self._object_snapshot is None:
            return False
        current = scene.objects.get(self.object_id)
        return current is not None and _freeze_state(current) == _freeze_state(
            self._object_snapshot
        )

    def _relationships_are_unchanged(self, scene: Any) -> bool:
        if self.object_id is None:
            return False
        if self.object_id in scene.collision_shapes:
            return False
        return all(self.object_id not in group.members for group in scene.groups)

    def _execute_first(self, scene: Any) -> Optional[CommandResult]:
        target_layer_id = self.layer_id or "layer_default"
        if target_layer_id not in {layer.id for layer in scene.layers}:
            return CommandResult.rejected(
                self,
                "execute",
                "The target layer is unavailable.",
            )
        if self.object_id is not None and self.object_id in scene.objects:
            return CommandResult.rejected(
                self,
                "execute",
                "The requested object id is already in use.",
            )

        self._previous_selected_id = scene.selected_id
        self._object_ids_before = tuple(scene.objects)

        if self.object_id is None:
            self.object_id = scene.add_polygon(self.polygon, self.layer_id)
        else:
            scene.add_object(
                self.object_id,
                self.polygon,
                self.layer_id,
                select=True,
            )

        self._object_snapshot = copy.deepcopy(scene.objects[self.object_id])
        self._executed_once = True
        return None

    def _execute_redo(self, scene: Any) -> Optional[CommandResult]:
        if (
            self.object_id is None
            or self._object_snapshot is None
            or self._object_ids_before is None
        ):
            return CommandResult.rejected(
                self,
                "execute",
                "The created object backup is unavailable.",
            )
        if self.object_id in scene.objects:
            return CommandResult.rejected(
                self,
                "execute",
                "The created object id is already in use.",
            )
        if tuple(scene.objects) != self._object_ids_before:
            return CommandResult.rejected(
                self,
                "execute",
                "The object collection changed before Redo.",
            )
        if scene.selected_id != self._previous_selected_id:
            return CommandResult.rejected(
                self,
                "execute",
                "The selection changed before Redo.",
            )
        if not self._previous_selection_is_available(scene):
            return CommandResult.rejected(
                self,
                "execute",
                "The previous selection is no longer available.",
            )
        if not self._stored_layer_exists(scene):
            return CommandResult.rejected(
                self,
                "execute",
                "The target layer is no longer available.",
            )

        scene.objects[self.object_id] = copy.deepcopy(self._object_snapshot)
        scene.selected_id = self.object_id
        scene._notify()
        return None

    def execute(self, scene: Any):
        if not self._executed_once:
            return self._execute_first(scene)
        return self._execute_redo(scene)

    def undo(self, scene: Any):
        if (
            self.object_id is None
            or self._object_snapshot is None
            or self._object_ids_before is None
        ):
            return CommandResult.rejected(
                self,
                "undo",
                "The created object backup is unavailable.",
            )
        if self.object_id not in scene.objects:
            return CommandResult.rejected(
                self,
                "undo",
                "The created object no longer exists.",
            )
        if tuple(scene.objects) != self._object_ids_before + (self.object_id,):
            return CommandResult.rejected(
                self,
                "undo",
                "The object collection changed before Undo.",
            )
        if not self._object_matches_snapshot(scene):
            return CommandResult.rejected(
                self,
                "undo",
                "The created object changed before Undo.",
            )
        if not self._relationships_are_unchanged(scene):
            return CommandResult.rejected(
                self,
                "undo",
                "The created object relationships changed before Undo.",
            )
        if scene.selected_id != self.object_id:
            return CommandResult.rejected(
                self,
                "undo",
                "The selection changed before Undo.",
            )
        if not self._previous_selection_is_available(scene):
            return CommandResult.rejected(
                self,
                "undo",
                "The previous selection is no longer available.",
            )

        scene.objects.pop(self.object_id)
        scene.selected_id = self._previous_selected_id
        scene._notify()
        return None


class AddPolygonCommand(_CreatePolygonCommandBase):
    def __init__(self, polygon: List[Tuple[int, int]], layer_id: Optional[str] = None):
        super().__init__(polygon, layer_id)


class CreateObjectCommand(_CreatePolygonCommandBase):
    def __init__(
        self,
        polygon: List[Tuple[int, int]],
        layer_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ):
        super().__init__(polygon, layer_id, object_id)


class CreateBezierObjectCommand(_CreatePolygonCommandBase):
    """Create one editable Bézier object with stable identity."""

    def __init__(
        self,
        beziers: Any,
        layer_id: Optional[str] = None,
        object_id: Optional[str] = None,
        *,
        steps_per_segment: int = 20,
    ):
        super().__init__([], layer_id, object_id)
        self.beziers = copy.deepcopy(beziers)
        self.steps_per_segment = steps_per_segment

    def execute(self, scene: Any):
        if not self._executed_once:
            try:
                canonical = canonicalize_beziers(self.beziers)
                polygon = sample_beziers_to_polygon(
                    canonical,
                    steps_per_segment=self.steps_per_segment,
                )
            except (TypeError, ValueError) as exc:
                return CommandResult.rejected(self, "execute", str(exc))

            self.beziers = canonical
            self.polygon = polygon
            result = self._execute_first(scene)
            if result is not None:
                return result
            if self.object_id is None:
                return CommandResult.failed(
                    self,
                    "execute",
                    "BezierCreationError",
                    "The created object id is unavailable.",
                )
            scene.set_object_beziers(
                self.object_id,
                canonical,
                steps_per_segment=self.steps_per_segment,
            )
            self._object_snapshot = copy.deepcopy(scene.objects[self.object_id])
            return None
        return self._execute_redo(scene)


class MoveGroupCommand(Command):
    """Move one group and restore its exact previous index."""

    def __init__(self, group_id: str, new_index: int):
        self.group_id = str(group_id)
        self.new_index = int(new_index)
        self._old_index: Optional[int] = None

    def execute(self, scene: Any):
        old_index = _group_index(scene, self.group_id)
        if old_index is None:
            return CommandResult.rejected(
                self,
                "execute",
                "The group no longer exists.",
            )
        target = max(0, min(self.new_index, len(scene.groups) - 1))
        if target == old_index:
            return CommandResult.no_change(
                self,
                "execute",
                "The group is already at the requested index.",
            )
        self._old_index = old_index
        scene.move_group(self.group_id, target)

    def undo(self, scene: Any):
        if self._old_index is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The previous group index is unavailable.",
            )
        if _group_index(scene, self.group_id) is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The moved group no longer exists.",
            )
        scene.move_group(self.group_id, self._old_index)


class AutoGenerateCollisionShapesCommand(Command):
    """Replace all collision shapes from current object polygons atomically."""

    def __init__(self):
        self._old_shapes: Optional[Dict[str, List[Tuple[float, float]]]] = None
        self._generated_shapes: Optional[Dict[str, List[Tuple[float, float]]]] = None
        self._object_geometry_token: Any = None
        self._executed_once = False

    @property
    def generated_count(self) -> int:
        return len(self._generated_shapes or {})

    @staticmethod
    def _current_geometry_token(scene: Any) -> Any:
        return _freeze_state(
            [
                (
                    object_id,
                    list(getattr(obj, "polygon", []) or []),
                )
                for object_id, obj in scene.objects.items()
            ]
        )

    def _build_shapes(
        self,
        scene: Any,
    ) -> tuple[Optional[Dict[str, List[Tuple[float, float]]]], Optional[str]]:
        generated: Dict[str, List[Tuple[float, float]]] = {}
        for object_id, obj in scene.objects.items():
            polygon = getattr(obj, "polygon", None)
            if not polygon or len(polygon) < 3:
                continue

            shape: List[Tuple[float, float]] = []
            for point in polygon:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    return None, f"Object {object_id!r} has an invalid polygon point."
                x, y = point
                if not isinstance(x, (int, float)) or isinstance(x, bool):
                    return None, f"Object {object_id!r} has a non-numeric x coordinate."
                if not isinstance(y, (int, float)) or isinstance(y, bool):
                    return None, f"Object {object_id!r} has a non-numeric y coordinate."
                fx = float(x)
                fy = float(y)
                if not math.isfinite(fx) or not math.isfinite(fy):
                    return None, f"Object {object_id!r} has a non-finite coordinate."
                shape.append((fx, fy))
            generated[str(object_id)] = shape
        return generated, None

    def execute(self, scene: Any):
        if not self._executed_once:
            generated, error = self._build_shapes(scene)
            if error is not None:
                return CommandResult.rejected(self, "execute", error)
            if not generated:
                return CommandResult.no_change(
                    self,
                    "execute",
                    "No valid scene polygons are available for collision generation.",
                )
            if _freeze_state(scene.collision_shapes) == _freeze_state(generated):
                return CommandResult.no_change(
                    self,
                    "execute",
                    "Collision shapes already match the current scene polygons.",
                )

            self._old_shapes = copy.deepcopy(scene.collision_shapes)
            self._generated_shapes = copy.deepcopy(generated)
            self._object_geometry_token = self._current_geometry_token(scene)
            self._executed_once = True
        else:
            if self._old_shapes is None or self._generated_shapes is None:
                return CommandResult.rejected(
                    self,
                    "execute",
                    "The collision generation backup is unavailable.",
                )
            if self._current_geometry_token(scene) != self._object_geometry_token:
                return CommandResult.rejected(
                    self,
                    "execute",
                    "Scene object geometry changed before Redo.",
                )
            if _freeze_state(scene.collision_shapes) != _freeze_state(self._old_shapes):
                return CommandResult.rejected(
                    self,
                    "execute",
                    "Collision shapes changed before Redo.",
                )

        scene.collision_shapes = copy.deepcopy(self._generated_shapes)
        scene._notify()
        return None

    def undo(self, scene: Any):
        if self._old_shapes is None or self._generated_shapes is None:
            return CommandResult.rejected(
                self,
                "undo",
                "The collision generation backup is unavailable.",
            )
        if self._current_geometry_token(scene) != self._object_geometry_token:
            return CommandResult.rejected(
                self,
                "undo",
                "Scene object geometry changed before Undo.",
            )
        if _freeze_state(scene.collision_shapes) != _freeze_state(
            self._generated_shapes
        ):
            return CommandResult.rejected(
                self,
                "undo",
                "Collision shapes changed before Undo.",
            )

        scene.collision_shapes = copy.deepcopy(self._old_shapes)
        scene._notify()
        return None


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
