from __future__ import annotations

import hashlib

import pytest

from src.core.tilemap_grids import GridKind, GridSpec, grid_round_trip
from src.core.tilemap_benchmark import benchmark_chunk_sizes
from src.core.tilemap_model import (
    TileCell,
    TileCellDelta,
    TileDefinition,
    TileLayer,
    TileMapBounds,
    TileMapDocument,
    TileMapError,
    TileMapLimitError,
    TileMapLockedError,
    TileSet,
)


def _tileset() -> TileSet:
    return TileSet(
        id="terrain",
        atlas_asset_id="atlas_asset",
        atlas_sha256=hashlib.sha256(b"atlas").hexdigest(),
        tiles=(
            TileDefinition(
                id="grass",
                asset_id="atlas_asset",
                source_rect=(0, 0, 16, 16),
                properties=(("terrain", "grass"),),
            ),
            TileDefinition(
                id="water",
                asset_id="atlas_asset",
                source_rect=(16, 0, 16, 16),
                variant="animated",
                animation_frames=("water",),
            ),
        ),
    )


def _map(**kwargs: object) -> TileMapDocument:
    return TileMapDocument(
        id="map",
        name="Terrain",
        tileset=_tileset(),
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0),),
        **kwargs,
    )


def test_tileset_ids_are_position_independent_and_atlas_hash_is_verified() -> None:
    tileset = _tileset()
    assert tileset.tile("grass").source_rect == (0, 0, 16, 16)
    assert tileset.verify_atlas(b"atlas")
    assert not tileset.verify_atlas(b"changed")


def test_sparse_map_stores_negative_cells_by_floor_chunk() -> None:
    document = _map(chunk_size=16)
    delta = document.set_cell("ground", (-1, -17), TileCell("grass"))
    assert delta.before is None
    assert document.get_cell("ground", (-1, -17)) == TileCell("grass")
    assert document.chunk_for((-1, -17)) == (-1, -2)
    assert document.populated_cell_count == 1
    assert document.populated_chunk_count == 1


def test_apply_deltas_validates_all_changes_before_mutating() -> None:
    document = _map()
    with pytest.raises(TileMapError, match="unknown tile ID"):
        document.apply_deltas(
            (
                TileCellDelta("ground", (0, 0), None, TileCell("grass")),
                TileCellDelta("ground", (1, 0), None, TileCell("missing")),
            )
        )
    assert document.populated_cell_count == 0


def test_remove_cell_releases_empty_chunk() -> None:
    document = _map()
    document.set_cell("ground", (0, 0), TileCell("grass"))
    document.set_cell("ground", (0, 0), None)
    assert document.populated_cell_count == 0
    assert document.populated_chunk_count == 0


def test_locked_layer_rejects_mutation() -> None:
    document = _map()
    document.set_layer_lock("ground", True)
    with pytest.raises(TileMapLockedError, match="locked"):
        document.set_cell("ground", (0, 0), TileCell("grass"))


def test_bounds_reject_coordinates_outside_map() -> None:
    document = _map(bounds=TileMapBounds(-2, -2, 2, 2))
    with pytest.raises(TileMapLimitError, match="outside map bounds"):
        document.set_cell("ground", (3, 0), TileCell("grass"))


def test_serialization_is_deterministic_and_contains_sparse_cells() -> None:
    document = _map()
    document.set_cell("ground", (1, 2), TileCell("grass"))
    payload = document.to_dict()
    assert payload["format_id"] == "neoeng-d-trace-tilemap"
    assert payload["cells"] == [
        {"layer_id": "ground", "x": 1, "y": 2, "cell": TileCell("grass").to_dict()}
    ]
    assert payload["layers"][0]["locked"] is False


@pytest.mark.parametrize("kind", list(GridKind))
def test_all_grids_round_trip_signed_coordinates(kind: GridKind) -> None:
    spec = GridSpec(
        kind, cell_width=64, cell_height=32 if kind != GridKind.ORTHOGONAL else 64
    )
    for coordinate in ((0, 0), (2, -3), (-4, 5)):
        assert grid_round_trip(spec, coordinate)


def test_orthogonal_picking_uses_floor_for_negative_coordinates() -> None:
    spec = GridSpec(GridKind.ORTHOGONAL, cell_width=10, cell_height=20)
    assert spec.world_to_cell((-0.01, -0.01)) == (-1, -1)
    assert spec.world_to_cell(spec.cell_to_world((-2, 3))) == (-2, 3)


def test_isometric_neighbors_are_cardinal_and_deterministic() -> None:
    spec = GridSpec(GridKind.ISOMETRIC, 64, 32)
    assert spec.neighbors((4, -2)) == ((5, -2), (3, -2), (4, -1), (4, -3))


def test_hexagonal_uses_axial_six_neighborhood() -> None:
    spec = GridSpec(GridKind.HEXAGONAL, 32, 32)
    assert len(spec.neighbors((0, 0))) == 6
    assert set(spec.neighbors((0, 0))) == {
        (1, 0),
        (1, -1),
        (0, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
    }


def test_invalid_tileset_and_chunk_contracts_fail_closed() -> None:
    with pytest.raises(TileMapError, match="lowercase SHA"):
        TileSet("terrain", "atlas", "A" * 64, (_tileset().tiles[0],))
    with pytest.raises(TileMapError, match="power of two"):
        _map(chunk_size=24)
    with pytest.raises(TileMapError, match="between"):
        _map(chunk_size=4)


def test_chunk_benchmark_reports_sparse_geometry_for_each_candidate() -> None:
    results = benchmark_chunk_sizes(
        lambda chunk_size: _map(chunk_size=chunk_size),
        width=4,
        height=4,
    )
    assert [result.chunk_size for result in results] == [16, 32, 64]
    assert all(result.populated_cells == 16 for result in results)
    assert [result.populated_chunks for result in results] == [1, 1, 1]
