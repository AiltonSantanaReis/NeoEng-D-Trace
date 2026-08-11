"""Stage 11 package 6: scene validation, relation and failure branches."""

from __future__ import annotations

import numpy as np
import pytest

from src.models import scene as scene_module
from src.models.scene import (
    Group,
    Layer,
    Scene,
    _attempt_repair,
    _lines_intersect,
    _normalize_polygon_winding,
    _remove_close_duplicates,
    _remove_colinear,
    _validate_polygon,
)

SQUARE = [(0, 0), (20, 0), (20, 20), (0, 20)]
CLOCKWISE = list(reversed(SQUARE))


def test_polygon_winding_validation_and_segment_intersections():
    assert _normalize_polygon_winding(CLOCKWISE + [CLOCKWISE[0]]) == SQUARE
    assert _validate_polygon(SQUARE)

    invalid = [
        None,
        [],
        [(0, 0), (1, 1)],
        [(0, 0), (1, 1), (2,)],
        [(0, 0), (True, 1), (2, 0)],
        [(0, 0), (10**1000, 1), (2, 0)],
        [(0, 0), (float("nan"), 1), (2, 0)],
        [(0, 0), (0, 0), (2, 0)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (20, 20), (0, 20), (20, 0)],
    ]
    for polygon in invalid:
        assert _validate_polygon(polygon) is False

    assert _lines_intersect((0, 0), (4, 4), (0, 4), (4, 0))
    assert _lines_intersect((0, 0), (4, 0), (2, 0), (6, 0))
    assert _lines_intersect((2, 0), (6, 0), (0, 0), (4, 0))
    assert _lines_intersect((0, 0), (4, 0), (4, 0), (4, 4))
    assert _lines_intersect((4, 0), (4, 4), (0, 0), (4, 0))
    assert not _lines_intersect((0, 0), (1, 0), (2, 0), (3, 0))


def test_polygon_cleanup_helpers_cover_empty_short_and_fallback_paths():
    assert _remove_close_duplicates([]) == []
    assert _remove_close_duplicates([(0, 0), (0.2, 0.2), (4, 0), (0, 0)]) == [
        (0, 0),
        (4, 0),
    ]
    short = [(0, 0), (1, 1)]
    assert _remove_colinear(short) is short
    colinear = [(0, 0), (1, 0), (2, 0)]
    assert _remove_colinear(colinear) is colinear
    assert _remove_colinear(SQUARE) == SQUARE


def test_polygon_repair_fallback_invalid_and_optional_backend_paths(monkeypatch):
    assert _attempt_repair([]) == ([], False)
    invalid = [(0, 0), (True, 1), (2, 0)]
    assert _attempt_repair(invalid) == (invalid, False)
    too_short = [(0, 0), (0.2, 0.2), (0.4, 0.4)]
    assert _attempt_repair(too_short) == (too_short, False)

    monkeypatch.setattr(scene_module, "HAS_SHAPELY", False)
    repaired, changed = _attempt_repair(SQUARE + [SQUARE[0]])
    assert changed is True
    assert repaired == SQUARE

    monkeypatch.setattr(scene_module, "HAS_SHAPELY", True)
    monkeypatch.setattr(
        scene_module,
        "Polygon",
        lambda points: (_ for _ in ()).throw(RuntimeError("backend")),
        raising=False,
    )
    repaired, changed = _attempt_repair(SQUARE)
    assert changed is True
    assert repaired == SQUARE


def test_scene_listener_isolation_and_collision_paths():
    scene = Scene()
    notices = []

    def broken():
        raise RuntimeError("listener")

    scene.subscribe(broken)
    scene.subscribe(broken)
    scene.subscribe(lambda: notices.append("ok"))
    scene._notify()
    assert broken not in scene._listeners
    assert notices == ["ok"]

    scene.set_object_collision("missing", True)
    scene.add_object("A", SQUARE)
    scene.set_object_collision("A", True)
    assert scene.has_collision("A")
    scene.set_object_collision("A", False)
    scene.set_object_collision("A", False)
    assert not scene.has_collision("A")


def test_scene_layer_errors_assignments_and_rendering():
    scene = Scene()
    layer = scene.create_layer("Gameplay")
    scene.add_object("A", SQUARE, layer.id)
    scene.add_object("B", SQUARE)

    with pytest.raises(ValueError):
        scene.remove_layer("layer_default")
    with pytest.raises(KeyError):
        scene.move_layer("missing", 0)
    with pytest.raises(KeyError):
        scene.set_layer_visibility("missing", True)
    with pytest.raises(KeyError):
        scene.set_layer_lock("missing", True)
    with pytest.raises(KeyError):
        scene.set_object_layer("missing", layer.id)
    with pytest.raises(KeyError):
        scene.set_object_layer("A", "missing")

    scene.move_layer(layer.id, -10)
    scene.set_layer_visibility(layer.id, False)
    assert [obj.id for obj in scene.render_list()] == ["B"]
    scene.set_layer_lock(layer.id, True)
    assert scene.is_layer_locked_for_object("A") is True
    assert scene.is_layer_locked_for_object("missing") is False
    scene.objects["A"].layer_id = "missing"
    assert scene.is_layer_locked_for_object("A") is False
    scene.objects["A"].layer_id = layer.id
    scene.remove_layer(layer.id)
    assert scene.objects["A"].layer_id == "layer_default"


def test_add_object_repair_duplicate_and_selection_paths(monkeypatch):
    scene = Scene()
    with pytest.raises(ValueError):
        scene.add_object("invalid", [(0, 0), (1, 1), (2, 2)])

    scene.set_auto_repair(True)
    monkeypatch.setattr(
        scene_module,
        "_attempt_repair",
        lambda polygon: (SQUARE, True),
    )
    scene.add_object("A", [(0, 0), (1, 1), (2, 2)], select=True)
    assert scene.selected_id == "A"
    assert scene.objects["A"].polygon == SQUARE

    with pytest.raises(ValueError):
        scene.add_object("A", SQUARE)
    monkeypatch.setattr(
        scene_module,
        "_attempt_repair",
        lambda polygon: (polygon, False),
    )
    with pytest.raises(ValueError):
        scene.add_object("B", [(0, 0), (1, 1), (2, 2)])


def test_bezier_preparation_and_duplicate_identity(monkeypatch):
    scene = Scene()
    monkeypatch.setattr(
        scene_module,
        "canonicalize_beziers",
        lambda value: (_ for _ in ()).throw(OverflowError("overflow")),
    )
    with pytest.raises(ValueError, match="representable"):
        scene.prepare_bezier_geometry([])

    monkeypatch.setattr(scene_module, "canonicalize_beziers", lambda value: value)
    monkeypatch.setattr(scene_module, "sample_beziers_to_polygon", lambda *a, **k: [])
    with pytest.raises(ValueError, match="sampled"):
        scene.prepare_bezier_geometry([])

    monkeypatch.setattr(
        scene_module, "sample_beziers_to_polygon", lambda *a, **k: SQUARE
    )
    assert scene.add_bezier_object([], object_id="curve", select=True) == "curve"
    assert scene.selected_id == "curve"
    with pytest.raises(ValueError):
        scene.add_bezier_object([], object_id="curve")


def test_add_polygon_records_failure_and_reraises(monkeypatch):
    scene = Scene()
    records = []
    monkeypatch.setattr(
        scene_module,
        "record_validation_exception",
        lambda event, exc, **fields: records.append(
            (event, type(exc).__name__, fields)
        ),
    )
    with pytest.raises(ValueError):
        scene.add_polygon([(0, 0), (1, 1), (2, 2)])
    assert records[0][0:2] == ("polygon.created", "ValueError")


def test_remove_rename_and_update_preserve_or_reject_relations():
    scene = Scene()
    scene.add_object("A", SQUARE, select=True)
    scene.add_object("B", SQUARE)
    group = scene.create_group("Actors")
    group.members = ["A", "B"]
    scene.set_object_collision("A", True)

    with pytest.raises(KeyError):
        scene.remove_object("missing")
    with pytest.raises(ValueError):
        scene.rename_object("A", " ")
    with pytest.raises(KeyError):
        scene.rename_object("missing", "C")
    scene.rename_object("A", "A")
    with pytest.raises(ValueError):
        scene.rename_object("A", "B")

    scene.rename_object("A", "C")
    assert list(scene.objects) == ["C", "B"]
    assert "C" in scene.collision_shapes
    assert group.members == ["C", "B"]
    assert scene.selected_id == "C"

    with pytest.raises(KeyError):
        scene.update_polygon("missing", SQUARE)
    scene.update_polygon("C", CLOCKWISE)
    assert scene.objects["C"].polygon == SQUARE
    assert scene.collision_shapes["C"] == [(float(x), float(y)) for x, y in SQUARE]
    scene.remove_object("C")
    assert scene.selected_id is None
    assert group.members == ["B"]
    assert "C" not in scene.collision_shapes


def test_group_errors_duplicates_and_bounds():
    scene = Scene()
    scene.add_object("A", SQUARE)
    first = scene.create_group("First")
    second = scene.create_group("Second")

    with pytest.raises(KeyError):
        scene.add_object_to_group(first.id, "missing")
    with pytest.raises(KeyError):
        scene.add_object_to_group("missing", "A")
    scene.add_object_to_group(first.id, "A")
    scene.add_object_to_group(first.id, "A")
    assert first.members == ["A"]
    with pytest.raises(KeyError):
        scene.remove_object_from_group("missing", "A")
    scene.remove_object_from_group(first.id, "missing")
    scene.remove_object_from_group(first.id, "A")
    assert first.members == []
    with pytest.raises(KeyError):
        scene.move_group("missing", 0)
    scene.move_group(second.id, -10)
    assert scene.groups[0] is second
    with pytest.raises(KeyError):
        scene.set_group_visibility("missing", True)
    with pytest.raises(KeyError):
        scene.set_group_lock("missing", True)


def test_image_replace_attach_and_clear_reset_state():
    scene = Scene()
    scene.add_object("A", SQUARE, select=True)
    scene.create_group("Actors")
    scene.set_object_collision("A", True)
    image = np.zeros((3, 4, 4), dtype=np.uint8)
    scene.load_image(image, "first.png")
    assert scene.get_image() is image
    assert "A" in scene.objects
    scene.replace_with_image(image, "second.png")
    assert scene.objects == {}
    assert [layer.id for layer in scene.layers] == ["layer_default"]
    scene.attach_project_image(None)
    assert scene.get_image() is None
    scene.clear()
    assert scene.groups == []


def test_project_save_load_success_warnings_and_failures(monkeypatch):
    scene = Scene()
    saved = []
    monkeypatch.setattr(
        "src.persistence.project_io.save_scene_project",
        lambda current, path: saved.append((current, path)),
    )
    scene.save_project("project.neoeng")
    assert saved == [(scene, "project.neoeng")]

    monkeypatch.setattr(
        "src.persistence.project_io.load_project_into_scene",
        lambda current, path: ("migrated",),
    )
    assert scene.load_project("project.neoeng") == ("migrated",)

    monkeypatch.setattr(
        "src.persistence.project_io.save_scene_project",
        lambda current, path: (_ for _ in ()).throw(OSError("save")),
    )
    with pytest.raises(OSError):
        scene.save_project("project.neoeng")
    monkeypatch.setattr(
        "src.persistence.project_io.load_project_into_scene",
        lambda current, path: (_ for _ in ()).throw(ValueError("load")),
    )
    with pytest.raises(ValueError):
        scene.load_project("project.neoeng")


def test_set_object_beziers_rejects_missing_and_updates_existing(monkeypatch):
    scene = Scene()
    with pytest.raises(KeyError):
        scene.set_object_beziers("missing", [])
    scene.add_object("A", SQUARE)
    monkeypatch.setattr(
        scene,
        "prepare_bezier_geometry",
        lambda beziers, steps_per_segment=20: (beziers, SQUARE),
    )
    scene.set_object_beziers("A", [["curve"]])
    assert scene.objects["A"].beziers == [["curve"]]
    assert scene.sample_beziers_to_polygon([["curve"]]) == SQUARE


def test_layer_group_default_identity_branches():
    assert Layer().id
    assert Group().id
    assert Layer(id="fixed").id == "fixed"
    assert Group(id="fixed").id == "fixed"
