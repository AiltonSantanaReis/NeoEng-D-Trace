from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image, ImageFont
from PySide6.QtCore import QPoint, QPointF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QResizeEvent,
    QTransform,
)
from PySide6.QtWidgets import QApplication, QWidget

from src.core.commands import CommandManager, CommandStatus
from src.models.scene import Scene
from src.tools.ellipse_selection import EllipseSelectionTool
from src.ui import canvas_view as canvas_view_module
from src.ui import export_dialog as export_dialog_module
from src.ui import export_preview as export_preview_module
from src.ui import tool_palette_commands as tool_palette_commands_module
from src.ui import viewport_settings as viewport_settings_module
from src.ui.canvas_view import CanvasView
from src.ui.export_dialog import ExportDialog
from src.ui.export_preview import ExportPreviewDialog, export_preview_headless
from src.ui.responsive_layout import ResponsivePanelLayout
from src.ui.tool_palette import ToolPalette
from src.utils import selection_tools as selection_tools_module


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class CanvasProbe:
    def __init__(self):
        self.model = Scene()
        self.model.cmd = CommandManager()
        self.updated = 0

    def update(self):
        self.updated += 1

    def get_transform(self):
        return QTransform()

    def image_to_widget(self, x, y):
        return QPointF(float(x), float(y))


class PaletteCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.scene = Mock()
        self.scene.get_image.return_value = np.zeros((16, 16), dtype=np.uint8)
        self.model = self.scene
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self.tool = None

    def get_zoom(self):
        return self._zoom

    def get_transform(self):
        return QTransform()

    def set_tool(self, tool):
        self.tool = tool


def mouse_event(
    button=Qt.MouseButton.LeftButton,
    modifiers=Qt.KeyboardModifier.NoModifier,
):
    event = Mock(spec=QMouseEvent)
    event.button.return_value = button
    event.modifiers.return_value = modifiers
    event.globalPos.return_value = QPoint(12, 14)
    return event


def paint_overlay(draw):
    image = QImage(180, 180, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    draw(painter)
    painter.end()
    return image


def test_ellipse_drag_commit_overlay_history_and_cancel(qt_app):
    canvas = CanvasProbe()
    tool = EllipseSelectionTool(canvas)
    left = mouse_event()
    shifted = mouse_event(modifiers=Qt.KeyboardModifier.ShiftModifier)

    assert tool.commit_selection() is None
    tool.on_mouse_press(left, (20, 30))
    tool.on_mouse_move(shifted, (5, 50))
    assert (tool._radius_x, tool._radius_y) == (20, 20)
    paint_overlay(tool.draw_overlay)
    tool.on_mouse_release(left, (5, 50))

    assert len(canvas.model.objects) == 1
    object_id = next(iter(canvas.model.objects))
    assert len(canvas.model.objects[object_id].polygon) >= 32
    assert tool._center is None

    tool.undo_last_action()
    assert canvas.model.objects == {}
    tool.redo_last_action()
    assert object_id in canvas.model.objects

    tool.update_language("pt")
    tool.cancel()
    assert tool.current_lang == "pt"
    assert tool._is_selecting is False
    paint_overlay(tool.draw_overlay)


def test_ellipse_nonshift_right_click_and_failed_release(qt_app, monkeypatch):
    canvas = CanvasProbe()
    tool = EllipseSelectionTool(canvas)
    left = mouse_event()
    right = mouse_event(Qt.MouseButton.RightButton)
    calls = []
    monkeypatch.setattr(tool, "show_context_menu", lambda event: calls.append(event))

    tool.on_mouse_press(right, (0, 0))
    assert calls == [right]

    tool.on_mouse_press(left, (10, 10))
    tool.on_mouse_move(left, (25, 18))
    assert (tool._radius_x, tool._radius_y) == (15, 8)
    monkeypatch.setattr(tool, "commit_selection", lambda: None)
    tool.on_mouse_release(left, (25, 18))
    assert tool._center == (10, 10)

    tool._is_selecting = False
    before = canvas.updated
    tool.on_mouse_move(left, (30, 30))
    assert canvas.updated == before

    canvas.model.cmd = None
    tool.undo_last_action()
    tool.redo_last_action()
    tool._radius_x = 0
    paint_overlay(tool.draw_overlay)


def test_tool_palette_navigation_mapping_and_active_language(qt_app, monkeypatch):
    canvas = PaletteCanvas()
    palette = ToolPalette(canvas)
    names = palette.tool_names()
    selected = []
    original_select = palette.select_tool_by_name
    original_buttons = palette.tool_buttons

    palette.tool_buttons = {
        name: Mock(**{"isChecked.return_value": False}) for name in names
    }
    monkeypatch.setattr(palette, "select_tool_by_name", selected.append)
    palette.select_next_tool()
    palette.select_prev_tool()
    assert selected == [names[0], names[-2]]

    palette.tool_buttons = original_buttons
    selected.clear()
    palette.tool_buttons[names[0]].setChecked(True)
    palette.select_next_tool()
    palette.select_prev_tool()
    assert selected == [names[1], names[-1]]

    monkeypatch.setattr(palette, "select_tool_by_name", original_select)
    mapped = []
    monkeypatch.setattr(palette, "select_lasso", lambda: mapped.append("lasso"))
    original_select("missing")
    original_select("lasso_tool")
    assert mapped == ["lasso"]
    assert palette.tool_buttons["lasso_tool"].isChecked()

    active = Mock()
    palette._active_magnetic_lasso = active
    palette.update_language("pt")
    palette.update_language("en")
    assert active.update_language.call_args_list[0].args == ("pt",)
    assert active.update_language.call_args_list[1].args == ("en",)
    palette.close()
    canvas.close()


def test_export_preview_states_metadata_and_resize(qt_app):
    sprite = Image.new("RGBA", (12, 8), (255, 0, 0, 255))
    dialog = ExportPreviewDialog(sprite, {}, lang="invalid")
    assert dialog.current_lang == "en"
    assert "No metadata" in dialog.metadata_label.text()

    dialog.sprite = None
    dialog._update_preview()
    dialog.sprite = sprite
    dialog._on_zoom_changed(150)
    dialog._on_scale_changed(Qt.CheckState.Unchecked.value)
    dialog._on_antialias_changed(Qt.CheckState.Unchecked.value)
    assert dialog.zoom_factor == 1.5
    assert dialog.scale_preview is False
    assert dialog.antialias is False

    dialog.metadata = {
        "id": "sprite",
        "rect": {"x": 1, "y": 2, "w": 3, "h": 4},
        "pivot": [0.5, 0.25],
    }
    dialog._update_metadata_display()
    assert "Rect" in dialog.metadata_label.text()
    assert "Pivot: (0.5, 0.2)" in dialog.metadata_label.text()

    dialog.metadata["pivot"] = {"x": 0.125, "y": 0.75}
    dialog._update_metadata_display()
    assert "x=0.125, y=0.750" in dialog.metadata_label.text()
    dialog.metadata["pivot"] = {"x": None, "y": "center"}
    dialog._update_metadata_display()
    assert "x=?, y=center" in dialog.metadata_label.text()

    dialog.scale_preview = True
    dialog.resizeEvent(QResizeEvent(QSize(640, 480), QSize(320, 240)))
    dialog.scale_preview = False
    dialog.resizeEvent(QResizeEvent(QSize(320, 240), QSize(640, 480)))
    dialog.close()


def test_export_preview_save_cancel_success_and_failure(qt_app, tmp_path, monkeypatch):
    sprite = Image.new("RGBA", (8, 8), (0, 255, 0, 255))
    dialog = ExportPreviewDialog(sprite, {"id": "sprite"})
    messages = []

    monkeypatch.setattr(
        export_preview_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )
    dialog._on_export()

    destination = tmp_path / "sprite.png"
    monkeypatch.setattr(
        export_preview_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(destination), ""),
    )
    monkeypatch.setattr(
        export_preview_module.QMessageBox,
        "information",
        lambda *args: messages.append(("ok", args)),
    )
    monkeypatch.setattr(
        export_preview_module.QMessageBox,
        "critical",
        lambda *args: messages.append(("error", args)),
    )
    dialog._on_export()
    assert destination.is_file()
    assert messages[-1][0] == "ok"

    monkeypatch.setattr(
        "src.exporters.sprite_exporter.save_sprite",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    dialog._on_export()
    assert messages[-1][0] == "error"
    dialog.close()


def test_export_preview_headless_metadata_variants(tmp_path, monkeypatch, capsys):
    image = Image.new("RGB", (180, 120), "navy")
    original_truetype = ImageFont.truetype

    def fail_only_arial(font, *args, **kwargs):
        if font == "arial.ttf":
            raise OSError("font missing")
        return original_truetype(font, *args, **kwargs)

    monkeypatch.setattr(ImageFont, "truetype", fail_only_arial)
    list_output = tmp_path / "list.png"
    dict_output = tmp_path / "dict.png"

    export_preview_headless(
        image,
        {"id": "sprite", "rect": {"w": 20, "h": 10}, "pivot": [1.0, 2.0]},
        str(list_output),
    )
    export_preview_headless(image, {"pivot": {"x": 0.25, "y": 0.75}}, str(dict_output))

    assert list_output.is_file()
    assert dict_output.is_file()
    assert "Preview saved" in capsys.readouterr().out


def test_export_dialog_missing_modules_and_prerequisite_paths(qt_app, monkeypatch):
    for name in (
        "HAS_SPRITE_EXPORTER",
        "HAS_ATLAS_EXPORTER",
        "HAS_METADATA_EXPORTER",
        "HAS_GLTF_EXPORTER",
    ):
        monkeypatch.setattr(export_dialog_module, name, False)

    scene = Scene()
    messages = []
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "critical",
        lambda *args: messages.append(("critical", args)),
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "information",
        lambda *args: messages.append(("information", args)),
    )
    dialog = ExportDialog(scene, lang="invalid")
    assert dialog.current_lang == "en"
    assert not dialog.btn_single.isEnabled()
    assert not dialog.btn_atlas.isEnabled()
    assert not dialog.btn_metadata_selected.isEnabled()
    assert not dialog.btn_gltf_scene.isEnabled()

    assert dialog._check_prerequisites() is False
    scene.image = np.zeros((8, 8, 4), dtype=np.uint8)
    assert dialog._check_prerequisites() is False
    scene.add_object("object", [(0, 0), (4, 0), (4, 4), (0, 4)])
    assert dialog._check_prerequisites(require_selection=True) is False
    scene.select_object("object")
    assert dialog._check_prerequisites(require_selection=True) is True
    assert [kind for kind, _ in messages] == [
        "critical",
        "information",
        "information",
    ]
    dialog.close()


def test_export_dialog_json_and_glb_postconditions(tmp_path):
    missing = tmp_path / "missing"
    empty = tmp_path / "empty.json"
    valid_json = tmp_path / "valid.json"
    short_glb = tmp_path / "short.glb"
    wrong_magic = tmp_path / "wrong.glb"
    wrong_version = tmp_path / "version.glb"
    valid_glb = tmp_path / "valid.glb"

    empty.write_text("", encoding="utf-8")
    valid_json.write_text('{"ok": true}', encoding="utf-8")
    short_glb.write_bytes(b"glTF")
    wrong_magic.write_bytes(b"nope" + (2).to_bytes(4, "little") + b"xxxx")
    wrong_version.write_bytes(b"glTF" + (1).to_bytes(4, "little") + b"xxxx")
    valid_glb.write_bytes(b"glTF" + (2).to_bytes(4, "little") + b"xxxx")

    assert ExportDialog._json_file_is_valid(str(missing)) is False
    assert ExportDialog._json_file_is_valid(str(empty)) is False
    assert ExportDialog._json_file_is_valid(str(valid_json)) is True
    assert ExportDialog._glb_file_is_valid(str(missing)) is False
    assert ExportDialog._glb_file_is_valid(str(short_glb)) is False
    assert ExportDialog._glb_file_is_valid(str(wrong_magic)) is False
    assert ExportDialog._glb_file_is_valid(str(wrong_version)) is False
    assert ExportDialog._glb_file_is_valid(str(valid_glb)) is True


def test_canvas_navigation_geometry_and_transform_branches(qt_app, monkeypatch):
    scene = Scene()
    canvas = CanvasView(scene)
    canvas.resize(500, 360)
    scene.add_object("square", [(10, 10), (50, 10), (50, 50), (10, 50)])
    scene.objects["short"] = SimpleNamespace(polygon=[(0, 0), (1, 1)])

    assert canvas._find_object_at(QPointF(20, 20)) == "square"
    assert canvas._find_object_at(QPointF(200, 200)) is None
    centers = []
    flashes = []
    monkeypatch.setattr(
        canvas,
        "center_on_polygon",
        lambda polygon, margin=50: centers.append((polygon, margin)),
    )
    monkeypatch.setattr(
        canvas,
        "flash_effect",
        lambda color, duration=300: flashes.append((color, duration)),
    )
    canvas.center_on_object("missing")
    canvas.center_on_object("square")
    canvas.focus_on_object("missing")
    canvas.focus_on_object("square")
    assert len(centers) == 2
    assert len(flashes) == 1

    canvas._current_polygon = []
    assert canvas._distance_to_last_point(1, 1) == float("inf")
    canvas._current_polygon = [(4, 5)]
    assert canvas._distance_to_last_point(7, 9) == 5.0
    assert canvas._get_image_center_screen() is None

    scene.image = None
    canvas.fit_to_window()
    scene.image = np.zeros((0, 0, 4), dtype=np.uint8)
    canvas.fit_to_window()
    scene.image = np.zeros((120, 200, 4), dtype=np.uint8)
    canvas.fit_to_window()
    assert canvas.get_zoom() > 0

    original_center = CanvasView.center_on_polygon.__get__(canvas, CanvasView)
    original_center([])
    original_center([(5, 5), (5, 5)])
    original_center([(0, 0), (100, 0), (100, 50), (0, 50)])
    before_zoom = canvas.get_zoom()
    canvas.set_zoom(0.001)
    assert canvas.get_zoom() == before_zoom
    canvas.set_zoom(2.0)
    assert canvas.get_zoom() == 2.0
    canvas._pan = QPointF(10, 20)
    assert canvas.widget_to_image(QPointF(14, 28)) == (2, 4)
    assert canvas.image_to_widget(2, 4) == QPointF(14, 28)
    canvas.close()


def test_canvas_command_success_rejection_and_failure_paths(qt_app, monkeypatch):
    scene = Scene()
    scene.cmd = CommandManager()
    canvas = CanvasView(scene)
    messages = []
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "warning",
        lambda *args: messages.append(("warning", args)),
    )
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "critical",
        lambda *args: messages.append(("critical", args)),
    )

    manager = Mock()
    manager.execute.side_effect = [
        SimpleNamespace(status=CommandStatus.REJECTED, message="", changed=False),
        SimpleNamespace(status=CommandStatus.FAILED, message="failed", changed=False),
    ]
    scene.cmd = manager
    canvas._execute_edit_command(Mock())
    canvas._execute_edit_command(Mock())
    assert [kind for kind, _ in messages[:2]] == ["warning", "critical"]

    scene.cmd = None
    with pytest.raises(RuntimeError, match="history is unavailable"):
        canvas._execute_edit_command(Mock())
    assert canvas._commit_native_polygon([(0, 0), (10, 0), (0, 10)]) is None
    canvas._toggle_collision("missing")
    canvas._delete_object("missing")

    scene.cmd = CommandManager()
    object_id = canvas._commit_native_polygon([(0, 0), (20, 0), (20, 20), (0, 20)])
    assert object_id in scene.objects
    before_updates = canvas.isVisible()
    canvas._toggle_collision(object_id)
    assert scene.has_collision(object_id)
    canvas._toggle_physics(object_id)
    assert not scene.has_collision(object_id)
    canvas._delete_object(object_id)
    assert object_id not in scene.objects
    assert canvas.isVisible() is before_updates

    scene.add_object("one", [(0, 0), (10, 0), (10, 10), (0, 10)])
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "question",
        lambda *args: canvas_view_module.QMessageBox.StandardButton.No,
    )
    canvas.clean_all()
    assert "one" in scene.objects
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "question",
        lambda *args: canvas_view_module.QMessageBox.StandardButton.Yes,
    )
    canvas.clean_all()
    assert scene.objects == {}
    assert canvas._current_polygon == []

    scene.cmd = None
    canvas.clean_all()
    assert messages[-1][0] == "critical"
    canvas.gizmo_toggle.setChecked(True)
    canvas._toggle_gizmo()
    assert canvas._gizmo_enabled is True
    canvas.close()


def test_canvas_modes_tools_and_gizmo_guard_branches(qt_app, monkeypatch):
    scene = Scene()
    scene.cmd = CommandManager()
    canvas = CanvasView(scene)
    messages = []
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "warning",
        lambda *args: messages.append(("warning", args)),
    )
    monkeypatch.setattr(
        canvas_view_module.QMessageBox,
        "critical",
        lambda *args: messages.append(("critical", args)),
    )

    scene.image = None
    canvas.update_image()
    assert canvas._qimage_lit is None
    scene.image = np.zeros((16, 24, 4), dtype=np.uint8)
    canvas.update_image()
    assert canvas._qimage_lit is not None
    assert canvas._gizmo_enabled is False
    canvas.update_image()

    started = []
    monkeypatch.setattr(canvas.threadpool, "start", started.append)
    canvas._qimage_xray_1 = None
    canvas.set_view_mode(canvas.VIEW_XRAY_1)
    assert len(started) == 1
    canvas._qimage_xray_1 = QImage(4, 4, QImage.Format.Format_ARGB32)
    canvas.set_view_mode(canvas.VIEW_XRAY_1)
    assert len(started) == 1

    modes = []
    monkeypatch.setattr(canvas, "set_view_mode", modes.append)
    canvas._view_mode = canvas.VIEW_LIT
    canvas.toggle_xray()
    canvas._view_mode = canvas.VIEW_XRAY_1
    canvas.toggle_xray()
    assert modes == [canvas.VIEW_XRAY_1, canvas.VIEW_LIT]
    canvas._on_xray_finished(QImage(2, 2, QImage.Format.Format_ARGB32), 2)
    assert canvas._qimage_xray_2 is not None

    cancel_calls = []
    current_tool = SimpleNamespace(on_cancel=lambda: cancel_calls.append("tool"))
    monkeypatch.setattr(
        canvas,
        "_cancel_gizmo_gesture",
        lambda: cancel_calls.append("gizmo") or True,
    )
    canvas._gizmo_active = True
    canvas._tool = current_tool
    canvas.set_tool(None)
    assert cancel_calls == ["gizmo", "tool"]

    canvas._gizmo_active = True
    canvas._tool = current_tool
    canvas.set_preview_mode(True)
    assert canvas._preview_mode is True
    assert cancel_calls[-2:] == ["gizmo", "tool"]
    canvas.set_preview_mode(False)
    canvas.show_temp_mask(np.ones((2, 2), dtype=np.uint8))
    canvas.clear_temp_mask()
    assert canvas._temp_mask is None

    canvas._report_gizmo_result(
        SimpleNamespace(status=CommandStatus.REJECTED, message="")
    )
    canvas._report_gizmo_result(
        SimpleNamespace(status=CommandStatus.FAILED, message="failed")
    )
    assert [kind for kind, _ in messages[-2:]] == ["warning", "critical"]

    scene.selected_id = None
    assert canvas._begin_gizmo_object_gesture() is False
    scene.add_object("move", [(0, 0), (10, 0), (10, 10), (0, 10)])
    scene.select_object("move")
    scene.cmd = None
    assert canvas._begin_gizmo_object_gesture() is False
    scene.cmd = CommandManager()
    assert canvas._begin_gizmo_object_gesture() is True

    canvas.gizmo = SimpleNamespace(active_axis=1, NONE=0)
    canvas._reset_gizmo_interaction()
    assert canvas.gizmo.active_axis == 0
    scene.selected_id = "missing"
    assert canvas._begin_gizmo_object_gesture() is False
    canvas.close()


def test_tool_palette_command_adapters_cover_auxiliary_actions():
    class TabsProbe:
        def __init__(self, index):
            self.index = index
            self.current_index = None

        def indexOf(self, panel):
            return self.index

        def setCurrentIndex(self, index):
            self.current_index = index

    panel = object()
    reference_tabs = TabsProbe(-1)
    tool_palette_commands_module.show_panel(
        SimpleNamespace(reference_panel_tabs=reference_tabs), panel
    )
    assert reference_tabs.current_index is None

    compact_tabs = TabsProbe(-1)
    window = SimpleNamespace(
        compact_panel_tabs=compact_tabs,
        reference_panel_tabs=None,
    )
    tool_palette_commands_module.show_panel(window, panel)
    assert compact_tabs.current_index is None

    class PanelProbe:
        def __init__(self):
            self.visible = False

        def setVisible(self, visible):
            self.visible = visible

    visible_panel = PanelProbe()
    visible_tabs = TabsProbe(1)
    visible_window = SimpleNamespace(
        compact_panel_tabs=visible_tabs,
        reference_panel_tabs=None,
    )
    visible_tabs.indexOf = lambda candidate: 1 if candidate is visible_panel else -1
    tool_palette_commands_module.show_panel(visible_window, visible_panel)
    assert visible_tabs.current_index == 1
    assert visible_panel.visible is True

    canvas = SimpleNamespace(
        pan_calls=[],
        zoom=2.0,
        zoom_calls=[],
        fit_calls=0,
        set_pan_mode=lambda enabled: canvas.pan_calls.append(enabled),
        get_zoom=lambda: canvas.zoom,
        set_zoom=lambda value: canvas.zoom_calls.append(value),
        fit_to_window=lambda: setattr(canvas, "fit_calls", canvas.fit_calls + 1),
    )
    collision_panel = SimpleNamespace(
        _sync_collision_manager_from_scene=Mock(),
    )
    window = SimpleNamespace(
        canvas=canvas,
        collision_panel=collision_panel,
        tool_palette=SimpleNamespace(navigation_actions={}),
        _focus_selected=Mock(),
        compact_panel_tabs=None,
        reference_panel_tabs=None,
    )

    tool_palette_commands_module.handle_auxiliary_action(window, "move_viewport")
    move_action = SimpleNamespace(isChecked=lambda: True)
    window.tool_palette.navigation_actions["move_viewport"] = move_action
    tool_palette_commands_module.handle_auxiliary_action(window, "move_viewport")
    assert canvas.pan_calls == [False, True]

    tool_palette_commands_module.handle_auxiliary_action(window, "zoom_viewport")
    tool_palette_commands_module.handle_auxiliary_action(window, "fit_view")
    tool_palette_commands_module.handle_auxiliary_action(window, "focus_selected")
    tool_palette_commands_module.handle_auxiliary_action(window, "validation")
    assert canvas.zoom_calls == [2.5]
    assert canvas.fit_calls == 1
    window._focus_selected.assert_called_once_with()
    collision_panel._sync_collision_manager_from_scene.assert_called_once_with()
    tool_palette_commands_module.handle_auxiliary_action(window, "unknown")


def test_remaining_integrated_branch_outcomes(qt_app, monkeypatch):
    class ToolbarProbe:
        def setToolButtonStyle(self, style):
            self.style = style

        def findChildren(self, child_type):
            return []

    layout = ResponsivePanelLayout.__new__(ResponsivePanelLayout)
    layout.owner = SimpleNamespace()
    layout._set_reference_toolbar_mode(compact=False)
    layout.owner = SimpleNamespace(reference_top_toolbar=ToolbarProbe())
    layout._set_reference_toolbar_mode(compact=True)

    window = QWidget()
    window.translations = {
        "en": {
            "view_settings": "View Settings",
            "grid": "Grid",
            "snap": "Snap",
        }
    }
    window.current_lang = "en"
    window.canvas = SimpleNamespace(
        is_grid_visible=lambda: True,
        _vertex_snap_settings=SimpleNamespace(enabled=True),
        set_grid_visible=Mock(),
        set_vertex_snapping=Mock(),
    )
    window.act_grid = Mock()
    window.act_snap = Mock()
    monkeypatch.setattr(
        viewport_settings_module.QDialog,
        "exec",
        lambda dialog: viewport_settings_module.QDialog.DialogCode.Rejected,
    )
    viewport_settings_module.open_view_settings(window)
    window.canvas.set_grid_visible.assert_not_called()
    window.canvas.set_vertex_snapping.assert_not_called()
    window.close()

    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[4:12, 5:14] = 255
    polygon = selection_tools_module.mask_to_polygon(mask, approx_dp=0.0)
    assert len(polygon) > 0
    monkeypatch.setattr(
        selection_tools_module.cv2,
        "approxPolyDP",
        lambda *_args: None,
    )
    assert selection_tools_module.mask_to_polygon(mask, approx_dp=1.0) == []
