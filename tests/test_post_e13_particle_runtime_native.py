from __future__ import annotations

from pathlib import Path

from scripts.audit_post_e13_particle_runtime import _native_payload
from src.runtime.particles import ParticleSimulation, load_particle_runtime_export_bytes


ROOT = Path(__file__).resolve().parents[1]


def test_post_e13_native_fixture_preserves_runtime_contract_and_count() -> None:
    payload, sidecars, _scenario = _native_payload()
    for engine in ("godot", "unity"):
        decision = next(
            item
            for item in payload["capabilities"][engine]["support"]
            if item["id"] == "runtime.particles"
        )
        assert decision["compatibility"] == "native"
        assert decision["mode"] == "native-deterministic-particle-system"

    document = load_particle_runtime_export_bytes(sidecars["runtime.particles"])
    simulation = ParticleSimulation(document)
    simulation.start()
    for _index in range(3):
        simulation.advance(0.1)
    assert simulation.snapshot.particle_count == 7


def test_post_e13_adapters_consume_and_render_particle_state() -> None:
    godot = (
        ROOT
        / "integrations"
        / "godot"
        / "addons"
        / "neoeng_d_trace"
        / "runtime_adapter.gd"
    ).read_text(encoding="utf-8")
    godot_particles = (
        ROOT
        / "integrations"
        / "godot"
        / "addons"
        / "neoeng_d_trace"
        / "runtime_particles.gd"
    ).read_text(encoding="utf-8")
    unity_editor = (
        ROOT
        / "integrations"
        / "unity"
        / "package"
        / "com.neoeng.dtrace"
        / "Editor"
        / "RuntimeAdapterGenerator.cs"
    ).read_text(encoding="utf-8")
    unity_runtime = (
        ROOT
        / "integrations"
        / "unity"
        / "package"
        / "com.neoeng.dtrace"
        / "Runtime"
        / "NeoEngRuntimeParticles.cs"
    ).read_text(encoding="utf-8")

    assert '"NeoEngRuntimeParticles"' in godot
    assert "advance_fixed_ticks" in godot
    assert "draw_circle" in godot_particles
    assert "ConfigureFromJson" in unity_editor
    assert "AdvanceFixedTicks" in unity_editor
    assert "SetParticles" in unity_runtime
    assert "RUNTIME_ADAPTER_PARTICLES=SUCCESS" in unity_editor


def test_post_e13_failure_guard_remains_explicit() -> None:
    unity_editor = (
        ROOT
        / "integrations"
        / "unity"
        / "package"
        / "com.neoeng.dtrace"
        / "Editor"
        / "RuntimeAdapterGenerator.cs"
    ).read_text(encoding="utf-8")
    assert "ValidateFile" in unity_editor
    assert "RUNTIME_ADAPTER_FAILURE=" in unity_editor
