from __future__ import annotations

from pathlib import Path

import pytest

from src.core.atomic_outputs import (
    AtomicOutputRollbackError,
    AtomicOutputTransaction,
)
from src.launcher import build_parser, run_headless
from tests.test_stage_7_cli_contract import _project


def _args(*values):
    return build_parser().parse_args(list(values))


def test_transaction_commits_all_outputs_and_cleans_staging(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    with AtomicOutputTransaction() as transaction:
        staged_first = transaction.stage_path(str(first))
        staged_second = transaction.stage_path(str(second))
        Path(staged_first).write_text("one", encoding="utf-8")
        Path(staged_second).write_text("two", encoding="utf-8")
        transaction.commit()

    assert first.read_text(encoding="utf-8") == "one"
    assert second.read_text(encoding="utf-8") == "two"
    assert not list(tmp_path.glob(".neoeng-*"))


def test_transaction_rolls_back_existing_outputs_on_commit_failure(
    tmp_path, monkeypatch
):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text("old-one", encoding="utf-8")
    second.write_text("old-two", encoding="utf-8")

    transaction = AtomicOutputTransaction()
    staged_first = transaction.stage_path(str(first))
    staged_second = transaction.stage_path(str(second))
    Path(staged_first).write_text("new-one", encoding="utf-8")
    Path(staged_second).write_text("new-two", encoding="utf-8")
    original_replace = transaction._replace

    def fail_second(source, destination):
        if Path(destination) == second:
            raise OSError("controlled second output failure")
        return original_replace(source, destination)

    monkeypatch.setattr(transaction, "_replace", fail_second)

    with pytest.raises(OSError, match="controlled second output failure"):
        transaction.commit()

    assert first.read_text(encoding="utf-8") == "old-one"
    assert second.read_text(encoding="utf-8") == "old-two"
    assert not list(tmp_path.glob(".neoeng-*"))


def test_transaction_removes_new_outputs_on_commit_failure(tmp_path, monkeypatch):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    transaction = AtomicOutputTransaction()
    staged_first = transaction.stage_path(str(first))
    staged_second = transaction.stage_path(str(second))
    Path(staged_first).write_text("new-one", encoding="utf-8")
    Path(staged_second).write_text("new-two", encoding="utf-8")
    original_replace = transaction._replace

    def fail_second(source, destination):
        if Path(destination) == second:
            raise OSError("controlled second output failure")
        return original_replace(source, destination)

    monkeypatch.setattr(transaction, "_replace", fail_second)

    with pytest.raises(OSError, match="controlled second output failure"):
        transaction.commit()

    assert not first.exists()
    assert not second.exists()
    assert not list(tmp_path.glob(".neoeng-*"))


def test_transaction_rejects_duplicate_destinations(tmp_path):
    destination = tmp_path / "same.json"
    transaction = AtomicOutputTransaction()
    transaction.stage_path(str(destination))

    with pytest.raises(ValueError, match="duplicate output destinations"):
        transaction.stage_path(str(destination))

    transaction.abort()
    assert not list(tmp_path.glob(".neoeng-*"))


def test_transaction_reports_rollback_failure(tmp_path, monkeypatch):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text("old-one", encoding="utf-8")
    second.write_text("old-two", encoding="utf-8")

    transaction = AtomicOutputTransaction()
    staged_first = transaction.stage_path(str(first))
    staged_second = transaction.stage_path(str(second))
    Path(staged_first).write_text("new-one", encoding="utf-8")
    Path(staged_second).write_text("new-two", encoding="utf-8")
    calls = 0

    original_replace = transaction._replace

    def fail_commit_and_rollback(source, destination):
        nonlocal calls
        calls += 1
        if calls == 1:
            return original_replace(source, destination)
        raise OSError("persistent replace failure")

    monkeypatch.setattr(transaction, "_replace", fail_commit_and_rollback)

    with pytest.raises(AtomicOutputRollbackError, match="rollback"):
        transaction.commit()

    assert calls == 3
    assert not list(tmp_path.glob(".neoeng-*"))


def test_cli_rolls_back_all_outputs_when_final_commit_fails(
    tmp_path, monkeypatch, capsys
):
    source = _project(tmp_path / "source.ndtproj")
    scene_glb = tmp_path / "scene.glb"
    metadata = tmp_path / "metadata.json"
    saved = tmp_path / "saved.ndtproj"
    for path in (scene_glb, metadata, saved):
        path.write_text(f"old:{path.name}", encoding="utf-8")

    original_replace = AtomicOutputTransaction._replace

    def fail_final_output(transaction, source_path, destination):
        if Path(destination) == saved:
            raise OSError("controlled final output failure")
        return original_replace(transaction, source_path, destination)

    monkeypatch.setattr(AtomicOutputTransaction, "_replace", fail_final_output)

    result = run_headless(
        _args(
            "--project",
            source,
            "--export-scene-gltf",
            str(scene_glb),
            "--export-json",
            str(metadata),
            "--save-project",
            str(saved),
        )
    )

    assert result == 1
    assert scene_glb.read_text(encoding="utf-8") == "old:scene.glb"
    assert metadata.read_text(encoding="utf-8") == "old:metadata.json"
    assert saved.read_text(encoding="utf-8") == "old:saved.ndtproj"
    assert not list(tmp_path.glob(".neoeng-*"))
    assert "Failed to commit output set" in capsys.readouterr().err
    assert not list(tmp_path.glob("*.tmp"))


def test_cli_rejects_duplicate_output_destinations(tmp_path, capsys):
    source = _project(tmp_path / "source.ndtproj")
    destination = tmp_path / "same.out"

    result = run_headless(
        _args(
            "--project",
            source,
            "--export-json",
            str(destination),
            "--save-project",
            str(destination),
        )
    )

    assert result == 1
    assert "duplicate output destinations" in capsys.readouterr().err
    assert not destination.exists()


def test_transaction_rejects_empty_destination():
    transaction = AtomicOutputTransaction()
    with pytest.raises(ValueError, match="non-empty path"):
        transaction.stage_path("")


def test_transaction_rejects_commit_after_success(tmp_path):
    destination = tmp_path / "result.json"
    transaction = AtomicOutputTransaction()
    staged = transaction.stage_path(str(destination))
    Path(staged).write_text("result", encoding="utf-8")
    transaction.commit()

    with pytest.raises(RuntimeError, match="already committed"):
        transaction.commit()


def test_transaction_cleans_backup_when_backup_copy_fails(tmp_path, monkeypatch):
    destination = tmp_path / "result.json"
    destination.write_text("old", encoding="utf-8")
    transaction = AtomicOutputTransaction()
    staged = transaction.stage_path(str(destination))
    Path(staged).write_text("new", encoding="utf-8")

    import src.core.atomic_outputs as atomic_outputs

    def fail_copy(*_args, **_kwargs):
        raise OSError("controlled backup failure")

    monkeypatch.setattr(atomic_outputs.shutil, "copy2", fail_copy)

    with pytest.raises(OSError, match="controlled backup failure"):
        transaction.commit()

    assert destination.read_text(encoding="utf-8") == "old"
    assert not list(tmp_path.glob(".neoeng-*"))
