"""Real OpenCV/Qt integration checks for the assisted detection pipeline."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from src.core.commands import AutoGenerateCollisionShapesCommand, CommandManager
from src.exporters.collision_exporter import (
    collision_shape_record,
    export_collision_document,
    save_collision_text,
)
from src.models.scene import Scene
from src.persistence.project_io import load_project_into_scene, save_scene_project
from src.tools import segmentation
from src.tools.auto_detect import detect_polygons
from src.tools.segmentation import normalize_roi, segment_grabcut
from src.ui.mask_viewer import MaskViewer


@pytest.fixture
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _image_with_subject() -> np.ndarray:
    image = np.zeros((180, 220, 3), dtype=np.uint8)
    cv2.rectangle(image, (45, 35), (175, 145), (210, 210, 210), thickness=-1)
    cv2.circle(image, (110, 90), 18, (0, 0, 0), thickness=-1)
    return image


def test_grabcut_returns_real_mask_and_roi_metrics() -> None:
    image = _image_with_subject()
    result = segment_grabcut(image, (35, 25, 150, 130), iterations=4)

    assert result.mask.dtype == np.uint8
    assert result.mask.shape == image.shape[:2]
    assert set(np.unique(result.mask)).issubset({0, 255})
    assert result.foreground_pixels > 8_000
    assert result.components == 1
    assert result.roi == (33, 23, 154, 134)


def test_grabcut_detection_preserves_hierarchy_contract() -> None:
    result = detect_polygons(
        _image_with_subject(),
        mode="grabcut",
        roi=(35, 25, 150, 130),
        grabcut_iterations=4,
        min_area=100,
    )

    assert result.feedback["mode"] == "grabcut"
    assert result.feedback["segmentation"]["foreground_pixels"] > 8_000
    assert len(result) == 1
    assert len(result[0]["polygon"]) >= 4
    assert isinstance(result[0]["holes"], list)


def test_grabcut_rejects_missing_or_invalid_roi() -> None:
    image = _image_with_subject()
    with pytest.raises(ValueError, match="requires an roi"):
        detect_polygons(image, mode="grabcut")
    with pytest.raises(ValueError, match="does not intersect"):
        normalize_roi((500, 500, 10, 10), image.shape[:2])


def test_segmentation_input_contracts_and_all_components() -> None:
    image = _image_with_subject()
    rgba = np.dstack([image, np.full(image.shape[:2], 255, dtype=np.uint8)])
    assert segmentation._uint8_image(rgba).shape == image.shape
    assert segmentation._uint8_image(np.full((3, 3), 4.0)).max() == 0
    assert segmentation._uint8_image(np.full((3, 3), 500.0)).max() == 0

    with pytest.raises(ValueError, match="grayscale, RGB"):
        segmentation._validate_image(np.zeros((2, 2, 2), dtype=np.uint8))
    with pytest.raises(ValueError, match="dtype must be numeric"):
        segmentation._validate_image(np.zeros((2, 2), dtype=object))
    with pytest.raises(ValueError, match="iterations must be between"):
        segment_grabcut(image, (30, 20, 160, 140), iterations=21)
    with pytest.raises(ValueError, match="keep_components"):
        segment_grabcut(image, (30, 20, 160, 140), keep_components="invalid")
    all_components = segment_grabcut(image, (30, 20, 160, 140), keep_components="all")
    assert all_components.components >= 1


def test_segmentation_roi_and_contour_contracts() -> None:
    with pytest.raises(ValueError, match="x, y, width"):
        normalize_roi((1, 2, 3), (10, 10))
    with pytest.raises(ValueError, match="non-negative"):
        normalize_roi((1, 2, 3, 3), (10, 10), padding=-1)
    with pytest.raises(ValueError, match="width and height"):
        normalize_roi((1, 2, 0, 3), (10, 10))
    mask = np.zeros((30, 30), dtype=np.uint8)
    cv2.rectangle(mask, (3, 3), (26, 26), 255, -1)
    cv2.rectangle(mask, (10, 10), (18, 18), 0, -1)
    contours, hierarchy = segmentation.mask_contours(mask, include_holes=True)
    assert len(contours) == 2
    assert hierarchy is not None
    with pytest.raises(ValueError, match="two-dimensional"):
        segmentation.mask_contours(np.zeros((2, 2, 1), dtype=np.uint8))


def test_collision_strategies_and_normalized_failures() -> None:
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object(
        "concave",
        [(0, 0), (100, 0), (100, 30), (40, 30), (40, 100), (0, 100)],
        select=False,
    )
    with pytest.raises(ValueError, match="strategy"):
        AutoGenerateCollisionShapesCommand("bad")
    hull_command = AutoGenerateCollisionShapesCommand("convex_hull")
    assert scene.cmd.execute(hull_command, scene).changed
    assert len(scene.collision_shapes["concave"]) < 6
    decomposition = AutoGenerateCollisionShapesCommand("convex_decomposition")
    assert scene.cmd.execute(decomposition, scene).changed
    assert decomposition.generated_part_count >= 2
    assert scene.cmd.undo(scene).changed
    assert scene.cmd.redo(scene).changed
    with pytest.raises(ValueError, match="image_size"):
        export_collision_document(scene, coordinate_space="normalized")
    with pytest.raises(ValueError, match="unsupported"):
        collision_shape_record(scene, "concave", coordinate_space="world")


def test_compound_collision_is_consumed_exported_and_persisted(tmp_path: Path) -> None:
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object(
        "concave",
        [(0, 0), (100, 0), (100, 30), (40, 30), (40, 100), (0, 100)],
        select=False,
    )
    command = AutoGenerateCollisionShapesCommand("convex_decomposition")
    result = scene.cmd.execute(command, scene)

    assert result.changed
    assert len(scene.collision_parts["concave"]) == 2
    document = export_collision_document(
        scene, coordinate_space="normalized", image_size=(100, 100)
    )
    record = document["shapes"][0]
    assert record["shape_type"] == "compound"
    assert len(record["parts"]) == 2
    assert record["parts"][0][1] == [1.0, 0.0]

    path = tmp_path / "compound.ndtproj"
    save_scene_project(scene, path)
    restored = Scene()
    load_project_into_scene(restored, path)
    assert restored.collision_parts == scene.collision_parts


def test_mask_viewer_roi_and_layers_are_rendered(qapp: QApplication) -> None:
    viewer = MaskViewer()
    viewer.resize(240, 200)
    image = _image_with_subject()
    viewer.set_numpy_image(image)
    viewer.set_layer_overlays({"Canny": True}, 1.0)
    viewer._get_qimage()
    assert viewer._composed_image is not None
    assert not np.array_equal(viewer._composed_image, image)

    selected: list[tuple[int, int, int, int]] = []
    viewer.roiSelected.connect(selected.append)
    viewer._roi_start = QPointF(10, 10)
    viewer._update_roi(QPointF(130, 120))
    roi = viewer.get_roi()
    assert roi is not None
    assert roi[2] > 0 and roi[3] > 0
    viewer.roiSelected.emit(roi)
    assert selected == [roi]


def test_segmentation_rejects_limits_and_normalizes_numeric_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = _image_with_subject()
    with pytest.raises(TypeError, match="numpy.ndarray"):
        segmentation._validate_image("not-an-image")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dimensions must be positive"):
        segmentation._validate_image(np.zeros((0, 2), dtype=np.uint8))
    with pytest.raises(ValueError, match="dimensions cannot exceed"):
        monkeypatch.setattr(segmentation, "MAX_IMAGE_DIMENSION", 2)
        segmentation._validate_image(np.zeros((3, 2), dtype=np.uint8))
    monkeypatch.setattr(segmentation, "MAX_IMAGE_DIMENSION", 10000)
    with pytest.raises(ValueError, match="pixel limit"):
        monkeypatch.setattr(segmentation, "MAX_IMAGE_PIXELS", 2)
        segmentation._validate_image(np.zeros((2, 2), dtype=np.uint8))
    monkeypatch.setattr(segmentation, "MAX_IMAGE_PIXELS", 100_000_000)
    with pytest.raises(ValueError, match="decoded byte limit"):
        monkeypatch.setattr(segmentation, "MAX_DECODED_IMAGE_BYTES", 2)
        segmentation._validate_image(image)
    monkeypatch.setattr(segmentation, "MAX_DECODED_IMAGE_BYTES", 512 * 1024 * 1024)
    with pytest.raises(ValueError, match="image must be"):
        segmentation._validate_image(np.zeros((2, 2, 1), dtype=np.uint8))
    assert segmentation._uint8_image(
        np.arange(9, dtype=np.float32).reshape(3, 3)
    ).shape == (3, 3, 3)
    assert (
        segmentation._uint8_image(np.array([[-1.0, 2.0]], dtype=np.float32)).max()
        == 255
    )
    finite = segmentation._uint8_image(
        np.array([[np.nan, np.inf], [-np.inf, 4.0]], dtype=np.float32)
    )
    assert finite.dtype == np.uint8
    with pytest.raises(ValueError, match="padding"):
        normalize_roi((1, 1, 2, 2), image.shape[:2], padding=True)
    with pytest.raises(ValueError, match="padding"):
        normalize_roi(  # type: ignore[arg-type]
            (1, 1, 2, 2), image.shape[:2], padding="1"
        )
    with pytest.raises(ValueError, match="coordinates"):
        normalize_roi(("bad", 1, 2, 2), image.shape[:2])  # type: ignore[arg-type]


def test_segmentation_cleans_components_and_validates_mask_formats() -> None:
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[2:8, 2:8] = 255
    mask[12:16, 12:16] = 255
    largest = segmentation._clean_mask(mask, keep_components="largest")
    all_components = segmentation._clean_mask(mask, keep_components="all")
    assert np.count_nonzero(largest) < np.count_nonzero(all_components)
    with pytest.raises(ValueError, match="keep_components"):
        segmentation._clean_mask(mask, keep_components="bad")
    empty = segmentation._clean_mask(
        np.zeros((20, 20), dtype=np.uint8), keep_components="largest"
    )
    assert not np.any(empty)
    contours, hierarchy = segmentation.mask_contours(mask.astype(np.float32))
    assert contours and hierarchy is not None


def test_grabcut_validates_iteration_types_and_export_contracts() -> None:
    image = _image_with_subject()
    with pytest.raises(ValueError, match="integer"):
        segment_grabcut(image, (30, 20, 100, 100), iterations=True)
    with pytest.raises(ValueError, match="between"):
        segment_grabcut(image, (30, 20, 100, 100), iterations=0)
    with pytest.raises(ValueError, match="padding"):
        segment_grabcut(image, (30, 20, 100, 100), padding=-1)
    scene = Scene()
    scene.add_object("triangle", [(0, 0), (10, 0), (0, 10)], select=False)
    scene.collision_shapes["triangle"] = [(0, 0), (10, 0), (0, 10)]
    scene.collision_shapes["triangle"] = [(0, 0), (1, 1)]
    with pytest.raises(ValueError, match="three distinct"):
        collision_shape_record(scene, "triangle")
    scene.collision_shapes["triangle"] = [(0, 0), (10, 0), (0, 10)]
    with pytest.raises(ValueError, match="positive dimensions"):
        collision_shape_record(
            scene, "triangle", coordinate_space="normalized", image_size=(0, 0)
        )
    assert collision_shape_record(scene, "missing") is None


def test_mask_viewer_real_modes_layers_and_view_contracts(qapp: QApplication) -> None:
    viewer = MaskViewer()
    viewer.resize(240, 200)
    assert viewer._get_qimage() is None
    viewer.set_display_mode(3)
    viewer.set_roi_mode(True)
    viewer.clear_roi()
    viewer.set_roi_mode(False)
    viewer.set_zoom(100.0)
    assert viewer.get_zoom() == 8.0
    viewer.set_zoom(0.01)
    assert viewer.get_zoom() == 0.1

    image = _image_with_subject()
    viewer.set_numpy_image(image)
    for mode in (0, 1, 2, 3, 99, -1):
        viewer.set_display_mode(mode)
        assert viewer.get_display_mode() == max(0, min(3, mode))

    viewer.set_layer_overlays(
        {"Sobel": True, "Canny": True, "Threshold": True, "Watershed": True},
        opacity=2.0,
    )
    rendered = viewer._get_qimage()
    assert rendered is not None
    viewer.set_layer_overlays(
        {"Sobel": False, "Canny": False, "Threshold": False, "Watershed": False},
        opacity=-1.0,
    )
    assert viewer._get_qimage() is not None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rgba = np.dstack([image, np.full(image.shape[:2], 255, dtype=np.uint8)])
    assert segmentation._uint8_image(gray).shape == (*gray.shape, 3)
    assert viewer._compose_layer_overlays(gray).shape == (*gray.shape, 3)
    assert viewer._compose_layer_overlays(rgba).shape == image.shape

    viewer.set_overlay_polygons(
        [{"polygon": [(40, 30), (180, 30), (180, 150)]}, [(0, 0)]]
    )
    assert viewer._find_polygon_at(QPointF(80, 50)) == 0
    assert viewer._find_polygon_at(QPointF(10, 10)) == -1
    viewer.set_selected_polygon_index(0)
    viewer.set_selected_polygon_index(99)
    assert viewer.get_selected_polygon_index() == -1
    viewer.set_view_transform(2.0, 3.0, 4.0)
    assert viewer.get_view_transform() == (2.0, 3.0, 4.0)
    viewer.set_pan(-2.0, 5.0)
    assert viewer.get_pan() == (-2.0, 5.0)
    viewer.reset_view()
    viewer.set_numpy_image(None)
    viewer.reset_view()
    assert viewer.get_numpy_image() is None


def test_detection_worker_and_collision_document_real_contracts(
    qapp: QApplication, tmp_path: Path
) -> None:
    from src.exporters.collision_exporter import (
        render_collision_text,
        save_collision_text,
    )
    from src.ui.mask_viewer import DetectionWorker

    errors: list[str] = []
    empty_worker = DetectionWorker(None, "grabcut", {})
    empty_worker.error.connect(errors.append)
    empty_worker.run()
    assert errors == ["No image data provided to worker"]

    results: list[object] = []
    worker = DetectionWorker(
        _image_with_subject(),
        "grabcut",
        {"roi": (35, 25, 150, 130), "grabcut_iterations": 2, "min_area": 100},
    )
    worker.finished.connect(results.append)
    worker.run()
    assert len(results) == 1

    scene = Scene()
    scene.add_object("triangle", [(0, 0), (10, 0), (0, 10)], select=False)
    scene.collision_shapes["triangle"] = [(0, 0), (10, 0), (0, 10)]
    document = export_collision_document(
        scene,
        results=[
            {
                "obj1_id": "triangle",
                "obj2_id": "other",
                "colliding": True,
                "mtv": (1, 2),
            }
        ],
        statistics={"nested": {"z": 2, "a": [True, None]}},
    )
    assert document["results"][0]["mtv"] == [1.0, 2.0]
    assert "Object triangle:" in render_collision_text(document)
    output = tmp_path / "collision.txt"
    save_collision_text(document, str(output))
    assert output.read_text(encoding="utf-8").startswith("Object triangle:")

    invalid_results = [
        [1],
        [{"obj1_id": "", "obj2_id": "b", "colliding": True}],
        [{"obj1_id": "a", "obj2_id": "", "colliding": True}],
        [{"obj1_id": "a", "obj2_id": "b", "colliding": 1}],
        [{"obj1_id": "a", "obj2_id": "b", "colliding": True, "mtv": [1]}],
        [{"obj1_id": "a", "obj2_id": "b", "colliding": True, "mtv": [float("nan"), 1]}],
    ]
    for invalid in invalid_results:
        with pytest.raises(ValueError):
            export_collision_document(scene, results=invalid)  # type: ignore[arg-type]


def test_collision_export_rejects_malformed_geometry_and_statistics(
    tmp_path: Path,
) -> None:
    from src.exporters.collision_exporter import _normalize_json_value

    scene = Scene()
    scene.add_object("shape", [(0, 0), (10, 0), (0, 10)], select=False)
    scene.collision_shapes["shape"] = [(0, 0), (10, 0), (0, 10)]
    with pytest.raises(ValueError, match="image_size"):
        collision_shape_record(
            scene, "shape", coordinate_space="normalized", image_size=(10,)
        )
    scene.collision_shapes["shape"] = "bad"
    with pytest.raises(ValueError, match="sequence"):
        collision_shape_record(scene, "shape")
    scene.collision_shapes["shape"] = [(0, 0), (1, 1), (2, 2)]
    with pytest.raises(ValueError, match="non-zero area"):
        collision_shape_record(scene, "shape")
    scene.collision_shapes["shape"] = [(0, 0), (10, 0), (0, 10)]
    scene.collision_shapes["ghost"] = [(0, 0), (10, 0), (0, 10)]
    with pytest.raises(ValueError, match="unknown object"):
        collision_shape_record(scene, "ghost")
    del scene.collision_shapes["ghost"]
    with pytest.raises(ValueError, match="non-JSON"):
        _normalize_json_value(object(), "stats")
    with pytest.raises(ValueError, match="finite"):
        _normalize_json_value(float("inf"), "stats")
    with pytest.raises(ValueError, match="finite"):
        export_collision_document(
            scene,
            results=[
                {"obj1_id": "a", "obj2_id": "b", "colliding": True, "mtv": [True, 1]}
            ],
        )
    output = tmp_path / "nested" / "collision.txt"
    document = export_collision_document(scene, results=[])
    save_collision_text(document, str(output))
    assert output.exists()


def test_mask_viewer_real_mouse_and_keyboard_events(qapp: QApplication) -> None:
    from PySide6.QtCore import QEvent, QPoint, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent

    viewer = MaskViewer()
    viewer.resize(240, 200)
    viewer.set_numpy_image(_image_with_subject())

    def mouse_event(
        event_type: QEvent.Type,
        button: Qt.MouseButton,
        x: float,
        y: float,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ) -> QMouseEvent:
        return QMouseEvent(
            event_type,
            QPointF(x, y),
            QPointF(x, y),
            QPointF(x, y),
            button,
            button,
            modifiers,
        )

    viewer.set_roi_mode(True)
    viewer.mousePressEvent(
        mouse_event(QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton, 20, 20)
    )
    viewer.mouseMoveEvent(
        mouse_event(QEvent.Type.MouseMove, Qt.MouseButton.LeftButton, 80, 80)
    )
    viewer.mouseReleaseEvent(
        mouse_event(QEvent.Type.MouseButtonRelease, Qt.MouseButton.LeftButton, 80, 80)
    )
    viewer.set_roi_mode(False)

    viewer.mousePressEvent(
        mouse_event(QEvent.Type.MouseButtonPress, Qt.MouseButton.MiddleButton, 20, 20)
    )
    viewer.mouseMoveEvent(
        mouse_event(QEvent.Type.MouseMove, Qt.MouseButton.MiddleButton, 30, 35)
    )
    viewer.mouseReleaseEvent(
        mouse_event(QEvent.Type.MouseButtonRelease, Qt.MouseButton.MiddleButton, 30, 35)
    )
    viewer.mousePressEvent(
        mouse_event(
            QEvent.Type.MouseButtonPress,
            Qt.MouseButton.LeftButton,
            20,
            20,
            Qt.KeyboardModifier.ShiftModifier,
        )
    )
    viewer.mouseReleaseEvent(
        mouse_event(
            QEvent.Type.MouseButtonRelease,
            Qt.MouseButton.LeftButton,
            20,
            20,
            Qt.KeyboardModifier.ShiftModifier,
        )
    )
    viewer.tool_handler = lambda event: True
    viewer.mousePressEvent(
        mouse_event(QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton, 20, 20)
    )
    viewer.tool_handler = None
    viewer.mousePressEvent(
        mouse_event(QEvent.Type.MouseButtonPress, Qt.MouseButton.RightButton, 20, 20)
    )

    def wheel(
        delta: int, modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier
    ) -> QWheelEvent:
        return QWheelEvent(
            QPointF(40, 40),
            QPointF(40, 40),
            QPoint(0, 0),
            QPoint(0, delta),
            Qt.MouseButton.NoButton,
            modifiers,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )

    viewer.wheelEvent(wheel(0))
    viewer.wheelEvent(wheel(120))
    viewer.wheelEvent(wheel(-120, Qt.KeyboardModifier.ControlModifier))
    viewer.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_R, Qt.KeyboardModifier.NoModifier)
    )
    viewer.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
    )


def test_roi_clamping_and_empty_overlay_path(qapp: QApplication) -> None:
    assert normalize_roi((-2, -3, 10, 10), (20, 20), padding=2) == (0, 0, 10, 9)
    viewer = MaskViewer()
    viewer.set_layer_overlays({"Threshold": True}, opacity=0.5)
    blank = np.zeros((20, 20, 3), dtype=np.uint8)
    composed = viewer._compose_layer_overlays(blank)
    assert composed.shape == blank.shape


def test_roi_boundary_clamps_right_and_bottom_edges() -> None:
    assert normalize_roi((18, 18, 5, 5), (20, 20)) == (18, 18, 2, 2)


def test_collision_export_rejects_non_numeric_and_malformed_points() -> None:
    scene = Scene()
    scene.add_object("shape", [(0, 0), (10, 0), (0, 10)], select=False)
    scene.collision_shapes["shape"] = [(0, 0), (10, 0), ("bad",)]
    with pytest.raises(ValueError, match="point 2 must contain"):
        collision_shape_record(scene, "shape")
    scene.collision_shapes["shape"] = [(0, 0), (10, 0), (None, 2)]
    with pytest.raises(ValueError, match="finite number"):
        collision_shape_record(scene, "shape")


def test_collision_text_supports_flat_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scene = Scene()
    scene.add_object("shape", [(0, 0), (10, 0), (0, 10)], select=False)
    scene.collision_shapes["shape"] = [(0, 0), (10, 0), (0, 10)]
    document = export_collision_document(scene)
    monkeypatch.chdir(tmp_path)
    save_collision_text(document, "flat.txt")
    assert (tmp_path / "flat.txt").exists()
