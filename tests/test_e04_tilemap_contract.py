from __future__ import annotations

import hashlib
import json

import pytest

from src.core.tilemap_benchmark import benchmark_chunk_sizes
from src.core.tilemap_grids import GridKind, GridSpec, grid_round_trip
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
from src.core.tilemap_rules import NeighborCondition, TerrainRule, TileRuleSet
from src.core.tilemap_tools import (
    bucket_fill,
    copy_cells,
    deterministic_tile_id,
    erase_line,
    paint_line,
    paint_rectangle,
    paste_cells,
)
from src.persistence.tilemap_io import (
    TileMapPersistenceError,
    load_tilemap,
    save_tilemap,
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


def test_paint_line_is_one_undoable_transaction_and_redoable() -> None:
    document = _map()
    transaction = paint_line(document, "ground", (0, 0), (3, 0), "grass")
    assert document.populated_cell_count == 4
    transaction.undo()
    assert document.populated_cell_count == 0
    transaction.redo()
    assert document.populated_cell_count == 4


def test_rectangle_and_eraser_cover_cells_without_snapshot_copy() -> None:
    document = _map()
    paint_rectangle(document, "ground", (-1, -1), (1, 1), "grass")
    assert document.populated_cell_count == 9
    erase_line(document, "ground", (-1, -1), (1, 1))
    assert document.populated_cell_count == 6


def test_bucket_fill_is_bounded_and_uses_grid_neighborhood() -> None:
    document = _map(bounds=TileMapBounds(0, 0, 3, 3))
    paint_line(document, "ground", (1, 0), (1, 3), "grass")
    transaction = bucket_fill(
        document,
        "ground",
        (0, 0),
        "water",
        grid=GridSpec(GridKind.ORTHOGONAL),
    )
    assert document.populated_cell_count == 8
    transaction.undo()
    assert document.populated_cell_count == 4
    with pytest.raises(TileMapLimitError, match="finite map bounds"):
        bucket_fill(
            _map(),
            "ground",
            (0, 0),
            "grass",
            grid=GridSpec(GridKind.ORTHOGONAL),
        )


def test_bucket_fill_limit_rejects_unbounded_work() -> None:
    document = _map(bounds=TileMapBounds(0, 0, 4, 4))
    with pytest.raises(TileMapLimitError, match="max_cells"):
        bucket_fill(
            document,
            "ground",
            (0, 0),
            "grass",
            grid=GridSpec(GridKind.ORTHOGONAL),
            max_cells=4,
        )


def test_copy_paste_is_relative_and_deterministic_variation_is_order_independent() -> (
    None
):
    document = _map()
    paint_line(document, "ground", (2, 3), (3, 3), "grass")
    clipboard = copy_cells(document, "ground", ((3, 3), (2, 3)))
    paste_cells(document, "ground", (-2, -1), clipboard)
    assert document.get_cell("ground", (-2, -1)) == TileCell("grass")
    assert document.get_cell("ground", (-1, -1)) == TileCell("grass")
    ids = ("grass", "water")
    assert deterministic_tile_id(
        ids, seed=7, coordinate=(-2, 4)
    ) == deterministic_tile_id(ids, seed=7, coordinate=(-2, 4))
    with pytest.raises(TileMapError, match="at least one tile"):
        deterministic_tile_id((), seed=1, coordinate=(0, 0))


def test_rule_tiles_use_priority_fallback_and_neighbor_invalidation() -> None:
    document = _map(bounds=TileMapBounds(-2, -2, 2, 2))
    rules = TileRuleSet(
        (
            TerrainRule(
                "grass-next-to-water",
                "grass",
                conditions=(NeighborCondition((1, 0), ("water",)),),
                priority=10,
            ),
        ),
        fallback_tile_id="water",
    )
    document.set_cell("ground", (1, 0), TileCell("water"))
    result = rules.resolve(
        document,
        "ground",
        (0, 0),
        grid=GridSpec(GridKind.ORTHOGONAL),
        seed=5,
    )
    assert result.tile_id == "grass"
    assert result.rule_id == "grass-next-to-water"
    assert (1, 0) in result.invalidated
    assert (
        rules.resolve(
            document,
            "ground",
            (2, 0),
            grid=GridSpec(GridKind.ORTHOGONAL),
        ).rule_id
        is None
    )
    resolutions, transaction = rules.apply(
        document,
        "ground",
        ((0, 0),),
        grid=GridSpec(GridKind.ORTHOGONAL),
        seed=5,
    )
    assert resolutions[0].tile_id == "grass"
    transaction.undo()
    assert document.get_cell("ground", (0, 0)) is None


def test_rule_tiles_reject_ambiguity_unknown_dependency_and_cycles() -> None:
    document = _map()
    ambiguous = TileRuleSet(
        (
            TerrainRule("a", "grass", priority=3),
            TerrainRule("b", "water", priority=3),
        ),
        fallback_tile_id="grass",
    )
    with pytest.raises(TileMapError, match="ambiguous"):
        ambiguous.resolve(
            document,
            "ground",
            (0, 0),
            grid=GridSpec(GridKind.ORTHOGONAL),
        )
    with pytest.raises(TileMapError, match="unknown rule"):
        TileRuleSet(
            (TerrainRule("a", "grass", depends_on=("missing",)),),
            fallback_tile_id="grass",
        )


def test_tilemap_save_reopen_preserves_cells_layers_and_lock(tmp_path) -> None:
    document = _map(bounds=TileMapBounds(-2, -2, 2, 2))
    document.set_cell("ground", (-1, 2), TileCell("grass", metadata=(("biome", "a"),)))
    document.set_layer_lock("ground", True)
    path = save_tilemap(document, tmp_path / "map.ndttilemap.json")
    reopened = load_tilemap(path)
    assert reopened.to_dict() == document.to_dict()
    with pytest.raises(TileMapLockedError):
        reopened.set_cell("ground", (0, 0), TileCell("grass"))


def test_tilemap_loader_rejects_invalid_format_and_duplicate_cells(tmp_path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"format_id":"wrong"}', encoding="utf-8")
    with pytest.raises(TileMapPersistenceError, match="unsupported tilemap format"):
        load_tilemap(invalid)
    duplicate = _map().to_dict()
    duplicate["cells"] = [
        {"layer_id": "ground", "x": 0, "y": 0, "cell": TileCell("grass").to_dict()},
        {"layer_id": "ground", "x": 0, "y": 0, "cell": TileCell("water").to_dict()},
    ]
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(TileMapPersistenceError, match="duplicate"):
        load_tilemap(duplicate_path)
    with pytest.raises(TileMapError, match="cycle"):
        TileRuleSet(
            (
                TerrainRule("a", "grass", depends_on=("b",)),
                TerrainRule("b", "water", depends_on=("a",)),
            ),
            fallback_tile_id="grass",
        )
