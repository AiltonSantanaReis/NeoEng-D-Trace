from __future__ import annotations

from pathlib import Path

from scripts.audit_stage2_contract import run


def test_stage2_contract_covers_normative_catalog_and_runtime_actions() -> None:
    report = run(Path.cwd())

    assert report["current_contract_result"] == "PASS"
    assert report["checks"]["required_catalog_complete"] is True
    assert report["checks"]["required_sizes_16_20_24"] is True
    assert report["checks"]["no_stage2_duplicate_svg_owners"] is True
    assert report["checks"]["runtime_actions_have_accessible_icons"] is True
