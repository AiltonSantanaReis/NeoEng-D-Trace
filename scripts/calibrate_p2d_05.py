"""Calibrate P2D-05 performance with separate timing and memory runs."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import struct
import subprocess
import tempfile
import time
import tracemalloc
import zlib
from pathlib import Path
from typing import Any, Callable

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.exporters.scene_authoring_export import (
    save_scene_authoring_export,
    serialize_scene_authoring_export,
)
from src.persistence.project_schema import Point3Record
from src.persistence.scene_authoring_io import (
    load_scene_authoring_v2,
    save_scene_authoring,
    serialize_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    PointRecord,
    ProjectReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _solid_png(width: int, height: int, rgba: tuple[int, int, int, int]) -> bytes:
    row = bytes(rgba) * width
    raw = b"".join(b"\x00" + row for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        _PNG_SIGNATURE
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(raw, level=6))
        + _png_chunk(b"IEND", b"")
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _document(root: Path, count: int, asset_mode: str) -> SceneAuthoringDocumentV2:
    project_bytes = b"p2d-05 performance calibration project\n"
    (root / "calibration.ndtproj").write_bytes(project_bytes)
    asset_dir = root / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets: list[AssetReferenceRecord] = []
    if asset_mode == "shared":
        payload = _solid_png(128, 128, (48, 128, 192, 255))
        path = asset_dir / "shared.png"
        path.write_bytes(payload)
        assets.append(
            AssetReferenceRecord(
                id="asset-shared",
                path="assets/shared.png",
                sha256=_sha256(payload),
            )
        )
    elif asset_mode == "unique":
        for index in range(count):
            payload = _solid_png(
                32 + index % 3 * 16,
                32 + index % 2 * 16,
                (32 + index % 192, 64 + index % 128, 96 + index % 96, 255),
            )
            path = asset_dir / f"asset-{index:05d}.png"
            path.write_bytes(payload)
            assets.append(
                AssetReferenceRecord(
                    id=f"asset-{index:05d}",
                    path=f"assets/{path.name}",
                    sha256=_sha256(payload),
                )
            )
    else:
        raise ValueError(f"unsupported asset mode: {asset_mode}")

    objects = [
        SceneObjectAuthoringRecord(
            id=f"object-{index:05d}",
            asset_id=(
                "asset-shared" if asset_mode == "shared" else f"asset-{index:05d}"
            ),
            layer_id=f"layer-{index % 3}",
            transform=SceneTransformRecord(
                position=Point3Record(
                    x=float(index % 64) * 8.0,
                    y=float(index // 64) * 8.0,
                    z=float(index % 5),
                ),
                rotation=Point3Record(x=0.0, y=0.0, z=float(index % 360)),
                scale=Point3Record(x=1.0, y=1.0, z=1.0),
                pivot=PointRecord(x=0.5, y=0.5),
            ),
        )
        for index in range(count)
    ]
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name=f"P2D-05 calibration {asset_mode}",
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        project=ProjectReferenceRecord(sha256=_sha256(project_bytes)),
        assets=assets,
        layers=[
            SceneLayerAuthoringRecord(id=f"layer-{index}", name=f"Layer {index}")
            for index in range(3)
        ],
        objects=objects,
        groups=(
            [
                SceneGroupAuthoringRecordV2(
                    id="calibration-group",
                    name="Calibration group",
                    members=[item.id for item in objects],
                    parent_group_id=None,
                )
            ]
            if objects
            else []
        ),
    )


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


def _measure(
    operation: Callable[[], Any], *, warmup: int, iterations: int
) -> dict[str, Any]:
    gc.collect()
    errors: list[dict[str, str]] = []
    for _ in range(warmup):
        try:
            operation()
        except Exception as exc:  # noqa: BLE001 - safe type only
            errors.append({"type": type(exc).__name__})
            break
    samples: list[float] = []
    if not errors:
        for _ in range(iterations):
            started = time.perf_counter_ns()
            try:
                operation()
            except Exception as exc:  # noqa: BLE001 - safe type only
                errors.append({"type": type(exc).__name__})
                break
            samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return {
        "timing_ms": _stats(samples),
        "error_count": len(errors),
        "errors": errors,
    }


def _process_memory() -> dict[str, int | None]:
    if os.name != "nt":
        return {"working_set_bytes": None, "private_bytes": None}
    import ctypes
    from ctypes import wintypes

    class _Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("page_fault_count", wintypes.DWORD),
            ("peak_working_set", ctypes.c_size_t),
            ("working_set", ctypes.c_size_t),
            ("quota_peak_paged_pool", ctypes.c_size_t),
            ("quota_paged_pool", ctypes.c_size_t),
            ("quota_peak_non_paged_pool", ctypes.c_size_t),
            ("quota_non_paged_pool", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
            ("private_usage", ctypes.c_size_t),
        ]

    counters = _Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("Kernel32.dll")
    psapi = ctypes.WinDLL("Psapi.dll")
    get_current_process = kernel32.GetCurrentProcess
    get_current_process.restype = wintypes.HANDLE
    process = get_current_process()
    get_process_memory_info = psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_Counters),
        wintypes.DWORD,
    ]
    get_process_memory_info.restype = wintypes.BOOL
    if not get_process_memory_info(process, ctypes.byref(counters), counters.cb):
        return {"working_set_bytes": None, "private_bytes": None}
    return {
        "working_set_bytes": int(counters.working_set),
        "private_bytes": int(counters.private_usage),
    }


def _memory_observation(
    document: SceneAuthoringDocumentV2,
    view: SceneAuthoringViewport,
    application: Any,
    iterations: int,
) -> dict[str, Any]:
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    session.set_selection(["object-00000"])
    gc.collect()
    process_initial = _process_memory()
    tracemalloc.start()
    traced_initial = tracemalloc.get_traced_memory()[0]
    traced_peak = traced_initial
    errors: list[dict[str, str]] = []
    for _ in range(iterations):
        try:
            session.translate_selected(
                Point3Record(x=1.0, y=0.0, z=0.0),
                description="P2D-05 calibration memory edit",
            )
            session.undo()
            view.sync()
            application.processEvents()
        except Exception as exc:  # noqa: BLE001 - safe type only
            errors.append({"type": type(exc).__name__})
            break
        _, peak = tracemalloc.get_traced_memory()
        traced_peak = max(traced_peak, peak)
    gc.collect()
    traced_final = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    return {
        "iterations": iterations,
        "python_tracemalloc": {
            "initial_bytes": traced_initial,
            "peak_bytes": traced_peak,
            "final_bytes": traced_final,
            "growth_bytes": traced_final - traced_initial,
        },
        "process_memory": {
            "initial": process_initial,
            "final": _process_memory(),
        },
        "error_count": len(errors),
        "errors": errors,
        "interpretation": "observational checkpoints; not a standalone leak verdict",
    }


def _workload(
    count: int,
    asset_mode: str,
    application: Any,
    *,
    warmup: int,
    iterations: int,
    memory_iterations: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="neoeng-p2d05-cal-") as name:
        root = Path(name)
        document = _document(root, count, asset_mode)
        scene_path = root / "calibration.ndtscene.json"
        save_scene_authoring(document, scene_path)
        session = SceneAuthoringSession(SceneAuthoringModel(document))
        session.set_selection(["object-00000"])
        view = SceneAuthoringViewport(session, project_root=root)
        view.resize(640, 480)
        view.show()
        application.processEvents()

        destinations = {
            target: root / f"calibration.{target}.runtime.json"
            for target in ("generic", "godot", "unity")
        }
        operations: dict[str, Callable[[], Any]] = {
            "serialize": lambda: serialize_scene_authoring(document),
            "load_validate": lambda: load_scene_authoring_v2(
                scene_path, verify_assets=True
            ),
            "save_atomic_recovery": lambda: save_scene_authoring(document, scene_path),
            "reload": lambda: load_scene_authoring_v2(scene_path, verify_assets=True),
            "edit_history": lambda: (
                session.translate_selected(
                    Point3Record(x=1.0, y=0.0, z=0.0),
                    description="P2D-05 calibration edit",
                ),
                session.undo(),
            ),
            "preview_sync": lambda: (view.sync(), application.processEvents()),
        }
        for target, destination in destinations.items():

            def export_operation(
                export_target: str = target,
                export_destination: Path = destination,
            ) -> Any:
                return save_scene_authoring_export(
                    document,
                    export_destination,
                    target=export_target,  # type: ignore[arg-type]
                    source_document_path=scene_path,
                )

            operations[f"export_{target}"] = export_operation
        measurements = {
            name: _measure(operation, warmup=warmup, iterations=iterations)
            for name, operation in operations.items()
        }
        memory = _memory_observation(document, view, application, memory_iterations)
        first_scene = serialize_scene_authoring(document)
        second_scene = serialize_scene_authoring(document)
        exports: dict[str, dict[str, Any]] = {}
        for target in ("generic", "godot", "unity"):
            first = serialize_scene_authoring_export(
                document, target=target  # type: ignore[arg-type]
            )
            second = serialize_scene_authoring_export(
                document, target=target  # type: ignore[arg-type]
            )
            exports[target] = {
                "bytes": len(first),
                "sha256": _sha256(first),
                "repeat_equal": first == second,
            }
        view.close()
        application.processEvents()
        return {
            "workload": {
                "object_count": count,
                "asset_mode": asset_mode,
                "asset_count": len(document.assets),
                "scene_bytes": len(first_scene),
            },
            "measurements": measurements,
            "memory": memory,
            "determinism": {
                "scene_bytes": len(first_scene),
                "scene_sha256": _sha256(first_scene),
                "scene_repeat_equal": first_scene == second_scene,
                "exports": exports,
            },
            "error_count": sum(
                int(item["error_count"]) for item in measurements.values()
            )
            + int(memory["error_count"]),
        }


def _git_value(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _parse_positive_list(value: str) -> list[int]:
    values = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not values or any(item < 1 for item in values):
        raise ValueError("object counts must be positive integers")
    return values


def _parse_asset_modes(value: str) -> list[str]:
    values = [item.strip().lower() for item in value.split(",") if item.strip()]
    if not values or any(item not in {"shared", "unique"} for item in values):
        raise ValueError("asset modes must be shared and/or unique")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--memory-iterations", type=int, default=20)
    parser.add_argument("--object-counts", default="64,128,256,512")
    parser.add_argument("--asset-modes", default="shared,unique")
    args = parser.parse_args()
    if args.iterations < 50 or args.warmup < 0 or args.memory_iterations < 1:
        parser.error(
            "iterations >= 50, warmup >= 0 and memory-iterations >= 1 required"
        )

    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    workloads = [
        _workload(
            count,
            asset_mode,
            application,
            warmup=args.warmup,
            iterations=args.iterations,
            memory_iterations=args.memory_iterations,
        )
        for asset_mode in _parse_asset_modes(args.asset_modes)
        for count in _parse_positive_list(args.object_counts)
    ]
    report = {
        "kind": "p2d-05-calibrated-performance-report",
        "schema_version": 1,
        "status": (
            "PASS" if all(item["error_count"] == 0 for item in workloads) else "FAIL"
        ),
        "source_commit": _git_value(["rev-parse", "HEAD"]),
        "branch": _git_value(["branch", "--show-current"]),
        "tracked_changes": len(
            [
                item
                for item in _git_value(
                    ["status", "--short", "--untracked-files=no"]
                ).splitlines()
                if item.strip()
            ]
        ),
        "environment": {
            "platform": platform.system(),
            "os_release": platform.release(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "qt_qpa_platform": os.environ.get("QT_QPA_PLATFORM", "default"),
            "timing_tracemalloc": False,
            "memory_measurement": (
                "tracemalloc plus process working-set/private-bytes when available"
            ),
        },
        "method": {
            "iterations": args.iterations,
            "warmup": args.warmup,
            "memory_iterations": args.memory_iterations,
            "timing_clock": "time.perf_counter_ns",
            "percentiles": ["p50", "p95", "p99", "worst"],
            "gpu": {
                "status": "not_measured",
                "reason": (
                    "no GPU counter is part of the current Qt/QGraphicsView "
                    "calibration path"
                ),
            },
        },
        "runtime_reference": {
            "target": "60 FPS",
            "frame_p95_ms": 16.7,
            "status": "not measured by operation calibration",
        },
        "normative_performance_status": (
            "MEASURED_ONLY_PENDING_EXPLICIT_BUDGET_ACCEPTANCE"
        ),
        "profiler_artifacts": [
            "artifacts/p2d05/profile-p2d05-512.prof",
            "artifacts/p2d05/profile-preview-512.prof",
            "artifacts/p2d05/profile-gesture-512.prof",
        ],
        "workloads": workloads,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "output": args.output.name}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
