from types import SimpleNamespace

import pytest

from src.core.snapping import SnapSettings, snap_point
from src.tools.polygon_edit_tool import PolygonEditTool


def test_pixel_and_grid_snap_use_half_up_rounding_and_origin() -> None:
    assert snap_point((1.5, 2.5)) == (2, 3)
    assert snap_point((11.9, 8.1), grid_size=4, origin=(1, 1)) == (13, 9)
    assert SnapSettings(enabled=False).apply((1.6, 2.4)) == (2, 2)
    assert SnapSettings(enabled=True, grid_size=4).apply((5.9, 2.1)) == (4, 4)


def test_snap_settings_reject_invalid_grid() -> None:
    with pytest.raises(ValueError, match="grid_size"):
        SnapSettings(enabled=True, grid_size=0)
    with pytest.raises(ValueError, match="finite"):
        snap_point((float("nan"), 0))


def test_polygon_edit_preview_uses_canvas_vertex_snap() -> None:
    class Transaction:
        active = True
        origin_polygon = [(0, 0), (1, 1), (4, 0)]

        def preview(self, polygon):
            self.previewed = polygon
            return polygon

    canvas = SimpleNamespace(
        snap_vertex_position=lambda position: (8, 12),
        update=lambda: None,
        model=SimpleNamespace(objects={}),
    )
    tool = PolygonEditTool(canvas)
    transaction = Transaction()
    tool._vertex_transaction = transaction
    tool._vertex_origin_index = 1

    tool._preview_vertex_position((3, 4))

    assert transaction.previewed == [(0, 0), (8, 12), (4, 0)]
    assert tool._vertex_preview_position == (8, 12)


def test_snapping_rejects_all_invalid_point_origin_and_numeric_inputs() -> None:
    for value in (True, "bad", float("inf")):
        with pytest.raises(ValueError):
            snap_point((value, 0))
    for point in ("xy", [1], [1, 2, 3]):
        with pytest.raises(ValueError, match="point"):
            snap_point(point)
    for origin in ("xy", [0], [0, 0, 0]):
        with pytest.raises(ValueError, match="origin"):
            snap_point((0, 0), origin=origin)
    for grid in (True, 0, -1, 1.5):
        with pytest.raises(ValueError, match="grid_size"):
            snap_point((0, 0), grid_size=grid)


def test_snap_settings_rejects_enabled_and_disabled_input_contracts() -> None:
    with pytest.raises(ValueError, match="enabled"):
        SnapSettings(enabled=1)
    with pytest.raises(ValueError, match="point"):
        SnapSettings(enabled=False).apply([1])
    with pytest.raises(ValueError, match="finite"):
        SnapSettings(enabled=False).apply((float("nan"), 0))
