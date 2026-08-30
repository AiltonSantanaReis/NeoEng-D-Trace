"""Stage C2E tests for the first concrete B-axis adapter."""

from __future__ import annotations

import pytest

from scripts.conformance import (
    AdapterContext,
    ConformanceAxis,
    ConformanceStatus,
    Stage9FunctionalBehaviorAdapter,
    combine_adapter_results,
    run_adapter,
)

_TOOL_NAMES = (
    "selection",
    "rect_selection",
    "ellipse_selection",
    "lasso_tool",
    "polygonal_lasso",
    "magnetic_lasso",
    "pen_tool",
    "polygon_edit",
    "collision_brush",
)


def _payload() -> dict:
    tools = {
        name: {
            "status": "PASS",
            "button_text": name,
            "checked": True,
            "tool_object_created": True,
        }
        for name in _TOOL_NAMES
    }
    xray = {
        "Lit": {"status": "PASS", "mode": 0, "expected": 0},
        "X-Ray 1": {"status": "PASS", "mode": 1, "expected": 1},
        "X-Ray 2": {"status": "PASS", "mode": 2, "expected": 2},
        "X-Ray 3": {"status": "PASS", "mode": 3, "expected": 3},
    }
    mask_modes = [
        {
            "index": index,
            "text": f"Mode {index}",
            "checked": True,
            "mode": index,
            "status": "PASS",
        }
        for index in range(4)
    ]
    return {
        "schema_version": 1,
        # These aggregate and non-B fields must not control C2E.
        "status": "FAIL",
        "automated_status": "FAIL",
        "checks": {
            "functional_actions": False,
            "visual_geometry": False,
            "human_review": False,
        },
        "functional": {
            "tool_palette": tools,
            "main_xray_actions": xray,
            "gizmo_gesture_transaction": {
                "status": "PASS",
                "detail": {
                    "started": True,
                    "committed": True,
                    "restored_after_undo": True,
                },
            },
            "gizmo_action": {
                "status": "PASS",
                "detail": {
                    "control_object_name": "act_gizmo",
                    "checked": True,
                    "viewport_state": True,
                    "semantic_context_member": True,
                },
            },
            # Geometry-owned legacy atom: intentionally excluded from B.
            "menus_on_screen": {
                "status": "FAIL",
                "detail": {"geometry": [0, 0, 1, 1], "screen": [0, 0, 1920, 1080]},
            },
            "inspector_scroll": {
                "status": "PASS",
                "detail": {"areas": 2, "passed": [True, True]},
            },
            "scenario_layer_actions": {
                "status": "PASS",
                "detail": {
                    "before": 1,
                    "after_add": 2,
                    "after_remove": 1,
                    "dedicated_window": True,
                },
            },
            # Capture evidence has no behavioral status and is intentionally excluded.
            "mask_viewer_capture": {"file": "mask.png", "width": 100, "height": 80},
            "mask_viewer_modes": mask_modes,
        },
        "visual": {"findings": [{"status": "FAIL"}]},
        "human_review": {"status": "NOT_CONFIRMED"},
    }


def _context() -> AdapterContext:
    return AdapterContext(
        source_baseline="28b812b",
        source_reference="artifacts/stage9-functional-ui-report.json",
    )


def test_stage9_behavior_adapter_maps_only_atomic_b_checks() -> None:
    result = run_adapter(
        Stage9FunctionalBehaviorAdapter(),
        _payload(),
        context=_context(),
    )

    assert len(result.checks) == 21
    assert {check.axis for check in result.checks} == {
        ConformanceAxis.BEHAVIOR_INTERACTION
    }
    assert sum(check.domain == "action" for check in result.checks) == 10
    assert sum(check.domain == "interaction-state" for check in result.checks) == 9
    assert sum(check.domain == "gizmo" for check in result.checks) == 2
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)
    assert tuple(check.check_id for check in result.checks[:4]) == (
        "B-ACTION_STAGE9_TOOL_SELECTION-001",
        "B-ACTION_STAGE9_TOOL_RECT_SELECTION-001",
        "B-ACTION_STAGE9_TOOL_ELLIPSE_SELECTION-001",
        "B-ACTION_STAGE9_TOOL_LASSO_TOOL-001",
    )


def test_stage9_behavior_adapter_ignores_legacy_aggregate_and_geometry_failure() -> (
    None
):
    payload = _payload()
    payload["status"] = "FAIL"
    payload["automated_status"] = "FAIL"
    payload["checks"] = {"functional_actions": False, "visual_geometry": False}
    payload["functional"]["menus_on_screen"]["status"] = "FAIL"
    payload["visual"] = {"findings": [{"status": "FAIL"}]}

    result = run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())
    assert all(check.status == ConformanceStatus.PASS for check in result.checks)
    assert not any(
        "menus_on_screen" in item for check in result.checks for item in check.evidence
    )


def test_stage9_behavior_adapter_propagates_atomic_tool_failure() -> None:
    payload = _payload()
    payload["functional"]["tool_palette"]["pen_tool"].update(
        {"status": "FAIL", "checked": False, "tool_object_created": False}
    )

    result = run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())
    failures = [
        check for check in result.checks if check.status == ConformanceStatus.FAIL
    ]

    assert [check.check_id for check in failures] == [
        "B-ACTION_STAGE9_TOOL_PEN_TOOL-001"
    ]
    assert "checked=False" in failures[0].evidence
    assert "tool_object_created=False" in failures[0].evidence


def test_stage9_behavior_adapter_uses_semantic_xray_mode_identity() -> None:
    payload = _payload()
    # Labels may change/localize; expected mode is the stable identity available
    # in the legacy payload.
    payload["functional"]["main_xray_actions"] = {
        "Iluminado": {"status": "PASS", "mode": 0, "expected": 0},
        "Raio X 1": {"status": "FAIL", "mode": 0, "expected": 1},
        "Raio X 2": {"status": "PASS", "mode": 2, "expected": 2},
        "Raio X 3": {"status": "PASS", "mode": 3, "expected": 3},
    }

    result = run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())
    failures = [
        check for check in result.checks if check.status == ConformanceStatus.FAIL
    ]
    assert [check.check_id for check in failures] == [
        "B-INTERACTION_STATE_STAGE9_VIEW_XRAY_1-001"
    ]
    assert "expected=1" in failures[0].evidence
    assert "actual_mode=0" in failures[0].evidence


def test_stage9_behavior_adapter_is_fail_closed_for_missing_atoms() -> None:
    payload = _payload()
    del payload["functional"]["gizmo_gesture_transaction"]
    del payload["functional"]["tool_palette"]["collision_brush"]
    payload["functional"]["mask_viewer_modes"] = payload["functional"][
        "mask_viewer_modes"
    ][:-1]

    result = run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())
    failures = [
        check for check in result.checks if check.status == ConformanceStatus.FAIL
    ]
    assert {check.check_id for check in failures} == {
        "B-ACTION_STAGE9_TOOL_COLLISION_BRUSH-001",
        "B-GIZMO_STAGE9_TRANSACTION_UNDO-001",
        "B-INTERACTION_STATE_STAGE9_MASK_MODE_3-001",
    }
    assert all("missing_atomic_state=true" in check.evidence for check in failures)


def test_stage9_behavior_adapter_rejects_unmapped_functional_scope_drift() -> None:
    payload = _payload()
    payload["functional"]["future_shortcut_matrix"] = {"status": "PASS"}
    with pytest.raises(ValueError, match="require explicit classification"):
        run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())

    payload = _payload()
    payload["functional"]["tool_palette"]["future_tool"] = {"status": "PASS"}
    with pytest.raises(ValueError, match="require explicit classification"):
        run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())


def test_stage9_behavior_adapter_rejects_ambiguous_mode_identity() -> None:
    payload = _payload()
    payload["functional"]["main_xray_actions"]["Alias"] = {
        "status": "PASS",
        "mode": 0,
        "expected": 0,
    }
    with pytest.raises(ValueError, match="duplicate Stage 9 X-Ray expected mode"):
        run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())

    payload = _payload()
    payload["functional"]["mask_viewer_modes"].append(
        {"index": 3, "text": "duplicate", "checked": True, "mode": 3, "status": "PASS"}
    )
    with pytest.raises(ValueError, match="duplicate Stage 9 mask viewer mode index"):
        run_adapter(Stage9FunctionalBehaviorAdapter(), payload, context=_context())


def test_stage9_behavior_adapter_integrates_with_canonical_evidence() -> None:
    result = run_adapter(
        Stage9FunctionalBehaviorAdapter(), _payload(), context=_context()
    )
    combined = combine_adapter_results((result,), source_baseline="28b812b")
    document = combined.build_evidence_document(producer="scripts/conformance/c2e")

    assert document["status"] == "PASS"
    assert document["blocking"] is False
    assert document["axes"]["G"]["status"] == "NOT_APPLICABLE"
    assert document["axes"]["V"]["status"] == "NOT_APPLICABLE"
    assert document["axes"]["B"]["status"] == "PASS"
    assert document["axes"]["B"]["check_count"] == 21
    assert document["historical_evidence"] == []
