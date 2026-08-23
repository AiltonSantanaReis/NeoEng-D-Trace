"""Real Qt-flow tests for the separated professional scenario editor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.exporters.scene_authoring_export import validate_scene_authoring_export
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _window(tmp_path: Path, qt_app) -> tuple[ScenarioEditorWindow, Scene]:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"real stage 8 project")
    image = tmp_path / "scene.png"
    rendered = QImage(40, 24, QImage.Format.Format_RGBA8888)
    rendered.fill(0xFF336699)
    assert rendered.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object("scene_object", [(0, 0), (40, 0), (40, 24), (0, 24)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene)
    window.show()
    qt_app.processEvents()
    assert window.professional_session is not None
    assert window.professional_viewport is not None
    assert window.professional_inspector is not None
    return window, scene


def _close(window: ScenarioEditorWindow, qt_app) -> None:
    window.close()
    qt_app.processEvents()


def test_dedicated_surface_has_required_components_and_isolated_close(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        assert window.windowTitle() == "Scenario Editor — NeoEng-D-Trace"
        assert window.toolbar.objectName() == "scenario_editor_toolbar"
        assert window.statusBar().objectName() == "scenario_editor_status_bar"
        assert isinstance(window.professional_inspector_scroll, QScrollArea)
        assert window.layer_stack is not None
        assert window.layer_stack.layer_list.count() == 1
        assert window.professional_viewport.is_authoring_enabled()
        assert not window.professional_viewport.is_preview_enabled()
        assert window.authoring_action.isChecked()
        assert not window.preview_action.isChecked()
    finally:
        _close(window, qt_app)


def test_layer_stack_and_transform_use_the_same_professional_session(
    tmp_path: Path, qt_app
) -> None:
    window, scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        viewport = window.professional_viewport
        stack = window.layer_stack
        assert session is not None and viewport is not None and stack is not None
        main_polygon = tuple(scene.objects["scene_object"].polygon)
        stack.add_button.click()
        qt_app.processEvents()
        assert len(session.document.layers) == 2
        new_id = session.document.layers[-1].id
        stack.layer_list.setCurrentRow(1)
        stack.name_edit.setText("Foreground")
        stack.name_edit.editingFinished.emit()
        assert session.document.layers[-1].name == "Foreground"
        assert session.rename_layer(new_id, "Foreground 2") is True
        assert session.document.layers[-1].name == "Foreground 2"
        stack.remove_button.click()
        qt_app.processEvents()
        assert len(session.document.layers) == 1

        session.set_selection(["scene_object"])
        before_main_history = scene.cmd.undo_count
        before_session_history = session.undo_count
        original_x = session.document.objects[0].transform.position.x
        start = QPointF(original_x, 12.0)
        end = QPointF(original_x + 15.0, 12.0)
        viewport._object_pressed("scene_object", start, Qt.KeyboardModifier.NoModifier)
        viewport._object_moved("scene_object", end)
        viewport._object_released("scene_object", end)
        assert session.undo_count == before_session_history + 1
        assert session.document.objects[0].transform.position.x != original_x
        assert tuple(scene.objects["scene_object"].polygon) == main_polygon
        assert scene.cmd.undo_count == before_main_history
    finally:
        _close(window, qt_app)


def test_numeric_save_reload_and_export_are_real_v2_artifacts(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        inspector = window.professional_inspector
        assert session is not None and inspector is not None
        session.set_selection(["scene_object"])
        inspector.position_x.setValue(77.0)
        inspector.apply_transform()
        window.save_action.trigger()
        qt_app.processEvents()
        scene_path = tmp_path / "scene.ndtscene.json"
        export_path = tmp_path / "scene.ndtscene.runtime.json"
        assert scene_path.is_file()
        first_bytes = scene_path.read_bytes()
        first_hash = hashlib.sha256(first_bytes).hexdigest()
        assert first_hash == hashlib.sha256(scene_path.read_bytes()).hexdigest()

        inspector.position_x.setValue(12.0)
        inspector.apply_transform()
        window.load_action.trigger()
        qt_app.processEvents()
        assert session.document.objects[0].transform.position.x == 77.0
        assert scene_path.read_bytes() == first_bytes

        window.export_action.trigger()
        qt_app.processEvents()
        assert export_path.is_file()
        payload = json.loads(export_path.read_bytes())
        assert payload["format_id"] == "neoeng-d-trace-scene-authoring-export"
        assert payload["source"]["sha256"] == first_hash
    finally:
        _close(window, qt_app)


def test_camera_parallax_sockets_and_overlay_contracts_are_editable(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        inspector = window.professional_inspector
        viewport = window.professional_viewport
        assert session is not None and inspector is not None and viewport is not None
        inspector.camera_x.setValue(120.0)
        inspector.camera_y.setValue(-30.0)
        inspector.camera_zoom.setValue(1.25)
        inspector.camera_apply_button.click()
        assert session.document.camera.position.x == 120.0
        assert session.document.camera.position.y == -30.0
        assert session.document.camera.zoom == 1.25
        inspector.parallax_depth.setValue(0.4)
        inspector.parallax_translation.setValue(0.7)
        inspector.parallax_zoom.setValue(0.8)
        inspector.parallax_apply_button.click()
        assert session.document.parallax_layers[0].depth == 0.4
        inspector.socket_id.setText("lamp_socket")
        inspector.socket_x.setValue(4.0)
        inspector.socket_y.setValue(8.0)
        inspector.add_socket_button.click()
        assert [item.id for item in session.document.sockets] == ["lamp_socket"]
        before = session.document
        window.overlay_action.setChecked(True)
        window._toggle_overlays()
        viewport.grab()
        assert session.document == before
    finally:
        _close(window, qt_app)


def test_preview_mode_is_read_only_and_overlay_is_visual_only(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        viewport = window.professional_viewport
        inspector = window.professional_inspector
        assert session is not None and viewport is not None and inspector is not None
        session.set_selection(["scene_object"])
        original = session.document.objects[0].transform
        window.preview_action.trigger()
        qt_app.processEvents()
        assert viewport.is_preview_enabled()
        assert not viewport.is_authoring_enabled()
        assert inspector.isEnabled() is False
        viewport._object_pressed(
            "scene_object", QPointF(10.0, 10.0), Qt.KeyboardModifier.NoModifier
        )
        viewport._object_moved("scene_object", QPointF(30.0, 10.0))
        viewport._object_released("scene_object", QPointF(30.0, 10.0))
        viewport._gizmo_started("translate", QPointF(10.0, 10.0))
        assert session.document.objects[0].transform == original
        assert session.undo_count == 0
        before = session.document
        window.overlay_action.setChecked(True)
        window._toggle_overlays()
        qt_app.processEvents()
        assert viewport.is_overlay_visible()
        viewport.grab()
        assert session.document == before
        window.authoring_action.trigger()
        qt_app.processEvents()
        assert viewport.is_authoring_enabled()
        assert not viewport.is_preview_enabled()
        assert inspector.isEnabled()
    finally:
        _close(window, qt_app)


def test_scenario_undo_redo_and_close_preserve_state_without_main_history(
    tmp_path: Path, qt_app
) -> None:
    window, scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        inspector = window.professional_inspector
        assert session is not None and inspector is not None
        main_history = scene.cmd.undo_count
        session.set_selection(["scene_object"])
        inspector.position_y.setValue(91.0)
        inspector.apply_transform()
        assert session.can_undo
        assert session.undo()
        assert session.can_redo
        assert session.redo()
        assert session.document.objects[0].transform.position.y == 91.0
        assert scene.cmd.undo_count == main_history
        window.close()
        qt_app.processEvents()
        assert not window.isVisible()
        assert session.can_undo
        assert session.document.objects[0].transform.position.y == 91.0
    finally:
        _close(window, qt_app)


@pytest.mark.parametrize("size", [(1280, 720), (1366, 768), (1920, 1080)])
def test_dedicated_editor_resize_matrix_keeps_critical_widgets_accessible(
    tmp_path: Path, qt_app, size: tuple[int, int]
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        window.resize(*size)
        qt_app.processEvents()
        assert window.professional_viewport.isVisible()
        assert window.professional_inspector_scroll.isVisible()
        assert window.layer_stack.isVisible()
        assert window.professional_viewport.width() > 0
        assert window.professional_inspector_scroll.height() > 0
        assert window.professional_inspector_scroll.widgetResizable()
    finally:
        _close(window, qt_app)


def test_professional_dirty_state_survives_close_reopen_and_save(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        inspector = window.professional_inspector
        assert session is not None and inspector is not None
        session.set_selection(["scene_object"])
        inspector.position_x.setValue(41.0)
        inspector.apply_transform()
        qt_app.processEvents()
        assert session.is_dirty is True
        assert "unsaved" in window.status_label.text().lower()
        window.close()
        window.show()
        qt_app.processEvents()
        assert session.document.objects[0].transform.position.x == 41.0
        assert session.is_dirty is True
        window.save_action.trigger()
        qt_app.processEvents()
        assert session.is_dirty is False
        assert "unsaved" not in window.status_label.text().lower()
    finally:
        _close(window, qt_app)


def test_selection_is_reflected_in_viewport_layer_stack_and_inspector(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        viewport = window.professional_viewport
        inspector = window.professional_inspector
        stack = window.layer_stack
        assert session is not None and viewport is not None
        assert inspector is not None and stack is not None
        session.set_selection(["scene_object"])
        qt_app.processEvents()
        assert inspector.selection_label.text() == "scene_object"
        assert stack.layer_list.currentItem() is not None
        assert stack.layer_list.currentItem().data(Qt.ItemDataRole.UserRole) == (
            session.document.objects[0].layer_id
        )
        assert viewport._items["scene_object"]._brush.color().name() == "#2aa8d8"
        stack.layer_list.setCurrentRow(0)
        qt_app.processEvents()
        assert session.selection.ids == ("scene_object",)
    finally:
        _close(window, qt_app)


def test_layer_stack_covers_add_remove_rename_reorder_visibility_lock_and_selection(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        stack = window.layer_stack
        assert session is not None and stack is not None
        stack.add_button.click()
        stack.add_button.click()
        qt_app.processEvents()
        layer_ids = [item.id for item in session.document.layers]
        assert len(layer_ids) == 3
        stack.layer_list.setCurrentRow(2)
        stack.name_edit.setText("Foreground")
        stack.name_edit.editingFinished.emit()
        stack.visible_box.setChecked(False)
        stack.locked_box.setChecked(True)
        qt_app.processEvents()
        assert session.document.layers[2].name == "Foreground"
        assert session.document.layers[2].visible is False
        assert session.document.layers[2].locked is True
        stack.up_button.click()
        qt_app.processEvents()
        assert session.document.layers[1].name == "Foreground"
        stack.layer_list.setCurrentRow(1)
        assert session.selection.ids == ()
        stack.remove_button.click()
        qt_app.processEvents()
        assert len(session.document.layers) == 2
        stack.layer_list.setCurrentRow(1)
        stack.remove_button.click()
        qt_app.processEvents()
        assert len(session.document.layers) == 1
    finally:
        _close(window, qt_app)


def test_overlay_changes_rendered_pixels_without_mutating_document(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        viewport = window.professional_viewport
        assert session is not None and viewport is not None
        before_document = session.document
        before_path = tmp_path / "overlay_before.png"
        after_path = tmp_path / "overlay_after.png"
        assert viewport.grab().save(str(before_path), "PNG")
        window.overlay_action.setChecked(True)
        window._toggle_overlays()
        qt_app.processEvents()
        assert viewport.grab().save(str(after_path), "PNG")
        assert (
            hashlib.sha256(before_path.read_bytes()).hexdigest()
            != hashlib.sha256(after_path.read_bytes()).hexdigest()
        )
        assert session.document == before_document
    finally:
        _close(window, qt_app)


def test_preview_blocks_numeric_clicks_and_real_asset_drop(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        viewport = window.professional_viewport
        inspector = window.professional_inspector
        assert session is not None and viewport is not None and inspector is not None
        session.set_selection(["scene_object"])
        window.preview_action.trigger()
        qt_app.processEvents()
        before = session.document
        inspector.position_x.setValue(222.0)
        QTest.mouseClick(inspector.apply_button, Qt.MouseButton.LeftButton)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(tmp_path / "scene.png"))])
        event = QDropEvent(
            QPoint(20, 20),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.dropEvent(event)
        assert not event.isAccepted()
        assert session.document == before
        assert session.undo_count == 0
        assert "read-only" in window.status_label.text().lower()
    finally:
        _close(window, qt_app)


def test_export_is_schema_valid_deterministic_and_hash_bound(
    tmp_path: Path, qt_app
) -> None:
    window, _scene = _window(tmp_path, qt_app)
    try:
        session = window.professional_session
        assert session is not None
        window.export_action.trigger()
        qt_app.processEvents()
        export_path = tmp_path / "scene.ndtscene.runtime.json"
        first_bytes = export_path.read_bytes()
        validate_scene_authoring_export(json.loads(first_bytes))
        first_hash = hashlib.sha256(first_bytes).hexdigest()
        window.export_action.trigger()
        qt_app.processEvents()
        second_bytes = export_path.read_bytes()
        assert second_bytes == first_bytes
        assert hashlib.sha256(second_bytes).hexdigest() == first_hash
        payload = json.loads(second_bytes)
        assert payload["source"]["sha256"]
        assert payload["scene"]["objects"][0]["id"] == "scene_object"
    finally:
        _close(window, qt_app)
