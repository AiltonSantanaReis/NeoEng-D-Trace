"""Undoable editing session for the professional scene authoring model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from src.core.scene_authoring_clipboard import (
    SceneClipboardGroupRecord,
    decode_scene_clipboard,
    encode_scene_clipboard,
)
from src.core.scene_authoring_model import (
    SceneAuthoringModel,
    SceneSelection,
    snap_transform,
)
from src.core.scene_authoring_order import ordered_scene_objects
from src.persistence.project_schema import MAX_ID_LENGTH, MAX_NAME_LENGTH, Point3Record
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocument,
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
    SceneGroupAuthoringRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneSnapRecord,
    SceneSocketRecord,
    SceneTransformRecord,
)


@dataclass(frozen=True)
class SceneAuthoringSnapshot:
    document: SceneAuthoringDocument
    selection: SceneSelection


@dataclass(frozen=True)
class _HistoryEntry:
    before: SceneAuthoringSnapshot
    after: SceneAuthoringSnapshot
    description: str


@dataclass(frozen=True)
class _TransformHistoryEntry:
    before: tuple[tuple[str, SceneTransformRecord], ...]
    after: tuple[tuple[str, SceneTransformRecord], ...]
    selection_before: SceneSelection
    selection_after: SceneSelection
    description: str


_DEFAULT_EDIT_OFFSET = Point3Record(x=16.0, y=16.0, z=0.0)


def _allocate_copy_id(source_id: str, used: set[str]) -> str:
    """Allocate a valid deterministic ID without colliding in the document."""

    suffix = "__copy"
    candidate = (source_id[: MAX_ID_LENGTH - len(suffix)] + suffix)[:MAX_ID_LENGTH]
    index = 2
    while candidate in used:
        suffix = f"__copy_{index}"
        candidate = (source_id[: MAX_ID_LENGTH - len(suffix)] + suffix)[:MAX_ID_LENGTH]
        index += 1
    used.add(candidate)
    return candidate


def _copy_group_name(name: str) -> str:
    suffix = " Copy"
    prefix = name[: max(1, MAX_NAME_LENGTH - len(suffix))]
    return (prefix + suffix)[:MAX_NAME_LENGTH]


class SceneAuthoringSession:
    """Transactional facade used by the viewport and numeric inspector."""

    def __init__(self, model: SceneAuthoringModel, *, max_history: int = 100) -> None:
        if max_history < 1:
            raise ValueError("max_history must be at least 1")
        self.model = model
        self.max_history = int(max_history)
        self._undo: list[_HistoryEntry | _TransformHistoryEntry] = []
        self._redo: list[_HistoryEntry | _TransformHistoryEntry] = []
        self._listeners: list[Callable[[], None]] = []
        self._gesture_before: SceneAuthoringSnapshot | None = None
        self._gesture_transform_before: (
            tuple[tuple[str, SceneTransformRecord], ...] | None
        ) = None
        self._gesture_selection_before: SceneSelection | None = None
        self._gesture_transform_history_safe = False
        self._isolated_group_id: str | None = None
        self._saved_document = self.document.model_copy(deep=True)
        self._force_dirty = False

    @property
    def document(self) -> SceneAuthoringDocument:
        return self.model.document

    @property
    def selection(self) -> SceneSelection:
        return self.model.selection

    @property
    def is_dirty(self) -> bool:
        """Whether the authored document differs from its last saved snapshot."""

        return self._force_dirty or self.document != self._saved_document

    def mark_saved(self) -> None:
        """Record the current authored document as the persisted baseline."""

        self._saved_document = self.document.model_copy(deep=True)
        self._force_dirty = False
        self._notify()

    def mark_unsaved(self) -> None:
        """Mark the active document as requiring an explicit save."""

        self._force_dirty = True
        self._notify()

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

    def _notify(self) -> None:
        if self._isolated_group_id is not None and not any(
            item.id == self._isolated_group_id for item in self.document.groups
        ):
            self._isolated_group_id = None
        for callback in list(self._listeners):
            callback()

    def snapshot(self) -> SceneAuthoringSnapshot:
        return SceneAuthoringSnapshot(
            document=self.document.model_copy(deep=True),
            selection=self.selection,
        )

    def _restore(self, snapshot: SceneAuthoringSnapshot) -> None:
        self.model.document = self.model.document.__class__.model_validate(
            snapshot.document, strict=True
        )
        known = {item.id for item in self.document.objects}
        ids = [item for item in snapshot.selection.ids if item in known]
        primary = (
            snapshot.selection.primary if snapshot.selection.primary in ids else None
        )
        self.model.selection = SceneSelection.from_ids(ids, primary)

    def _record(self, before: SceneAuthoringSnapshot, description: str) -> bool:
        after = self.snapshot()
        if before == after:
            return False
        self._undo.append(_HistoryEntry(before, after, description))
        if len(self._undo) > self.max_history:
            del self._undo[: len(self._undo) - self.max_history]
        self._redo.clear()
        return True

    def _capture_transform_state(
        self, object_ids: Iterable[str]
    ) -> tuple[tuple[str, SceneTransformRecord], ...]:
        requested = tuple(dict.fromkeys(object_ids))
        requested_set = set(requested)
        captured = tuple(
            (item.id, item.transform.model_copy(deep=True))
            for item in self.document.objects
            if item.id in requested_set
        )
        if len(captured) != len(requested_set):
            known = {item.id for item in self.document.objects}
            missing = next(item for item in requested if item not in known)
            raise KeyError(missing)
        return captured

    def _restore_transform_state(
        self,
        states: tuple[tuple[str, SceneTransformRecord], ...],
        selection: SceneSelection,
    ) -> None:
        state_by_id = dict(states)
        known = {item.id for item in self.document.objects}
        missing = next(
            (item_id for item_id in state_by_id if item_id not in known), None
        )
        if missing is not None:
            raise KeyError(missing)
        objects = [
            (
                item.model_copy(update={"transform": state_by_id[item.id]})
                if item.id in state_by_id
                else item
            )
            for item in self.document.objects
        ]
        self.model.document = self.model.document.__class__.model_validate(
            self.document.model_copy(update={"objects": objects}), strict=True
        )
        known = {item.id for item in self.document.objects}
        ids = [item for item in selection.ids if item in known]
        primary = selection.primary if selection.primary in ids else None
        self.model.selection = SceneSelection.from_ids(ids, primary)

    def _record_transform(
        self,
        before: tuple[tuple[str, SceneTransformRecord], ...],
        selection_before: SceneSelection,
        description: str,
    ) -> bool:
        object_ids = tuple(item_id for item_id, _ in before)
        after = self._capture_transform_state(object_ids)
        selection_after = self.selection
        if before == after and selection_before == selection_after:
            return False
        self._undo.append(
            _TransformHistoryEntry(
                before,
                after,
                selection_before,
                selection_after,
                description,
            )
        )
        if len(self._undo) > self.max_history:
            del self._undo[: len(self._undo) - self.max_history]
        self._redo.clear()
        return True

    def _apply_transform_operation(
        self,
        object_ids: Iterable[str],
        operation: Callable[[], None],
        description: str,
    ) -> bool:
        requested = tuple(dict.fromkeys(object_ids))
        known = {item.id for item in self.document.objects}
        if any(item_id not in known for item_id in requested):
            return self.apply(operation, description)
        before = self._capture_transform_state(requested)
        selection_before = self.selection
        try:
            operation()
        except Exception:
            self._restore_transform_state(before, selection_before)
            self._notify()
            raise
        changed = self._record_transform(before, selection_before, description)
        self._notify()
        return changed

    def apply(self, operation: Callable[[], None], description: str) -> bool:
        """Run an operation atomically and place it in local history."""

        if self._gesture_before is not None:
            self._gesture_transform_history_safe = False
        before = self.snapshot()
        try:
            operation()
        except Exception:
            self._restore(before)
            self._notify()
            raise
        changed = self._record(before, description)
        self._notify()
        return changed

    def begin_gesture(self) -> None:
        if self._gesture_before is not None:
            raise RuntimeError("an authoring gesture is already active")
        self._gesture_before = self.snapshot()
        self._gesture_transform_before = self._capture_transform_state(
            self.selection.ids
        )
        self._gesture_selection_before = self.selection
        self._gesture_transform_history_safe = True

    def restore_gesture_base(self) -> None:
        if self._gesture_before is None:
            raise RuntimeError("no authoring gesture is active")
        self._restore(self._gesture_before)
        self._notify()

    def finish_gesture(self, description: str) -> bool:
        if self._gesture_before is None:
            raise RuntimeError("no authoring gesture is active")
        before = self._gesture_before
        transform_before = self._gesture_transform_before
        selection_before = self._gesture_selection_before
        history_safe = self._gesture_transform_history_safe
        self._gesture_before = None
        self._gesture_transform_before = None
        self._gesture_selection_before = None
        self._gesture_transform_history_safe = False
        if (
            history_safe
            and transform_before is not None
            and selection_before is not None
        ):
            changed = self._record_transform(
                transform_before, selection_before, description
            )
        else:
            changed = self._record(before, description)
        self._notify()
        return changed

    def cancel_gesture(self) -> None:
        if self._gesture_before is None:
            return
        before = self._gesture_before
        self._gesture_before = None
        self._gesture_transform_before = None
        self._gesture_selection_before = None
        self._gesture_transform_history_safe = False
        self._restore(before)
        self._notify()

    def set_selection(
        self, object_ids: Iterable[str], primary: str | None = None
    ) -> SceneSelection:
        if self._gesture_before is not None:
            self._gesture_transform_history_safe = False
        selected = self.model.set_selection(object_ids, primary)
        self._notify()
        return selected

    def clear_selection(self) -> None:
        self.model.clear_selection()
        self._notify()

    def translate_selected(
        self,
        delta: Point3Record,
        description: str = "Move objects",
    ) -> bool:
        return self._apply_transform_operation(
            self.selection.ids,
            lambda: self.model.translate_selected(delta),
            description,
        )

    def transform_selected(
        self,
        *,
        translation: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0),
        rotation_z: float = 0.0,
        scale_factor: float = 1.0,
        description: str = "Transform objects",
    ) -> bool:
        return self._apply_transform_operation(
            self.selection.ids,
            lambda: self.model.transform_selected(
                translation=translation,
                rotation_z=rotation_z,
                scale_factor=scale_factor,
            ),
            description,
        )

    def preview_transform_selected(
        self,
        *,
        translation: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0),
        rotation_z: float = 0.0,
        scale_factor: float = 1.0,
    ) -> None:
        if self._gesture_before is None:
            raise RuntimeError("no authoring gesture is active")
        self.restore_gesture_base()
        self.model.transform_selected(
            translation=translation,
            rotation_z=rotation_z,
            scale_factor=scale_factor,
        )
        self._notify()

    def update_transform(
        self,
        object_id: str,
        transform: SceneTransformRecord,
    ) -> bool:
        return self._apply_transform_operation(
            (object_id,),
            lambda: self.model.update_transform(object_id, transform),
            "Edit object transform",
        )

    def add_asset(self, asset: AssetReferenceRecord) -> bool:
        return self.apply(
            lambda: self.model.add_asset(asset),
            "Import scene asset",
        )

    def update_asset(self, asset: AssetReferenceRecord) -> bool:
        return self.apply(
            lambda: self.model.update_asset(asset),
            "Update scene asset",
        )

    def add_object(
        self,
        obj: SceneObjectAuthoringRecord,
        *,
        select: bool = False,
    ) -> bool:
        return self.apply(
            lambda: self.model.add_object(obj, select=select),
            "Add scene object",
        )

    def remove_object(self, object_id: str) -> bool:
        return self.apply(
            lambda: self.model.remove_object(object_id),
            "Remove scene object",
        )

    def _selected_objects_in_document_order(
        self,
    ) -> tuple[SceneObjectAuthoringRecord, ...]:
        selected = set(self.selection.ids)
        objects = tuple(
            item for item in ordered_scene_objects(self.document) if item.id in selected
        )
        if len(objects) != len(selected):
            missing = next(
                item for item in selected if item not in {obj.id for obj in objects}
            )
            raise KeyError(missing)
        return objects

    def nudge_selected(self, delta: Point3Record) -> bool:
        """Move the current selection through the existing transactional path."""

        return self.translate_selected(delta, "Nudge selected objects")

    def duplicate_selected(
        self,
        offset: Point3Record = _DEFAULT_EDIT_OFFSET,
    ) -> tuple[str, ...]:
        """Duplicate selection as independent objects with deterministic IDs."""

        selected = self._selected_objects_in_document_order()
        if not selected:
            return ()
        created: list[str] = []

        def operation() -> None:
            for item in selected:
                self.model.assert_editable(item.id)
            used = {item.id for item in self.document.objects}
            for item in selected:
                object_id = _allocate_copy_id(item.id, used)
                position = Point3Record(
                    x=item.transform.position.x + offset.x,
                    y=item.transform.position.y + offset.y,
                    z=item.transform.position.z + offset.z,
                )
                transform = snap_transform(
                    item.transform.model_copy(update={"position": position}),
                    self.document.snap,
                )
                self.model.add_object(
                    item.model_copy(update={"id": object_id, "transform": transform})
                )
                created.append(object_id)
            self.model.set_selection(created, created[-1])

        self.apply(operation, "Duplicate selected objects")
        return tuple(created)

    def delete_selected(self) -> bool:
        """Delete the complete selection after atomic lock preflight."""

        ids = tuple(self.selection.ids)
        if not ids:
            return False
        return self.apply(
            lambda: self.model.remove_objects(ids),
            "Delete selected objects",
        )

    def copy_selected_payload(self) -> bytes | None:
        """Return a strict clipboard payload without mutating document state."""

        objects = list(self._selected_objects_in_document_order())
        if not objects:
            return None
        object_ids = {item.id for item in objects}
        complete_groups = [
            group
            for group in self.document.groups
            if group.members and set(group.members).issubset(object_ids)
        ]
        complete_group_ids = {group.id for group in complete_groups}
        groups = [
            SceneClipboardGroupRecord(
                id=group.id,
                name=group.name,
                members=list(group.members),
                visible=group.visible,
                locked=group.locked,
                parent_group_id=(
                    getattr(group, "parent_group_id", None)
                    if getattr(group, "parent_group_id", None) in complete_group_ids
                    else None
                ),
            )
            for group in complete_groups
        ]
        return encode_scene_clipboard(objects, groups)

    def paste_payload(
        self,
        value: bytes | bytearray,
        offset: Point3Record = _DEFAULT_EDIT_OFFSET,
    ) -> tuple[str, ...]:
        """Paste a validated payload atomically, allocating new identities."""

        payload = decode_scene_clipboard(value)
        created: list[str] = []

        def operation() -> None:
            asset_ids = {item.id for item in self.document.assets}
            layer_ids = {item.id for item in self.document.layers}
            for item in payload.objects:
                if item.asset_id not in asset_ids:
                    raise ValueError(f"asset {item.asset_id!r} is not available")
                if item.layer_id not in layer_ids:
                    raise ValueError(f"layer {item.layer_id!r} is not available")
            if payload.groups and not isinstance(
                self.document, SceneAuthoringDocumentV2
            ):
                if any(group.parent_group_id is not None for group in payload.groups):
                    raise ValueError("nested group paste requires schema V2")

            used_objects = {item.id for item in self.document.objects}
            object_id_map: dict[str, str] = {}
            for item in payload.objects:
                object_id = _allocate_copy_id(item.id, used_objects)
                object_id_map[item.id] = object_id
                position = Point3Record(
                    x=item.transform.position.x + offset.x,
                    y=item.transform.position.y + offset.y,
                    z=item.transform.position.z + offset.z,
                )
                transform = snap_transform(
                    item.transform.model_copy(update={"position": position}),
                    self.document.snap,
                )
                self.model.add_object(
                    item.model_copy(update={"id": object_id, "transform": transform})
                )
                created.append(object_id)

            used_groups = {group.id for group in self.document.groups}
            group_id_map = {
                group.id: _allocate_copy_id(group.id, used_groups)
                for group in payload.groups
            }
            for group in payload.groups:
                members = [object_id_map[item] for item in group.members]
                parent_id = (
                    group_id_map.get(group.parent_group_id)
                    if group.parent_group_id is not None
                    else None
                )
                record: SceneGroupAuthoringRecord
                if isinstance(self.document, SceneAuthoringDocumentV2):
                    record = SceneGroupAuthoringRecordV2(
                        id=group_id_map[group.id],
                        name=_copy_group_name(group.name),
                        members=members,
                        visible=group.visible,
                        locked=group.locked,
                        parent_group_id=parent_id,
                    )
                else:
                    record = SceneGroupAuthoringRecord(
                        id=group_id_map[group.id],
                        name=_copy_group_name(group.name),
                        members=members,
                        visible=group.visible,
                        locked=group.locked,
                    )
                self.model.add_group(record)
            self.model.set_selection(created, created[-1])

        self.apply(operation, "Paste scene objects")
        return tuple(created)

    def set_snap(self, snap: SceneSnapRecord) -> bool:
        return self.apply(
            lambda: self.model.set_snap(snap),
            "Edit snapping",
        )

    def add_layer(self, layer: SceneLayerAuthoringRecord) -> bool:
        return self.apply(lambda: self.model.add_layer(layer), "Add scene layer")

    def remove_layer(self, layer_id: str) -> bool:
        return self.apply(
            lambda: self.model.remove_layer(layer_id),
            "Remove scene layer",
        )

    def rename_layer(self, layer_id: str, name: str) -> bool:
        return self.apply(
            lambda: self.model.rename_layer(layer_id, name),
            "Rename scene layer",
        )

    def reorder_layer(self, layer_id: str, target_index: int) -> bool:
        return self.apply(
            lambda: self.model.reorder_layer(layer_id, target_index),
            "Reorder scene layer",
        )

    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        return self.apply(
            lambda: self.model.set_layer_visibility(layer_id, visible),
            "Set scene layer visibility",
        )

    def set_layer_locked(self, layer_id: str, locked: bool) -> bool:
        return self.apply(
            lambda: self.model.set_layer_locked(layer_id, locked),
            "Set scene layer lock",
        )

    def set_camera(self, camera: SceneCameraAuthoringRecord) -> bool:
        return self.apply(
            lambda: self.model.set_camera(camera),
            "Edit scene camera",
        )

    def set_parallax_layer(self, parallax: SceneParallaxLayerRecord) -> bool:
        return self.apply(
            lambda: self.model.set_parallax_layer(parallax),
            "Edit layer parallax",
        )

    def add_socket(self, socket: SceneSocketRecord) -> bool:
        return self.apply(
            lambda: self.model.add_socket(socket),
            "Add scene socket",
        )

    def update_socket_position(self, socket_id: str, position: Point3Record) -> bool:
        return self.apply(
            lambda: self.model.update_socket_position(socket_id, position),
            "Move scene socket",
        )

    def remove_socket(self, socket_id: str) -> bool:
        return self.apply(
            lambda: self.model.remove_socket(socket_id),
            "Remove scene socket",
        )

    def _restore_history_entry(
        self,
        entry: _HistoryEntry | _TransformHistoryEntry,
        *,
        before: bool,
    ) -> None:
        if isinstance(entry, _TransformHistoryEntry):
            state = entry.before if before else entry.after
            selection = entry.selection_before if before else entry.selection_after
            self._restore_transform_state(state, selection)
            return
        self._restore(entry.before if before else entry.after)

    def undo(self) -> bool:
        if not self._undo:
            return False
        entry = self._undo.pop()
        self._restore_history_entry(entry, before=True)
        self._redo.append(entry)
        self._notify()
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        entry = self._redo.pop()
        self._restore_history_entry(entry, before=False)
        self._undo.append(entry)
        self._notify()
        return True

    @property
    def isolated_group_id(self) -> str | None:
        """Return the transient group currently isolated in the viewport."""

        return self._isolated_group_id

    def set_isolated_group(self, group_id: str | None) -> bool:
        if group_id is not None and not any(
            item.id == group_id for item in self.document.groups
        ):
            raise KeyError(group_id)
        if self._isolated_group_id == group_id:
            return False
        self._isolated_group_id = group_id
        self._notify()
        return True

    def clear_isolation(self) -> bool:
        return self.set_isolated_group(None)

    def add_group(self, group: SceneGroupAuthoringRecord) -> bool:
        return self.apply(
            lambda: self.model.add_group(group),
            "Create scene group",
        )

    def group_selection(self, group: SceneGroupAuthoringRecord) -> bool:
        return self.apply(
            lambda: self.model.group_selection(group),
            "Group selected objects",
        )

    def remove_group(self, group_id: str) -> bool:
        return self.apply(
            lambda: self.model.remove_group(group_id),
            "Delete scene group",
        )

    def rename_group(self, group_id: str, name: str) -> bool:
        return self.apply(
            lambda: self.model.rename_group(group_id, name),
            "Rename scene group",
        )

    def reorder_group(self, group_id: str, target_index: int) -> bool:
        return self.apply(
            lambda: self.model.reorder_group(group_id, target_index),
            "Reorder scene group",
        )

    def set_group_parent(self, group_id: str, parent_group_id: str | None) -> bool:
        return self.apply(
            lambda: self.model.set_group_parent(group_id, parent_group_id),
            "Reparent scene group",
        )

    def set_group_visibility(self, group_id: str, visible: bool) -> bool:
        return self.apply(
            lambda: self.model.set_group_visibility(group_id, visible),
            "Set scene group visibility",
        )

    def set_group_locked(self, group_id: str, locked: bool) -> bool:
        return self.apply(
            lambda: self.model.set_group_locked(group_id, locked),
            "Set scene group lock",
        )

    def add_objects_to_group(
        self,
        group_id: str,
        object_ids: Iterable[str],
    ) -> bool:
        return self.apply(
            lambda: self.model.add_objects_to_group(group_id, object_ids),
            "Add objects to scene group",
        )

    def remove_objects_from_group(
        self,
        group_id: str,
        object_ids: Iterable[str],
    ) -> bool:
        return self.apply(
            lambda: self.model.remove_objects_from_group(group_id, object_ids),
            "Remove objects from scene group",
        )

    def clear_history(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._gesture_before = None
        self._gesture_transform_before = None
        self._gesture_selection_before = None
        self._gesture_transform_history_safe = False
        self._notify()
