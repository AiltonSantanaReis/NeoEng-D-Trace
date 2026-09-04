"""Behavioral tests for the first P2D-05 error-presentation lot."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QStatusBar, QWidget

from src.core.bezier_geometry import BezierSegments
from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.persistence.p2d05_presentation import build_p2d05_presentation
from src.tools.pen_tool import PenTool
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui.error_presentation import show_p2d05_error

BEZIERS: BezierSegments = [
    ((0.0, 0.0), (0.0, -20.0), (20.0, -20.0), (20.0, 0.0)),
]


class _Canvas:
    def __init__(self, model):
        self.model = model
        self.updates = 0
        self._zoom = 1.0

    def update(self):
        self.updates += 1

    def get_zoom(self):
        return self._zoom


class _StatusWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._status_bar = QStatusBar(self)

    def statusBar(self):
        return self._status_bar


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_build_p2d05_presentation_localizes_action_and_redacts_detail():
    exc = OSError(
        r"write failed at C:\Project\private\private\scene.json token=top-secret"
    )

    presentation = build_p2d05_presentation(
        exc,
        operation="save",
        language="pt",
    )

    assert presentation.code == "P2D05-WRITE"
    assert presentation.severity == "WARNING"
    assert presentation.blocking is False
    assert presentation.headline == "Não foi possível salvar o cenário"
    assert presentation.action == (
        "Verifique a permissão de gravação e o espaço livre e tente novamente"
    )
    assert presentation.preserved_state == (
        "O arquivo salvo anteriormente permanece inalterado"
    )
    assert presentation.channel == "MODAL"
    assert presentation.retryable is True
    assert presentation.focus_target is None
    assert "Não foi possível salvar o cenário" in presentation.message
    assert "Verifique a permissão de gravação" in presentation.message
    assert "arquivo salvo anteriormente permanece inalterado" in presentation.message
    assert r"C:\Project\private" not in presentation.message
    assert "top-secret" not in presentation.message
    assert "<path>" in presentation.safe_detail
    assert "top-secret" not in presentation.detailed_text
    assert "Código do erro: P2D05-WRITE" in presentation.detailed_text


def test_modal_uses_real_qt_box_with_safe_details(qt_app, monkeypatch):
    parent = QWidget()
    boxes = []

    def capture_exec(box):
        boxes.append(box)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "exec", capture_exec)
    exc = OSError(
        r"write failed at C:\Project\private\private\scene.json token=top-secret"
    )

    presentation = show_p2d05_error(
        parent,
        exc,
        operation="save",
        language="pt",
        severity="critical",
        channel="modal",
    )

    assert len(boxes) == 1
    box = boxes[0]
    assert presentation.code == "P2D05-WRITE"
    assert presentation.severity == "CRITICAL"
    assert presentation.blocking is True
    assert presentation.channel == "MODAL"
    assert presentation.retryable is True
    assert box.windowTitle() == "Falha na operação"
    assert box.textFormat() == Qt.TextFormat.PlainText
    assert box.accessibleName() == "P2D05-WRITE"
    assert box.text() == presentation.message
    assert box.detailedText() == presentation.detailed_text
    assert r"C:\Project\private" not in box.text()
    assert r"C:\Project\private" not in box.detailedText()
    assert "top-secret" not in box.text()
    assert "top-secret" not in box.detailedText()

    box.deleteLater()
    parent.deleteLater()
    qt_app.processEvents()


def test_status_channel_is_persistent_and_actionable(qt_app):
    window = _StatusWindow()
    exc = ValueError(
        r"Invalid sampled geometry at C:\Project\private\private\scene.json "
        "token=top-secret"
    )

    presentation = show_p2d05_error(
        window,
        exc,
        operation="edit",
        severity="warning",
        channel="status",
    )

    status_message = window.statusBar().currentMessage()
    assert presentation.code == "P2D05-OPERATION"
    assert presentation.severity == "WARNING"
    assert presentation.blocking is False
    assert presentation.channel == "STATUS"
    assert presentation.retryable is True
    assert status_message == presentation.message
    assert "Verify the selected item and document state" in status_message
    assert "No change was applied" in status_message
    assert r"C:\Project\private" not in status_message
    assert "top-secret" not in status_message

    window.deleteLater()
    qt_app.processEvents()


def test_pen_invalid_close_preserves_nodes_model_and_history():
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    tool = PenTool(_Canvas(scene))
    tool._load_nodes_from_beziers(BEZIERS)
    before_nodes = tuple(node.anchor for node in tool._nodes)
    before_objects = dict(scene.objects)
    before_history = scene.cmd.undo_count

    assert tool.commit_selection(closed=True) is None

    assert tuple(node.anchor for node in tool._nodes) == before_nodes
    assert scene.objects == before_objects
    assert scene.cmd.undo_count == before_history
    assert tool._editing_object_id is None
    assert tool._last_error.startswith("The operation was rejected [P2D05-OPERATION]")
    assert "Verify the selected item and document state" in tool._last_error
    assert "No change was applied" in tool._last_error


def test_pen_rejection_preserves_state_and_redacts_command_detail(monkeypatch):
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    tool = PenTool(_Canvas(scene))
    tool._load_nodes_from_beziers(BEZIERS)
    before_nodes = tuple(node.anchor for node in tool._nodes)
    before_objects = dict(scene.objects)
    before_history = scene.cmd.undo_count

    def reject(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.REJECTED,
            changed=False,
            message=(
                r"Invalid sampled geometry at C:\Project\private\private\scene.json "
                "token=top-secret"
            ),
        )

    monkeypatch.setattr(scene.cmd, "execute", reject)

    assert tool.commit_selection() is None

    assert tuple(node.anchor for node in tool._nodes) == before_nodes
    assert scene.objects == before_objects
    assert scene.cmd.undo_count == before_history
    assert tool._editing_object_id is None
    assert "P2D05-OPERATION" in tool._last_error
    assert "Verify the selected item and document state" in tool._last_error
    assert "No change was applied" in tool._last_error
    assert r"C:\Project\private" not in tool._last_error
    assert "top-secret" not in tool._last_error


def test_polygon_selection_and_rejection_are_actionable_without_mutation(monkeypatch):
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object(
        "poly",
        [(0, 0), (20, 0), (20, 20), (0, 20)],
    )
    before_polygon = list(scene.objects["poly"].polygon)
    before_history = scene.cmd.undo_count
    tool = PolygonEditTool(_Canvas(scene))

    tool.start_adding_new()
    assert "P2D05-OPERATION" in tool._last_error

    assert "Verify the selected item and document state" in tool._last_error

    tool.selected_polygon_id = "poly"
    tool.selected_vertex = 1

    def reject(_command, _model):
        return SimpleNamespace(
            status=CommandStatus.REJECTED,
            changed=False,
            message=(
                r"geometry rejected at C:\Project\private\private\scene.json "
                "token=top-secret"
            ),
        )

    monkeypatch.setattr(scene.cmd, "execute", reject)
    tool.add_vertex_at_pos((20, 10))

    assert scene.objects["poly"].polygon == before_polygon
    assert scene.cmd.undo_count == before_history
    assert "P2D05-OPERATION" in tool._last_error
    assert "No change was applied" in tool._last_error
    assert r"C:\Project\private" not in tool._last_error
    assert "top-secret" not in tool._last_error
