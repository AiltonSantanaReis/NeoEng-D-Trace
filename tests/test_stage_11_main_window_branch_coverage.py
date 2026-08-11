"""Stage 11 branch contracts for the main application window."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

import src.ui.main_window as main_window_module
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    instance = MainWindow(scene, _ConfigStub())
    yield instance
    instance._mark_document_clean()
    instance.close()


def test_collision_export_failure_cancel_and_real_text_output(
    window, tmp_path: Path, monkeypatch
) -> None:
    errors: list[str] = []
    notices: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args: errors.append(str(args[2]))
    )
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args: notices.append(str(args[2]))
    )

    monkeypatch.setattr(
        main_window_module,
        "export_collision_document",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("invalid shape")),
    )
    assert window.export_collision_json() is False
    assert window.export_collision_txt() is False
    assert errors and all("invalid shape" in message for message in errors)

    document = {
        "format_id": "neoeng-d-trace-collisions",
        "format_version": 1,
        "shapes": [
            {
                "object_id": "A",
                "shape_type": "polygon",
                "points": [[0.0, 0.0], [2.0, 0.0], [0.0, 2.0]],
            }
        ],
        "results": [],
        "statistics": {},
    }
    monkeypatch.setattr(
        main_window_module,
        "export_collision_document",
        lambda *args, **kwargs: document,
    )
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args, **kwargs: ("", "")
    )
    assert window._save_collision_json(document) is False
    assert window.export_collision_txt() is False

    output = tmp_path / "collisions.txt"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output), "Text Files (*.txt)"),
    )
    assert window.export_collision_txt() is True
    assert output.is_file()
    assert "Object A:" in output.read_text(encoding="utf-8")
    assert notices[-1].endswith(str(output))

    monkeypatch.setattr(
        main_window_module,
        "save_collision_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("write blocked")),
    )
    assert window.export_collision_txt() is False
    assert "write blocked" in errors[-1]


def test_focus_tools_and_command_history_branches(window, monkeypatch) -> None:
    centered: list[str] = []
    messages: list[str] = []
    monkeypatch.setattr(window.canvas, "center_on_object", centered.append)
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args: messages.append(str(args[2]))
    )
    monkeypatch.setattr(window.side_panel, "_get_selected_obj", lambda: ("OBJ", None))
    window._focus_selected()
    assert centered == ["OBJ"]
    monkeypatch.setattr(window.side_panel, "_get_selected_obj", lambda: (None, None))
    window._focus_selected()
    assert messages

    updates: list[str] = []
    monkeypatch.setattr(window.canvas, "update", lambda: updates.append("canvas"))
    monkeypatch.setattr(window.side_panel, "refresh", lambda: updates.append("panel"))
    monkeypatch.setattr(window, "_on_scene_changed", lambda: updates.append("scene"))
    monkeypatch.setattr(
        window, "_update_undo_redo_actions", lambda: updates.append("actions")
    )
    monkeypatch.setattr(window.canvas, "request_tool_undo", lambda: True)
    monkeypatch.setattr(window.canvas, "request_tool_redo", lambda: True)
    assert window._undo() is None
    assert window._redo() is None

    manager = SimpleNamespace(
        undo=lambda scene: "undone",
        redo=lambda scene: "redone",
        can_undo=True,
        can_redo=True,
    )
    window.scene.cmd = manager
    monkeypatch.setattr(window.canvas, "request_tool_undo", lambda: False)
    monkeypatch.setattr(window.canvas, "request_tool_redo", lambda: False)
    assert window._undo() == "undone"
    assert window._redo() == "redone"
    window.scene.cmd = None
    assert window._undo() is None
    assert window._redo() is None
    assert "panel" in updates and "scene" in updates

    selected: list[str] = []
    monkeypatch.setattr(window.tool_palette, "select_tool_by_name", selected.append)
    window._select_tool("pen_tool")
    assert selected == ["pen_tool"]


def test_language_success_fallback_menu_and_exception(window, monkeypatch) -> None:
    window.set_language("pt")
    assert window.current_lang == "pt"
    window.set_language("unsupported")
    assert window.current_lang == "en"

    class _Signal:
        def connect(self, callback):
            self.callback = callback

    class _Action:
        def __init__(self, text):
            self._text = text
            self.triggered = _Signal()

        def text(self):
            return self._text

        def setText(self, text):
            self._text = text

    class _Menu:
        def __init__(self, parent):
            self.actions = []

        def addAction(self, text):
            action = _Action(text)
            self.actions.append(action)
            return action

        def exec(self, position):
            return None

    monkeypatch.setattr(main_window_module, "QMenu", _Menu)
    window.show_language_menu()
    assert window.act_english.text()
    assert window.act_portuguese.text()
    window.update_language()

    original = window.update_language
    monkeypatch.setattr(
        window,
        "update_language",
        lambda: (_ for _ in ()).throw(RuntimeError("translation failure")),
    )
    with pytest.raises(RuntimeError, match="translation failure"):
        window.set_language("pt")
    monkeypatch.setattr(window, "update_language", original)
    window.current_lang = "missing"
    window.update_language()
    assert window.current_lang == "en"


def test_document_signature_dirty_and_path_helpers(
    window, tmp_path: Path, monkeypatch
) -> None:
    fallback = window._signature_path_hint()
    assert fallback.name == "untitled.ndtproj"
    image_path = (tmp_path / "asset.png").resolve()
    window.scene.image_path = str(image_path)
    assert window._signature_path_hint() == image_path.parent / "untitled.ndtproj"
    project_path = tmp_path / "project.ndtproj"
    window._project_path = project_path
    assert window._signature_path_hint() == project_path

    window._project_path = None
    window.scene.image_path = None
    window._document_name = None
    window.scene.objects.clear()
    window.scene.groups.clear()
    window.scene.collision_shapes.clear()
    window._clean_signature = None
    assert window.is_document_modified() is False
    window._document_name = "named.ndtproj"
    assert window.is_document_modified() is True
    window._clean_signature = "not-current"
    assert window.is_document_modified() is True
    monkeypatch.setattr(
        window,
        "_compute_document_signature",
        lambda: (_ for _ in ()).throw(ValueError("signature failure")),
    )
    assert window.is_document_modified() is True

    assert window._normalized_project_path("sample").name == "sample.ndtproj"
    assert window._normalized_project_path("sample.NDTPROJ").name == "sample.NDTPROJ"
    window._project_path = project_path
    assert window._project_dialog_start() == str(project_path)
    window._project_path = None
    window._last_folder = str(tmp_path)
    window._document_name = "draft.png"
    assert window._project_dialog_start() == str(tmp_path / "draft.ndtproj")


def test_history_and_document_view_refresh_branches(window, monkeypatch) -> None:
    action_updates: list[str] = []
    monkeypatch.setattr(
        window, "_update_undo_redo_actions", lambda: action_updates.append("updated")
    )
    window.scene.cmd = None
    window._reset_command_history()
    fallback_manager = SimpleNamespace(_undo=[1], _redo=[2])
    window.scene.cmd = fallback_manager
    window._reset_command_history()
    assert fallback_manager._undo == [] and fallback_manager._redo == []
    assert len(action_updates) == 2

    events: list[str] = []
    monkeypatch.setattr(window.side_panel, "refresh", lambda: events.append("side"))
    monkeypatch.setattr(window.layers, "refresh", lambda: events.append("layers"))
    monkeypatch.setattr(window.groups, "refresh", lambda: events.append("groups"))
    monkeypatch.setattr(window.canvas, "update", lambda: events.append("canvas"))
    monkeypatch.setattr(window.canvas, "fit_to_window", lambda: events.append("fit"))
    window.scene.image = None
    window._refresh_document_views(project_loaded=False)
    assert "fit" not in events
    window.scene.image = np.zeros((2, 2, 4), dtype=np.uint8)
    window._refresh_document_views(project_loaded=False)
    assert "fit" in events


@pytest.mark.parametrize(
    ("choice", "save_result", "expected"),
    [
        (QMessageBox.StandardButton.Save, True, True),
        (QMessageBox.StandardButton.Save, False, False),
        (QMessageBox.StandardButton.Discard, False, True),
        (QMessageBox.StandardButton.Cancel, False, False),
    ],
)
def test_unsaved_confirmation_choices(
    window, monkeypatch, choice, save_result: bool, expected: bool
) -> None:
    monkeypatch.setattr(window, "is_document_modified", lambda: True)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: choice)
    monkeypatch.setattr(window, "save_project", lambda: save_result)
    assert window._confirm_unsaved_changes() is expected


def test_image_reference_rebase_resolve_and_restore(window, tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    destination_dir = source_dir / "copies"
    asset_dir = destination_dir / "assets"
    asset_dir.mkdir(parents=True)
    window._project_path = source_dir / "original.ndtproj"
    window.scene.image_path = "copies/assets/image.png"
    window.scene.image_path_kind = "relative"
    window.scene.image_sha256 = "d" * 64
    window.scene._image_reference_loaded = True

    original = window._rebase_image_reference_for_save(destination_dir / "copy.ndtproj")
    assert window.scene.image_path == "assets/image.png"
    assert window.scene.image_path_kind == "relative"
    window._restore_image_reference(original)
    assert window.scene.image_path == "copies/assets/image.png"

    window.scene.image_path = None
    assert window._resolved_project_image_path(window._project_path) is None
    window.scene.image_path = "assets/image.png"
    window.scene.image_path_kind = "relative"
    assert (
        window._resolved_project_image_path(window._project_path)
        == (source_dir / "assets/image.png").resolve()
    )
    absolute = tmp_path / "absolute.png"
    window.scene.image_path = str(absolute)
    window.scene.image_path_kind = "absolute"
    assert window._resolved_project_image_path(window._project_path) == absolute


def test_attach_project_image_missing_unreadable_and_hash_mismatch(
    window, tmp_path: Path
) -> None:
    project_path = tmp_path / "project.ndtproj"
    staged = Scene()
    staged.image_path = "missing.png"
    staged.image_path_kind = "relative"
    warnings = window._attach_project_image(project_path, staged)
    assert len(warnings) == 1 and "missing.png" in warnings[0]

    unreadable = tmp_path / "unreadable.png"
    unreadable.write_text("not an image", encoding="utf-8")
    staged.image_path = unreadable.name
    warnings = window._attach_project_image(project_path, staged)
    assert len(warnings) == 1 and "unreadable.png" in warnings[0]

    image_path = tmp_path / "valid.png"
    image = np.zeros((3, 4, 4), dtype=np.uint8)
    assert cv2.imwrite(str(image_path), image)
    staged.image_path = image_path.name
    staged.image_sha256 = hashlib.sha256(b"different").hexdigest()
    warnings = window._attach_project_image(project_path, staged)
    assert staged.image is not None
    assert len(warnings) == 1 and "SHA-256" in warnings[0]


def test_project_and_image_dialog_cancellation_paths(window, monkeypatch) -> None:
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("", "")
    )
    assert window.open_project() is False
    assert window.open_image() is False
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args, **kwargs: ("", "")
    )
    assert window.save_project_as() is False


def test_open_image_failure_and_unsaved_rejection(
    window, tmp_path: Path, monkeypatch
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args: errors.append(str(args[2]))
    )
    missing = tmp_path / "missing.png"
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(missing), ""),
    )
    assert window.open_image() is False
    assert errors

    valid = tmp_path / "valid.png"
    assert cv2.imwrite(str(valid), np.zeros((2, 3, 3), dtype=np.uint8))
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(valid), ""),
    )
    monkeypatch.setattr(window, "_confirm_unsaved_changes", lambda: False)
    assert window.open_image() is False
    assert window.scene.image is None


def test_export_dialog_success_and_exception_restores_preview(
    window, monkeypatch
) -> None:
    preview: list[bool] = []
    monkeypatch.setattr(window.canvas, "set_preview_mode", preview.append)

    class _Dialog:
        current_lang = "en"

        def __init__(self, *args, **kwargs):
            pass

        def minimumWidth(self):
            return 470

        def exec(self):
            return 0

    monkeypatch.setattr(main_window_module, "ExportDialog", _Dialog)
    window.open_export()
    assert preview == [True, False]

    class _FailingDialog:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("dialog failure")

    monkeypatch.setattr(main_window_module, "ExportDialog", _FailingDialog)
    with pytest.raises(RuntimeError, match="dialog failure"):
        window.open_export()
    assert preview[-2:] == [True, False]


def test_mask_viewer_close_and_collision_action_branches(window, monkeypatch) -> None:
    events: list[object] = []

    class _Signal:
        def connect(self, callback):
            events.append(callback)

    class _MaskDialog:
        destroyed = _Signal()

        def __init__(self, *args, **kwargs):
            self.current_lang = kwargs["lang"]

        def setModal(self, value):
            events.append(("modal", value))

        def setAttribute(self, attribute, value):
            events.append((attribute, value))

        def show(self):
            events.append("show")

        def update_language(self, lang):
            events.append(("language", lang))

        def raise_(self):
            events.append("raise")

        def activateWindow(self):
            events.append("activate")

    monkeypatch.setattr(main_window_module, "MaskViewerDialog", _MaskDialog)
    window.open_mask_viewer()
    assert "show" in events
    window.open_mask_viewer()
    assert "raise" in events and "activate" in events
    window._clear_mask_viewer_reference()
    assert window._mask_viewer_dialog is None

    monkeypatch.setattr(
        main_window_module,
        "MaskViewerDialog",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("mask failure")),
    )
    errors: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args: errors.append(str(args[2]))
    )
    window.open_mask_viewer()
    assert "mask failure" in errors[-1]

    close_event = QCloseEvent()
    monkeypatch.setattr(window, "_confirm_unsaved_changes", lambda: True)
    window.closeEvent(close_event)
    assert close_event.isAccepted()

    overlay: list[object] = []
    monkeypatch.setattr(window.collision_overlay, "set_visible", overlay.append)
    monkeypatch.setattr(window.canvas, "update", lambda: overlay.append("update"))
    window.collision_overlay_action.setChecked(True)
    window._toggle_collision_overlay()
    assert overlay[:2] == [True, "update"]

    results = [SimpleNamespace(obj1_id="A", obj2_id="B", colliding=True, mtv=(1, 0))]
    registered: list[tuple[str, object]] = []
    manager = SimpleNamespace(
        batch_test=lambda: results,
        register=lambda shape_id, shape: registered.append((shape_id, shape)),
    )
    window.collision_manager = manager
    monkeypatch.setattr(
        window.collision_overlay,
        "update_collision_results",
        lambda payload: overlay.append(payload),
    )
    window._on_collision_batch_test()
    assert overlay[-2][0]["obj1_id"] == "A"
    window.scene.collision_shapes = {"A": [(0, 0), (1, 0), (0, 1)]}
    window._on_collision_auto_generate()
    assert registered[0][0] == "A"

    window.collision_manager = None
    window._on_collision_batch_test()
    window._on_collision_auto_generate()
    monkeypatch.setattr(window, "_build_collision_document", lambda **kwargs: None)
    assert window._on_collision_export() is False
    window.scene.collision_shapes.clear()


def test_main_window_residual_optional_component_branches(window, monkeypatch) -> None:
    original = (
        window.side_panel,
        window.tool_palette,
        window.groups,
        window.canvas,
        window._mask_viewer_dialog,
    )
    window.side_panel = object()
    window.tool_palette = object()
    window.groups = object()
    window.canvas = SimpleNamespace(_tool=None)
    window._mask_viewer_dialog = object()
    window.update_language()
    window._focus_selected()
    window._select_tool("pen_tool")
    (
        window.side_panel,
        window.tool_palette,
        window.groups,
        window.canvas,
        window._mask_viewer_dialog,
    ) = original

    window.set_last_folder("folder")
    window.select_tool("magnetic_lasso")
    assert window._last_folder == "folder"
    assert window._current_tool == "magnetic_lasso"


def test_main_window_residual_history_view_and_signature_branches(
    window, monkeypatch
) -> None:
    monkeypatch.setattr(window, "_update_undo_redo_actions", lambda: None)
    manager = SimpleNamespace(_redo=[1])
    window.scene.cmd = manager
    window._reset_command_history()
    assert manager._redo == []
    manager = SimpleNamespace(_undo=[1])
    window.scene.cmd = manager
    window._reset_command_history()
    assert manager._undo == []

    original_layers, original_groups = window.layers, window.groups
    window.layers = object()
    window.groups = object()
    window.scene.image = None
    window._refresh_document_views(project_loaded=False)
    window.layers, window.groups = original_layers, original_groups

    window._project_path = None
    window.scene.image_path = "relative/image.png"
    assert window._signature_path_hint().name == "untitled.ndtproj"


def test_main_window_residual_image_warning_and_dialog_branches(
    window, tmp_path: Path, monkeypatch
) -> None:
    window.scene.image_path = None
    assert window._attach_project_image(tmp_path / "project.ndtproj") == []

    image_path = tmp_path / "read-error.png"
    image_path.write_bytes(b"present")
    window.scene.image_path = str(image_path)
    window.scene.image_path_kind = "absolute"
    monkeypatch.setattr(
        cv2,
        "imread",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("read failed")),
    )
    assert len(window._attach_project_image(tmp_path / "project.ndtproj")) == 1

    warnings = []
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args[2])
    )
    window._show_project_warnings([])
    window._show_project_warnings(["first", "second"])
    assert "first" in warnings[-1] and "second" in warnings[-1]

    project_path = tmp_path / "project.ndtproj"
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(project_path), ""),
    )
    monkeypatch.setattr(window, "_confirm_unsaved_changes", lambda: False)
    assert window.open_project() is False


def test_main_window_residual_save_and_json_failure_branches(
    window, tmp_path: Path, monkeypatch
) -> None:
    errors = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args: errors.append(str(args[2]))
    )
    output = tmp_path / "collision.json"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output), ""),
    )
    monkeypatch.setattr(
        main_window_module,
        "save_json_metadata",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("json failed")),
    )
    assert window._save_collision_json({}) is False
    assert "json failed" in errors[-1]

    project_path = tmp_path / "existing.ndtproj"
    window._project_path = project_path
    saved = []
    monkeypatch.setattr(
        window, "_save_project_to", lambda path: saved.append(path) or True
    )
    assert window.save_project() is True
    assert saved == [project_path]
