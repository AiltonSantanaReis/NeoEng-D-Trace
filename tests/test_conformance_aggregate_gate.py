"""Stage C2F tests for the aggregate NeoEng G/V/B conformance gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_conformance_gate import main as gate_cli_main
from scripts.audit_stage9_responsive_dpi import CRITICAL_WIDGETS, DPI_CASES, RESOLUTIONS
from scripts.conformance import (
    ConformanceAxis,
    ConformanceStatus,
    GateInput,
    run_aggregate_gate,
)

_BASELINE = "6d4e935012345678901234567890123456789abc"


def _source() -> dict:
    return {"commit": _BASELINE, "branch": "conformance/multiaxis-baseline"}


def _geometry_payload() -> dict:
    workers = []
    for dpi_label, scale in DPI_CASES:
        dimensions = {}
        widget_states = {}
        for resolution, (width, height) in RESOLUTIONS.items():
            dimensions[resolution] = {
                "requested_logical": [width, height],
                "expected_physical": [round(width * scale), round(height * scale)],
                "actual_window_size": [width, height],
                "actual_capture_size": [round(width * scale), round(height * scale)],
                "status": "PASS",
            }
            widget_states[resolution] = {
                widget: {
                    "status": "PASS",
                    "snapshot": {
                        "visible": True,
                        "geometry": [0, 0, 100, 80],
                        "frame_geometry": [0, 0, 100, 80],
                        "root_geometry": [10, 20, 100, 80],
                    },
                }
                for widget in CRITICAL_WIDGETS
            }
        workers.append(
            {
                "dpi": {"label": dpi_label, "requested_scale": scale},
                "source": _source(),
                "capture_dimensions": {"status": "PASS", "states": dimensions},
                "critical_widgets": {"status": "PASS", "states": widget_states},
                # Mixed aggregate failures are deliberately irrelevant.
                "automated_status": "FAIL",
                "checks": {"functional_actions": False, "visual_artifacts": False},
            }
        )
    return {
        "schema_version": 1,
        "source": _source(),
        "automated_status": "FAIL",
        "human_review": "NOT_CONFIRMED",
        "workers": workers,
    }


def _visual_payload() -> dict:
    return {
        "schema": "neoeng.stage1-contract-audit",
        "schema_version": 1,
        "source": _source(),
        "current_contract_result": "FAIL",
        "consolidated_decision": "REVIEW_REQUIRED",
        "checks": {
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
        },
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


def _behavior_payload() -> dict:
    tools = {
        name: {
            "status": "PASS",
            "button_text": name,
            "checked": True,
            "tool_object_created": True,
        }
        for name in (
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
    }
    return {
        "schema_version": 1,
        "source": _source(),
        "status": "FAIL",
        "automated_status": "FAIL",
        "checks": {"functional_actions": False, "visual_geometry": False},
        "functional": {
            "tool_palette": tools,
            "main_xray_actions": {
                "Lit": {"status": "PASS", "mode": 0, "expected": 0},
                "X-Ray 1": {"status": "PASS", "mode": 1, "expected": 1},
                "X-Ray 2": {"status": "PASS", "mode": 2, "expected": 2},
                "X-Ray 3": {"status": "PASS", "mode": 3, "expected": 3},
            },
            "gizmo_gesture_transaction": {
                "status": "PASS",
                "detail": {"committed": True, "restored_after_undo": True},
            },
            "gizmo_action": {
                "status": "PASS",
                "detail": {"checked": True, "viewport_state": True},
            },
            "menus_on_screen": {"status": "FAIL", "detail": {"geometry": [0, 0, 1, 1]}},
            "inspector_scroll": {"status": "PASS", "detail": {"areas": 2}},
            "scenario_layer_actions": {
                "status": "PASS",
                "detail": {"before": 1, "after_add": 2, "after_remove": 1},
            },
            "mask_viewer_capture": {"file": "mask.png"},
            "mask_viewer_modes": [
                {
                    "index": index,
                    "text": f"Mode {index}",
                    "checked": True,
                    "mode": index,
                    "status": "PASS",
                }
                for index in range(4)
            ],
        },
        "visual": {"findings": [{"status": "FAIL"}]},
        "human_review": {"status": "NOT_CONFIRMED"},
    }


def _gate():
    return run_aggregate_gate(
        source_baseline=_BASELINE,
        geometry=GateInput(
            _geometry_payload(), "artifacts/stage9-responsive-dpi-report.json"
        ),
        visual=GateInput(
            _visual_payload(), "artifacts/stage1-contract-report.json"
        ),
        behavior=GateInput(
            _behavior_payload(), "artifacts/stage9-functional-ui-report.json"
        ),
    )


def _write_payloads(
    tmp_path: Path, *, behavior_failure: bool = False
) -> tuple[Path, Path, Path]:
    geometry = _geometry_payload()
    visual = _visual_payload()
    behavior = _behavior_payload()
    if behavior_failure:
        behavior["functional"]["tool_palette"]["pen_tool"]["status"] = "FAIL"

    paths = (
        tmp_path / "geometry.json",
        tmp_path / "visual.json",
        tmp_path / "behavior.json",
    )
    for path, payload in zip(paths, (geometry, visual, behavior)):
        path.write_text(json.dumps(payload), encoding="utf-8")
    return paths


def test_aggregate_gate_populates_all_three_required_axes() -> None:
    gate = _gate()

    assert gate.status == ConformanceStatus.PASS
    assert gate.blocking is False
    assert gate.exit_code == 0
    assert gate.axis_statuses() == {"G": "PASS", "V": "PASS", "B": "PASS"}
    assert len(gate.adapted.report.checks) == 60 + 12 + 21


def test_aggregate_gate_preserves_historical_evidence_outside_axes() -> None:
    gate = _gate()
    document = gate.adapted.build_evidence_document(producer="scripts/conformance/c2f")

    assert document["axes"]["G"]["check_count"] == 60
    assert document["axes"]["V"]["check_count"] == 12
    assert document["axes"]["B"]["check_count"] == 21
    assert len(document["historical_evidence"]) == 1
    assert "H" not in document["axes"]


def test_aggregate_gate_propagates_only_atomic_product_failure() -> None:
    behavior = _behavior_payload()
    behavior["functional"]["tool_palette"]["pen_tool"].update(
        {"status": "FAIL", "checked": False, "tool_object_created": False}
    )
    gate = run_aggregate_gate(
        source_baseline=_BASELINE,
        geometry=GateInput(_geometry_payload(), "g.json"),
        visual=GateInput(_visual_payload(), "v.json"),
        behavior=GateInput(behavior, "b.json"),
    )

    assert gate.status == ConformanceStatus.FAIL
    assert gate.blocking is True
    assert gate.exit_code == 1
    assert gate.axis_statuses() == {"G": "PASS", "V": "PASS", "B": "FAIL"}
    failures = gate.adapted.report.axis_result(
        ConformanceAxis.BEHAVIOR_INTERACTION
    ).failures
    assert [check.check_id for check in failures] == [
        "B-ACTION_STAGE9_TOOL_PEN_TOOL-001"
    ]


def test_aggregate_gate_rejects_top_level_source_commit_mismatch() -> None:
    visual = _visual_payload()
    visual["source"]["commit"] = "stale"
    with pytest.raises(ValueError, match="source commit does not match"):
        run_aggregate_gate(
            source_baseline=_BASELINE,
            geometry=GateInput(_geometry_payload(), "g.json"),
            visual=GateInput(visual, "v.json"),
            behavior=GateInput(_behavior_payload(), "b.json"),
        )


def test_aggregate_gate_rejects_geometry_worker_source_commit_mismatch() -> None:
    geometry = _geometry_payload()
    geometry["workers"][2]["source"]["commit"] = "stale-worker"
    with pytest.raises(ValueError, match=r"workers\[2\].*does not match"):
        run_aggregate_gate(
            source_baseline=_BASELINE,
            geometry=GateInput(geometry, "g.json"),
            visual=GateInput(_visual_payload(), "v.json"),
            behavior=GateInput(_behavior_payload(), "b.json"),
        )


def test_aggregate_gate_rejects_missing_provenance_instead_of_returning_na() -> None:
    behavior = _behavior_payload()
    del behavior["source"]
    with pytest.raises(ValueError, match=r"stage9 functional behavior\.source"):
        run_aggregate_gate(
            source_baseline=_BASELINE,
            geometry=GateInput(_geometry_payload(), "g.json"),
            visual=GateInput(_visual_payload(), "v.json"),
            behavior=GateInput(behavior, "b.json"),
        )


def test_aggregate_gate_writes_deterministic_canonical_evidence(tmp_path: Path) -> None:
    gate = _gate()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    gate.write_evidence(first, producer="scripts/audit_conformance_gate.py")
    gate.write_evidence(second, producer="scripts/audit_conformance_gate.py")

    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_text(encoding="utf-8"))
    assert document["status"] == "PASS"
    assert document["blocking"] is False
    assert set(document["axes"]) == {"G", "V", "B"}


def test_aggregate_gate_cli_writes_pass_evidence_and_returns_zero(
    tmp_path: Path,
) -> None:
    geometry, visual, behavior = _write_payloads(tmp_path)
    output = tmp_path / "conformance.json"

    code = gate_cli_main(
        [
            "--source-baseline", _BASELINE,
            "--geometry-report", str(geometry),
            "--visual-report", str(visual),
            "--behavior-report", str(behavior),
            "--output", str(output),
        ]
    )

    assert code == 0
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["status"] == "PASS"
    assert document["axes"]["G"]["status"] == "PASS"
    assert document["axes"]["V"]["status"] == "PASS"
    assert document["axes"]["B"]["status"] == "PASS"


def test_aggregate_gate_cli_writes_blocking_evidence_and_returns_one(
    tmp_path: Path,
) -> None:
    geometry, visual, behavior = _write_payloads(tmp_path, behavior_failure=True)
    output = tmp_path / "conformance.json"

    code = gate_cli_main(
        [
            "--source-baseline", _BASELINE,
            "--geometry-report", str(geometry),
            "--visual-report", str(visual),
            "--behavior-report", str(behavior),
            "--output", str(output),
        ]
    )

    assert code == 1
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["status"] == "FAIL"
    assert document["blocking"] is True
    assert document["axes"]["B"]["failure_count"] == 1


def test_aggregate_gate_cli_returns_two_for_invalid_provenance_without_output(
    tmp_path: Path,
) -> None:
    geometry, visual, behavior = _write_payloads(tmp_path)
    data = json.loads(visual.read_text(encoding="utf-8"))
    data["source"]["commit"] = "stale"
    visual.write_text(json.dumps(data), encoding="utf-8")
    output = tmp_path / "conformance.json"

    code = gate_cli_main(
        [
            "--source-baseline", _BASELINE,
            "--geometry-report", str(geometry),
            "--visual-report", str(visual),
            "--behavior-report", str(behavior),
            "--output", str(output),
        ]
    )

    assert code == 2
    assert not output.exists()
