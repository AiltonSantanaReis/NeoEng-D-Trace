"""E09-C collision, authored-object and persistence contracts."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.vector_scene_resource import (
    build_vector_geometry,
    create_vector_scene_object,
)
from src.core.vectorization import VectorizationError, vectorize_image_file
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import (
    SceneAuthoringAssetError,
    load_scene_authoring,
    save_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneTransformRecord,
)


def _source(tmp_path: Path):
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    assert ok
    project = tmp_path / "project"
    asset_path = project / "assets" / "scene" / "subject.png"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(encoded.tobytes())
    return project, asset_path, vectorize_image_file(asset_path)


def _transform() -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=20.0, y=30.0, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document(project: Path, asset_path: Path) -> SceneAuthoringDocumentV1:
    asset = AssetReferenceRecord(
        id="subject",
        path=asset_path.relative_to(project).as_posix(),
        sha256=hashlib.sha256(asset_path.read_bytes()).hexdigest(),
    )
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="E09 vector", generator="NeoEng-D-Trace", app_version="0.3.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[asset],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[],
        groups=[],
    )


def test_build_vector_geometry_preserves_edit_and_generates_collision(
    tmp_path: Path,
) -> None:
    _, _, result = _source(tmp_path)
    edited = [(24, 18), (110, 20), (103, 77), (24, 77)]
    geometry = build_vector_geometry(result, edited, collision_strategy="convex_hull")

    assert geometry.source_sha256 == result.source_sha256
    assert len(geometry.original_polygon) == 4
    assert geometry.polygon[1].x == 110
    assert len(geometry.collision_polygon) == 4
    assert geometry.detection_parameters["collision_strategy"] == "convex_hull"


def test_invalid_edited_geometry_never_creates_an_object(tmp_path: Path) -> None:
    project, asset_path, result = _source(tmp_path)
    with pytest.raises(VectorizationError, match="invalid_geometry"):
        create_vector_scene_object(
            result,
            object_id="subject-object",
            asset_id="subject",
            layer_id="foreground",
            transform=_transform(),
            edited_polygon=[(24, 18), (10, 90), (103, 77), (24, 77)],
        )
    assert not (project / "scene.ndtscene.json").exists()


def test_vector_object_undo_redo_duplicate_and_save_reopen(tmp_path: Path) -> None:
    project, asset_path, result = _source(tmp_path)
    session = SceneAuthoringSession(SceneAuthoringModel(_document(project, asset_path)))
    assert session.add_vector_object(
        result,
        object_id="subject-object",
        asset_id="subject",
        layer_id="foreground",
        transform=_transform(),
    )
    assert session.document.objects[0].vector_geometry is not None
    assert session.document.objects[0].vector_geometry.collision_polygon
    assert session.undo()
    assert not session.document.objects
    assert session.redo()
    session.set_selection(["subject-object"])
    assert session.duplicate_selected()
    assert len(session.document.objects) == 2

    path = project / "scene.ndtscene.json"
    save_scene_authoring(session.document, path)
    restored = load_scene_authoring(path)
    assert len(restored.objects) == 2
    assert restored.objects[1].vector_geometry == restored.objects[0].vector_geometry


def test_vector_object_persistence_rejects_tampered_source_asset(
    tmp_path: Path,
) -> None:
    project, asset_path, result = _source(tmp_path)
    session = SceneAuthoringSession(SceneAuthoringModel(_document(project, asset_path)))
    session.add_vector_object(
        result,
        object_id="subject-object",
        asset_id="subject",
        layer_id="foreground",
        transform=_transform(),
    )
    path = project / "scene.ndtscene.json"
    save_scene_authoring(session.document, path)
    asset_path.write_bytes(b"tampered")
    with pytest.raises(SceneAuthoringAssetError, match="asset hash"):
        load_scene_authoring(path)
