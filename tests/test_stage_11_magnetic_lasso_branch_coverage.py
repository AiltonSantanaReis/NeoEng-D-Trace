"""Stage 11 branch contracts for the magnetic lasso UI adapter."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

import src.tools.magnetic_lasso as magnetic_module
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.tools.magnetic_lasso import MagneticLassoTool, _MagneticPathWorker
from src.tools.magnetic_lasso_engine import MagneticLassoSettings, build_edge_features


class _Canvas:
    def __init__(self, image=None):
        self.model = Scene()
        self.model.cmd = CommandManager()
        self.model.image = image
        self.scene = self.model
        self.updates = 0
        self.focus_reasons = []
        self._zoom = 1.0

    def update(self):
        self.updates += 1

    def setFocus(self, reason):
        self.focus_reasons.append(reason)

    def get_zoom(self):
        return self._zoom

    def get_transform(self):
        return QTransform()


class _Event:
    def __init__(self, *, button=None, key=None):
        self._button = button
        self._key = key

    def button(self):
        return self._button

    def key(self):
        return self._key

    def globalPos(self):
        return QPoint(0, 0)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def quiet_messages(monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)


def _tool(*, mode="legacy", image=None) -> MagneticLassoTool:
    settings = MagneticLassoSettings(mode=mode)
    return MagneticLassoTool(_Canvas(image), settings)


def _worker_payload(worker: _MagneticPathWorker) -> dict:
    payloads = []
    worker.signals.completed.connect(payloads.append)
    worker.run()
    assert len(payloads) == 1
    return payloads[0]


def test_legacy_pathfinder_and_workers_cover_all_solver_modes(monkeypatch) -> None:
    edge_map = np.zeros((5, 5), dtype=np.uint8)
    path = magnetic_module.dijkstra_pathfinding(edge_map, (0, 0), (4, 4))
    assert path[0] == (0, 0) and path[-1] == (4, 4)
    assert magnetic_module.sobel_edge_detection(edge_map).shape == edge_map.shape

    settings = MagneticLassoSettings(mode="legacy")
    legacy = _MagneticPathWorker(
        1,
        0,
        "segment",
        "legacy",
        edge_map,
        None,
        None,
        "token",
        settings,
        (0, 0),
        (2, 2),
    )
    payload = _worker_payload(legacy)
    assert payload["path"][0] == (0, 0) and payload["commit_safe"] is True

    image = np.zeros((8, 8), dtype=np.uint8)
    prepare = _MagneticPathWorker(
        2, 0, "prepare", "precise", None, None, image, "token", settings, (0, 0), (0, 0)
    )
    payload = _worker_payload(prepare)
    assert payload["path"] == [] and payload["edge_features"] is not None

    features = build_edge_features(image)
    monkeypatch.setattr(
        magnetic_module,
        "live_wire_preview_path",
        lambda *args, **kwargs: [(1, 1), (2, 2)],
    )
    preview = _MagneticPathWorker(
        3,
        0,
        "preview",
        "precise",
        features.strength,
        features,
        None,
        "token",
        settings,
        (1, 1),
        (2, 2),
    )
    payload = _worker_payload(preview)
    assert payload["path"] == [(1, 1), (2, 2)] and payload["commit_safe"] is False

    monkeypatch.setattr(
        magnetic_module,
        "dijkstra_pathfinding",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("solver failed")),
    )
    failed = _MagneticPathWorker(
        4,
        0,
        "segment",
        "legacy",
        edge_map,
        None,
        None,
        "token",
        settings,
        (0, 0),
        (1, 1),
    )
    assert "solver failed" in _worker_payload(failed)["error"]


def test_image_tokens_arrays_cache_and_edge_overlay(qt_app) -> None:
    empty = np.empty((0, 0), dtype=np.uint8)
    image = np.arange(64, dtype=np.uint8).reshape(8, 8)
    qimage = QImage(4, 3, QImage.Format.Format_Grayscale8)
    qimage.fill(7)
    assert MagneticLassoTool._image_token(None) is None
    assert MagneticLassoTool._image_token(empty)[0] == "numpy"
    assert MagneticLassoTool._image_token(image)[0] == "numpy"
    assert MagneticLassoTool._image_token(qimage)[0] == "qimage"
    assert MagneticLassoTool._image_token(object())[0] == "other"

    no_image = _tool()
    assert no_image._get_image_array() is None
    no_image.canvas_view.model.image = object()
    assert no_image._get_image_array() is None
    assert "Unsupported scene image type" in no_image._last_error
    no_image.canvas_view.model.image = np.zeros((2, 2, 2, 2), dtype=np.uint8)
    assert no_image._get_image_array() is None
    assert "Unsupported numpy image" in no_image._last_error

    qtool = _tool(image=qimage)
    converted = qtool._get_image_array()
    assert converted.shape == (3, 4)

    precise = _tool(mode="precise", image=image)
    precise._compute_edge_map()
    assert (
        precise._edge_features is not None and precise._edge_overlay_image is not None
    )
    cached = precise._edge_map
    precise._compute_edge_map()
    assert precise._edge_map is cached
    precise.canvas_view.model.image = image.copy()
    precise._invalidate_stale_edge_cache()
    assert precise._edge_map is None

    legacy = _tool(image=image)
    legacy._compute_edge_map()
    assert legacy._edge_features is None and legacy._edge_map is not None
    assert MagneticLassoTool._make_edge_overlay(None) is None
    assert (
        MagneticLassoTool._make_edge_overlay(np.zeros((0, 0), dtype=np.uint8)) is None
    )
    assert (
        MagneticLassoTool._make_edge_overlay(np.zeros((2, 2, 2), dtype=np.uint8))
        is None
    )


def test_snapping_and_synchronous_path_branches(monkeypatch) -> None:
    legacy = _tool()
    assert legacy._snap_anchor((1.4, 2.6)) == (1, 3)
    legacy._edge_map = np.zeros((5, 5), dtype=np.uint8)
    assert legacy._compute_magnetic_path((-3, -2), (99, 99))[0] == (0, 0)
    assert legacy._compute_magnetic_path((2, 2), (2, 2)) == [(2, 2)]

    no_image = _tool(mode="precise")
    assert no_image._snap_anchor((2.2, 3.8)) == (2, 4)
    assert no_image._compute_magnetic_path((0, 0), (2, 2)) == []

    precise = _tool(mode="precise", image=np.zeros((7, 7), dtype=np.uint8))
    precise._compute_edge_map()
    monkeypatch.setattr(magnetic_module, "snap_to_edge", lambda *args, **kwargs: (4, 5))
    monkeypatch.setattr(
        magnetic_module, "live_wire_path", lambda *args: [(0, 0), (3, 3)]
    )
    assert precise._snap_anchor((3, 3)) == (4, 5)
    assert precise._compute_magnetic_path((0, 0), (3, 3)) == [(0, 0), (3, 3)]
    precise._edge_features = None
    precise.canvas_view.model.image = None
    assert precise._compute_magnetic_path((0, 0), (3, 3)) == []


def test_async_queue_start_and_next_request_branches(monkeypatch) -> None:
    tool = _tool(mode="precise", image=np.zeros((4, 4), dtype=np.uint8))
    started = []
    monkeypatch.setattr(tool, "_start_async_path", started.append)
    tool._request_async_path("preview", (0, 0), (1, 1))
    assert started[-1]["purpose"] == "preview"

    tool._active_path_request = 1
    tool._request_async_path("preview", (0, 0), (2, 2))
    assert tool._queued_preview_request["end"] == (2, 2)
    tool._request_async_path("segment", (0, 0), (3, 3))
    assert tool._queued_action_request["purpose"] == "segment"
    assert tool._queued_preview_request is None and tool._segment_pending is True
    tool._request_async_path("preview", (0, 0), (1, 1))
    assert tool._queued_preview_request is None
    tool._request_async_path("prepare", (0, 0), (0, 0))

    tool._active_path_request = None
    tool._queued_action_request = None
    tool._queued_preview_request = {
        "revision": tool._state_revision,
        "purpose": "preview",
    }
    tool._start_next_async_path()
    assert started[-1]["purpose"] == "preview"
    tool._queued_preview_request = {"revision": -1, "purpose": "preview"}
    tool._segment_pending = True
    tool._start_next_async_path()
    assert tool._segment_pending is False

    original_start = MagneticLassoTool._start_async_path.__get__(tool)
    monkeypatch.setattr(tool, "_start_async_path", original_start)
    tool._path_pool = SimpleNamespace(start=lambda worker: started.append(worker))
    stale = {"revision": -1, "purpose": "prepare", "start": (0, 0), "end": (0, 0)}
    tool._start_async_path(stale)
    assert not isinstance(started[-1], _MagneticPathWorker)
    request = {
        "revision": tool._state_revision,
        "purpose": "preview",
        "start": (0, 0),
        "end": (1, 1),
    }
    tool._start_async_path(request)
    assert isinstance(started[-1], _MagneticPathWorker)


def _payload(tool, purpose, **changes):
    payload = {
        "request_id": 1,
        "revision": tool._state_revision,
        "purpose": purpose,
        "start": (0, 0),
        "end": (2, 2),
        "path": [(0, 0), (1, 1), (2, 2)],
        "error": None,
        "commit_safe": True,
        "edge_map": np.zeros((3, 3), dtype=np.uint8),
        "edge_features": None,
        "image_hash": "hash",
        "image_token": tool._current_image_token(),
        "edge_signature": tool._current_edge_signature(),
    }
    payload.update(changes)
    return payload


def test_async_result_prepare_preview_segment_finish_and_failures(monkeypatch) -> None:
    tool = _tool(image=np.zeros((3, 3), dtype=np.uint8))
    monkeypatch.setattr(tool, "_start_next_async_path", lambda: None)
    tool._active_path_request = 1
    tool._path_workers[1] = object()
    tool._on_async_path_result(_payload(tool, "prepare"))
    assert tool._active_path_request is None and tool._edge_map is not None

    tool._anchors = [(0, 0)]
    tool._on_async_path_result(_payload(tool, "preview"))
    assert tool._preview_path_endpoint == (2, 2)
    tool._on_async_path_result(_payload(tool, "preview", start=(9, 9)))

    tool._segment_pending = True
    tool._on_async_path_result(_payload(tool, "segment"))
    assert tool._anchors[-1] == (2, 2) and tool._segment_pending is False
    failures = []
    monkeypatch.setattr(
        tool, "_handle_async_failure", lambda *args: failures.append(args)
    )
    tool._on_async_path_result(_payload(tool, "segment", path=[]))
    assert failures[-1][0] == "segment"

    finished = []
    monkeypatch.setattr(
        tool, "_finish_with_closing_path", lambda path: finished.append(path)
    )
    tool._on_async_path_result(_payload(tool, "finish"))
    assert finished
    tool._on_async_path_result(_payload(tool, "finish", path=[]))
    assert failures[-1][0] == "finish"
    tool._on_async_path_result(_payload(tool, "segment", error="boom"))
    assert tool._last_error == "boom"

    queued = {
        "revision": tool._state_revision,
        "purpose": "segment",
        "start": (0, 0),
        "end": (2, 2),
    }
    tool._queued_action_request = queued
    tool._anchors = [(0, 0)]
    tool._on_async_path_result(_payload(tool, "preview"))
    assert tool._anchors[-1] == (2, 2)

    stale_starts = []
    monkeypatch.setattr(
        tool, "_start_next_async_path", lambda: stale_starts.append(True)
    )
    tool._on_async_path_result(_payload(tool, "prepare", revision=-1))
    tool._on_async_path_result(_payload(tool, "prepare", image_token="stale"))
    assert len(stale_starts) == 2


def test_anchor_history_rebuild_and_close_detection(monkeypatch) -> None:
    tool = _tool()
    tool._rebuild_path()
    assert tool._path == [] and tool.remove_last_anchor() is False
    assert tool.restore_last_anchor() is False
    assert tool._append_anchor((0, 0)) is True
    assert tool._append_anchor((0, 0)) is False
    monkeypatch.setattr(tool, "_compute_magnetic_path", lambda *args: [])
    assert tool._append_anchor((2, 0)) is False
    assert tool._append_anchor((2, 0), [(0, 0), (1, 0), (2, 0)]) is True
    assert tool._append_anchor((2, 2), [(9, 9), (2, 2)]) is True
    assert tool._path[-1] == (2, 2)
    assert tool._can_close_at((0, 0)) is True

    assert tool.remove_last_anchor() is True
    assert tool.restore_last_anchor() is True
    assert tool.remove_last_anchor() is True
    tool._redo_anchor_stack[-1] = (tool._redo_anchor_stack[-1][0], None)
    monkeypatch.setattr(tool, "_compute_magnetic_path", lambda *args: [])
    assert tool.restore_last_anchor() is False
    monkeypatch.setattr(tool, "_compute_magnetic_path", lambda *args: [(2, 0), (2, 2)])
    assert tool.restore_last_anchor() is True
    tool._reset_selection_state()
    assert not tool._anchors and not tool._redo_anchor_stack


def test_mouse_key_and_history_event_branches(monkeypatch) -> None:
    tool = _tool()
    left = _Event(button=Qt.MouseButton.LeftButton)
    right = _Event(button=Qt.MouseButton.RightButton)
    tool._segment_pending = True
    tool.on_mouse_press(left, (1, 1))
    tool._segment_pending = False
    tool.on_mouse_press(left, (1, 1))
    assert tool._anchors == [(1, 1)]
    monkeypatch.setattr(tool, "_compute_magnetic_path", lambda *args: [(1, 1), (2, 2)])
    tool.on_mouse_press(left, (2, 2))
    assert tool._anchors[-1] == (2, 2)
    context = []
    monkeypatch.setattr(tool, "show_context_menu", lambda event: context.append(event))
    tool.on_mouse_press(right, (0, 0))
    assert context == [right]

    tool.on_mouse_move(left, (3, 3))
    assert tool._preview_path_endpoint == (3, 3)
    tool.on_mouse_move(left, (3, 3))
    tool._segment_pending = True
    tool.on_mouse_move(left, (4, 4))
    tool._segment_pending = False
    tool.on_mouse_release(left, (0, 0))

    actions = []
    monkeypatch.setattr(tool, "cancel", lambda: actions.append("cancel"))
    monkeypatch.setattr(
        tool, "remove_last_anchor", lambda: actions.append("remove") or True
    )
    monkeypatch.setattr(tool, "finish_selection", lambda: actions.append("finish"))
    assert tool.on_key_press(_Event(key=Qt.Key.Key_Escape)) is True
    assert tool.on_key_press(_Event(key=Qt.Key.Key_Delete)) is True
    tool._anchors = [(0, 0), (2, 0), (0, 2)]
    assert tool.on_key_press(_Event(key=Qt.Key.Key_Return)) is True
    assert tool.on_key_press(_Event(key=Qt.Key.Key_A)) is False
    tool.on_double_click(left, (0, 0))
    assert "finish" in actions


def test_candidate_finish_commit_success_and_validation_failures(monkeypatch) -> None:
    tool = _tool()
    assert tool._candidate_closed_path() == []
    tool._anchors = [(0, 0), (4, 0), (0, 4)]
    tool._path = [(0, 0), (4, 0), (0, 4)]
    monkeypatch.setattr(tool, "_compute_magnetic_path", lambda *args: [])
    assert tool._candidate_closed_path() == []
    candidate = tool._candidate_closed_path([(9, 9), (0, 0)])
    assert candidate[-1] == (9, 9)

    object_id = tool._finish_with_closing_path([(0, 4), (0, 0)])
    assert object_id in tool.canvas_view.model.objects
    assert tool._anchors == []

    assert tool.commit_selection([(0, 0), (1, 0)]) is None
    monkeypatch.setattr(
        magnetic_module, "polygon_self_intersects", lambda polygon: True
    )
    assert tool.commit_selection([(0, 0), (4, 0), (0, 4)]) is None
    assert tool._last_error == "Polygon self-intersects"
    monkeypatch.setattr(
        magnetic_module, "polygon_self_intersects", lambda polygon: False
    )
    monkeypatch.setattr(
        tool,
        "commit_polygon_command",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("commit failed")),
    )
    assert tool.commit_selection([(0, 0), (4, 0), (0, 4)]) is None
    assert "commit failed" in tool._last_error

    shown = []
    monkeypatch.setattr(tool, "_show_invalid_selection", lambda: shown.append(True))
    tool._anchors = [(0, 0), (1, 0), (2, 0)]
    tool._path = list(tool._anchors)
    monkeypatch.setattr(tool, "_candidate_closed_path", lambda *args: [])
    assert tool.finish_selection() is None and shown


def test_modes_presets_overlay_drawing_and_project_history(qt_app, monkeypatch) -> None:
    tool = _tool(mode="precise", image=np.zeros((8, 8), dtype=np.uint8))
    tool._anchors = [(1, 1), (6, 1), (1, 6)]
    tool._path = [(1, 1), (6, 1), (1, 6)]
    tool._preview_path = [(1, 6), (1, 1)]
    tool._hover_can_close = True
    tool.settings.show_edge_map = True
    image = QImage(10, 10, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    tool.draw_overlay(painter)
    painter.end()
    assert tool._edge_overlay_image is not None

    tool._set_mode("invalid")
    tool._set_mode("precise")
    tool._set_mode("legacy")
    assert tool.settings.mode == "legacy" and tool._anchors == []
    tool._set_preset(tool.settings.preset)
    tool._anchors = [(0, 0)]
    tool._set_preset("fast")
    assert tool.settings.preset == "fast" and tool._anchors == []

    prepared = []
    monkeypatch.setattr(tool, "prepare_edge_map_async", lambda: prepared.append(True))
    tool._toggle_edge_overlay(True)
    tool._toggle_edge_overlay(False)
    assert prepared == [True]

    history = []
    tool.canvas_view.model.cmd = SimpleNamespace(
        undo=lambda model: history.append("undo"),
        redo=lambda model: history.append("redo"),
    )
    tool._undo_project()
    tool._redo_project()
    monkeypatch.setattr(tool, "on_undo", lambda: False)
    monkeypatch.setattr(tool, "on_redo", lambda: False)
    tool.undo_last_action()
    tool.redo_last_action()
    assert history == ["undo", "redo", "undo", "redo"]
    tool.update_language("pt")
    tool.update_language("unsupported")
    assert tool.current_lang == "pt"


def test_real_widget_background_cursor_prepare_and_event_paths(
    qt_app, monkeypatch
) -> None:
    class _WidgetCanvas(QWidget):
        def __init__(self):
            super().__init__()
            self.model = Scene()
            self.model.cmd = CommandManager()
            self.model.image = np.zeros((8, 8), dtype=np.uint8)
            self.scene = self.model
            self.updates = 0

        def update(self):
            self.updates += 1

        def get_zoom(self):
            return 1.0

        def get_transform(self):
            return QTransform()

    canvas = _WidgetCanvas()
    tool = MagneticLassoTool(canvas, MagneticLassoSettings(mode="legacy"))
    assert tool._uses_background_pathfinding() is True
    tool._set_path_busy(True)
    tool._set_path_busy(True)
    assert tool._path_busy is True
    tool._set_path_busy(False)
    assert tool._path_busy is False

    requests = []
    monkeypatch.setattr(
        tool, "_request_async_path", lambda *args: requests.append(args)
    )
    tool.prepare_edge_map_async()
    assert requests[-1][0] == "prepare"
    tool._edge_map = np.zeros((8, 8), dtype=np.uint8)
    before = len(requests)
    tool.prepare_edge_map_async()
    assert len(requests) == before

    tool._edge_map = None
    assert tool._snap_anchor((2.4, 3.6)) == (2, 4)
    assert requests[-1][0] == "prepare"

    left = _Event(button=Qt.MouseButton.LeftButton)
    tool._anchors = [(0, 0)]
    tool._preview_path = [(0, 0), (2, 2)]
    tool._preview_path_start = (0, 0)
    tool._preview_path_endpoint = (2, 2)
    monkeypatch.setattr(tool, "_snap_anchor", lambda point: (2, 2))
    tool.on_mouse_press(left, (2, 2))
    assert tool._anchors[-1] == (2, 2) and tool._preview_path == []

    tool._anchors = [(0, 0)]
    tool.on_mouse_press(left, (3, 3))
    assert requests[-1][0] == "segment" and tool._segment_pending is True
    tool._segment_pending = False
    tool._anchors = [(0, 0)]
    tool._preview_path = []
    tool.on_mouse_move(left, (4, 4))
    assert requests[-1][0] == "preview"

    tool._anchors = [(0, 0), (4, 0), (0, 4)]
    tool._preview_path = [(0, 4), (0, 0)]
    tool._preview_path_start = (0, 4)
    tool._preview_path_endpoint = (0, 0)
    finished = []
    monkeypatch.setattr(
        tool, "_finish_with_closing_path", lambda path: finished.append(path)
    )
    tool.finish_selection()
    assert finished

    tool.settings.mode = "precise"
    tool._segment_pending = False
    tool._preview_path = []
    tool.finish_selection()
    assert requests[-1][0] == "finish"
    canvas.close()


def test_context_menu_builds_all_actions_without_modal_execution(monkeypatch) -> None:
    class _Signal:
        def connect(self, callback):
            self.callback = callback

    class _Action:
        def __init__(self):
            self.triggered = _Signal()
            self.toggled = _Signal()

        def setEnabled(self, value):
            self.enabled = value

        def setCheckable(self, value):
            self.checkable = value

        def setChecked(self, value):
            self.checked = value

    class _Menu:
        def __init__(self, parent=None):
            self.actions = []

        def setStyleSheet(self, value):
            self.style = value

        def addAction(self, text):
            action = _Action()
            self.actions.append(action)
            return action

        def addMenu(self, text):
            return _Menu()

        def addSeparator(self):
            return None

        def exec(self, position):
            self.position = position

    class _Group:
        def __init__(self, parent):
            self.actions = []

        def setExclusive(self, value):
            self.exclusive = value

        def addAction(self, action):
            self.actions.append(action)

    monkeypatch.setattr(magnetic_module, "QMenu", _Menu)
    monkeypatch.setattr(magnetic_module, "QActionGroup", _Group)
    tool = _tool(mode="precise")
    tool._anchors = [(0, 0), (2, 0), (0, 2)]
    tool._path = list(tool._anchors)
    tool.show_context_menu(_Event(button=Qt.MouseButton.RightButton))

    tool._anchors = []
    tool._path = []
    tool.show_context_menu(_Event(button=Qt.MouseButton.RightButton))


def test_async_failure_warning_exception_and_empty_rebuild_segment(monkeypatch) -> None:
    tool = _tool()
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("headless")),
    )
    tool._handle_async_failure("segment", "failed")
    assert "failed" in tool._last_error
    tool._handle_async_failure("preview", "failed")

    tool._anchors = [(0, 0)]
    tool._segments = [[]]
    tool._rebuild_path()
    assert tool._path == [(0, 0)]
    tool._segments = [[(1, 1), (2, 2)]]
    tool._rebuild_path()
    assert tool._path[-1] == (2, 2)
