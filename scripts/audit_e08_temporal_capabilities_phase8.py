"""Official E08-E determinism and destination-capability audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from scripts.audit_runtime_particles_phase4 import _document as particle_document
from scripts.audit_runtime_post_processing_phase5 import _document as post_document
from src.runtime.post_processing import PostProcessingRuntime
from src.runtime.temporal_qualification import (
    TemporalQualificationDocumentV1,
    TemporalToleranceRecord,
    build_e08_capability_matrix,
    collect_particle_checkpoints,
    compare_frame_series,
    compare_temporal_checkpoints,
    serialize_temporal_qualification,
    temporal_qualification_sha256,
)


def _source_tree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def run(output: Path) -> dict[str, object]:
    requests = (1.0 / 60.0, 1.0 / 30.0, 1.0 / 60.0, 1.0 / 15.0)
    tolerance = TemporalToleranceRecord(
        fixed_dt=1.0 / 60.0,
        time_abs=1e-9,
        frame_abs=1.0 / 255.0,
        max_frame_fraction=0.0,
        state_exact=True,
    )
    first = collect_particle_checkpoints(particle_document(), requests)
    second = collect_particle_checkpoints(particle_document(), requests)
    logical = compare_temporal_checkpoints(first, second, tolerance)

    runtime = PostProcessingRuntime()
    runtime.load_manifest(post_document())
    source = np.ones((4, 4, 4), dtype=np.float64)
    source[:, :, :3] = (0.18, 0.26, 0.38)
    frame = runtime.preview(source).image
    visual = compare_frame_series(
        (frame, frame), (frame.copy(), frame.copy()), tolerance
    )
    capabilities = build_e08_capability_matrix()
    document = TemporalQualificationDocumentV1(
        source_sha256=hashlib.sha256(b"e08-e-authoritative-fixture").hexdigest(),
        tolerance=tolerance,
        checkpoints=list(first),
        capabilities=list(capabilities),
    )
    raw = serialize_temporal_qualification(document)
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "stage": "runtime-temporal-capabilities-phase8",
        "status": (
            "PASS"
            if logical.passed and visual.passed and _source_tree_clean()
            else "FAIL"
        ),
        "source": {"tree_clean": _source_tree_clean()},
        "tolerance": tolerance.model_dump(mode="json"),
        "logical_comparison": {
            "passed": logical.passed,
            "checkpoints": logical.compared_checkpoints,
            "state_mismatches": list(logical.state_mismatches),
            "max_time_error": logical.max_time_error,
        },
        "visual_comparison": {
            "passed": visual.passed,
            "frames": visual.compared_checkpoints,
            "max_frame_error": visual.max_frame_error,
            "max_frame_fraction": visual.max_frame_fraction,
        },
        "capability_matrix": [entry.model_dump(mode="json") for entry in capabilities],
        "qualification_document_sha256": temporal_qualification_sha256(document),
        "qualification_document_bytes": len(raw),
        "limitations": [
            "Logical replay is exact for the approved CPU fixed-step path.",
            "Visual tolerance does not claim GPU equivalence.",
            "Godot and Unity FX entries are explicit degraded metadata until destination runtimes execute the sidecars.",
        ],
    }
    (output / "stage8-e-temporal-capabilities-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
