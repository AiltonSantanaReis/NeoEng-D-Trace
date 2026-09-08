"""Qt-independent lifecycle for new, open, save and save-as scenes."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

from src.core.independent_scene_authoring import IndependentSceneAuthoringModel
from src.persistence.independent_scene_io import (
    IndependentSceneWriteError,
    independent_scene_sha256,
    load_independent_scene,
    save_independent_scene,
)
from src.persistence.independent_scene_schema import (
    INDEPENDENT_SCENE_FILE_EXTENSION,
    IndependentSceneCameraRecord,
    IndependentSceneDocument,
    IndependentSceneDocumentV2,
    IndependentScenePrimitiveRecord,
    IndependentScenePrimitiveTransformRecord,
    SceneResolutionRecord,
    default_independent_scene_document_v2,
    upgrade_independent_scene_document,
)
from src.persistence.project_schema import PointRecord


class IndependentSceneSession:
    """Own document state without a project/image reference or Qt dependency."""

    def __init__(
        self,
        document: IndependentSceneDocument | None = None,
        *,
        last_folder: str | None = None,
    ) -> None:
        self.document = document or default_independent_scene_document_v2()
        self.path: Path | None = None
        self.last_folder = last_folder
        self.persisted_file_sha256: str | None = None
        self.clean_signature = independent_scene_sha256(self.document)
        self._undo: list[IndependentSceneDocumentV2] = []
        self._redo: list[IndependentSceneDocumentV2] = []
        self._selection: tuple[str, ...] = ()

    @property
    def document_name(self) -> str:
        return self.document.metadata.name

    @property
    def is_modified(self) -> bool:
        return independent_scene_sha256(self.document) != self.clean_signature

    def new(
        self,
        *,
        name: str = "Untitled Scene",
        width: int = 1920,
        height: int = 1080,
    ) -> IndependentSceneDocumentV2:
        self.document = default_independent_scene_document_v2(
            name=name,
            width=width,
            height=height,
        )
        self.path = None
        self.persisted_file_sha256 = None
        self.clean_signature = independent_scene_sha256(self.document)
        self._undo.clear()
        self._redo.clear()
        self._selection = ()
        return self.document

    def update_document(self, document: IndependentSceneDocument) -> None:
        self.document = document
        self._undo.clear()
        self._redo.clear()
        self._selection = tuple(
            item.id
            for item in getattr(document, "objects", [])
            if item.id in self._selection
        )

    def _authoring_document(self) -> IndependentSceneDocumentV2:
        upgraded = upgrade_independent_scene_document(self.document)
        if upgraded is not self.document:
            self.document = upgraded
        return upgraded

    def _mutate_authoring(self, operation):
        before = upgrade_independent_scene_document(self.document).model_copy(deep=True)
        model = IndependentSceneAuthoringModel(before)
        model.set_selection(
            item
            for item in self._selection
            if any(primitive.id == item for primitive in before.objects)
        )
        result = operation(model)
        self._selection = model.selection
        if model.document != before:
            self.document = model.document
            self._undo.append(before)
            self._redo.clear()
        return result

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    @property
    def object_count(self) -> int:
        return len(getattr(self.document, "objects", []))

    @property
    def selection(self) -> tuple[str, ...]:
        return self._selection

    def set_selection(self, primitive_ids: Sequence[str]) -> tuple[str, ...]:
        return self._mutate_authoring(lambda model: model.set_selection(primitive_ids))

    def clear_selection(self) -> None:
        self._selection = ()

    def add_primitive(
        self,
        *,
        kind: str,
        points: Sequence,
        name: str | None = None,
        primitive_id: str | None = None,
        closed: bool | None = None,
        filled: bool | None = None,
    ) -> IndependentScenePrimitiveRecord:
        return self._mutate_authoring(
            lambda model: model.add_primitive(
                kind=kind,
                points=points,
                name=name,
                primitive_id=primitive_id,
                closed=closed,
                filled=filled,
            )
        )

    def update_primitive_transform(
        self,
        primitive_id: str,
        transform: IndependentScenePrimitiveTransformRecord,
    ) -> IndependentScenePrimitiveRecord:
        return self._mutate_authoring(
            lambda model: model.update_transform(primitive_id, transform)
        )

    def update_primitive_geometry(
        self,
        primitive_id: str,
        *,
        points: Sequence,
        closed: bool | None = None,
        filled: bool | None = None,
    ) -> IndependentScenePrimitiveRecord:
        return self._mutate_authoring(
            lambda model: model.update_geometry(
                primitive_id,
                points=points,
                closed=closed,
                filled=filled,
            )
        )

    def remove_primitive(self, primitive_id: str) -> None:
        self._mutate_authoring(lambda model: model.remove_primitive(primitive_id))

    def duplicate_primitive(
        self,
        primitive_id: str,
        *,
        new_id: str | None = None,
    ) -> IndependentScenePrimitiveRecord:
        return self._mutate_authoring(
            lambda model: model.duplicate_primitive(primitive_id, new_id=new_id)
        )

    def translate_selection(self, *, delta_x: float, delta_y: float) -> tuple[str, ...]:
        return self._mutate_authoring(
            lambda model: model.translate_selection(
                delta_x=delta_x,
                delta_y=delta_y,
            )
        )

    def duplicate_selection(self) -> tuple[IndependentScenePrimitiveRecord, ...]:
        return self._mutate_authoring(lambda model: model.duplicate_selection())

    def remove_selection(self) -> tuple[str, ...]:
        return self._mutate_authoring(lambda model: model.remove_selection())

    def undo(self) -> bool:
        if not self._undo:
            return False
        current = upgrade_independent_scene_document(self.document).model_copy(
            deep=True
        )
        self._redo.append(current)
        self.document = self._undo.pop()
        self._selection = tuple(
            item
            for item in self._selection
            if item in {obj.id for obj in self.document.objects}
        )
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        current = upgrade_independent_scene_document(self.document).model_copy(
            deep=True
        )
        self._undo.append(current)
        self.document = self._redo.pop()
        self._selection = tuple(
            item
            for item in self._selection
            if item in {obj.id for obj in self.document.objects}
        )
        return True

    def set_resolution(self, width: int, height: int) -> None:
        self.document = type(self.document).model_validate(
            self.document.model_copy(
                update={"resolution": SceneResolutionRecord(width=width, height=height)}
            ),
            strict=True,
        )

    def set_camera(self, *, x: float, y: float, zoom: float) -> None:
        self.document = type(self.document).model_validate(
            self.document.model_copy(
                update={
                    "camera": IndependentSceneCameraRecord(
                        position=PointRecord(x=x, y=y),
                        zoom=zoom,
                    )
                }
            ),
            strict=True,
        )

    def normalized_path(self, path: str | Path) -> Path:
        destination = Path(path)
        if destination.suffix.lower() != INDEPENDENT_SCENE_FILE_EXTENSION:
            destination = destination.with_suffix(INDEPENDENT_SCENE_FILE_EXTENSION)
        return destination

    def dialog_start(self) -> str:
        if self.path is not None:
            return str(self.path)
        base = Path(self.last_folder) if self.last_folder else Path.cwd()
        return str(base / f"{self.document_name}{INDEPENDENT_SCENE_FILE_EXTENSION}")

    def save(self, path: str | Path | None = None) -> Path:
        destination = self.normalized_path(path or self.path or self.dialog_start())
        resolved_destination = destination.resolve(strict=False)
        if (
            self.path is not None
            and resolved_destination == self.path
            and self.persisted_file_sha256 is not None
        ):
            if not destination.is_file():
                raise IndependentSceneWriteError(
                    "independent scene file changed externally or was removed"
                )
            current_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
            if current_hash != self.persisted_file_sha256:
                raise IndependentSceneWriteError(
                    "independent scene file changed externally; refusing to overwrite"
                )
        save_independent_scene(self.document, destination)
        self.path = resolved_destination
        self.last_folder = str(self.path.parent)
        self.persisted_file_sha256 = hashlib.sha256(
            destination.read_bytes()
        ).hexdigest()
        self.clean_signature = independent_scene_sha256(self.document)
        self._undo.clear()
        self._redo.clear()
        return self.path

    def save_as(self, path: str | Path) -> Path:
        return self.save(path)

    def load(self, path: str | Path) -> IndependentSceneDocument:
        destination = self.normalized_path(path).resolve(strict=False)
        document = load_independent_scene(destination)
        self.document = document
        self.path = destination
        self.last_folder = str(destination.parent)
        self.persisted_file_sha256 = hashlib.sha256(
            destination.read_bytes()
        ).hexdigest()
        self.clean_signature = independent_scene_sha256(document)
        self._undo.clear()
        self._redo.clear()
        self._selection = ()
        return document


__all__ = ["IndependentSceneSession"]
