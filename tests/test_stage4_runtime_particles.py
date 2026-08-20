from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace

import pytest

from src.runtime import (
    ParticleDocumentV1,
    ParticleEmitterRecord,
    ParticleFormatError,
    ParticleSimulation,
    ParticleSimulationError,
    ParticleSourceBindingRecord,
    ParticleValidationError,
    RuntimeHost,
    load_particle_runtime_export,
    load_particle_runtime_export_bytes,
    particle_runtime_export_sha256,
    replay_particle_simulation,
    save_particle_runtime_export,
    serialize_particle_runtime_export,
    validate_particle_runtime_export,
)


def _document(
    *,
    seed: int = 7,
    emission_rate: float = 10.0,
    burst_count: int = 1,
) -> ParticleDocumentV1:
    return ParticleDocumentV1(
        source=ParticleSourceBindingRecord(sha256="a" * 64),
        fixed_dt=0.1,
        max_substeps=4,
        emitters=[
            ParticleEmitterRecord(
                id="smoke",
                seed=seed,
                initial_velocity={"x": 1.0, "y": 2.0, "z": 0.0},
                velocity_spread={"x": 0.25, "y": 0.5, "z": 0.0},
                acceleration={"x": 0.0, "y": -1.0, "z": 0.0},
                emission_rate=emission_rate,
                lifetime=0.5,
                max_particles=4,
                burst_count=burst_count,
            )
        ],
    )


def test_particle_contract_is_canonical_hash_bound_and_authorial_only() -> None:
    document = _document()
    raw = serialize_particle_runtime_export(document)

    assert raw == serialize_particle_runtime_export(document)
    assert raw.endswith(b"\n")
    assert particle_runtime_export_sha256(document) == hashlib.sha256(raw).hexdigest()

    payload = json.loads(raw)
    assert payload["format_id"] == "neoeng-d-trace-runtime-particles"
    assert payload["schema_version"] == 1
    assert payload["algorithm_version"] == 1
    assert "particles" not in payload
    assert "simulation_time" not in payload
    assert "rng_state" not in payload
    assert validate_particle_runtime_export(payload) == document
    assert load_particle_runtime_export_bytes(raw) == document


@pytest.mark.parametrize(
    "raw",
    [
        lambda valid: b"\xef\xbb\xbf" + valid,
        lambda valid: b'{"format_id":"x","format_id":"y"}',
        lambda valid: valid.replace(b"\n", b"", 1),
        lambda valid: valid.replace(b'"schema_version": 1', b'"schema_version": 2'),
    ],
)
def test_particle_loader_rejects_noncanonical_or_invalid_bytes(raw) -> None:
    valid = serialize_particle_runtime_export(_document())
    with pytest.raises(ParticleFormatError):
        load_particle_runtime_export_bytes(raw(valid))


def test_particle_contract_rejects_duplicate_ids_limits_and_unknown_fields() -> None:
    payload = _document().model_dump(mode="json")

    duplicate = copy.deepcopy(payload)
    duplicate["emitters"].append(copy.deepcopy(duplicate["emitters"][0]))
    with pytest.raises(ParticleValidationError, match="IDs"):
        validate_particle_runtime_export(duplicate)

    too_many = copy.deepcopy(payload)
    too_many["emitters"][0]["max_particles"] = 100_001
    with pytest.raises(ParticleValidationError):
        validate_particle_runtime_export(too_many)

    unknown = copy.deepcopy(payload)
    unknown["emitters"][0]["unexpected"] = True
    with pytest.raises(ParticleValidationError):
        validate_particle_runtime_export(unknown)


def test_particle_simulation_uses_fixed_steps_and_seeded_determinism() -> None:
    first = ParticleSimulation(_document())
    second = ParticleSimulation(_document())
    first.start()
    second.start()

    first.advance(0.05)
    second.advance(0.05)
    assert first.snapshot.tick_index == 0
    assert first.snapshot.particle_count == 0

    first.advance(0.05)
    second.advance(0.05)
    assert first.snapshot.tick_index == 1
    assert first.snapshot == second.snapshot
    assert first.states() == second.states()

    different = ParticleSimulation(_document(seed=8))
    different.start()
    different.advance(0.1)
    assert different.snapshot.state_sha256 != first.snapshot.state_sha256

    zero_seed = ParticleSimulation(_document(seed=0))
    one_seed = ParticleSimulation(_document(seed=1))
    zero_seed.start()
    one_seed.start()
    zero_seed.advance(0.1)
    one_seed.advance(0.1)
    assert zero_seed.snapshot.state_sha256 != one_seed.snapshot.state_sha256


def test_particle_simulation_enforces_pause_and_lifetime_limits() -> None:
    simulation = ParticleSimulation(_document(emission_rate=0.0))
    simulation.start()
    simulation.advance(0.1)
    before_pause = simulation.snapshot
    simulation.pause()

    with pytest.raises(ParticleSimulationError, match="running"):
        simulation.advance(0.1)
    assert simulation.snapshot == replace(before_pause, phase="paused")

    simulation.resume()
    simulation.advance(0.4)
    assert simulation.snapshot.particle_count == 0

    with pytest.raises(ParticleSimulationError, match="catch-up"):
        simulation.advance(0.5)


def test_particle_replay_is_reproducible_and_hash_bound() -> None:
    document = _document()
    simulation = ParticleSimulation(document)
    simulation.start()
    simulation.begin_replay_recording()
    simulation.advance(0.1)
    simulation.advance(0.2)
    tape = simulation.finish_replay_recording()

    replayed = replay_particle_simulation(document, tape)
    assert replayed == simulation.snapshot

    changed = _document(seed=99)
    with pytest.raises(ParticleSimulationError, match="document hash"):
        replay_particle_simulation(changed, tape)

    with pytest.raises(ParticleSimulationError, match="fixed_dt"):
        replay_particle_simulation(
            document,
            replace(tape, fixed_dt=0.2),
        )


def test_particle_replay_recording_rejects_duplicate_recorders() -> None:
    simulation = ParticleSimulation(_document())
    simulation.start()
    with pytest.raises(ParticleSimulationError, match="not active"):
        simulation.finish_replay_recording()
    simulation.begin_replay_recording()
    with pytest.raises(ParticleSimulationError, match="already active"):
        simulation.begin_replay_recording()


def test_particle_export_is_atomic_and_rejects_invalid_destinations(tmp_path) -> None:
    document = _document()
    destination = tmp_path / "particles.json"
    save_particle_runtime_export(document, destination)
    assert destination.read_bytes() == serialize_particle_runtime_export(document)

    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(ParticleValidationError, match="directory"):
        save_particle_runtime_export(document, directory)

    with pytest.raises(ParticleValidationError, match="parent"):
        save_particle_runtime_export(document, tmp_path / "missing" / "particles.json")


def test_runtime_host_advertises_particles_as_native_capability() -> None:
    host = RuntimeHost()
    assert "runtime.particles" in host.supported_capabilities
    decision = host.negotiate([]).decisions
    assert decision == ()


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("emitters", 0, "seed"), True),
        (("emitters", 0, "seed"), -1),
        (("emitters", 0, "emission_rate"), "invalid"),
        (("emitters", 0, "emission_rate"), float("nan")),
        (("emitters", 0, "lifetime"), 0.0),
        (("emitters", 0, "max_particles"), True),
        (("emitters", 0, "max_particles"), 0),
        (("emitters", 0, "burst_count"), 5),
        (("fixed_dt",), True),
        (("fixed_dt",), 0.0),
        (("max_substeps",), True),
        (("max_substeps",), 0),
    ],
)
def test_particle_contract_rejects_invalid_numeric_and_limit_inputs(
    path, value
) -> None:
    payload = _document().model_dump(mode="json")
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(ParticleValidationError):
        validate_particle_runtime_export(payload)


def test_particle_contract_rejects_vector_bounds_and_total_capacity() -> None:
    vector_payload = _document().model_dump(mode="json")
    vector_payload["emitters"][0]["initial_velocity"]["x"] = 1_000_001.0
    with pytest.raises(ParticleValidationError):
        validate_particle_runtime_export(vector_payload)

    capacity_payload = _document().model_dump(mode="json")
    capacity_payload["emitters"] = [
        dict(capacity_payload["emitters"][0], id="a", max_particles=100_000),
        dict(capacity_payload["emitters"][0], id="b", max_particles=100_000),
        dict(capacity_payload["emitters"][0], id="c", max_particles=1),
    ]
    with pytest.raises(ParticleValidationError, match="particle limit"):
        validate_particle_runtime_export(capacity_payload)


def test_particle_loader_and_runtime_lifecycle_fail_closed(tmp_path) -> None:
    with pytest.raises(ParticleFormatError):
        load_particle_runtime_export_bytes("not-bytes")  # type: ignore[arg-type]
    with pytest.raises(ParticleFormatError):
        load_particle_runtime_export_bytes(b"\xff")
    with pytest.raises(ParticleFormatError):
        load_particle_runtime_export_bytes(b" " * 2_000_001)
    with pytest.raises(ParticleFormatError):
        load_particle_runtime_export(tmp_path / "missing.json")

    simulation = ParticleSimulation(_document(emission_rate=0.0))
    with pytest.raises(ParticleSimulationError, match="running"):
        simulation.advance(0.1)
    with pytest.raises(ParticleSimulationError, match="running"):
        simulation.pause()
    with pytest.raises(ParticleSimulationError, match="paused"):
        simulation.resume()
    simulation.start()
    with pytest.raises(ParticleSimulationError, match="current phase"):
        simulation.start()
    simulation.stop()
    simulation.start()
    simulation.pause()
    simulation.resume()
    simulation.stop()


def test_particle_replay_rejects_format_algorithm_and_length_drift() -> None:
    simulation = ParticleSimulation(_document())
    simulation.start()
    simulation.begin_replay_recording()
    simulation.advance(0.1)
    tape = simulation.finish_replay_recording()

    with pytest.raises(ParticleSimulationError, match="format"):
        replay_particle_simulation(
            simulation.document,
            replace(tape, format_id="invalid"),
        )
    with pytest.raises(ParticleSimulationError, match="algorithm"):
        replay_particle_simulation(
            simulation.document,
            replace(tape, algorithm_version=2),
        )
    with pytest.raises(ParticleSimulationError, match="tick"):
        replay_particle_simulation(
            simulation.document,
            replace(tape, elapsed_requests=(0.0,) * 100_001),
        )
