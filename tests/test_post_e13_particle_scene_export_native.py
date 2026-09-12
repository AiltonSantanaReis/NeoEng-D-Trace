"""Contract checks for the authored-particle scene export bridge."""

from __future__ import annotations

import pytest

from src.exporters.scene_authoring_export import (
    SceneAuthoringExportError,
    build_scene_authoring_export,
)
from tests.test_e08_fx_authoring import _document
from tests.test_post_e13_particle_authoring import _system


def _authored_document():
    return _document().model_copy(update={"particle_systems": [_system("spark-fx")]})


def test_native_scene_exports_preserve_authored_particle_systems() -> None:
    document = _authored_document()
    for target in ("godot", "unity"):
        payload = build_scene_authoring_export(document, target=target)
        assert "runtime_particles" in payload["capabilities"]["supported"]
        assert "runtime_particles" not in payload["capabilities"]["unsupported"]
        assert payload["scene"]["particle_systems"][0]["id"] == "spark-fx"
        assert payload["scene"]["particle_systems"][0]["emitters"][0]["id"] == "main"


def test_legacy_native_scene_shape_stays_unchanged_without_particles() -> None:
    payload = build_scene_authoring_export(_document(), target="godot")
    assert "particle_systems" not in payload["scene"]
    assert "runtime_particles" in payload["capabilities"]["supported"]


def test_native_scene_export_rejects_unbound_authored_particle_system() -> None:
    document = _authored_document().model_copy(update={"sockets": []})
    with pytest.raises(SceneAuthoringExportError, match="exactly one VFX socket"):
        build_scene_authoring_export(document, target="unity")


def test_native_importers_materialize_particle_components_from_scene_exports() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    godot = (
        root / "integrations/godot/addons/neoeng_d_trace/professional_scene_importer.gd"
    ).read_text(encoding="utf-8")
    godot_runtime = (
        root / "integrations/godot/addons/neoeng_d_trace/runtime_particles.gd"
    ).read_text(encoding="utf-8")
    unity = (
        root / "integrations/unity/package/com.neoeng.dtrace/Editor/"
        "ProfessionalSceneImportGenerator.cs"
    ).read_text(encoding="utf-8")

    assert "particle_systems" in godot
    assert "Particles_" in godot
    assert "neoeng-d-trace-scene-authoring" in godot_runtime
    assert "ParticleRuntimeJson" in unity
    assert "ConfigureFromJson" in unity
    assert "UNITY_PROFESSIONAL_SCENE_PARTICLES=" in unity
