"""Qt-independent document state and persistence path coordination."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from src.persistence import PROJECT_FILE_EXTENSION, build_project_document
from src.persistence.errors import ProjectValidationError


class DocumentSession:
    def __init__(
        self,
        scene: Any,
        *,
        last_folder: str | None = None,
    ) -> None:
        self.scene = scene
        self.project_path: Path | None = None
        self.document_name: str | None = None
        self.last_folder = last_folder
        self.clean_signature: str | None = None

    def signature_path_hint(self) -> Path:
        if self.project_path is not None:
            return self.project_path
        image_path = getattr(self.scene, "image_path", None)
        if image_path:
            candidate = Path(os.fsdecode(image_path))
            if candidate.is_absolute():
                return candidate.parent / f"untitled{PROJECT_FILE_EXTENSION}"
        return Path.cwd() / f"untitled{PROJECT_FILE_EXTENSION}"

    def compute_signature(self) -> str:
        try:
            document = build_project_document(self.scene, self.signature_path_hint())
        except ProjectValidationError:
            return self.compute_unvalidated_signature()
        payload = json.dumps(
            document.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def compute_unvalidated_signature(self) -> str:
        image_path = getattr(self.scene, "image_path", None)
        snapshot = (
            os.fsdecode(image_path) if image_path is not None else None,
            getattr(self.scene, "image_path_kind", None),
            getattr(self.scene, "image_sha256", None),
            tuple(
                (layer.id, layer.name, layer.visible, layer.locked)
                for layer in self.scene.layers
            ),
            tuple(
                (
                    object_id,
                    obj.id,
                    obj.layer_id,
                    tuple(obj.polygon),
                    tuple(tuple(segment) for segment in (obj.beziers or [])),
                )
                for object_id, obj in self.scene.objects.items()
            ),
            tuple(
                (
                    group.id,
                    group.name,
                    group.visible,
                    group.locked,
                    tuple(group.members),
                )
                for group in self.scene.groups
            ),
            tuple(
                (object_id, tuple(shape))
                for object_id, shape in self.scene.collision_shapes.items()
            ),
        )
        return hashlib.sha256(repr(snapshot).encode("utf-8")).hexdigest()

    def is_modified(self) -> bool:
        if self.clean_signature is None:
            return bool(
                self.document_name
                or getattr(self.scene, "image_path", None)
                or self.scene.objects
                or self.scene.groups
                or self.scene.collision_shapes
            )
        try:
            return self.compute_signature() != self.clean_signature
        except Exception:
            return True

    def mark_clean(self) -> None:
        self.clean_signature = self.compute_signature()

    def mark_unsaved(self) -> None:
        self.clean_signature = None

    def normalized_project_path(self, path: str | os.PathLike[str]) -> Path:
        destination = Path(path)
        if destination.suffix.lower() != PROJECT_FILE_EXTENSION:
            destination = destination.with_suffix(PROJECT_FILE_EXTENSION)
        return destination

    def project_dialog_start(self) -> str:
        if self.project_path is not None:
            return str(self.project_path)
        base = Path(self.last_folder) if self.last_folder else Path.cwd()
        stem = Path(self.document_name).stem if self.document_name else "project"
        return str(base / f"{stem}{PROJECT_FILE_EXTENSION}")

    def rebase_image_reference_for_save(
        self,
        destination: Path,
    ) -> tuple[object, ...]:
        original = (
            getattr(self.scene, "image_path", None),
            getattr(self.scene, "image_path_kind", None),
            getattr(self.scene, "image_sha256", None),
            getattr(self.scene, "_image_reference_loaded", False),
        )
        if (
            self.project_path is None
            or getattr(self.scene, "image_path", None) is None
            or getattr(self.scene, "image_path_kind", None) != "relative"
        ):
            return original

        source = (
            self.project_path.parent / os.fsdecode(self.scene.image_path)
        ).resolve(strict=False)
        destination_parent = destination.parent.resolve(strict=False)
        try:
            relative = source.relative_to(destination_parent)
        except ValueError:
            self.scene.image_path = str(source)
            self.scene.image_path_kind = "absolute"
        else:
            self.scene.image_path = relative.as_posix()
            self.scene.image_path_kind = "relative"
        return original

    def restore_image_reference(self, original: tuple[object, ...]) -> None:
        (
            self.scene.image_path,
            self.scene.image_path_kind,
            self.scene.image_sha256,
            self.scene._image_reference_loaded,
        ) = original
