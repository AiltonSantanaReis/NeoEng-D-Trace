from __future__ import annotations

from scripts.audit_post_e13_tilemap_runtime_engines import _engine_status


def test_engine_status_reports_evaluated_gate_instead_of_initial_placeholder() -> None:
    assert _engine_status(False, False, {}) == "NOT_RUN"
    assert _engine_status(True, True, {"status": "NOT_RUN"}) == "PASS"
    assert _engine_status(True, False, {"status": "PENDING_EVIDENCE"}) == (
        "PENDING_EVIDENCE"
    )
    assert _engine_status(True, False, {"status": "NOT_RUN"}) == "FAIL"
