"""P2D-05 regression tests for LayersPanel command failures."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from src.core.commands import CommandManager, CommandStatus, CreateLayerCommand
from src.models.scene import Scene
from src.ui.layers_panel import LayersPanel


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _window_with_panel(qt_app: QApplication):
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    layer = scene.create_layer("Artwork")
    window = QMainWindow()
    panel = LayersPanel(scene, window)
    window.statusBar()
    window.show()
    panel.show()
    qt_app.processEvents()
    assert panel._select_layer_id(layer.id)
    return window, panel, scene


def _capture_modals(monkeypatch: pytest.MonkeyPatch):
    boxes = []

    def capture(box):
        boxes.append(box)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "exec", capture)
    return boxes


def _layer_state(scene: Scene):
    return [
        (layer.id, layer.name, layer.visible, layer.locked) for layer in scene.layers
    ]


def _close_window(qt_app: QApplication, window: QMainWindow) -> None:
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def test_rejected_layer_command_uses_persistent_status_without_mutation(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _layer_state(scene)
    before_history = scene.cmd.undo_count
    raw = r"layer rejected at C:\Project\private\scene.ndtscene " "token=top-secret"

    def reject(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.REJECTED,
            changed=False,
            message=raw,
        )

    monkeypatch.setattr(scene.cmd, "execute", reject)
    boxes = _capture_modals(monkeypatch)

    result = panel._execute_edit_command(CreateLayerCommand("Draft"))

    status_message = window.statusBar().currentMessage()
    assert result.status is CommandStatus.REJECTED
    assert boxes == []
    assert "P2D05-OPERATION" in status_message
    assert "Verify the selected item and document state" in status_message
    assert "No change was applied" in status_message
    assert r"C:\Project\private" not in status_message
    assert "top-secret" not in status_message
    assert _layer_state(scene) == before
    assert scene.cmd.undo_count == before_history
    _close_window(qt_app, window)


def test_failed_layer_command_uses_safe_modal_with_details(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _layer_state(scene)
    before_history = scene.cmd.undo_count
    raw = r"layer failed at C:\Project\private\scene.ndtscene " "password=hunter2"

    def fail(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.FAILED,
            changed=False,
            message=raw,
        )

    monkeypatch.setattr(scene.cmd, "execute", fail)
    boxes = _capture_modals(monkeypatch)

    result = panel._execute_edit_command(CreateLayerCommand("Draft"))

    assert result.status is CommandStatus.FAILED
    assert len(boxes) == 1
    box = boxes[0]
    assert "P2D05-OPERATION" in box.text()
    assert "No change was applied" in box.text()
    assert box.accessibleName() == "P2D05-OPERATION"
    assert r"C:\Project\private" not in box.text()
    assert r"C:\Project\private" not in box.detailedText()
    assert "hunter2" not in box.text()
    assert "hunter2" not in box.detailedText()
    assert _layer_state(scene) == before
    assert scene.cmd.undo_count == before_history
    box.deleteLater()
    _close_window(qt_app, window)


def test_missing_layer_history_uses_safe_modal_and_preserves_state(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _layer_state(scene)
    scene.cmd = None
    boxes = _capture_modals(monkeypatch)

    result = panel._execute_edit_command(CreateLayerCommand("Draft"))

    assert result is None
    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert "Verify the selected item and document state" in boxes[0].text()
    assert "No change was applied" in boxes[0].text()
    assert _layer_state(scene) == before
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_layer_action_exception_uses_safe_modal_without_mutation(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    before = _layer_state(scene)
    raw = (
        r"unexpected layer error at C:\Project\private\scene.ndtscene "
        "secret=top-secret"
    )
    boxes = _capture_modals(monkeypatch)

    def fail(_command):
        raise TypeError(raw)

    monkeypatch.setattr(panel, "_execute_edit_command", fail)
    panel._toggle_vis()

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert "No change was applied" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].detailedText()
    assert "top-secret" not in boxes[0].text()
    assert "top-secret" not in boxes[0].detailedText()
    assert _layer_state(scene) == before
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_layers_panel_forwards_language_to_p2d05_status(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, panel, scene = _window_with_panel(qt_app)
    panel.update_language("pt")

    def reject(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.REJECTED,
            changed=False,
            message="rejected",
        )

    monkeypatch.setattr(scene.cmd, "execute", reject)
    panel._execute_edit_command(CreateLayerCommand("Draft"))

    status_message = window.statusBar().currentMessage()
    assert "A operação foi rejeitada" in status_message
    assert "Nenhuma alteração foi aplicada" in status_message
    _close_window(qt_app, window)
