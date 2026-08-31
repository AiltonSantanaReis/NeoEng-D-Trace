"""Contract tests for the isolated P2D-05 O-1 history fast path."""

from __future__ import annotations

import pytest

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import (
    SceneAuthoringSession,
    _TransformHistoryEntry,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import serialize_scene_authoring
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)

SHA = "a" * 64


def _transform(x: float, y: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=2.0),
        rotation=Point3Record(x=0.0, y=0.0, z=15.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
        flip_x=False,
        flip_y=True,
    )


def _document(*, locked: bool = False) -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-05 O-1 test",
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/object.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer", locked=locked)],
        objects=[
            SceneObjectAuthoringRecord(
                id="object_a",
                asset_id="asset",
                layer_id="layer",
                transform=_transform(10.0, 20.0),
            ),
            SceneObjectAuthoringRecord(
                id="object_b",
                asset_id="asset",
                layer_id="layer",
                transform=_transform(30.0, 20.0),
            ),
        ],
        groups=[],
    )


def test_transform_history_round_trips_bytes_and_mixed_history() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["object_a", "object_b"], "object_b")
    before = serialize_scene_authoring(session.document)

    assert session.translate_selected(Point3Record(x=5.0, y=-3.0, z=1.0))
    assert isinstance(session._undo[-1], _TransformHistoryEntry)
    transformed = serialize_scene_authoring(session.document)
    assert transformed != before

    assert session.rename_layer("layer", "Renamed")
    assert not isinstance(session._undo[-1], _TransformHistoryEntry)
    assert session.undo() is True
    assert session.document.layers[0].name == "Layer"
    assert serialize_scene_authoring(session.document) == transformed
    assert session.undo() is True
    assert serialize_scene_authoring(session.document) == before
    assert session.selection.ids == ("object_a", "object_b")
    assert session.selection.primary == "object_b"

    assert session.redo() is True
    assert serialize_scene_authoring(session.document) == transformed
    assert session.redo() is True
    assert session.document.layers[0].name == "Renamed"


def test_gesture_preview_keeps_full_restore_and_commits_delta() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["object_a"])
    session.begin_gesture()
    session.preview_transform_selected(translation=Point3Record(x=4.0, y=1.0, z=0.0))
    session.preview_transform_selected(translation=Point3Record(x=8.0, y=2.0, z=0.0))
    assert session.finish_gesture("Move object") is True
    assert isinstance(session._undo[-1], _TransformHistoryEntry)
    assert session.undo() is True
    assert session.document.objects[0].transform.position == Point3Record(
        x=10.0, y=20.0, z=2.0
    )


def test_generic_operation_inside_gesture_keeps_full_restore_fallback() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["object_a"])
    before = serialize_scene_authoring(session.document)
    session.begin_gesture()
    session.rename_layer("layer", "Temporary")
    session.cancel_gesture()
    assert serialize_scene_authoring(session.document) == before


def test_transform_failure_preserves_document_and_history() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document(locked=True)))
    session.set_selection(["object_a"])
    before = serialize_scene_authoring(session.document)
    with pytest.raises(PermissionError, match="layer"):
        session.translate_selected(Point3Record(x=1.0, y=0.0, z=0.0))
    assert serialize_scene_authoring(session.document) == before
    assert session.undo_count == 0
    assert session.redo_count == 0
