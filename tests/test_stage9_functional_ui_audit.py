"""Executable interaction checks used by the local Stage 9 UI audit."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from scripts.audit_stage9_functional_ui import AuditConfig, fixture_scene, settle
from src.persistence.project_schema import PointRecord
from src.persistence.scene_authoring_io import load_scene_authoring_v2
from src.persistence.scene_authoring_schema import (
    SceneCameraAuthoringRecord,
    SceneParallaxLayerRecord,
)
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _window() -> MainWindow:
    window = MainWindow(fixture_scene(), AuditConfig())
    # Simulate the same refresh invoked after a real image/project load.
    window._refresh_document_views(project_loaded=False)
    return window


def test_all_tool_palette_actions_create_a_real_canvas_tool(qt_app):
    window = _window()
    try:
        for name, button in window.tool_palette.tool_buttons.items():
            button.click()
            settle(qt_app)
            assert button.isChecked(), name
            assert window.tool_palette.button_group.checkedButton() is button
            assert window.canvas._tool is not None, name
    finally:
        window.close()
        settle(qt_app)


def test_xray_actions_update_canvas_state(qt_app):
    window = _window()
    try:
        actions = (
            (window.act_lit, window.canvas.VIEW_LIT),
            (window.act_xray1, window.canvas.VIEW_XRAY_1),
            (window.act_xray2, window.canvas.VIEW_XRAY_2),
            (window.act_xray3, window.canvas.VIEW_XRAY_3),
        )
        for action, expected in actions:
            action.trigger()
            settle(qt_app)
            assert window.canvas._view_mode == expected
    finally:
        window.close()
        settle(qt_app)


def test_scenario_editor_actions_change_the_authoring_document(qt_app, tmp_path):
    project = tmp_path / "stage9-ui.ndtproj"
    project.write_bytes(b"stage9-ui-project\n")
    window = _window()
    try:
        window._project_path = project
        window.scenario_authoring.bind_project(project)
        window.scenario_authoring.reset()
        window.open_scenario_editor()
        editor = window.scenario_editor_window
        assert editor is not None
        editor.show()
        settle(qt_app)
        panel = editor.scenario_panel
        before = panel.list.count()
        panel.btn_add.click()
        assert panel.list.count() == before + 1
        panel.btn_remove.click()
        assert panel.list.count() == before
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        settle(qt_app)


def test_professional_v2_document_drives_main_preview_and_menu_save(qt_app, tmp_path):
    project = tmp_path / "canonical-preview.ndtproj"
    project.write_bytes(b"canonical-preview-project\n")
    window = _window()
    second_window = None
    try:
        window._project_path = project
        window.scenario_authoring.bind_project(project)
        window.open_scenario_editor()
        editor = window.scenario_editor_window
        assert editor is not None and editor.professional_session is not None
        session = editor.professional_session
        layer_id = session.document.layers[0].id
        assert session.set_layer_visibility(layer_id, False) is True
        assert (
            session.set_parallax_layer(
                SceneParallaxLayerRecord(layer_id=layer_id, depth=0.75)
            )
            is True
        )
        assert (
            session.set_camera(
                SceneCameraAuthoringRecord(
                    position=PointRecord(x=24.0, y=-12.0), zoom=1.5
                )
            )
            is True
        )
        settle(qt_app)

        assert window.canvas._scenario_layers[0].visible is False
        assert window.canvas._scenario_layers[0].parallax.depth == 0.75
        assert window.canvas._scenario_camera.position == (24.0, -12.0)

        window.scenario_save_action.trigger()
        settle(qt_app)
        canonical_path = project.with_suffix(".ndtscene.json")
        assert canonical_path.is_file()
        saved = load_scene_authoring_v2(canonical_path)
        assert saved.layers[0].visible is False
        assert saved.parallax_layers[0].depth == 0.75
        assert saved.camera.position == PointRecord(x=24.0, y=-12.0)
        assert not project.with_name("canonical-preview.ndtscenario.json").exists()

        second_window = _window()
        second_window._project_path = project
        second_window._refresh_document_views(project_loaded=True)
        settle(qt_app)
        assert second_window.canvas._scenario_layers[0].visible is False
        assert second_window.canvas._scenario_layers[0].parallax.depth == 0.75
        assert second_window.canvas._scenario_camera.position == (24.0, -12.0)
    finally:
        if second_window is not None:
            second_window.close()
            settle(qt_app)
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        settle(qt_app)


def test_existing_v1_document_is_explicitly_migrated_into_professional_v2(
    qt_app, tmp_path
):
    project = tmp_path / "legacy-migration.ndtproj"
    project.write_bytes(b"legacy-migration-project\n")
    window = _window()
    try:
        window._project_path = project
        window.scenario_authoring.bind_project(project)
        legacy = window.scenario_authoring.document
        assert legacy is not None
        layer_id = legacy.layers[0].id
        window.scenario_authoring.rename_layer(layer_id, "Legacy Background")
        window.scenario_authoring.set_layer_visible(layer_id, False)
        window.scenario_authoring.set_layer_parallax(layer_id, depth=0.25)
        window.scenario_authoring.set_camera(x=-8.0, y=16.0, zoom=1.25)
        legacy_path = project.with_suffix(".ndtscenario.json")
        window.scenario_authoring.save()
        assert legacy_path.is_file()
        assert not project.with_suffix(".ndtscene.json").exists()

        window.open_scenario_editor()
        editor = window.scenario_editor_window
        assert editor is not None and editor.professional_session is not None
        migrated = editor.professional_session.document
        assert migrated.layers[0].name == "Legacy Background"
        assert migrated.layers[0].visible is False
        assert migrated.parallax_layers[0].depth == 0.25
        assert migrated.camera.position == PointRecord(x=-8.0, y=16.0)
        assert migrated.camera.zoom == 1.25

        window.scenario_save_action.trigger()
        settle(qt_app)
        canonical_path = project.with_suffix(".ndtscene.json")
        assert canonical_path.is_file()
        saved = load_scene_authoring_v2(canonical_path)
        assert saved.layers[0].name == "Legacy Background"
        assert saved.layers[0].visible is False
        assert saved.parallax_layers[0].depth == 0.25
        assert saved.camera.position == PointRecord(x=-8.0, y=16.0)
        assert saved.camera.zoom == 1.25
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        settle(qt_app)


def test_professional_inspector_applies_transform_and_socket(qt_app, tmp_path):
    project = tmp_path / "stage9-professional.ndtproj"
    project.write_bytes(b"stage9-professional-project\n")
    asset = tmp_path / "stage9-asset.png"
    asset.write_bytes(b"stage9-asset-fixture")
    window = _window()
    window.scene.image_path = asset
    try:
        window._project_path = project
        window.scenario_authoring.bind_project(project)
        window.scenario_authoring.reset()
        window.open_scenario_editor()
        editor = window.scenario_editor_window
        assert editor is not None
        editor.show()
        settle(qt_app)
        inspector = editor.professional_inspector
        assert inspector is not None
        object_id = editor.professional_session.document.objects[0].id
        editor.professional_session.set_selection([object_id], object_id)
        inspector.position_x.setValue(42.0)
        inspector.position_y.setValue(-7.0)
        inspector.apply_button.click()
        changed = editor.professional_session.document.objects[0].transform.position
        assert (changed.x, changed.y) == (42.0, -7.0)

        inspector.socket_id.setText("stage9-light")
        inspector.socket_type.setCurrentText("light")
        inspector.add_socket_button.click()
        assert any(
            item.id == "stage9-light"
            for item in editor.professional_session.document.sockets
        )
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window._mark_document_clean()
        window.close()
        settle(qt_app)


def test_mask_viewer_all_modes_change_the_display(qt_app):
    window = _window()
    try:
        dialog = window.open_mask_viewer()
        settle(qt_app)
        dialog = dialog or window._mask_viewer_dialog
        assert dialog is not None
        for index, button in enumerate(dialog.view_mode_buttons):
            button.click()
            settle(qt_app)
            assert dialog.viewer.get_display_mode() == index
            assert button.isChecked()
    finally:
        if window._mask_viewer_dialog is not None:
            window._mask_viewer_dialog.close()
        window.close()
        settle(qt_app)
