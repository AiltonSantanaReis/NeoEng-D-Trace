"""Atomic-write contracts for project persistence v1."""

from __future__ import annotations

import io

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

    read_sizes = []
    original_open = project_io.Path.open

    class TrackingBytesIO(io.BytesIO):
        def read(self, size=-1):
            read_sizes.append(size)
            return super().read(size)

    def bounded_open(self, mode="r", *args, **kwargs):
        if self == path:
            return TrackingBytesIO(b"{}")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(project_io, "MAX_PROJECT_FILE_BYTES", 1)
    monkeypatch.setattr(project_io.Path, "open", bounded_open)

    with pytest.raises(ProjectReadError):
        Scene().load_project(str(path))
    assert read_sizes == [2]

    monkeypatch.setattr(project_io, "MAX_IMAGE_FILE_BYTES", 1)
    assert project_io._hash_file_if_available(path) is None
    assert read_sizes == [2, 2]

    assert project_io._hash_file_if_available(tmp_path / "missing.png") is None
    with original_open(path, "wb") as handle:
        handle.write(b"12")
    assert project_io._hash_file_if_available(path) is None
    assert read_sizes == [2, 2]
