"""Run the fail-closed quality audit for Stage 4B.5.

The audit exercises the real lateral scenario loader, runtime exporter,
orthographic preview and overlay geometry.  It records reproducible hashes and
bounded timings without persisting host paths, machine identifiers or process
metadata.  A performance limit is a safety ceiling for severe regressions; it
is not presented as a historical baseline or as a claim of a particular FPS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

from src.core.parallax_camera import OrthographicCamera
from src.core.scenario_preview import (
    ScenarioPreviewLayer,
    build_overlay_geometry,
    project_layer_points,
)
from src.exporters.scenario_exporter import serialize_scenario_runtime_export
from src.persistence.scenario_io import load_scenario, serialize_scenario
from src.persistence.scenario_schema import ScenarioDocumentV1
from tools.evidence_integrity import digest_bytes, digest_path, write_json_lf

ROOT = Path(__file__).resolve().parents[1]
INPUT_PROJECT = (
    ROOT / "docs/evidence/artifacts/stage4b3-authoring-2026-08-18/"
    "authoring_fixture.ndtproj"
)
INPUT_SCENARIO = (
    ROOT / "docs/evidence/artifacts/stage4b3-authoring-2026-08-18/"
    "authoring_fixture.ndtscenario.json"
)
DEFAULT_OUTPUT = ROOT / "docs/evidence/artifacts/stage4b5-quality-2026-08-18"

SERIALIZATION_OPERATIONS = 500
PROJECTION_OPERATIONS = 10_000
OVERLAY_OPERATIONS = 10_000
MAX_SERIALIZATION_SECONDS = 10.0
MAX_PROJECTION_SECONDS = 5.0
MAX_OVERLAY_SECONDS = 5.0


def _digest(raw: bytes) -> dict[str, Any]:
    return digest_bytes(raw)


def _git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _fixture() -> ScenarioDocumentV1:
    if not INPUT_PROJECT.is_file() or not INPUT_SCENARIO.is_file():
        raise FileNotFoundError("versioned Stage 4B.3 fixtures are missing")
    return load_scenario(INPUT_SCENARIO, project_path=INPUT_PROJECT)


def _preview_inputs(
    document: ScenarioDocumentV1,
) -> tuple[
    OrthographicCamera, tuple[ScenarioPreviewLayer, ...], list[tuple[float, float]]
]:
    camera_record = document.camera
    camera = OrthographicCamera(
        (1280.0, 720.0),
        position=(float(camera_record.position.x), float(camera_record.position.y)),
        zoom=float(camera_record.zoom),
    )
    layers = tuple(
        ScenarioPreviewLayer(
            item.id,
            tuple(item.object_ids),
            visible=item.visible,
        )
        for item in document.layers
    )
    points = [(float(index), float((index * 7) % 311)) for index in range(64)]
    return camera, layers, points


def _determinism_checks(
    document: ScenarioDocumentV1,
) -> dict[str, Any]:
    before = serialize_scenario(document)
    runtime_outputs = [serialize_scenario_runtime_export(document) for _ in range(5)]
    runtime_hashes = [hashlib.sha256(value).hexdigest() for value in runtime_outputs]
    runtime_deterministic = len(set(runtime_outputs)) == 1

    camera, layers, points = _preview_inputs(document)
    projection_outputs = [
        tuple(tuple(project_layer_points(camera, layer, points)) for layer in layers)
        for _ in range(5)
    ]
    projection_deterministic = len(set(projection_outputs)) == 1
    overlay_outputs = [
        build_overlay_geometry((1280.0, 720.0), aspect_ratio=(16, 9)) for _ in range(5)
    ]
    overlay_deterministic = len(set(overlay_outputs)) == 1
    after = serialize_scenario(document)

    return {
        "runtime_export": {
            "deterministic": runtime_deterministic,
            "hashes": runtime_hashes,
            "bytes": len(runtime_outputs[0]),
        },
        "preview_projection": {"deterministic": projection_deterministic},
        "overlay_geometry": {"deterministic": overlay_deterministic},
        "input_unchanged": before == after,
        "passed": (
            runtime_deterministic
            and projection_deterministic
            and overlay_deterministic
            and before == after
        ),
    }


def _timed(label: str, operations: int, function) -> dict[str, Any]:
    started = time.perf_counter()
    for _ in range(operations):
        function()
    elapsed = time.perf_counter() - started
    return {
        "label": label,
        "operations": operations,
        "elapsed_seconds": round(elapsed, 6),
        "operations_per_second": (
            round(operations / elapsed, 3) if elapsed > 0 else None
        ),
    }


def _benchmark(document: ScenarioDocumentV1) -> dict[str, Any]:
    runtime = serialize_scenario_runtime_export(document)
    camera, layers, points = _preview_inputs(document)
    layer = layers[0]

    serialize_result = _timed(
        "runtime_export_serialization",
        SERIALIZATION_OPERATIONS,
        lambda: serialize_scenario_runtime_export(document),
    )
    projection_result = _timed(
        "preview_projection",
        PROJECTION_OPERATIONS,
        lambda: project_layer_points(camera, layer, points),
    )
    overlay_result = _timed(
        "overlay_geometry",
        OVERLAY_OPERATIONS,
        lambda: build_overlay_geometry((1280.0, 720.0), aspect_ratio=(16, 9)),
    )
    measurements = [serialize_result, projection_result, overlay_result]
    limits = {
        "runtime_export_serialization": MAX_SERIALIZATION_SECONDS,
        "preview_projection": MAX_PROJECTION_SECONDS,
        "overlay_geometry": MAX_OVERLAY_SECONDS,
    }
    for measurement in measurements:
        measurement["max_elapsed_seconds"] = limits[measurement["label"]]
        measurement["within_limit"] = (
            measurement["elapsed_seconds"] <= measurement["max_elapsed_seconds"]
        )
    return {
        "warmup": {"runtime_export_sha256": hashlib.sha256(runtime).hexdigest()},
        "limits_are_safety_ceilings": True,
        "measurements": measurements,
        "passed": all(item["within_limit"] for item in measurements),
    }


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _write_artifacts(output: Path, document: ScenarioDocumentV1) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    expected = {
        "artifact-index.json",
        "benchmark-report.json",
        "scenario-input.ndtproj",
        "scenario-input.ndtscenario.json",
        "scenario-runtime-a.ndtscenario.runtime.json",
        "scenario-runtime-b.ndtscenario.runtime.json",
    }
    unexpected = {path.name for path in output.iterdir() if path.is_file()} - expected
    if unexpected:
        raise RuntimeError(
            f"unexpected files in evidence directory: {sorted(unexpected)}"
        )
    input_project = output / "scenario-input.ndtproj"
    input_scenario = output / "scenario-input.ndtscenario.json"
    runtime_a = output / "scenario-runtime-a.ndtscenario.runtime.json"
    runtime_b = output / "scenario-runtime-b.ndtscenario.runtime.json"
    report_path = output / "benchmark-report.json"

    input_project.write_bytes(INPUT_PROJECT.read_bytes())
    input_scenario.write_bytes(INPUT_SCENARIO.read_bytes())
    runtime_payload = serialize_scenario_runtime_export(document)
    runtime_a.write_bytes(runtime_payload)
    runtime_b.write_bytes(serialize_scenario_runtime_export(document))

    determinism = _determinism_checks(document)
    benchmark = _benchmark(document)
    report = {
        "schema_version": 1,
        "status": "PASS" if determinism["passed"] and benchmark["passed"] else "FAIL",
        "stage": "4B.5",
        "commit": _git_output("rev-parse", "HEAD"),
        "branch": "feature branch (identifier omitted by repository hygiene gate)",
        "environment": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "python": platform.python_version(),
        },
        "inputs": {
            "project": {"path": _relative(INPUT_PROJECT), **digest_path(INPUT_PROJECT)},
            "scenario": {
                "path": _relative(INPUT_SCENARIO),
                **digest_path(INPUT_SCENARIO),
            },
        },
        "checks": {
            "determinism": determinism,
            "benchmark": benchmark,
            "artifact_bytes_match": runtime_a.read_bytes() == runtime_b.read_bytes(),
        },
        "artifacts": {
            "runtime_sha256": hashlib.sha256(runtime_payload).hexdigest(),
            "runtime_bytes": len(runtime_payload),
        },
        "limitations": [
            (
                "No historical timing baseline existed before Stage 4B.5; timing "
                "values are a first reproducible local baseline."
            ),
            (
                "The audit measures the editor-side pure preview/export contracts, "
                "not an engine runtime or FPS claim."
            ),
        ],
    }
    write_json_lf(report_path, report)

    files = {
        path.name: digest_path(path)
        for path in (input_project, input_scenario, runtime_a, runtime_b, report_path)
    }
    index = {
        "schema_version": 1,
        "stage": "4B.5",
        "files": files,
        "count": len(files),
    }
    write_json_lf(output / "artifact-index.json", index)
    return report


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="new evidence directory; it must not already exist",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    try:
        document = _fixture()
        report = _write_artifacts(output, document)
    except Exception as exc:
        print(f"STAGE4B5=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    status = report["status"]
    print(f"STAGE4B5={status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
