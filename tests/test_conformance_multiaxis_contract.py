"""Contract tests for the additive G/V/B conformance foundation."""

from __future__ import annotations

import pytest

from scripts.conformance import (
    AXIS_DOMAINS,
    AXIS_ORDER,
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
    MultiAxisConformance,
    aggregate_status,
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
        source="tests/fixture",
        summary=f"fixture {check_id}",
    )


def test_only_g_v_b_are_product_conformance_axes():
    assert tuple(axis.value for axis in AXIS_ORDER) == ("G", "V", "B")
    assert {axis.value for axis in ConformanceAxis} == {"G", "V", "B"}
    assert "H" not in {axis.value for axis in ConformanceAxis}


def test_axis_domains_keep_geometry_visual_and_behavior_concerns_separate():
    assert AXIS_DOMAINS[ConformanceAxis.GEOMETRY_PHYSICS] == (
        "layout",
        "viewport",
        "alignment",
        "transform",
        "collision",
        "snap",
    )
    assert "visual-state" in AXIS_DOMAINS[ConformanceAxis.VISUAL_SYSTEM]
    assert "interaction-state" in AXIS_DOMAINS[ConformanceAxis.BEHAVIOR_INTERACTION]
    assert "visual-state" not in AXIS_DOMAINS[ConformanceAxis.BEHAVIOR_INTERACTION]


def test_check_identity_is_axis_owned_and_domain_validated():
    valid = _check(
        "G-LAYOUT-001",
        ConformanceAxis.GEOMETRY_PHYSICS,
        "layout",
        ConformanceStatus.PASS,
    )
    assert valid.check_id == "G-LAYOUT-001"

    with pytest.raises(ValueError, match="does not match declared axis"):
        _check(
            "V-LAYOUT-001",
            ConformanceAxis.GEOMETRY_PHYSICS,
            "layout",
            ConformanceStatus.PASS,
        )

    with pytest.raises(ValueError, match="not valid for axis"):
        _check(
            "V-LAYOUT-001",
            ConformanceAxis.VISUAL_SYSTEM,
            "layout",
            ConformanceStatus.PASS,
        )


def test_status_precedence_is_fail_closed_without_hiding_approved_changes():
    assert aggregate_status(()) == ConformanceStatus.NOT_APPLICABLE
    assert (
        aggregate_status((ConformanceStatus.NOT_APPLICABLE,))
        == ConformanceStatus.NOT_APPLICABLE
    )
    assert (
        aggregate_status((ConformanceStatus.NOT_APPLICABLE, ConformanceStatus.PASS))
        == ConformanceStatus.PASS
    )
    assert (
        aggregate_status(
            (ConformanceStatus.PASS, ConformanceStatus.APPROVED_BASELINE_CHANGE)
        )
        == ConformanceStatus.APPROVED_BASELINE_CHANGE
    )
    assert (
        aggregate_status(
            (ConformanceStatus.APPROVED_BASELINE_CHANGE, ConformanceStatus.FAIL)
        )
        == ConformanceStatus.FAIL
    )


def test_multiaxis_aggregation_keeps_axis_results_independent():
    report = MultiAxisConformance(
        source_baseline="6ecd1ce",
        checks=(
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
            _check(
                "B-ACTION-001",
                ConformanceAxis.BEHAVIOR_INTERACTION,
                "action",
                ConformanceStatus.PASS,
            ),
        ),
    )

    assert (
        report.axis_result(ConformanceAxis.GEOMETRY_PHYSICS).status
        == ConformanceStatus.PASS
    )
    assert (
        report.axis_result(ConformanceAxis.VISUAL_SYSTEM).status
        == ConformanceStatus.APPROVED_BASELINE_CHANGE
    )
    assert (
        report.axis_result(ConformanceAxis.BEHAVIOR_INTERACTION).status
        == ConformanceStatus.PASS
    )
    assert report.status == ConformanceStatus.APPROVED_BASELINE_CHANGE
    assert report.is_blocking is False


def test_failure_on_one_axis_blocks_aggregate_without_mutating_other_axes():
    report = MultiAxisConformance(
        source_baseline="6ecd1ce",
        checks=(
            _check(
                "G-COLLISION-001",
                ConformanceAxis.GEOMETRY_PHYSICS,
                "collision",
                ConformanceStatus.FAIL,
            ),
            _check(
                "V-PALETTE-001",
                ConformanceAxis.VISUAL_SYSTEM,
                "palette",
                ConformanceStatus.PASS,
            ),
            _check(
                "B-UNDO_REDO-001",
                ConformanceAxis.BEHAVIOR_INTERACTION,
                "undo-redo",
                ConformanceStatus.PASS,
            ),
        ),
    )

    assert report.axis_result(ConformanceAxis.GEOMETRY_PHYSICS).is_blocking is True
    assert (
        report.axis_result(ConformanceAxis.VISUAL_SYSTEM).status
        == ConformanceStatus.PASS
    )
    assert (
        report.axis_result(ConformanceAxis.BEHAVIOR_INTERACTION).status
        == ConformanceStatus.PASS
    )
    assert report.status == ConformanceStatus.FAIL
    assert report.is_blocking is True


def test_duplicate_check_ids_are_rejected_globally():
    check = _check(
        "B-COMMAND-001",
        ConformanceAxis.BEHAVIOR_INTERACTION,
        "command",
        ConformanceStatus.PASS,
    )
    with pytest.raises(ValueError, match="globally unique"):
        MultiAxisConformance(source_baseline="6ecd1ce", checks=(check, check))
