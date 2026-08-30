"""Stage C2C tests for the first concrete G-axis adapter."""

from __future__ import annotations

import pytest

from scripts.audit_stage9_responsive_dpi import CRITICAL_WIDGETS, DPI_CASES, RESOLUTIONS
from scripts.conformance import (
    AdapterContext,
    ConformanceAxis,
    ConformanceStatus,
    Stage9ResponsiveGeometryAdapter,
    combine_adapter_results,
    run_adapter,
)


def _dimension_state(width: int, height: int, scale: float) -> dict:
    return {
        "requested_logical": [width, height],
        "expected_physical": [round(width * scale), round(height * scale)],
        "actual_window_size": [width, height],
        "actual_capture_size": [round(width * scale), round(height * scale)],
        "status": "PASS",
    }


def _widget_state() -> dict:
    return {
        "status": "PASS",
        "snapshot": {
            "visible": True,
            "geometry": [0, 0, 100, 80],
            "frame_geometry": [0, 0, 100, 80],
            "root_geometry": [10, 20, 100, 80],
        },
    }


def _worker(dpi_label: str, scale: float) -> dict:
    dimension_states = {
        label: _dimension_state(width, height, scale)
        for label, (width, height) in RESOLUTIONS.items()
    }
    widget_states = {
        label: {widget: _widget_state() for widget in CRITICAL_WIDGETS}
        for label in RESOLUTIONS
    }
    return {
        "dpi": {"label": dpi_label, "requested_scale": scale},
        "capture_dimensions": {
            "status": "PASS",
            "states": dimension_states,
        },
        "critical_widgets": {
            "status": "PASS",
            "states": widget_states,
        },
        # These aggregate/mixed fields are intentionally irrelevant to C2C.
        "automated_status": "FAIL",
        "checks": {
            "functional_actions": False,
            "visual_artifacts": False,
        },
    }


def _payload() -> dict:
    return {
        "schema_version": 1,
        "automated_status": "FAIL",
        "human_review": "NOT_CONFIRMED",
        "workers": [_worker(label, scale) for label, scale in DPI_CASES],
    }


def _context() -> AdapterContext:
    return AdapterContext(
        source_baseline="931dc88",
        source_reference="artifacts/stage9-responsive-dpi-report.json",
    )


def test_stage9_geometry_adapter_maps_only_atomic_g_checks() -> None:
    result = run_adapter(
        Stage9ResponsiveGeometryAdapter(),
        _payload(),
        context=_context(),
    )

    expected_viewport = len(DPI_CASES) * len(RESOLUTIONS)
    expected_layout = expected_viewport * len(CRITICAL_WIDGETS)
    assert len(result.checks) == expected_viewport + expected_layout == 60
    assert {check.axis for check in result.checks} == {ConformanceAxis.GEOMETRY_PHYSICS}
    assert sum(check.domain == "viewport" for check in result.checks) == 12
    assert sum(check.domain == "layout" for check in result.checks) == 48
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)
    assert tuple(check.check_id for check in result.checks[:5]) == (
        "G-VIEWPORT_DPI100_720P_COMPACTA-001",
        "G-LAYOUT_DPI100_720P_COMPACTA_MAIN_SPLITTER-001",
        "G-LAYOUT_DPI100_720P_COMPACTA_REFERENCE_TOOL_PALETTE-001",
        "G-LAYOUT_DPI100_720P_COMPACTA_CANVAS-001",
        "G-LAYOUT_DPI100_720P_COMPACTA_PANEL_STACK-001",
    )


def test_stage9_geometry_adapter_ignores_legacy_aggregate_failures() -> None:
    payload = _payload()
    payload["automated_status"] = "FAIL"
    for worker in payload["workers"]:
        worker["automated_status"] = "FAIL"
        worker["checks"] = {
            "functional_actions": False,
            "visual_geometry": False,
            "visual_artifacts": False,
        }

    result = run_adapter(
        Stage9ResponsiveGeometryAdapter(),
        payload,
        context=_context(),
    )
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)


def test_stage9_geometry_adapter_propagates_atomic_dimension_failure() -> None:
    payload = _payload()
    state = payload["workers"][0]["capture_dimensions"]["states"]["720p_Compacta"]
    state["status"] = "FAIL"
    state["actual_capture_size"] = [1, 1]

    result = run_adapter(
        Stage9ResponsiveGeometryAdapter(),
        payload,
        context=_context(),
    )
    failed = [
        check for check in result.checks if check.status == ConformanceStatus.FAIL
    ]
    assert [check.check_id for check in failed] == [
        "G-VIEWPORT_DPI100_720P_COMPACTA-001"
    ]
    assert any("actual_capture_size=[1, 1]" in item for item in failed[0].evidence)


def test_stage9_geometry_adapter_propagates_atomic_widget_failure() -> None:
    payload = _payload()
    state = payload["workers"][0]["critical_widgets"]["states"]["720p_Compacta"][
        "canvas"
    ]
    state["status"] = "FAIL"
    state["snapshot"]["geometry"] = [0, 0, 0, 0]

    result = run_adapter(
        Stage9ResponsiveGeometryAdapter(),
        payload,
        context=_context(),
    )
    failed = [
        check for check in result.checks if check.status == ConformanceStatus.FAIL
    ]
    assert [check.check_id for check in failed] == [
        "G-LAYOUT_DPI100_720P_COMPACTA_CANVAS-001"
    ]
    assert failed[0].domain == "layout"
    assert any("geometry=[0, 0, 0, 0]" in item for item in failed[0].evidence)


def test_stage9_geometry_adapter_is_fail_closed_for_missing_expected_worker() -> None:
    payload = _payload()
    payload["workers"] = payload["workers"][1:]

    result = run_adapter(
        Stage9ResponsiveGeometryAdapter(),
        payload,
        context=_context(),
    )
    failures = [
        check for check in result.checks if check.status == ConformanceStatus.FAIL
    ]

    # One missing DPI worker owns 3 viewport atoms + 3*4 critical-widget atoms.
    assert len(failures) == 15
    assert all(any(item == "dpi=100" for item in check.evidence) for check in failures)
    assert all(
        any(item == "missing_atomic_state=true" for item in check.evidence)
        for check in failures
    )


def test_stage9_geometry_adapter_rejects_ambiguous_worker_identity() -> None:
    payload = _payload()
    payload["workers"].append(_worker("100", 1.0))
    with pytest.raises(ValueError, match="duplicate Stage 9 DPI worker label"):
        run_adapter(
            Stage9ResponsiveGeometryAdapter(),
            payload,
            context=_context(),
        )

    payload = _payload()
    payload["workers"][0]["dpi"]["label"] = "175"
    with pytest.raises(ValueError, match="unexpected Stage 9 DPI worker label"):
        run_adapter(
            Stage9ResponsiveGeometryAdapter(),
            payload,
            context=_context(),
        )


def test_stage9_geometry_adapter_integrates_with_canonical_evidence() -> None:
    result = run_adapter(
        Stage9ResponsiveGeometryAdapter(),
        _payload(),
        context=_context(),
    )
    combined = combine_adapter_results((result,), source_baseline="931dc88")
    document = combined.build_evidence_document(producer="scripts/conformance/c2c")

    assert document["status"] == "PASS"
    assert document["blocking"] is False
    assert document["axes"]["G"]["status"] == "PASS"
    assert document["axes"]["G"]["check_count"] == 60
    assert document["axes"]["V"]["status"] == "NOT_APPLICABLE"
    assert document["axes"]["B"]["status"] == "NOT_APPLICABLE"
    assert document["historical_evidence"] == []
