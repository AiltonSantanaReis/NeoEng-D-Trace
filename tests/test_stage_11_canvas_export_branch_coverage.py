from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image, ImageDraw
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QKeyEvent, QPainter
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui import canvas_view as canvas_module
from src.ui import export_dialog as export_module
from src.ui.canvas_view import CanvasView, ToolInterface, XrayWorker
from src.ui.export_dialog import ExportDialog


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def scene_with_exports():
    scene = Scene()
    scene.cmd = CommandManager(max_history=40)
    scene.image = np.zeros((96, 96, 4), dtype=np.uint8)
    scene.add_object("A", [(10, 10), (50, 10), (50, 50), (10, 50)], select=True)
    scene.cmd.clear()
    return scene


def event(
    button=Qt.MouseButton.LeftButton,
    position=(20, 20),
    key=Qt.Key.Key_A,
):
    value = Mock()
    value.button.return_value = button
    value.position.return_value = QPointF(*position)
    value.pos.return_value = QPoint(*position)
    value.globalPos.return_value = QPoint(*position)
    value.key.return_value = key
    return value


class ProgressProbe:
    def __init__(self, cancel_checks=()):
        self.cancel_checks = iter(cancel_checks)
        self.values = []
        self.closed = False
        self.label = None
        self.range = None

    def setWindowModality(self, modality):
        self.modality = modality

    def show(self):
        self.shown = True

    def wasCanceled(self):
        return next(self.cancel_checks, False)

    def setValue(self, value):
        self.values.append(value)

    def close(self):
        self.closed = True

    def setLabelText(self, label):
        self.label = label

    def setRange(self, minimum, maximum):
        self.range = (minimum, maximum)


def progress_factory(monkeypatch, schedules):
    created = []
    pending = iter(schedules)

    def factory(*args, **kwargs):
        probe = ProgressProbe(next(pending, ()))
        created.append(probe)
        return probe

    monkeypatch.setattr(export_module, "QProgressDialog", factory)
    return created


def capture_export_boundaries(monkeypatch):
    messages = []
    events = []
    exceptions = []
    monkeypatch.setattr(
        export_module.QMessageBox,
        "information",
        lambda *args: messages.append(("information", args)),
    )
    monkeypatch.setattr(
        export_module.QMessageBox,
        "warning",
        lambda *args: messages.append(("warning", args)),
    )
    monkeypatch.setattr(
        export_module.QMessageBox,
        "critical",
        lambda *args: messages.append(("critical", args)),
    )
    monkeypatch.setattr(
        export_module,
        "record_validation_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )
    monkeypatch.setattr(
        export_module,
        "record_validation_exception",
        lambda *args, **kwargs: exceptions.append((args, kwargs)),
    )
    return messages, events, exceptions


def test_xray_worker_modes_cancellation_and_failure(qt_app, monkeypatch):
    calls = []

    class Processor:
        @staticmethod
        def generate_xray(image, mode):
            calls.append((image.shape, mode))
            return QImage(3, 2, QImage.Format.Format_ARGB32)

    monkeypatch.setattr(canvas_module, "VIEW_PROCESSOR_CLASS", Processor)
    for view_mode, expected_mode in (
        (CanvasView.VIEW_LIT, 1),
        (CanvasView.VIEW_XRAY_1, 1),
        (CanvasView.VIEW_XRAY_2, 2),
        (CanvasView.VIEW_XRAY_3, 3),
    ):
        finished = []
        progress = []
        worker = XrayWorker(np.zeros((3, 4), dtype=np.uint8), view_mode)
        worker.signals.finished.connect(
            lambda image, mode: finished.append((image.width(), mode))
        )
        worker.signals.progress.connect(progress.append)
        worker.run()
        assert calls[-1][1] == expected_mode
        assert finished == [(3, view_mode)]
        assert progress == [10, 90, 100]

    cancelled = XrayWorker(np.zeros((2, 2), dtype=np.uint8), CanvasView.VIEW_XRAY_1)
    cancelled.cancel()
    cancelled.run()
    assert len(calls) == 4

    monkeypatch.setattr(canvas_module, "VIEW_PROCESSOR_CLASS", None)
    XrayWorker(None, CanvasView.VIEW_XRAY_1).run()

    class FailedProcessor:
        @staticmethod
        def generate_xray(image, mode):
            raise RuntimeError("forced xray failure")

    monkeypatch.setattr(canvas_module, "VIEW_PROCESSOR_CLASS", FailedProcessor)
    XrayWorker(np.zeros((2, 2), dtype=np.uint8), CanvasView.VIEW_XRAY_1).run()


def test_export_single_invalid_cancel_success_and_failure(
    qt_app, tmp_path, monkeypatch
):
    scene = scene_with_exports()
    dialog = ExportDialog(scene)
    messages, events, exceptions = capture_export_boundaries(monkeypatch)
    monkeypatch.setattr(dialog, "_validation_file", lambda name: None)

    original_polygon = list(scene.objects["A"].polygon)
    scene.objects["A"].polygon = [(0, 0), (1, 1)]
    dialog.export_single()
    assert events[-1][0][:2] == ("export.sprite", "BLOCKED")
    scene.objects["A"].polygon = original_polygon

    monkeypatch.setattr(
        export_module.QFileDialog, "getSaveFileName", lambda *args: ("", "")
    )
    dialog.export_single()
    assert events[-1][0][:2] == ("export.sprite", "CANCELLED")

    image = Image.new("RGBA", (8, 6), (255, 0, 0, 255))
    monkeypatch.setattr(
        export_module, "extract_masked_sprite", lambda *args, **kwargs: image
    )
    success_path = tmp_path / "sprite.png"
    monkeypatch.setattr(
        export_module.QFileDialog,
        "getSaveFileName",
        lambda *args: (str(success_path), ""),
    )
    monkeypatch.setattr(
        export_module, "save_sprite", lambda value, path: value.save(path)
    )
    dialog.export_single()
    assert success_path.stat().st_size > 0
    assert events[-1][0][:2] == ("export.sprite", "SUCCESS")

    failed_path = tmp_path / "missing-output.png"
    monkeypatch.setattr(
        export_module.QFileDialog,
        "getSaveFileName",
        lambda *args: (str(failed_path), ""),
    )
    monkeypatch.setattr(export_module, "save_sprite", lambda *args: None)
    dialog.export_single()
    assert exceptions[-1][0][0] == "export.sprite"
    assert messages[-1][0] == "critical"
    dialog.close()


def test_export_batch_cancel_success_errors_and_interruption(
    qt_app, tmp_path, monkeypatch
):
    scene = scene_with_exports()
    scene.add_object("B", [(55, 10), (85, 10), (85, 40), (55, 40)])
    scene.objects["invalid"] = SimpleNamespace(polygon=[(0, 0), (1, 1)])
    dialog = ExportDialog(scene)
    messages, events, _ = capture_export_boundaries(monkeypatch)

    monkeypatch.setattr(
        export_module.QFileDialog, "getExistingDirectory", lambda *args: ""
    )
    dialog.export_batch()
    assert events[-1][0][:2] == ("export.sprite.batch", "CANCELLED")

    monkeypatch.setattr(
        export_module.QFileDialog,
        "getExistingDirectory",
        lambda *args: str(tmp_path),
    )
    created = progress_factory(monkeypatch, [(True,), (False, False, False), (False,)])
    monkeypatch.setattr(
        export_module,
        "extract_masked_sprite",
        lambda *args, **kwargs: Image.new("RGBA", (4, 4), (0, 255, 0, 255)),
    )
    monkeypatch.setattr(
        export_module, "save_sprite", lambda image, path: image.save(path)
    )
    dialog.export_batch()
    assert events[-1][0][:2] == ("export.sprite.batch", "CANCELLED")

    save_calls = []

    def partial_save(image, path):
        save_calls.append(path)
        if len(save_calls) == 1:
            image.save(path)

    monkeypatch.setattr(export_module, "save_sprite", partial_save)
    dialog.export_batch()
    assert events[-1][0][:2] == ("export.sprite.batch", "FAILURE")
    assert events[-1][1]["exported"] == 1
    assert events[-1][1]["errors"] == 1

    monkeypatch.setattr(
        export_module, "save_sprite", lambda image, path: image.save(path)
    )
    dialog.export_batch()
    assert events[-1][0][:2] == ("export.sprite.batch", "SUCCESS")
    assert created[-1].values[-1] == len(scene.objects)
    assert messages[-1][0] == "information"
    dialog.close()


def test_export_atlas_cancel_empty_success_and_failures(
    qt_app, tmp_path, monkeypatch
):  # noqa: E501
    scene = scene_with_exports()
    dialog = ExportDialog(scene)
    messages, events, exceptions = capture_export_boundaries(monkeypatch)
    monkeypatch.setattr(dialog, "_validation_directory", lambda name: None)

    monkeypatch.setattr(
        export_module.QFileDialog, "getExistingDirectory", lambda *args: ""
    )
    dialog.export_atlas()
    assert events[-1][0][:2] == ("export.atlas", "CANCELLED")

    monkeypatch.setattr(
        export_module.QFileDialog,
        "getExistingDirectory",
        lambda *args: str(tmp_path),
    )
    created = progress_factory(
        monkeypatch,
        [(True,), (False,), (False,), (False,), (False,)],
    )
    dialog.export_atlas()
    assert events[-1][0][:2] == ("export.atlas", "CANCELLED")
    assert created[0].closed is True

    monkeypatch.setattr(
        export_module,
        "extract_masked_sprite",
        Mock(side_effect=RuntimeError("forced extraction failure")),
    )
    dialog.export_atlas()
    assert events[-1][0][:2] == ("export.atlas", "BLOCKED")
    assert messages[-1][0] == "warning"

    image = Image.new("RGBA", (5, 5), (0, 0, 255, 255))
    monkeypatch.setattr(
        export_module, "extract_masked_sprite", lambda *args, **kwargs: image
    )
    atlas_path = tmp_path / "atlas.png"
    json_path = tmp_path / "atlas.json"

    def valid_atlas(items, directory, base_name, **kwargs):
        image.save(atlas_path)
        json_path.write_text('{"frames": {}}', encoding="utf-8")
        return [{"atlas_path": str(atlas_path), "json_path": str(json_path)}]

    monkeypatch.setattr(export_module, "build_atlas", valid_atlas)
    dialog.export_atlas()
    assert events[-1][0][:2] == ("export.atlas", "SUCCESS")
    assert created[2].range == (0, 0)

    monkeypatch.setattr(export_module, "build_atlas", lambda *args, **kwargs: [])
    dialog.export_atlas()
    assert exceptions[-1][0][0] == "export.atlas"

    monkeypatch.setattr(
        export_module,
        "build_atlas",
        Mock(side_effect=RuntimeError("forced atlas failure")),
    )
    dialog.export_atlas()
    assert exceptions[-1][0][0] == "export.atlas"
    assert messages[-1][0] == "critical"
    dialog.close()


def test_gltf_scene_and_object_cancel_success_and_postconditions(
    qt_app, tmp_path, monkeypatch
):
    scene = scene_with_exports()
    dialog = ExportDialog(scene)
    messages, events, exceptions = capture_export_boundaries(monkeypatch)
    monkeypatch.setattr(dialog, "_validation_file", lambda name: None)

    monkeypatch.setattr(
        export_module.QFileDialog, "getSaveFileName", lambda *args: ("", "")
    )
    dialog.export_gltf_scene()
    dialog.export_gltf_object()
    assert [entry[0][1] for entry in events[-2:]] == ["CANCELLED", "CANCELLED"]

    scene_path = tmp_path / "scene.glb"
    object_path = tmp_path / "object.glb"
    paths = iter((str(scene_path), str(object_path)))
    monkeypatch.setattr(
        export_module.QFileDialog,
        "getSaveFileName",
        lambda *args: (next(paths), ""),
    )

    def write_scene(value, path):
        with open(path, "wb") as stream:
            stream.write(b"glTF" + (2).to_bytes(4, "little") + b"scene")
        return True

    def write_object(object_id, value, path):
        with open(path, "wb") as stream:
            stream.write(b"glTF" + (2).to_bytes(4, "little") + b"object")
        return True

    monkeypatch.setattr(export_module, "export_scene_to_gltf", write_scene)
    monkeypatch.setattr(export_module, "export_object_to_gltf", write_object)
    dialog.export_gltf_scene()
    dialog.export_gltf_object()
    assert [entry[0][1] for entry in events[-2:]] == ["SUCCESS", "SUCCESS"]

    failed_paths = iter(
        (str(tmp_path / "failed-scene.glb"), str(tmp_path / "failed-object.glb"))
    )
    monkeypatch.setattr(
        export_module.QFileDialog,
        "getSaveFileName",
        lambda *args: (next(failed_paths), ""),
    )
    monkeypatch.setattr(export_module, "export_scene_to_gltf", lambda *args: False)
    monkeypatch.setattr(export_module, "export_object_to_gltf", lambda *args: False)
    dialog.export_gltf_scene()
    dialog.export_gltf_object()
    assert [entry[0][0] for entry in exceptions[-2:]] == [
        "export.gltf.scene",
        "export.gltf.object",
    ]
    assert messages[-1][0] == "critical"
    dialog.close()


def test_canvas_context_menu_selection_and_manual_polygon(qt_app, monkeypatch):
    scene = scene_with_exports()
    canvas = CanvasView(scene)
    canvas.resize(320, 240)
    callbacks = []
    menus = []

    class ActionProbe:
        def __init__(self, text):
            self.text = text
            self.enabled = True
            self.triggered = SimpleNamespace(connect=callbacks.append)

        def setEnabled(self, enabled):
            self.enabled = enabled

    class MenuProbe:
        def __init__(self, parent):
            self.actions = []
            menus.append(self)

        def setStyleSheet(self, value):
            self.style = value

        def addAction(self, text):
            action = ActionProbe(text)
            self.actions.append(action)
            return action

        def addSeparator(self):
            self.actions.append(None)

        def exec(self, position):
            self.executed_at = position

    monkeypatch.setattr(canvas_module, "QMenu", MenuProbe)
    canvas.contextMenuEvent(event(position=(20, 20)))
    assert any(action and "Selected" in action.text for action in menus[-1].actions)
    canvas.contextMenuEvent(event(position=(200, 200)))
    assert not any(action and "Selected" in action.text for action in menus[-1].actions)

    canvas._tool = ToolInterface(on_mouse_press=Mock())
    canvas.contextMenuEvent(event())
    canvas._tool = None
    canvas._current_polygon = [(1, 1)]
    canvas.contextMenuEvent(event())
    canvas._current_polygon = []
    monkeypatch.setattr(canvas, "get_transform", lambda: canvas_module.QTransform())

    middle = event(Qt.MouseButton.MiddleButton, (10, 10))
    canvas.mousePressEvent(middle)
    assert canvas._dragging is True
    canvas.mouseMoveEvent(event(Qt.MouseButton.NoButton, (20, 25)))
    canvas.mouseReleaseEvent(event(Qt.MouseButton.MiddleButton, (20, 25)))
    assert canvas._dragging is False

    canvas.mousePressEvent(event(position=(20, 20)))
    assert scene.selected_id == "A"
    canvas.mousePressEvent(event(position=(80, 80)))
    canvas.mousePressEvent(event(position=(81, 81)))
    assert len(canvas._current_polygon) == 1
    canvas.mousePressEvent(event(position=(90, 80)))
    canvas.mousePressEvent(event(position=(90, 90)))
    canvas.mousePressEvent(event(Qt.MouseButton.RightButton, (90, 90)))
    assert canvas._current_polygon == []
    assert len(scene.objects) == 2
    canvas.close()


def test_canvas_gizmo_tools_history_and_release_paths(qt_app, monkeypatch):
    scene = scene_with_exports()
    canvas = CanvasView(scene)
    canvas._qimage_lit = QImage(20, 20, QImage.Format.Format_ARGB32)
    canvas._gizmo_enabled = True
    canvas._preview_mode = False

    gizmo = SimpleNamespace(
        NONE=0,
        AXIS_X=1,
        AXIS_Y=2,
        active_axis=0,
        set_screen_position=Mock(),
        hit_test=Mock(return_value=1),
        update_hover=Mock(return_value=True),
        draw=Mock(),
    )
    canvas.gizmo = gizmo
    monkeypatch.setattr(canvas, "_begin_gizmo_object_gesture", Mock(return_value=False))
    canvas.mousePressEvent(event(position=(12, 13)))
    assert gizmo.active_axis == gizmo.NONE

    scene.select_object(None)
    canvas.mousePressEvent(event(position=(12, 13)))
    assert canvas._gizmo_active is False
    canvas.mouseMoveEvent(event(Qt.MouseButton.NoButton, (20, 30)))
    assert canvas._pan.y() == 0
    finish = Mock()
    monkeypatch.setattr(canvas, "_finish_gizmo_gesture", finish)
    canvas.mouseReleaseEvent(event())
    finish.assert_not_called()

    canvas._gizmo_active = True
    canvas._gizmo_transaction = object()
    canvas._gizmo_start_mouse = QPointF(20, 30)
    canvas._zoom = 2.0
    gizmo.active_axis = gizmo.AXIS_Y
    canvas._gizmo_operation = gizmo.AXIS_Y
    preview = Mock()
    monkeypatch.setattr(canvas, "_preview_gizmo_transform", preview)
    canvas.mouseMoveEvent(event(Qt.MouseButton.NoButton, (30, 40)))
    preview.assert_called_with(translation=(0.0, -5.0))
    canvas._gizmo_active = False
    canvas._gizmo_transaction = None
    gizmo.hit_test.return_value = gizmo.NONE
    tool = ToolInterface(
        on_mouse_press=Mock(),
        on_mouse_move=Mock(),
        on_mouse_release=Mock(),
        on_double_click=Mock(),
        on_key_press=Mock(return_value=True),
        on_undo=Mock(return_value=True),
        on_redo=Mock(side_effect=RuntimeError("forced redo failure")),
    )
    canvas._tool = tool
    canvas.mousePressEvent(event(position=(30, 30)))
    canvas.mouseMoveEvent(event(Qt.MouseButton.NoButton, (32, 34)))
    canvas.mouseReleaseEvent(event(position=(32, 34)))
    canvas.mouseDoubleClickEvent(event(position=(32, 34)))
    assert canvas.request_tool_undo() is True
    assert canvas.request_tool_redo() is False
    key_event = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_A,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.keyPressEvent(key_event)
    assert key_event.isAccepted()

    cancel = Mock()
    monkeypatch.setattr(canvas, "_cancel_gizmo_gesture", cancel)
    canvas._gizmo_active = True
    escape = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Escape,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.keyPressEvent(escape)
    cancel.assert_called_once()
    canvas.close()


def test_canvas_paint_modes_overlays_helpers_and_language(qt_app):
    scene = scene_with_exports()
    scene.add_object("B", [(55, 10), (85, 10), (85, 40), (55, 40)])
    canvas = CanvasView(scene)
    canvas.resize(360, 280)
    image = QImage(96, 96, QImage.Format.Format_ARGB32)
    image.fill(0xFF223344)
    canvas._qimage_lit = image
    canvas._qimage_xray_1 = image
    canvas._qimage_xray_2 = image
    canvas._qimage_xray_3 = image
    canvas._gizmo_enabled = True
    canvas.gizmo = SimpleNamespace(
        set_screen_position=Mock(),
        draw=Mock(),
    )
    canvas._tool = ToolInterface(draw_overlay=Mock(), update_language=Mock())
    canvas._collision_overlay = SimpleNamespace(draw=Mock())
    canvas._current_polygon = [(2, 2), (20, 2), (20, 20)]
    canvas._flash_color = canvas_module.QColor(255, 255, 255, 20)
    canvas.show()
    qt_app.processEvents()

    for mode in (
        CanvasView.VIEW_LIT,
        CanvasView.VIEW_XRAY_1,
        CanvasView.VIEW_XRAY_2,
        CanvasView.VIEW_XRAY_3,
        CanvasView.VIEW_COLLISION,
    ):
        canvas._view_mode = mode
        canvas.grab()

    canvas._preview_mode = True
    canvas.grab()
    canvas._preview_mode = False
    canvas._qimage_lit = None
    canvas.grab()

    target = QImage(200, 100, QImage.Format.Format_ARGB32)
    target.fill(0)
    painter = QPainter(target)
    canvas._draw_axis_gizmo(painter)
    canvas._draw_hud(painter)
    canvas._draw_grid(painter, 130, 90)
    painter.end()

    canvas.update_language("pt")
    assert canvas.gizmo_toggle.text() == "Eixo"
    canvas._tool.update_language.assert_called_once_with("pt")
    canvas.close()


def test_tileset_export_ui_cancel_and_success_paths(qt_app, tmp_path, monkeypatch):
    scene = scene_with_exports()
    dialog = ExportDialog(scene)
    messages, events, exceptions = capture_export_boundaries(monkeypatch)

    empty_dialog = ExportDialog(Scene())
    empty_dialog.export_tileset()
    assert events[-1][0][:2] == ("export.tileset", "BLOCKED")
    empty_dialog.close()

    monkeypatch.setattr(export_module.QInputDialog, "getInt", lambda *args: (16, False))
    dialog.export_tileset()
    assert events[-1][0][:2] == ("export.tileset", "CANCELLED")

    responses = iter([(16, True), (16, False)])
    monkeypatch.setattr(
        export_module.QInputDialog, "getInt", lambda *args: next(responses)
    )
    dialog.export_tileset()
    assert events[-1][0][:2] == ("export.tileset", "CANCELLED")

    monkeypatch.setattr(export_module.QInputDialog, "getInt", lambda *args: (16, True))
    monkeypatch.setattr(dialog, "_validation_directory", lambda name: None)
    monkeypatch.setattr(
        export_module.QFileDialog, "getExistingDirectory", lambda *args: ""
    )
    dialog.export_tileset()
    assert events[-1][0][:2] == ("export.tileset", "CANCELLED")

    monkeypatch.setattr(dialog, "_validation_directory", lambda name: str(tmp_path))
    dialog.export_tileset()
    assert events[-1][0][:2] == ("export.tileset", "SUCCESS")
    assert messages[-1][0] == "information"
    assert not exceptions
    dialog.close()


def test_animation_batch_export_ui_cancel_and_success_paths(
    qt_app, tmp_path, monkeypatch
):
    scene = scene_with_exports()
    dialog = ExportDialog(scene)
    messages, events, exceptions = capture_export_boundaries(monkeypatch)

    monkeypatch.setattr(
        export_module.QFileDialog, "getExistingDirectory", lambda *args: ""
    )
    dialog.export_animation_batch()
    assert events[-1][0][:2] == ("export.animation.batch", "CANCELLED")

    source = tmp_path / "frames"
    output = tmp_path / "animation"
    source.mkdir()
    output.mkdir()
    image = Image.new("RGBA", (24, 24), (255, 255, 255, 0))
    ImageDraw.Draw(image).rectangle((4, 4, 18, 18), fill=(255, 255, 255, 255))
    image.save(source / "frame_1.png")
    directories = iter((str(source), ""))
    monkeypatch.setattr(
        export_module.QFileDialog,
        "getExistingDirectory",
        lambda *args: next(directories),
    )
    monkeypatch.setattr(dialog, "_validation_directory", lambda name: None)
    dialog.export_animation_batch()
    assert events[-1][0][:2] == ("export.animation.batch", "CANCELLED")

    directories = iter((str(source), str(output)))
    monkeypatch.setattr(
        export_module.QFileDialog,
        "getExistingDirectory",
        lambda *args: next(directories),
    )
    monkeypatch.setattr(dialog, "_validation_directory", lambda name: None)
    dialog.export_animation_batch()
    assert events[-1][0][:2] == ("export.animation.batch", "SUCCESS")
    assert messages[-1][0] == "information"
    assert not exceptions
    dialog.close()
