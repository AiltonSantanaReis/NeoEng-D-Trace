from pathlib import Path

from tools.formal_legacy_reconciliation import (
    build_formal_gate,
    resolve_manifest_inventory,
)

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


def test_manifest_inventory_uses_tracked_audit_when_sources_are_absent(tmp_path):
    relative_audit = (
        "docs/evidence/artifacts/legacy-26-formal-review-20260901/"
        "untracked_manifest_audit.json"
    )
    audit_target = tmp_path / relative_audit
    audit_target.parent.mkdir(parents=True)
    audit_source = ROOT / relative_audit
    audit_target.write_bytes(audit_source.read_bytes())

    result = resolve_manifest_inventory(tmp_path)

    assert result["accepted"] is True
    assert result["schema_version"] == 2
    assert result["summary"]["observed"] == 63
    assert result["summary"]["resolved"] == 63
    assert all(
        entry["source_validation"]["absence_in_clean_checkout_is_allowed"]
        for entry in result["entries"]
    )
