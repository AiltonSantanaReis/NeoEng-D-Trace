#!/usr/bin/env python3
"""
Main benchmark runner for NeoEng-D-Trace.
Runs all benchmark scripts and generates a summary report.
"""

import subprocess
import sys
from pathlib import Path


def run_benchmark(script_name: str) -> bool:
    """Run a single benchmark script."""
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"❌ Benchmark script not found: {script_name}")
        return False

    print(f"\n🚀 Running {script_name}...")
    print("-" * 50)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print(result.stdout)
            print(f"PASS: {script_name} completed successfully")
            return True
        else:
            print(
                f"FAIL: {script_name} failed with return code "
                f"{result.returncode}"
            )
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"FAIL: {script_name} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"FAIL: {script_name} failed with exception: {e}")
        return False


def main():
    """Run all benchmarks."""
    print("NeoEng-D-Trace Benchmark Suite")
    print("=" * 60)

    benchmarks = [
        "benchmark_triangulation.py",
        "benchmark_convex_decomp.py",
        "benchmark_gltf_export.py",
    ]

    results = []
    for benchmark in benchmarks:
        success = run_benchmark(benchmark)
        results.append((benchmark, success))

    # Summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    successful = sum(1 for _, success in results if success)
    total = len(results)

    for benchmark, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{benchmark}: {status}")

    print(f"\nOverall: {successful}/{total} benchmarks passed")

    if successful == total:
        print("All benchmarks completed successfully!")
        return 0
    else:
        print("Some benchmarks failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
