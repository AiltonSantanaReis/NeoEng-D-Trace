"""Regression tests for the Stage 4B.5 quality auditor."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_stage4b5_quality as audit


def test_stage4b5_determinism_checks_use_real_versioned_fixture() -> None:
    document = audit._fixture()
    result = audit._determinism_checks(document)
    assert result["passed"] is True
    assert result["runtime_export"]["deterministic"] is True
    assert result["preview_projection"]["deterministic"] is True
    assert result["overlay_geometry"]["deterministic"] is True
    assert result["input_unchanged"] is True


def test_stage4b5_artifact_index_matches_report_and_bytes(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        audit,
        "_benchmark",
        lambda document: {
            "limits_are_safety_ceilings": True,
            "measurements": [],
            "passed": True,
        },
    )
    report = audit._write_artifacts(tmp_path / "quality", audit._fixture())
    output = tmp_path / "quality"
    index = json.loads((output / "artifact-index.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert index["count"] == len(index["files"]) == 5
    for name, expected in index["files"].items():
        actual = audit.digest_path(output / name)
        assert actual == expected


def test_stage4b5_audit_has_no_host_path_in_report(tmp_path: Path) -> None:
    audit._write_artifacts(tmp_path / "quality", audit._fixture())
    report_text = (tmp_path / "quality/benchmark-report.json").read_text(
        encoding="utf-8"
    )
    assert str(audit.ROOT) not in report_text
    assert "Users" not in report_text
