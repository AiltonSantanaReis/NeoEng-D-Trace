from __future__ import annotations

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
