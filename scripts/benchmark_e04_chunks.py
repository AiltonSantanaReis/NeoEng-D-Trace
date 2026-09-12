"""Run the E04-A chunk benchmark without starting the GUI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.tilemap_benchmark import benchmark_chunk_sizes  # noqa: E402
from src.core.tilemap_model import (  # noqa: E402
    TileDefinition,
    TileLayer,
    TileMapDocument,
    TileSet,
)


def _document(chunk_size: int) -> TileMapDocument:
    tileset = TileSet(
        id="benchmark",
        atlas_asset_id="atlas",
        atlas_sha256="0" * 64,
        tiles=(TileDefinition("grass", "atlas", (0, 0, 16, 16)),),
    )
    return TileMapDocument(
        id="benchmark-map",
        name="Benchmark",
        tileset=tileset,
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0),),
        chunk_size=chunk_size,
    )


def main() -> int:
    results = benchmark_chunk_sizes(_document)
    fastest = min(results, key=lambda item: (item.elapsed_ms, item.chunk_size))
    print(
        json.dumps(
            {
                "candidates": [result.__dict__ for result in results],
                "selected": fastest.chunk_size,
                "selection_rule": (
                    "lowest measured insertion time; chunk size is tie-broken "
                    "by smaller value"
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
