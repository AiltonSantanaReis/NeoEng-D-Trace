"""In-memory contracts for the NeoEng multiaxis conformance gate.

Stage C1 intentionally defines semantics only. Existing auditors are not
rewritten here, and serialized evidence formats are deferred to Stage C2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ConformanceAxis(str, Enum):
    """The three independent, blocking product-conformance axes."""

    GEOMETRY_PHYSICS = "G"
    VISUAL_SYSTEM = "V"
    BEHAVIOR_INTERACTION = "B"


AXIS_ORDER = (
    ConformanceAxis.GEOMETRY_PHYSICS,
    ConformanceAxis.VISUAL_SYSTEM,
    ConformanceAxis.BEHAVIOR_INTERACTION,
)

AXIS_DOMAINS: dict[ConformanceAxis, tuple[str, ...]] = {
    ConformanceAxis.GEOMETRY_PHYSICS: (
        "layout",
        "viewport",
        "alignment",
        "transform",
        "collision",
        "snap",
    ),
    ConformanceAxis.VISUAL_SYSTEM: (
        "token",
        "palette",
        "typography",
        "iconography",
        "spacing",
        "contrast",
        "visual-state",
    ),
    ConformanceAxis.BEHAVIOR_INTERACTION: (
        "action",
        "command",
        "selection",
        "interaction-state",
        "shortcut",
        "persistence",
        "undo-redo",
        "gizmo",
    ),
}


class ConformanceStatus(str, Enum):
    """Canonical result states for checks, axes, and the aggregate gate."""

    PASS = "PASS"
    FAIL = "FAIL"
    APPROVED_BASELINE_CHANGE = "APPROVED_BASELINE_CHANGE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


_CHECK_ID = re.compile(r"^(?P<axis>[GVB])-[A-Z][A-Z0-9_]*-[0-9]{3}$")


@dataclass(frozen=True, slots=True)
class ConformanceCheck:
    """One atomic check owned by exactly one conformance axis and domain."""

    check_id: str
    axis: ConformanceAxis
    domain: str
    status: ConformanceStatus
    source: str
    summary: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        match = _CHECK_ID.fullmatch(self.check_id)
        if match is None:
            raise ValueError(f"invalid conformance check ID: {self.check_id!r}")
        if match.group("axis") != self.axis.value:
            raise ValueError(
                "conformance check ID axis does not match declared axis: "
                f"{self.check_id!r} != {self.axis.value!r}"
            )
        if self.domain not in AXIS_DOMAINS[self.axis]:
            raise ValueError(
                f"domain {self.domain!r} is not valid for axis {self.axis.value}"
            )
        if not self.source.strip():
            raise ValueError("conformance check source must not be empty")
        if not self.summary.strip():
            raise ValueError("conformance check summary must not be empty")


_STATUS_PRECEDENCE = {
    ConformanceStatus.NOT_APPLICABLE: 0,
    ConformanceStatus.PASS: 1,
    ConformanceStatus.APPROVED_BASELINE_CHANGE: 2,
    ConformanceStatus.FAIL: 3,
}


def aggregate_status(statuses: Iterable[ConformanceStatus]) -> ConformanceStatus:
    """Aggregate statuses deterministically using fail-closed precedence.

    FAIL dominates. An approved baseline change remains visible instead of
    being silently collapsed into PASS. PASS dominates NOT_APPLICABLE, while an
    empty/all-NOT_APPLICABLE set remains NOT_APPLICABLE.
    """

    materialized = tuple(statuses)
    if not materialized:
        return ConformanceStatus.NOT_APPLICABLE
    return max(materialized, key=_STATUS_PRECEDENCE.__getitem__)


@dataclass(frozen=True, slots=True)
class AxisResult:
    """Deterministic aggregate of all checks owned by one axis."""

    axis: ConformanceAxis
    checks: tuple[ConformanceCheck, ...]

    def __post_init__(self) -> None:
        foreign = tuple(check.check_id for check in self.checks if check.axis != self.axis)
        if foreign:
            raise ValueError(
                f"axis result {self.axis.value} contains foreign checks: {foreign!r}"
            )

    @property
    def status(self) -> ConformanceStatus:
        return aggregate_status(check.status for check in self.checks)

    @property
    def failures(self) -> tuple[ConformanceCheck, ...]:
        return tuple(
            check for check in self.checks if check.status == ConformanceStatus.FAIL
        )

    @property
    def approved_changes(self) -> tuple[ConformanceCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if check.status == ConformanceStatus.APPROVED_BASELINE_CHANGE
        )

    @property
    def is_blocking(self) -> bool:
        return self.status == ConformanceStatus.FAIL


@dataclass(frozen=True, slots=True)
class MultiAxisConformance:
    """Canonical aggregate over independent G/V/B results.

    Historical compatibility evidence is intentionally absent from this model;
    Stage C2 may reference it as supporting evidence without granting it axis
    semantics or blocking precedence.
    """

    source_baseline: str
    checks: tuple[ConformanceCheck, ...]

    def __post_init__(self) -> None:
        if not self.source_baseline.strip():
            raise ValueError("source baseline must not be empty")
        ids = tuple(check.check_id for check in self.checks)
        if len(ids) != len(set(ids)):
            raise ValueError("conformance check IDs must be globally unique")

    def axis_result(self, axis: ConformanceAxis) -> AxisResult:
        return AxisResult(
            axis=axis,
            checks=tuple(check for check in self.checks if check.axis == axis),
        )

    def axis_results(self) -> tuple[AxisResult, ...]:
        return tuple(self.axis_result(axis) for axis in AXIS_ORDER)

    @property
    def status(self) -> ConformanceStatus:
        return aggregate_status(result.status for result in self.axis_results())

    @property
    def is_blocking(self) -> bool:
        return self.status == ConformanceStatus.FAIL
