from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from src.core.commands import CommandManager, CommandResult, CommandStatus
from src.models.scene import Scene
from src.tools import magnetic_lasso as magnetic_module
from src.tools.collision_brush_tool import CollisionBrushTool
from src.tools.magnetic_lasso import MagneticLassoTool
from src.tools.magnetic_lasso_engine import MagneticLassoSettings
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui import mask_viewer as mask_module
from src.ui.mask_viewer import DetectionWorker, MaskViewer, MaskViewerDialog


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class CanvasProbe(QWidget):
    def __init__(self, scene: Scene):
        super().__init__()
        self.model = scene
        self.scene = scene
        self.update_count = 0
        self._zoom = 1.0

    def update(self):
        self.update_count += 1
        super().update()

    def get_zoom(self):
        return self._zoom

    def get_transform(self):
        return QTransform()

    def focus_on_object(self, object_id):
        self.focused_object = object_id


def scene_with_object(image=True):
    scene = Scene()
    scene.cmd = CommandManager(max_history=40)
    scene.add_object("A", [(10, 10), (70, 10), (70, 60), (10, 60)], select=True)
    if image:
        scene.image = np.zeros((96, 96, 3), dtype=np.uint8)
    scene.cmd.clear()
    return scene


def event(
    button=Qt.MouseButton.LeftButton,
    key=None,
    modifiers=Qt.KeyboardModifier.NoModifier,
    position=(20, 20),
):
    value = Mock()
    value.button.return_value = button
    value.key.return_value = key
    value.modifiers.return_value = modifiers
    value.position.return_value = QPointF(*position)
    value.pos.return_value = QPoint(*position)
    value.globalPos.return_value = QPoint(*position)
    return value


def paint_tool(draw):
    image = QImage(120, 120, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    draw(painter)
    painter.end()
    return image


def test_magnetic_pathfinder_worker_modes_and_errors(monkeypatch):
    edge_map = np.full((8, 8), 255, dtype=np.uint8)
    path = magnetic_module.dijkstra_pathfinding(edge_map, (0, 0), (7, 7))
    assert path[0] == (0, 0)
    assert path[-1] == (7, 7)

    payloads = []
    worker = magnetic_module._MagneticPathWorker(
        request_id=1,
        revision=2,
        purpose="segment",
        mode="legacy",
        edge_map=edge_map,
        edge_features=None,
        image_array=None,
        image_token=("image", 1),
        settings=MagneticLassoSettings(mode="legacy"),
        start=(0, 0),
        end=(7, 7),
    )
    worker.signals.completed.connect(payloads.append)
    worker.run()
    assert payloads[-1]["path"][-1] == (7, 7)
    assert payloads[-1]["commit_safe"] is True

    prepare = magnetic_module._MagneticPathWorker(
        request_id=2,
        revision=3,
        purpose="prepare",
        mode="precise",
        edge_map=None,
        edge_features=None,
        image_array=np.zeros((12, 12), dtype=np.uint8),
        image_token=("image", 2),
        settings=MagneticLassoSettings(mode="precise"),
        start=(0, 0),
        end=(0, 0),
    )
    prepare.signals.completed.connect(payloads.append)
    prepare.run()
    assert payloads[-1]["path"] == []
    assert payloads[-1]["edge_map"].shape == (12, 12)

    monkeypatch.setattr(
        magnetic_module,
        "build_edge_features",
        Mock(side_effect=RuntimeError("forced worker failure")),
    )
    failed = magnetic_module._MagneticPathWorker(
        request_id=3,
        revision=4,
        purpose="preview",
        mode="precise",
        edge_map=None,
        edge_features=None,
        image_array=np.zeros((4, 4), dtype=np.uint8),
        image_token=("image", 3),
        settings=MagneticLassoSettings(mode="precise"),
        start=(0, 0),
        end=(3, 3),
    )
    failed.signals.completed.connect(payloads.append)
    failed.run()
    assert "forced worker failure" in payloads[-1]["error"]
    assert payloads[-1]["commit_safe"] is False


def test_magnetic_image_cache_tokens_and_conversion(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = MagneticLassoTool(canvas, MagneticLassoSettings(mode="legacy"))
    monkeypatch.setattr(tool, "_uses_background_pathfinding", lambda: False)

    array = np.zeros((6, 7, 3), dtype=np.uint8)
    empty = np.empty((0, 0), dtype=np.uint8)
    assert tool._image_token(array)[0] == "numpy"
    assert tool._image_token(empty)[-1] == 0
    assert tool._image_token(QImage(3, 4, QImage.Format.Format_RGB32))[0] == "qimage"
    assert tool._image_token(object())[0] == "other"
    assert tool._image_token(None) is None

    scene.image = array
    converted = tool._get_image_array()
    assert converted.shape == (6, 7)
    tool._compute_edge_map()
    first_map = tool._edge_map
    tool._compute_edge_map()
    assert tool._edge_map is first_map
    assert tool._make_edge_overlay(first_map) is not None
    assert tool._make_edge_overlay(None) is None
    assert tool._make_edge_overlay(np.zeros((2, 2, 2), dtype=np.uint8)) is None

    scene.image = "invalid"
    assert tool._get_image_array() is None
    assert "Unsupported scene image type" in tool._last_error
    scene.image = np.zeros((2, 2, 2, 2), dtype=np.uint8)
    assert tool._get_image_array() is None
    assert "Unsupported numpy image" in tool._last_error
    tool._last_image_token = ("stale",)
    tool._edge_map = np.ones((2, 2), dtype=np.uint8)
    tool._invalidate_stale_edge_cache()
    assert tool._edge_map is None


def test_magnetic_anchor_history_events_commit_and_overlay(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = MagneticLassoTool(canvas, MagneticLassoSettings(mode="legacy"))
    monkeypatch.setattr(tool, "_uses_background_pathfinding", lambda: False)
    warnings = Mock()
    monkeypatch.setattr(magnetic_module.QMessageBox, "warning", warnings)

    assert tool._append_anchor((10, 10)) is True
    assert tool._append_anchor((10, 10)) is False
    assert tool._append_anchor((40, 10), [(10, 10), (40, 10)]) is True
    assert tool._append_anchor((40, 40), [(40, 10), (40, 40)]) is True
    assert tool._can_close_at((10, 10)) is True
    paint_tool(tool.draw_overlay)

    assert tool.remove_last_anchor() is True
    assert tool.restore_last_anchor() is True
    assert tool.on_undo() is True
    assert tool.on_redo() is True
    assert tool.on_key_press(event(key=Qt.Key.Key_Delete)) is True
    assert tool.restore_last_anchor() is True

    object_count = len(scene.objects)
    object_id = tool._finish_with_closing_path([(40, 40), (10, 40), (10, 10)])
    assert object_id is not None
    assert len(scene.objects) == object_count + 1
    assert tool._anchors == []

    tool._anchors = [(1, 1), (2, 2)]
    assert tool.finish_selection() is None
    warnings.assert_called()
    assert tool.on_key_press(event(key=Qt.Key.Key_Escape)) is True
    assert tool.on_key_press(event(key=Qt.Key.Key_A)) is False

    tool._append_anchor((5, 5))
    tool._set_mode("unknown")
    assert tool.settings.mode == "legacy"
    tool._set_mode("precise")
    assert tool.settings.mode == "precise"
    assert tool._anchors == []
    current_preset = tool.settings.preset
    tool._set_preset(current_preset)
    tool._set_preset("fast" if current_preset != "fast" else "balanced")
    tool._toggle_edge_overlay(False)
    assert tool.settings.show_edge_map is False


def test_magnetic_async_result_queue_and_failure_paths(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = MagneticLassoTool(canvas, MagneticLassoSettings(mode="legacy"))
    monkeypatch.setattr(tool, "_uses_background_pathfinding", lambda: True)
    monkeypatch.setattr(tool, "_set_path_busy", Mock())
    monkeypatch.setattr(magnetic_module.QMessageBox, "warning", Mock())
    started = Mock()
    monkeypatch.setattr(tool, "_start_async_path", started)

    tool._active_path_request = 9
    tool._request_async_path("preview", (1, 1), (2, 2))
    assert tool._queued_preview_request["end"] == (2, 2)
    tool._request_async_path("segment", (1, 1), (3, 3))
    assert tool._queued_action_request["purpose"] == "segment"
    assert tool._queued_preview_request is None

    tool._active_path_request = None
    tool._start_next_async_path()
    started.assert_called_once()
    tool._queued_action_request = None
    tool._queued_preview_request = None
    tool._start_next_async_path()

    next_path = Mock()
    monkeypatch.setattr(tool, "_start_next_async_path", next_path)
    signature = tool._current_edge_signature()
    token = tool._current_image_token()
    tool._state_revision = 7
    tool._active_path_request = 10
    tool._on_async_path_result(
        {
            "request_id": 10,
            "revision": 6,
            "purpose": "prepare",
            "start": (0, 0),
            "end": (0, 0),
            "path": [],
            "error": None,
            "edge_map": np.ones((4, 4), dtype=np.uint8),
            "edge_features": None,
            "image_token": token,
            "edge_signature": signature,
        }
    )
    assert tool._edge_map.shape == (4, 4)
    next_path.assert_called_once()

    tool._anchors = [(1, 1)]
    tool._state_revision = 7
    tool._on_async_path_result(
        {
            "request_id": 11,
            "revision": 7,
            "purpose": "preview",
            "start": (1, 1),
            "end": (3, 3),
            "path": [(1, 1), (3, 3)],
            "error": None,
            "edge_map": tool._edge_map,
            "edge_features": None,
            "image_token": token,
            "edge_signature": signature,
        }
    )
    assert tool._preview_path == [(1, 1), (3, 3)]

    tool._on_async_path_result(
        {
            "request_id": 12,
            "revision": 7,
            "purpose": "segment",
            "start": (1, 1),
            "end": (4, 4),
            "path": [],
            "error": None,
            "edge_map": tool._edge_map,
            "edge_features": None,
            "image_token": token,
            "edge_signature": signature,
        }
    )
    assert "No path returned" in tool._last_error
    tool._handle_async_failure("preview", "preview failed")
    assert tool._last_error == "preview: preview failed"


def test_mask_viewer_image_overlay_transform_and_events(qt_app):
    viewer = MaskViewer()
    viewer.resize(160, 120)
    selected = []
    clicked = []
    viewer.polygonSelected.connect(selected.append)
    viewer.imageClicked.connect(lambda point: clicked.append((point.x(), point.y())))

    image = np.zeros((40, 60), dtype=np.uint8)
    viewer.set_numpy_image(image)
    copy = viewer.get_numpy_image()
    copy[0, 0] = 255
    assert viewer.get_numpy_image()[0, 0] == 0
    viewer.set_overlay_polygons(
        [
            {"polygon": [(5, 5), (30, 5), (30, 30), (5, 30)]},
            [(35, 5), (55, 5), (55, 30), (35, 30)],
            {"polygon": []},
        ]
    )
    assert viewer._find_polygon_at(QPointF(10, 10)) == 0
    assert viewer._find_polygon_at(QPointF(40, 10)) == 1
    assert viewer._find_polygon_at(QPointF(90, 90)) == -1
    viewer.set_selected_polygon_index(99)
    viewer.set_selected_polygon_index(0)
    assert selected[-1] == 0

    viewer.set_view_transform(20.0, 3, 4)
    assert viewer.get_view_transform() == (8.0, 3.0, 4.0)
    viewer.set_zoom(2.0, QPointF(30, 20))
    point = viewer.image_to_view((10, 8))
    restored = viewer.view_to_image(point)
    assert restored == pytest.approx((10, 8))
    viewer.zoom_by(0.5)
    viewer.reset_view()
    assert viewer.get_zoom() > 0

    pan_start = event(
        modifiers=Qt.KeyboardModifier.ShiftModifier,
        position=(20, 20),
    )
    viewer.mousePressEvent(pan_start)
    viewer.mouseMoveEvent(event(position=(35, 30)))
    viewer.mouseReleaseEvent(event())
    assert viewer._panning is False
    assert pan_start.accept.called

    viewer.set_view_transform(1.0, 0, 0)
    select_event = event(position=(10, 10))
    viewer.mousePressEvent(select_event)
    assert viewer.get_selected_polygon_index() == 0
    viewer.set_overlay_polygons([])
    click_event = event(position=(12, 14))
    viewer.mousePressEvent(click_event)
    assert clicked[-1] == pytest.approx((12, 14))

    handled = event(position=(3, 3))
    viewer.tool_handler = Mock(return_value=True)
    viewer.mousePressEvent(handled)
    viewer.tool_handler.assert_called_once()
    viewer.show()
    qt_app.processEvents()
    viewer.grab()
    viewer.close()


def test_mask_viewer_qimage_branches_and_detection_worker(qt_app, monkeypatch):
    viewer = MaskViewer()
    viewer.set_numpy_image(np.zeros((4, 5), dtype=np.uint8))
    gray = viewer._get_qimage()
    assert gray.format() == QImage.Format.Format_Grayscale8
    assert viewer._get_qimage() is gray

    monkeypatch.setattr(mask_module, "HAS_CV2", False)
    viewer.set_numpy_image(np.zeros((4, 5, 3), dtype=np.uint8))
    assert viewer._get_qimage().format() == QImage.Format.Format_RGB888
    viewer._image = np.zeros((2,), dtype=np.uint8)
    viewer._qimage_cache = None
    assert viewer._get_qimage() is None
    viewer.set_numpy_image(None)
    assert viewer._get_qimage() is None
    viewer.reset_view()
    assert viewer.get_view_transform() == (1.0, 0.0, 0.0)

    errors = []
    empty_worker = DetectionWorker(None, "basic", {})
    empty_worker.error.connect(errors.append)
    empty_worker.run()
    assert errors[-1] == "No image data provided to worker"

    monkeypatch.setattr(
        "src.tools.auto_detect.detect_polygons",
        Mock(return_value=[[(0, 0), (3, 0), (0, 3)]]),
    )
    finished = []
    worker = DetectionWorker(np.zeros((5, 5), dtype=np.uint8), "basic", {})
    worker.finished.connect(finished.append)
    worker.run()
    assert len(finished[-1]) == 1

    monkeypatch.setattr(
        "src.tools.auto_detect.detect_polygons",
        Mock(side_effect=RuntimeError("forced detection failure")),
    )
    failed = DetectionWorker(np.zeros((5, 5), dtype=np.uint8), "basic", {})
    failed.error.connect(errors.append)
    failed.run()
    assert errors[-1] == "forced detection failure"


def test_mask_dialog_presets_detection_and_apply_outcomes(qt_app, monkeypatch):
    scene = scene_with_object(image=False)
    dialog = MaskViewerDialog(scene, lang="invalid")
    warnings = Mock()
    critical = Mock()
    information = Mock()
    monkeypatch.setattr(mask_module.QMessageBox, "warning", warnings)
    monkeypatch.setattr(mask_module.QMessageBox, "critical", critical)
    monkeypatch.setattr(mask_module.QMessageBox, "information", information)

    dialog._run_detection()
    warnings.assert_called()
    dialog.update_language("pt")
    dialog.update_language("invalid")
    assert dialog.current_lang == "en"
    dialog.preset_combo.setCurrentIndex(-1)
    assert dialog._selected_preset_id() == "Basic"
    dialog._apply_preset("Perfect")
    dialog._apply_preset("missing")
    dialog._apply_preset_params({"min_area": 77.0, "unknown": 3})
    assert dialog.params["unknown"] == 3
    dialog._on_polygon_selected(0)
    dialog._on_polygon_selected(-1)
    dialog._toggle_advanced_params(Qt.CheckState.Checked.value)
    dialog._toggle_advanced_params(Qt.CheckState.Unchecked.value)

    dialog._last_polygons = []
    dialog._apply_to_scene()
    dialog._last_polygons = [[(0, 0), (10, 0), (0, 10)]]
    scene.cmd = None
    dialog._apply_to_scene()
    warnings.assert_called()

    scene.cmd = CommandManager()
    dialog._last_polygons = [[(0, 0), (1, 1)]]
    dialog._apply_to_scene()
    dialog._last_polygons = [[(0, 0), (10, 0), (0, 10)]]
    dialog.close = Mock()
    dialog._apply_to_scene()
    information.assert_called()
    dialog.close.assert_called_once()
    dialog._on_detection_finished([])
    dialog._on_detection_finished([[(0, 0), (3, 0), (0, 3)]])
    dialog._on_detection_error("forced")
    critical.assert_called()
    dialog.close()


def test_collision_brush_toggle_hit_testing_and_transform_events(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = CollisionBrushTool(canvas)
    critical = Mock()
    monkeypatch.setattr("src.tools.collision_brush_tool.QMessageBox.critical", critical)

    assert tool._find_polygon_at((20, 20)) == "A"
    assert tool._find_polygon_at((100, 100)) is None
    tool.on_mouse_press(event(), (20, 20))
    assert scene.has_collision("A") is True
    tool.on_mouse_press(event(), (20, 20))
    assert scene.has_collision("A") is False

    original_manager = scene.cmd
    scene.cmd = None
    tool.on_mouse_press(event(), (20, 20))
    critical.assert_called()
    scene.cmd = original_manager

    hub = Mock()
    monkeypatch.setattr(tool, "_show_hub_menu", hub)
    tool.on_mouse_press(event(Qt.MouseButton.RightButton), (20, 20))
    hub.assert_called_once()

    assert tool._begin_transform_gesture("A", "Move") is True
    tool.on_mouse_move(event(), (100, 100))
    tool.on_mouse_move(event(), (110, 115))
    tool.on_mouse_press(event(), (110, 115))
    assert tool._transform_transaction is None
    scene.cmd.undo(scene)

    assert tool._begin_transform_gesture("A", "Scale") is True
    scale_menu = Mock()
    monkeypatch.setattr(tool, "_show_scale_menu", scale_menu)
    tool.on_mouse_press(event(Qt.MouseButton.RightButton), (20, 20))
    scale_menu.assert_called_once()
    assert tool.on_key_press(event(key=Qt.Key.Key_Escape)) is True
    assert tool.on_key_press(event(key=Qt.Key.Key_A)) is False
    assert tool.on_undo() is False
    assert tool.on_redo() is False


def test_collision_brush_outcomes_remove_overlay_and_edit(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = CollisionBrushTool(canvas)
    warnings = Mock()
    critical = Mock()
    monkeypatch.setattr("src.tools.collision_brush_tool.QMessageBox.warning", warnings)
    monkeypatch.setattr("src.tools.collision_brush_tool.QMessageBox.critical", critical)

    rejected = CommandResult(CommandStatus.REJECTED, "X", "execute", "rejected")
    failed = CommandResult(CommandStatus.FAILED, "X", "execute", "failed")
    tool._report_command_result(rejected, "Operation")
    tool._report_command_result(failed, "Operation")
    warnings.assert_called()
    critical.assert_called()

    tool._start_edit(None)
    palette = SimpleNamespace(select_tool_by_name=Mock())
    tool._start_edit(SimpleNamespace(tool_palette=palette))
    palette.select_tool_by_name.assert_called_once_with("polygon_edit")
    tool._undo()
    tool._redo()

    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.question",
        Mock(return_value=QMessageBox.StandardButton.No),
    )
    tool._remove("A")
    assert "A" in scene.objects
    monkeypatch.setattr(
        "src.tools.collision_brush_tool.QMessageBox.question",
        Mock(return_value=QMessageBox.StandardButton.Yes),
    )
    tool.moving = True
    tool.moving_oid = "A"
    tool.scaling = True
    tool.scaling_oid = "A"
    tool.selected_polygon_id = "A"
    tool._remove("A")
    assert "A" not in scene.objects
    assert tool.selected_polygon_id is None

    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = CollisionBrushTool(canvas)
    scene.collision_shapes["A"] = list(scene.objects["A"].polygon)
    tool.selected_polygon_id = "A"
    tool.moving = True
    tool.moving_oid = "A"
    tool.scaling = True
    tool.scaling_oid = "A"
    paint_tool(tool.draw_overlay)


def test_polygon_edit_selection_hit_testing_overlay_and_events(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = PolygonEditTool(canvas)
    left = event()
    right = event(Qt.MouseButton.RightButton)

    assert tool.find_vertex_at((10, 10)) == ("A", 0)
    assert tool.find_vertex_at((200, 200)) == (None, None)
    assert tool.find_polygon_at((20, 20)) == "A"
    assert tool.find_polygon_at((200, 200)) is None
    square = [QPointF(0, 0), QPointF(10, 0), QPointF(10, 10), QPointF(0, 10)]
    assert tool.point_in_polygon((5, 5), square) is True
    assert tool.point_in_polygon((20, 5), square) is False

    tool.multi_select = True
    tool.on_mouse_press(left, (20, 20))
    assert tool.selected_polygon_ids == {"A"}
    tool.on_mouse_press(left, (20, 20))
    assert tool.selected_polygon_ids == set()
    tool.multi_select = False
    tool.on_mouse_press(left, (10, 10))
    assert tool._vertex_transaction is not None
    tool.on_mouse_move(event(Qt.MouseButton.NoButton), (15, 16))
    tool.on_mouse_release(left, (15, 16))
    assert tool._vertex_transaction is None

    tool.selected_polygon_ids = {"A", "missing"}
    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    canvas._zoom = 0.0
    paint_tool(tool.draw_overlay)
    menu = Mock()
    monkeypatch.setattr(tool, "show_context_menu", menu)
    tool.on_mouse_press(right, (30, 30))
    menu.assert_called_once()
    tool.adding_new = True
    tool.on_mouse_press(right, (30, 30))
    assert tool.adding_new is False


def test_polygon_edit_vertex_guards_deletion_and_history(qt_app, monkeypatch):
    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = PolygonEditTool(canvas)
    information = Mock()
    warnings = Mock()
    critical = Mock()
    monkeypatch.setattr(
        "src.tools.polygon_edit_tool.QMessageBox.information", information
    )
    monkeypatch.setattr("src.tools.polygon_edit_tool.QMessageBox.warning", warnings)
    monkeypatch.setattr("src.tools.polygon_edit_tool.QMessageBox.critical", critical)

    tool.start_adding_new()
    information.assert_called_once()
    tool.selected_polygon_id = "A"
    tool.start_adding_new()
    assert tool.adding_new is True
    assert tool.on_key_press(event(key=Qt.Key.Key_Escape)) is True
    assert tool.on_key_press(event(key=Qt.Key.Key_A)) is False

    tool.add_vertex_at_pos((40, 10))
    assert len(scene.objects["A"].polygon) == 5
    tool.delete_selected_vertex()
    assert len(scene.objects["A"].polygon) == 4
    tool.select_all_vertices()
    assert tool.selected_vertex == 0
    tool.clear_selection()
    assert tool.selected_polygon_ids == set()
    tool.undo_last_action()
    tool.redo_last_action()

    tool.multi_select = True
    tool.selected_polygon_ids = {"A", "missing"}
    tool.delete_selected_polygon()
    assert "A" in scene.objects
    warnings.assert_called()
    tool.selected_polygon_ids = {"A"}
    tool.delete_selected_polygon()
    assert "A" not in scene.objects

    scene = scene_with_object()
    canvas = CanvasProbe(scene)
    tool = PolygonEditTool(canvas)
    tool.selected_polygon_id = "A"
    tool.selected_vertex = 0
    assert tool._begin_vertex_gesture() is True
    assert tool.on_undo() is True
    assert tool.on_redo() is False
    tool.on_cancel()
