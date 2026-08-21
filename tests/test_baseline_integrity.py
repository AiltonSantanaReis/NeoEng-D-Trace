from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools import baseline_integrity


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repository(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Integrity Test")
    _git(root, "config", "user.email", "integrity@example.invalid")


def test_local_ignored_venv_does_not_block_manifest(
    monkeypatch, tmp_path: Path
) -> None:
    _init_repository(tmp_path)
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    cached = tmp_path / ".venv" / "Lib" / "site-packages" / "sample"
    cached.mkdir(parents=True)
    (cached / "module.cpython-311.pyc").write_bytes(b"local-cache")
    _git(tmp_path, "add", ".gitignore", "app.py")

    monkeypatch.setattr(baseline_integrity, "ROOT", tmp_path)
    monkeypatch.setattr(
        baseline_integrity,
        "MANIFEST_PATH",
        tmp_path / "baseline_manifest.json",
    )

    assert baseline_integrity.find_forbidden_paths() == []
    assert baseline_integrity.write_manifest() == 0

    manifest = json.loads(
        (tmp_path / "baseline_manifest.json").read_text(encoding="utf-8")
    )
    assert set(manifest["files"]) == {".gitignore", "app.py"}


def test_tracked_forbidden_environment_file_is_blocked(
    monkeypatch, tmp_path: Path
) -> None:
    _init_repository(tmp_path)
    forbidden = tmp_path / ".venv" / "tracked.pyc"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_bytes(b"tracked-cache")
    _git(tmp_path, "add", "-f", ".venv/tracked.pyc")

    monkeypatch.setattr(baseline_integrity, "ROOT", tmp_path)
    monkeypatch.setattr(
        baseline_integrity,
        "MANIFEST_PATH",
        tmp_path / "baseline_manifest.json",
    )

    assert baseline_integrity.find_forbidden_paths() == [".venv/tracked.pyc"]
    assert baseline_integrity.write_manifest() == 2


def test_manifest_date_is_informational_but_must_be_valid(
    monkeypatch, tmp_path: Path
) -> None:
    _init_repository(tmp_path)
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    monkeypatch.setattr(baseline_integrity, "ROOT", tmp_path)
    monkeypatch.setattr(
        baseline_integrity,
        "MANIFEST_PATH",
        tmp_path / "baseline_manifest.json",
    )
    assert baseline_integrity.write_manifest() == 0

    manifest_path = tmp_path / "baseline_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["baseline_date"] = "2000-01-01"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert baseline_integrity.verify_manifest() == 0

    manifest["baseline_date"] = "not-a-date"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert baseline_integrity.verify_manifest() == 1


def test_git_blob_mode_ignores_worktree_eol_conversion(
    monkeypatch, tmp_path: Path
) -> None:
    _init_repository(tmp_path)
    artifact = tmp_path / "app.py"
    artifact.write_bytes(b"line\n")
    _git(tmp_path, "add", "app.py")
    artifact.write_bytes(b"line\r\n")

    monkeypatch.setattr(baseline_integrity, "ROOT", tmp_path)
    monkeypatch.setattr(
        baseline_integrity,
        "MANIFEST_PATH",
        tmp_path / "baseline_manifest.json",
    )

    assert baseline_integrity.write_manifest(use_git_blob=True) == 0
    expected = json.loads(
        (tmp_path / "baseline_manifest.json").read_text(encoding="utf-8")
    )
    assert expected["files"]["app.py"]["size"] == 5
    assert baseline_integrity.verify_manifest(use_git_blob=True) == 0

    artifact.write_bytes(b"changed\n")
    assert baseline_integrity.verify_manifest(use_git_blob=True) == 0
    assert baseline_integrity.verify_manifest(use_git_blob=False) == 1


def test_baseline_ignores_untracked_worktree_outputs(
    monkeypatch, tmp_path: Path
) -> None:
    _init_repository(tmp_path)
    tracked = tmp_path / "app.py"
    tracked.write_text("print('ok')\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    (tmp_path / "build-output.bin").write_bytes(b"local-only")

    monkeypatch.setattr(baseline_integrity, "ROOT", tmp_path)
    monkeypatch.setattr(
        baseline_integrity,
        "MANIFEST_PATH",
        tmp_path / "baseline_manifest.json",
    )

    assert baseline_integrity.write_manifest(use_git_blob=True) == 0
    manifest = json.loads(
        (tmp_path / "baseline_manifest.json").read_text(encoding="utf-8")
    )
    assert set(manifest["files"]) == {"app.py"}
    assert baseline_integrity.verify_manifest(use_git_blob=True) == 0
