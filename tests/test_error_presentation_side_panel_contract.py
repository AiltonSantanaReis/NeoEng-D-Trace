"""P2D-05 regression tests for SidePanel numeric-transform failures."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.side_panel import SidePanel


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _window_with_panel(qt_app: QApplication):
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object(
        "object",
        [(10, 10), (30, 10), (30, 30), (10, 30)],
        select=True,
    )
    window = QMainWindow()
    canvas = CanvasView(scene, window)
    window.setCentralWidget(canvas)
    panel = SidePanel(scene, canvas, window)
    window.statusBar()
    window.show()
    panel.show()
    qt_app.processEvents()
    return window, panel, scene


def _capture_modals(monkeypatch: pytest.MonkeyPatch):
    boxes = []

    def capture(box):
        boxes.append(box)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "exec", capture)
    return boxes


def _scene_transform_state(scene: Scene):
    obj = scene.objects["object"]
    return (
        tuple(obj.position),
        tuple(obj.rotation),
        tuple(obj.scale),
        tuple(obj.pivot),
        list(obj.polygon),
    )


def _close_window(qt_app: QApplication, window: QMainWindow) -> None:
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def test_rejected_numeric_transform_uses_persistent_status_without_mutation(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _scene_transform_state(scene)
    before_history = scene.cmd.undo_count
    panel.position_x.setValue(90.0)
    raw = (
        r"transform rejected at C:\Project\private\private\scene.ndtscene "
        "token=top-secret"
    )

    def reject(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.REJECTED,
            changed=False,
            message=raw,
        )

    monkeypatch.setattr(scene.cmd, "execute", reject)
    boxes = _capture_modals(monkeypatch)

    panel._on_apply_transform()

    status_message = window.statusBar().currentMessage()
    assert boxes == []
    assert "P2D05-OPERATION" in status_message
    assert "Verify the selected item and document state" in status_message
    assert "No change was applied" in status_message
    assert r"C:\Project\private" not in status_message
    assert "top-secret" not in status_message
    assert _scene_transform_state(scene) == before
    assert scene.cmd.undo_count == before_history
    assert panel.position_x.value() == pytest.approx(90.0)
    _close_window(qt_app, window)


def test_failed_numeric_transform_uses_safe_critical_modal_and_preserves_state(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _scene_transform_state(scene)
    before_history = scene.cmd.undo_count
    raw = (
        r"transform failed at C:\Project\private\private\scene.ndtscene "
        "password=hunter2"
    )

    def fail(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.FAILED,
            changed=False,
            message=raw,
        )

    monkeypatch.setattr(scene.cmd, "execute", fail)
    boxes = _capture_modals(monkeypatch)

    panel._on_apply_transform()

    assert len(boxes) == 1
    box = boxes[0]
    assert box.accessibleName() == "P2D05-OPERATION"
    assert "P2D05-OPERATION" in box.text()
    assert "No change was applied" in box.text()
    assert r"C:\Project\private" not in box.text()
    assert "hunter2" not in box.text()
    assert "hunter2" not in box.detailedText()
    assert _scene_transform_state(scene) == before
    assert scene.cmd.undo_count == before_history
    box.deleteLater()
    _close_window(qt_app, window)


def test_invalid_numeric_transform_uses_status_and_keeps_history_unchanged(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    scene.objects["object"].scale = (0.0, 1.0, 1.0)
    before = _scene_transform_state(scene)
    before_history = scene.cmd.undo_count
    boxes = _capture_modals(monkeypatch)

    panel._on_apply_transform()

    status_message = window.statusBar().currentMessage()
    assert boxes == []
    assert "P2D05-OPERATION" in status_message
    assert "No change was applied" in status_message
    assert _scene_transform_state(scene) == before
    assert scene.cmd.undo_count == before_history
    _close_window(qt_app, window)


def test_missing_transform_history_uses_safe_critical_modal(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _scene_transform_state(scene)
    scene.cmd = None
    boxes = _capture_modals(monkeypatch)

    panel._on_apply_transform()

    assert len(boxes) == 1
    assert boxes[0].accessibleName() == "P2D05-OPERATION"
    assert "Verify the selected item and document state" in boxes[0].text()
    assert "No change was applied" in boxes[0].text()
    assert _scene_transform_state(scene) == before
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_unexpected_transform_exception_uses_redacted_critical_modal(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _scene_transform_state(scene)
    raw = (
        r"unexpected transform error at C:\Project\private\private\scene.ndtscene "
        "secret=top-secret"
    )

    def fail_capture(*_args, **_kwargs):
        raise TypeError(raw)

    monkeypatch.setattr("src.ui.side_panel.capture_transform_state", fail_capture)
    boxes = _capture_modals(monkeypatch)

    panel._on_apply_transform()

    assert len(boxes) == 1
    assert boxes[0].accessibleName() == "P2D05-OPERATION"
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert "top-secret" not in boxes[0].detailedText()
    assert _scene_transform_state(scene) == before
    assert scene.cmd.undo_count == 0
    boxes[0].deleteLater()
    _close_window(qt_app, window)
