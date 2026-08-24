from __future__ import annotations

from pathlib import Path

from scripts.audit_stage1_contract import run


def test_stage1_current_contract_passes_without_unclassified_chrome_colors() -> None:
    report = run(
        Path.cwd(),
        Path(
            "artifacts/stage0-9-final-audit-20260824/"
            "source-ui-capture/stage1-baseline-report.json"
        ),
    )

    assert report["current_contract_result"] == "PASS"
    assert report["consolidated_decision"] == "PASS_WITH_HISTORICAL_EVOLUTION"
    assert report["historical_result"]["classification"] == "HISTORICAL_ONLY"
    assert report["checks"]["no_unclassified_direct_chrome_colors"] is True
    assert report["evidence"]["inline_style_files"] == []
