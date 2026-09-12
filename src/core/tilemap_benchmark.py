"""Small deterministic chunk-size benchmark used to qualify E04-A."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from time import perf_counter

from src.core.tilemap_model import TileCell, TileMapDocument


@dataclass(frozen=True)
class ChunkBenchmark:
    chunk_size: int
    populated_cells: int
    populated_chunks: int
    elapsed_ms: float


def benchmark_chunk_sizes(
    factory: object,
    *,
    candidates: tuple[int, ...] = (16, 32, 64),
    width: int = 64,
    height: int = 64,
    repetitions: int = 3,
) -> tuple[ChunkBenchmark, ...]:
    """Measure sparse insertion for each approved candidate on one machine.

    ``factory`` is intentionally a callable-like object rather than a concrete
    map type so the benchmark remains independent of Qt and persistence.
    """

    if not callable(factory):
        raise TypeError("factory must be callable")
    if width <= 0 or height <= 0:
        raise ValueError("benchmark dimensions must be positive")
    if repetitions <= 0:
        raise ValueError("benchmark repetitions must be positive")
    results: list[ChunkBenchmark] = []
    for chunk_size in candidates:
        samples: list[float] = []
        document: TileMapDocument | None = None
        for _ in range(repetitions):
            candidate = factory(chunk_size)
            if not isinstance(candidate, TileMapDocument):
                raise TypeError("factory must return TileMapDocument")
            document = candidate
            started = perf_counter()
            for y in range(height):
                for x in range(width):
                    document.set_cell("ground", (x, y), TileCell("grass"))
            samples.append((perf_counter() - started) * 1000.0)
        assert document is not None
        results.append(
            ChunkBenchmark(
                chunk_size,
                document.populated_cell_count,
                document.populated_chunk_count,
                float(median(samples)),
            )
        )
    return tuple(results)


__all__ = ["ChunkBenchmark", "benchmark_chunk_sizes"]
