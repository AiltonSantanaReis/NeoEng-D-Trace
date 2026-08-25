from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.viewport_state import ViewportState


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_viewport_state_is_structured_and_complete(qt_app):
    canvas = CanvasView(Scene())
    try:
        state = canvas.viewport_state()
        assert isinstance(state, ViewportState)
        assert state.view_mode == "LIT"
        assert state.zoom == pytest.approx(1.0)
        assert state.snap_enabled is False
        assert state.snap_grid_size == 1
        assert state.grid_visible is True
        assert state.gizmo_enabled is False
        assert state.pan_x == pytest.approx(0.0)
        assert state.pan_y == pytest.approx(0.0)
        assert state.selection_ids == ()
        assert state.selection_count == 0
        assert (state.cursor_x, state.cursor_y) == (0, 0)
    finally:
        canvas.close()


def test_structured_signal_tracks_zoom_view_snap_grid_and_cursor(qt_app, monkeypatch):
    canvas = CanvasView(Scene())
    states: list[ViewportState] = []
    canvas.viewport_state_model_changed.connect(states.append)
    try:
        canvas.set_zoom(1.5)
        assert states[-1].zoom == pytest.approx(1.5)

        monkeypatch.setattr(canvas, "update", lambda: None)
        canvas.set_view_mode(canvas.VIEW_XRAY_2)
        assert states[-1].view_mode == "X-RAY 2"

        canvas.set_vertex_snapping(True, grid_size=16)
        assert states[-1].snap_enabled is True
        assert states[-1].snap_grid_size == 16

        canvas.set_grid_visible(False)
        assert states[-1].grid_visible is False

        cursor_position = QPointF(42.0, 24.0)
        expected_cursor = canvas.widget_to_image(cursor_position)
        canvas._update_cursor_position(cursor_position)
        assert (states[-1].cursor_x, states[-1].cursor_y) == expected_cursor
    finally:
        canvas.close()


def test_legacy_text_signal_is_adapter_not_canonical_contract(qt_app):
    canvas = CanvasView(Scene())
    legacy_events: list[str] = []
    canvas.viewport_state_changed.connect(legacy_events.append)
    try:
        canvas.set_zoom(2.0)
        assert legacy_events
        assert isinstance(legacy_events[-1], str)
        assert canvas.viewport_state().zoom == pytest.approx(2.0)
    finally:
        canvas.close()
