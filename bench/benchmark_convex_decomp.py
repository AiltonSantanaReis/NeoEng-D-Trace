#!/usr/bin/env python3
"""
Benchmark script for NeoEng-D-Trace convex decomposition performance.
Measures time and memory usage for convex decomposition operations.
"""

from src.physics.convex_decomp import convex_decompose_polygon
import time
import tracemalloc
import statistics
from typing import List, Tuple
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def generate_test_polygons() -> List[List[Tuple[float, float]]]:
    """
    Generate test polygons of various complexities for convex decomposition.
    """
    polygons = []

    # Simple triangle (already convex)
    polygons.append([(0, 0), (1, 0), (0.5, 1)])

    # Square (already convex)
    polygons.append([(0, 0), (1, 0), (1, 1), (0, 1)])

    # L-shape (concave, needs decomposition)
    polygons.append([(0, 0), (2, 0), (2, 2), (1, 2), (1, 1), (0, 1)])

    # Complex concave polygon
    polygons.append(
        [
            (0, 0),
            (3, 0),
            (3, 1),
            (2, 1),
            (2, 2),
            (3, 2),
            (3, 3),
            (0, 3),
            (0, 2),
            (1, 2),
            (1, 1),
            (0, 1),
        ]
    )

    # Star shape (10 vertices, concave)
    import math

    star = []
    for i in range(10):
        angle = i * math.pi / 5
        radius = 1 if i % 2 == 0 else 0.5
        star.append((radius * math.cos(angle), radius * math.sin(angle)))
    polygons.append(star)

    # Large complex polygon (30 vertices)
    large = []
    for i in range(30):
        angle = i * 2 * math.pi / 30
        radius = 1 + 0.3 * (i % 3)  # Vary radius for complexity
        large.append((radius * math.cos(angle), radius * math.sin(angle)))
    polygons.append(large)

    return polygons


def benchmark_convex_decomposition(
    polygons: List[List[Tuple[float, float]]], iterations: int = 50
) -> dict:
    """Benchmark convex decomposition performance."""
    results = {
        "polygon_sizes": [],
        "times": [],
        "memory_peaks": [],
        "convex_parts": [],
        "total_vertices": [],
    }

    for polygon in polygons:
        times = []
        memories = []
        convex_parts = 0
        total_vertices = 0

        print(
            f"Benchmarking convex decomposition for polygon with "
            f"{len(polygon)} vertices..."
        )

        for _ in range(iterations):
            tracemalloc.start()
            start_time = time.perf_counter()

            convex_polygons = convex_decompose_polygon(polygon)

            end_time = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            times.append(end_time - start_time)
            memories.append(peak)
            convex_parts = len(convex_polygons)
            total_vertices = sum(len(p) for p in convex_polygons)

        results["polygon_sizes"].append(len(polygon))
        results["times"].append(times)
        results["memory_peaks"].append(memories)
        results["convex_parts"].append(convex_parts)
        results["total_vertices"].append(total_vertices)

    return results


def print_results(results: dict):
    """Print benchmark results in a readable format."""
    print("\n" + "=" * 60)
    print("CONVEX DECOMPOSITION BENCHMARK RESULTS")
    print("=" * 60)

    for i, size in enumerate(results["polygon_sizes"]):
        times = results["times"][i]
        memories = results["memory_peaks"][i]
        parts = results["convex_parts"][i]
        vertices = results["total_vertices"][i]

        print(f"\nInput Polygon Size: {size} vertices")
        print(f"  Convex Parts: {parts}")
        print(f"  Total Output Vertices: {vertices}")
        print(f"  Avg Time: {statistics.mean(times)*1000:.2f} ms")
        print(f"  Min Time: {min(times)*1000:.2f} ms")
        print(f"  Max Time: {max(times)*1000:.2f} ms")
        print(f"  Std Dev: {statistics.stdev(times)*1000:.2f} ms")
        print(f"  Avg Memory: {statistics.mean(memories)/1024:.1f} KB")
        print(f"  Peak Memory: {max(memories)/1024:.1f} KB")


def main():
    """Main benchmark function."""
    print("Starting NeoEng-D-Trace Convex Decomposition Benchmarks...")

    polygons = generate_test_polygons()
    # Fewer iterations for complex polygons
    results = benchmark_convex_decomposition(polygons, iterations=30)
    print_results(results)

    print("\nBenchmark completed successfully!")


if __name__ == "__main__":
    main()
