from __future__ import annotations

import copy
import math

import numpy as np
import pytest

from src.core.bezier_geometry import (
    canonical_point,
    canonicalize_beziers,
    cubic_bezier_point,
    replace_handle,
    sample_beziers,
    sample_beziers_to_polygon,
)
from src.physics import convex_decomp

BEZIERS = [
    ((0, 0), (0, -10), (10, -10), (10, 0)),
    ((10, 0), (20, 10), (30, 10), (40, 0)),
]


@pytest.mark.parametrize(
    "value,message",
    [
        (None, "exactly two"),
        ((1,), "exactly two"),
        ((True, 1), "numeric"),
        (("1", 1), "numeric"),
        ((math.nan, 1), "finite"),
        ((10**400, 1), "representable"),
    ],
)
def test_canonical_point_rejects_invalid_atoms(value, message):
    with pytest.raises(ValueError, match=message):
        canonical_point(value)


@pytest.mark.parametrize(
    "value,message",
    [
        ((segment for segment in BEZIERS), "sequence"),
        ([], "At least one"),
        ([((0, 0), (1, 1), (2, 2))], "four control points"),
        (
            [BEZIERS[0], ((11, 0), (20, 10), (30, 10), (40, 0))],
            "not continuous",
        ),
    ],
)
def test_canonicalize_beziers_rejects_malformed_or_discontinuous(value, message):
    with pytest.raises(ValueError, match=message):
        canonicalize_beziers(value)


def test_sampling_is_continuous_deterministic_and_does_not_alias_input():
    source = copy.deepcopy(BEZIERS)
    sampled = sample_beziers(source, steps_per_segment=4)

    assert len(sampled) == 9
    assert sampled[0] == (0.0, 0.0)
    assert sampled[4] == (10.0, 0.0)
    assert sampled[-1] == (40.0, 0.0)
    assert source == BEZIERS


@pytest.mark.parametrize("steps", [True, 1.5, 0, -1])
def test_sampling_rejects_invalid_step_contract(steps):
    with pytest.raises(ValueError, match="steps_per_segment"):
        sample_beziers(BEZIERS, steps_per_segment=steps)


def test_cubic_endpoints_and_linear_control_polygon_are_exact():
    controls = ((0, 0), (10, 10), (20, 20), (30, 30))

    assert cubic_bezier_point(0, *controls) == (0.0, 0.0)
    assert cubic_bezier_point(1, *controls) == (30.0, 30.0)
    assert cubic_bezier_point(0.5, *controls) == (15.0, 15.0)


def test_polygon_sampling_collapses_duplicates_and_rejects_degenerate_curve():
    point = ((1, 1), (1, 1), (1, 1), (1, 1))
    with pytest.raises(ValueError, match="at least three points"):
        sample_beziers_to_polygon([point])


@pytest.mark.parametrize(
    "segment_index,handle_index,message",
    [
        (True, 1, "segment_index"),
        (-1, 1, "outside"),
        (2, 1, "outside"),
        (0, True, "handle_index"),
        (0, 0, "control point 1 or 2"),
        (0, 3, "control point 1 or 2"),
    ],
)
def test_replace_handle_rejects_invalid_indices(segment_index, handle_index, message):
    with pytest.raises(ValueError, match=message):
        replace_handle(BEZIERS, segment_index, handle_index, (5, 5))


def test_replace_handle_is_independent_and_preserves_continuity():
    source = copy.deepcopy(BEZIERS)
    replaced = replace_handle(source, 1, 1, (25, 15))

    assert replaced[1][1] == (25.0, 15.0)
    assert replaced[0][3] == replaced[1][0]
    assert source == BEZIERS


@pytest.mark.parametrize(
    "polygon",
    [
        [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (2.0, 1.0), (0.0, 4.0)],
        [
            (0.0, 0.0),
            (3.0, 0.0),
            (3.0, 2.0),
            (1.0, 2.0),
            (1.0, 1.0),
            (0.0, 1.0),
        ],
    ],
)
def test_fallback_triangulation_is_orientation_independent(monkeypatch, polygon):
    monkeypatch.setattr(convex_decomp, "HAS_EARCUT", False)

    for candidate in (polygon, list(reversed(polygon))):
        triangles = convex_decomp.triangulate_to_convex(candidate)
        assert len(triangles) == len(polygon) - 2
        assert all(convex_decomp.is_convex_polygon(item) for item in triangles)
        assert math.isclose(
            sum(convex_decomp.polygon_area(item) for item in triangles),
            convex_decomp.polygon_area(polygon),
            rel_tol=0.0,
            abs_tol=1e-10,
        )


def test_reflex_vertex_and_degenerate_triangle_are_not_ears():
    arrow = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (2.0, 1.0), (0.0, 4.0)]

    assert convex_decomp.is_ear(arrow, 3) is False
    assert (
        convex_decomp.is_point_in_triangle(
            (1.0, 0.0), [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
        )
        is False
    )


@pytest.mark.parametrize(
    "polygon,message",
    [
        ([(0, 0), (1, 0), (1, math.inf)], "finite"),
        ([(0, 0), (1, 0), (True, 1)], "numeric"),
        ([(0, 0), (1, 0), (0, 0)], "non-zero area"),
        ([(0, 0), (1, 0), (1, 1), (1, 0)], "repeated vertices"),
    ],
)
def test_triangulation_rejects_invalid_geometry(polygon, message):
    with pytest.raises(ValueError, match=message):
        convex_decomp.triangulate_to_convex(polygon)


def test_terminal_duplicate_is_canonicalized_and_short_inputs_stay_empty(monkeypatch):
    monkeypatch.setattr(convex_decomp, "HAS_EARCUT", False)
    square = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]

    assert len(convex_decomp.triangulate_to_convex(square)) == 2
    assert convex_decomp.triangulate_to_convex([]) == []
    assert convex_decomp.triangulate_to_convex([(0, 0), (1, 1)]) == []


def test_backend_malformed_indices_fail_closed(monkeypatch):
    class BrokenBackend:
        @staticmethod
        def triangulate_float64(vertices, ring_ends):
            return np.array([0, 1], dtype=np.uint32)

    monkeypatch.setattr(convex_decomp, "HAS_EARCUT", True)
    monkeypatch.setattr(convex_decomp, "earcut", BrokenBackend(), raising=False)

    with pytest.raises(ValueError, match="malformed indices"):
        convex_decomp.triangulate_to_convex([(0, 0), (2, 0), (2, 2), (0, 2)])


def test_backend_out_of_range_indices_fail_closed(monkeypatch):
    class BrokenBackend:
        @staticmethod
        def triangulate_float64(vertices, ring_ends):
            return np.array([0, 1, 9, 0, 2, 3], dtype=np.int64)

    monkeypatch.setattr(convex_decomp, "HAS_EARCUT", True)
    monkeypatch.setattr(convex_decomp, "earcut", BrokenBackend(), raising=False)

    with pytest.raises(ValueError, match="out-of-range indices"):
        convex_decomp.triangulate_to_convex([(0, 0), (2, 0), (2, 2), (0, 2)])


@pytest.mark.parametrize(
    "method_name,dtype",
    [("triangulate_float64", np.float64), ("triangulate_float32", np.float32)],
)
def test_optional_backend_preserves_area_for_supported_precision(
    monkeypatch, method_name, dtype
):
    observed = {}

    def triangulate(vertices, ring_ends):
        observed["dtype"] = vertices.dtype
        observed["rings"] = ring_ends.tolist()
        return np.array([2, 3, 0, 0, 1, 2], dtype=np.uint32)

    backend = type("Backend", (), {method_name: staticmethod(triangulate)})()
    monkeypatch.setattr(convex_decomp, "HAS_EARCUT", True)
    monkeypatch.setattr(convex_decomp, "earcut", backend, raising=False)

    triangles = convex_decomp.triangulate_to_convex([(0, 0), (2, 0), (2, 2), (0, 2)])

    assert observed == {"dtype": np.dtype(dtype), "rings": [4]}
    assert len(triangles) == 2
    assert sum(convex_decomp.polygon_area(item) for item in triangles) == 4.0


def test_public_helpers_reject_short_or_unrepresentable_inputs():
    assert convex_decomp.polygon_area([]) == 0.0
    assert convex_decomp.is_point_in_triangle((0, 0), [(0, 0), (1, 0)]) is False
    assert convex_decomp.is_ear([(0, 0), (1, 0)], 0) is False
    assert convex_decomp.ear_clipping_triangulation([(0, 0), (1, 0)]) == []

    with pytest.raises(ValueError, match="representable"):
        convex_decomp.triangulate_to_convex([(0, 0), (1, 0), (10**400, 1)])


def test_merge_helpers_cover_empty_disjoint_and_both_shared_edge_directions():
    assert convex_decomp.merge_triangles_to_convex([]) == []
    assert (
        convex_decomp.try_merge_polygons(
            [(0, 0), (1, 0), (0, 1)],
            [(2, 0), (3, 0), (2, 1)],
        )
        is None
    )

    first = [(0, 0), (1, 0), (0, 1)]
    second = [(1, 0), (1, 1), (0, 1)]
    assert convex_decomp.try_merge_polygons(first, second) is not None
    assert (
        convex_decomp.try_merge_polygons(list(reversed(first)), list(reversed(second)))
        is not None
    )
