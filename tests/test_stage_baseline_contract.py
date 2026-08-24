from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.validate_stage_baseline_contract import load_json, validate


BASELINE = Path(__file__).parents[1] / "docs" / "evidence" / "final-target-baseline-v1.json"


def _report(tmp_path: Path, *, classification: str = "EXPECTED_EVOLUTION", sha: str | None = None) -> Path:
    artifact = tmp_path / "evidence.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    report = {
        "baseline_id": "FINAL_TARGET",
        "stage": 1,
        "commit": "test-commit",
        "environment": {"platform": "test", "python": "test"},
        "command": "pytest tests/test_stage_baseline_contract.py",
        "decision": "PASS",
        "checks": [
            {
                "id": "tokens.palette",
                "result": "PASS",
                "classification": classification,
                "justification": "Token contract remains valid; geometry change is documented.",
            }
        ],
        "artifacts": [{"path": artifact.name, "sha256": sha or actual_sha, "visual": False}],
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return report_path


def test_contract_accepts_classified_evolution_with_valid_hash(tmp_path: Path) -> None:
    errors = validate(load_json(BASELINE), load_json(_report(tmp_path)), _report(tmp_path).resolve())
    assert errors == []


def test_contract_rejects_unclassified_change(tmp_path: Path) -> None:
    report_path = _report(tmp_path, classification="UNCLASSIFIED_CHANGE")
    errors = validate(load_json(BASELINE), load_json(report_path), report_path.resolve())
    assert any("bloqueia aprovação" in error for error in errors)


def test_contract_rejects_hash_mismatch(tmp_path: Path) -> None:
    report_path = _report(tmp_path, sha="0" * 64)
    errors = validate(load_json(BASELINE), load_json(report_path), report_path.resolve())
    assert any("hash divergente" in error for error in errors)
