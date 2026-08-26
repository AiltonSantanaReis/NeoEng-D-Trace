"""Unified serialized evidence for NeoEng multiaxis conformance.

Stage C2A defines the evidence envelope only. Adapters that translate existing
legacy/current auditors into atomic G/V/B checks are introduced in later C2
stages. Historical material may be attached as supporting evidence, but it is
never promoted to a fourth blocking axis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from scripts.conformance.contracts import (
    AXIS_ORDER,
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
    MultiAxisConformance,
    aggregate_status,
)

EVIDENCE_SCHEMA_VERSION = 1
EVIDENCE_KIND = "neoeng.multiaxis-conformance"

_AXIS_NAMES = {
    ConformanceAxis.GEOMETRY_PHYSICS: "Geometry & Physics",
    ConformanceAxis.VISUAL_SYSTEM: "Visual System",
    ConformanceAxis.BEHAVIOR_INTERACTION: "Behavior & Interaction",
}


@dataclass(frozen=True, slots=True)
class HistoricalEvidence:
    """Non-blocking historical context attached to a conformance report."""

    source: str
    reference: str
    summary: str

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("historical evidence source must not be empty")
        if not self.reference.strip():
            raise ValueError("historical evidence reference must not be empty")
        if not self.summary.strip():
            raise ValueError("historical evidence summary must not be empty")

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "reference": self.reference,
            "summary": self.summary,
        }


def _check_to_dict(check: ConformanceCheck) -> dict[str, Any]:
    return {
        "id": check.check_id,
        "axis": check.axis.value,
        "domain": check.domain,
        "status": check.status.value,
        "source": check.source,
        "summary": check.summary,
        "evidence": list(check.evidence),
    }


def _axis_to_dict(report: MultiAxisConformance, axis: ConformanceAxis) -> dict[str, Any]:
    result = report.axis_result(axis)
    checks = tuple(sorted(result.checks, key=lambda item: item.check_id))
    return {
        "name": _AXIS_NAMES[axis],
        "status": result.status.value,
        "blocking": result.is_blocking,
        "check_count": len(checks),
        "failure_count": len(result.failures),
        "approved_change_count": len(result.approved_changes),
        "checks": [_check_to_dict(check) for check in checks],
    }


def build_evidence_document(
    report: MultiAxisConformance,
    *,
    producer: str,
    historical_evidence: Iterable[HistoricalEvidence] = (),
) -> dict[str, Any]:
    """Build a deterministic schema-v1 evidence document from a G/V/B report."""

    if not producer.strip():
        raise ValueError("evidence producer must not be empty")

    historical = tuple(historical_evidence)
    document = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "kind": EVIDENCE_KIND,
        "source_baseline": report.source_baseline,
        "status": report.status.value,
        "blocking": report.is_blocking,
        "producer": producer,
        "axes": {
            axis.value: _axis_to_dict(report, axis)
            for axis in AXIS_ORDER
        },
        "historical_evidence": [item.as_dict() for item in historical],
    }
    validate_evidence_document(document)
    return document


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _parse_status(value: Any, label: str) -> ConformanceStatus:
    try:
        return ConformanceStatus(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} has invalid conformance status: {value!r}") from exc


def _validate_historical_evidence(items: Any) -> None:
    if not isinstance(items, list):
        raise ValueError("historical_evidence must be an array")
    for index, raw in enumerate(items):
        item = _require_mapping(raw, f"historical_evidence[{index}]")
        HistoricalEvidence(
            source=str(item.get("source", "")),
            reference=str(item.get("reference", "")),
            summary=str(item.get("summary", "")),
        )


def validate_evidence_document(document: Mapping[str, Any]) -> None:
    """Validate schema-v1 evidence and reject inconsistent/tampered aggregates.

    Validation is intentionally fail-closed: exactly G/V/B are accepted as
    product axes, status/count aggregates are recomputed, and historical
    evidence is validated outside the blocking axis map.
    """

    if document.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported conformance evidence schema_version: "
            f"{document.get('schema_version')!r}"
        )
    if document.get("kind") != EVIDENCE_KIND:
        raise ValueError(f"invalid conformance evidence kind: {document.get('kind')!r}")
    if not isinstance(document.get("source_baseline"), str) or not document[
        "source_baseline"
    ].strip():
        raise ValueError("source_baseline must be a non-empty string")
    if not isinstance(document.get("producer"), str) or not document["producer"].strip():
        raise ValueError("producer must be a non-empty string")

    axes = _require_mapping(document.get("axes"), "axes")
    expected_axis_keys = tuple(axis.value for axis in AXIS_ORDER)
    if set(axes) != set(expected_axis_keys):
        raise ValueError(
            "axes must contain exactly G, V, and B; "
            f"found {tuple(axes)!r}"
        )

    all_check_ids: list[str] = []
    axis_statuses: list[ConformanceStatus] = []

    for axis in AXIS_ORDER:
        raw_axis = _require_mapping(axes[axis.value], f"axes.{axis.value}")
        if raw_axis.get("name") != _AXIS_NAMES[axis]:
            raise ValueError(f"axes.{axis.value}.name does not match canonical axis name")

        raw_checks = raw_axis.get("checks")
        if not isinstance(raw_checks, list):
            raise ValueError(f"axes.{axis.value}.checks must be an array")

        checks: list[ConformanceCheck] = []
        for index, raw_check in enumerate(raw_checks):
            check = _require_mapping(raw_check, f"axes.{axis.value}.checks[{index}]")
            evidence = check.get("evidence", [])
            if not isinstance(evidence, list) or not all(
                isinstance(item, str) for item in evidence
            ):
                raise ValueError(
                    f"axes.{axis.value}.checks[{index}].evidence must be an array of strings"
                )
            try:
                declared_axis = ConformanceAxis(check.get("axis"))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"axes.{axis.value}.checks[{index}].axis is invalid"
                ) from exc
            parsed = ConformanceCheck(
                check_id=str(check.get("id", "")),
                axis=declared_axis,
                domain=str(check.get("domain", "")),
                status=_parse_status(
                    check.get("status"),
                    f"axes.{axis.value}.checks[{index}].status",
                ),
                source=str(check.get("source", "")),
                summary=str(check.get("summary", "")),
                evidence=tuple(evidence),
            )
            if parsed.axis != axis:
                raise ValueError(
                    f"check {parsed.check_id!r} is stored under axis {axis.value} "
                    f"but declares {parsed.axis.value}"
                )
            checks.append(parsed)
            all_check_ids.append(parsed.check_id)

        if len(all_check_ids) != len(set(all_check_ids)):
            raise ValueError("conformance evidence check IDs must be globally unique")

        computed_status = aggregate_status(check.status for check in checks)
        declared_status = _parse_status(raw_axis.get("status"), f"axes.{axis.value}.status")
        if declared_status != computed_status:
            raise ValueError(f"axes.{axis.value}.status does not match its checks")

        expected_blocking = computed_status == ConformanceStatus.FAIL
        if raw_axis.get("blocking") is not expected_blocking:
            raise ValueError(f"axes.{axis.value}.blocking does not match its status")
        if raw_axis.get("check_count") != len(checks):
            raise ValueError(f"axes.{axis.value}.check_count does not match its checks")
        if raw_axis.get("failure_count") != sum(
            check.status == ConformanceStatus.FAIL for check in checks
        ):
            raise ValueError(f"axes.{axis.value}.failure_count does not match its checks")
        if raw_axis.get("approved_change_count") != sum(
            check.status == ConformanceStatus.APPROVED_BASELINE_CHANGE
            for check in checks
        ):
            raise ValueError(
                f"axes.{axis.value}.approved_change_count does not match its checks"
            )
        axis_statuses.append(computed_status)

    overall_status = aggregate_status(axis_statuses)
    declared_overall = _parse_status(document.get("status"), "status")
    if declared_overall != overall_status:
        raise ValueError("overall status does not match G/V/B axis statuses")
    if document.get("blocking") is not (overall_status == ConformanceStatus.FAIL):
        raise ValueError("overall blocking flag does not match overall status")

    _validate_historical_evidence(document.get("historical_evidence"))


def write_evidence_json(
    path: Path,
    report: MultiAxisConformance,
    *,
    producer: str,
    historical_evidence: Iterable[HistoricalEvidence] = (),
) -> dict[str, Any]:
    """Write canonical deterministic JSON evidence and return its document."""

    document = build_evidence_document(
        report,
        producer=producer,
        historical_evidence=historical_evidence,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return document


def read_evidence_json(path: Path) -> dict[str, Any]:
    """Read and validate canonical conformance evidence from disk."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    document = dict(_require_mapping(raw, "document"))
    validate_evidence_document(document)
    return document
