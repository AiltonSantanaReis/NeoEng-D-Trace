"""Adapter boundary for NeoEng multiaxis conformance.

Stage C2B defines how existing auditors may feed canonical G/V/B checks without
changing those auditors or importing their aggregate PASS/FAIL status blindly.
Concrete auditor mappings are intentionally deferred to C2C/C2D/C2E.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from scripts.conformance.contracts import ConformanceCheck, MultiAxisConformance
from scripts.conformance.evidence import HistoricalEvidence, build_evidence_document

_ADAPTER_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class AdapterContext:
    """Immutable provenance supplied to one adapter invocation."""

    source_baseline: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.source_baseline.strip():
            raise ValueError("adapter source_baseline must not be empty")
        if not self.source_reference.strip():
            raise ValueError("adapter source_reference must not be empty")


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """Canonical output from one adapter invocation.

    Adapters emit atomic G/V/B checks plus optional non-blocking historical
    context. They do not emit an aggregate axis or overall status; those are
    recomputed by the canonical contracts and evidence schema.
    """

    adapter_name: str
    checks: tuple[ConformanceCheck, ...] = ()
    historical_evidence: tuple[HistoricalEvidence, ...] = ()

    def __post_init__(self) -> None:
        if _ADAPTER_NAME.fullmatch(self.adapter_name) is None:
            raise ValueError(
                "adapter_name must be a stable lowercase slug containing only "
                "letters, digits, '.', '_' or '-': "
                f"{self.adapter_name!r}"
            )
        check_ids = tuple(check.check_id for check in self.checks)
        if len(check_ids) != len(set(check_ids)):
            raise ValueError(
                f"adapter {self.adapter_name!r} emitted duplicate check IDs"
            )


@runtime_checkable
class ConformanceAdapter(Protocol):
    """Protocol implemented by concrete auditor adapters."""

    name: str

    def adapt(self, payload: Any, *, context: AdapterContext) -> AdapterResult:
        """Translate one auditor payload into atomic canonical evidence."""
        ...


@dataclass(frozen=True, slots=True)
class AdaptedConformance:
    """Deterministic combination of one or more adapter results."""

    source_baseline: str
    adapter_names: tuple[str, ...]
    report: MultiAxisConformance
    historical_evidence: tuple[HistoricalEvidence, ...]

    def build_evidence_document(self, *, producer: str) -> dict[str, Any]:
        """Serialize through the canonical C2A evidence envelope."""

        return build_evidence_document(
            self.report,
            producer=producer,
            historical_evidence=self.historical_evidence,
        )


def run_adapter(
    adapter: ConformanceAdapter,
    payload: Any,
    *,
    context: AdapterContext,
) -> AdapterResult:
    """Invoke an adapter and validate its declared identity and result type."""

    name = getattr(adapter, "name", None)
    if not isinstance(name, str) or _ADAPTER_NAME.fullmatch(name) is None:
        raise ValueError(f"adapter exposes invalid name: {name!r}")

    result = adapter.adapt(payload, context=context)
    if not isinstance(result, AdapterResult):
        raise TypeError(
            f"adapter {name!r} must return AdapterResult, "
            f"got {type(result).__name__}"
        )
    if result.adapter_name != name:
        raise ValueError(
            f"adapter identity mismatch: declared {name!r}, "
            f"returned {result.adapter_name!r}"
        )
    return result


def combine_adapter_results(
    results: tuple[AdapterResult, ...],
    *,
    source_baseline: str,
) -> AdaptedConformance:
    """Combine adapter outputs into one fail-closed G/V/B report.

    Check IDs are globally unique across adapters. The function does not trust
    or accept aggregate statuses from legacy auditors; only canonical atomic
    checks participate in aggregation.
    """

    if not source_baseline.strip():
        raise ValueError("source_baseline must not be empty")

    check_owner: dict[str, str] = {}
    checks: list[ConformanceCheck] = []
    historical: list[HistoricalEvidence] = []
    names: list[str] = []

    for result in results:
        if not isinstance(result, AdapterResult):
            raise TypeError("results must contain only AdapterResult values")
        names.append(result.adapter_name)
        historical.extend(result.historical_evidence)
        for check in result.checks:
            previous = check_owner.get(check.check_id)
            if previous is not None:
                raise ValueError(
                    f"duplicate conformance check ID {check.check_id!r} emitted by "
                    f"adapters {previous!r} and {result.adapter_name!r}"
                )
            check_owner[check.check_id] = result.adapter_name
            checks.append(check)

    ordered_checks = tuple(sorted(checks, key=lambda check: check.check_id))
    ordered_history = tuple(
        sorted(
            historical,
            key=lambda item: (item.source, item.reference, item.summary),
        )
    )
    ordered_names = tuple(sorted(names))

    return AdaptedConformance(
        source_baseline=source_baseline,
        adapter_names=ordered_names,
        report=MultiAxisConformance(
            source_baseline=source_baseline,
            checks=ordered_checks,
        ),
        historical_evidence=ordered_history,
    )
