"""Real contract tests for Stage 4B.3 scenario authoring."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import (
    ScenarioAuthoringError,
    ScenarioAuthoringState,
)
from src.models.scene import Scene
from src.persistence.scenario_io import ScenarioFormatError, ScenarioValidationError
from src.ui import scenario_authoring_actions as scenario_actions
from src.ui.main_window import MainWindow
from src.ui.scenario_panel import ScenarioPanel


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _Config:
    def get(self, key, default=None):
        del key
        return default

    def set(self, key, value):
        del key, value

    def save(self):
        return None


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = np.zeros((80, 80, 4), dtype=np.uint8)
    scene.image[:, :, 3] = 255
    scene.add_object("object_a", [(8, 8), (32, 8), (32, 32), (8, 32)], select=True)
    scene.cmd.clear()
    return scene


def test_authoring_commands_are_isolated_and_reversible(tmp_path):
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"real project fixture\n")
    scene = _scene()
    state = ScenarioAuthoringState(scene)
    state.bind_project(project)
    original_scene = list(scene.objects["object_a"].polygon)
    original_project_undo = scene.cmd.undo_count

    layer_id = state.document.layers[0].id
    assert state.rename_layer(layer_id, "Foreground").changed
    assert state.set_layer_parallax(layer_id, depth=0.75, zoom_strength=0.4).changed
    assert state.set_camera(x=12.0, y=-4.0, zoom=1.5).changed
    added_id = state.add_layer("Background")
    assert state.assign_object("object_a", added_id).changed
    assert state.document.layers[-1].object_ids == ["object_a"]
    assert scene.objects["object_a"].polygon == original_scene
    assert scene.cmd.undo_count == original_project_undo

    while state.commands.can_undo:
        assert state.undo().ok
    assert state.document.layers[0].name == "Default"
    assert state.document.camera.zoom == 1.0
    assert state.document.layers[0].object_ids == ["object_a"]
    while state.commands.can_redo:
        assert state.redo().ok
    assert state.document.layers[-1].object_ids == ["object_a"]


def test_authoring_round_trip_hash_binding_and_atomic_failure(tmp_path):
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"real project fixture\n")
    state = ScenarioAuthoringState(_scene())
    state.bind_project(project)
    state.rename_layer(state.document.layers[0].id, "Saved Layer")
    destination = state.save()
    before = destination.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    assert state.scenario_path == destination
    assert state.saved_digest == digest
    assert state.is_dirty is False

    reloaded = ScenarioAuthoringState(_scene())
    reloaded.bind_project(project)
    assert reloaded.document == state.document
    assert reloaded.is_dirty is False

    project.write_bytes(b"changed project fixture\n")
    with pytest.raises(ScenarioValidationError):
        reloaded.load(destination)
    assert destination.read_bytes() == before

    with pytest.raises(ScenarioAuthoringError):
        state.remove_layer(state.document.layers[0].id)
    assert destination.read_bytes() == before


def test_invalid_sidecar_bind_restores_previous_authoring_state(tmp_path):
    first_project = tmp_path / "first.ndtproj"
    second_project = tmp_path / "second.ndtproj"
    first_project.write_bytes(b"first project\\n")
    second_project.write_bytes(b"second project\\n")
    invalid_sidecar = second_project.with_name("second.ndtscenario.json")
    invalid_sidecar.write_text("{}\\n", encoding="utf-8")
    state = ScenarioAuthoringState(_scene())
    state.bind_project(first_project)
    original_document = state.document

    with pytest.raises(ScenarioFormatError):
        state.bind_project(second_project)

    assert state.project_path == first_project.resolve()
    assert state.document == original_document


def test_scenario_panel_controls_edit_and_save_the_real_sidecar(tmp_path, qt_app):
    project = tmp_path / "panel.ndtproj"
    project.write_bytes(b"panel project\\n")
    state = ScenarioAuthoringState(_scene())
    state.bind_project(project)
    panel = ScenarioPanel(state, state.scene)
    panel.show()
    qt_app.processEvents()
    try:
        panel.list.setCurrentRow(0)
        panel.name_edit.setText("Edited in panel")
        panel._rename()
        panel.depth_spin.setValue(0.6)
        panel._set_parallax()
        panel.camera_zoom_spin.setValue(1.25)
        panel._set_camera()
        panel.btn_add.click()
        panel.btn_save.click()

        assert state.document.layers[0].name == "Edited in panel"
        assert state.document.layers[0].parallax.depth == 0.6
        assert state.document.camera.zoom == 1.25
        assert state.scenario_path.is_file()
        assert state.is_dirty is False
    finally:
        panel.close()
        qt_app.processEvents()


def test_main_window_keeps_scenario_authoring_out_of_main_layers(qt_app, tmp_path):
    project = tmp_path / "scenario-editor.ndtproj"
    project.write_bytes(b"scenario editor fixture\n")
    window = MainWindow(_scene(), _Config())
    window._project_path = project
    window.scenario_authoring.bind_project(project)
    window.show()
    qt_app.processEvents()
    try:
        assert window.layers.tabs.count() == 1
        assert window.scenario_panel is None
        assert window.compact_panel_tabs.count() == 4
        assert window.scenario_open_action in window.scenario_menu.actions()
        assert window.command_registry.action("scenario.open") is window.scenario_open_action
        window.open_scenario_editor()
        qt_app.processEvents()
        editor = window.scenario_editor_window
        assert editor is not None and editor.isVisible()
        assert editor.scenario_panel.list.count() == 1
        assert editor.scenario_panel.name_edit.height() >= 20
        assert editor.scenario_panel.btn_add.isEnabled()
        assert window.scenario_save_action in window.scenario_menu.actions()
        assert window.scenario_export_action in window.scenario_menu.actions()
        assert window.command_registry.action("scenario.export") is window.scenario_export_action
        assert window.command_registry.action("scenario.save") is window.scenario_save_action
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        qt_app.processEvents()


def test_scenario_state_negative_paths_and_preview_contracts(tmp_path):
    with pytest.raises(ValueError):
        ScenarioAuthoringState(_scene(), max_history=0)

    empty = Scene()
    empty.cmd = CommandManager(max_history=4)
    empty.layers.clear()
    state = ScenarioAuthoringState(empty, max_history=1)
    assert state.is_available is False
    assert state.is_dirty is False
    with pytest.raises(ScenarioAuthoringError):
        state.document_or_raise()
    with pytest.raises(ScenarioAuthoringError):
        state.reset()
    with pytest.raises(ScenarioAuthoringError):
        state.save()
    with pytest.raises(ScenarioAuthoringError):
        state.load()
    with pytest.raises(ScenarioAuthoringError):
        state.preview_layers()
    with pytest.raises(ScenarioAuthoringError):
        state.preview_camera((80.0, 80.0))

    state.bind_project(None)
    invalid = tmp_path / "invalid.txt"
    invalid.write_bytes(b"not a project")
    with pytest.raises(ScenarioAuthoringError):
        state.bind_project(invalid)

    project = tmp_path / "empty.ndtproj"
    project.write_bytes(b"empty project\n")
    state.bind_project(project)
    assert [layer.id for layer in state.document.layers] == ["layer_default"]
    layer_id = state.document.layers[0].id
    assert state.set_layer_visible(layer_id, False).changed
    assert state.set_layer_visible(layer_id, False).changed is False
    assert state.rename_layer(layer_id, "Default").changed is False
    with pytest.raises(ScenarioAuthoringError):
        state.rename_layer(layer_id, "   ")
    with pytest.raises(ScenarioAuthoringError):
        state.rename_layer("missing", "Layer")
    with pytest.raises(ScenarioAuthoringError):
        state.set_layer_parallax("missing", depth=0.5)
    with pytest.raises(ScenarioAuthoringError):
        state.move_layer("missing", 0)
    assert state.move_layer(layer_id, 99).changed is False
    added_one = state.add_layer(" ")
    added_two = state.add_layer("Second")
    assert added_one == "scenario_layer_1"
    assert added_two == "scenario_layer_2"
    assert len(state.preview_layers()) == 3
    assert state.preview_camera((80.0, 80.0)).zoom == 1.0
    assert state.remove_layer(added_two).changed
    assert state.remove_layer(added_one).changed
    with pytest.raises(ScenarioAuthoringError):
        state.remove_layer(layer_id)
    with pytest.raises(ScenarioAuthoringError):
        state.assign_object("missing", layer_id)

    state.undo()
    state.undo()
    assert state.commands.undo_count == 0
    assert state.undo().changed is False
    assert state.redo().changed


def test_scenario_command_rejects_stale_undo_without_mutating_scene(tmp_path):
    project = tmp_path / "stale.ndtproj"
    project.write_bytes(b"stale project\n")
    state = ScenarioAuthoringState(_scene())
    state.bind_project(project)
    layer_id = state.document.layers[0].id
    before = state.document
    assert state.rename_layer(layer_id, "Changed").changed
    command = state.commands._undo[-1]
    state._set_document(before)
    result = command.undo(state)
    assert result.status.name == "REJECTED"
    assert state.document == before
    state._set_document(command.after)
    assert state.undo().ok
    assert state.redo().ok


def test_scenario_history_empty_rebind_and_stale_execute_paths(tmp_path):
    project = tmp_path / "history.ndtproj"
    other_project = tmp_path / "other.ndtproj"
    project.write_bytes(b"history project\n")
    other_project.write_bytes(b"other project\n")
    state = ScenarioAuthoringState(_scene())
    notifications = []
    state.commands.subscribe(lambda: notifications.append("changed"))
    state.commands.subscribe(lambda: notifications.append("changed"))
    state.bind_project(project)
    state.bind_project(project)
    assert notifications
    state.reset()
    layer_id = state.document.layers[0].id
    assert state.rename_layer(layer_id, "Changed").changed
    command = state.commands._undo[-1]
    state._set_document(command.after)
    assert command.execute(state).status.name == "REJECTED"
    state.commands.clear()
    assert state.undo().changed is False
    assert state.redo().changed is False
    state._rebind_project_hash(other_project)
    assert state.saved_digest is None


def test_scenario_action_adapter_success_and_fail_closed_paths(
    tmp_path, qt_app, monkeypatch
):
    project = tmp_path / "actions.ndtproj"
    project.write_bytes(b"actions project\n")
    window = MainWindow(_scene(), _Config())
    reports = []
    monkeypatch.setattr(
        scenario_actions,
        "_report",
        lambda _window, title, message: reports.append((title, message)),
    )
    try:
        assert scenario_actions._save(window) is False
        assert scenario_actions._load(window) is False
        assert scenario_actions._reset(window) is False
        scenario_actions._sync_preview(window)
        window._project_path = project
        window.scenario_authoring.bind_project(project)
        assert scenario_actions._save(window) is True
        assert scenario_actions._load(window) is True
        window.scenario_authoring.rename_layer(
            window.scenario_authoring.document.layers[0].id, "Dirty"
        )
        monkeypatch.setattr(
            scenario_actions.QMessageBox,
            "question",
            lambda *args, **kwargs: scenario_actions.QMessageBox.StandardButton.No,
        )
        assert scenario_actions._reset(window) is False
        monkeypatch.setattr(
            scenario_actions.QMessageBox,
            "question",
            lambda *args, **kwargs: scenario_actions.QMessageBox.StandardButton.Yes,
        )
        assert scenario_actions._reset(window) is True
        assert reports
        window.scenario_authoring.bind_project(None)
        scenario_actions._sync_preview(window)
    finally:
        window.close()
        qt_app.processEvents()
