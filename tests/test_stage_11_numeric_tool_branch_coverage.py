from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QWidget

import src.core.view_processor as view_module
import src.tools.auto_detect as detect_module
import src.tools.mask_utils as mask_module
from src.core.commands import CommandResult, CommandStatus
from src.core.view_processor import ViewProcessor
from src.tools.base_tool import BaseTool


def contour(points):
    return np.asarray(points, dtype=np.int32).reshape(-1, 1, 2)


def test_detect_result_access_and_dispatch_errors(monkeypatch):
    result = detect_module.DetectResult([{"polygon": [1]}], {"status": "ok"})
    assert result[0]["polygon"] == [1]
    assert result["polygons"] == list(result)
    assert result["feedback"] == {"status": "ok"}
    assert result.get("polygons") == list(result)
    assert result.get("feedback") == {"status": "ok"}
    assert result.get("missing", 7) == 7
    with pytest.raises(KeyError):
        result["missing"]

    monkeypatch.setattr(
        detect_module,
        "_detect_polygons_enhanced",
        Mock(side_effect=RuntimeError("forced detection failure")),
    )
    with pytest.raises(RuntimeError, match="forced detection failure"):
        detect_module.detect_polygons(np.zeros((2, 2), dtype=np.uint8), "enhanced")


def test_basic_detection_color_downscale_filter_and_short_polygon(monkeypatch):
    short = contour([(1, 1), (8, 1)])
    rejected = contour([(1, 1), (5, 1), (3, 2)])
    square = contour([(4, 4), (20, 4), (20, 20), (4, 20)])
    monkeypatch.setattr(
        detect_module.cv2,
        "findContours",
        lambda *args: ([short, rejected, square], None),
    )
    monkeypatch.setattr(
        detect_module,
        "rdp_simplify",
        lambda points, epsilon: [] if len(points) == 3 else points,
    )

    image = np.zeros((48, 48, 3), dtype=np.uint8)
    result = detect_module._detect_polygons_basic(
        image,
        downscale=0.5,
        min_area=-1,
        rdp_epsilon=0.25,
    )

    assert len(result) == 1
    assert result[0]["polygon"] == [(8, 8), (40, 8), (40, 40), (8, 40)]
    assert result[0]["bbox"] == (8, 8, 34, 34)
    assert result[0]["area"] == pytest.approx(1024.0)

    monkeypatch.setattr(
        detect_module.cv2,
        "findContours",
        lambda *args: ([square], None),
    )
    plain = detect_module._detect_polygons_basic(
        np.zeros((32, 32), dtype=np.uint8), min_area=9999
    )
    assert plain == []


def test_perfect_detection_small_thresholds_convexity_and_downscale():
    clear = np.zeros((80, 80, 3), dtype=np.uint8)
    cv2.rectangle(clear, (15, 15), (60, 60), (255, 255, 255), -1)
    clear_result = detect_module._detect_polygons_perfect(
        clear,
        downscale=0.5,
        min_area=20,
        decompose_convex=True,
    )
    assert clear_result
    assert clear_result[0]["area"] > 1000
    assert len(clear_result[0]["polygon"]) >= 3

    otsu = np.full((60, 60), 20, dtype=np.uint8)
    cv2.rectangle(otsu, (10, 10), (45, 45), 180, -1)
    otsu_result = detect_module._detect_polygons_perfect(otsu, min_area=20)
    assert otsu_result


def test_perfect_detection_large_watershed_fallback(monkeypatch):
    image = np.full((220, 220), 20, dtype=np.uint8)
    mask = np.zeros_like(image)
    cv2.rectangle(mask, (40, 40), (180, 180), 255, -1)
    monkeypatch.setattr(
        detect_module, "multi_scale_edges", lambda *args, **kwargs: mask
    )
    monkeypatch.setattr(
        detect_module, "threshold_adaptive", lambda *args, **kwargs: mask.copy()
    )
    monkeypatch.setattr(
        detect_module, "close_small_gaps", lambda value, **kwargs: value
    )
    monkeypatch.setattr(
        detect_module.cv2,
        "distanceTransform",
        lambda *args: np.zeros_like(mask, dtype=np.float32),
    )
    monkeypatch.setattr(
        detect_module.cv2,
        "connectedComponents",
        lambda value: (1, np.zeros_like(value, dtype=np.int32)),
    )
    monkeypatch.setattr(
        detect_module.cv2,
        "watershed",
        lambda color, markers: np.ones_like(markers),
    )

    result = detect_module._detect_polygons_perfect(
        image,
        min_area=100,
        watershed_distance=8,
    )

    assert len(result) == 1
    assert result[0]["bbox"] == (40, 40, 141, 141)


def test_perfect_detection_hierarchy_degenerate_and_rejected_simplification(
    monkeypatch,
):
    child = contour([(0, 0), (5, 0), (5, 5), (0, 5)])
    degenerate = contour([(10, 10), (10, 10), (10, 10)])
    hierarchy = np.asarray([[[-1, -1, -1, 1], [-1, -1, 0, -1]]], dtype=np.int32)
    monkeypatch.setattr(
        detect_module.cv2,
        "findContours",
        lambda *args: ([child, degenerate], hierarchy),
    )
    monkeypatch.setattr(
        detect_module,
        "curvature_adaptive_simplify",
        lambda *args, **kwargs: [(10, 10), (10, 10), (10, 10)],
    )
    result = detect_module._detect_polygons_perfect(
        np.zeros((210, 210), dtype=np.uint8),
        min_area=-1,
    )
    assert len(result) == 1
    assert result[0]["quality_metrics"]["circularity"] == 0
    assert result[0]["quality_metrics"]["convexity"] == 0

    monkeypatch.setattr(
        detect_module,
        "curvature_adaptive_simplify",
        lambda *args, **kwargs: [],
    )
    assert (
        detect_module._detect_polygons_perfect(
            np.zeros((210, 210), dtype=np.uint8), min_area=-1
        )
        == []
    )


def test_enhanced_detection_holes_smoothing_bezier_and_downscale():
    image = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(image, (10, 10), (90, 90), 255, -1)
    cv2.rectangle(image, (35, 35), (65, 65), 0, -1)

    result = detect_module._detect_polygons_enhanced(
        image,
        detect_holes=True,
        min_area=5,
        chaikin_iterations=1,
        fit_bezier=True,
    )
    outer = [item for item in result if not item["is_hole"]]
    holes = [item for item in result if item["is_hole"]]
    assert len(outer) == 1
    assert len(holes) == 1
    assert len(outer[0]["holes"]) == 1
    assert any("bezier_segments" in item for item in result)

    scaled = detect_module._detect_polygons_enhanced(
        image,
        downscale=0.5,
        min_area=5,
    )
    assert scaled
    assert scaled[0]["bbox"][2] > 70


def test_enhanced_detection_edge_fallback_short_and_bezier_failure(monkeypatch):
    short = contour([(1, 1), (4, 1)])
    triangle = contour([(10, 10), (40, 10), (25, 40)])
    monkeypatch.setattr(
        detect_module,
        "enhanced_edge_detection",
        lambda *args: np.zeros((50, 50), dtype=np.uint8),
    )
    monkeypatch.setattr(
        detect_module.cv2,
        "findContours",
        lambda *args: ([short, triangle], None),
    )
    monkeypatch.setattr(
        detect_module,
        "catmull_rom_to_beziers",
        Mock(side_effect=RuntimeError("forced bezier failure")),
    )

    result = detect_module._detect_polygons_enhanced(
        np.tile(np.arange(50, dtype=np.uint8), (50, 1)),
        min_area=-1,
        fit_bezier=True,
    )

    assert len(result) == 1
    assert result[0]["polygon"] == [(10, 10), (40, 10), (25, 40)]
    assert "bezier_segments" not in result[0]


class FakeArrayModule:
    ndarray = np.ndarray
    uint8 = np.uint8
    float32 = np.float32

    @staticmethod
    def asarray(value):
        return np.asarray(value)

    @staticmethod
    def asnumpy(value):
        return np.asarray(value)

    abs = staticmethod(np.abs)
    max = staticmethod(np.max)
    maximum = staticmethod(np.maximum)
    sqrt = staticmethod(np.sqrt)


class FakeNdimage:
    @staticmethod
    def gaussian_filter(value, sigma):
        return np.asarray(value)

    @staticmethod
    def sobel(value, axis):
        return np.gradient(np.asarray(value, dtype=np.float32), axis=axis)

    @staticmethod
    def laplace(value):
        return cv2.Laplacian(np.asarray(value, dtype=np.float32), cv2.CV_32F)


@pytest.mark.parametrize("mode", [1, 2, 3, 99])
def test_gpu_xray_pipeline_with_numpy_backend(monkeypatch, mode):
    monkeypatch.setattr(view_module, "cp", FakeArrayModule)
    monkeypatch.setattr(view_module, "ndimage", FakeNdimage)
    source = np.zeros((12, 12, 3), dtype=np.uint8)
    source[3:9, 3:9] = 255

    result = ViewProcessor._gpu_generate_xray(source, mode)

    assert result.shape == (12, 12, 3)
    assert result.dtype == np.uint8


def test_gpu_xray_zero_normalization_and_qimage_boundaries(monkeypatch):
    monkeypatch.setattr(view_module, "cp", FakeArrayModule)
    monkeypatch.setattr(view_module, "ndimage", FakeNdimage)
    gray = np.zeros((8, 8), dtype=np.uint8)
    for mode in (1, 2, 3):
        assert ViewProcessor._gpu_generate_xray(gray, mode).shape == (8, 8, 3)

    monkeypatch.setattr(view_module, "HAS_GPU", True)
    assert ViewProcessor.to_qimage(gray) is not None

    class FailedArrayModule(FakeArrayModule):
        @staticmethod
        def asnumpy(value):
            raise RuntimeError("forced download failure")

    monkeypatch.setattr(view_module, "cp", FailedArrayModule)
    assert ViewProcessor.to_qimage(gray) is None
    assert ViewProcessor.to_qimage(np.zeros((0, 2), dtype=np.uint8)) is None

    monkeypatch.setattr(
        ViewProcessor,
        "_gpu_generate_xray",
        staticmethod(Mock(side_effect=RuntimeError("forced gpu failure"))),
    )
    monkeypatch.setattr(
        ViewProcessor,
        "_cpu_generate_xray",
        staticmethod(Mock(side_effect=RuntimeError("forced cpu failure"))),
    )
    assert ViewProcessor.generate_xray(gray) is None


def test_mask_threshold_morphology_and_contour_contracts():
    rgb = np.zeros((15, 15, 3), dtype=np.uint8)
    rgb[5:10, 5:10] = 255
    threshold = mask_module.threshold_adaptive(rgb, block_size=3, C=1)
    assert threshold.shape == rgb.shape[:2]

    with pytest.raises(ValueError):
        mask_module.threshold_adaptive("invalid")
    with pytest.raises(ValueError):
        mask_module.threshold_adaptive(np.zeros((2, 2, 2, 2)))

    mask = np.zeros((12, 12), dtype=np.uint8)
    mask[3:9, 3:9] = 255
    for shape, custom in (
        ("rect", None),
        ("ellipse", None),
        ("custom", np.ones((3, 3), dtype=np.uint8)),
    ):
        assert (
            mask_module.close_small_gaps(
                mask, kernel_shape=shape, custom_kernel=custom
            ).shape
            == mask.shape
        )

    with pytest.raises(ValueError):
        mask_module.close_small_gaps("invalid")
    with pytest.raises(ValueError):
        mask_module.close_small_gaps(np.zeros((2, 2, 2)))
    with pytest.raises(ValueError):
        mask_module.close_small_gaps(mask, kernel_shape="custom")
    with pytest.raises(ValueError):
        mask_module.close_small_gaps(mask, kernel_shape="unknown")

    assert mask_module.extract_contours(mask)
    with pytest.raises(ValueError):
        mask_module.extract_contours("invalid")
    with pytest.raises(ValueError):
        mask_module.extract_contours(np.zeros((2, 2, 2)))


def test_rdp_curvature_and_weighted_simplification_branches(monkeypatch):
    with pytest.raises(ValueError):
        mask_module.rdp_simplify(np.zeros((3, 2)))
    assert mask_module.rdp_simplify([(0, 0), (1, 1)]) == [(0.0, 0.0), (1.0, 1.0)]
    assert mask_module.rdp_simplify([(0, 0), (2, 2), (0, 0)], 0.1)
    assert mask_module.rdp_simplify([(0, 0), (1, 0), (2, 0)], 10) == [
        (0.0, 0.0),
        (2.0, 0.0),
    ]

    with pytest.raises(ValueError):
        mask_module.curvature_adaptive_simplify("invalid")
    assert mask_module.curvature_adaptive_simplify([(0, 0), (1, 1)]) == [
        (0, 0),
        (1, 1),
    ]
    with pytest.raises(ValueError):
        mask_module.curvature_adaptive_simplify(
            [(0, 0), (1, 0), (1, 1)], min_points=True
        )
    with pytest.raises(ValueError):
        mask_module.curvature_adaptive_simplify(
            [(0, 0), (1, 0), (1, 1)], min_points=3.0
        )

    repeated = np.asarray([[[1, 1]], [[1, 1]], [[1, 1]], [[1, 1]]])
    assert len(mask_module.curvature_adaptive_simplify(repeated, min_points=3)) >= 3
    matrix = np.asarray([(0, 0), (4, 0), (4, 4), (0, 4)])
    assert len(mask_module.curvature_adaptive_simplify(matrix, min_points=3)) >= 3
    assert mask_module._compute_discrete_curvature([(0, 0), (1, 1)]) == [0.0, 0.0]

    monkeypatch.setattr(
        mask_module,
        "_violates_curvature_preservation",
        lambda points, removed: True,
    )
    weighted = mask_module._iterative_rdp_with_weights(
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [1],
        min_points=3,
    )
    assert len(weighted) == 4
    assert mask_module._iterative_rdp_with_weights([(0, 0), (1, 1)], []) == [
        (0.0, 0.0),
        (1.0, 1.0),
    ]


def test_curvature_preservation_true_false_and_degenerate():
    assert (
        mask_module._violates_curvature_preservation([(0, 0), (1, 1)], (0, 0)) is False
    )
    assert (
        mask_module._violates_curvature_preservation([(0, 0), (0, 0), (0, 0)], (0, 0))
        is False
    )
    acute = [(0, 0), (10, 0), (9, 1)]
    assert mask_module._violates_curvature_preservation(acute, (5, 0)) is True
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert mask_module._violates_curvature_preservation(square, (5, 5)) is False


def test_base_tool_coordinate_interface_and_default_callbacks():
    class RaisingPoint:
        def x(self):
            raise ValueError("bad x")

        def y(self):
            return 1

    assert BaseTool._point_coordinates(QPointF(1.5, 2.5)) == (1.5, 2.5)
    assert BaseTool._point_coordinates([3, 4, 5]) == (3.0, 4.0)
    assert BaseTool._point_coordinates(["x", 4]) is None
    assert BaseTool._point_coordinates(RaisingPoint()) is None
    assert BaseTool._point_coordinates(object()) is None

    canvas = SimpleNamespace(
        get_zoom=Mock(side_effect=RuntimeError("zoom failure")),
        _zoom=float("nan"),
        _pan=QPointF(10, 20),
        image_to_widget=Mock(side_effect=RuntimeError("transform failure")),
        widget_to_image=Mock(side_effect=RuntimeError("transform failure")),
    )
    tool = BaseTool(canvas)
    assert tool.get_canvas_zoom(default=2) == 2
    assert tool.image_to_screen(3, 4) == (13.0, 24.0)
    assert tool.screen_to_image(13, 24) == (3, 4)

    canvas.image_to_widget = lambda x, y: (x + 1, y + 2)
    canvas.widget_to_image = lambda point: QPointF(point.x() / 2, point.y() / 2)
    assert tool.image_to_screen(3, 4) == (4.0, 6.0)
    assert tool.screen_to_image(5, 7) == (2, 4)

    interface = tool.interface()
    interface.on_mouse_press(None, (0, 0))
    interface.on_mouse_move(None, (0, 0))
    interface.on_mouse_release(None, (0, 0))
    interface.on_double_click(None, (0, 0))
    interface.on_cancel()
    interface.draw_overlay(None)
    interface.update_language("en")
    assert interface.on_key_press(None) is False
    assert interface.on_undo() is False
    assert interface.on_redo() is False


def test_base_tool_polygon_command_boundaries(monkeypatch):
    messages = []
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.critical",
        lambda *args: messages.append(("critical", args[1], args[2])),
    )
    monkeypatch.setattr(
        "src.tools.base_tool.QMessageBox.warning",
        lambda *args: messages.append(("warning", args[1], args[2])),
    )

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    assert app is not None
    canvas = QWidget()
    canvas.model = SimpleNamespace(cmd=None)
    tool = BaseTool(canvas)
    tool._last_error = ""
    assert tool.commit_polygon_command([(0, 0), (5, 0), (0, 5)]) is None
    assert "unavailable" in tool._last_error.lower()

    manager = Mock()
    canvas.model.cmd = manager
    manager.execute.side_effect = RuntimeError("forced manager failure")
    assert tool.commit_polygon_command([(0, 0), (5, 0), (0, 5)]) is None

    for status in (
        CommandStatus.REJECTED,
        CommandStatus.FAILED,
        CommandStatus.NO_CHANGE,
    ):
        manager.execute.side_effect = None
        manager.execute.return_value = CommandResult(
            status, "Add", "execute", "boundary"
        )
        assert tool.commit_polygon_command([(0, 0), (5, 0), (0, 5)]) is None

    def apply(command, model):
        command.object_id = "created-object"
        return CommandResult(CommandStatus.APPLIED, "Add", "execute")

    manager.execute.side_effect = apply
    assert (
        tool.commit_polygon_command(
            [(0, 0), (5, 0), (0, 5)], action_name="Test Polygon"
        )
        == "created-object"
    )
    assert {message[0] for message in messages} == {"critical", "warning"}
