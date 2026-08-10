"""Stage 4 UI contracts for opening and saving project documents."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.persistence import load_project_document
from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def quiet_messages(monkeypatch):
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)


def _window() -> MainWindow:
    scene = Scene()
    scene.cmd = CommandManager()
    return MainWindow(scene, _ConfigStub())


def _write_png(path: Path) -> np.ndarray:
    image = np.zeros((12, 16, 4), dtype=np.uint8)
    image[:, :, 3] = 255
    assert cv2.imwrite(str(path), image)
    return image


def _project_with_image(project_path: Path, image_path: Path) -> None:
    image = _write_png(image_path)
    scene = Scene()
    scene.cmd = CommandManager()
    scene.load_image(image, str(image_path))
    scene.add_object("obj", [(0, 0), (10, 0), (0, 10)])
    scene.save_project(str(project_path))


def _close_clean(window: MainWindow) -> None:
    window._mark_document_clean()
    window.close()


def test_open_project_loads_image_resets_history_and_marks_clean(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    project_path = tmp_path / "sample.ndtproj"
    image_path = tmp_path / "sample.png"
    _project_with_image(project_path, image_path)

    window = _window()
    window.scene.add_object("old", [(0, 0), (8, 0), (0, 8)])
    window.scene.cmd._undo.append(object())

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(project_path), ""),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Discard,
    )

    assert window.open_project() is True
    assert set(window.scene.objects) == {"obj"}
    assert window.scene.image is not None
    assert window._project_path == project_path.resolve()
    assert window.scene.cmd._undo == []
    assert window.scene.cmd._redo == []
    assert window.is_document_modified() is False
    assert window.windowTitle() == "NeoEng-D-Trace - sample.ndtproj"
    assert window.tool_palette.isEnabled() is True
    _close_clean(window)


def test_invalid_project_does_not_mutate_current_scene(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    invalid = tmp_path / "invalid.ndtproj"
    invalid.write_text("{", encoding="utf-8")

    window = _window()
    window.scene.add_object("kept", [(0, 0), (8, 0), (0, 8)])
    window._mark_document_clean()

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(invalid), ""),
    )

    assert window.open_project() is False
    assert set(window.scene.objects) == {"kept"}
    assert window._project_path is None
    assert window.is_document_modified() is False
    _close_clean(window)


def test_save_as_appends_extension_and_marks_document_clean(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    window = _window()
    window.scene.add_object("obj", [(0, 0), (8, 0), (0, 8)])
    requested = tmp_path / "saved_project"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(requested), ""),
    )

    assert window.save_project_as() is True
    destination = tmp_path / "saved_project.ndtproj"
    assert destination.is_file()
    assert window._project_path == destination.resolve()
    assert window.is_document_modified() is False
    assert window.windowTitle() == "NeoEng-D-Trace - saved_project.ndtproj"
    loaded = load_project_document(destination)
    assert [item.id for item in loaded.document.objects] == ["obj"]
    _close_clean(window)


def test_open_image_replaces_previous_document_and_is_unsaved(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    image_path = tmp_path / "new.png"
    _write_png(image_path)

    window = _window()
    window.scene.add_object("old", [(0, 0), (8, 0), (0, 8)])

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(image_path), ""),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Discard,
    )

    assert window.open_image() is True
    assert window.scene.objects == {}
    assert window.scene.groups == []
    assert window.scene.collision_shapes == {}
    assert [layer.id for layer in window.scene.layers] == ["layer_default"]
    assert window._project_path is None
    assert window.is_document_modified() is True
    assert window.windowTitle() == "NeoEng-D-Trace - new.png*"
    _close_clean(window)


def test_cancelled_close_keeps_window_open(
    qt_app,
    monkeypatch,
    quiet_messages,
):
    window = _window()
    window.scene.add_object("obj", [(0, 0), (8, 0), (0, 8)])
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )

    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted() is False
    _close_clean(window)


def test_selection_only_does_not_mark_document_dirty(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("obj", [(0, 0), (8, 0), (0, 8)])
    window = MainWindow(scene, _ConfigStub())
    assert window.is_document_modified() is False

    scene.select_object("obj")

    assert window.is_document_modified() is False
    assert not window.windowTitle().endswith("*")
    _close_clean(window)


def test_save_as_rebases_external_relative_image_to_absolute_path(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    assets_dir = source_dir / "assets"
    assets_dir.mkdir(parents=True)
    target_dir.mkdir()

    image_path = assets_dir / "image.png"
    image = _write_png(image_path)
    source_project = source_dir / "source.ndtproj"

    source_scene = Scene()
    source_scene.cmd = CommandManager()
    source_scene.image = image
    source_scene.image_path = "assets/image.png"
    source_scene.image_path_kind = "relative"
    source_scene.image_sha256 = hashlib.sha256(image_path.read_bytes()).hexdigest()
    source_scene._image_reference_loaded = True
    source_scene.save_project(str(source_project))

    window = _window()
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(source_project), ""),
    )
    assert window.open_project() is True

    target_project = target_dir / "copy.ndtproj"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(target_project), ""),
    )
    assert window.save_project_as() is True

    loaded = load_project_document(target_project)
    assert loaded.document.image is not None
    assert loaded.document.image.path_kind == "absolute"
    assert Path(loaded.document.image.path) == image_path.resolve()
    assert window.is_document_modified() is False
    _close_clean(window)


def test_auxiliary_project_load_failure_keeps_current_document(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    project_path = tmp_path / "valid.ndtproj"
    image_path = tmp_path / "valid.png"
    _project_with_image(project_path, image_path)

    window = _window()
    window.scene.add_object("kept", [(0, 0), (8, 0), (0, 8)])
    window._mark_document_clean()

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(project_path), ""),
    )

    def fail_after_project_validation(*args, **kwargs):
        raise OSError("simulated auxiliary image failure")

    monkeypatch.setattr(
        window,
        "_attach_project_image",
        fail_after_project_validation,
    )

    assert window.open_project() is False
    assert set(window.scene.objects) == {"kept"}
    assert window._project_path is None
    assert window.is_document_modified() is False
    _close_clean(window)


def test_image_hash_read_failure_is_warning_not_partial_open(
    qt_app,
    tmp_path,
    monkeypatch,
):
    project_path = tmp_path / "hash-warning.ndtproj"
    image_path = tmp_path / "hash-warning.png"
    _project_with_image(project_path, image_path)

    staged_scene = Scene()
    staged_scene.load_project(str(project_path))
    window = _window()
    real_open = Path.open

    def fail_image_hash_open(path, *args, **kwargs):
        if Path(path) == image_path:
            raise OSError("simulated hash read failure")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_image_hash_open)

    warnings = window._attach_project_image(project_path, staged_scene)

    assert staged_scene.image is not None
    assert len(warnings) == 1
    assert "SHA-256" in warnings[0]
    _close_clean(window)


def test_save_failure_does_not_claim_success_or_change_project_path(
    qt_app,
    tmp_path,
    monkeypatch,
    quiet_messages,
):
    window = _window()
    window.scene.add_object("obj", [(0, 0), (8, 0), (0, 8)])
    requested = tmp_path / "must-not-exist.ndtproj"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(requested), ""),
    )

    def fail_save(path):
        raise OSError("simulated save failure")

    monkeypatch.setattr(window.scene, "save_project", fail_save)

    assert window.save_project_as() is False
    assert window._project_path is None
    assert window.is_document_modified() is True
    assert requested.exists() is False
    assert window.windowTitle().endswith("*")
    _close_clean(window)
