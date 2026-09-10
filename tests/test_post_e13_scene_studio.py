"""Functional regression contracts for the post-E13 parallax studio."""

import hashlib
from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtGui import QDropEvent, QImage
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_sequence import set_sequence, evaluate_sequence, particles_at, sequence_time
from src.exporters.scene_authoring_export import build_scene_authoring_export, SceneAuthoringExportError
from src.models.scene import Scene
from src.persistence.scene_authoring_schema import AssetReferenceRecord, SceneAuthoringDocumentV2, SceneLayerAuthoringRecord
from src.persistence.scene_sequence_schema import SceneClip, SceneSequence
from src.persistence.scene_authoring_io import save_scene_authoring, load_scene_authoring_v2
from src.ui.scenario_editor_window import ScenarioEditorWindow


@pytest.fixture
def studio(tmp_path):
    app = QApplication.instance() or QApplication([])
    image = tmp_path / "sprite.png"
    pixels = QImage(120, 80, QImage.Format.Format_RGBA8888)
    pixels.fill(0xff5b8890)
    assert pixels.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object("sprite", [(0, 0), (120, 0), (120, 80), (0, 80)])
    project = tmp_path / "studio.ndtproj"
    scene.save_project(str(project))
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene, language="pt")
    window.show()
    app.processEvents()
    yield window, app
    window.sequence_panel.stop()
    window.professional_session.mark_saved()
    window.close()
    window.deleteLater()
    app.processEvents()


def test_layout_preserves_existing_tools_and_categorizes_inspector(studio):
    window, app = studio
    assert window.studio_library_tabs.count() == 3
    assert window.professional_inspector.category_tabs.count() == 5
    assert window.studio_inspector_tabs.count() == 3
    assert window.professional_viewport.isVisible()
    assert window.sequence_panel.isVisible()
    assert not window.tilemap_panel.isVisible()
    assert window.layer_stack.move_selection_button.text() == "Mover seleção para a moldura"


def test_asset_drop_uses_selected_depth_frame_and_undo(studio):
    window, app = studio
    session = window.professional_session
    session.add_layer(SceneLayerAuthoringRecord(id="foreground", name="Frente"))
    window.layer_stack.layer_list.setCurrentRow(1)
    viewport = window.professional_viewport
    mime = QMimeData()
    mime.setData("application/x-neoeng-scene-asset", session.document.assets[0].id.encode())
    event = QDropEvent(QPointF(100, 100), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    before = session.undo_count
    viewport.dropEvent(event)
    assert event.isAccepted()
    assert session.document.objects[-1].layer_id == "foreground"
    assert session.undo_count == before + 1
    assert session.undo()
    assert len(session.document.objects) == 1
    assert session.redo()
    assert session.document.objects[-1].layer_id == "foreground"


def test_move_multiple_objects_into_frame_preserves_selection(studio):
    window, _ = studio
    session = window.professional_session
    viewport = window.professional_viewport
    viewport.place_asset_from_library(session.document.assets[0].id)
    ids = [obj.id for obj in session.document.objects]
    session.set_selection(ids)
    session.add_layer(SceneLayerAuthoringRecord(id="front", name="Frente"))
    window.layer_stack.layer_list.setCurrentRow(1)
    assert set(session.selection.ids) == set(ids)
    window.layer_stack.move_selection_button.click()
    assert {obj.layer_id for obj in session.document.objects} == {"front"}
    session.undo()
    assert {obj.layer_id for obj in session.document.objects} != {"front"}


def test_locked_frame_rejects_drop_without_mutation(studio):
    window, _ = studio
    session = window.professional_session
    session.set_layer_locked(session.document.layers[0].id, True)
    before = session.snapshot()
    assert not window.professional_viewport.place_asset_from_library(session.document.assets[0].id)
    assert session.snapshot() == before


def test_timeline_camera_play_seek_stop_never_changes_authoring(studio):
    window, app = studio
    panel = window.sequence_panel
    panel.add_clip("camera")
    session = window.professional_session
    before, history = session.snapshot(), session.undo_count
    panel.seek(2.5)
    app.processEvents()
    assert panel.preview.session.document.camera.position.x == 100
    assert session.snapshot() == before
    assert session.undo_count == history
    panel.toggle_play()
    assert panel.timer.isActive()
    panel.toggle_play()
    assert not panel.timer.isActive()
    panel.seek(0)
    assert panel.preview.session.document.camera.position.x == 0
    panel.stop_button.click()
    assert panel.preview is None
    assert panel.position == 0
    assert window.professional_pages.currentWidget() is window.professional_viewport
    assert session.snapshot() == before


def test_sequence_roundtrip_and_history(studio, tmp_path):
    window, _ = studio
    panel = window.sequence_panel
    for kind in ("camera", "light", "rain", "snow", "dust", "fire", "text"):
        panel.add_clip(kind)
    session = window.professional_session
    assert len(panel.sequence.clips) == 7
    session.undo()
    assert len(panel.sequence.clips) == 6
    session.redo()
    path = tmp_path / "studio.ndtscene.json"
    save_scene_authoring(session.document, path)
    loaded = load_scene_authoring_v2(path)
    assert loaded.sequence == session.document.sequence
    assert loaded.sequence.schema_version == 1
    assert evaluate_sequence(loaded, 2) == evaluate_sequence(session.document, 2)


def test_motion_animates_only_selected_object_and_opacity(studio):
    window, _ = studio
    session = window.professional_session
    session.set_selection(["sprite"])
    panel = window.sequence_panel
    panel.add_clip("motion")
    assert len(panel.sequence.clips) == 1
    clip = panel.sequence.clips[0]
    panel.change_clip(clip.id, {"end_rotation": 90., "end_opacity": 0.2})
    initial = session.document.objects[0]
    result = evaluate_sequence(session.document, 2.5).objects[0]
    assert result.transform.position.x == initial.transform.position.x + 50
    assert result.transform.rotation.z == 45
    assert result.material.opacity == pytest.approx(.6)
    assert session.document.objects[0] == initial


def test_clip_editor_and_overlap_rejection_are_atomic(studio):
    window, _ = studio
    panel = window.sequence_panel
    panel.add_clip("camera")
    panel.name.setText("Travelling")
    panel.fields["end_x"].setValue(600)
    panel.apply_button.click()
    assert panel.sequence.clips[0].end_x == 600
    assert panel.sequence.clips[0].name == "Travelling"
    before = window.professional_session.snapshot()
    panel.add_clip("camera")
    assert window.professional_session.snapshot() == before
    panel.duration.setValue(1)
    panel.change_sequence()
    assert window.professional_session.snapshot() == before


@pytest.mark.parametrize("kind", ["rain", "snow", "dust", "fire"])
def test_particle_emitter_determinism_lifecycle_and_bounds(kind):
    clip = SceneClip(id="fx", name="FX", kind=kind, loop=True)
    first = particles_at(clip, 1.5)
    assert first and first != particles_at(clip, 2)
    assert first == particles_at(clip, 1.5)
    assert not particles_at(clip, 5)
    assert not particles_at(clip, -1)
    assert len(particles_at(clip.model_copy(update={"intensity": 10}), 1)) <= 1000
    assert not particles_at(clip.model_copy(update={"loop": False}), 4.5)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_invalid_sequence_times_rejected(value):
    with pytest.raises(ValueError):
        sequence_time(value, SceneSequence())


def test_legacy_document_unchanged_and_engine_export_fail_closed(studio):
    window, _ = studio
    document = window.professional_session.document
    assert "sequence" not in document.model_dump()
    window.sequence_panel.add_clip("camera")
    document = window.professional_session.document
    generic = build_scene_authoring_export(document, target="generic")
    assert generic["scene"]["sequence"]["clips"]
    for target in ("godot", "unity"):
        with pytest.raises(SceneAuthoringExportError, match="Timeline"):
            build_scene_authoring_export(document, target=target)


def test_close_stops_playback(studio):
    window, _ = studio
    panel = window.sequence_panel
    panel.add_clip("camera")
    panel.toggle_play()
    window.close()
    assert not panel.timer.isActive()
    assert panel.preview is None


def test_missing_audio_asset_is_actionable_and_nonfatal(studio):
    window, app = studio
    panel = window.sequence_panel
    session = window.professional_session
    assert session.add_asset(
        AssetReferenceRecord(id="gone", path="missing-audio.wav", source_path="missing-audio.wav", sha256="0" * 64)
    )
    sequence = SceneSequence(
        clips=[SceneClip(id="missing-audio", name="Áudio ausente", kind="audio", duration=5, asset_id="gone")]
    )
    assert set_sequence(session, sequence)
    panel.seek(1.0)
    app.processEvents()
    assert "missing-audio" in panel._audio_failures
    assert "Áudio ausente/alterado" in window.status_label.text()
    assert panel.preview is not None
    panel.stop()
    assert not panel._audio_failures
