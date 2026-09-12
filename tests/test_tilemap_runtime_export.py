from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.core.tilemap_model import (
    TileCell,
    TileDefinition,
    TileLayer,
    TileMapDocument,
    TileSet,
)
from src.core.tilemap_rules import NeighborCondition, TerrainRule, TileRuleSet
from src.exporters.tilemap_runtime_export import (
    TileMapRuntimeExportError,
    build_tilemap_runtime_package,
    build_tilemap_runtime_payload,
    validate_tilemap_runtime_payload,
)
from src.persistence.tilemap_io import save_tilemap


def _document(
    project_root: Path, *, atlas_path: str | None = "assets/tiles/terrain.png"
) -> Path:
    atlas = project_root / "assets" / "tiles" / "terrain.png"
    atlas.parent.mkdir(parents=True, exist_ok=True)
    atlas.write_bytes(b"atlas-v1")
    tileset = TileSet(
        id="terrain",
        atlas_asset_id="terrain-atlas",
        atlas_sha256=hashlib.sha256(atlas.read_bytes()).hexdigest(),
        atlas_path=atlas_path,
        tiles=(
            TileDefinition("grass", "terrain-atlas", (0, 0, 16, 16)),
            TileDefinition("water", "terrain-atlas", (16, 0, 16, 16)),
        ),
    )
    rules = TileRuleSet(
        (
            TerrainRule(
                "water-edge",
                "water",
                conditions=(NeighborCondition((1, 0), ("grass",)),),
                priority=2,
            ),
        ),
        fallback_tile_id="grass",
    )
    document = TileMapDocument(
        id="scenario",
        name="Scenario",
        tileset=tileset,
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0), TileLayer("deco", "Deco", 1)),
        rule_set_payload=rules.to_dict(),
    )
    document.set_cell("ground", (0, 0), TileCell("grass"))
    document.set_cell("ground", (1, 0), TileCell("water", variant="blue"))
    document.set_cell(
        "deco", (-1, 2), TileCell("grass", metadata=(("biome", "meadow"),))
    )
    source = project_root / "maps" / "scenario.ndttilemap.json"
    save_tilemap(document, source)
    return source


def test_runtime_package_binds_cells_rules_and_atlas_bytes(tmp_path: Path) -> None:
    source = _document(tmp_path)
    package = build_tilemap_runtime_package(
        source,
        project_root=tmp_path,
        destination=tmp_path / "runtime",
    )

    assert package.payload["source"]["path"] == "tilemap.json"
    assert package.payload["counts"] == {
        "layers": 2,
        "tiles": 2,
        "cells": 3,
        "rules": 1,
    }
    assert package.payload["rules"]["fallback_tile_id"] == "grass"
    assert package.payload["atlas"]["path"] == "assets/tiles/terrain.png"
    assert package.atlas_path.read_bytes() == b"atlas-v1"
    assert package.payload_path.is_file()
    assert (
        json.loads(package.payload_path.read_text(encoding="utf-8")) == package.payload
    )
    validate_tilemap_runtime_payload(package.payload, project_root=package.directory)


def test_runtime_payload_is_deterministic_and_normalizes_empty_rules(
    tmp_path: Path,
) -> None:
    source = _document(tmp_path)
    raw = json.loads(source.read_text(encoding="utf-8"))
    raw.pop("rules")
    source.write_text(json.dumps(raw), encoding="utf-8")
    document_source = source
    from src.persistence.tilemap_io import load_tilemap

    payload_a = build_tilemap_runtime_payload(
        load_tilemap(document_source), tilemap_path=source, project_root=tmp_path
    )
    payload_b = build_tilemap_runtime_payload(
        load_tilemap(document_source), tilemap_path=source, project_root=tmp_path
    )
    assert payload_a == payload_b
    assert payload_a["rules"] == {"fallback_tile_id": "grass", "rules": []}


def test_runtime_export_requires_explicit_atlas_path(tmp_path: Path) -> None:
    source = _document(tmp_path, atlas_path=None)
    from src.persistence.tilemap_io import load_tilemap

    with pytest.raises(TileMapRuntimeExportError, match="atlas path is required"):
        build_tilemap_runtime_payload(
            load_tilemap(source), tilemap_path=source, project_root=tmp_path
        )


def test_runtime_export_rejects_atlas_drift(tmp_path: Path) -> None:
    source = _document(tmp_path)
    atlas = tmp_path / "assets" / "tiles" / "terrain.png"
    atlas.write_bytes(b"changed-atlas")
    from src.persistence.tilemap_io import load_tilemap

    with pytest.raises(TileMapRuntimeExportError, match="atlas hash mismatch"):
        build_tilemap_runtime_payload(
            load_tilemap(source), tilemap_path=source, project_root=tmp_path
        )


def test_runtime_export_rejects_unsafe_reference(tmp_path: Path) -> None:
    source = _document(tmp_path)
    from src.persistence.tilemap_io import load_tilemap

    with pytest.raises(TileMapRuntimeExportError, match="safe relative path"):
        build_tilemap_runtime_payload(
            load_tilemap(source),
            tilemap_path=source,
            project_root=tmp_path,
            source_reference="../scenario.json",
        )


def test_runtime_validator_rejects_duplicate_cell_and_count_drift(
    tmp_path: Path,
) -> None:
    source = _document(tmp_path)
    package = build_tilemap_runtime_package(
        source,
        project_root=tmp_path,
        destination=tmp_path / "runtime",
    )
    duplicate = json.loads(json.dumps(package.payload))
    duplicate["cells"].append(duplicate["cells"][0])
    with pytest.raises(TileMapRuntimeExportError, match="duplicate runtime cell"):
        validate_tilemap_runtime_payload(duplicate)

    counts = json.loads(json.dumps(package.payload))
    counts["counts"]["cells"] += 1
    with pytest.raises(TileMapRuntimeExportError, match="counts"):
        validate_tilemap_runtime_payload(counts)


def test_runtime_package_refuses_overwrite(tmp_path: Path) -> None:
    source = _document(tmp_path)
    destination = tmp_path / "runtime"
    build_tilemap_runtime_package(
        source, project_root=tmp_path, destination=destination
    )
    with pytest.raises(TileMapRuntimeExportError, match="refusing to overwrite"):
        build_tilemap_runtime_package(
            source, project_root=tmp_path, destination=destination
        )
