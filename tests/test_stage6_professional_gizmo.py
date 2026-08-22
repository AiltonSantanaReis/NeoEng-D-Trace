"""Characterization and regression gates for the professional gizmo stage."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF, Qt

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.gizmo import TransformGizmo
from src.ui.scene_authoring_viewport import SceneTransformGizmo


@pytest.fixture(scope="module")
def qt_app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_handle_contract_is_unambiguous_and_describable():
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(100.0, 100.0))

    assert gizmo.CENTER != gizmo.SCALE_UNIFORM
    assert gizmo.hit_test(QPointF(100.0, 100.0)) == gizmo.CENTER
    assert gizmo.hit_test(QPointF(108.0, 100.0)) == gizmo.SCALE_UNIFORM
    assert gizmo.handle_name(gizmo.CENTER) == "Uniform scale center handle"
    assert gizmo.handle_tooltip(gizmo.ROTATE_Z).endswith("(drag)")
    assert set(gizmo.available_handles()) == {
        gizmo.AXIS_X,
        gizmo.AXIS_Y,
        gizmo.TRANSLATE_XY,
        gizmo.ROTATE_Z,
        gizmo.CENTER,
        gizmo.SCALE_UNIFORM,
        gizmo.SCALE_X,
        gizmo.SCALE_Y,
    }


def test_visual_bounds_are_shared_by_paint_and_layout():
    gizmo = TransformGizmo()
    gizmo.set_screen_position(QPointF(110.0, 90.0))
    bounds = gizmo.visual_bounds(margin=12.0)

    assert bounds.left() < 110.0 < bounds.right()
    assert bounds.top() < 90.0 < bounds.bottom()
    assert bounds.width() == pytest.approx(bounds.height())
    assert bounds.width() > 180.0


def test_canvas_clamps_gizmo_inside_small_viewport(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("edge", [(0, 0), (20, 0), (20, 20), (0, 20)], select=True)
    object_id = next(iter(scene.objects))
    scene.select_object(object_id)
    view = CanvasView(scene)
    view.gizmo = TransformGizmo()
    view._gizmo_enabled = True
    view.resize(320, 240)
    view.show()
    qt_app.processEvents()
    try:
        position = view._update_gizmo_screen_position()
        assert position is not None
        assert view.gizmo.visual_bounds().left() >= 0.0
        assert view.gizmo.visual_bounds().top() >= 0.0
        assert view.gizmo.visual_bounds().right() <= view.width()
        assert view.gizmo.visual_bounds().bottom() <= view.height()
    finally:
        view.close()


def test_multiple_selection_anchor_is_stable_for_gizmo(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("left", [(10, 10), (30, 10), (30, 30), (10, 30)])
    scene.add_object("right", [(40, 20), (60, 20), (60, 40), (40, 40)])
    scene.select_objects(["left", "right"], primary="left")
    view = CanvasView(scene)
    try:
        assert view._selected_object_ids() == ["left", "right"]
        anchor = view._selection_anchor_image()
        assert anchor is not None
        assert anchor.x() == pytest.approx(35.0)
        assert anchor.y() == pytest.approx(25.0)
    finally:
        view.close()


def test_gizmo_translation_snaps_from_original_anchor(qt_app):
    view = CanvasView(Scene())
    view.set_vertex_snapping(True, grid_size=4, origin=(0.0, 0.0))
    view._gizmo_anchor_image = (10.0, 10.0)

    assert view._snap_gizmo_translation((3.0, 5.0)) == (2.0, 6.0)
    view.close()


def test_keyboard_nudge_is_transactional_and_undoable(qt_app):
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("nudge", [(10, 10), (30, 10), (30, 30), (10, 30)], select=True)
    object_id = next(iter(scene.objects))
    scene.select_object(object_id)
    view = CanvasView(scene)
    view.gizmo = TransformGizmo()
    view._gizmo_enabled = True
    try:
        before = tuple(scene.objects[object_id].position)
        assert view._nudge_selected_with_gizmo(1.0, 0.0) is True
        after = tuple(scene.objects[object_id].position)
        assert after[0] == pytest.approx(before[0] + 1.0)
        assert scene.cmd.undo_count == 1
        assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
        assert tuple(scene.objects[object_id].position) == before
    finally:
        view.close()


def test_scenario_gizmo_rejects_empty_hit_area_and_exposes_hover():
    gizmo = SceneTransformGizmo()

    assert gizmo._mode_for(QPointF(40.0, 0.0)) == "rotate"
    assert gizmo._mode_for(QPointF(30.0, 30.0)) == "scale"
    assert gizmo._mode_for(QPointF(0.0, -30.0)) == "translate_y"
    assert gizmo._mode_for(QPointF(55.0, -20.0)) is None
    assert gizmo._mode_for(QPointF(100.0, 100.0)) is None


def test_scenario_gizmo_preserves_center_translation_contract():
    gizmo = SceneTransformGizmo()

    assert gizmo._mode_for(QPointF(0.0, 0.0)) == "translate"
    assert gizmo._mode_for(QPointF(30.0, 0.0)) == "translate_x"
    assert gizmo._mode_for(QPointF(0.0, -30.0)) == "translate_y"


def test_accessible_toggle_contract_is_present(qt_app):
    view = CanvasView(Scene())
    try:
        assert view.gizmo_toggle.accessibleName() == "Transform gizmo toggle"
        assert "interactive 2D" in view.gizmo_toggle.accessibleDescription()
        assert view.focusPolicy() == Qt.FocusPolicy.StrongFocus
    finally:
        view.close()
