from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QTreeWidgetItem

from src.core.scene_authoring_groups import (
    locked_group_for_object,
    object_is_effectively_locked,
    object_is_effectively_visible,
    object_ids_for_group,
)
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import load_scene_authoring_v2, save_scene_authoring
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scene_authoring_group_stack import SceneAuthoringGroupStack


SHA = "b" * 64


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _transform(x: float, y: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document() -> SceneAuthoringDocumentV2:
    source = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-02B flow", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero", asset_id="asset", layer_id="layer", transform=_transform(10, 20)
            ),
            SceneObjectAuthoringRecord(
                id="prop", asset_id="asset", layer_id="layer", transform=_transform(40, 50)
            ),
            SceneObjectAuthoringRecord(
                id="free", asset_id="asset", layer_id="layer", transform=_transform(70, 80)
            ),
        ],
        groups=[],
    )
    return upgrade_scene_authoring_document(source)


def _grouped_document() -> SceneAuthoringDocumentV2:
    return _document().model_copy(
        update={
            "groups": [
                SceneGroupAuthoringRecordV2(
                    id="actors", name="Actors", members=["hero"]
                ),
                SceneGroupAuthoringRecordV2(
                    id="details", name="Details", members=["prop"], parent_group_id="actors"
                ),
            ]
        }
    )


def _find_item(panel: SceneAuthoringGroupStack, kind: str, item_id: str) -> QTreeWidgetItem:
    from PySide6.QtWidgets import QTreeWidgetItemIterator

    cursor = QTreeWidgetItemIterator(panel.tree)
    while cursor.value() is not None:
        item = cursor.value()
        if (
            item.data(0, panel._KIND_ROLE) == kind
            and item.data(0, panel._ID_ROLE) == item_id
        ):
            return item
        cursor += 1
    raise AssertionError(f"missing tree item {kind}:{item_id}")


def test_schema_parentage_roundtrip_and_cycles_are_rejected(tmp_path: Path) -> None:
    document = _grouped_document()
    scene_path = tmp_path / "scene.ndtscene.json"
    asset_path = tmp_path / "assets" / "a.png"
    asset_path.parent.mkdir()
    asset_path.write_bytes(b"asset")
    document = document.model_copy(
        update={"assets": [document.assets[0].model_copy(update={"sha256": SHA})]}
    )
    # The fixture hash is intentionally the stable contract value; round-trip
    # validation is independent from asset verification here.
    save_scene_authoring(document, scene_path)
    loaded = load_scene_authoring_v2(scene_path, verify_assets=False)
    assert loaded.groups == document.groups
    assert loaded.groups[1].parent_group_id == "actors"

    invalid = document.model_copy(
        update={
            "groups": [
                document.groups[0].model_copy(update={"parent_group_id": "details"}),
                document.groups[1],
            ]
        }
    )
    with pytest.raises(ValueError, match="cycle"):
        SceneAuthoringDocumentV2.model_validate(invalid, strict=True)


def test_group_operations_inherit_visibility_lock_and_isolation() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["hero"])
    session.group_selection(
        SceneGroupAuthoringRecordV2(id="actors", name="Actors", members=[])
    )
    session.add_group(
        SceneGroupAuthoringRecordV2(
            id="details", name="Details", members=["prop"], parent_group_id="actors"
        )
    )
    assert object_ids_for_group(session.document, "actors") == ("hero", "prop")

    session.set_group_visibility("actors", False)
    assert not object_is_effectively_visible(session.document, "hero")
    assert not object_is_effectively_visible(session.document, "prop")
    session.set_group_visibility("actors", True)
    session.set_group_locked("actors", True)
    assert object_is_effectively_locked(session.document, "hero")
    assert locked_group_for_object(session.document, "prop").id == "actors"
    with pytest.raises(PermissionError, match="group"):
        session.translate_selected(Point3Record(x=5.0, y=0.0, z=0.0))

    session.set_group_locked("actors", False)
    session.mark_saved()
    session.set_isolated_group("details")
    assert object_is_effectively_visible(
        session.document, "prop", isolated_group_id=session.isolated_group_id
    )
    assert not object_is_effectively_visible(
        session.document, "hero", isolated_group_id=session.isolated_group_id
    )
    assert not session.is_dirty
    assert session.undo_count > 0

    session.clear_isolation()
    session.remove_group("actors")
    assert [item.id for item in session.document.objects] == ["hero", "prop", "free"]
    assert session.document.groups[0].id == "details"
    assert session.document.groups[0].parent_group_id is None


def test_professional_group_tree_flow_and_transient_isolation(qt_app: QApplication) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_grouped_document()))
    panel = SceneAuthoringGroupStack(session)
    try:
        qt_app.processEvents()
        actors = _find_item(panel, "group", "actors")
        details = _find_item(panel, "group", "details")
        assert details.parent() is actors

        panel.tree.setCurrentItem(details)
        qt_app.processEvents()
        assert session.selection.ids == ("prop",)
        del actors, details
        panel.isolate_button.click()
        qt_app.processEvents()
        assert session.isolated_group_id == "details"
        panel.isolate_button.click()
        qt_app.processEvents()
        assert session.isolated_group_id is None

        panel.tree.setCurrentItem(_find_item(panel, "group", "actors"))
        panel.visible_box.setChecked(False)
        qt_app.processEvents()
        assert not session.document.groups[0].visible
        panel.visible_box.setChecked(True)
        panel.locked_box.setChecked(True)
        qt_app.processEvents()
        assert session.document.groups[0].locked
    finally:
        panel.close()
