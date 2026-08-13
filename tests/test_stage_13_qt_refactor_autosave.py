"""Stage 13 contracts for document state, autosave, and recovery."""

from __future__ import annotations

from datetime import datetime, timezone
import io
import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError
from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.app_paths import default_state_directory
from src.core.commands import CommandManager
from src.core.config import AppConfig
from src.core.document_session import DocumentSession
from src.core.view_processor import ViewProcessor
from src.models.scene import Scene
from src.persistence.autosave import AutosaveError, AutosaveStore
from src.ui.main_window import MainWindow


class _ConfigStub:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager()
    return scene


def _close_clean(window: MainWindow) -> None:
    window._mark_document_clean()
    window.close()


def test_document_session_preserves_dirty_signature_contract(tmp_path: Path) -> None:
    scene = _scene()
    scene.add_object("shape", [(0, 0), (8, 0), (0, 8)])
    session = DocumentSession(scene, last_folder=str(tmp_path))

    session.mark_clean()
    assert session.is_modified() is False

    scene.select_object("shape")
    assert session.is_modified() is False

    scene.update_polygon("shape", [(0, 0), (9, 0), (0, 9)])
    assert session.is_modified() is True
    assert session.normalized_project_path(tmp_path / "project").suffix == ".ndtproj"


def test_autosave_roundtrip_keeps_source_context_and_scene_data(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ndtproj"
    scene = _scene()
    scene.add_object("shape", [(0, 0), (8, 0), (0, 8)])
    scene.save_project(str(source))
    store = AutosaveStore(
        tmp_path / "state" / "recovery.json",
        clock=lambda: datetime(2026, 8, 13, 12, 30, tzinfo=timezone.utc),
    )

    store.save(
        scene,
        reference_project_path=source,
        source_project_path=source,
        document_name=source.name,
    )
    snapshot = store.load()
    recovered = _scene()
    snapshot.apply_to(recovered)

    assert snapshot.saved_at_utc == datetime(2026, 8, 13, 12, 30, tzinfo=timezone.utc)
    assert snapshot.source_project_path == source.resolve(strict=False)
    assert snapshot.reference_project_path == source.resolve(strict=False)
    assert snapshot.document_name == "source.ndtproj"
    assert list(recovered.objects) == ["shape"]


def test_autosave_atomic_failure_preserves_previous_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    scene = _scene()
    scene.add_object("first", [(0, 0), (8, 0), (0, 8)])
    store = AutosaveStore(tmp_path / "recovery.json")
    reference = tmp_path / "source.ndtproj"
    store.save(scene, reference_project_path=reference)
    original = store.path.read_bytes()

    scene.add_object("second", [(10, 0), (18, 0), (10, 8)])
    monkeypatch.setattr(
        "src.persistence.autosave.os.replace",
        lambda *args: (_ for _ in ()).throw(OSError("replace blocked")),
    )

    with pytest.raises(AutosaveError, match="replace blocked"):
        store.save(scene, reference_project_path=reference)

    assert store.path.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))


def test_invalid_autosave_is_quarantined_without_deletion(tmp_path: Path) -> None:
    path = tmp_path / "recovery.json"
    path.write_text("{", encoding="utf-8")
    store = AutosaveStore(path)

    with pytest.raises(AutosaveError) as captured:
        store.load()

    quarantine = captured.value.quarantine_path
    assert quarantine is not None
    assert quarantine.read_text(encoding="utf-8") == "{"
    assert not path.exists()


def test_autosave_rejects_relative_context_path_and_bounds_file_read(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "recovery.json"
    scene = _scene()
    store = AutosaveStore(path)
    store.save(scene, reference_project_path=tmp_path / "untitled.ndtproj")
    value = json.loads(path.read_text(encoding="utf-8"))
    value["reference_project_path"] = "relative.ndtproj"
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(AutosaveError, match="absolute"):
        store.load()
    assert not path.exists()

    path.write_bytes(b"{}")
    read_sizes = []
    original_open = Path.open

    class TrackingBytesIO(io.BytesIO):
        def read(self, size=-1):
            read_sizes.append(size)
            return super().read(size)

    def bounded_open(self, mode="r", *args, **kwargs):
        if self == path and mode == "rb":
            return TrackingBytesIO(b"{}")
        return original_open(self, mode, *args, **kwargs)

    monkeypatch.setattr("src.persistence.autosave.MAX_AUTOSAVE_FILE_BYTES", 2)
    monkeypatch.setattr("src.persistence.autosave.Path.open", bounded_open)
    with pytest.raises(AutosaveError):
        store.load()
    assert read_sizes == [3]


def test_autosave_paths_and_configuration_are_bounded(tmp_path: Path) -> None:
    assert (
        default_state_directory(
            {"LOCALAPPDATA": str(tmp_path / "local")},
            home=tmp_path / "home",
            platform="win32",
        )
        == tmp_path / "local" / "NeoEng-D-Trace"
    )
    assert (
        default_state_directory(
            {"XDG_STATE_HOME": str(tmp_path / "state")},
            home=tmp_path / "home",
            platform="linux",
        )
        == tmp_path / "state" / "NeoEng-D-Trace"
    )
    assert AppConfig().autosave_enabled is True
    assert AppConfig().autosave_interval_seconds == 60
    with pytest.raises(ValidationError):
        AppConfig(autosave_interval_seconds=14)
    with pytest.raises(ValidationError):
        AppConfig(autosave_interval_seconds=3_601)


def test_non_adapter_layers_are_qt_independent_and_main_window_is_reduced() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden = []
    for path in (root / "src").rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("src/ui/", "src/tools/")):
            continue
        if relative == "src/launcher.py":
            continue
        source = path.read_text(encoding="utf-8")
        if "from PySide6" in source or "import PySide6" in source:
            forbidden.append(relative)

    assert forbidden == []
    main_window = (root / "src/ui/main_window.py").read_text(encoding="utf-8")
    assert len(main_window.splitlines()) < 1_200
    xray = ViewProcessor.generate_xray_array(
        np.zeros((8, 8), dtype=np.uint8),
        mode=2,
    )
    assert xray.shape == (8, 8, 3)


def test_main_window_autosaves_modified_document_and_clears_after_save(
    qt_app,
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = AutosaveStore(tmp_path / "state" / "recovery.json")
    window = MainWindow(
        _scene(),
        _ConfigStub({"autosave_interval_seconds": 15}),
        autosave_store=store,
    )
    window.scene.add_object("shape", [(0, 0), (8, 0), (0, 8)])

    assert window.autosave_timer.interval() == 15_000
    assert window.perform_autosave() is True
    assert window.perform_autosave() is False
    assert store.exists() is True

    destination = tmp_path / "saved.ndtproj"
    monkeypatch.setattr(
        "src.ui.main_window.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(destination), ""),
    )
    assert window.save_project_as() is True
    assert destination.is_file()
    assert store.exists() is False
    _close_clean(window)


def test_recovery_is_explicit_keeps_snapshot_and_marks_document_dirty(
    qt_app,
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.ndtproj"
    original = _scene()
    original.add_object("recovered", [(0, 0), (8, 0), (0, 8)])
    original.save_project(str(source))
    store = AutosaveStore(tmp_path / "state" / "recovery.json")
    store.save(
        original,
        reference_project_path=source,
        source_project_path=source,
        document_name=source.name,
    )
    window = MainWindow(_scene(), _ConfigStub(), autosave_store=store)
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    assert window.offer_autosave_recovery() is True
    assert list(window.scene.objects) == ["recovered"]
    assert window._project_path == source.resolve(strict=False)
    assert window.is_document_modified() is True
    assert store.exists() is True
    _close_clean(window)


def test_recovery_detaches_changed_source_and_requires_save_as(
    qt_app,
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "source.ndtproj"
    original = _scene()
    original.add_object("recovered", [(0, 0), (8, 0), (0, 8)])
    original.save_project(str(source))
    store = AutosaveStore(tmp_path / "state" / "recovery.json")
    store.save(
        original,
        reference_project_path=source,
        source_project_path=source,
        document_name=source.name,
    )
    source.unlink()
    window = MainWindow(_scene(), _ConfigStub(), autosave_store=store)
    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(window, "_show_project_warnings", warnings.extend)

    assert window.offer_autosave_recovery() is True
    assert window._project_path is None
    assert window.is_document_modified() is True
    assert any("Save As" in warning for warning in warnings)
    _close_clean(window)


def test_deferred_recovery_survives_close_and_blocks_overwrite(
    qt_app,
    tmp_path: Path,
    monkeypatch,
) -> None:
    original = _scene()
    original.add_object("preserved", [(0, 0), (8, 0), (0, 8)])
    store = AutosaveStore(tmp_path / "state" / "recovery.json")
    store.save(
        original,
        reference_project_path=tmp_path / "untitled.ndtproj",
    )
    original_bytes = store.path.read_bytes()
    window = MainWindow(_scene(), _ConfigStub(), autosave_store=store)
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )

    assert window.offer_autosave_recovery() is False
    window.scene.add_object("new", [(10, 0), (18, 0), (10, 8)])
    assert window.perform_autosave() is False
    window._mark_document_clean()
    window.close()
    assert store.path.read_bytes() == original_bytes


def test_recovery_discard_removes_snapshot_without_mutating_scene(
    qt_app,
    tmp_path: Path,
    monkeypatch,
) -> None:
    original = _scene()
    original.add_object("discarded", [(0, 0), (8, 0), (0, 8)])
    store = AutosaveStore(tmp_path / "state" / "recovery.json")
    store.save(
        original,
        reference_project_path=tmp_path / "untitled.ndtproj",
    )
    window = MainWindow(_scene(), _ConfigStub(), autosave_store=store)
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Discard,
    )

    assert window.offer_autosave_recovery() is False
    assert window.scene.objects == {}
    assert store.exists() is False
    _close_clean(window)
