from __future__ import annotations

import json

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

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
    SceneSnapRecord,
    SceneTransformRecord,
)
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

SHA = "c" * 64


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.clipboard().clear()
    app.processEvents()


def _transform(x: float, y: float, z: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=z),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document(
    *,
    locked_b: bool = False,
    group: bool = False,
) -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata={"name": "P2D-03B test", "generator": "test", "app_version": "0"},
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[
            SceneObjectAuthoringRecord(
                id="a",
                asset_id="asset",
                layer_id="layer",
                transform=_transform(0.0, 0.0),
            ),
            SceneObjectAuthoringRecord(
                id="b",
                asset_id="asset",
                layer_id="layer",
                transform=_transform(100.0, 20.0, 3.0),
                locked=locked_b,
            ),
        ],
        groups=(
            [
                SceneGroupAuthoringRecord(
                    id="group",
                    name="Group",
                    members=["a", "b"],
                )
            ]
            if group
            else []
        ),
    )


def _session(**kwargs) -> SceneAuthoringSession:
    return SceneAuthoringSession(SceneAuthoringModel(_document(**kwargs)))


def test_nudge_is_world_space_transactional_and_undoable():
    session = _session()
    session.set_selection(["a", "b"], primary="b")
    before = session.document.model_copy(deep=True)

    assert session.nudge_selected(Point3Record(x=1.0, y=-1.0, z=0.0)) is True
    assert session.document.objects[0].transform.position == Point3Record(
        x=1.0, y=-1.0, z=0.0
    )
    assert session.document.objects[1].transform.position == Point3Record(
        x=101.0, y=19.0, z=3.0
    )
    assert session.undo_count == 1

    assert session.undo() is True
    assert session.document == before
    assert session.selection.ids == ("a", "b")
    assert session.selection.primary == "b"
    assert session.redo() is True


def test_nudge_respects_existing_snap_and_noop_has_no_history():
    session = _session()
    session.model.set_snap(
        SceneSnapRecord(enabled=True, spacing=PointRecord(x=16.0, y=16.0))
    )
    session.set_selection(["a"])

    assert session.nudge_selected(Point3Record(x=1.0, y=0.0, z=0.0)) is False
    assert (
        session.document.objects[0].transform.position == _transform(0.0, 0.0).position
    )
    assert session.undo_count == 0


def test_duplicate_allocates_ids_offset_and_exclusive_selection():
    session = _session()
    session.set_selection(["a", "b"], primary="b")

    created = session.duplicate_selected()

    assert created == ("a__copy", "b__copy")
    assert [item.id for item in session.document.objects] == [
        "a",
        "b",
        "a__copy",
        "b__copy",
    ]
    assert session.document.objects[2].transform.position == Point3Record(
        x=16.0, y=16.0, z=0.0
    )
    assert session.document.objects[3].transform.position == Point3Record(
        x=116.0, y=36.0, z=3.0
    )
    assert session.selection.ids == created
    assert session.selection.primary == "b__copy"
    assert session.undo_count == 1
    assert session.undo() is True
    assert [item.id for item in session.document.objects] == ["a", "b"]


def test_duplicate_does_not_modify_existing_group_membership():
    session = _session(group=True)
    session.set_selection(["a", "b"])

    created = session.duplicate_selected()

    assert created == ("a__copy", "b__copy")
    assert session.document.groups[0].members == ["a", "b"]
    assert len(session.document.groups) == 1


def test_delete_is_all_or_nothing_when_any_selected_object_is_locked():
    session = _session(locked_b=True)
    session.set_selection(["a", "b"], primary="b")
    before = session.document.model_copy(deep=True)

    with pytest.raises(PermissionError):
        session.delete_selected()

    assert session.document == before
    assert session.selection.ids == ("a", "b")
    assert session.undo_count == 0


def test_delete_removes_multiple_objects_and_group_membership_in_one_entry():
    session = _session(group=True)
    session.set_selection(["a", "b"])

    assert session.delete_selected() is True
    assert session.document.objects == []
    assert session.document.groups[0].members == []
    assert session.selection.ids == ()
    assert session.undo_count == 1
    assert session.undo() is True
    assert [item.id for item in session.document.objects] == ["a", "b"]
    assert session.document.groups[0].members == ["a", "b"]


def test_copy_is_non_mutating_and_paste_creates_new_objects():
    session = _session()
    session.set_selection(["a", "b"], primary="b")
    before = session.document.model_copy(deep=True)
    before_selection = session.selection

    payload = session.copy_selected_payload()

    assert isinstance(payload, bytes)
    assert session.document == before
    assert session.selection == before_selection
    assert session.undo_count == 0

    created = session.paste_payload(payload)
    assert created == ("a__copy", "b__copy")
    assert session.selection.ids == created
    assert [item.id for item in session.document.objects] == [
        "a",
        "b",
        "a__copy",
        "b__copy",
    ]
    assert session.document.objects[2].transform.position == Point3Record(
        x=16.0, y=16.0, z=0.0
    )
    assert session.undo_count == 1
    assert session.undo() is True
    assert session.document == before


def test_paste_clones_complete_group_and_drops_partial_group_membership():
    complete = _session(group=True)
    complete.set_selection(["a", "b"])
    created = complete.paste_payload(complete.copy_selected_payload())
    assert created == ("a__copy", "b__copy")
    assert len(complete.document.groups) == 2
    assert complete.document.groups[1].id == "group__copy"
    assert complete.document.groups[1].members == list(created)

    partial = _session(group=True)
    partial.set_selection(["a"])
    partial_created = partial.paste_payload(partial.copy_selected_payload())
    assert partial_created == ("a__copy",)
    assert len(partial.document.groups) == 1
    assert partial.document.groups[0].members == ["a", "b"]


def test_invalid_clipboard_is_rejected_without_partial_mutation():
    session = _session()
    session.set_selection(["a"])
    valid = json.loads(session.copy_selected_payload().decode("utf-8"))
    valid["objects"][0]["unexpected"] = True
    invalid = json.dumps(valid, separators=(",", ":")).encode("utf-8")
    before = session.document.model_copy(deep=True)

    with pytest.raises(ValueError):
        session.paste_payload(invalid)

    assert session.document == before
    assert session.selection.ids == ("a",)
    assert session.undo_count == 0


def test_preview_blocks_keyboard_mutations_but_keeps_document_intact(qt_app):
    session = _session()
    view = SceneAuthoringViewport(session)
    view.show()
    view.set_preview_enabled(True)
    view.set_authoring_enabled(False)
    session.set_selection(["a"])
    before = session.document.model_copy(deep=True)
    try:
        view.setFocus()
        QTest.keyClick(view, Qt.Key.Key_Right)
        assert session.document == before
        assert session.undo_count == 0
    finally:
        view.close()
        view.deleteLater()
        qt_app.processEvents()
