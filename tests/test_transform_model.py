"""Contracts for persistent object transforms and selection state."""

from __future__ import annotations

import json

import pytest

from src.models.scene import Scene
from src.persistence.project_schema import Point3Record, TransformRecord


def test_new_object_gets_center_pivot_and_world_position() -> None:
    scene = Scene()
    scene.add_object("box", [(10, 20), (30, 20), (30, 40), (10, 40)])

    obj = scene.objects["box"]
    assert obj.pivot == (0.5, 0.5)
    assert obj.position == (20.0, 30.0, 0.0)
    assert obj.rotation == (0.0, 0.0, 0.0)
    assert obj.scale == (1.0, 1.0, 1.0)


def test_pivot_presets_update_anchor_without_mutating_polygon() -> None:
    scene = Scene()
    scene.add_object("box", [(10, 20), (30, 20), (30, 40), (10, 40)])
    original = list(scene.objects["box"].polygon)

    scene.objects["box"].set_pivot(0.5, 1.0)

    assert scene.objects["box"].polygon == original
    assert scene.objects["box"].pivot == (0.5, 1.0)
    assert scene.objects["box"].position == (20.0, 40.0, 0.0)


def test_multiple_selection_preserves_primary_and_rejects_unknown_objects() -> None:
    scene = Scene()
    scene.add_object("one", [(0, 0), (10, 0), (10, 10)])
    scene.add_object("two", [(20, 0), (30, 0), (30, 10)])

    scene.select_objects(["two", "one"], primary="one")

    assert scene.selected_ids == ["two", "one"]
    assert scene.selected_id == "one"
    with pytest.raises(KeyError):
        scene.select_objects(["missing"])


def test_transform_record_is_strict_and_finite() -> None:
    record = TransformRecord(
        position=Point3Record(x=1, y=2, z=3),
        rotation=Point3Record(x=0, y=0, z=45),
        scale=Point3Record(x=1, y=1, z=1),
        pivot={"x": 0.5, "y": 1.0},
    )
    assert record.rotation.z == 45
    with pytest.raises(ValueError):
        Point3Record(x=0, y=0, z=float("inf"))


def test_transform_round_trip_is_backward_compatible(tmp_path) -> None:
    path = tmp_path / "transform.ndtproj"
    scene = Scene()
    scene.add_object("box", [(10, 20), (30, 20), (30, 40), (10, 40)])
    scene.objects["box"].set_pivot(0.5, 1.0)
    scene.objects["box"].position = (25.0, 45.0, 7.0)
    scene.objects["box"].rotation = (0.0, 0.0, 30.0)
    scene.objects["box"].scale = (1.5, 0.75, 1.0)
    scene.save_project(str(path))

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["objects"][0]["transform"]["position"] == {
        "x": 25.0,
        "y": 45.0,
        "z": 7.0,
    }

    restored = Scene()
    restored.load_project(str(path))
    obj = restored.objects["box"]
    assert obj.position == (25.0, 45.0, 7.0)
    assert obj.rotation == (0.0, 0.0, 30.0)
    assert obj.scale == (1.5, 0.75, 1.0)
    assert obj.pivot == (0.5, 1.0)
