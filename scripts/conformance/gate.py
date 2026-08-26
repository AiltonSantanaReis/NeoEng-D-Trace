"""Aggregate NeoEng G/V/B conformance gate.

Stage C2F composes the three first concrete axis adapters into one canonical
NeoEng Conformance Gate.  It preserves the central multiaxis rule: product
status comes only from atomic G/V/B checks.  Historical material remains
supporting evidence, while malformed, stale, or incomplete input evidence is
reported as a gate-execution error rather than being misclassified as a
product-axis finding.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.conformance.adapters import (
    AdaptedConformance,
    AdapterContext,
    AdapterResult,
    combine_adapter_results,
    run_adapter,
)
from scripts.conformance.contracts import (
    AXIS_ORDER,
    ConformanceAxis,
    ConformanceStatus,
)
from scripts.conformance.evidence import write_evidence_json
from scripts.conformance.stage1_visual_adapter import Stage1VisualSystemAdapter
from scripts.conformance.stage9_behavior_adapter import Stage9FunctionalBehaviorAdapter
from scripts.conformance.stage9_geometry_adapter import Stage9ResponsiveGeometryAdapter


@dataclass(frozen=True, slots=True)
class GateInput:
    """One legacy/current auditor payload with its stable evidence reference."""

    payload: Any
    source_reference: str

    def __post_init__(self) -> None:
        if not self.source_reference.strip():
            raise ValueError("gate input source_reference must not be empty")


@dataclass(frozen=True, slots=True)
class AggregateGateResult:
    """Completed canonical G/V/B gate result."""

    adapted: AdaptedConformance

    @property
    def status(self) -> ConformanceStatus:
        return self.adapted.report.status

    @property
    def blocking(self) -> bool:
        return self.adapted.report.is_blocking

    @property
    def exit_code(self) -> int:
        """Process exit code for a successfully executed conformance gate."""

        return 1 if self.blocking else 0

    def axis_statuses(self) -> dict[str, str]:
        return {
            result.axis.value: result.status.value
            for result in self.adapted.report.axis_results()
        }

    def write_evidence(self, path: Path, *, producer: str) -> dict[str, Any]:
        """Write the canonical C2A evidence envelope for this gate result."""

        return write_evidence_json(
            path,
            self.adapted.report,
            producer=producer,
            historical_evidence=self.adapted.historical_evidence,
        )


_ADAPTERS = (
    (
        Stage9ResponsiveGeometryAdapter(),
        ConformanceAxis.GEOMETRY_PHYSICS,
        "stage9 responsive geometry",
    ),
    (
        Stage1VisualSystemAdapter(),
        ConformanceAxis.VISUAL_SYSTEM,
        "stage1 visual system",
    ),
    (
        Stage9FunctionalBehaviorAdapter(),
        ConformanceAxis.BEHAVIOR_INTERACTION,
        "stage9 functional behavior",
    ),
)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _source_commit(payload: Any, *, label: str) -> str:
    report = _require_mapping(payload, label)
    source = _require_mapping(report.get("source"), f"{label}.source")
    commit = source.get("commit")
    if not isinstance(commit, str) or not commit.strip():
        raise ValueError(f"{label}.source.commit must be a non-empty string")
    return commit


def _validate_provenance(
    gate_input: GateInput,
    *,
    source_baseline: str,
    label: str,
    validate_worker_sources: bool = False,
) -> None:
    commit = _source_commit(gate_input.payload, label=label)
    if commit != source_baseline:
        raise ValueError(
            f"{label} source commit does not match gate source_baseline: "
            f"{commit!r} != {source_baseline!r}"
        )

    if not validate_worker_sources:
        return

    report = _require_mapping(gate_input.payload, label)
    workers = report.get("workers")
    if not isinstance(workers, list):
        raise ValueError(f"{label}.workers must be an array")
    for index, worker in enumerate(workers):
        worker_label = f"{label}.workers[{index}]"
        worker_commit = _source_commit(worker, label=worker_label)
        if worker_commit != source_baseline:
            raise ValueError(
                f"{worker_label} source commit does not match gate "
                f"source_baseline: {worker_commit!r} != {source_baseline!r}"
            )


def _validate_adapter_axis(
    result: AdapterResult,
    *,
    expected_axis: ConformanceAxis,
) -> None:
    if not result.checks:
        raise ValueError(
            f"adapter {result.adapter_name!r} emitted no canonical checks for "
            f"required axis {expected_axis.value}"
        )
    foreign = tuple(
        check.check_id for check in result.checks if check.axis != expected_axis
    )
    if foreign:
        raise ValueError(
            f"adapter {result.adapter_name!r} emitted checks outside required axis "
            f"{expected_axis.value}: {foreign!r}"
        )


def _validate_complete_gate(adapted: AdaptedConformance) -> None:
    expected_names = tuple(sorted(adapter.name for adapter, _axis, _label in _ADAPTERS))
    if adapted.adapter_names != expected_names:
        raise ValueError(
            "aggregate gate adapter set is incomplete or unexpected: "
            f"{adapted.adapter_names!r} != {expected_names!r}"
        )

    for axis in AXIS_ORDER:
        axis_result = adapted.report.axis_result(axis)
        if not axis_result.checks:
            raise ValueError(
                f"aggregate gate has no checks for required axis {axis.value}"
            )
        if axis_result.status == ConformanceStatus.NOT_APPLICABLE:
            raise ValueError(
                f"aggregate gate required axis {axis.value} is NOT_APPLICABLE"
            )


def run_aggregate_gate(
    *,
    source_baseline: str,
    geometry: GateInput,
    visual: GateInput,
    behavior: GateInput,
) -> AggregateGateResult:
    """Run the canonical NeoEng G/V/B gate from three auditor payloads.

    Provenance mismatches and adapter/schema errors are execution errors.  Once
    all three adapters execute successfully, product blocking is derived only
    from their atomic canonical checks.
    """

    if not source_baseline.strip():
        raise ValueError("gate source_baseline must not be empty")

    inputs = (geometry, visual, behavior)
    _validate_provenance(
        geometry,
        source_baseline=source_baseline,
        label="stage9 responsive geometry",
        validate_worker_sources=True,
    )
    _validate_provenance(
        visual,
        source_baseline=source_baseline,
        label="stage1 visual system",
    )
    _validate_provenance(
        behavior,
        source_baseline=source_baseline,
        label="stage9 functional behavior",
    )

    results: list[AdapterResult] = []
    for gate_input, (adapter, expected_axis, _label) in zip(inputs, _ADAPTERS):
        result = run_adapter(
            adapter,
            gate_input.payload,
            context=AdapterContext(
                source_baseline=source_baseline,
                source_reference=gate_input.source_reference,
            ),
        )
        _validate_adapter_axis(result, expected_axis=expected_axis)
        results.append(result)

    adapted = combine_adapter_results(tuple(results), source_baseline=source_baseline)
    _validate_complete_gate(adapted)
    return AggregateGateResult(adapted=adapted)
