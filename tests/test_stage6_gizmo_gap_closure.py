"""Stage 6 gap-closure tests for vertex gizmo and main-panel transforms."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.tools.polygon_edit_tool import PolygonEditTool
from src.ui.canvas_view import CanvasView
from src.ui.gizmo import TransformGizmo
from src.ui.side_panel import SidePanel


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    scene.add_object(
        "object", [(20, 20), (180, 20), (180, 160), (20, 160)], select=True
    )
    scene.select_object("object")
    return scene


def test_transform_gizmo_reference_contract_is_headless(qt_app):
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(120, 90))

    assert gizmo.available_handles() == (
        gizmo.AXIS_X,
        gizmo.AXIS_Y,
        gizmo.TRANSLATE_XY,
        gizmo.ROTATE_Z,
        gizmo.CENTER,
        gizmo.SCALE_UNIFORM,
        gizmo.SCALE_X,
        gizmo.SCALE_Y,
    )
    assert gizmo.handle_name(999) == "No gizmo handle"
    assert gizmo.handle_tooltip(gizmo.AXIS_X).endswith(" (drag)")
    assert gizmo.visual_bounds(4).contains(QPointF(120, 90))
    assert gizmo.hit_test(QPointF(120, 90)) == gizmo.CENTER
    assert gizmo.hit_test(QPointF(130, 90)) == gizmo.SCALE_UNIFORM
    assert gizmo.hit_test(QPointF(196, 90)) == gizmo.SCALE_X
    assert gizmo.hit_test(QPointF(120, 14)) == gizmo.SCALE_Y
    assert gizmo.hit_test(QPointF(132, 82)) == gizmo.TRANSLATE_XY
    assert gizmo.hit_test(QPointF(150, 90)) == gizmo.AXIS_X
    assert gizmo.hit_test(QPointF(120, 60)) == gizmo.AXIS_Y
    assert gizmo.hit_test(QPointF(120, 120)) == gizmo.AXIS_Y
    assert gizmo.hit_test(QPointF(156, 126)) == gizmo.ROTATE_Z
    assert gizmo.hit_test(QPointF(300, 300)) == gizmo.NONE
    assert gizmo._distance_to_segment(QPointF(2, 3), QPointF(0, 0), QPointF(0, 0))
    assert gizmo.update_hover(QPointF(150, 90)) is True
    assert gizmo.update_hover(QPointF(150, 90)) is False

    gizmo.active_axis = gizmo.ROTATE_Z
    gizmo.hover_axis = gizmo.SCALE_X
    gizmo.set_vertex_mode(True)
    assert gizmo.active_axis == gizmo.NONE
    assert gizmo.hover_axis == gizmo.NONE
    assert gizmo.available_handles() == (
        gizmo.AXIS_X,
        gizmo.AXIS_Y,
        gizmo.TRANSLATE_XY,
    )
    assert gizmo.hit_test(QPointF(132, 82)) == gizmo.TRANSLATE_XY
    assert gizmo.hit_test(QPointF(150, 90)) == gizmo.AXIS_X
    assert gizmo.hit_test(QPointF(120, 60)) == gizmo.AXIS_Y
    assert gizmo.hit_test(QPointF(300, 300)) == gizmo.NONE
    gizmo.set_vertex_mode(False)

    gizmo.active_axis = gizmo.AXIS_X
    assert gizmo._color(gizmo.AXIS_Y, gizmo.color_y).alpha() == 70
    assert gizmo._color(gizmo.AXIS_X, gizmo.color_x).alpha() == 255
    image = QImage(320, 240, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    gizmo.draw(painter)
    painter.end()
    assert not image.isNull()


def test_vertex_gizmo_exposes_only_xy_handles_and_anchors_selected_vertex(qt_app):
    scene = _scene()
    view = CanvasView(scene)
    tool = PolygonEditTool(view)
    view.set_tool(tool.interface())
    view.gizmo = TransformGizmo()
    view._gizmo_enabled = True
    tool.selected_polygon_id = "object"
    tool.selected_vertex = 0
    view.resize(320, 240)
    view.show()
    qt_app.processEvents()
    try:
        target = view._selected_vertex_target()
        assert target == ("object", 0, (20.0, 20.0))
        anchor = view._selection_anchor_image()
        assert anchor == QPointF(20.0, 20.0)
        view._update_gizmo_screen_position()
        view.gizmo.set_vertex_mode(True)
        assert set(view.gizmo.available_handles()) == {
            view.gizmo.AXIS_X,
            view.gizmo.AXIS_Y,
            view.gizmo.TRANSLATE_XY,
        }
        assert (
            view.gizmo.hit_test(
                QPointF(view.gizmo.screen_pos.x() + 51, view.gizmo.screen_pos.y())
            )
            == view.gizmo.AXIS_X
        )
        assert (
            view.gizmo.hit_test(
                QPointF(view.gizmo.screen_pos.x(), view.gizmo.screen_pos.y() - 51)
            )
            == view.gizmo.AXIS_Y
        )
        assert (
            view.gizmo.hit_test(
                QPointF(view.gizmo.screen_pos.x() + 4, view.gizmo.screen_pos.y() - 8)
            )
            == view.gizmo.TRANSLATE_XY
        )
        assert (
            view.gizmo.hit_test(
                QPointF(
                    view.gizmo.screen_pos.x() + view.gizmo.screen_pos.x(),
                    view.gizmo.screen_pos.y() - view.gizmo.rotation_radius,
                )
            )
            == view.gizmo.NONE
        )
    finally:
        view.close()


def test_vertex_gizmo_xy_preview_commit_undo_and_cancel_are_transactional(qt_app):
    scene = _scene()
    view = CanvasView(scene)
    tool = PolygonEditTool(view)
    view.set_tool(tool.interface())
    view.gizmo = TransformGizmo()
    view._gizmo_enabled = True
    tool.selected_polygon_id = "object"
    tool.selected_vertex = 0
    original = list(scene.objects["object"].polygon)
    try:
        view._gizmo_operation = view.gizmo.TRANSLATE_XY
        assert view._begin_gizmo_vertex_gesture() is True
        view._preview_gizmo_vertex(view.image_to_widget(37, 44))
        assert scene.objects["object"].polygon[0] == (37, 44)
        assert scene.cmd.undo_count == 0
        result = view._finish_gizmo_gesture()
        assert result is not None
        assert result.status is CommandStatus.APPLIED
        assert scene.cmd.undo_count == 1
        assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
        assert scene.objects["object"].polygon == original

        assert view._begin_gizmo_vertex_gesture() is True
        view._preview_gizmo_vertex(view.image_to_widget(41, 49))
        assert view._cancel_gizmo_gesture() is True
        assert scene.objects["object"].polygon == original
        assert scene.cmd.undo_count == 0
    finally:
        view.close()


def test_main_side_panel_numeric_transform_is_atomic_and_round_trips(qt_app):
    scene = _scene()
    view = CanvasView(scene)
    panel = SidePanel(scene, view)
    panel.show()
    qt_app.processEvents()
    try:
        assert panel.transform_group.isEnabled()
        assert panel.position_x.value() == pytest.approx(
            scene.objects["object"].position[0]
        )
        assert panel.rotation_z.value() == pytest.approx(0.0)
        original = list(scene.objects["object"].polygon)
        panel.position_x.setValue(100.0)
        panel.position_y.setValue(90.0)
        panel.position_z.setValue(12.0)
        panel.rotation_z.setValue(15.0)
        panel.scale_x.setValue(1.25)
        panel.scale_y.setValue(0.75)
        panel._on_apply_transform()
        obj = scene.objects["object"]
        assert tuple(obj.position) == pytest.approx((100.0, 90.0, 12.0))
        assert tuple(obj.rotation) == pytest.approx((0.0, 0.0, 15.0))
        assert tuple(obj.scale) == pytest.approx((1.25, 0.75, 1.0))
        assert obj.polygon != original
        assert scene.cmd.undo_count == 1
        assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
        assert scene.objects["object"].polygon == original
        assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
        assert tuple(scene.objects["object"].position) == pytest.approx(
            (100.0, 90.0, 12.0)
        )
    finally:
        panel.close()
        view.close()


def test_main_side_panel_disables_numeric_transform_without_selection(qt_app):
    scene = _scene()
    scene.select_object(None)
    view = CanvasView(scene)
    panel = SidePanel(scene, view)
    panel.show()
    qt_app.processEvents()
    try:
        assert panel.transform_group.isEnabled() is False
        assert panel.btn_apply_transform.isEnabled() is False
    finally:
        panel.close()
        view.close()
