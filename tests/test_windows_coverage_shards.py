from pathlib import Path

from tools.run_windows_coverage_shards import (
    build_pytest_command,
    discover_test_files,
    parse_junit,
    resolve_external_output,
)


def test_discover_test_files_is_deterministic_and_unfiltered(tmp_path: Path) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_z.py").write_text("", encoding="utf-8")
    (tests_root / "test_a.py").write_text("", encoding="utf-8")
    (tests_root / "helper.py").write_text("", encoding="utf-8")

    assert [path.name for path in discover_test_files(tmp_path)] == [
        "test_a.py",
        "test_z.py",
    ]


def test_build_command_keeps_official_selection_and_closes_coverage() -> None:
    command = build_pytest_command(
        "python",
        Path("tests/test_qt.py"),
        Path("C:/reports/junit.xml"),
        append_coverage=True,
        final_shard=True,
        coverage_path=Path("C:/reports/coverage.xml"),
    )

    assert command[0:4] == ["python", "-m", "pytest", str(Path("tests/test_qt.py"))]
    assert "--cov=src" in command
    assert "--cov-branch" in command
    assert "--cov-report=" in command
    assert "--cov-append" in command
    assert "--cov-fail-under=90" in command
    assert "--cov-report=term-missing" in command
    assert f"--cov-report=xml:{Path('C:/reports/coverage.xml')}" in command
    assert not any(argument in command for argument in ("--ignore", "-k"))


def test_parse_junit_accumulates_testsuite_metrics(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        '<testsuites><testsuite tests="3" failures="1" errors="0" '
        'skipped="1" time="0.25" /></testsuites>',
        encoding="utf-8",
    )

    assert parse_junit(report) == {
        "tests": 3,
        "failures": 1,
        "errors": 0,
        "skipped": 1,
        "time": 0.25,
        "junit_missing": False,
    }


def test_output_must_be_external_to_the_project(tmp_path: Path) -> None:
    assert resolve_external_output(tmp_path).is_absolute()
