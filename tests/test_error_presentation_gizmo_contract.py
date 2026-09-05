"""P2D-05 regression tests for CanvasView transform-gizmo failures."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _window_with_scene(qt_app: QApplication, *, manager: bool = True):
    scene = Scene()
    scene.cmd = CommandManager(max_history=10) if manager else None
    scene.add_object(
        "object",
        [(10, 10), (30, 10), (30, 30), (10, 30)],
        select=True,
    )
    window = QMainWindow()
    canvas = CanvasView(scene, window)
    window.setCentralWidget(canvas)
    window.statusBar()
    window.show()
    qt_app.processEvents()
    return window, canvas, scene


def _capture_modals(monkeypatch: pytest.MonkeyPatch):
    boxes = []

    def capture(box):
        boxes.append(box)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "exec", capture)
    return boxes


def _close_window(qt_app: QApplication, window: QMainWindow) -> None:
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def test_rejected_gizmo_result_is_persistent_actionable_status_without_mutation(
    qt_app: QApplication,
):
    window, canvas, scene = _window_with_scene(qt_app)
    before = list(scene.objects["object"].polygon)
    raw = (
        r"geometry changed at C:\Project\private\private\scene.ndtscene "
        "token=top-secret"
    )

    presentation = canvas._report_gizmo_result(
        SimpleNamespace(status=CommandStatus.REJECTED, message=raw)
    )

    assert presentation is not None
    assert presentation.code == "P2D05-OPERATION"
    assert presentation.channel == "STATUS"
    assert presentation.blocking is False
    assert "Verify the selected item and document state" in presentation.message
    assert "No change was applied" in presentation.message
    assert window.statusBar().currentMessage() == presentation.message
    assert r"C:\Project\private" not in presentation.message
    assert "top-secret" not in presentation.message
    assert scene.objects["object"].polygon == before
    assert scene.cmd.undo_count == 0
    _close_window(qt_app, window)


def test_failed_gizmo_result_uses_safe_modal_with_accessible_details(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    raw = (
        r"transform failed at C:\Project\private\private\scene.ndtscene "
        "password=hunter2"
    )

    presentation = canvas._report_gizmo_result(
        SimpleNamespace(status=CommandStatus.FAILED, message=raw)
    )

    assert len(boxes) == 1
    box = boxes[0]
    assert presentation is not None
    assert presentation.code == "P2D05-OPERATION"
    assert presentation.channel == "MODAL"
    assert presentation.blocking is True
    assert box.accessibleName() == "P2D05-OPERATION"
    assert box.text() == presentation.message
    assert box.detailedText() == presentation.detailed_text
    assert r"C:\Project\private" not in box.text()
    assert "hunter2" not in box.text()
    assert "hunter2" not in box.detailedText()
    assert scene.cmd.undo_count == 0
    box.deleteLater()
    _close_window(qt_app, window)


def test_gizmo_requires_history_and_preserves_state(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app, manager=False)
    boxes = _capture_modals(monkeypatch)
    before = list(scene.objects["object"].polygon)

    assert canvas._begin_gizmo_object_gesture() is False

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert "Verify the selected item and document state" in boxes[0].text()
    assert "No change was applied" in boxes[0].text()
    assert canvas._gizmo_transaction is None
    assert scene.objects["object"].polygon == before
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_preview_failure_rolls_back_and_never_exposes_raw_detail(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    before = list(scene.objects["object"].polygon)
    assert canvas._begin_gizmo_object_gesture() is True
    transaction = canvas._gizmo_transaction
    assert transaction is not None

    def fail_preview(**_kwargs):
        raise RuntimeError(
            r"preview failed at C:\Project\private\private\scene.ndtscene "
            "token=top-secret"
        )

    monkeypatch.setattr(transaction, "preview_transform", fail_preview)
    canvas._preview_gizmo_transform(translation=(5.0, 2.0))

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert scene.objects["object"].polygon == before
    assert scene.cmd.undo_count == 0
    assert canvas._gizmo_transaction is None
    assert canvas._gizmo_active is False
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_commit_failure_rolls_back_preview_without_history(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    before = list(scene.objects["object"].polygon)
    assert canvas._begin_gizmo_object_gesture() is True
    transaction = canvas._gizmo_transaction
    assert transaction is not None
    canvas._preview_gizmo_transform(translation=(5.0, 2.0))
    assert scene.objects["object"].polygon != before

    def fail_commit(_manager):
        raise RuntimeError(
            r"commit failed at C:\Project\private\private\scene.ndtscene "
            "secret=top-secret"
        )

    monkeypatch.setattr(transaction, "commit", fail_commit)
    assert canvas._finish_gizmo_gesture() is None

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert scene.objects["object"].polygon == before
    assert scene.cmd.undo_count == 0
    assert canvas._gizmo_transaction is None
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_cancel_failure_reports_error_and_does_not_overwrite_external_state(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    assert canvas._begin_gizmo_object_gesture() is True
    canvas._preview_gizmo_transform(translation=(5.0, 2.0))
    scene.objects["object"].position = (999.0, 998.0, 0.0)

    assert canvas._cancel_gizmo_gesture() is False

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert "No change was applied" in boxes[0].text()
    assert tuple(scene.objects["object"].position) == (999.0, 998.0, 0.0)
    assert scene.cmd.undo_count == 0
    assert canvas._gizmo_transaction is None
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_vertex_gizmo_start_exception_uses_same_safe_boundary(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    canvas._tool = SimpleNamespace(
        selected_polygon_id="object",
        selected_vertex=0,
        begin_vertex_gizmo_gesture=lambda: (_ for _ in ()).throw(
            RuntimeError(
                r"vertex start failed at C:\Project\private\private\scene.ndtscene "
                "token=top-secret"
            )
        ),
    )

    assert canvas._begin_gizmo_vertex_gesture() is False

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert scene.cmd.undo_count == 0
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_gizmo_constructor_failure_uses_safe_modal(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)

    def fail_constructor(*_args, **_kwargs):
        raise RuntimeError(
            r"transaction failed at C:\Project\private\private\scene.ndtscene "
            "token=top-secret"
        )

    monkeypatch.setattr(
        "src.ui.canvas_view.TransformGestureTransaction",
        fail_constructor,
    )
    assert canvas._begin_gizmo_object_gesture() is False

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert canvas._gizmo_transaction is None
    assert scene.cmd.undo_count == 0
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_preview_failure_with_rollback_failure_still_surfaces_safe_error(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    assert canvas._begin_gizmo_object_gesture() is True
    transaction = canvas._gizmo_transaction
    assert transaction is not None

    def fail_preview(**_kwargs):
        raise RuntimeError(
            r"preview failed at C:\Project\private\private\scene.ndtscene "
            "token=top-secret"
        )

    def fail_rollback():
        raise RuntimeError(
            r"rollback failed at C:\Project\private\private\scene.ndtscene "
            "secret=top-secret"
        )

    monkeypatch.setattr(transaction, "preview_transform", fail_preview)
    monkeypatch.setattr(transaction, "cancel", fail_rollback)
    canvas._preview_gizmo_transform(translation=(5.0, 2.0))

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert scene.cmd.undo_count == 0
    assert canvas._gizmo_transaction is None
    boxes[0].deleteLater()
    _close_window(qt_app, window)


def test_commit_failure_with_rollback_failure_still_surfaces_safe_error(
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
):
    window, canvas, scene = _window_with_scene(qt_app)
    boxes = _capture_modals(monkeypatch)
    assert canvas._begin_gizmo_object_gesture() is True
    transaction = canvas._gizmo_transaction
    assert transaction is not None

    def fail_commit(_manager):
        raise RuntimeError(
            r"commit failed at C:\Project\private\private\scene.ndtscene "
            "token=top-secret"
        )

    def fail_rollback():
        raise RuntimeError(
            r"rollback failed at C:\Project\private\private\scene.ndtscene "
            "secret=top-secret"
        )

    monkeypatch.setattr(transaction, "commit", fail_commit)
    monkeypatch.setattr(transaction, "cancel", fail_rollback)
    assert canvas._finish_gizmo_gesture() is None

    assert len(boxes) == 1
    assert "P2D05-OPERATION" in boxes[0].text()
    assert r"C:\Project\private" not in boxes[0].text()
    assert "top-secret" not in boxes[0].text()
    assert scene.cmd.undo_count == 0
    assert canvas._gizmo_transaction is None
    boxes[0].deleteLater()
    _close_window(qt_app, window)
