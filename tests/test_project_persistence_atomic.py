"""Atomic-write contracts for project persistence v1."""

from __future__ import annotations

import pytest

from src.models.scene import Scene
from src.persistence import project_io
from src.persistence.errors import ProjectReadError, ProjectWriteError


def test_atomic_replace_failure_preserves_existing_destination(tmp_path, monkeypatch):
    destination = tmp_path / "project.ndtproj"
    destination.write_bytes(b"previous-valid-content")

    def fail_replace(source, target):
        raise OSError("controlled replace failure")

    monkeypatch.setattr(project_io.os, "replace", fail_replace)

    with pytest.raises(ProjectWriteError):
        Scene().save_project(str(destination))

    assert destination.read_bytes() == b"previous-valid-content"
    assert list(tmp_path.glob(f".{destination.name}.*.tmp")) == []


def test_successful_save_replaces_existing_destination_and_leaves_no_temp(tmp_path):
    destination = tmp_path / "project.ndtproj"
    destination.write_bytes(b"old")

    Scene().save_project(str(destination))

    assert destination.read_bytes() != b"old"
    assert list(tmp_path.glob(f".{destination.name}.*.tmp")) == []


def test_missing_destination_directory_is_rejected(tmp_path):
    destination = tmp_path / "missing" / "project.ndtproj"

    with pytest.raises(ProjectWriteError):
        Scene().save_project(str(destination))


def test_oversized_input_is_rejected_before_json_parsing(tmp_path, monkeypatch):
    path = tmp_path / "large.ndtproj"
    path.write_bytes(b"{}")

    monkeypatch.setattr(project_io, "MAX_PROJECT_FILE_BYTES", 1)

    with pytest.raises(ProjectReadError):
        Scene().load_project(str(path))


def test_actual_bytes_are_rechecked_after_stat(tmp_path, monkeypatch):
    path = tmp_path / "changing.ndtproj"
    path.write_bytes(b"")

    original_read_bytes = project_io.Path.read_bytes

    def oversized_read_bytes(self):
        if self == path:
            return b"{}"
        return original_read_bytes(self)

    monkeypatch.setattr(project_io, "MAX_PROJECT_FILE_BYTES", 1)
    monkeypatch.setattr(project_io.Path, "read_bytes", oversized_read_bytes)

    with pytest.raises(ProjectReadError):
        Scene().load_project(str(path))
