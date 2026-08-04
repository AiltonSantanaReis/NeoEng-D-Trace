"""Qt contracts for Etapa 0.5.2F. Execute on Windows with PySide6."""

from __future__ import annotations

from unittest.mock import Mock, patch

import numpy as np
import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from src.tools.magnetic_lasso import MagneticLassoTool
from src.tools.magnetic_lasso_engine import MagneticLassoSettings


@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def make_canvas(width=101, height=40):
    image = QImage(width, height, QImage.Format.Format_Grayscale8)
    image.fill(0)
    scene = Mock()
    scene.get_image.return_value = image
    scene.cmd = None
    scene.add_polygon.return_value = "object-1"

    canvas = Mock()
    canvas.scene = scene
    canvas.model = scene
    canvas._zoom = 1.0
    canvas._pan = QPointF(0.0, 0.0)
    canvas.get_zoom.return_value = 1.0
    canvas.get_transform.return_value = Mock()
    return canvas, scene


def test_qimage_padding_is_removed_from_numpy_array():
    canvas, _ = make_canvas(width=101, height=37)
    tool = MagneticLassoTool(canvas)

    array = tool._get_image_array()

    assert array.shape == (37, 101)
    assert array.dtype == np.uint8


@pytest.mark.parametrize(
    "image",
    [
        np.zeros((37, 101), dtype=np.uint8),
        np.zeros((37, 101, 3), dtype=np.uint8),
        np.zeros((37, 101, 4), dtype=np.uint8),
    ],
)
def test_real_cv2_ndarray_scene_image_is_supported(image):
    canvas, scene = make_canvas(width=101, height=37)
    if image.ndim == 2:
        image[:, 52:] = 255
    else:
        image[:, 52:, :3] = 255
        if image.shape[2] == 4:
            image[:, :, 3] = 255
    scene.get_image.return_value = image
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings())

    array = tool._get_image_array()
    tool._compute_edge_map()

    assert array is not None
    assert array.shape == (37, 101)
    assert array.dtype == np.uint8
    assert tool._edge_map is not None
    assert int(tool._edge_map.max()) > 0


def test_mouse_preview_works_with_real_cv2_ndarray_scene_image():
    canvas, scene = make_canvas(width=80, height=60)
    image = np.zeros((60, 80, 4), dtype=np.uint8)
    image[:, 40:, :3] = 255
    image[:, :, 3] = 255
    scene.get_image.return_value = image
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings())
    tool._anchors = [(39, 10)]
    tool._path = [(39, 10)]

    event = Mock()
    tool.on_mouse_move(event, (39, 50))

    assert tool._preview_path
    assert tool._preview_path[0] == (39, 10)
    assert tool._preview_path[-1][1] == 50


def test_application_settings_default_to_precise_and_direct_api_keeps_legacy():
    canvas, _ = make_canvas()
    direct_tool = MagneticLassoTool(canvas)
    app_tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings())

    assert direct_tool.settings.mode == "legacy"
    assert app_tool.settings.mode == "precise"
    app_tool._set_mode("legacy")
    assert app_tool.settings.mode == "legacy"


def test_cancel_callback_clears_all_in_progress_state():
    canvas, _ = make_canvas()
    tool = MagneticLassoTool(canvas)
    tool._anchors = [(1, 1), (10, 1)]
    tool._segments = [[(1, 1), (10, 1)]]
    tool._path = [(1, 1), (10, 1)]
    tool._preview_path = [(10, 1), (10, 10)]

    tool.on_cancel()

    assert tool._anchors == []
    assert tool._segments == []
    assert tool._path == []
    assert tool._preview_path == []


def test_anchor_undo_and_redo_do_not_touch_project_history():
    canvas, scene = make_canvas()
    project_history = Mock()
    scene.cmd = project_history
    tool = MagneticLassoTool(canvas)
    tool._anchors = [(1, 1), (8, 1)]
    tool._segments = [[(1, 1), (8, 1)]]
    tool._rebuild_path()

    assert tool.on_undo() is True
    assert tool._anchors == [(1, 1)]
    assert tool.on_redo() is True
    assert tool._anchors == [(1, 1), (8, 1)]
    project_history.undo.assert_not_called()
    project_history.redo.assert_not_called()
    project_history.execute.assert_not_called()


def test_failed_finish_preserves_anchors_and_segments():
    canvas, _ = make_canvas()
    tool = MagneticLassoTool(canvas)
    tool._anchors = [(1, 1), (20, 1), (20, 20)]
    tool._segments = [
        [(1, 1), (20, 1)],
        [(20, 1), (20, 20)],
    ]
    tool._rebuild_path()

    with (
        patch.object(tool, "_compute_magnetic_path", return_value=[]),
        patch.object(tool, "_show_invalid_selection"),
    ):
        result = tool.finish_selection()

    assert result is None
    assert len(tool._anchors) == 3
    assert len(tool._segments) == 2


def test_successful_finish_clears_state_only_after_object_creation():
    from src.core.commands import CommandManager
    from src.models.scene import Scene

    canvas, _ = make_canvas()
    scene = Scene()
    scene.cmd = CommandManager()
    canvas.scene = scene
    canvas.model = scene
    tool = MagneticLassoTool(canvas, MagneticLassoSettings(mode="legacy"))
    tool._anchors = [(1, 1), (20, 1), (20, 20)]
    tool._segments = [
        [(1, 1), (20, 1)],
        [(20, 1), (20, 20)],
    ]
    tool._rebuild_path()

    with patch.object(
        tool,
        "_compute_magnetic_path",
        return_value=[(20, 20), (1, 20), (1, 1)],
    ):
        result = tool.finish_selection()

    assert result is not None
    assert result in scene.objects
    assert scene.cmd.undo_count == 1
    assert tool._anchors == []
    assert tool._path == []


def test_interface_exposes_key_and_local_history_callbacks():
    canvas, _ = make_canvas()
    interface = MagneticLassoTool(canvas).interface()

    assert callable(interface.on_key_press)
    assert callable(interface.on_undo)
    assert callable(interface.on_redo)


def test_commit_sanitizes_backtracking_before_scene_command():
    from src.core.commands import CommandManager
    from src.models.scene import Scene

    canvas, _ = make_canvas()
    scene = Scene()
    scene.cmd = CommandManager()
    canvas.scene = scene
    canvas.model = scene
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings())

    object_id = tool.commit_selection([(0, 0), (12, 0), (6, 0), (12, 10), (0, 10)])

    assert object_id is not None
    assert object_id in scene.objects
    assert scene.selected_id == object_id


def test_invalid_collinear_finish_does_not_enter_project_history():
    from src.core.commands import CommandManager
    from src.models.scene import Scene

    canvas, _ = make_canvas()
    scene = Scene()
    scene.cmd = CommandManager()
    canvas.scene = scene
    canvas.model = scene
    tool = MagneticLassoTool(canvas, settings=MagneticLassoSettings())

    object_id = tool.commit_selection([(0, 0), (10, 0), (20, 0)])

    assert object_id is None
    assert scene.objects == {}
    assert scene.cmd._undo == []
