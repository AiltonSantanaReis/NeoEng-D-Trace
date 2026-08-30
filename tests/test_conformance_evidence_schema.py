"""Schema-v1 tests for deterministic multiaxis conformance evidence."""

from __future__ import annotations

import copy

import pytest

from scripts.conformance import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA_VERSION,
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
    HistoricalEvidence,
    MultiAxisConformance,
    build_evidence_document,
    read_evidence_json,
    validate_evidence_document,
    write_evidence_json,
)


def _check(
    check_id: str,
    axis: ConformanceAxis,
    domain: str,
    status: ConformanceStatus,
) -> ConformanceCheck:
    return ConformanceCheck(
        check_id=check_id,
        axis=axis,
        domain=domain,
        status=status,
        source="tests/fixture-auditor",
        summary=f"fixture {check_id}",
        evidence=("artifact://fixture",),
    )


def _report() -> MultiAxisConformance:
    return MultiAxisConformance(
        source_baseline="39002f1230357d843613914c9524d5d06a833002",
        checks=(
            _check(
                "B-ACTION-001",
                ConformanceAxis.BEHAVIOR_INTERACTION,
                "action",
                ConformanceStatus.PASS,
            ),
            _check(
                "G-LAYOUT-001",
                ConformanceAxis.GEOMETRY_PHYSICS,
                "layout",
                ConformanceStatus.PASS,
            ),
            _check(
                "V-TOKEN-001",
                ConformanceAxis.VISUAL_SYSTEM,
                "token",
                ConformanceStatus.APPROVED_BASELINE_CHANGE,
            ),
        ),
    )


def test_schema_v1_contains_exactly_three_blocking_axes_and_no_h_axis():
    document = build_evidence_document(_report(), producer="tests")

    assert document["schema_version"] == EVIDENCE_SCHEMA_VERSION == 1
    assert document["kind"] == EVIDENCE_KIND
    assert tuple(document["axes"]) == ("G", "V", "B")
    assert "H" not in document["axes"]
    assert document["status"] == "APPROVED_BASELINE_CHANGE"
    assert document["blocking"] is False


def test_checks_are_serialized_deterministically_inside_each_axis():
    report = MultiAxisConformance(
        source_baseline="39002f1",
        checks=(
            _check(
                "G-VIEWPORT-002",
                ConformanceAxis.GEOMETRY_PHYSICS,
                "viewport",
                ConformanceStatus.PASS,
            ),
            _check(
                "G-LAYOUT-001",
                ConformanceAxis.GEOMETRY_PHYSICS,
                "layout",
                ConformanceStatus.PASS,
            ),
        ),
    )
    document = build_evidence_document(report, producer="tests")

    assert [item["id"] for item in document["axes"]["G"]["checks"]] == [
        "G-LAYOUT-001",
        "G-VIEWPORT-002",
    ]
    assert document["axes"]["G"]["check_count"] == 2


def test_historical_evidence_is_non_blocking_supporting_context():
    document = build_evidence_document(
        _report(),
        producer="tests",
        historical_evidence=(
            HistoricalEvidence(
                source="scripts/audit_stage1_ui_theme.py",
                reference="schema2/reference_top_toolbar",
                summary="Historical geometry reference retained for comparison.",
            ),
        ),
    )

    assert (
        document["historical_evidence"][0]["reference"]
        == "schema2/reference_top_toolbar"
    )
    assert document["status"] == "APPROVED_BASELINE_CHANGE"
    assert set(document["axes"]) == {"G", "V", "B"}


def test_validator_rejects_h_axis_and_unknown_schema_versions():
    document = build_evidence_document(_report(), producer="tests")

    with_h = copy.deepcopy(document)
    with_h["axes"]["H"] = copy.deepcopy(with_h["axes"]["G"])
    with pytest.raises(ValueError, match="exactly G, V, and B"):
        validate_evidence_document(with_h)

    future = copy.deepcopy(document)
    future["schema_version"] = 99
    with pytest.raises(ValueError, match="unsupported"):
        validate_evidence_document(future)


def test_validator_rejects_tampered_axis_and_overall_aggregates():
    document = build_evidence_document(_report(), producer="tests")

    bad_axis = copy.deepcopy(document)
    bad_axis["axes"]["V"]["status"] = "PASS"
    with pytest.raises(ValueError, match=r"axes\.V\.status"):
        validate_evidence_document(bad_axis)

    bad_overall = copy.deepcopy(document)
    bad_overall["status"] = "PASS"
    with pytest.raises(ValueError, match="overall status"):
        validate_evidence_document(bad_overall)


def test_validator_rejects_foreign_or_duplicate_check_identity():
    document = build_evidence_document(_report(), producer="tests")

    foreign = copy.deepcopy(document)
    foreign["axes"]["G"]["checks"][0]["axis"] = "V"
    with pytest.raises(ValueError, match="does not match declared axis"):
        validate_evidence_document(foreign)

    duplicate = copy.deepcopy(document)
    duplicate["axes"]["G"]["checks"].append(
        copy.deepcopy(duplicate["axes"]["G"]["checks"][0])
    )
    with pytest.raises(ValueError, match="globally unique"):
        validate_evidence_document(duplicate)


def test_write_read_roundtrip_is_valid_and_byte_deterministic(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    report = _report()

    write_evidence_json(first, report, producer="tests")
    write_evidence_json(second, report, producer="tests")

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().endswith(b"\n")
    assert read_evidence_json(first) == read_evidence_json(second)
