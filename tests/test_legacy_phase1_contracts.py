"""Phase 1 contracts: real fixtures, concrete boundaries and Qt delivery."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QApplication

from src.core.commands import AddPolygonCommand, CommandStatus
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from tests.legacy_phase1_fixtures import (
    POLYGON_FIXTURES,
    DeterministicSignalEmitter,
    key_event,
    mouse_event,
    qimage_from_array,
    real_canvas,
    real_scene,
    scene_state_token,
    synthetic_image_array,
    wait_for_signal,
)


@pytest.fixture()
def qt_app() -> QApplication:
    """Provide the required real QApplication explicitly to each Qt test."""

    return QApplication.instance() or QApplication([])


def _fixtures_by_classification(classification: str):
    return [
        fixture
        for fixture in POLYGON_FIXTURES
        if fixture.classification == classification
    ]


def test_polygon_fixtures_have_stable_hashes_and_explicit_expectations():
    assert {fixture.name for fixture in POLYGON_FIXTURES} == {
        "valid_rectangle",
        "valid_l_shape",
        "invalid_self_overlapping",
        "invalid_collinear",
    }
    for fixture in POLYGON_FIXTURES:
        assert fixture.sha256 == fixture.expected_sha256
        assert fixture.sha256 == fixture.sha256
        assert fixture.points


def test_valid_and_invalid_polygon_fixtures_follow_real_scene_contract():
    for fixture in _fixtures_by_classification("valid"):
        scene = real_scene()
        scene.add_object(fixture.name, list(fixture.points), select=True)
        assert fixture.name in scene.objects
        assert scene.selected_id == fixture.name

    for fixture in _fixtures_by_classification(
        "invalid_self_intersection"
    ) + _fixtures_by_classification("invalid_zero_area"):
        scene = real_scene()
        before = scene_state_token(scene)
        with pytest.raises(ValueError, match="Invalid polygon"):
            scene.add_object(fixture.name, list(fixture.points), select=True)
        assert scene_state_token(scene) == before
        assert scene.cmd.undo_count == 0


def test_real_scene_manager_contract_preserves_state_on_failed_command():
    scene = real_scene()
    valid = next(
        fixture for fixture in POLYGON_FIXTURES if fixture.name == "valid_l_shape"
    )
    invalid = next(
        fixture for fixture in POLYGON_FIXTURES if fixture.name == "invalid_collinear"
    )

    command = AddPolygonCommand(list(valid.points))
    applied = scene.cmd.execute(command, scene)
    assert applied.status is CommandStatus.APPLIED
    assert command.object_id is not None
    committed = scene_state_token(scene)
    assert scene.cmd.undo_count == 1

    failed = scene.cmd.execute(AddPolygonCommand(list(invalid.points)), scene)
    assert failed.status is CommandStatus.FAILED
    assert failed.error_type == "ValueError"
    assert scene_state_token(scene) == committed
    assert scene.cmd.undo_count == 1

    undone = scene.cmd.undo(scene)
    assert undone.status is CommandStatus.APPLIED
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 1
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene_state_token(scene) == committed


def test_real_image_factories_preserve_qimage_and_ndarray_contract():
    array = synthetic_image_array()
    qimage = qimage_from_array(array)

    assert isinstance(array, np.ndarray)
    assert array.dtype == np.uint8
    assert array.shape == (24, 32)
    assert isinstance(qimage, QImage)
    assert qimage.width() == 32
    assert qimage.height() == 24
    assert qimage.format() == QImage.Format.Format_Grayscale8

    array_scene = real_scene(image=array)
    qimage_scene = real_scene(image=qimage)
    assert array_scene.get_image() is array
    assert qimage_scene.get_image() is qimage


def test_real_canvas_view_uses_real_scene_and_command_manager(qt_app: QApplication):
    scene = real_scene(image=qimage_from_array(synthetic_image_array()))
    canvas = real_canvas(scene)
    canvas.resize(640, 480)
    canvas.show()
    qt_app.processEvents()
    try:
        assert isinstance(canvas, CanvasView)
        assert isinstance(canvas.model, Scene)
        assert canvas.model is scene
        object_id = canvas._commit_native_polygon([(0, 0), (40, 0), (40, 30), (0, 30)])
        assert object_id in scene.objects
        assert scene.selected_id == object_id
        assert scene.cmd.undo_count == 1
    finally:
        canvas.close()
        canvas.deleteLater()
        qt_app.processEvents()


def test_native_qt_event_factories_create_typed_events():
    press = mouse_event(
        QEvent.Type.MouseButtonPress,
        10,
        12,
        button=Qt.MouseButton.LeftButton,
    )
    move = mouse_event(
        QEvent.Type.MouseMove,
        14,
        16,
        button=Qt.MouseButton.NoButton,
        buttons=Qt.MouseButton.LeftButton,
    )
    key = key_event(Qt.Key.Key_Escape)

    assert isinstance(press, QMouseEvent)
    assert press.type() is QEvent.Type.MouseButtonPress
    assert press.position().x() == 10.0
    assert isinstance(move, QMouseEvent)
    assert move.type() is QEvent.Type.MouseMove
    assert move.buttons() == Qt.MouseButton.LeftButton
    assert isinstance(key, QKeyEvent)
    assert key.key() == Qt.Key.Key_Escape


def test_event_loop_waits_for_real_signal_without_arbitrary_sleep(
    qt_app: QApplication,
):
    emitter = DeterministicSignalEmitter()
    token: dict[str, Any] = {"generation": 3, "request": 11}

    payload = wait_for_signal(
        emitter.ready,
        lambda: QTimer.singleShot(0, lambda: emitter.ready.emit(token)),
        timeout_ms=250,
    )

    assert payload == (token,)
    qt_app.processEvents()


def test_event_loop_timeout_is_explicit_and_not_a_skip(qt_app: QApplication):
    emitter = DeterministicSignalEmitter()

    with pytest.raises(TimeoutError, match="within 20 ms"):
        wait_for_signal(emitter.ready, lambda: None, timeout_ms=20)
