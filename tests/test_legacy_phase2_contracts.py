"""Phase 2 replacement contracts for geometry, export and viewport cases."""

from __future__ import annotations

import copy
import math

import numpy as np
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from src.core.bezier_geometry import canonicalize_beziers
from src.core.commands import (
    CommandStatus,
    CreateBezierObjectCommand,
    HandleMoveCommand,
)
from src.core.convex_decomp import (
    convex_decompose_polygon,
    is_convex_polygon,
    polygon_area,
    triangulate_to_convex,
)
from src.exporters.atlas_exporter import pack_sprites_to_atlas
from src.tools.edge_utils import sobel_magnitude
from src.tools.mask_utils import curvature_adaptive_simplify
from src.ui.mask_viewer import MaskViewer
from tests.legacy_phase1_fixtures import POLYGON_FIXTURES, real_scene


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    """Use one real Qt application for all Phase 2 viewport assertions."""

    return QApplication.instance() or QApplication([])


def _fixture(name: str):
    return next(item for item in POLYGON_FIXTURES if item.name == name)


def _circle_contour(point_count: int = 32) -> np.ndarray:
    points = []
    for index in range(point_count):
        angle = 2 * np.pi * index / point_count
        points.append((int(50 + 30 * np.cos(angle)), int(50 + 30 * np.sin(angle))))
    return np.asarray(points).reshape(-1, 1, 2)


def test_phase2_case_01_valid_l_decomposes_without_losing_area() -> None:
    """Case #1 uses a real simple L and preserves strict convex output."""

    polygon = list(_fixture("valid_l_shape").points)
    pieces = convex_decompose_polygon(polygon)

    assert len(pieces) >= 2
    assert all(len(piece) <= 8 and is_convex_polygon(piece) for piece in pieces)
    assert math.isclose(
        sum(polygon_area(piece) for piece in pieces),
        polygon_area(polygon),
        rel_tol=0.0,
        abs_tol=1e-9,
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_phase2_case_02_triangulation_preserves_valid_l_geometry(reverse: bool) -> None:
    """Case #2 accepts both windings but never weakens invalid-geometry checks."""

    polygon = list(_fixture("valid_l_shape").points)
    if reverse:
        polygon.reverse()

    triangles = triangulate_to_convex(polygon)

    assert len(triangles) == len(polygon) - 2
    assert all(
        len(triangle) == 3 and polygon_area(triangle) > 0 for triangle in triangles
    )
    assert math.isclose(
        sum(polygon_area(triangle) for triangle in triangles),
        polygon_area(polygon),
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def test_phase2_case_02_self_intersection_remains_rejected() -> None:
    invalid_polygon = list(_fixture("invalid_self_overlapping").points)

    with pytest.raises(ValueError, match="preserve polygon geometry"):
        convex_decompose_polygon(invalid_polygon)


def test_phase2_case_03_sobel_contract_is_float32_finite_and_unclipped() -> None:
    image = np.zeros((24, 32), dtype=np.uint8)
    image[3:21, 15:17] = 255
    image[11:13, 3:29] = 180

    magnitude = sobel_magnitude(image)

    assert magnitude.dtype == np.float32
    assert magnitude.shape == image.shape
    assert np.isfinite(magnitude).all()
    assert float(magnitude.max()) > 255.0


def test_phase2_case_04_rotated_atlas_preserves_rect_and_derivable_uv() -> None:
    image = Image.new("RGBA", (3, 5), (23, 47, 71, 255))

    [(atlas, entries)] = pack_sprites_to_atlas(
        [(image, {"name": "rotated-fixture"})],
        max_size=(5, 4),
        padding=0,
        allow_rotate=True,
    )

    entry = entries[0]
    packed = entry["packed_rect"]
    uv = (
        packed["x"] / atlas.width,
        packed["y"] / atlas.height,
        (packed["x"] + packed["w"]) / atlas.width,
        (packed["y"] + packed["h"]) / atlas.height,
    )

    assert len(entries) == 1
    assert atlas.size == (5, 3)
    assert entry["rotated"] is True
    assert entry["rect"] == {"x": 0, "y": 0, "w": 5, "h": 3}
    assert packed == {"x": 0, "y": 0, "w": 5, "h": 3}
    assert uv == (0.0, 0.0, 1.0, 1.0)
    assert entry["extrusion"] == 0


def test_phase2_case_05_real_bezier_history_round_trips_valid_geometry() -> None:
    beziers = [((0, 0), (0, -100), (100, -100), (100, 0))]
    scene = real_scene()
    created = scene.cmd.execute(
        CreateBezierObjectCommand(beziers, object_id="CURVE"), scene
    )
    assert created.status is CommandStatus.APPLIED
    scene.cmd.clear()

    before = copy.deepcopy(scene.objects["CURVE"].__dict__)
    moved = scene.cmd.execute(
        HandleMoveCommand("CURVE", 0, 1, (0, -100), (15.0, -125.0)), scene
    )
    assert moved.status is CommandStatus.APPLIED
    after = copy.deepcopy(scene.objects["CURVE"].__dict__)
    assert after != before
    assert scene.objects["CURVE"].beziers[0][1] == (15.0, -125.0)

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["CURVE"].__dict__ == before
    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene.objects["CURVE"].__dict__ == after
    assert scene.objects["CURVE"].beziers == canonicalize_beziers(
        [((0, 0), (15.0, -125.0), (100, -100), (100, 0))]
    )


def test_phase2_case_05_invalid_bezier_is_rejected_without_history() -> None:
    scene = real_scene()
    before = (copy.deepcopy(scene.objects), scene.selected_id, scene.cmd.undo_count)
    collinear = [((0, 0), (10, 0), (20, 0), (30, 0))]

    result = scene.cmd.execute(
        CreateBezierObjectCommand(collinear, object_id="INVALID"), scene
    )

    assert result.status is CommandStatus.REJECTED
    assert scene.objects == before[0]
    assert scene.selected_id == before[1]
    assert scene.cmd.undo_count == before[2]


def test_phase2_case_23_min_points_is_explicit_and_default_stays_permissive() -> None:
    contour = _circle_contour()

    default_result = curvature_adaptive_simplify(
        contour, base_eps=5.0, curvature_factor=1.0
    )
    guarded_result = curvature_adaptive_simplify(
        contour, base_eps=5.0, curvature_factor=1.0, min_points=8
    )

    assert len(default_result) >= 3
    assert 8 <= len(guarded_result) < len(contour)
    assert all(len(point) == 2 for point in guarded_result)


@pytest.mark.parametrize(
    ("widget_size", "image_shape", "expected"),
    [
        ((400, 300), (200, 300), (1.5, -25.0, 0.0)),
        ((300, 400), (200, 300), (2.0, -150.0, 0.0)),
        ((400, 300), (300, 200), (2.0, 0.0, -150.0)),
    ],
)
def test_phase2_case_24_reset_view_uses_real_fit_and_center(
    qt_app: QApplication,
    widget_size: tuple[int, int],
    image_shape: tuple[int, int],
    expected: tuple[float, float, float],
) -> None:
    viewer = MaskViewer()
    viewer.resize(*widget_size)
    viewer.set_numpy_image(np.zeros((*image_shape, 3), dtype=np.uint8))
    viewer.reset_view()

    assert viewer.get_view_transform() == expected
    viewer.close()
