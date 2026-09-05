"""Pen creation through Qt events; not an OS-native packaged-build audit."""

from __future__ import annotations

import copy

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.polygon_validation import is_valid_polygon
from src.exporters.sprite_exporter import export_sprite
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _Config:
    def get(self, key, default=None):
        return default

    def set(self, key, value):
        pass

    def save(self):
        pass


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qt_app, tmp_path):
    pixels = np.full((320, 400, 4), 255, dtype=np.uint8)
    source = tmp_path / "pen-input.png"
    Image.fromarray(pixels).save(source)
    scene = Scene()
    scene.cmd = CommandManager()
    scene.image = pixels
    scene.image_path = str(source)
    current = MainWindow(scene, _Config())
    current.resize(1280, 900)
    current._refresh_document_views(project_loaded=False)
    current.show()
    current.activateWindow()
    qt_app.processEvents()
    QTest.qWait(30)
    current.canvas._zoom = 1.0
    current.canvas._pan = QPointF(40, 40)
    QTest.mouseClick(current.tool_palette.btn_pen, Qt.MouseButton.LeftButton)
    current.canvas.setFocus()
    qt_app.processEvents()
    try:
        yield current
    finally:
        current._mark_document_clean()
        current.close()
        current.deleteLater()
        qt_app.processEvents()


def _point(window, point):
    converted = window.canvas.image_to_widget(*point)
    position = QPoint(round(converted.x()), round(converted.y()))
    assert window.canvas.rect().contains(position)
    return position


def _click(window, point):
    QTest.mouseClick(
        window.canvas, Qt.MouseButton.LeftButton, pos=_point(window, point)
    )
    QApplication.processEvents()


def _drag(window, start, end):
    QTest.mousePress(
        window.canvas, Qt.MouseButton.LeftButton, pos=_point(window, start)
    )
    QTest.mouseMove(window.canvas, _point(window, end))
    QTest.mouseRelease(
        window.canvas, Qt.MouseButton.LeftButton, pos=_point(window, end)
    )
    QApplication.processEvents()


def _tool(window):
    return window.canvas._active_tool_object()


@pytest.mark.parametrize("size", [20, 40, 60, 80, 100])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("zoom", [0.75, 1.0, 2.0])
def test_corner_clicks_close_across_size_winding_and_zoom(window, size, reverse, zoom):
    window.canvas._zoom = zoom
    points = [(80, 60), (80 + size, 60), (80 + size, 60 + size)]
    if reverse:
        points = [points[0], points[2], points[1]]
    for point in points:
        _click(window, point)
    assert not window.scene.objects
    assert window.scene.cmd.undo_count == 0
    _click(window, points[0])
    assert len(window.scene.objects) == 1, _tool(window)._last_error
    obj = next(iter(window.scene.objects.values()))
    assert is_valid_polygon(obj.polygon)
    assert obj.beziers[-1][3] == obj.beziers[0][0]
    assert all(
        segment[0] == segment[1] and segment[2] == segment[3] for segment in obj.beziers
    )
    assert window.scene.cmd.undo_count == 1
    snapshot = (copy.deepcopy(obj.beziers), copy.deepcopy(obj.polygon))
    QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    assert not window.scene.objects and window.scene.cmd.redo_count == 1
    QTest.keyClick(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    restored = next(iter(window.scene.objects.values()))
    assert (restored.beziers, restored.polygon) == snapshot


def test_drag_creates_explicit_handles_and_next_click_preserves_them(window, tmp_path):
    _click(window, (80, 80))
    _drag(window, (200, 80), (200, 110))
    node = _tool(window)._nodes[-1]
    assert node.handle_out == pytest.approx((200, 110))
    assert node.handle_in == pytest.approx((200, 50))
    handles = (node.handle_in, node.handle_out)
    _click(window, (200, 200))
    assert (node.handle_in, node.handle_out) == handles
    assert _tool(window)._nodes[-1].handle_in == _tool(window)._nodes[-1].anchor
    _click(window, (80, 200))
    _click(window, (80, 80))
    assert len(window.scene.objects) == 1, _tool(window)._last_error
    assert window.scene.cmd.undo_count == 1
    obj = next(iter(window.scene.objects.values()))
    assert obj.beziers[0][2] == handles[0]
    assert obj.beziers[1][1] == handles[1]
    assert is_valid_polygon(obj.polygon)
    original = (copy.deepcopy(obj.beziers), copy.deepcopy(obj.polygon))
    project = tmp_path / "pen-roundtrip.ndtproj"
    window._project_path = project
    window.save_project_action.trigger()
    QApplication.processEvents()
    assert project.is_file()
    loaded = Scene()
    loaded.load_project(str(project))
    loaded.attach_project_image(np.full((320, 400, 4), 255, dtype=np.uint8))
    restored = next(iter(loaded.objects.values()))
    assert (restored.beziers, restored.polygon) == original
    sprite_path = tmp_path / "pen-roundtrip.png"
    sprite = export_sprite(restored.id, loaded, str(sprite_path))
    with Image.open(sprite_path) as reopened:
        assert reopened.mode == "RGBA" and reopened.size == sprite.size
        assert reopened.tobytes() == sprite.tobytes()
        assert reopened.getchannel("A").getextrema() == (0, 255)
        assert min(reopened.size) > 100
    assert (restored.beziers, restored.polygon) == original


def test_releasing_drag_stops_handle_motion_and_switch_cancels_preview(window):
    _drag(window, (120, 120), (160, 120))
    tool = _tool(window)
    node = tool._nodes[0]
    handles = (node.handle_in, node.handle_out)
    assert handles == ((80.0, 120.0), (160.0, 120.0))
    QTest.mouseMove(window.canvas, _point(window, (200, 160)))
    QApplication.processEvents()
    assert (node.handle_in, node.handle_out) == handles
    assert not window.scene.objects and window.scene.cmd.undo_count == 0
    QTest.mouseClick(window.tool_palette.btn_rect, Qt.MouseButton.LeftButton)
    QApplication.processEvents()
    assert tool._nodes == [] and not tool._is_placing_handle
    assert not window.scene.objects and window.scene.cmd.undo_count == 0


@pytest.mark.parametrize(
    "points",
    [
        [(60, 60), (140, 60), (220, 60)],
        [(60, 60), (200, 200), (60, 200), (200, 60)],
        [(60, 60), (200, 60), (120, 60), (200, 200), (60, 200)],
    ],
)
def test_real_invalid_paths_still_reject_without_state_or_history_mutation(
    window, points
):
    for point in points:
        _click(window, point)
    tool = _tool(window)
    before = [(node.anchor, node.handle_in, node.handle_out) for node in tool._nodes]
    _click(window, points[0])
    assert not window.scene.objects
    assert window.scene.cmd.undo_count == 0 and window.scene.cmd.redo_count == 0
    assert [
        (node.anchor, node.handle_in, node.handle_out) for node in tool._nodes
    ] == before
    assert tool._editing_object_id is None
    assert "P2D05" in tool._last_error
    assert window.statusBar().currentMessage()


def test_double_click_finishes_a_small_valid_path_only_once(window):
    for point in [(80, 80), (120, 80), (120, 120)]:
        _click(window, point)
    QTest.mouseDClick(
        window.canvas, Qt.MouseButton.LeftButton, pos=_point(window, (120, 120))
    )
    QApplication.processEvents()
    assert len(window.scene.objects) == 1, _tool(window)._last_error
    assert window.scene.cmd.undo_count == 1
    assert is_valid_polygon(next(iter(window.scene.objects.values())).polygon)


@pytest.mark.parametrize("zoom", [0.75, 1.0, 2.0])
@pytest.mark.parametrize("screen_delta", [2, 5])
def test_drag_threshold_is_measured_in_screen_pixels(window, zoom, screen_delta):
    window.canvas._zoom = zoom
    start = _point(window, (100, 100))
    end = start + QPoint(screen_delta, 0)
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=start)
    # The release coordinate must work even if Qt coalesces every move event.
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=end)
    QApplication.processEvents()
    node = _tool(window)._nodes[0]
    if screen_delta < 3:
        assert node.handle_in == node.anchor and node.handle_out == node.anchor
    else:
        assert node.handle_out != node.anchor
        assert node.handle_in == pytest.approx(
            (
                2 * node.anchor[0] - node.handle_out[0],
                2 * node.anchor[1] - node.handle_out[1],
            )
        )
        assert (
            np.hypot(
                node.handle_out[0] - node.anchor[0],
                node.handle_out[1] - node.anchor[1],
            )
            * zoom
            >= 3.0
        )
    assert not _tool(window)._is_placing_handle


def test_escape_during_drag_cancels_preview_before_release(window):
    start = _point(window, (120, 120))
    end = _point(window, (160, 120))
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window.canvas, end)
    QApplication.processEvents()
    tool = _tool(window)
    assert tool._nodes[0].handle_out == (160, 120)
    assert not window.scene.objects and window.scene.cmd.undo_count == 0
    QTest.keyClick(window.canvas, Qt.Key.Key_Escape)
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=end)
    QTest.mouseMove(window.canvas, _point(window, (200, 160)))
    QApplication.processEvents()
    assert not tool._nodes and not tool._is_placing_handle
    assert not window.scene.objects and window.scene.cmd.undo_count == 0


@pytest.mark.parametrize("key", [Qt.Key.Key_Z, Qt.Key.Key_Y])
def test_history_cancels_creation_before_touching_committed_history(window, key):
    QTest.mouseClick(window.tool_palette.btn_rect, Qt.MouseButton.LeftButton)
    _drag(window, (40, 40), (80, 80))
    assert len(window.scene.objects) == 1 and window.scene.cmd.undo_count == 1
    if key == Qt.Key.Key_Y:
        QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        QApplication.processEvents()
        assert not window.scene.objects and window.scene.cmd.redo_count == 1
    QTest.mouseClick(window.tool_palette.btn_pen, Qt.MouseButton.LeftButton)
    _drag(window, (140, 140), (160, 140))
    tool = _tool(window)
    before = [
        (obj.id, copy.deepcopy(obj.polygon)) for obj in window.scene.objects.values()
    ]
    counts = (window.scene.cmd.undo_count, window.scene.cmd.redo_count)
    QTest.keyClick(window, key, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    assert not tool._nodes and not tool._is_placing_handle
    assert [(obj.id, obj.polygon) for obj in window.scene.objects.values()] == before
    assert (window.scene.cmd.undo_count, window.scene.cmd.redo_count) == counts
    QTest.keyClick(window, key, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    assert (window.scene.cmd.undo_count, window.scene.cmd.redo_count) != counts


def test_close_uses_both_explicit_handles_of_first_anchor(window):
    _drag(window, (80, 80), (110, 80))
    handles = (_tool(window)._nodes[0].handle_in, _tool(window)._nodes[0].handle_out)
    for point in [(200, 80), (200, 200), (80, 200), (80, 80)]:
        _click(window, point)
    assert len(window.scene.objects) == 1, _tool(window)._last_error
    obj = next(iter(window.scene.objects.values()))
    assert obj.beziers[0][1] == handles[1]
    assert obj.beziers[-1][2] == handles[0]
    assert obj.beziers[-1][3] == obj.beziers[0][0]
    assert is_valid_polygon(obj.polygon) and window.scene.cmd.undo_count == 1


def test_explicit_controls_reproducing_old_quantization_defect_still_reject(window):
    # Recreate the old automatic tangent by explicit gestures. The resulting
    # integer overlap must remain invalid; there is no repair or validator bypass.
    _click(window, (225, 35))
    _drag(window, (285, 35), (267, 35))
    _drag(window, (285, 95), (267, 95))
    tool = _tool(window)
    before = [(n.anchor, n.handle_in, n.handle_out) for n in tool._nodes]
    _click(window, (225, 35))
    assert not window.scene.objects and window.scene.cmd.undo_count == 0
    assert [(n.anchor, n.handle_in, n.handle_out) for n in tool._nodes] == before
    assert "Invalid sampled" in tool._last_error


@pytest.mark.parametrize("reverse", [False, True])
def test_non_axis_aligned_corner_contour_closes(window, reverse):
    points = [(70, 70), (113, 93), (99, 148), (53, 123)]
    if reverse:
        points.reverse()
    for point in [*points, points[0]]:
        _click(window, point)
    assert len(window.scene.objects) == 1, _tool(window)._last_error
    obj = next(iter(window.scene.objects.values()))
    assert is_valid_polygon(obj.polygon) and window.scene.cmd.undo_count == 1
