from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_stage6_scenario_quality import (
    _files_index,
    _path_leaks,
    _write_stage6_report,
    run,
)


def _reports() -> tuple[dict, dict, dict, dict]:
    return (
        {"status": "PASS"},
        {"status": "PASS", "worktree_clean_at_capture_start": True},
        {"passed": True},
        {"passed": True},
    )


def test_stage6_report_is_fail_closed_for_dirty_source_tree(tmp_path: Path) -> None:
    ui, scene, deterministic, benchmark = _reports()
    report = _write_stage6_report(
        tmp_path,
        source={"worktree_clean": False, "commit": "a" * 40, "branch": "test"},
        ui_report=ui,
        scene_report=scene,
        determinism=deterministic,
        benchmark=benchmark,
        leaks=[],
    )
    assert report["status"] == "FAIL"
    assert report["checks"]["source_tree_clean"] is False


def test_stage6_report_fails_closed_on_host_path_leak(tmp_path: Path) -> None:
    ui, scene, deterministic, benchmark = _reports()
    report = _write_stage6_report(
        tmp_path,
        source={"worktree_clean": True, "commit": "a" * 40, "branch": "test"},
        ui_report=ui,
        scene_report=scene,
        determinism=deterministic,
        benchmark=benchmark,
        leaks=["report.log"],
    )
    assert report["status"] == "FAIL"
    assert report["checks"]["privacy"] is False


def test_stage6_artifact_index_hashes_every_non_index_file(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "capture.png").write_bytes(b"fixture")
    (tmp_path / "stage6-report.json").write_text("{}\n", encoding="utf-8")
    files = _files_index(tmp_path)
    assert set(files) == {"nested/capture.png", "stage6-report.json"}
    assert files["nested/capture.png"]["bytes"] == 7
    assert len(files["nested/capture.png"]["sha256"]) == 64


def test_stage6_rejects_existing_output_without_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    (output / "sentinel.txt").write_text("keep\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run(output)
    assert (output / "sentinel.txt").read_text(encoding="utf-8") == "keep\n"


def test_stage6_path_leak_scan_detects_windows_path(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps({"path": "C:\\Users\\someone\\fixture.png"}),
        encoding="utf-8",
    )
    assert _path_leaks(tmp_path) == ["report.json"]
