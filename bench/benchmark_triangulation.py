#!/usr/bin/env python3
"""
Benchmark script for NeoEng-D-Trace triangulation performance.
Measures time and memory usage for polygon triangulation operations.
"""

from src.physics.convex_decomp import triangulate_to_convex
import time
import tracemalloc
import statistics
from typing import List, Tuple
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def generate_test_polygons() -> List[List[Tuple[float, float]]]:
    """Generate test polygons of various complexities."""
    polygons = []

    # Simple triangle
    polygons.append([(0, 0), (1, 0), (0.5, 1)])

    # Square
    polygons.append([(0, 0), (1, 0), (1, 1), (0, 1)])

    # Complex concave polygon (L-shape)
    polygons.append([(0, 0), (2, 0), (2, 2), (1, 2), (1, 1), (0, 1)])

    # Star shape (10 vertices)
    import math

    star = []
    for i in range(10):
        angle = i * math.pi / 5
        radius = 1 if i % 2 == 0 else 0.5
        star.append((radius * math.cos(angle), radius * math.sin(angle)))
    polygons.append(star)

    # Large polygon (50 vertices)
    large = []
    for i in range(50):
        angle = i * 2 * math.pi / 50
        large.append((math.cos(angle), math.sin(angle)))
    polygons.append(large)

    return polygons


def benchmark_triangulation(
    polygons: List[List[Tuple[float, float]]], iterations: int = 100
) -> dict:
    """Benchmark triangulation performance."""
    results = {
        "polygon_sizes": [],
        "times": [],
        "memory_peaks": [],
        "triangles_generated": [],
    }

    for polygon in polygons:
        times = []
        memories = []
        triangles_count = 0

        print(f"Benchmarking polygon with {len(polygon)} vertices...")

        for _ in range(iterations):
            tracemalloc.start()
            start_time = time.perf_counter()

            triangles = triangulate_to_convex(polygon)

            end_time = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            times.append(end_time - start_time)
            memories.append(peak)
            triangles_count = len(triangles)

        results["polygon_sizes"].append(len(polygon))
        results["times"].append(times)
        results["memory_peaks"].append(memories)
        results["triangles_generated"].append(triangles_count)

    return results


def print_results(results: dict):
    """Print benchmark results in a readable format."""
    print("\n" + "=" * 60)
    print("TRIANGULATION BENCHMARK RESULTS")
    print("=" * 60)

    for i, size in enumerate(results["polygon_sizes"]):
        times = results["times"][i]
        memories = results["memory_peaks"][i]
        triangles = results["triangles_generated"][i]

        print(f"\nPolygon Size: {size} vertices")
        print(f"  Triangles Generated: {triangles}")
        print(f"  Avg Time: {statistics.mean(times)*1000:.2f} ms")
        print(f"  Min Time: {min(times)*1000:.2f} ms")
        print(f"  Max Time: {max(times)*1000:.2f} ms")
        print(f"  Std Dev: {statistics.stdev(times)*1000:.2f} ms")
        print(f"  Avg Memory: {statistics.mean(memories)/1024:.1f} KB")
        print(f"  Peak Memory: {max(memories)/1024:.1f} KB")


def main():
    """Main benchmark function."""
    print("Starting NeoEng-D-Trace Triangulation Benchmarks...")

    polygons = generate_test_polygons()
    results = benchmark_triangulation(polygons, iterations=50)
    print_results(results)

    print("\nBenchmark completed successfully!")


if __name__ == "__main__":
    main()
