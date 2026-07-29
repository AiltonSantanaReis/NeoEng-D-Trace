"""Implementation of :mod:`src.core.commands`.

Implementation preserved in the single ``src`` source tree.
"""

from typing import List, Optional, Tuple, Any, Dict
from src.core.logger import logger


class Command:
    def execute(self, scene: Any):
        raise NotImplementedError()

    def undo(self, scene: Any):
        raise NotImplementedError()


class CompositeCommand(Command):
    """Command that executes multiple sub-commands as a transaction."""

    def __init__(self, commands: List[Command]):
        self.commands = commands
        self._executed: List[Command] = []

    def execute(self, scene: Any):
        for cmd in self.commands:
            try:
                cmd.execute(scene)
                self._executed.append(cmd)
            except Exception as e:
                logger.error(f"Composite command failed at {cmd}: {e}")
                # Undo executed commands
                for executed in reversed(self._executed):
                    try:
                        executed.undo(scene)
                    except Exception as undo_e:
                        logger.error(f"Undo failed for {executed}: {undo_e}")
                raise e

    def undo(self, scene: Any):
        for cmd in reversed(self._executed):
            try:
                cmd.undo(scene)
            except Exception as e:
                logger.error(f"Undo failed for {cmd}: {e}")
                # Continue undoing others


class CommandManager:
    """Manages command execution with undo/redo functionality."""

    def __init__(self, max_history=50):
        """Initialize CommandManager with maximum history size."""
        self.max_history = max_history
        self._undo: List[Command] = []
        self._redo: List[Command] = []

    def execute(self, cmd: Command, scene: Any) -> None:
        """Execute a command, handling exceptions and managing undo stack."""
        try:
            cmd.execute(scene)
            self._undo.append(cmd)
            if len(self._undo) > self.max_history:
                self._undo.pop(0)
            self._redo.clear()
        except Exception as e:
            logger.error(f"Command execution failed: {e}")

    def undo(self, scene: Any) -> None:
        """Undo the last command, handling exceptions."""
        if not self._undo:
            return
        c = self._undo.pop()
        try:
            c.undo(scene)
            self._redo.append(c)
        except Exception as e:
            logger.error(f"Command undo failed: {e}")
            # Put back if undo failed
            self._undo.append(c)

    def redo(self, scene: Any) -> None:
        """Redo the last undone command, handling exceptions."""
        if not self._redo:
            return
        c = self._redo.pop()
        try:
            c.execute(scene)
            self._undo.append(c)
        except Exception as e:
            logger.error(f"Command redo failed: {e}")
            # Put back if redo failed
            self._redo.append(c)


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


class ExpandContractCommand(Command):
    def __init__(
        self,
        object_id: str,
        old_polygon: List[Tuple[int, int]],
        new_polygon: List[Tuple[int, int]],
    ):
        self.object_id = object_id
        self.old_polygon = [tuple(p) for p in old_polygon]
        self.new_polygon = [tuple(p) for p in new_polygon]

    def execute(self, scene: Any):
        if self.object_id not in scene.objects:
            return
        scene.update_polygon(self.object_id, self.new_polygon)

    def undo(self, scene: Any):
        if self.object_id not in scene.objects:
            return
        scene.update_polygon(self.object_id, self.old_polygon)


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
    def __init__(
        self, polygon: List[Tuple[int, int]], layer_id: Optional[str] = None
    ):
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
    def __init__(self, object_id: str):
        self.object_id = object_id
        self._was_enabled = False

    def execute(self, scene: Any):
        self._was_enabled = scene.has_collision(self.object_id)
        scene.set_object_collision(self.object_id, not self._was_enabled)

    def undo(self, scene: Any):
        scene.set_object_collision(self.object_id, self._was_enabled)


class ClearSceneCommand(Command):
    def __init__(self):
        self._backup_objects = {}
        self._backup_groups = []
        self._backup_collisions = {}

    def execute(self, scene: Any):
        self._backup_objects = scene.objects.copy()
        if hasattr(scene, "groups"):
            self._backup_groups = list(getattr(scene, "groups", []))
        if hasattr(scene, "collision_shapes"):
            self._backup_collisions = scene.collision_shapes.copy()
        scene.objects.clear()
        if hasattr(scene, "groups"):
            scene.groups.clear()
        if hasattr(scene, "collision_shapes"):
            scene.collision_shapes.clear()
        scene._notify()

    def undo(self, scene: Any):
        scene.objects = self._backup_objects.copy()
        if hasattr(scene, "groups"):
            scene.groups = list(self._backup_groups)
        if hasattr(scene, "collision_shapes"):
            scene.collision_shapes = self._backup_collisions.copy()
        scene._notify()


# --- NOVO COMANDO PARA CORRIGIR ERROS DE IMPORTAÇÃO ---


class DeleteObjectCommand(Command):
    def __init__(self, object_id: str):
        self.object_id = object_id
        self._backup_obj: Optional[Any] = None

    def execute(self, scene: Any):
        if self.object_id in scene.objects:
            self._backup_obj = scene.objects[self.object_id]
            scene.remove_object(self.object_id)

    def undo(self, scene: Any):
        if self._backup_obj:
            # Restaura o objeto diretamente para manter metadados
            scene.objects[self.object_id] = self._backup_obj
            scene._notify()
