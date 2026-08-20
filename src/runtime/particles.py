"""Deterministic, versioned particle simulation for the runtime ADR.

The particle document is a sidecar to the existing scenario-runtime export. It
stores authorial emitter configuration only. Simulation state, random state and
replay tapes are transient and are never written into the authorial document.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_schema import Point3Record, StrictProjectModel

PARTICLES_FORMAT_ID: Literal["neoeng-d-trace-runtime-particles"] = (
    "neoeng-d-trace-runtime-particles"
)
PARTICLES_SCHEMA_VERSION: Literal[1] = 1
PARTICLES_API_VERSION: Literal[1] = 1
PARTICLES_SOURCE_FORMAT_ID: Literal["neoeng-d-trace-scenario-runtime"] = (
    "neoeng-d-trace-scenario-runtime"
)
PARTICLES_SOURCE_SCHEMA_VERSION: Literal[1] = 1
PARTICLE_ALGORITHM_VERSION: Literal[1] = 1

MAX_PARTICLE_ID_LENGTH = 128
MAX_PARTICLE_EMITTERS = 1_024
MAX_PARTICLES_PER_EMITTER = 100_000
MAX_TOTAL_PARTICLES = 200_000
MAX_PARTICLE_REPLAY_TICKS = 100_000
MAX_PARTICLE_LIFETIME = 3_600.0
MAX_PARTICLE_EMISSION_RATE = 100_000.0
MAX_PARTICLE_SPEED = 1_000_000.0
MAX_PARTICLE_FIXED_DT = 1.0
MAX_PARTICLE_SUBSTEPS = 8
_UINT32_MASK = 0xFFFFFFFF
_UINT32_SCALE = 1.0 / 4_294_967_296.0


class ParticleRuntimeError(ValueError):
    """Base class for controlled particle contract and runtime failures."""


class ParticleFormatError(ParticleRuntimeError):
    """Raised when particle bytes are not canonical UTF-8 JSON."""


class ParticleValidationError(ParticleRuntimeError):
    """Raised when an authorial particle document violates its contract."""


class ParticleSimulationError(ParticleRuntimeError):
    """Raised when a simulation operation cannot be completed safely."""


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _bounded(value: float, field: str, minimum: float, maximum: float) -> float:
    number = _finite(value, field)
    if number < minimum or number > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return number


def _non_negative_int(value: int, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < 0 or value > maximum:
        raise ValueError(f"{field} must be between 0 and {maximum}")
    return value


class ParticleSourceBindingRecord(StrictProjectModel):
    """Exact scenario-runtime export to which this sidecar is bound."""

    format_id: Literal["neoeng-d-trace-scenario-runtime"] = PARTICLES_SOURCE_FORMAT_ID
    schema_version: Literal[1] = PARTICLES_SOURCE_SCHEMA_VERSION
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class ParticleEmitterRecord(StrictProjectModel):
    """Bounded authorial configuration for one deterministic emitter."""

    id: str = Field(min_length=1, max_length=MAX_PARTICLE_ID_LENGTH)
    enabled: bool = True
    seed: int = 1
    origin: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0)
    initial_velocity: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0)
    velocity_spread: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0)
    acceleration: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0)
    emission_rate: float = 0.0
    lifetime: float = 1.0
    max_particles: int = 1
    burst_count: int = 0

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        return _non_negative_int(value, "emitter.seed", _UINT32_MASK)

    @field_validator("emission_rate")
    @classmethod
    def validate_emission_rate(cls, value: float) -> float:
        return _bounded(
            value,
            "emitter.emission_rate",
            0.0,
            MAX_PARTICLE_EMISSION_RATE,
        )

    @field_validator("lifetime")
    @classmethod
    def validate_lifetime(cls, value: float) -> float:
        return _bounded(value, "emitter.lifetime", 0.000001, MAX_PARTICLE_LIFETIME)

    @field_validator("max_particles")
    @classmethod
    def validate_max_particles(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("emitter.max_particles must be an integer")
        if value < 1 or value > MAX_PARTICLES_PER_EMITTER:
            raise ValueError(
                "emitter.max_particles must be between "
                f"1 and {MAX_PARTICLES_PER_EMITTER}"
            )
        return value

    @field_validator("burst_count")
    @classmethod
    def validate_burst_count(cls, value: int) -> int:
        return _non_negative_int(
            value,
            "emitter.burst_count",
            MAX_PARTICLES_PER_EMITTER,
        )

    @field_validator("initial_velocity", "velocity_spread", "acceleration")
    @classmethod
    def validate_vector(cls, value: Point3Record, info) -> Point3Record:
        for component in (value.x, value.y, value.z):
            _bounded(
                component,
                f"emitter.{info.field_name}",
                -MAX_PARTICLE_SPEED,
                MAX_PARTICLE_SPEED,
            )
        return value

    @model_validator(mode="after")
    def validate_burst_limit(self) -> "ParticleEmitterRecord":
        if self.burst_count > self.max_particles:
            raise ValueError("emitter.burst_count cannot exceed max_particles")
        return self


class ParticleDocumentV1(StrictProjectModel):
    """Version 1 authorial particle sidecar."""

    format_id: Literal["neoeng-d-trace-runtime-particles"] = PARTICLES_FORMAT_ID
    schema_version: Literal[1] = PARTICLES_SCHEMA_VERSION
    algorithm_version: Literal[1] = PARTICLE_ALGORITHM_VERSION
    source: ParticleSourceBindingRecord
    fixed_dt: float = 1.0 / 60.0
    max_substeps: int = MAX_PARTICLE_SUBSTEPS
    emitters: list[ParticleEmitterRecord] = Field(
        min_length=1,
        max_length=MAX_PARTICLE_EMITTERS,
    )

    @field_validator("fixed_dt")
    @classmethod
    def validate_fixed_dt(cls, value: float) -> float:
        return _bounded(value, "particles.fixed_dt", 0.000001, MAX_PARTICLE_FIXED_DT)

    @field_validator("max_substeps")
    @classmethod
    def validate_max_substeps(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("particles.max_substeps must be an integer")
        if value < 1 or value > MAX_PARTICLE_SUBSTEPS:
            raise ValueError(
                "particles.max_substeps must be between 1 and "
                f"{MAX_PARTICLE_SUBSTEPS}"
            )
        return value

    @model_validator(mode="after")
    def validate_emitters(self) -> "ParticleDocumentV1":
        ids = [emitter.id for emitter in self.emitters]
        if len(ids) != len(set(ids)):
            raise ValueError("particle emitter IDs must be unique")
        total = sum(emitter.max_particles for emitter in self.emitters)
        if total > MAX_TOTAL_PARTICLES:
            raise ValueError(
                f"particle document exceeds the {MAX_TOTAL_PARTICLES} particle limit"
            )
        return self


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ParticleValidationError(
            f"particle document cannot be serialized: {exc}"
        ) from exc
    return (text + "\n").encode("utf-8")


def _validated_document(payload: object) -> ParticleDocumentV1:
    if isinstance(payload, ParticleDocumentV1):
        return payload
    if not isinstance(payload, Mapping):
        raise ParticleValidationError("particle document root must be an object")
    try:
        return ParticleDocumentV1.model_validate(payload, strict=True)
    except Exception as exc:
        raise ParticleValidationError(str(exc)) from exc


def build_particle_runtime_export(
    document: ParticleDocumentV1 | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and copy authorial particle configuration for export."""

    return _validated_document(document).model_dump(mode="json")


def serialize_particle_runtime_export(
    document: ParticleDocumentV1 | Mapping[str, Any],
) -> bytes:
    """Serialize only authorial state as canonical UTF-8 JSON."""

    payload = build_particle_runtime_export(document)
    encoded = _canonical_json_bytes(payload)
    if len(encoded) > MAX_PROJECT_FILE_BYTES:
        raise ParticleValidationError(
            "particle document exceeds the project file limit"
        )
    return encoded


def particle_runtime_export_sha256(
    document: ParticleDocumentV1 | Mapping[str, Any],
) -> str:
    """Return the hash of the exact canonical authorial sidecar bytes."""

    return hashlib.sha256(serialize_particle_runtime_export(document)).hexdigest()


def validate_particle_runtime_export(payload: Mapping[str, Any]) -> ParticleDocumentV1:
    """Strictly validate a decoded particle payload."""

    return _validated_document(payload)


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_particle_runtime_export_bytes(raw: bytes) -> ParticleDocumentV1:
    """Load canonical particle bytes, rejecting ambiguous JSON."""

    if not isinstance(raw, bytes):
        raise ParticleFormatError("particle manifest bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise ParticleFormatError("particle manifest exceeds the file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ParticleFormatError("UTF-8 BOM is not allowed")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as exc:
        raise ParticleFormatError(f"invalid particle JSON: {exc}") from exc
    try:
        document = _validated_document(payload)
    except ParticleValidationError as exc:
        raise ParticleFormatError(f"invalid particle manifest: {exc}") from exc
    if raw != serialize_particle_runtime_export(document):
        raise ParticleFormatError("particle manifest bytes are not canonical")
    return document


def load_particle_runtime_export(path: str | os.PathLike[str]) -> ParticleDocumentV1:
    """Load a canonical particle sidecar from disk."""

    candidate = Path(path)
    try:
        raw = candidate.read_bytes()
    except OSError as exc:
        raise ParticleFormatError(f"particle manifest cannot be read: {exc}") from exc
    return load_particle_runtime_export_bytes(raw)


def save_particle_runtime_export(
    document: ParticleDocumentV1 | Mapping[str, Any],
    destination: str | os.PathLike[str],
) -> None:
    """Atomically replace one authorial particle sidecar."""

    path = Path(destination)
    if path.exists() and path.is_dir():
        raise ParticleValidationError("particle export destination is a directory")
    if not path.parent.exists() or not path.parent.is_dir():
        raise ParticleValidationError(
            "particle export destination parent directory does not exist"
        )
    payload = serialize_particle_runtime_export(document)
    transaction = AtomicOutputTransaction()
    try:
        with transaction as active:
            staged = active.stage_path(str(path))
            Path(staged).write_bytes(payload)
            active.commit()
    except (OSError, ValueError) as exc:
        raise ParticleValidationError(f"failed to save particle export: {exc}") from exc


@dataclass
class _Particle:
    particle_id: int
    age: float
    position: list[float]
    velocity: list[float]


@dataclass
class _EmitterState:
    rng_state: int
    emission_remainder: float
    burst_pending: int
    next_particle_id: int
    particles: list[_Particle]


@dataclass(frozen=True)
class ParticleStateRecord:
    """Immutable observable particle state for tests and previews."""

    emitter_id: str
    particle_id: int
    age: float
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]


@dataclass(frozen=True)
class ParticleSimulationSnapshot:
    """Deterministic simulation state; never serialized as authorial data."""

    phase: Literal["ready", "running", "paused", "stopped"]
    fixed_dt: float
    tick_index: int
    simulation_time: float
    accumulator: float
    particle_count: int
    state_sha256: str


@dataclass(frozen=True)
class ParticleReplayV1:
    """Transient replay tape bound to one exact authorial document."""

    format_id: str
    algorithm_version: int
    document_sha256: str
    fixed_dt: float
    elapsed_requests: tuple[float, ...]


def _next_random(state: int) -> tuple[int, float]:
    next_state = (1_664_525 * state + 1_013_904_223) & _UINT32_MASK
    return next_state, next_state * _UINT32_SCALE


class ParticleSimulation:
    """Fixed-step deterministic particle simulator with pause and replay."""

    def __init__(self, document: ParticleDocumentV1) -> None:
        self._document = _validated_document(document)
        self._phase: Literal["ready", "running", "paused", "stopped"] = "ready"
        self._tick_index = 0
        self._simulation_time = 0.0
        self._accumulator = 0.0
        self._emitters = {
            emitter.id: _EmitterState(
                rng_state=emitter.seed,
                emission_remainder=0.0,
                burst_pending=emitter.burst_count,
                next_particle_id=0,
                particles=[],
            )
            for emitter in self._ordered_emitters()
        }
        self._recording: list[float] | None = None

    @property
    def document(self) -> ParticleDocumentV1:
        return self._document

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def snapshot(self) -> ParticleSimulationSnapshot:
        states = self.states()
        emitter_state = [
            {
                "id": emitter.id,
                "rng_state": self._emitters[emitter.id].rng_state,
                "emission_remainder": self._emitters[emitter.id].emission_remainder,
                "burst_pending": self._emitters[emitter.id].burst_pending,
                "next_particle_id": self._emitters[emitter.id].next_particle_id,
            }
            for emitter in self._ordered_emitters()
        ]
        encoded = _canonical_json_bytes(
            {
                "tick_index": self._tick_index,
                "simulation_time": self._simulation_time,
                "accumulator": self._accumulator,
                "emitters": emitter_state,
                "particles": [
                    {
                        "id": state.emitter_id,
                        "particle_id": state.particle_id,
                        "age": state.age,
                        "position": state.position,
                        "velocity": state.velocity,
                    }
                    for state in states
                ],
            }
        )
        return ParticleSimulationSnapshot(
            phase=self._phase,
            fixed_dt=self._document.fixed_dt,
            tick_index=self._tick_index,
            simulation_time=self._simulation_time,
            accumulator=self._accumulator,
            particle_count=len(states),
            state_sha256=hashlib.sha256(encoded).hexdigest(),
        )

    def _ordered_emitters(self) -> tuple[ParticleEmitterRecord, ...]:
        return tuple(sorted(self._document.emitters, key=lambda item: item.id))

    def start(self) -> ParticleSimulationSnapshot:
        if self._phase not in {"ready", "paused", "stopped"}:
            raise ParticleSimulationError("cannot start from the current phase")
        self._phase = "running"
        return self.snapshot

    def pause(self) -> ParticleSimulationSnapshot:
        if self._phase != "running":
            raise ParticleSimulationError("pause requires a running simulation")
        self._phase = "paused"
        return self.snapshot

    def resume(self) -> ParticleSimulationSnapshot:
        if self._phase != "paused":
            raise ParticleSimulationError("resume requires a paused simulation")
        self._phase = "running"
        return self.snapshot

    def stop(self) -> ParticleSimulationSnapshot:
        if self._phase not in {"ready", "running", "paused", "stopped"}:
            raise ParticleSimulationError("stop requires an active simulation")
        self._phase = "stopped"
        return self.snapshot

    def begin_replay_recording(self) -> None:
        if self._recording is not None:
            raise ParticleSimulationError("replay recording is already active")
        self._recording = []

    def finish_replay_recording(self) -> ParticleReplayV1:
        if self._recording is None:
            raise ParticleSimulationError("replay recording is not active")
        tape = ParticleReplayV1(
            format_id=PARTICLES_FORMAT_ID,
            algorithm_version=PARTICLE_ALGORITHM_VERSION,
            document_sha256=particle_runtime_export_sha256(self._document),
            fixed_dt=self._document.fixed_dt,
            elapsed_requests=tuple(self._recording),
        )
        self._recording = None
        return tape

    def advance(self, elapsed: float) -> ParticleSimulationSnapshot:
        if self._phase != "running":
            raise ParticleSimulationError("advance requires a running simulation")
        value = _finite(elapsed, "particles.elapsed")
        if value < 0.0 or value > self._document.fixed_dt * self._document.max_substeps:
            raise ParticleSimulationError(
                "elapsed exceeds the fixed-step catch-up limit"
            )
        if self._recording is not None:
            if len(self._recording) >= MAX_PARTICLE_REPLAY_TICKS:
                raise ParticleSimulationError("replay tick limit exceeded")
            self._recording.append(value)
        candidate = self._accumulator + value
        steps = int(math.floor(candidate / self._document.fixed_dt + 1e-12))
        if steps > self._document.max_substeps:
            raise ParticleSimulationError("fixed-step catch-up limit exceeded")
        for _ in range(steps):
            self._step(self._document.fixed_dt)
        self._accumulator = candidate - steps * self._document.fixed_dt
        self._tick_index += steps
        self._simulation_time += steps * self._document.fixed_dt
        return self.snapshot

    def states(self) -> tuple[ParticleStateRecord, ...]:
        result: list[ParticleStateRecord] = []
        for emitter in self._ordered_emitters():
            state = self._emitters[emitter.id]
            for particle in sorted(state.particles, key=lambda item: item.particle_id):
                result.append(
                    ParticleStateRecord(
                        emitter_id=emitter.id,
                        particle_id=particle.particle_id,
                        age=particle.age,
                        position=(
                            particle.position[0],
                            particle.position[1],
                            particle.position[2],
                        ),
                        velocity=(
                            particle.velocity[0],
                            particle.velocity[1],
                            particle.velocity[2],
                        ),
                    )
                )
        return tuple(result)

    def _step(self, dt: float) -> None:
        for emitter in self._ordered_emitters():
            state = self._emitters[emitter.id]
            if emitter.enabled:
                available = emitter.max_particles - len(state.particles)
                burst = min(state.burst_pending, max(0, available))
                state.burst_pending -= burst
                state.emission_remainder += emitter.emission_rate * dt
                continuous = min(
                    int(math.floor(state.emission_remainder)),
                    max(0, available - burst),
                )
                state.emission_remainder -= continuous
                for _ in range(burst + continuous):
                    self._spawn(emitter, state)
            survivors: list[_Particle] = []
            for particle in state.particles:
                particle.velocity[0] += float(emitter.acceleration.x) * dt
                particle.velocity[1] += float(emitter.acceleration.y) * dt
                particle.velocity[2] += float(emitter.acceleration.z) * dt
                particle.position[0] += particle.velocity[0] * dt
                particle.position[1] += particle.velocity[1] * dt
                particle.position[2] += particle.velocity[2] * dt
                particle.age += dt
                if particle.age < emitter.lifetime:
                    survivors.append(particle)
            state.particles = survivors

    def _spawn(self, emitter: ParticleEmitterRecord, state: _EmitterState) -> None:
        state.rng_state, random_x = _next_random(state.rng_state)
        state.rng_state, random_y = _next_random(state.rng_state)
        state.rng_state, random_z = _next_random(state.rng_state)
        randoms = (
            2.0 * random_x - 1.0,
            2.0 * random_y - 1.0,
            2.0 * random_z - 1.0,
        )
        velocity = [
            float(emitter.initial_velocity.x)
            + float(emitter.velocity_spread.x) * randoms[0],
            float(emitter.initial_velocity.y)
            + float(emitter.velocity_spread.y) * randoms[1],
            float(emitter.initial_velocity.z)
            + float(emitter.velocity_spread.z) * randoms[2],
        ]
        state.particles.append(
            _Particle(
                particle_id=state.next_particle_id,
                age=0.0,
                position=[
                    float(emitter.origin.x),
                    float(emitter.origin.y),
                    float(emitter.origin.z),
                ],
                velocity=velocity,
            )
        )
        state.next_particle_id += 1


def replay_particle_simulation(
    document: ParticleDocumentV1,
    replay: ParticleReplayV1,
) -> ParticleSimulationSnapshot:
    """Replay a tape only when its contract and document hash match."""

    if replay.format_id != PARTICLES_FORMAT_ID:
        raise ParticleSimulationError("unsupported particle replay format")
    if replay.algorithm_version != PARTICLE_ALGORITHM_VERSION:
        raise ParticleSimulationError("unsupported particle replay algorithm")
    if replay.fixed_dt != document.fixed_dt:
        raise ParticleSimulationError(
            "particle replay fixed_dt does not match document"
        )
    if replay.document_sha256 != particle_runtime_export_sha256(document):
        raise ParticleSimulationError("particle replay document hash does not match")
    if len(replay.elapsed_requests) > MAX_PARTICLE_REPLAY_TICKS:
        raise ParticleSimulationError("replay tick limit exceeded")
    simulation = ParticleSimulation(document)
    simulation.start()
    for elapsed in replay.elapsed_requests:
        simulation.advance(elapsed)
    return simulation.snapshot
