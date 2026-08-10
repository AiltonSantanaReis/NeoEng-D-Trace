"""Stage 9 static collision architecture and compatibility contracts."""

import inspect
import math

import numpy as np
import pytest

from src.collision import (
    CollisionObject,
    StaticCollisionManager,
    polygon_collision_sat,
    polygons_overlap,
)
from src.collision.broadphase import AABB, UniformGridBroadPhase
from src.collision.sat2d import project as canonical_project
from src.core.convex_decomp import triangulate_to_convex
from src.physics.broadphase import AABB as HistoricalAABB
from src.physics.convex_decomp import triangulate_to_convex as historical_triangulate
from src.physics.physics_manager import PhysicsManager, PhysicsObject
from src.physics.sat2d import polygon_edges, project, sat_polygon_vs_polygon
from src.ui import canvas_view, main_window, side_panel

SQUARE = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
L_SHAPE = [
    (0.0, 0.0),
    (4.0, 0.0),
    (4.0, 1.0),
    (1.0, 1.0),
    (1.0, 4.0),
    (0.0, 4.0),
]


def test_convex_overlap_returns_outward_mtv() -> None:
    second = [(1, 0), (3, 0), (3, 2), (1, 2)]
    colliding, mtv = polygons_overlap(SQUARE, second)

    assert colliding is True
    assert mtv is not None
    moved = [(x + mtv[0], y + mtv[1]) for x, y in SQUARE]
    touching, touching_mtv = polygons_overlap(moved, second)
    assert touching is True
    assert touching_mtv is not None
    assert math.isclose(math.hypot(*touching_mtv), 0.0, abs_tol=1e-9)


def test_separate_convex_polygons_do_not_overlap() -> None:
    assert polygons_overlap(SQUARE, [(3, 0), (5, 0), (5, 2), (3, 2)]) == (
        False,
        None,
    )


def test_closed_clockwise_polygon_is_canonicalized() -> None:
    clockwise_closed = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    assert polygons_overlap(clockwise_closed, SQUARE)[0] is True


def test_concave_hole_does_not_create_sat_false_positive() -> None:
    inside_missing_region = [(2, 2), (3, 2), (3, 3), (2, 3)]
    assert polygons_overlap(L_SHAPE, inside_missing_region) == (False, None)


def test_concave_overlap_has_no_misleading_partial_mtv() -> None:
    crossing_vertical_arm = [(0.5, 2), (1.5, 2), (1.5, 3), (0.5, 3)]
    assert polygons_overlap(L_SHAPE, crossing_vertical_arm) == (True, None)


@pytest.mark.parametrize(
    "polygon",
    [
        [],
        [(0, 0), (1, 1)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (2, 0), (2, 0), (0, 2)],
        [(0, 0), (2, 2), (0, 2), (2, 0)],
        [(0, 0), (2, 0), (float("nan"), 2)],
        [(0, 0), (2, 0), (float("inf"), 2)],
        [(0, 0), (2, 0), (True, 2)],
        [(0, 0), "bad", (0, 2)],
        [(0, 0), 7, (0, 2)],
    ],
)
def test_invalid_geometry_is_rejected_controlled(polygon) -> None:
    with pytest.raises(ValueError):
        polygons_overlap(polygon, SQUARE)


@pytest.mark.parametrize("epsilon", [-1.0, float("nan"), float("inf")])
def test_invalid_epsilon_is_rejected(epsilon: float) -> None:
    with pytest.raises(ValueError, match="epsilon"):
        polygons_overlap(SQUARE, SQUARE, epsilon)


def test_numpy_compatibility_adapter_preserves_types() -> None:
    colliding, mtv = polygon_collision_sat(
        np.asarray(SQUARE), np.asarray([(1, 0), (3, 0), (3, 2), (1, 2)])
    )
    assert colliding is True
    assert isinstance(mtv, np.ndarray)
    assert mtv.shape == (2,)


def test_numpy_compatibility_adapter_rejects_wrong_dimensions() -> None:
    with pytest.raises(ValueError, match="two-dimensional"):
        polygon_collision_sat(np.asarray([0.0, 1.0]), np.asarray(SQUARE))


def test_historical_list_adapter_preserves_incomplete_geometry_behavior() -> None:
    assert sat_polygon_vs_polygon([], SQUARE) == (False, None)
    assert sat_polygon_vs_polygon(SQUARE, []) == (False, None)


def test_historical_sat_helpers_cover_empty_zero_axis_and_valid_overlap() -> None:
    assert project(SQUARE, (0.0, 0.0)) == (0.0, 0.0)
    assert polygon_edges([]) == []
    assert sat_polygon_vs_polygon(SQUARE, SQUARE)[0] is True


def test_public_and_historical_names_share_one_implementation() -> None:
    assert PhysicsManager is StaticCollisionManager
    assert PhysicsObject is CollisionObject
    assert HistoricalAABB is AABB
    assert historical_triangulate is triangulate_to_convex
    assert project is canonical_project
    source = inspect.getsource(main_window)
    assert "StaticCollisionManager" in source
    assert "physics.physics_manager import PhysicsManager" not in source
    assert "self.physics_manager" not in source
    visible_ui = inspect.getsource(canvas_view) + inspect.getsource(side_panel)
    assert "Physics Collision" not in visible_ui
    assert "Physics: " not in visible_ui
    assert "Física: " not in visible_ui


def test_manager_does_not_advertise_dynamic_physics() -> None:
    manager = StaticCollisionManager()
    for unsupported in (
        "gravity",
        "backend",
        "step",
        "fixed_dt",
        "register_collision_callback",
    ):
        assert not hasattr(manager, unsupported)


@pytest.mark.parametrize("cell_size", [0, -1, 1.5, True])
def test_manager_rejects_invalid_grid_size(cell_size) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        StaticCollisionManager(cell_size)


def test_mixed_identifier_types_are_deterministic() -> None:
    manager = StaticCollisionManager()
    manager.register(1, SQUARE)
    manager.register("two", SQUARE, (1, 0))
    manager.register(("three",), SQUARE, (1, 1))

    first = manager.batch_test()
    assert first == manager.batch_test()
    assert [(item.obj1_id, item.obj2_id) for item in first] == [
        (1, "two"),
        (1, ("three",)),
        ("two", ("three",)),
    ]


def test_unhashable_identifier_is_rejected_controlled() -> None:
    with pytest.raises(ValueError, match="hashable"):
        StaticCollisionManager().register([], SQUARE)


def test_registration_is_atomic_when_replacement_is_invalid() -> None:
    manager = StaticCollisionManager()
    manager.register("shape", SQUARE, metadata={"version": 1})

    with pytest.raises(ValueError):
        manager.register("shape", [(0, 0), (1, 1)])

    preserved = manager.get_object("shape")
    assert preserved is not None
    assert preserved.metadata == {"version": 1}
    assert preserved.shape == tuple(SQUARE)


def test_registered_shape_is_isolated_from_external_mutation() -> None:
    source = list(SQUARE)
    manager = StaticCollisionManager()
    manager.register("shape", source)
    source[0] = (100.0, 100.0)

    registered = manager.get_object("shape")
    assert registered is not None
    assert registered.shape[0] == (0.0, 0.0)


@pytest.mark.parametrize("position", [(1,), (float("nan"), 0), (0, "bad")])
def test_invalid_position_is_rejected(position) -> None:
    with pytest.raises(ValueError, match="Position"):
        StaticCollisionManager().register("shape", SQUARE, position)


def test_position_update_refreshes_queries() -> None:
    manager = StaticCollisionManager()
    manager.register("first", SQUARE)
    manager.register("second", SQUARE, (5, 0))

    assert manager.query_collisions("first") == []
    assert manager.update_position("second", (1, 0)) is True
    assert [result.obj2_id for result in manager.query_collisions("first")] == [
        "second"
    ]
    assert manager.update_position("missing", (0, 0)) is False


def test_add_and_remove_body_are_compatibility_adapters() -> None:
    manager = StaticCollisionManager()
    shape_id = manager.add_body(SQUARE, is_static=True, metadata={"kind": "test"})

    registered = manager.get_object(shape_id)
    assert registered is not None
    assert registered.metadata == {"kind": "test"}
    manager.remove_body(shape_id)
    assert manager.get_object(shape_id) is None
    with pytest.raises(ValueError, match="boolean"):
        manager.add_body(SQUARE, is_static=1)


def test_batch_stats_and_clear_are_consistent() -> None:
    manager = StaticCollisionManager()
    manager.register("first", SQUARE)
    manager.register("second", SQUARE, (1, 0))
    manager.register("far", SQUARE, (200, 0))

    results = manager.batch_test()
    stats = manager.get_stats()

    assert len(results) == 1
    assert stats["total_objects"] == 3
    assert stats["total_collision_tests"] == 1
    assert stats["total_collisions_found"] == 1
    assert stats["collision_rate"] == 1.0
    manager.clear()
    assert manager.get_all_objects() == []
    assert manager.get_stats()["total_objects"] == 0


def test_broadphase_accepts_mixed_ids_without_comparison() -> None:
    broadphase = UniformGridBroadPhase(64)
    broadphase.insert(1, AABB(0, 0, 10, 10))
    broadphase.insert("two", AABB(1, 1, 11, 11))

    assert len(broadphase.get_all_pairs()) == 1
