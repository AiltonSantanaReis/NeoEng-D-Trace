"""User-like functional flows for the production editor surface.

These tests intentionally use the real ``MainWindow``, ``ToolPalette`` and
``CanvasView`` with Qt mouse/key events.  They complement the unit and
contract suites; activating a QAction alone is not considered proof that a
tool can complete an operation.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QToolButton

import src.tools.base_tool as base_tool_module
import src.ui.main_window as main_window_module
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _Config:
    def get(self, key: str, default=None):
        del key
        return default

    def set(self, key: str, value) -> None:
        del key, value

    def save(self) -> None:
        return None


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _settle(app: QApplication, milliseconds: int = 80) -> None:
    app.processEvents()
    QTest.qWait(milliseconds)
    app.processEvents()


def _wait_until(app: QApplication, predicate, timeout_ms: int = 8_000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        if predicate():
            return True
        _settle(app, 25)
    return bool(predicate())


def _make_window(tmp_path: Path, qt_app: QApplication) -> MainWindow:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "user-flow-source.png"
    pixels = np.zeros((220, 320, 4), dtype=np.uint8)
    pixels[:, :, :3] = (24, 28, 38)
    pixels[:, :, 3] = 255
    pixels[40:100, 40:100, :3] = (235, 235, 235)
    pixels[40:100, 40:100, 3] = 255
    pixels[118:184, 132:212, :3] = (44, 170, 220)
    Image.fromarray(pixels, "RGBA").save(source)

    scene = Scene()
    scene.cmd = CommandManager(max_history=40)
    scene.image = pixels
    scene.image_path = str(source)
    scene.add_object(
        "seed",
        [(40, 40), (100, 40), (100, 100), (40, 100)],
        select=False,
    )
    scene.cmd.clear()

    window = MainWindow(scene, _Config())
    window._refresh_document_views(project_loaded=False)
    window.show()
    window.activateWindow()
    window.canvas.setFocus()
    _settle(qt_app)
    return window


def _screen_point(window: MainWindow, point: tuple[int, int]) -> QPoint:
    converted = window.canvas.image_to_widget(*point)
    return QPoint(round(converted.x()), round(converted.y()))


def _click_image(
    window: MainWindow,
    point: tuple[int, int],
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    QTest.mouseClick(
        window.canvas,
        Qt.MouseButton.LeftButton,
        modifiers,
        _screen_point(window, point),
    )


def _drag_image(
    window: MainWindow,
    points: list[tuple[int, int]],
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    if len(points) < 2:
        raise ValueError("a drag requires at least two points")
    canvas = window.canvas
    QTest.mousePress(
        canvas,
        Qt.MouseButton.LeftButton,
        modifiers,
        _screen_point(window, points[0]),
    )
    for point in points[1:]:
        QTest.mouseMove(canvas, _screen_point(window, point))
    QTest.mouseRelease(
        canvas,
        Qt.MouseButton.LeftButton,
        modifiers,
        _screen_point(window, points[-1]),
    )


def _close_clean(window: MainWindow, qt_app: QApplication) -> None:
    window._mark_document_clean()
    window.close()
    window.deleteLater()
    _settle(qt_app)


def _run_isolated(tmp_path: Path, qt_app: QApplication, operation) -> None:
    window = _make_window(tmp_path, qt_app)
    try:
        operation(window)
    finally:
        _close_clean(window, qt_app)


def test_every_palette_tool_completes_a_user_like_operation(
    tmp_path: Path, qt_app: QApplication
) -> None:
    def select(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["selection"].click()
        _click_image(window, (65, 65))
        assert window.scene.selected_id == "seed"

    def rectangle(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["rect_selection"].click()
        before = set(window.scene.objects)
        _drag_image(window, [(120, 35), (205, 95)])
        created = set(window.scene.objects) - before
        assert len(created) == 1
        assert len(window.scene.objects[next(iter(created))].polygon) == 4

    def ellipse(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["ellipse_selection"].click()
        before = set(window.scene.objects)
        _drag_image(window, [(140, 125), (195, 175)])
        created = set(window.scene.objects) - before
        assert len(created) == 1
        assert len(window.scene.objects[next(iter(created))].polygon) == 64

    def lasso(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["lasso_tool"].click()
        before = set(window.scene.objects)
        _drag_image(
            window,
            [(125, 35), (185, 35), (205, 90), (145, 105), (125, 35)],
        )
        assert len(set(window.scene.objects) - before) == 1

    def polygonal_lasso(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["polygonal_lasso"].click()
        before = set(window.scene.objects)
        for point in [(120, 120), (205, 120), (205, 185)]:
            _click_image(window, point)
        _click_image(window, (120, 120))
        assert len(set(window.scene.objects) - before) == 1

    def magnetic_lasso(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["magnetic_lasso"].click()
        tool = window.tool_palette._active_magnetic_lasso
        assert tool is not None
        assert _wait_until(qt_app, lambda: tool._edge_map is not None)
        before = set(window.scene.objects)
        for point in [(40, 40), (100, 40), (100, 100)]:
            _click_image(window, point)
            assert _wait_until(qt_app, lambda: not tool._segment_pending)
        _click_image(window, (40, 40))
        assert _wait_until(
            qt_app,
            lambda: len(set(window.scene.objects) - before) == 1
            and not tool._anchors
            and not tool._segment_pending,
        )

    def pen(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["pen_tool"].click()
        before = set(window.scene.objects)
        # Simple clicks create corners; the size/zoom regression matrix lives
        # in test_pen_creation_gestures.py, including the former 60 px failure.
        _click_image(window, (225, 35))
        _click_image(window, (305, 35))
        _click_image(window, (305, 115))
        _click_image(window, (225, 35))
        _settle(qt_app)
        created = set(window.scene.objects) - before
        assert len(created) == 1
        beziers = window.scene.objects[next(iter(created))].beziers
        assert beziers is not None
        assert beziers[-1][3] == beziers[0][0]

    def polygon_edit(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["polygon_edit"].click()
        _click_image(window, (65, 65))
        if window.act_gizmo.isChecked():
            window.act_gizmo.trigger()
        original = tuple(window.scene.objects["seed"].polygon[0])
        _drag_image(window, [(40, 40), (34, 44)])
        assert tuple(window.scene.objects["seed"].polygon[0]) != original

    def collision_brush(window: MainWindow) -> None:
        window.tool_palette.tool_buttons["collision_brush"].click()
        _click_image(window, (65, 65))
        assert window.scene.has_collision("seed")
        assert window.scene.cmd.undo(window.scene).changed
        assert not window.scene.has_collision("seed")

    cases = (
        select,
        rectangle,
        ellipse,
        lasso,
        polygonal_lasso,
        magnetic_lasso,
        pen,
        polygon_edit,
        collision_brush,
    )
    for index, operation in enumerate(cases):
        _run_isolated(tmp_path / f"tool-{index}", qt_app, operation)


def test_pen_invalid_close_preserves_preview_and_history(
    tmp_path: Path, qt_app: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejected close must leave the in-progress gesture and model untouched."""

    monkeypatch.setattr(
        base_tool_module.QMessageBox,
        "warning",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok,
    )
    window = _make_window(tmp_path, qt_app)
    try:
        window.tool_palette.tool_buttons["pen_tool"].click()
        tool = window.canvas._active_tool_object()
        before_objects = set(window.scene.objects)
        before_history = window.scene.cmd.undo_count
        # Collinear anchors are genuinely invalid. The former 60 px triangle
        # is now a positive regression, not an invalid-polygon fixture.
        for point in ((225, 35), (265, 35), (305, 35)):
            _click_image(window, point)
        before_nodes = tuple(node.anchor for node in tool._nodes)

        _click_image(window, (225, 35))
        _settle(qt_app)

        assert set(window.scene.objects) == before_objects
        assert tuple(node.anchor for node in tool._nodes) == before_nodes
        assert tool._editing_object_id is None
        assert window.scene.cmd.undo_count == before_history
        assert "Invalid sampled" in tool._last_error
    finally:
        _close_clean(window, qt_app)


def test_user_flow_persists_and_exports_through_main_window_actions(
    tmp_path: Path, qt_app: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    window = _make_window(tmp_path, qt_app)
    project = tmp_path / "user-flow.ndtproj"
    collision_export = tmp_path / "user-flow-collisions.json"
    reopened = None
    try:
        window.tool_palette.tool_buttons["rect_selection"].click()
        before = set(window.scene.objects)
        _drag_image(window, [(120, 35), (205, 95)])
        created = set(window.scene.objects) - before
        assert len(created) == 1
        created_id = next(iter(created))

        window.tool_palette.tool_buttons["collision_brush"].click()
        if window.act_gizmo.isChecked():
            window.act_gizmo.trigger()
        _click_image(window, (160, 65))
        assert window.scene.has_collision(created_id)

        window._project_path = project
        window.save_project_action.trigger()
        _settle(qt_app)
        assert project.is_file()

        monkeypatch.setattr(
            main_window_module.QFileDialog,
            "getSaveFileName",
            lambda *_args, **_kwargs: (str(collision_export), "JSON"),
        )
        monkeypatch.setattr(
            main_window_module.QMessageBox,
            "information",
            lambda *_args, **_kwargs: None,
        )
        window.act_export_collision_json.trigger()
        _settle(qt_app)
        assert collision_export.is_file()
        assert '"schema_version"' in collision_export.read_text(encoding="utf-8")
    finally:
        _close_clean(window, qt_app)

    reopened_scene = Scene()
    reopened = MainWindow(reopened_scene, _Config())
    reopened.show()
    _settle(qt_app)
    try:
        monkeypatch.setattr(
            main_window_module.QFileDialog,
            "getOpenFileName",
            lambda *_args, **_kwargs: (str(project), "NDT Project"),
        )
        monkeypatch.setattr(
            main_window_module.QMessageBox,
            "warning",
            lambda *_args, **_kwargs: None,
        )
        reopened.open_project_action.trigger()
        _settle(qt_app)
        assert created_id in reopened.scene.objects
        assert reopened.scene.has_collision(created_id)
        assert reopened.scene.image is not None
        assert reopened.tool_palette.isEnabled()
    finally:
        _close_clean(reopened, qt_app)


def test_auxiliary_rail_actions_complete_user_like_flows(
    tmp_path: Path, qt_app: QApplication
) -> None:
    """Exercise validation and navigation through the real rail actions."""

    window = _make_window(tmp_path, qt_app)
    try:
        window.tool_palette.tool_buttons["collision_brush"].click()
        _click_image(window, (65, 65))
        assert window.scene.has_collision("seed")
        assert "seed" in window.collision_manager.objects

        navigation = window.tool_palette.navigation_actions
        navigation["validation"].trigger()
        panel_tabs = [
            tabs
            for tabs in (window.compact_panel_tabs, window.reference_panel_tabs)
            if tabs.indexOf(window.collision_panel) >= 0
        ]
        assert panel_tabs
        assert any(
            tabs.currentWidget() is window.collision_panel
            and window.collision_panel.isVisible()
            for tabs in panel_tabs
        )
        assert "seed" in window.collision_manager.objects

        navigation["fit_view"].trigger()
        before_zoom = window.canvas.get_zoom()
        navigation["zoom_viewport"].trigger()
        assert window.canvas.get_zoom() > before_zoom

        navigation["fit_view"].trigger()
        before_pan = (window.canvas._pan.x(), window.canvas._pan.y())
        navigation["move_viewport"].trigger()
        assert window.canvas.is_pan_mode()
        start = QPoint(window.canvas.width() // 2, window.canvas.height() // 2)
        end = QPoint(start.x() + 45, start.y() + 25)
        QTest.mousePress(
            window.canvas,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            start,
        )
        QTest.mouseMove(window.canvas, end)
        QTest.mouseRelease(
            window.canvas,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            end,
        )
        _settle(qt_app, 50)
        after_pan = (window.canvas._pan.x(), window.canvas._pan.y())
        assert after_pan != before_pan
        navigation["move_viewport"].trigger()
        assert not window.canvas.is_pan_mode()

        window.tool_palette.tool_buttons["selection"].click()
        _click_image(window, (65, 65))
        assert list(window.scene.selected_ids) == ["seed"]
        before_focus = (window.canvas._pan.x(), window.canvas._pan.y())
        navigation["focus_selected"].trigger()
        after_focus = (window.canvas._pan.x(), window.canvas._pan.y())
        assert after_focus != before_focus
    finally:
        _close_clean(window, qt_app)


def test_reference_shell_preserves_control_geometry_and_tool_visibility(
    tmp_path: Path, qt_app: QApplication
) -> None:
    """Every supported shell size keeps controls and the complete tool rail usable."""

    window = _make_window(tmp_path / "responsive-shell", qt_app)
    try:
        top_controls = tuple(
            getattr(window, name)
            for name in (
                "reference_fit_button",
                "reference_focus_button",
                "reference_pan_button",
                "reference_undo_button",
                "reference_redo_button",
            )
        )
        for width, height in ((1280, 720), (1366, 768), (1920, 1080)):
            window.resize(width, height)
            _settle(qt_app)
            for button in top_controls:
                assert button.isVisible()
                assert button.width() >= button.minimumSizeHint().width()
                assert button.height() >= button.minimumSizeHint().height()

        rail_buttons = [
            button
            for button in window.reference_tool_palette.findChildren(QToolButton)
            if button.property("uiRole") == "reference_tool"
        ]
        expected_rail_buttons = sum(
            not action.isSeparator() for action in window.tool_palette.actions()
        )
        assert len(rail_buttons) == expected_rail_buttons
        assert all(button.isVisible() for button in rail_buttons)
        assert all(button.iconSize().width() >= 22 for button in rail_buttons)
    finally:
        _close_clean(window, qt_app)
