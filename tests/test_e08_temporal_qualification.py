"""E08-E determinism, tolerance and destination matrix checks."""

from __future__ import annotations

import numpy as np
import pytest
from pydantic import ValidationError

from scripts.audit_runtime_particles_phase4 import _document as particle_document
from src.runtime.temporal_qualification import (
    TemporalQualificationDocumentV1,
    TemporalToleranceRecord,
    build_e08_capability_matrix,
    collect_particle_checkpoints,
    compare_frame_series,
    compare_temporal_checkpoints,
    serialize_temporal_qualification,
)


def _tolerance() -> TemporalToleranceRecord:
    return TemporalToleranceRecord(
        fixed_dt=1.0 / 60.0,
        time_abs=1e-9,
        frame_abs=1.0 / 255.0,
        max_frame_fraction=0.0,
        state_exact=True,
    )


def test_particle_checkpoints_are_reproducible_at_declared_times() -> None:
    requests = (1.0 / 60.0, 1.0 / 30.0, 1.0 / 60.0)
    first = collect_particle_checkpoints(particle_document(), requests)
    second = collect_particle_checkpoints(particle_document(), requests)

    report = compare_temporal_checkpoints(first, second, _tolerance())
    assert report.passed
    assert report.compared_checkpoints == 3
    assert report.state_mismatches == ()


def test_frame_comparison_records_visual_tolerance_and_rejects_excess() -> None:
    source = np.zeros((2, 2, 4), dtype=np.float64)
    within = source + (1.0 / 255.0)
    beyond = source.copy()
    beyond[0, 0, 0] = 0.2

    assert compare_frame_series((source,), (within,), _tolerance()).passed
    rejected = compare_frame_series((source,), (beyond,), _tolerance())
    assert not rejected.passed
    assert rejected.max_frame_fraction > 0.0


def test_capability_matrix_is_explicit_about_local_and_destinations() -> None:
    entries = build_e08_capability_matrix()
    assert len(entries) == 12
    assert {entry.destination for entry in entries} == {
        "local-raster",
        "godot",
        "unity",
    }
    assert all(entry.reason for entry in entries)
    assert any(
        entry.destination == "godot"
        and entry.capability == "runtime.post_processing"
        and entry.compatibility == "degraded"
        for entry in entries
    )


def test_qualification_document_is_canonical_and_rejects_duplicate_samples() -> None:
    checkpoints = collect_particle_checkpoints(particle_document(), (1.0 / 60.0,))
    document = TemporalQualificationDocumentV1(
        source_sha256="a" * 64,
        tolerance=_tolerance(),
        checkpoints=list(checkpoints),
        capabilities=list(build_e08_capability_matrix()),
    )
    raw = serialize_temporal_qualification(document)
    assert raw.endswith(b"\n")
    assert b"local-raster" in raw

    with pytest.raises(ValidationError, match="sample IDs"):
        TemporalQualificationDocumentV1(
            source_sha256="a" * 64,
            tolerance=_tolerance(),
            checkpoints=[checkpoints[0], checkpoints[0].model_copy()],
            capabilities=list(build_e08_capability_matrix()),
        )
