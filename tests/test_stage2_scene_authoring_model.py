"""Positive and negative contract tests for the professional scene model."""

from __future__ import annotations

import pytest

from src.core.scene_authoring_model import (
    SceneAuthoringModel,
    SceneSelection,
    snap_transform,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneGroupAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneSnapRecord,
    SceneTransformRecord,
)

SHA = "a" * 64


def _transform(x: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=2.0, z=3.0),
        rotation=Point3Record(x=0.0, y=0.0, z=45.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=1.0),
    )


def _document() -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Authoring test", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="tree", path="assets/tree.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="background", name="Background")],
        objects=[],
        groups=[],
    )


def _object(object_id: str = "tree-1") -> SceneObjectAuthoringRecord:
    return SceneObjectAuthoringRecord(
        id=object_id,
        asset_id="tree",
        layer_id="background",
        transform=_transform(),
    )


def test_contract_is_separate_and_references_are_explicit() -> None:
    document = _document()
    assert document.format_id == "neoeng-d-trace-scene-authoring"
    assert document.schema_version == 1
    assert document.project.schema_version == 1
    assert document.assets[0].path == "assets/tree.png"


@pytest.mark.parametrize("path", ["C:/asset.png", "/asset.png", "../asset.png", ""])
def test_asset_paths_must_be_portable_relative_paths(path: str) -> None:
    with pytest.raises(ValueError, match="relative|blank|escape|at least"):
        AssetReferenceRecord(id="asset", path=path, sha256=SHA)


def test_transform_rejects_invalid_scale_and_pivot() -> None:
    with pytest.raises(ValueError, match="positive"):
        SceneTransformRecord(
            position=Point3Record(x=0.0, y=0.0, z=0.0),
            rotation=Point3Record(x=0.0, y=0.0, z=0.0),
            scale=Point3Record(x=0.0, y=1.0, z=1.0),
            pivot=PointRecord(x=0.5, y=0.5),
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        SceneTransformRecord(
            position=Point3Record(x=0, y=0, z=0),
            rotation=Point3Record(x=0, y=0, z=0),
            scale=Point3Record(x=1, y=1, z=1),
            pivot=PointRecord(x=1.1, y=0.5),
        )


def test_document_rejects_unknown_asset_and_layer() -> None:
    with pytest.raises(ValueError, match="unknown asset"):
        SceneAuthoringDocumentV1(
            **{
                **_document().model_dump(),
                "objects": [_object().model_copy(update={"asset_id": "missing"})],
            }
        )
    with pytest.raises(ValueError, match="unknown layer"):
        SceneAuthoringDocumentV1(
            **{
                **_document().model_dump(),
                "objects": [_object().model_copy(update={"layer_id": "missing"})],
            }
        )


def test_model_supports_selection_objects_groups_and_transform_updates() -> None:
    model = SceneAuthoringModel(_document())
    model.add_object(_object("tree-1"), select=True)
    model.add_object(_object("tree-2"))
    assert model.selection == SceneSelection(ids=("tree-1",), primary="tree-1")

    model.set_selection(["tree-2", "tree-1"], primary="tree-2")
    model.translate_selected(Point3Record(x=10.0, y=0.0, z=0.0))
    assert [item.transform.position.x for item in model.document.objects] == [
        10.0,
        10.0,
    ]

    model.group_selection(
        SceneGroupAuthoringRecord(id="trees", name="Trees", members=[])
    )
    assert model.document.groups[0].members == ["tree-2", "tree-1"]


def test_selection_rejects_unknown_objects_and_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        SceneSelection(ids=("a", "a"))
    model = SceneAuthoringModel(_document())
    with pytest.raises(KeyError, match="missing"):
        model.set_selection(["missing"])


def test_snapping_is_deterministic_and_disabled_state_is_lossless() -> None:
    transform = _transform(12.6)
    snapped = snap_transform(
        transform,
        SceneSnapRecord(enabled=True, mode="grid", spacing=PointRecord(x=5, y=2)),
    )
    assert snapped.position.x == 15.0
    assert snap_transform(transform, SceneSnapRecord(enabled=False)) == transform


def test_snap_spacing_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        SceneSnapRecord(spacing=PointRecord(x=0, y=1))


def test_relative_translation_preserves_offsets_and_locked_objects_are_rejected() -> (
    None
):
    model = SceneAuthoringModel(_document())
    model.add_object(_object("tree-1"))
    model.add_object(
        _object("tree-2").model_copy(update={"transform": _transform(20.0)})
    )
    model.set_selection(["tree-1", "tree-2"])
    model.translate_selected(Point3Record(x=5.0, y=-1.0, z=2.0))
    assert [item.transform.position.x for item in model.document.objects] == [5.0, 25.0]
    assert [item.transform.position.z for item in model.document.objects] == [5.0, 5.0]

    locked = SceneAuthoringModel(_document())
    locked.add_object(_object().model_copy(update={"locked": True}), select=True)
    with pytest.raises(PermissionError, match="locked"):
        locked.translate_selected(Point3Record(x=1.0, y=0.0, z=0.0))


def test_remove_object_updates_groups_and_selection_without_dangling_references() -> (
    None
):
    model = SceneAuthoringModel(_document())
    model.add_object(_object("tree-1"), select=True)
    model.add_object(_object("tree-2"))
    model.set_selection(["tree-1", "tree-2"])
    model.group_selection(
        SceneGroupAuthoringRecord(id="trees", name="Trees", members=[])
    )
    model.remove_object("tree-1")
    assert [item.id for item in model.document.objects] == ["tree-2"]
    assert model.document.groups[0].members == ["tree-2"]
    assert model.selection == SceneSelection(ids=("tree-2",), primary="tree-2")


def test_model_rejects_duplicate_assets_objects_groups_and_missing_objects() -> None:
    model = SceneAuthoringModel(_document())
    asset = AssetReferenceRecord(id="rock", path="assets/rock.png", sha256=SHA)
    model.add_asset(asset)
    with pytest.raises(ValueError, match="asset ID exists"):
        model.add_asset(asset)

    model.add_object(_object("tree-1"))
    with pytest.raises(ValueError, match="object ID exists"):
        model.add_object(_object("tree-1"))
    with pytest.raises(KeyError, match="tree-missing"):
        model.remove_object("tree-missing")
    with pytest.raises(KeyError, match="tree-missing"):
        model.update_transform("tree-missing", _transform())
    with pytest.raises(KeyError, match="member"):
        model.add_group(
            SceneGroupAuthoringRecord(
                id="bad-group", name="Bad", members=["tree-missing"]
            )
        )
    model.add_group(SceneGroupAuthoringRecord(id="trees", name="Trees", members=[]))
    with pytest.raises(ValueError, match="group ID exists"):
        model.add_group(SceneGroupAuthoringRecord(id="trees", name="Again", members=[]))


def test_model_handles_empty_selection_and_locked_layer() -> None:
    model = SceneAuthoringModel(_document())
    model.clear_selection()
    with pytest.raises(ValueError, match="empty selection"):
        model.group_selection(
            SceneGroupAuthoringRecord(id="empty", name="Empty", members=[])
        )

    locked_layer = _document().model_copy(
        update={
            "layers": [
                _document().layers[0].model_copy(update={"locked": True}),
            ],
        }
    )
    locked_model = SceneAuthoringModel(locked_layer)
    locked_model.add_object(_object(), select=True)
    with pytest.raises(PermissionError, match="layer"):
        locked_model.update_transform("tree-1", _transform(4.0))


def test_model_snap_update_and_unselected_objects_are_preserved() -> None:
    model = SceneAuthoringModel(_document())
    model.add_object(_object("tree-1"), select=True)
    model.add_object(
        _object("tree-2").model_copy(update={"transform": _transform(20.0)})
    )
    model.set_snap(
        SceneSnapRecord(enabled=True, mode="grid", spacing=PointRecord(x=5, y=2))
    )
    model.set_selection(["tree-1"])
    model.translate_selected(Point3Record(x=2.6, y=0.0, z=0.0))
    assert model.document.objects[0].transform.position.x == 5.0
    assert model.document.objects[1].transform.position.x == 20.0


def test_selection_primary_and_snap_value_reject_invalid_inputs() -> None:
    from src.core.scene_authoring_model import snap_value

    with pytest.raises(ValueError, match="primary"):
        SceneSelection(ids=("one",), primary="missing")
    with pytest.raises(ValueError, match="finite"):
        snap_value(float("nan"), 1)
    with pytest.raises(ValueError, match="finite"):
        snap_value(1, float("inf"))
    with pytest.raises(ValueError, match="finite"):
        snap_value(True, 1)


def test_schema_rejects_path_separators_and_invalid_group_members() -> None:
    with pytest.raises(ValueError, match="separators"):
        AssetReferenceRecord(id="asset", path="assets\\tree.png", sha256=SHA)
    with pytest.raises(ValueError, match="non-empty"):
        SceneGroupAuthoringRecord(id="bad", name="Bad", members=[""])
    with pytest.raises(ValueError, match="unique"):
        SceneGroupAuthoringRecord(id="bad", name="Bad", members=["a", "a"])


def test_schema_rejects_unknown_group_reference_and_invalid_numeric_helper_inputs() -> (
    None
):
    from src.persistence.scene_authoring_schema import _finite, _positive, _unit

    with pytest.raises(ValueError, match="unknown object"):
        SceneAuthoringDocumentV1(
            **{
                **_document().model_dump(),
                "groups": [
                    SceneGroupAuthoringRecord(id="bad", name="Bad", members=["missing"])
                ],
            }
        )
    with pytest.raises(ValueError, match="finite"):
        _finite(True, "test")
    with pytest.raises(ValueError, match="positive"):
        _positive(0, "test")
    with pytest.raises(ValueError, match="between"):
        _unit(2, "test")
