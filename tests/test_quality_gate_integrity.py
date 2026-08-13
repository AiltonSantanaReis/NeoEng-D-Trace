from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.check_coverage_policy import evaluate_coverage
from tools.run_legacy_tests import load_reconciliation, validate_replacement_tests


def _write_coverage(tmp_path: Path, *, total_line: float, total_branch: float) -> Path:
    path = tmp_path / "coverage.xml"
    path.write_text(
        f"""<?xml version="1.0" ?>
<coverage line-rate="{total_line}" branch-rate="{total_branch}">
  <packages><package name="src"><classes>
    <class name="good" filename="src/good.py"
           line-rate="0.95" branch-rate="0.90">
      <lines>
        <line number="1" hits="1" branch="true"
              condition-coverage="100% (2/2)"/>
      </lines>
    </class>
  </classes></package></packages>
</coverage>
""",
        encoding="utf-8",
    )
    return path


def test_coverage_policy_accepts_integrated_targets(tmp_path: Path) -> None:
    path = _write_coverage(tmp_path, total_line=0.90, total_branch=0.85)

    assert evaluate_coverage(path) == []


def test_coverage_policy_rejects_total_regressions(tmp_path: Path) -> None:
    path = _write_coverage(tmp_path, total_line=0.8999, total_branch=0.8499)

    failures = evaluate_coverage(path)

    assert any("total line coverage" in failure for failure in failures)
    assert any("total branch coverage" in failure for failure in failures)


def test_coverage_policy_rejects_low_module_rates(tmp_path: Path) -> None:
    path = tmp_path / "coverage.xml"
    path.write_text(
        """<?xml version="1.0" ?>
<coverage line-rate="0.95" branch-rate="0.90">
  <packages><package name="src"><classes>
    <class name="weak" filename="src/weak.py"
           line-rate="0.29" branch-rate="0.25">
      <lines>
        <line number="1" hits="1" branch="true"
              condition-coverage="25% (1/4)"/>
      </lines>
    </class>
  </classes></package></packages>
</coverage>
""",
        encoding="utf-8",
    )

    failures = evaluate_coverage(path)

    assert any("module line coverage src/weak.py" in failure for failure in failures)
    assert any("module branch coverage src/weak.py" in failure for failure in failures)


def test_current_legacy_replacement_nodes_are_collectable() -> None:
    project_root = Path(__file__).resolve().parents[1]
    legacy_root = project_root / "quality" / "legacy_tests"
    _, expectations = load_reconciliation(legacy_root)

    report = validate_replacement_tests(project_root, expectations)

    assert report == {
        "status": "collected",
        "references": 17,
        "pytest_returncode": 0,
    }


def test_legacy_replacement_collection_fails_closed(
    tmp_path: Path, monkeypatch
) -> None:
    def failed_collection(*args, **kwargs):
        from subprocess import CompletedProcess

        return CompletedProcess(args[0], 4, "test node not found")

    monkeypatch.setattr("tools.run_legacy_tests.subprocess.run", failed_collection)
    expectations = {
        "legacy::sample::test_case": {
            "replacement_tests": ["tests/missing.py::test_missing"]
        }
    }

    from pytest import raises

    with raises(RuntimeError, match="collection failed"):
        validate_replacement_tests(tmp_path, expectations)


def test_engine_validation_manifest_matches_preserved_reports() -> None:
    project_root = Path(__file__).resolve().parents[1]
    evidence_root = project_root / "docs" / "evidence"
    manifest = json.loads(
        (
            evidence_root / "PRE_ETAPA_14_ENGINE_VALIDATION_MANIFEST_2026-08-13.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["tested_source_commit"] == (
        "0a9bd99a0b0ef622fe6294f43ee69c7d68ac72c1"
    )
    assert manifest["working_tree_clean_before_execution"] is True
    assert {item["engine"] for item in manifest["validations"]} == {
        "godot",
        "unity",
    }

    expected_checks = {
        "metadata",
        "texture",
        "collision",
        "glb-external",
        "glb-engine",
    }
    for validation in manifest["validations"]:
        report_path = evidence_root / validation["report"]
        report_text = report_path.read_text(encoding="utf-8")
        canonical_bytes = (
            report_text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        )
        report = json.loads(report_text)

        assert (
            hashlib.sha256(canonical_bytes).hexdigest()
            == validation["report_canonical_sha256"]
        )
        assert report["engine"] == validation["engine"]
        assert report["status"] == validation["status"] == "SUCCESS"
        assert set(report["checks"]) == set(validation["checks"]) == expected_checks
        assert all(command["returncode"] == 0 for command in report["commands"])


def test_integrity_audit_records_both_real_engine_validations() -> None:
    project_root = Path(__file__).resolve().parents[1]
    audit = (
        project_root
        / "docs"
        / "evidence"
        / "AUDITORIA_INTEGRIDADE_PRE_ETAPA_14_2026-08-13.md"
    ).read_text(encoding="utf-8")

    assert "Godot e Unity foram reproduzidos localmente" in audit
    assert "Unity permanece não reproduzido" not in audit
