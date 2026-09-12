"""Post-E13 authored particle systems, runtime preview and persistence checks."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record
from src.persistence.scene_authoring_io import serialize_scene_authoring
from src.persistence.scene_authoring_schema import (
    SceneLightSocketRecord,
    SceneParticleSystemRecord,
    SceneVfxSocketRecord,
)
from src.runtime.particles import ParticleEmitterRecord, ParticleSimulation
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import (
    SceneAuthoringViewport,
    SceneParticleGraphicsItem,
)
from tests.test_e08_fx_authoring import _document


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _system(system_id: str = "fountain") -> SceneParticleSystemRecord:
    return SceneParticleSystemRecord(
        id=system_id,
        loop=True,
        duration=1.5,
        emitters=[
            ParticleEmitterRecord(
                id="main",
                seed=17,
                initial_velocity=Point3Record(x=12.0, y=-36.0, z=0.0),
                velocity_spread=Point3Record(x=8.0, y=12.0, z=0.0),
                acceleration=Point3Record(x=0.0, y=28.0, z=0.0),
                emission_rate=30.0,
                lifetime=1.0,
                max_particles=48,
                burst_count=4,
            )
        ],
    )


def test_legacy_v2_wire_shape_stays_unchanged_without_particle_systems() -> None:
    document = _document()
    payload = document.model_dump()
    assert "particle_systems" not in payload

    authored = document.model_copy(
        update={
            "particle_systems": [_system()],
            "sockets": [
                SceneVfxSocketRecord(
                    id="fountain-socket",
                    layer_id="layer",
                    position=Point3Record(x=40.0, y=80.0, z=0.0),
                    effect_id="fountain",
                )
            ],
        }
    )
    raw = serialize_scene_authoring(authored)
    assert b"particle_systems" in raw
    assert authored.particle_systems[0].runtime_document().emitters[0].id == "main"


def test_authored_particle_system_uses_deterministic_runtime_lifecycle() -> None:
    document = _system().runtime_document()
    first = ParticleSimulation(document)
    second = ParticleSimulation(document)
    first.start()
    second.start()
    first.advance(0.125)
    first.advance(0.125)
    second.advance(0.125)
    second.advance(0.125)
    assert first.states()
    assert first.states() == second.states()
    assert first.snapshot.particle_count == len(first.states())


def test_session_authored_vfx_is_undoable_and_redoable() -> None:
    document = _document().model_copy(update={"sockets": []})
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    socket = SceneVfxSocketRecord(
        id="fountain-socket",
        layer_id="layer",
        position=Point3Record(x=40.0, y=80.0, z=0.0),
        effect_id="fountain",
        scale=1.25,
    )
    assert session.add_socket(socket, _system())
    assert session.document.particle_systems[0].id == "fountain"
    assert session.undo()
    assert session.document.sockets == []
    assert session.redo()
    assert session.document.particle_systems[0].emitters[0].emission_rate == 30.0


def test_viewport_particle_item_samples_authored_system_and_loop() -> None:
    item = SceneParticleGraphicsItem("fountain", 1.0, system=_system())
    initial = item._states
    item.set_preview_time(0.35)
    assert item.has_authored_system
    assert item._states
    assert item._states != initial
    item.set_preview_time(1.85)
    wrapped = item._states
    item.set_preview_time(0.35)
    assert item._states == wrapped


def test_inspector_can_create_and_edit_authored_vfx_in_portuguese(
    qt_app: QApplication,
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    inspector = SceneAuthoringInspector(session)
    try:
        inspector.update_language("pt")
        inspector.socket_id.setText("fountain-socket")
        inspector.socket_type.setCurrentText("vfx")
        inspector.socket_effect_id.setText("fountain")
        inspector.socket_x.setValue(40.0)
        inspector.socket_y.setValue(80.0)
        inspector.particle_emission_rate.setValue(36.0)
        inspector.particle_burst_count.setValue(6)
        inspector._add_socket()
        assert session.document.particle_systems[0].id == "fountain"
        assert session.document.particle_systems[0].emitters[0].emission_rate == 36.0
        inspector.particle_emission_rate.setValue(48.0)
        inspector._update_socket()
        assert session.document.particle_systems[0].emitters[0].emission_rate == 48.0
        assert (
            inspector._field_labels["particle_emission_rate"].text()
            == "Taxa de emissão"
        )
        assert inspector.particle_preview_button.text() == "Reproduzir partículas"
    finally:
        inspector.close()
        qt_app.processEvents()


def test_switching_existing_socket_to_vfx_enables_native_add_controls(
    qt_app: QApplication,
) -> None:
    document = _document().model_copy(
        update={
            "sockets": [
                SceneLightSocketRecord(
                    id="key-light",
                    layer_id="layer",
                    position=Point3Record(x=20.0, y=30.0, z=0.0),
                    color="#ffffff",
                )
            ],
            "particle_systems": [],
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    inspector = SceneAuthoringInspector(session)
    try:
        inspector.socket_type.setCurrentText("vfx")
        assert inspector.socket_effect_id.isEnabled()
        assert inspector.particle_preview_button.isEnabled()
        assert inspector.socket_enabled.isChecked()
        inspector.socket_id.setText("fountain-socket")
        inspector.socket_effect_id.setText("fountain")
        inspector._add_socket()
        socket = next(
            item for item in session.document.sockets if item.id == "fountain-socket"
        )
        assert isinstance(socket, SceneVfxSocketRecord)
        assert socket.enabled
        assert session.document.particle_systems[0].id == "fountain"
    finally:
        inspector.close()
        qt_app.processEvents()


def test_viewport_runs_authored_preview_only_when_preview_is_enabled(
    qt_app: QApplication, tmp_path
) -> None:
    document = _document().model_copy(
        update={
            "particle_systems": [_system()],
            "sockets": [
                SceneVfxSocketRecord(
                    id="fountain-socket",
                    layer_id="layer",
                    position=Point3Record(x=40.0, y=80.0, z=0.0),
                    effect_id="fountain",
                )
            ],
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    try:
        assert not viewport._particle_preview_timer.isActive()
        viewport.set_preview_enabled(True)
        qt_app.processEvents()
        assert viewport._particle_preview_timer.isActive()
        viewport.reset_particle_preview()
        assert viewport._particle_items["fountain-socket"].preview_time == 0.0
        viewport.set_preview_enabled(False)
        assert not viewport._particle_preview_timer.isActive()
    finally:
        viewport.close()
        qt_app.processEvents()
