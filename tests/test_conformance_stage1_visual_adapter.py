"""Stage C2D tests for the first concrete V-axis adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit_stage1_contract import run as run_stage1_contract
from scripts.conformance import (
    AdapterContext,
    ConformanceAxis,
    ConformanceStatus,
    Stage1VisualSystemAdapter,
    combine_adapter_results,
    run_adapter,
)


_ATOMIC_CHECKS = {
    "required_token_schema": True,
    "hex_colors_valid": True,
    "token_colors_unique": True,
    "primary_text_contrast": True,
    "secondary_text_contrast": True,
    "focus_contrast": True,
    "qss_is_generated_from_tokens": True,
    "qss_required_states": True,
    "qss_required_roles": True,
    "forbidden_colors_absent": True,
    "no_inline_application_styles": True,
    "no_unclassified_direct_chrome_colors": True,
}


def _payload() -> dict:
    return {
        "schema": "neoeng.stage1-contract-audit",
        "schema_version": 1,
        "current_contract_result": "FAIL",
        "consolidated_decision": "REVIEW_REQUIRED",
        "checks": dict(_ATOMIC_CHECKS),
        "evidence": {
            "token_schema": ["window", "surface", "text_primary", "accent"],
            "token_values": {
                "window": "#101010",
                "surface": "#202020",
                "text_primary": "#F0F0F0",
                "accent": "#4F8CFF",
            },
            "contrast_ratios": {
                "primary_on_window": 12.0,
                "secondary_on_surface": 5.0,
                "focus_on_window": 3.5,
            },
            "qss_sha256": "a" * 64,
            "qss_states": {
                "hover": True,
                "pressed": True,
                "checked": True,
                "disabled": True,
                "focus": True,
            },
            "forbidden_colors": ["#FF4500", "#00BFFF"],
            "inline_style_files": [],
            "direct_color_inventory": {
                "application_chrome_review_entries": [],
                "pass": True,
            },
        },
        "historical_result": {
            "source": "docs/evidence/stage1-baseline-report.json",
            "status": "PASS",
            "finding_count": 0,
            "unexpected_geometry_delta_count": 0,
            "classification": "HISTORICAL_ONLY",
            "interpretation": "Historical geometry remains diagnostic only.",
        },
    }


def _context() -> AdapterContext:
    return AdapterContext(
        source_baseline="9923d97",
        source_reference="artifacts/stage1-contract-report.json",
    )


def test_stage1_visual_adapter_maps_only_atomic_v_checks() -> None:
    result = run_adapter(Stage1VisualSystemAdapter(), _payload(), context=_context())

    assert len(result.checks) == 12
    assert {check.axis for check in result.checks} == {ConformanceAxis.VISUAL_SYSTEM}
    assert sum(check.domain == "token" for check in result.checks) == 4
    assert sum(check.domain == "palette" for check in result.checks) == 3
    assert sum(check.domain == "contrast" for check in result.checks) == 3
    assert sum(check.domain == "visual-state" for check in result.checks) == 2
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)
    assert tuple(check.check_id for check in result.checks[:4]) == (
        "V-TOKEN_STAGE1_REQUIRED_SCHEMA-001",
        "V-TOKEN_STAGE1_HEX_COLORS_VALID-001",
        "V-PALETTE_STAGE1_TOKEN_COLORS_UNIQUE-001",
        "V-CONTRAST_STAGE1_PRIMARY_TEXT-001",
    )


def test_stage1_visual_adapter_ignores_legacy_aggregate_failure() -> None:
    payload = _payload()
    payload["current_contract_result"] = "FAIL"
    payload["consolidated_decision"] = "REVIEW_REQUIRED"

    result = run_adapter(Stage1VisualSystemAdapter(), payload, context=_context())
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)


def test_stage1_visual_adapter_propagates_atomic_failure_with_evidence() -> None:
    payload = _payload()
    payload["checks"]["primary_text_contrast"] = False
    payload["current_contract_result"] = "PASS"
    payload["evidence"]["contrast_ratios"]["primary_on_window"] = 2.1

    result = run_adapter(Stage1VisualSystemAdapter(), payload, context=_context())
    failures = [check for check in result.checks if check.status == ConformanceStatus.FAIL]

    assert [check.check_id for check in failures] == [
        "V-CONTRAST_STAGE1_PRIMARY_TEXT-001"
    ]
    assert failures[0].domain == "contrast"
    assert "primary_on_window=2.1" in failures[0].evidence
    assert "threshold=>=4.5" in failures[0].evidence


def test_stage1_visual_adapter_is_fail_closed_for_missing_expected_atom() -> None:
    payload = _payload()
    del payload["checks"]["qss_required_states"]

    result = run_adapter(Stage1VisualSystemAdapter(), payload, context=_context())
    failures = [check for check in result.checks if check.status == ConformanceStatus.FAIL]

    assert [check.check_id for check in failures] == [
        "V-VISUAL_STATE_STAGE1_QSS_REQUIRED_STATES-001"
    ]
    assert "missing_atomic_check=true" in failures[0].evidence


def test_stage1_visual_adapter_rejects_unmapped_new_legacy_atom() -> None:
    payload = _payload()
    payload["checks"]["future_typography_rule"] = True

    with pytest.raises(ValueError, match="require explicit classification"):
        run_adapter(Stage1VisualSystemAdapter(), payload, context=_context())


def test_stage1_visual_adapter_preserves_history_outside_blocking_axes() -> None:
    result = run_adapter(Stage1VisualSystemAdapter(), _payload(), context=_context())

    assert len(result.historical_evidence) == 1
    historical = result.historical_evidence[0]
    assert historical.source == "scripts/audit_stage1_contract.py"
    assert historical.reference == "docs/evidence/stage1-baseline-report.json"
    assert "HISTORICAL_ONLY" in historical.summary
    assert "unexpected_geometry_delta_count=0" in historical.summary

    combined = combine_adapter_results((result,), source_baseline="9923d97")
    document = combined.build_evidence_document(producer="scripts/conformance/c2d")
    assert document["status"] == "PASS"
    assert document["axes"]["G"]["status"] == "NOT_APPLICABLE"
    assert document["axes"]["V"]["status"] == "PASS"
    assert document["axes"]["V"]["check_count"] == 12
    assert document["axes"]["B"]["status"] == "NOT_APPLICABLE"
    assert len(document["historical_evidence"]) == 1


def test_stage1_visual_adapter_accepts_real_stage1_contract_shape() -> None:
    historical_report = Path(
        "docs/evidence/artifacts/"
        "ui-modernization-stage1-final-20260821/stage1-baseline-report.json"
    )
    payload = run_stage1_contract(Path.cwd(), historical_report)

    result = run_adapter(Stage1VisualSystemAdapter(), payload, context=_context())

    assert len(result.checks) == 12
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)
    assert len(result.historical_evidence) == 1
