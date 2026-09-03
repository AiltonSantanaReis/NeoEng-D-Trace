from pathlib import Path

from tools.formal_legacy_reconciliation import build_formal_gate

ROOT = Path(__file__).resolve().parents[1]


def test_formal_gate_accepts_current_contract_without_rewriting_history():
    result = build_formal_gate(ROOT)

    assert result["accepted"] is True
    assert result["historical_snapshots"]["unchanged"] is True
    assert result["historical_runner"]["accepted"] is False
    assert result["manifest_resolution"]["accepted"] is True
    assert result["manifest_resolution"]["count"] == 63
    assert result["substitutes"] == {
        "accepted": True,
        "junit": (
            "docs/evidence/artifacts/legacy-26-phase5-20260901/"
            "native-substitutes.xml"
        ),
        "tests": 42,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }
