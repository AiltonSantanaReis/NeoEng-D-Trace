"""Determinism and destination-capability qualification for E08-E.

The module keeps logical replay (fixed timestep, seed and state hashes) separate
from visual frame equivalence.  A CPU preview may be exact while a destination
adapter is only degraded; the capability matrix records that distinction
instead of treating a compatible sidecar as proof of engine rendering.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Literal, Sequence

import numpy as np
from pydantic import Field, field_validator, model_validator

from src.persistence.project_schema import StrictProjectModel
from src.runtime.particles import ParticleDocumentV1, ParticleSimulation

TEMPORAL_QUALIFICATION_FORMAT_ID = "neoeng-d-trace-runtime-temporal-qualification"
TEMPORAL_QUALIFICATION_SCHEMA_VERSION = 1
TEMPORAL_QUALIFICATION_ALGORITHM_VERSION = 1
MAX_TEMPORAL_CHECKPOINTS = 256
MAX_TEMPORAL_TOLERANCE = 1.0

Compatibility = Literal["native", "degraded", "incompatible"]
TemporalDestination = Literal["local-raster", "godot", "unity"]


class TemporalQualificationError(ValueError):
    """Base class for controlled temporal qualification failures."""


class TemporalQualificationValidationError(TemporalQualificationError):
    """Raised when a tolerance, checkpoint or capability matrix is invalid."""


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TemporalQualificationValidationError(f"{field} must be finite")
    number = float(value)
    if not math.isfinite(number):
        raise TemporalQualificationValidationError(f"{field} must be finite")
    return number


class TemporalToleranceRecord(StrictProjectModel):
    """Tolerance registered before a temporal comparison is measured."""

    fixed_dt: float = Field(gt=0.0, le=1.0)
    time_abs: float = Field(ge=0.0, le=MAX_TEMPORAL_TOLERANCE)
    frame_abs: float = Field(ge=0.0, le=MAX_TEMPORAL_TOLERANCE)
    max_frame_fraction: float = Field(ge=0.0, le=1.0)
    state_exact: bool = True

    @field_validator("fixed_dt", "time_abs", "frame_abs", "max_frame_fraction")
    @classmethod
    def validate_finite(cls, value: float) -> float:
        return _finite(value, "temporal tolerance")


class TemporalCheckpointRecord(StrictProjectModel):
    """One logical checkpoint at a declared simulation time."""

    sample_id: str = Field(min_length=1, max_length=64)
    elapsed_request: float = Field(ge=0.0, le=1.0)
    simulation_time: float = Field(ge=0.0, le=3600.0)
    tick_index: int = Field(ge=0)
    state_sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class CapabilityMatrixEntry(StrictProjectModel):
    """One explicit capability decision for a backend and destination."""

    destination: TemporalDestination
    backend: str = Field(min_length=1, max_length=96)
    capability: str = Field(min_length=1, max_length=96)
    compatibility: Compatibility
    mode: str = Field(min_length=1, max_length=96)
    reason: str = Field(min_length=1, max_length=512)


class TemporalQualificationDocumentV1(StrictProjectModel):
    """Canonical E08-E evidence contract."""

    format_id: Literal["neoeng-d-trace-runtime-temporal-qualification"] = (
        "neoeng-d-trace-runtime-temporal-qualification"
    )
    schema_version: Literal[1] = 1
    algorithm_version: Literal[1] = 1
    source_sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    tolerance: TemporalToleranceRecord
    checkpoints: list[TemporalCheckpointRecord] = Field(
        min_length=1, max_length=MAX_TEMPORAL_CHECKPOINTS
    )
    capabilities: list[CapabilityMatrixEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_document(self) -> "TemporalQualificationDocumentV1":
        sample_ids = [item.sample_id for item in self.checkpoints]
        if len(sample_ids) != len(set(sample_ids)):
            raise TemporalQualificationValidationError(
                "temporal checkpoint sample IDs must be unique"
            )
        keys = [
            (item.destination, item.backend, item.capability)
            for item in self.capabilities
        ]
        if len(keys) != len(set(keys)):
            raise TemporalQualificationValidationError(
                "capability matrix entries must be unique"
            )
        return self


@dataclass(frozen=True)
class TemporalComparisonReport:
    """Measured comparison without conflating logical and visual status."""

    passed: bool
    compared_checkpoints: int
    state_mismatches: tuple[str, ...]
    max_time_error: float
    max_frame_error: float
    max_frame_fraction: float


def collect_particle_checkpoints(
    document: ParticleDocumentV1,
    elapsed_requests: Sequence[float],
) -> tuple[TemporalCheckpointRecord, ...]:
    """Run one deterministic particle tape and record declared checkpoints."""

    if not elapsed_requests or len(elapsed_requests) > MAX_TEMPORAL_CHECKPOINTS:
        raise TemporalQualificationValidationError(
            "temporal checkpoint count is outside the supported range"
        )
    simulation = ParticleSimulation(document)
    simulation.start()
    records: list[TemporalCheckpointRecord] = []
    for index, elapsed in enumerate(elapsed_requests):
        value = _finite(float(elapsed), "elapsed request")
        snapshot = simulation.advance(value)
        records.append(
            TemporalCheckpointRecord(
                sample_id=f"t{index:03d}",
                elapsed_request=value,
                simulation_time=snapshot.simulation_time,
                tick_index=snapshot.tick_index,
                state_sha256=snapshot.state_sha256,
            )
        )
    return tuple(records)


def compare_temporal_checkpoints(
    reference: Sequence[TemporalCheckpointRecord],
    candidate: Sequence[TemporalCheckpointRecord],
    tolerance: TemporalToleranceRecord,
) -> TemporalComparisonReport:
    """Compare logical replay checkpoints under a pre-registered tolerance."""

    if len(reference) != len(candidate) or not reference:
        raise TemporalQualificationError(
            "temporal checkpoint series must have equal non-zero length"
        )
    mismatches: list[str] = []
    max_time_error = 0.0
    for expected, actual in zip(reference, candidate, strict=True):
        if expected.sample_id != actual.sample_id:
            mismatches.append(expected.sample_id)
            continue
        time_error = abs(
            float(expected.simulation_time) - float(actual.simulation_time)
        )
        max_time_error = max(max_time_error, time_error)
        if time_error > tolerance.time_abs:
            mismatches.append(expected.sample_id)
        if tolerance.state_exact and expected.state_sha256 != actual.state_sha256:
            mismatches.append(expected.sample_id)
    unique_mismatches = tuple(dict.fromkeys(mismatches))
    return TemporalComparisonReport(
        passed=not unique_mismatches,
        compared_checkpoints=len(reference),
        state_mismatches=unique_mismatches,
        max_time_error=max_time_error,
        max_frame_error=0.0,
        max_frame_fraction=0.0,
    )


def compare_frame_series(
    reference: Sequence[np.ndarray],
    candidate: Sequence[np.ndarray],
    tolerance: TemporalToleranceRecord,
) -> TemporalComparisonReport:
    """Compare visual frames while retaining the logical checkpoint result."""

    if len(reference) != len(candidate) or not reference:
        raise TemporalQualificationError("frame series must have equal non-zero length")
    max_error = 0.0
    max_fraction = 0.0
    mismatches: list[str] = []
    for index, (expected, actual) in enumerate(zip(reference, candidate, strict=True)):
        if not isinstance(expected, np.ndarray) or not isinstance(actual, np.ndarray):
            raise TemporalQualificationError("frame series must contain NumPy arrays")
        if expected.shape != actual.shape or expected.size == 0:
            raise TemporalQualificationError("frame shapes must match and be non-empty")
        expected_float = np.asarray(expected, dtype=np.float64)
        actual_float = np.asarray(actual, dtype=np.float64)
        if not np.isfinite(expected_float).all() or not np.isfinite(actual_float).all():
            raise TemporalQualificationError("frame series must contain finite values")
        delta = np.abs(expected_float - actual_float)
        frame_error = float(delta.max(initial=0.0))
        frame_fraction = float(np.mean(delta > tolerance.frame_abs))
        max_error = max(max_error, frame_error)
        max_fraction = max(max_fraction, frame_fraction)
        if (
            frame_error > tolerance.frame_abs
            or frame_fraction > tolerance.max_frame_fraction
        ):
            mismatches.append(f"frame-{index:03d}")
    return TemporalComparisonReport(
        passed=not mismatches,
        compared_checkpoints=len(reference),
        state_mismatches=tuple(mismatches),
        max_time_error=0.0,
        max_frame_error=max_error,
        max_frame_fraction=max_fraction,
    )


def build_e08_capability_matrix() -> tuple[CapabilityMatrixEntry, ...]:
    """Return the declared matrix; no destination is marked native by inference."""

    entries: list[CapabilityMatrixEntry] = []
    destinations: tuple[tuple[TemporalDestination, str], ...] = (
        ("local-raster", "cpu-preview"),
        ("godot", "godot-adapter-v1"),
        ("unity", "unity-adapter-v1"),
    )
    for destination, backend in destinations:
        for capability in (
            "runtime.fixed_update",
            "runtime.particles",
            "runtime.shaders",
            "runtime.post_processing",
        ):
            if destination == "local-raster":
                compatibility: Compatibility = "native"
                mode = "deterministic-cpu-preview"
                reason = "The approved local reference runtime executes this capability deterministically."
            elif capability == "runtime.fixed_update":
                compatibility = "native"
                mode = "adapter-fixed-tick-contract"
                reason = "The adapter contract records fixed-step semantics, but visual equivalence is separate."
            else:
                compatibility = "degraded"
                mode = "validated-sidecar-metadata"
                reason = "Destination adapter metadata is validated; native destination rendering is not implemented in E08-E."
            entries.append(
                CapabilityMatrixEntry(
                    destination=destination,
                    backend=backend,
                    capability=capability,
                    compatibility=compatibility,
                    mode=mode,
                    reason=reason,
                )
            )
    return tuple(entries)


def serialize_temporal_qualification(
    document: TemporalQualificationDocumentV1,
) -> bytes:
    """Serialize the E08-E document canonically for evidence hashing."""

    payload = document.model_dump(mode="json")
    encoded = (
        json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")
    return encoded


def temporal_qualification_sha256(document: TemporalQualificationDocumentV1) -> str:
    return hashlib.sha256(serialize_temporal_qualification(document)).hexdigest()


__all__ = [
    "CapabilityMatrixEntry",
    "Compatibility",
    "TemporalCheckpointRecord",
    "TemporalComparisonReport",
    "TemporalDestination",
    "TemporalQualificationDocumentV1",
    "TemporalQualificationError",
    "TemporalQualificationValidationError",
    "TemporalToleranceRecord",
    "build_e08_capability_matrix",
    "collect_particle_checkpoints",
    "compare_frame_series",
    "compare_temporal_checkpoints",
    "serialize_temporal_qualification",
    "temporal_qualification_sha256",
]
