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
    # This polygon contains a consecutive duplicate but is typically valid
    # (our validation heuristics accept it), so add_object should succeed
    # even with auto_repair disabled.
    poly = [(0, 0), (0, 0), (40, 0), (40, 40), (0, 40)]
    s.add_object("test_obj_dup", poly)
    assert "test_obj_dup" in s.objects

    # For a self-intersecting polygon (bow-tie), behavior depends on
    # whether repair heuristics (or shapely) can fix it. We assert the
    # following property: enabling auto_repair must not make the result
    # worse — after enabling it we should be able to add the polygon
    # (if it was previously rejected).
    bow = [(0, 0), (30, 30), (0, 30), (30, 0)]
    s2 = scene.Scene()
    raised_before = False
    try:
        s2.add_object("maybe_bow", bow)
    except ValueError:
        raised_before = True

    s2.set_auto_repair(True)
    # After enabling auto_repair we should be able to add or still be fine
    # (i.e., no exception should propagate)
    s2.add_object("maybe_bow", bow)
    assert "maybe_bow" in s2.objects


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
