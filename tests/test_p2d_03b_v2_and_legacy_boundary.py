from __future__ import annotations

import pytest

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)


SHA = "1" * 64


def _transform(x: float, y: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _v2_session() -> SceneAuthoringSession:
    document = SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-03B V2", generator="test", app_version="0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[
            SceneObjectAuthoringRecord(
                id="a", asset_id="asset", layer_id="layer", transform=_transform(0, 0)
            ),
            SceneObjectAuthoringRecord(
                id="b", asset_id="asset", layer_id="layer", transform=_transform(10, 5)
            ),
        ],
        groups=[
            SceneGroupAuthoringRecordV2(
                id="parent", name="Parent", members=["a"]
            ),
            SceneGroupAuthoringRecordV2(
                id="child", name="Child", members=["b"], parent_group_id="parent"
            ),
        ],
    )
    return SceneAuthoringSession(SceneAuthoringModel(document))


def test_v2_paste_clones_complete_nested_group_hierarchy():
    session = _v2_session()
    session.set_selection(["a", "b"])

    created = session.paste_payload(session.copy_selected_payload())

    assert created == ("a__copy", "b__copy")
    assert [group.id for group in session.document.groups] == [
        "parent",
        "child",
        "parent__copy",
        "child__copy",
    ]
    assert session.document.groups[2].members == ["a__copy"]
    assert session.document.groups[2].parent_group_id is None
    assert session.document.groups[3].members == ["b__copy"]
    assert session.document.groups[3].parent_group_id == "parent__copy"


def test_existing_unitary_session_delete_obeys_professional_lock_contract():
    session = _v2_session()
    session.model.document = session.document.model_copy(
        update={"objects": [session.document.objects[0].model_copy(update={"locked": True}), session.document.objects[1]]}
    )
    before = session.document.model_copy(deep=True)

    with pytest.raises(PermissionError):
        session.remove_object("a")

    assert session.document == before
    assert session.undo_count == 0
