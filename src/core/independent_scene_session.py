"""Qt-independent lifecycle for new, open, save and save-as scenes."""

from __future__ import annotations

from pathlib import Path

from src.persistence.independent_scene_io import (
    independent_scene_sha256,
    load_independent_scene,
    save_independent_scene,
)
from src.persistence.independent_scene_schema import (
    INDEPENDENT_SCENE_FILE_EXTENSION,
    IndependentSceneCameraRecord,
    IndependentSceneDocumentV1,
    SceneResolutionRecord,
    default_independent_scene_document,
)


class IndependentSceneSession:
    """Own document state without a project/image reference or Qt dependency."""

    def __init__(
        self,
        document: IndependentSceneDocumentV1 | None = None,
        *,
        last_folder: str | None = None,
    ) -> None:
        self.document = document or default_independent_scene_document()
        self.path: Path | None = None
        self.last_folder = last_folder
        self.clean_signature = independent_scene_sha256(self.document)

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
    ) -> IndependentSceneDocumentV1:
        self.document = default_independent_scene_document(
            name=name,
            width=width,
            height=height,
        )
        self.path = None
        self.clean_signature = independent_scene_sha256(self.document)
        return self.document

    def update_document(self, document: IndependentSceneDocumentV1) -> None:
        self.document = IndependentSceneDocumentV1.model_validate(
            document,
            strict=True,
        )

    def set_resolution(self, width: int, height: int) -> None:
        self.document = IndependentSceneDocumentV1.model_validate(
            self.document.model_copy(
                update={"resolution": SceneResolutionRecord(width=width, height=height)}
            ),
            strict=True,
        )

    def set_camera(self, *, x: float, y: float, zoom: float) -> None:
        self.document = IndependentSceneDocumentV1.model_validate(
            self.document.model_copy(
                update={
                    "camera": IndependentSceneCameraRecord(
                        position={"x": x, "y": y},
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
        save_independent_scene(self.document, destination)
        self.path = destination.resolve(strict=False)
        self.last_folder = str(self.path.parent)
        self.clean_signature = independent_scene_sha256(self.document)
        return self.path

    def save_as(self, path: str | Path) -> Path:
        return self.save(path)

    def load(self, path: str | Path) -> IndependentSceneDocumentV1:
        destination = self.normalized_path(path).resolve(strict=False)
        document = load_independent_scene(destination)
        self.document = document
        self.path = destination
        self.last_folder = str(destination.parent)
        self.clean_signature = independent_scene_sha256(document)
        return document


__all__ = ["IndependentSceneSession"]
