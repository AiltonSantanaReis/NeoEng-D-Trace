"""Compare full and delta history finalization for P2D-05 O-1."""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.calibrate_p2d_05 import _document
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    ratio = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * ratio


def _stats(values: list[float]) -> dict[str, float | int]:
    return {
        "sample_count": len(values),
        "mean_ms": sum(values) / len(values) if values else 0.0,
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "p99_ms": _percentile(values, 0.99),
        "worst_ms": max(values, default=0.0),
    }


def _run_variant(
    count: int,
    asset_mode: str,
    *,
    optimized: bool,
    warmup: int,
    iterations: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="neoeng-p2d05-o1-finish-") as name:
        document = _document(Path(name), count, asset_mode)
        session = SceneAuthoringSession(SceneAuthoringModel(document))
        session.set_selection(["object-00000"])
        samples: list[float] = []
        errors: list[dict[str, str]] = []
        for index in range(warmup + iterations):
            try:
                session.begin_gesture()
                session.preview_transform_selected(
                    translation=Point3Record(
                        x=float(index % 17 + 1), y=float(index % 11 + 1), z=0.0
                    )
                )
                if not optimized:
                    session._gesture_transform_history_safe = False
                started = time.perf_counter_ns()
                changed = session.finish_gesture("P2D-05 O-1 finish benchmark")
                elapsed = (time.perf_counter_ns() - started) / 1_000_000.0
                if not changed:
                    raise RuntimeError("gesture finalization produced no change")
                if not session.undo():
                    raise RuntimeError("gesture finalization could not undo")
                if index >= warmup:
                    samples.append(elapsed)
            except Exception as exc:  # noqa: BLE001 - diagnostic type only
                errors.append({"type": type(exc).__name__})
                break
        return {
            "timing_ms": _stats(samples),
            "error_count": len(errors),
            "errors": errors,
        }


def _git_value(arguments: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *arguments], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--object-counts", default="64,128,256,512")
    parser.add_argument("--asset-modes", default="shared,unique")
    args = parser.parse_args()
    if args.iterations < 50 or args.warmup < 0:
        parser.error("iterations >= 50 and warmup >= 0 required")

    workloads: list[dict[str, Any]] = []
    for asset_mode in (item.strip() for item in args.asset_modes.split(",")):
        for raw_count in (item.strip() for item in args.object_counts.split(",")):
            count = int(raw_count)
            legacy = _run_variant(
                count,
                asset_mode,
                optimized=False,
                warmup=args.warmup,
                iterations=args.iterations,
            )
            optimized = _run_variant(
                count,
                asset_mode,
                optimized=True,
                warmup=args.warmup,
                iterations=args.iterations,
            )
            legacy_p95 = legacy["timing_ms"]["p95_ms"]
            optimized_p95 = optimized["timing_ms"]["p95_ms"]
            improvement = (
                ((legacy_p95 - optimized_p95) / legacy_p95) * 100.0
                if legacy_p95
                else 0.0
            )
            workloads.append(
                {
                    "asset_mode": asset_mode,
                    "object_count": count,
                    "legacy_full_history": legacy,
                    "optimized_delta_history": optimized,
                    "p95_improvement_percent": improvement,
                    "error_count": legacy["error_count"] + optimized["error_count"],
                }
            )

    report = {
        "kind": "p2d-05-o1-gesture-finish-ab-report",
        "schema_version": 1,
        "status": (
            "PASS" if all(item["error_count"] == 0 for item in workloads) else "FAIL"
        ),
        "source_commit": _git_value(["rev-parse", "HEAD"]),
        "branch": _git_value(["branch", "--show-current"]),
        "environment": {
            "platform": os.name,
            "timing_clock": "time.perf_counter_ns",
            "timing_tracemalloc": False,
        },
        "method": {
            "iterations": args.iterations,
            "warmup": args.warmup,
            "legacy_variant": "full document snapshot at gesture finish",
            "optimized_variant": "transform-only delta at gesture finish",
            "interpretation": (
                "controlled A/B of history finalization; not a product budget"
            ),
        },
        "workloads": workloads,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "output": args.output.name}))
    gc.collect()
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
