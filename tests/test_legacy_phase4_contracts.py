"""Native contracts for legacy cases #17--#22 and #27.

These tests intentionally use the production Scene/CommandManager/CanvasView
objects, real Qt image/event objects, and real OpenCV/Qt worker execution.
They do not replace a missing production contract with a generic test double.
"""

from __future__ import annotations

from typing import Any, Callable

import cv2
import numpy as np
import pytest
import shiboken6
from PySide6.QtCore import QEvent, QEventLoop, Qt, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from src.core.commands import CommandStatus
from src.models.scene import Scene
from src.tools.magnetic_lasso import (
    MagneticLassoTool,
    _MagneticPathWorker,
)
from src.tools.magnetic_lasso_engine import (
    MagneticLassoSettings,
    build_edge_features,
)
from tests.legacy_phase1_fixtures import (
    mouse_event,
    qimage_from_array,
    real_canvas,
    real_scene,
)


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def native_scene_canvas(qt_app: QApplication):
    image = _phase4_image()
    scene = real_scene(image=image, image_path="fixture://legacy-phase4")
    canvas = real_canvas(scene)
    canvas.resize(180, 180)
    canvas.show()
    qt_app.processEvents()
    try:
        yield scene, canvas, image
    finally:
        if shiboken6.isValid(canvas):
            canvas.close()
            canvas.deleteLater()
            qt_app.processEvents()


def _phase4_image() -> np.ndarray:
    """Return a fixed image with two deterministic contours."""

    image = np.zeros((160, 160), dtype=np.uint8)
    cv2.rectangle(image, (24, 24), (136, 136), 255, 2)
    cv2.circle(image, (80, 80), 42, 180, 2)
    return image


def _large_phase4_image() -> np.ndarray:
    """Return a deterministic workload that exceeds the segment deadline."""

    image = np.zeros((1024, 1024), dtype=np.uint8)
    cv2.rectangle(image, (128, 128), (896, 896), 255, 3)
    cv2.line(image, (128, 896), (896, 128), 190, 3)
    cv2.circle(image, (512, 512), 280, 160, 3)
    return image


def _wait_until(
    app: QApplication,
    predicate: Callable[[], bool],
    *,
    timeout_ms: int = 3000,
    description: str,
) -> None:
    """Wait through the Qt event loop with an explicit deterministic timeout."""

    if predicate():
        return
    loop = QEventLoop()
    poll = QTimer()
    deadline = QTimer()
    state = {"satisfied": False}

    def check() -> None:
        if predicate():
            state["satisfied"] = True
            loop.quit()

    poll.setInterval(1)
    poll.timeout.connect(check)
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poll.start()
    deadline.start(timeout_ms)
    check()
    if not state["satisfied"]:
        loop.exec()
    poll.stop()
    deadline.stop()
    app.processEvents()
    if not state["satisfied"] and not predicate():
        raise AssertionError(f"timeout waiting for {description}")


def _run_worker(
    app: QApplication,
    worker: _MagneticPathWorker,
    *,
    description: str,
) -> dict[str, Any]:
    payloads: list[dict[str, Any]] = []
    worker.signals.completed.connect(payloads.append)
    pool = QThreadPool()
    pool.setMaxThreadCount(1)
    pool.start(worker)
    _wait_until(
        app,
        lambda: len(payloads) == 1,
        description=description,
    )
    assert pool.waitForDone(5000)
    assert len(payloads) == 1
    return payloads[0]


def _prepare_tool(
    scene: Scene, canvas: QWidget, *, mode: str = "precise"
) -> MagneticLassoTool:
    settings = MagneticLassoSettings(mode=mode)
    tool = MagneticLassoTool(canvas, settings=settings)
    tool._compute_edge_map()
    assert tool._edge_map is not None
    assert tool._last_image_token == tool._current_image_token()
    return tool


def test_phase4_case_17_accepts_real_ndarray_and_qimage(native_scene_canvas) -> None:
    scene, canvas, image = native_scene_canvas
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings())

    array = tool._get_image_array()
    assert array is not None
    assert array.shape == image.shape
    assert array.dtype == np.uint8
    assert np.array_equal(array, image)

    qimage = qimage_from_array(image)
    scene.load_image(qimage, "fixture://legacy-phase4-qimage")
    converted = tool._get_image_array()
    assert converted is not None
    assert converted.shape == image.shape
    assert converted.dtype == np.uint8
    assert np.array_equal(converted, image)

    scene.load_image(object(), "fixture://legacy-phase4-invalid")
    assert tool._get_image_array() is None
    assert tool._last_error == "Unsupported scene image type: object"


def test_phase4_case_18_cache_hit_and_invalidation_are_observable(
    native_scene_canvas,
) -> None:
    scene, canvas, image = native_scene_canvas
    tool = _prepare_tool(scene, canvas)
    first_map = tool._edge_map
    first_hash = tool._last_image_hash
    assert first_map is not None
    assert first_hash

    tool._compute_edge_map()
    assert tool._edge_map is first_map
    assert tool._last_image_hash == first_hash

    image[30:40, 30:40] = 127
    tool._compute_edge_map()
    assert tool._edge_map is not first_map
    assert tool._last_image_hash != first_hash

    replacement = image.copy()
    scene.load_image(replacement, "fixture://legacy-phase4")
    tool._invalidate_stale_edge_cache()
    assert tool._edge_map is None
    tool._compute_edge_map()
    assert tool._edge_map is not None
    assert tool._last_image_token == tool._current_image_token()

    scene.load_image(None, "fixture://legacy-phase4-removed")
    tool._compute_edge_map()
    assert tool._edge_map is None
    assert tool._edge_features is None
    assert tool._edge_overlay_image is None


def test_phase4_case_19_worker_delivers_real_success_and_error(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    scene, canvas, image = native_scene_canvas
    tool = _prepare_tool(scene, canvas)
    settings = tool.settings.normalized()
    features = build_edge_features(image, sensitivity=settings.sensitivity)
    token = tool._current_image_token()

    worker = _MagneticPathWorker(
        101,
        0,
        "segment",
        "precise",
        features.strength,
        features,
        None,
        token,
        settings,
        (24, 24),
        (136, 24),
    )
    payload = _run_worker(qt_app, worker, description="successful magnetic worker")
    assert payload["error"] is None
    assert payload["commit_safe"] is True
    assert payload["path"]
    assert payload["path"][0] == (24, 24)
    assert payload["path"][-1] == (136, 24)
    assert payload["edge_map"] is features.strength

    invalid_image = np.zeros((20, 20, 2, 2), dtype=np.uint8)
    failed_worker = _MagneticPathWorker(
        102,
        0,
        "segment",
        "precise",
        None,
        None,
        invalid_image,
        token,
        settings,
        (1, 1),
        (2, 2),
    )
    failed = _run_worker(qt_app, failed_worker, description="magnetic worker error")
    assert failed["path"] == []
    assert failed["error"]
    assert "ValueError" in failed["error"]


def test_phase4_case_20_preview_is_delivered_by_real_qt_worker(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    scene, canvas, _ = native_scene_canvas
    tool = _prepare_tool(scene, canvas)
    tool._anchors = [(24, 24)]
    tool._path = [(24, 24)]
    event = mouse_event(
        QEvent.Type.MouseMove,
        136,
        24,
        button=Qt.MouseButton.NoButton,
        buttons=Qt.MouseButton.NoButton,
    )

    tool.on_mouse_move(event, (136, 24))
    assert tool._active_path_request is not None or tool._preview_path
    _wait_until(
        qt_app,
        lambda: bool(tool._preview_path) and tool._active_path_request is None,
        description="real preview delivery",
    )
    assert tool._preview_path_start == (24, 24)
    assert tool._preview_path_endpoint is not None
    assert tool._preview_path[0] == (24, 24)
    assert tool._preview_path[-1] == tool._preview_path_endpoint


def test_phase4_case_20_cancel_discards_pending_result_without_history(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    scene, canvas, _ = native_scene_canvas
    tool = _prepare_tool(scene, canvas)
    tool._anchors = [(24, 24)]
    tool._path = [(24, 24)]
    event = mouse_event(QEvent.Type.MouseButtonPress, 136, 24)

    tool.on_mouse_press(event, (136, 24))
    assert tool._segment_pending is True
    revision_before_cancel = tool._state_revision
    tool.cancel()
    assert tool._state_revision > revision_before_cancel
    assert tool._anchors == []
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0

    _wait_until(
        qt_app,
        lambda: tool._active_path_request is None and not tool._path_workers,
        description="cancelled worker disposal",
    )
    assert scene.objects == {}
    assert scene.cmd.undo_count == 0


def test_phase4_cases_19_20_stale_result_cannot_overwrite_new_preview(
    native_scene_canvas,
) -> None:
    scene, canvas, _ = native_scene_canvas
    tool = _prepare_tool(scene, canvas)
    tool._anchors = [(24, 24)]
    current = {
        "request_id": 201,
        "revision": tool._state_revision,
        "purpose": "preview",
        "start": (24, 24),
        "end": (136, 24),
        "path": [(24, 24), (80, 24), (136, 24)],
        "error": None,
        "commit_safe": False,
        "edge_map": tool._edge_map,
        "edge_features": tool._edge_features,
        "image_hash": tool._last_image_hash,
        "image_token": tool._current_image_token(),
        "edge_signature": tool._current_edge_signature(),
    }
    tool._on_async_path_result(current)
    assert tool._preview_path_endpoint == (136, 24)

    stale = dict(current)
    stale["request_id"] = 200
    stale["revision"] = tool._state_revision - 1
    stale["end"] = (24, 136)
    stale["path"] = [(24, 24), (24, 80), (24, 136)]
    tool._on_async_path_result(stale)
    assert tool._preview_path_endpoint == (136, 24)
    assert tool._preview_path == [(24, 24), (80, 24), (136, 24)]


def test_phase4_case_21_real_double_click_closes_and_invalid_path_stays_out(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    scene, canvas, _ = native_scene_canvas
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings(mode="legacy"))
    tool._anchors = [(24, 24), (136, 24), (136, 136)]
    tool._segments = [
        [(24, 24), (136, 24)],
        [(136, 24), (136, 136)],
    ]
    tool._rebuild_path()
    tool._preview_path = [(136, 136), (24, 136), (24, 24)]
    tool._preview_path_start = (136, 136)
    tool._preview_path_endpoint = (24, 24)
    tool.on_double_click(
        mouse_event(QEvent.Type.MouseButtonDblClick, 24, 24),
        (24, 24),
    )
    qt_app.processEvents()

    object_id = next(iter(scene.objects), None)
    assert object_id is not None
    assert object_id in scene.objects
    assert scene.cmd.undo_count == 1

    failed = MagneticLassoTool(canvas, settings=MagneticLassoSettings(mode="legacy"))
    before_ids = tuple(scene.objects)
    assert failed.commit_selection([(24, 24), (80, 24), (136, 24)]) is None
    assert tuple(scene.objects) == before_ids
    assert scene.cmd.undo_count == 1


def test_phase4_case_22_solver_is_fail_closed_without_image_and_works_with_edges(
    native_scene_canvas,
) -> None:
    scene, canvas, image = native_scene_canvas
    scene.load_image(None, "fixture://legacy-phase4-missing")
    missing = MagneticLassoTool(canvas, settings=MagneticLassoSettings())
    assert missing._compute_magnetic_path((24, 24), (136, 24)) == []
    assert missing._edge_map is None

    scene.load_image(image, "fixture://legacy-phase4-restored")


def test_phase4_case_27_end_to_end_real_image_worker_cache_scene_history(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    scene, canvas, _ = native_scene_canvas
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings(mode="legacy"))
    tool._compute_edge_map()
    assert tool._edge_map is not None
    first_map = tool._edge_map
    tool._compute_edge_map()
    assert tool._edge_map is first_map
    canvas.set_tool(tool)

    def add_anchor(x: int, y: int) -> None:
        tool.on_mouse_press(mouse_event(QEvent.Type.MouseButtonPress, x, y), (x, y))

    add_anchor(24, 24)
    assert tool._anchors == [(24, 24)]
    add_anchor(136, 24)
    _wait_until(
        qt_app,
        lambda: len(tool._anchors) == 2
        and tool._active_path_request is None
        and not tool._path_workers,
        description="first end-to-end segment",
    )
    add_anchor(136, 136)
    _wait_until(
        qt_app,
        lambda: len(tool._anchors) == 3
        and tool._active_path_request is None
        and not tool._path_workers,
        description="second end-to-end segment",
    )

    add_anchor(24, 24)
    _wait_until(
        qt_app,
        lambda: len(scene.objects) == 1
        and tool._active_path_request is None
        and not tool._path_workers,
        description="end-to-end close and commit",
    )
    object_id = next(iter(scene.objects))
    polygon = list(scene.objects[object_id].polygon)
    assert polygon
    assert scene.selected_id == object_id
    assert scene.cmd.undo_count == 1

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects == {}
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert object_id in scene.objects
    assert list(scene.objects[object_id].polygon) == polygon
    assert scene.selected_id == object_id


def test_phase4_characterize_late_preview_after_real_canvas_destruction(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    """Characterize the missing close-safe bridge before adding its fix."""

    scene, canvas, _ = native_scene_canvas
    tool = _prepare_tool(scene, canvas)
    tool._anchors = [(24, 24)]
    request_id = 901
    tool._active_path_request = request_id
    payload = {
        "request_id": request_id,
        "revision": tool._state_revision,
        "purpose": "preview",
        "start": (24, 24),
        "end": (136, 24),
        "path": [(24, 24), (80, 24), (136, 24)],
        "error": None,
        "commit_safe": False,
        "edge_map": tool._edge_map,
        "edge_features": tool._edge_features,
        "image_hash": tool._last_image_hash,
        "image_token": tool._current_image_token(),
        "edge_signature": tool._current_edge_signature(),
    }

    canvas.deleteLater()
    qt_app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not shiboken6.isValid(canvas)
    before_objects = tuple(scene.objects)
    before_history = scene.cmd.undo_count
    tool._on_async_path_result(payload)
    assert tool._canvas_closed is True
    assert tuple(scene.objects) == before_objects
    assert scene.cmd.undo_count == before_history
    assert tool._preview_path == []


def test_phase4_real_segment_timeout_cancels_and_discards_late_result(
    qt_app: QApplication,
    native_scene_canvas,
) -> None:
    scene, canvas, _ = native_scene_canvas
    image = _large_phase4_image()
    scene.load_image(image, "fixture://legacy-phase4-timeout")
    settings = MagneticLassoSettings(
        mode="precise",
        segment_timeout_ms=50,
    )
    tool = MagneticLassoTool(canvas, settings=settings)
    tool._anchors = [(128, 128)]
    tool._preview_path = [(128, 128), (200, 128)]
    canvas.set_tool(tool)

    before_objects = tuple(scene.objects)
    before_history = scene.cmd.undo_count
    revision_before = tool._state_revision
    tool._request_async_path("segment", (128, 128), (896, 128))
    request_id = tool._active_path_request
    assert request_id is not None
    worker = tool._path_workers[request_id]
    payloads: list[dict[str, Any]] = []
    worker.signals.completed.connect(payloads.append)

    _wait_until(
        qt_app,
        lambda: (
            tool._active_path_request is None
            and not tool._segment_pending
            and tool._last_error == "segment: Timeout after 50 ms"
        ),
        timeout_ms=2000,
        description="real segment timeout",
    )
    assert tool._state_revision > revision_before
    assert worker._cancel_event.is_set()
    assert tool._path_busy is False
    assert tool._anchors == [(128, 128)]
    assert tool._preview_path == [(128, 128), (200, 128)]
    assert tuple(scene.objects) == before_objects
    assert scene.cmd.undo_count == before_history

    _wait_until(
        qt_app,
        lambda: not tool._path_workers,
        timeout_ms=10000,
        description="cooperative cancellation and late response disposal",
    )
    assert len(payloads) == 1
    assert payloads[0]["cancelled"] is True
    assert float(payloads[0]["elapsed_ms"]) >= settings.segment_timeout_ms
    assert tool._anchors == [(128, 128)]
    assert tool._preview_path == [(128, 128), (200, 128)]
    assert tuple(scene.objects) == before_objects
    assert scene.cmd.undo_count == before_history
