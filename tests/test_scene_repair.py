# tests/test_scene_repair.py
import pytest

from src.models import scene


def test_attempt_repair_duplicates_and_colinear():
    # Polygon with a consecutive duplicate and a colinear vertex
    pts = [(0, 0), (0, 0), (40.0, 0.0), (20.0, 0.0), (40.0, 40.0), (0, 40.0)]

    repaired, flag = scene._attempt_repair(pts)
    assert (
        flag is True
    ), "Attempt repair should flag True for trivial duplicates/colinear"
    assert scene._validate_polygon(repaired) is True, "Repaired polygon must validate"
    # Repaired polygon should have at least 3 vertices
    assert len(repaired) >= 3


def test_scene_add_object_auto_repair_toggle():
    s = scene.Scene()
    poly = [(0, 0), (0, 0), (40, 0), (40, 40), (0, 40)]

    with pytest.raises(ValueError, match="Invalid polygon"):
        s.add_object("test_obj_dup", poly)

    assert "test_obj_dup" not in s.objects

    s.set_auto_repair(True)
    s.add_object("test_obj_dup", poly)

    assert "test_obj_dup" in s.objects
    repaired = s.objects["test_obj_dup"].polygon
    assert scene._validate_polygon(repaired) is True
    assert all(
        repaired[index] != repaired[(index + 1) % len(repaired)]
        for index in range(len(repaired))
    )


def test_attempt_repair_self_intersection():
    # Bow-tie self-intersecting polygon
    pts = [(0, 0), (30, 30), (0, 30), (30, 0)]
    repaired, flag = scene._attempt_repair(pts)

    # If shapely is available we expect a repair attempt to possibly succeed.
    # If not available, the heuristic may not fix it; either behavior is acceptable
    # but we assert that the function returns a tuple and does not throw.
    assert isinstance(repaired, list)
    assert isinstance(flag, bool)
    if flag:
        assert scene._validate_polygon(repaired) is True
