"""E02-A contract and history tests for independent-scene primitives."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.independent_scene_gestures import IndependentScenePointEditGesture
from src.core.independent_scene_session import IndependentSceneSession
from src.persistence.independent_scene_schema import (
    IndependentScenePrimitiveGeometryRecord,
    IndependentScenePrimitiveTransformRecord,
    default_independent_scene_document,
    default_independent_scene_document_v2,
    upgrade_independent_scene_document,
)
from src.persistence.project_schema import PointRecord


def _points(*values: tuple[float, float]) -> list[PointRecord]:
    return [PointRecord(x=x, y=y) for x, y in values]


def test_v2_document_is_explicit_successor_without_project_reference() -> None:
    document = default_independent_scene_document_v2(name="Shapes")
    payload = document.model_dump(mode="json")

    assert payload["schema_version"] == 2
    assert payload["compatibility"] == {
        "reader_min_schema_version": 1,
        "writer_schema_version": 2,
    }
    assert payload["objects"] == []
    assert "project" not in payload


def test_v1_upgrade_is_copy_and_preserves_authoring_defaults() -> None:
    legacy = default_independent_scene_document(width=640, height=360)
    upgraded = upgrade_independent_scene_document(legacy)

    assert legacy.schema_version == 1
    assert upgraded.schema_version == 2
    assert upgraded.resolution == legacy.resolution
    assert upgraded.objects == []


@pytest.mark.parametrize(
    ("kind", "points", "closed", "filled"),
    [
        ("rectangle", _points((0, 0), (100, 50)), True, True),
        ("ellipse", _points((0, 0), (100, 50)), True, True),
        ("polygon", _points((0, 0), (100, 0), (50, 50)), True, True),
        ("path", _points((0, 0), (100, 50)), False, False),
    ],
)
def test_all_e02_primitive_kinds_validate(kind, points, closed, filled) -> None:
    geometry = IndependentScenePrimitiveGeometryRecord(
        kind=kind,
        points=points,
        closed=closed,
        filled=filled,
    )

    assert geometry.kind == kind
    assert geometry.points == points


def test_polygon_self_intersection_and_duplicate_points_are_rejected() -> None:
    with pytest.raises(ValueError, match="self-intersect"):
        IndependentScenePrimitiveGeometryRecord(
            kind="polygon",
            points=_points((0, 0), (100, 100), (0, 100), (100, 0)),
        )
    with pytest.raises(ValueError, match="unique"):
        IndependentScenePrimitiveGeometryRecord(
            kind="polygon",
            points=_points((0, 0), (100, 0), (100, 0)),
        )


def test_open_path_cannot_be_filled_and_transform_has_safe_bounds() -> None:
    with pytest.raises(ValueError, match="cannot be filled"):
        IndependentScenePrimitiveGeometryRecord(
            kind="path",
            points=_points((0, 0), (10, 10)),
            closed=False,
            filled=True,
        )
    with pytest.raises(ValueError, match="positive"):
        IndependentScenePrimitiveTransformRecord(
            scale=PointRecord(x=0, y=1),
        )
    with pytest.raises(ValueError, match="between"):
        IndependentScenePrimitiveTransformRecord(
            pivot=PointRecord(x=2, y=0.5),
        )


def test_session_creates_three_shapes_and_round_trips_them(tmp_path: Path) -> None:
    session = IndependentSceneSession()
    rectangle = session.add_primitive(
        kind="rectangle",
        points=_points((0, 0), (100, 50)),
        primitive_id="rect",
    )
    ellipse = session.add_primitive(
        kind="ellipse",
        points=_points((120, 0), (220, 80)),
        primitive_id="ellipse",
    )
    polygon = session.add_primitive(
        kind="polygon",
        points=_points((0, 100), (100, 100), (50, 180)),
        primitive_id="poly",
    )

    assert [item.id for item in session.document.objects] == [
        rectangle.id,
        ellipse.id,
        polygon.id,
    ]
    assert session.object_count == 3
    path = session.save(tmp_path / "authoring.ndtscene")
    reopened = IndependentSceneSession()
    loaded = reopened.load(path)

    assert loaded.schema_version == 2
    assert [item.geometry.kind for item in loaded.objects] == [
        "rectangle",
        "ellipse",
        "polygon",
    ]


def test_session_undo_redo_duplicate_remove_and_transform() -> None:
    session = IndependentSceneSession()
    session.add_primitive(
        kind="rectangle",
        points=_points((0, 0), (10, 10)),
        primitive_id="rect",
    )
    session.add_primitive(
        kind="ellipse",
        points=_points((20, 20), (30, 30)),
        primitive_id="ellipse",
    )
    assert session.can_undo

    assert session.undo()
    assert [item.id for item in session.document.objects] == ["rect"]
    assert session.redo()
    assert [item.id for item in session.document.objects] == ["rect", "ellipse"]

    duplicate = session.duplicate_primitive("rect", new_id="rect_copy")
    assert duplicate.id == "rect_copy"
    assert len(session.document.objects) == 3
    session.update_primitive_transform(
        "rect_copy",
        IndependentScenePrimitiveTransformRecord(
            position=PointRecord(x=50, y=50),
        ),
    )
    assert session.document.objects[-1].transform.position.x == 50
    session.remove_primitive("rect_copy")
    assert [item.id for item in session.document.objects] == ["rect", "ellipse"]


def test_session_rejects_locked_primitive_without_mutating_document() -> None:
    session = IndependentSceneSession()
    session.add_primitive(
        kind="rectangle",
        points=_points((0, 0), (10, 10)),
        primitive_id="locked",
    )
    session.document = session.document.model_copy(
        update={
            "objects": [session.document.objects[0].model_copy(update={"locked": True})]
        }
    )
    before = session.document

    with pytest.raises(PermissionError, match="locked"):
        session.remove_primitive("locked")

    assert session.document == before


def test_session_batch_selection_translate_duplicate_and_remove() -> None:
    session = IndependentSceneSession()
    session.add_primitive(
        kind="rectangle",
        points=_points((0, 0), (10, 10)),
        primitive_id="rect",
    )
    session.add_primitive(
        kind="ellipse",
        points=_points((20, 20), (30, 30)),
        primitive_id="ellipse",
    )

    assert session.set_selection(["rect", "ellipse"]) == ("rect", "ellipse")
    session.translate_selection(delta_x=12, delta_y=8)
    assert session.document.objects[0].transform.position == PointRecord(x=12, y=8)
    assert session.document.objects[1].transform.position == PointRecord(x=12, y=8)

    copies = session.duplicate_selection()
    assert len(copies) == 2
    assert session.selection == tuple(item.id for item in copies)
    assert session.object_count == 4
    session.remove_selection()
    assert session.object_count == 2
    assert session.selection == ()


def test_session_batch_selection_respects_locked_objects() -> None:
    session = IndependentSceneSession()
    session.add_primitive(
        kind="rectangle",
        points=_points((0, 0), (10, 10)),
        primitive_id="locked",
    )
    session.document = session.document.model_copy(
        update={
            "objects": [session.document.objects[0].model_copy(update={"locked": True})]
        }
    )
    session.set_selection(["locked"])

    with pytest.raises(PermissionError, match="locked"):
        session.translate_selection(delta_x=1, delta_y=1)


def test_point_edit_gesture_commits_and_supports_double_click_finalize() -> None:
    session = IndependentSceneSession()
    primitive = session.add_primitive(
        kind="polygon",
        points=_points((0, 0), (100, 0), (50, 100)),
        primitive_id="poly",
    )
    gesture = IndependentScenePointEditGesture()
    gesture.begin(primitive.id, primitive.geometry)

    assert gesture.preview_point(1, PointRecord(x=120, y=0))
    points = gesture.double_click_finalize()
    session.update_primitive_geometry("poly", points=points)

    assert gesture.state == "finalized"
    assert session.document.objects[0].geometry.points[1] == PointRecord(x=120, y=0)


def test_point_edit_invalid_preview_does_not_mutate_and_escape_cancels() -> None:
    session = IndependentSceneSession()
    primitive = session.add_primitive(
        kind="polygon",
        points=_points((0, 0), (100, 0), (50, 100)),
        primitive_id="poly",
    )
    original = tuple(primitive.geometry.points)
    gesture = IndependentScenePointEditGesture()
    gesture.begin(primitive.id, primitive.geometry)

    assert not gesture.preview_point(1, PointRecord(x=50, y=100))
    assert gesture.state == "preview_invalid"
    assert tuple(session.document.objects[0].geometry.points) == original
    assert gesture.escape() == original
    assert gesture.state == "cancelled"
    assert tuple(gesture.working_points) == original


def test_point_edit_rejects_near_duplicate_preview_points() -> None:
    geometry = IndependentScenePrimitiveGeometryRecord(
        kind="polygon",
        points=_points((0, 0), (100, 0), (50, 100)),
    )
    gesture = IndependentScenePointEditGesture()
    gesture.begin("poly", geometry)

    assert not gesture.preview_point(1, PointRecord(x=50, y=101))
    assert gesture.state == "preview_invalid"
    assert "24 pixels" in (gesture.last_error or "")


def test_point_edit_gesture_rejects_locked_primitive() -> None:
    geometry = IndependentScenePrimitiveGeometryRecord(
        kind="rectangle",
        points=_points((0, 0), (100, 50)),
    )
    gesture = IndependentScenePointEditGesture()
    with pytest.raises(PermissionError, match="locked"):
        gesture.begin("locked", geometry, locked=True)
