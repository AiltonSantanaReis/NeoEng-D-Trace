"""Controlled P2D-05/O-2 preview and viewport baseline producer.

The harness reuses one viewport per workload and resets the authored fixture
between operations. This keeps harness allocation separate from the measured
Qt path while preserving the real session/viewport callbacks.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import subprocess
import tempfile
import tracemalloc
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QEvent, QPointF
from PySide6.QtWidgets import QApplication

from scripts.calibrate_p2d_05 import (
    _document,
    _measure,
    _process_memory,
    _sha256,
)
from src.core.scene_authoring_model import SceneAuthoringModel, SceneSelection
from src.core.scene_authoring_preview import build_scene_authoring_preview
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneGroupAuthoringRecordV2,
    SceneLightSocketRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneTransformRecord,
    SceneTriggerSocketRecord,
    SceneVfxSocketRecord,
)
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

O2_HEAD = "15300a0d580a57110828d8511ae48a0f68326e3a"
RESOLUTIONS: tuple[tuple[int, int], ...] = (
    (1280, 720),
    (1366, 768),
    (1920, 1080),
)
CORE_OPERATIONS = (
    "full_sync",
    "incremental_refresh",
    "selection_refresh",
    "preview_toggle",
    "navigation_zoom",
    "navigation_pan",
    "navigation_fit",
    "navigation_resize",
    "preview_frame_build",
    "user_gesture_cycle",
)
STRUCTURAL_OPERATIONS = (
    "object_add_remove",
    "asset_update",
    "layer_visibility_toggle",
    "layer_reorder_toggle",
    "group_visibility_toggle",
    "group_membership_toggle",
    "group_isolation_toggle",
)


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


def _representative_document(
    root: Path, count: int, asset_mode: str
) -> SceneAuthoringDocumentV2:
    base = _document(root, count, asset_mode)
    midpoint = max(1, count // 2)
    groups = [
        SceneGroupAuthoringRecordV2(
            id="calibration-group-a",
            name="Calibration group A",
            members=[item.id for item in base.objects[:midpoint]],
            parent_group_id=None,
        ),
        SceneGroupAuthoringRecordV2(
            id="calibration-group-b",
            name="Calibration group B",
            members=[item.id for item in base.objects[midpoint:]],
            parent_group_id=None,
        ),
    ]
    parallax_layers = [
        SceneParallaxLayerRecord(
            layer_id=f"layer-{index}",
            depth=float(index) * 0.25,
            translation_strength=1.0 - index * 0.1,
            zoom_strength=1.0 - index * 0.05,
        )
        for index in range(3)
    ]
    sockets = [
        SceneLightSocketRecord(
            id="socket-light",
            layer_id="layer-0",
            object_id="object-00000",
            position=Point3Record(x=24.0, y=24.0, z=0.0),
            color="#ffd166",
            intensity=1.0,
            radius=96.0,
        ),
        SceneVfxSocketRecord(
            id="socket-vfx",
            layer_id="layer-1",
            object_id=None,
            position=Point3Record(x=96.0, y=48.0, z=0.0),
            effect_id="calibration-spark",
            scale=1.0,
            enabled=True,
        ),
        SceneTriggerSocketRecord(
            id="socket-trigger",
            layer_id="layer-2",
            object_id=None,
            position=Point3Record(x=160.0, y=80.0, z=0.0),
            event_id="calibration-trigger",
            size=Point3Record(x=48.0, y=32.0, z=1.0),
        ),
    ]
    return base.model_copy(
        update={
            "groups": groups,
            "parallax_layers": parallax_layers,
            "sockets": sockets,
        }
    )


def _geometries(
    document: SceneAuthoringDocumentV2,
) -> dict[str, tuple[tuple[float, float], ...]]:
    return {
        item.id: ((-32.0, -24.0), (32.0, -24.0), (32.0, 24.0), (-32.0, 24.0))
        for item in document.objects
    }


class _Harness:
    def __init__(
        self,
        document: SceneAuthoringDocumentV2,
        root: Path,
        application: QApplication,
        width: int,
        height: int,
    ) -> None:
        self.document = document
        self.application = application
        self.width = width
        self.height = height
        self.session = SceneAuthoringSession(
            SceneAuthoringModel(document.model_copy(deep=True))
        )
        self.session.set_selection(["object-00000"])
        self.view = SceneAuthoringViewport(self.session, project_root=root)
        self.view.resize(width, height)
        self.view.show()
        application.processEvents()

    def reset(self) -> None:
        """Restore the fixture outside the timed operation window."""

        self.session.model.document = self.document.model_copy(deep=True)
        self.session.model.selection = SceneSelection.from_ids(
            ["object-00000"], "object-00000"
        )
        self.session._undo.clear()
        self.session._redo.clear()
        self.session._gesture_before = None
        self.session._gesture_transform_before = None
        self.session._gesture_selection_before = None
        self.session._gesture_transform_history_safe = False
        self.session._isolated_group_id = None
        self.view._preview_enabled = False
        self.view._navigation_zoom = 1.0
        self.view._navigation_center = None
        self.view.sync()
        self.view._set_navigation_state(1.0, self.view._natural_navigation_center())
        self.application.processEvents()

    def close(self) -> None:
        self.view.close()
        self.view.setScene(None)
        self.view.graphics_scene.clear()
        self.view.deleteLater()
        self.application.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.application.processEvents()


def _operation(
    name: str,
    harness: _Harness,
) -> tuple[Callable[[], Any], str]:
    session = harness.session
    view = harness.view
    application = harness.application
    document = harness.document
    width, height = harness.width, harness.height
    geometries = _geometries(document)

    if name == "full_sync":

        def full_sync_operation() -> None:
            view.sync()
            application.processEvents()

        return (
            full_sync_operation,
            "complete QGraphicsScene rebuild with asset resolution",
        )
    if name == "incremental_refresh":

        def incremental_refresh_operation() -> None:
            view._refresh_after_model_change()
            application.processEvents()

        return (
            incremental_refresh_operation,
            "transform, selection, gizmo and viewport repaint refresh",
        )
    if name == "selection_refresh":
        ids = [item.id for item in document.objects]
        selection_ids = ids[:2]
        selection_state: dict[str, bool] = {"multi": False}

        def selection_operation() -> Any:
            selection_state["multi"] = not selection_state["multi"]
            selected = selection_ids if selection_state["multi"] else ids[:1]
            return session.set_selection(selected, selected[-1])

        return selection_operation, "real session selection notification and refresh"
    if name == "preview_toggle":
        return (
            lambda: view.set_preview_enabled(not view.is_preview_enabled()),
            "authoring/preview toggle including the current full sync path",
        )
    if name == "navigation_zoom":
        zoom_state: dict[str, bool] = {"forward": False}

        def zoom_operation() -> Any:
            zoom_state["forward"] = not zoom_state["forward"]
            return view._zoom_at(
                view._viewport_center(),
                120.0 if zoom_state["forward"] else -120.0,
            )

        return zoom_operation, "anchored user-wheel zoom path"
    if name == "navigation_pan":
        pan_state: dict[str, float] = {"offset": 0.0}

        def pan_operation() -> Any:
            pan_state["offset"] = 24.0 if pan_state["offset"] == 0.0 else 0.0
            center = view.navigation_center
            return view._set_navigation_state(
                view.navigation_zoom,
                QPointF(center.x() + pan_state["offset"], center.y() + 12.0),
            )

        return pan_operation, "transient viewport pan and navigation transform"
    if name == "navigation_fit":
        return view.fit_all, "fit-all bounds calculation and navigation transform"
    if name == "navigation_resize":
        resize_state: dict[str, bool] = {"alternate": False}

        def resize_operation() -> Any:
            resize_state["alternate"] = not resize_state["alternate"]
            extra = 1 if resize_state["alternate"] else 0
            view.resize(width + extra, height + extra)
            application.processEvents()
            return view.size()

        return resize_operation, "real resize event and navigation reflow"
    if name == "preview_frame_build":
        return (
            lambda: build_scene_authoring_preview(
                document,
                (float(width), float(height)),
                geometries,
                isolated_group_id=session.isolated_group_id,
            ),
            "deterministic non-Qt preview frame projection",
        )
    if name == "user_gesture_cycle":
        gesture_state: dict[str, float] = {"offset": 0.0}

        def gesture_operation() -> Any:
            gesture_state["offset"] = 1.0 if gesture_state["offset"] == 0.0 else 0.0
            session.begin_gesture()
            session.preview_transform_selected(
                translation=Point3Record(x=gesture_state["offset"], y=0.0, z=0.0)
            )
            application.processEvents()
            session.cancel_gesture()
            application.processEvents()

        return gesture_operation, "real preview-transform plus cancel flow"
    if name == "object_add_remove":
        probe = SceneObjectAuthoringRecord(
            id="o2-probe-object",
            asset_id=document.assets[0].id,
            layer_id="layer-0",
            transform=SceneTransformRecord(
                position=Point3Record(x=512.0, y=512.0, z=0.0),
                rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                scale=Point3Record(x=1.0, y=1.0, z=1.0),
                pivot=PointRecord(x=0.5, y=0.5),
            ),
        )
        add_remove_state: dict[str, bool] = {"present": False}

        def add_remove_operation() -> Any:
            add_remove_state["present"] = not add_remove_state["present"]
            return (
                session.add_object(probe, select=False)
                if add_remove_state["present"]
                else session.remove_object(probe.id)
            )

        return add_remove_operation, "structural object change and scene rebuild"
    if name == "asset_update":
        original = document.assets[0]
        alternate = original.model_copy(update={"source_path": "fixture-source.png"})
        asset_state: dict[str, bool] = {"alternate": False}

        def asset_operation() -> Any:
            asset_state["alternate"] = not asset_state["alternate"]
            return session.update_asset(
                alternate if asset_state["alternate"] else original
            )

        return asset_operation, "asset-reference revision and scene rebuild"
    if name == "layer_visibility_toggle":
        layer_visibility_state: dict[str, bool] = {"visible": True}

        def layer_visibility_operation() -> Any:
            layer_visibility_state["visible"] = not layer_visibility_state["visible"]
            return session.set_layer_visibility(
                "layer-1", layer_visibility_state["visible"]
            )

        return (
            layer_visibility_operation,
            "layer visibility and visible-object filtering",
        )
    if name == "layer_reorder_toggle":
        layer_reorder_state: dict[str, bool] = {"moved": False}

        def layer_reorder_operation() -> Any:
            layer_reorder_state["moved"] = not layer_reorder_state["moved"]
            return session.reorder_layer(
                "layer-0", 2 if layer_reorder_state["moved"] else 0
            )

        return layer_reorder_operation, "canonical layer order and scene rebuild"
    if name == "group_visibility_toggle":
        group_visibility_state: dict[str, bool] = {"visible": True}

        def group_visibility_operation() -> Any:
            group_visibility_state["visible"] = not group_visibility_state["visible"]
            return session.set_group_visibility(
                "calibration-group-a", group_visibility_state["visible"]
            )

        return group_visibility_operation, "group visibility and membership filtering"
    if name == "group_membership_toggle":
        membership_state: dict[str, bool] = {"member": True}

        def membership_operation() -> Any:
            membership_state["member"] = not membership_state["member"]
            if membership_state["member"]:
                return session.add_objects_to_group(
                    "calibration-group-a", ["object-00000"]
                )
            return session.remove_objects_from_group(
                "calibration-group-a", ["object-00000"]
            )

        return (
            membership_operation,
            "group membership and effective visibility evaluation",
        )
    if name == "group_isolation_toggle":
        isolation_state: dict[str, bool] = {"isolated": False}

        def isolation_operation() -> Any:
            isolation_state["isolated"] = not isolation_state["isolated"]
            return session.set_isolated_group(
                "calibration-group-a" if isolation_state["isolated"] else None
            )

        return isolation_operation, "transient isolation and visible-object filtering"
    raise ValueError(f"unsupported O-2 operation: {name}")


def _memory_observation(
    harness: _Harness,
    iterations: int,
) -> dict[str, Any]:
    gc.collect()
    process_initial = _process_memory()
    tracemalloc.start()
    traced_initial = tracemalloc.get_traced_memory()[0]
    traced_peak = traced_initial
    errors: list[dict[str, str]] = []
    for _ in range(iterations):
        try:
            harness.view._refresh_after_model_change()
            harness.application.processEvents()
        except Exception as exc:  # noqa: BLE001 - evidence producer boundary
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
    root: Path,
    count: int,
    asset_mode: str,
    width: int,
    height: int,
    application: QApplication,
    operation_names: tuple[str, ...],
    *,
    warmup: int,
    iterations: int,
    memory_iterations: int,
) -> dict[str, Any]:
    document = _representative_document(root, count, asset_mode)
    harness = _Harness(document, root, application, width, height)
    measurements: dict[str, Any] = {}
    details: dict[str, str] = {}
    try:
        for name in operation_names:
            harness.reset()
            operation, detail = _operation(name, harness)
            measurements[name] = _measure(
                operation, warmup=warmup, iterations=iterations
            )
            details[name] = detail
        harness.reset()
        memory = _memory_observation(harness, memory_iterations)
        geometries = _geometries(document)
        first_frame = build_scene_authoring_preview(
            document, (float(width), float(height)), geometries
        )
        second_frame = build_scene_authoring_preview(
            document, (float(width), float(height)), geometries
        )
        frame_digest = _sha256(repr(first_frame).encode("utf-8"))
        return {
            "workload": {
                "object_count": count,
                "asset_mode": asset_mode,
                "asset_count": len(document.assets),
                "resolution": {"width": width, "height": height},
                "socket_count": len(document.sockets),
                "group_count": len(document.groups),
                "layer_count": len(document.layers),
            },
            "measurements": measurements,
            "operation_details": details,
            "memory": memory,
            "determinism": {
                "preview_object_count": len(first_frame.objects),
                "preview_socket_count": len(first_frame.sockets),
                "preview_repr_sha256": frame_digest,
                "preview_repeat_equal": first_frame == second_frame,
            },
            "error_count": sum(
                int(item["error_count"]) for item in measurements.values()
            )
            + int(memory["error_count"]),
        }
    finally:
        harness.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--memory-iterations", type=int, default=20)
    parser.add_argument("--object-counts", default="64,128,256,512")
    parser.add_argument("--asset-modes", default="shared,unique")
    parser.add_argument(
        "--expected-source-commit",
        default=O2_HEAD,
        help="Expected commit to bind this run (defaults to the O-2-0 baseline HEAD).",
    )
    args = parser.parse_args()
    if args.iterations < 50 or args.warmup < 0 or args.memory_iterations < 1:
        parser.error(
            "iterations >= 50, warmup >= 0 and memory-iterations >= 1 required"
        )
    expected_source_commit = args.expected_source_commit
    if _git_value(["rev-parse", "HEAD"]) != expected_source_commit:
        parser.error("benchmark must run at the expected source commit")

    existing_application = QApplication.instance()
    application = (
        existing_application
        if isinstance(existing_application, QApplication)
        else QApplication([])
    )
    counts = _parse_positive_list(args.object_counts)
    asset_modes = _parse_asset_modes(args.asset_modes)
    workloads: list[dict[str, Any]] = []
    structural_workloads: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="neoeng-p2d05-o2-") as name:
        root = Path(name)
        for asset_mode in asset_modes:
            for count in counts:
                for width, height in RESOLUTIONS:
                    workloads.append(
                        _workload(
                            root,
                            count,
                            asset_mode,
                            width,
                            height,
                            application,
                            CORE_OPERATIONS,
                            warmup=args.warmup,
                            iterations=args.iterations,
                            memory_iterations=args.memory_iterations,
                        )
                    )
                    print(
                        json.dumps(
                            {
                                "status": "PROGRESS",
                                "completed": len(workloads),
                                "total": len(asset_modes)
                                * len(counts)
                                * len(RESOLUTIONS)
                                + len(asset_modes),
                                "asset_mode": asset_mode,
                                "object_count": count,
                                "resolution": f"{width}x{height}",
                            }
                        ),
                        flush=True,
                    )
        for asset_mode in asset_modes:
            structural_workloads.append(
                _workload(
                    root,
                    512,
                    asset_mode,
                    1920,
                    1080,
                    application,
                    STRUCTURAL_OPERATIONS,
                    warmup=args.warmup,
                    iterations=args.iterations,
                    memory_iterations=args.memory_iterations,
                )
            )
            print(
                json.dumps(
                    {
                        "status": "PROGRESS",
                        "completed": len(workloads) + len(structural_workloads),
                        "total": len(asset_modes) * len(counts) * len(RESOLUTIONS)
                        + len(asset_modes),
                        "asset_mode": asset_mode,
                        "object_count": 512,
                        "resolution": "1920x1080",
                        "structural": True,
                    }
                ),
                flush=True,
            )

    all_workloads = workloads + structural_workloads
    report = {
        "kind": "p2d-05-o2-preview-viewport-baseline",
        "schema_version": 2,
        "status": (
            "PASS"
            if all(item["error_count"] == 0 for item in all_workloads)
            else "FAIL"
        ),
        "source_commit": _git_value(["rev-parse", "HEAD"]),
        "expected_source_commit": expected_source_commit,
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
            "resolution_matrix": [
                {"width": width, "height": height} for width, height in RESOLUTIONS
            ],
            "core_operations": list(CORE_OPERATIONS),
            "structural_operations": list(STRUCTURAL_OPERATIONS),
            "structural_matrix_scope": "512 objects at 1920x1080 per asset mode",
            "harness_scope": (
                "one reusable viewport per workload; fixture reset and teardown "
                "outside timed operation"
            ),
            "gpu": {
                "status": "not_measured",
                "reason": "no GPU counter is part of the controlled QGraphicsView path",
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
        "historical_comparison": {
            "report": "artifacts/p2d05/calibration-o1-final-20260830.json",
            "status": "reference_only_not_o2_baseline",
        },
        "workloads": workloads,
        "structural_workloads": structural_workloads,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "source_commit": report["source_commit"],
                "workloads": len(all_workloads),
                "output": args.output.name,
            }
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
