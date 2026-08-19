"""Factory for the in-memory professional authoring document."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from src.models.scene import Scene
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_io import project_reference_for
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneGroupAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    default_scene_authoring_metadata,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_asset(project_path: Path, raw_path: Any) -> tuple[str, str] | None:
    if raw_path is None:
        return None
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = project_path.parent / candidate
    candidate = candidate.resolve(strict=False)
    if not candidate.is_file():
        return None
    try:
        relative = candidate.relative_to(project_path.parent.resolve())
    except ValueError:
        return None
    portable = PurePosixPath(relative.as_posix())
    if portable.is_absolute() or ".." in portable.parts:
        return None
    return portable.as_posix(), _sha256(candidate)


def document_from_scene(
    scene: Scene,
    project_path: Path,
    *,
    name: str | None = None,
) -> SceneAuthoringDocumentV1:
    """Build a strict authoring document without inventing asset references.

    The current project image is the only asset that can be derived safely from
    the existing project contract. Objects are included only when that image
    reference is relative, present and hashable. Later stages can add explicit
    multi-asset import while preserving this document's strictness.
    """

    project = Path(project_path).resolve(strict=False)
    asset_info = _relative_asset(project, getattr(scene, "image_path", None))
    assets: list[AssetReferenceRecord] = []
    asset_id = "project_image"
    if asset_info is not None:
        path, digest = asset_info
        assets.append(
            AssetReferenceRecord(
                id=asset_id,
                path=path,
                sha256=digest,
            )
        )

    layers = [
        SceneLayerAuthoringRecord(
            id=layer.id,
            name=layer.name,
            visible=bool(layer.visible),
            locked=bool(layer.locked),
        )
        for layer in scene.layers
    ]
    if not layers:
        layers = [SceneLayerAuthoringRecord(id="layer_default", name="Default")]

    known_layers = {item.id for item in layers}
    objects: list[SceneObjectAuthoringRecord] = []
    if assets:
        for object_id, item in scene.objects.items():
            layer_id = item.layer_id if item.layer_id in known_layers else layers[0].id
            objects.append(
                SceneObjectAuthoringRecord(
                    id=object_id,
                    asset_id=asset_id,
                    layer_id=layer_id,
                    transform=SceneTransformRecord(
                        position=Point3Record(
                            x=float(item.position[0]),
                            y=float(item.position[1]),
                            z=float(item.position[2]),
                        ),
                        rotation=Point3Record(
                            x=float(item.rotation[0]),
                            y=float(item.rotation[1]),
                            z=float(item.rotation[2]),
                        ),
                        scale=Point3Record(
                            x=float(item.scale[0]),
                            y=float(item.scale[1]),
                            z=float(item.scale[2]),
                        ),
                        pivot=PointRecord(
                            x=float(item.pivot[0]),
                            y=float(item.pivot[1]),
                        ),
                    ),
                )
            )

    groups = [
        SceneGroupAuthoringRecord(
            id=group.id,
            name=group.name,
            members=[
                member for member in group.members if member in {o.id for o in objects}
            ],
            visible=bool(group.visible),
            locked=bool(group.locked),
        )
        for group in scene.groups
        if any(member in {o.id for o in objects} for member in group.members)
    ]
    return SceneAuthoringDocumentV1(
        metadata=default_scene_authoring_metadata(name or project.stem),
        project=project_reference_for(project),
        assets=assets,
        layers=layers,
        objects=objects,
        groups=groups,
    )
