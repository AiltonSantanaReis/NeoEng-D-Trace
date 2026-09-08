from __future__ import annotations

import pytest

from src.core.navmesh_2d import (
    NavMeshError,
    NavMeshSource,
    NavObstacle,
    NavRegion,
    bake_navmesh,
    find_path,
)
from src.persistence.navmesh_io import load_navmesh, save_navmesh


def test_bake_routes_around_obstacle_and_is_deterministic() -> None:
    source = NavMeshSource(
        regions=[NavRegion("room", (0, 0, 128, 64))],
        obstacles=[NavObstacle("wall", (48, 0, 16, 32))],
        agent_radius=4,
        cell_size=8,
    )
    first = bake_navmesh(source)
    second = bake_navmesh(source)
    assert first == second
    path = find_path(source, first, (8, 24), (112, 24))
    assert len(path.points) > 2
    assert path.bake_hash == source.source_hash()


def test_source_change_obsoletes_bake_and_persistence_round_trip(tmp_path) -> None:
    source = NavMeshSource(regions=[NavRegion("room", (0, 0, 64, 64))], cell_size=8)
    bake = bake_navmesh(source)
    destination = save_navmesh(source, tmp_path / "scenario.navmesh.json")
    reopened = load_navmesh(destination)
    assert reopened.source_hash() == source.source_hash()
    source.obstacles.append(NavObstacle("crate", (16, 16, 8, 8)))
    source.touch()
    assert bake.is_obsolete(source)
    with pytest.raises(NavMeshError, match="obsolete_bake"):
        find_path(source, bake, (4, 4), (56, 56))


@pytest.mark.parametrize(
    "factory,code",
    [
        (
            lambda: NavMeshSource(
                regions=[NavRegion("room", (0, 0, 10, 10))], agent_radius=0
            ),
            "invalid_agent_radius",
        ),
        (lambda: NavMeshSource(regions=[]), "no_walkable_region"),
        (
            lambda: NavMeshSource(regions=[NavRegion("room", (0, 0, 32, 32))]),
            "point_outside_region",
        ),
    ],
)
def test_navmesh_rejects_canonical_negatives(factory, code: str) -> None:
    if code == "no_walkable_region":
        source = factory()
        with pytest.raises(NavMeshError, match=code):
            bake_navmesh(source)
    elif code == "point_outside_region":
        source = factory()
        bake = bake_navmesh(source)
        with pytest.raises(NavMeshError, match=code):
            find_path(source, bake, (-1, 0), (8, 8))
    else:
        with pytest.raises(NavMeshError, match=code):
            factory()
