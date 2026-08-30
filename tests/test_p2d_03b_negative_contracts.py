from __future__ import annotations

import json

import pytest

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneGroupAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)

SHA = "f" * 64


def _transform(x: float = 0.0, y: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _session(*, group: bool = False) -> SceneAuthoringSession:
    document = SceneAuthoringDocumentV1(
        metadata={"name": "P2D-03B negative", "generator": "test", "app_version": "0"},
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[
            SceneObjectAuthoringRecord(
                id="a", asset_id="asset", layer_id="layer", transform=_transform()
            ),
            SceneObjectAuthoringRecord(
                id="b", asset_id="asset", layer_id="layer", transform=_transform(10, 5)
            ),
        ],
        groups=(
            [SceneGroupAuthoringRecord(id="group", name="Group", members=["a", "b"])]
            if group
            else []
        ),
    )
    return SceneAuthoringSession(SceneAuthoringModel(document))


def test_empty_commands_are_noops_without_history():
    session = _session()

    assert session.nudge_selected(Point3Record(x=1.0, y=0.0, z=0.0)) is False
    assert session.duplicate_selected() == ()
    assert session.delete_selected() is False
    assert session.copy_selected_payload() is None
    assert session.undo_count == 0
    assert session.redo_count == 0


@pytest.mark.parametrize("locked_kind", ["object", "layer", "group"])
def test_duplicate_preflights_every_lock_kind_without_mutation(locked_kind: str):
    session = _session(group=locked_kind == "group")
    if locked_kind == "object":
        session.model.document = session.document.model_copy(
            update={
                "objects": [
                    session.document.objects[0].model_copy(update={"locked": True}),
                    session.document.objects[1],
                ]
            }
        )
    elif locked_kind == "layer":
        session.model.document = session.document.model_copy(
            update={
                "layers": [
                    session.document.layers[0].model_copy(update={"locked": True})
                ]
            }
        )
    else:
        session.model.document = session.document.model_copy(
            update={
                "groups": [
                    session.document.groups[0].model_copy(update={"locked": True})
                ]
            }
        )
    session.set_selection(["a", "b"])
    before = session.document.model_copy(deep=True)

    with pytest.raises(PermissionError):
        session.duplicate_selected()

    assert session.document == before
    assert session.selection.ids == ("a", "b")
    assert session.undo_count == 0


def test_delete_preflights_locked_group_without_mutation():
    session = _session(group=True)
    session.model.document = session.document.model_copy(
        update={
            "groups": [session.document.groups[0].model_copy(update={"locked": True})]
        }
    )
    session.set_selection(["a", "b"])
    before = session.document.model_copy(deep=True)

    with pytest.raises(PermissionError):
        session.delete_selected()

    assert session.document == before
    assert session.undo_count == 0


def test_paste_rejects_missing_reference_without_mutation():
    session = _session()
    session.set_selection(["a"])
    payload = json.loads(session.copy_selected_payload().decode("utf-8"))
    payload["objects"][0]["asset_id"] = "missing-asset"
    before = session.document.model_copy(deep=True)

    with pytest.raises(ValueError, match="missing-asset"):
        session.paste_payload(json.dumps(payload).encode("utf-8"))

    assert session.document == before
    assert session.selection.ids == ("a",)
    assert session.undo_count == 0


@pytest.mark.parametrize(
    "change",
    [
        lambda payload: payload.update({"format_id": "other-format"}),
        lambda payload: payload.update({"schema_version": 999}),
        lambda payload: payload["objects"][0].update({"unexpected": True}),
    ],
)
def test_paste_rejects_incompatible_payloads_atomically(change):
    session = _session()
    session.set_selection(["a"])
    payload = json.loads(session.copy_selected_payload().decode("utf-8"))
    change(payload)
    before = session.document.model_copy(deep=True)

    with pytest.raises(ValueError):
        session.paste_payload(json.dumps(payload).encode("utf-8"))

    assert session.document == before
    assert session.undo_count == 0


def test_allocator_resolves_current_id_collision_deterministically():
    session = _session()
    session.model.add_object(
        session.document.objects[0].model_copy(
            update={"id": "a__copy", "transform": _transform(50.0, 50.0)}
        )
    )
    session.set_selection(["a"])

    assert session.duplicate_selected() == ("a__copy_2",)
