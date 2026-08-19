"""Undoable editing session for the professional scene authoring model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from src.core.scene_authoring_model import SceneAuthoringModel, SceneSelection
from src.persistence.project_schema import Point3Record
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocument,
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
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


class SceneAuthoringSession:
    """Transactional facade used by the viewport and numeric inspector."""

    def __init__(self, model: SceneAuthoringModel, *, max_history: int = 100) -> None:
        if max_history < 1:
            raise ValueError("max_history must be at least 1")
        self.model = model
        self.max_history = int(max_history)
        self._undo: list[_HistoryEntry] = []
        self._redo: list[_HistoryEntry] = []
        self._listeners: list[Callable[[], None]] = []
        self._gesture_before: SceneAuthoringSnapshot | None = None

    @property
    def document(self) -> SceneAuthoringDocument:
        return self.model.document

    @property
    def selection(self) -> SceneSelection:
        return self.model.selection

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

    def apply(self, operation: Callable[[], None], description: str) -> bool:
        """Run an operation atomically and place it in local history."""

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

    def restore_gesture_base(self) -> None:
        if self._gesture_before is None:
            raise RuntimeError("no authoring gesture is active")
        self._restore(self._gesture_before)
        self._notify()

    def finish_gesture(self, description: str) -> bool:
        if self._gesture_before is None:
            raise RuntimeError("no authoring gesture is active")
        before = self._gesture_before
        self._gesture_before = None
        changed = self._record(before, description)
        self._notify()
        return changed

    def cancel_gesture(self) -> None:
        if self._gesture_before is None:
            return
        before = self._gesture_before
        self._gesture_before = None
        self._restore(before)
        self._notify()

    def set_selection(
        self, object_ids: Iterable[str], primary: str | None = None
    ) -> SceneSelection:
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
        return self.apply(
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
        return self.apply(
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
        return self.apply(
            lambda: self.model.update_transform(object_id, transform),
            "Edit object transform",
        )

    def add_asset(self, asset: AssetReferenceRecord) -> bool:
        return self.apply(
            lambda: self.model.add_asset(asset),
            "Import scene asset",
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

    def set_snap(self, snap: SceneSnapRecord) -> bool:
        return self.apply(
            lambda: self.model.set_snap(snap),
            "Edit snapping",
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

    def undo(self) -> bool:
        if not self._undo:
            return False
        entry = self._undo.pop()
        self._restore(entry.before)
        self._redo.append(entry)
        self._notify()
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        entry = self._redo.pop()
        self._restore(entry.after)
        self._undo.append(entry)
        self._notify()
        return True

    def clear_history(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._gesture_before = None
        self._notify()
