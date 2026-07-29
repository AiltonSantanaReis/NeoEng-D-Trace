#!/usr/bin/env python3
"""
Benchmark script for NeoEng-D-Trace GLTF export performance.
Measures time and memory usage for GLTF export operations.
"""

from src.exporters.gltf_exporter import export_scene_to_gltf
from src.models.scene import Scene, SceneObject
import time
import tracemalloc
import statistics
import tempfile
import os
from typing import List, Tuple
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def generate_test_scenes() -> List[Scene]:
    """Generate test scenes of various complexities."""
    scenes = []

    # Scene 1: Single triangle
    scene1 = Scene()
    obj1 = SceneObject("tri", [(0, 0), (1, 0), (0.5, 1)], "default")
    scene1.objects["tri"] = obj1
    scenes.append(("single_triangle", scene1))

    # Scene 2: Multiple simple objects
    scene2 = Scene()
    objects = [
        ("square", [(0, 0), (1, 0), (1, 1), (0, 1)]),
        ("triangle", [(2, 0), (3, 0), (2.5, 1)]),
        ("pentagon", [(0, 2), (1, 2), (1.5, 3), (0.5, 3.5), (0, 3)]),
    ]
    for name, poly in objects:
        scene2.objects[name] = SceneObject(name, poly, "default")
    scenes.append(("multiple_simple", scene2))

    # Scene 3: Complex concave objects
    scene3 = Scene()
    complex_objects = [
        ("l_shape", [(0, 0), (2, 0), (2, 2), (1, 2), (1, 1), (0, 1)]),
        ("star", generate_star_polygon(10)),
        ("complex", generate_complex_polygon(20)),
    ]
    for name, poly in complex_objects:
        scene3.objects[name] = SceneObject(name, poly, "default")
    scenes.append(("complex_objects", scene3))

    # Scene 4: Large scene (many objects)
    scene4 = Scene()
    for i in range(20):
        x_offset = (i % 5) * 2
        y_offset = (i // 5) * 2
        poly = [
            (x_offset + x, y_offset + y) for x, y in [(0, 0), (1, 0), (0.5, 1)]
        ]
        scene4.objects[f"obj_{i}"] = SceneObject(f"obj_{i}", poly, "default")
    scenes.append(("large_scene", scene4))

    return scenes


def generate_star_polygon(points: int) -> List[Tuple[float, float]]:
    """Generate a star polygon."""
    import math

    star = []
    for i in range(points):
        angle = i * 2 * math.pi / points
        radius = 1 if i % 2 == 0 else 0.5
        star.append((radius * math.cos(angle), radius * math.sin(angle)))
    return star


def generate_complex_polygon(vertices: int) -> List[Tuple[float, float]]:
    """Generate a complex polygon."""
    import math

    poly = []
    for i in range(vertices):
        angle = i * 2 * math.pi / vertices
        radius = 1 + 0.2 * math.sin(angle * 3)  # Add some complexity
        poly.append((radius * math.cos(angle), radius * math.sin(angle)))
    return poly


def benchmark_gltf_export(
    scenes: List[Tuple[str, Scene]], iterations: int = 20
) -> dict:
    """Benchmark GLTF export performance."""
    results = {
        "scene_names": [],
        "object_counts": [],
        "times": [],
        "memory_peaks": [],
        "file_sizes": [],
    }

    for scene_name, scene in scenes:
        times = []
        memories = []
        file_sizes = []

        print(
            f"Benchmarking GLTF export for scene '{scene_name}' "
            f"with {len(scene.objects)} objects..."
        )

        for _ in range(iterations):
            with tempfile.NamedTemporaryFile(
                suffix=".glb", delete=False
            ) as tmp:
                tmp_path = tmp.name

            try:
                tracemalloc.start()
                start_time = time.perf_counter()

                success = export_scene_to_gltf(scene, tmp_path)

                end_time = time.perf_counter()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                if success:
                    file_size = os.path.getsize(tmp_path)
                    times.append(end_time - start_time)
                    memories.append(peak)
                    file_sizes.append(file_size)

            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        results["scene_names"].append(scene_name)
        results["object_counts"].append(len(scene.objects))
        results["times"].append(times)
        results["memory_peaks"].append(memories)
        results["file_sizes"].append(file_sizes)

    return results


def print_results(results: dict):
    """Print benchmark results in a readable format."""
    print("\n" + "=" * 60)
    print("GLTF EXPORT BENCHMARK RESULTS")
    print("=" * 60)

    for i, scene_name in enumerate(results["scene_names"]):
        obj_count = results["object_counts"][i]
        times = results["times"][i]
        memories = results["memory_peaks"][i]
        file_sizes = results["file_sizes"][i]

        if not times:
            print(f"\nScene '{scene_name}': No successful exports")
            continue

        print(f"\nScene '{scene_name}': {obj_count} objects")
        print(f"  Avg File Size: {statistics.mean(file_sizes):.0f} bytes")
        print(f"  Avg Time: {statistics.mean(times)*1000:.2f} ms")
        print(f"  Min Time: {min(times)*1000:.2f} ms")
        print(f"  Max Time: {max(times)*1000:.2f} ms")
        print(f"  Std Dev: {statistics.stdev(times)*1000:.2f} ms")
        print(f"  Avg Memory: {statistics.mean(memories)/1024:.1f} KB")
        print(f"  Peak Memory: {max(memories)/1024:.1f} KB")


def main():
    """Main benchmark function."""
    print("Starting NeoEng-D-Trace GLTF Export Benchmarks...")

    scenes = generate_test_scenes()
    # Fewer iterations for I/O operations
    results = benchmark_gltf_export(scenes, iterations=10)
    print_results(results)

    print("\nBenchmark completed successfully!")


if __name__ == "__main__":
    main()
