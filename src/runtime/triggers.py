"""Deterministic, versioned trigger runtime for the runtime ADR.

Trigger authoring is stored in a sidecar bound to the scenario-runtime export.
Active zones, emitted events and replay frames are transient execution state;
they are never silently written back to the authoring document.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_schema import Point3Record, StrictProjectModel

TRIGGERS_FORMAT_ID: Literal["neoeng-d-trace-runtime-triggers"] = (
    "neoeng-d-trace-runtime-triggers"
)
TRIGGERS_SCHEMA_VERSION: Literal[1] = 1
TRIGGERS_API_VERSION: Literal[1] = 1
TRIGGERS_ALGORITHM_VERSION: Literal[1] = 1
TRIGGERS_SOURCE_FORMAT_ID: Literal["neoeng-d-trace-scenario-runtime"] = (
    "neoeng-d-trace-scenario-runtime"
)
TRIGGERS_SOURCE_SCHEMA_VERSION: Literal[1] = 1

MAX_TRIGGER_ID_LENGTH = 128
MAX_TRIGGER_ZONES = 1_024
MAX_TRIGGER_EVENTS = 2_048
MAX_TRIGGER_CONDITIONS = 16
MAX_TRIGGER_PAYLOAD_KEYS = 32
MAX_TRIGGER_PRIORITY = 1_000_000
MAX_TRIGGER_FIXED_DT = 1.0
MAX_TRIGGER_SUBSTEPS = 8
MAX_TRIGGER_REPLAY_FRAMES = 100_000

TriggerConditionOperator = Literal[
    "eq", "neq", "gt", "gte", "lt", "lte", "truthy", "falsy"
]
TriggerTransition = Literal["enter", "stay", "exit"]


class TriggerRuntimeError(ValueError):
    """Base class for controlled trigger contract/runtime failures."""


class TriggerFormatError(TriggerRuntimeError):
    """Raised when trigger bytes are not canonical UTF-8 JSON."""


class TriggerValidationError(TriggerRuntimeError):
    """Raised when an authorial trigger document is invalid."""


class TriggerExecutionError(TriggerRuntimeError):
    """Raised when trigger execution input or state is invalid."""


class TriggerCancellationError(TriggerExecutionError):
    """Raised when a trigger step is cancelled before commit."""


def _finite(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be a finite number")
    return number


def _bounded(value: float, field_name: str, minimum: float, maximum: float) -> float:
    number = _finite(value, field_name)
    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return number


def _validate_json_value(value: Any, *, field_name: str, depth: int = 0) -> None:
    if depth > 8:
        raise ValueError(f"{field_name} exceeds the nesting limit")
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, bool):
            return
        if isinstance(value, int) and not isinstance(value, bool):
            return
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{field_name} must contain finite numbers")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(
                item, field_name=f"{field_name}[{index}]", depth=depth + 1
            )
        return
    if isinstance(value, dict):
        if len(value) > MAX_TRIGGER_PAYLOAD_KEYS:
            raise ValueError(f"{field_name} exceeds the key limit")
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"{field_name} keys must be non-empty strings")
            _validate_json_value(
                item, field_name=f"{field_name}.{key}", depth=depth + 1
            )
        return
    raise ValueError(f"{field_name} contains a non-JSON value")


class TriggerSourceBindingRecord(StrictProjectModel):
    """Exact scenario-runtime export to which the trigger sidecar is bound."""

    format_id: Literal["neoeng-d-trace-scenario-runtime"] = TRIGGERS_SOURCE_FORMAT_ID
    schema_version: Literal[1] = TRIGGERS_SOURCE_SCHEMA_VERSION
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class TriggerConditionRecord(StrictProjectModel):
    """One deterministic condition evaluated against an observation context."""

    key: str = Field(min_length=1, max_length=MAX_TRIGGER_ID_LENGTH)
    operator: TriggerConditionOperator
    value: Any = None

    @model_validator(mode="after")
    def validate_condition(self) -> "TriggerConditionRecord":
        _validate_json_value(self.value, field_name="condition.value")
        if self.operator in {"gt", "gte", "lt", "lte"}:
            _finite(self.value, "condition.value")
        if self.operator in {"truthy", "falsy"} and self.value is not None:
            raise ValueError(f"{self.operator} conditions must not define value")
        return self


class TriggerEventRecord(StrictProjectModel):
    """Stable event definition emitted by a zone transition."""

    id: str = Field(min_length=1, max_length=MAX_TRIGGER_ID_LENGTH)
    enabled: bool = True
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_json_value(value, field_name="event.payload")
        return value


class TriggerZoneRecord(StrictProjectModel):
    """Axis-aligned bounded trigger zone and its transition bindings."""

    id: str = Field(min_length=1, max_length=MAX_TRIGGER_ID_LENGTH)
    enabled: bool = True
    priority: int = 0
    center: Point3Record
    size: Point3Record
    conditions: list[TriggerConditionRecord] = Field(
        default_factory=list, max_length=MAX_TRIGGER_CONDITIONS
    )
    enter_event_id: str | None = Field(default=None, max_length=MAX_TRIGGER_ID_LENGTH)
    stay_event_id: str | None = Field(default=None, max_length=MAX_TRIGGER_ID_LENGTH)
    exit_event_id: str | None = Field(default=None, max_length=MAX_TRIGGER_ID_LENGTH)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("zone.priority must be a strict integer")
        if value < -MAX_TRIGGER_PRIORITY or value > MAX_TRIGGER_PRIORITY:
            raise ValueError("zone.priority exceeds the trigger limit")
        return value

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: Point3Record) -> Point3Record:
        for coordinate in (value.x, value.y, value.z):
            _bounded(coordinate, "zone.size", 0.000001, float(MAX_TRIGGER_PRIORITY))
        return value


class TriggerDocumentV1(StrictProjectModel):
    """Version 1 authorial trigger sidecar contract."""

    format_id: Literal["neoeng-d-trace-runtime-triggers"] = TRIGGERS_FORMAT_ID
    schema_version: Literal[1] = TRIGGERS_SCHEMA_VERSION
    algorithm_version: Literal[1] = TRIGGERS_ALGORITHM_VERSION
    required_capability: Literal["runtime.triggers"] = "runtime.triggers"
    source: TriggerSourceBindingRecord
    fixed_dt: float = 1.0 / 60.0
    max_substeps: int = MAX_TRIGGER_SUBSTEPS
    zones: list[TriggerZoneRecord] = Field(min_length=1, max_length=MAX_TRIGGER_ZONES)
    events: list[TriggerEventRecord] = Field(
        min_length=1, max_length=MAX_TRIGGER_EVENTS
    )

    @field_validator("fixed_dt")
    @classmethod
    def validate_fixed_dt(cls, value: float) -> float:
        return _bounded(value, "triggers.fixed_dt", 0.000001, MAX_TRIGGER_FIXED_DT)

    @field_validator("max_substeps")
    @classmethod
    def validate_max_substeps(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("triggers.max_substeps must be a strict integer")
        if value < 1 or value > MAX_TRIGGER_SUBSTEPS:
            raise ValueError("triggers.max_substeps exceeds the trigger limit")
        return value

    @model_validator(mode="after")
    def validate_references(self) -> "TriggerDocumentV1":
        zone_ids = [zone.id for zone in self.zones]
        event_ids = [event.id for event in self.events]
        if len(zone_ids) != len(set(zone_ids)):
            raise ValueError("trigger zone IDs must be unique")
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("trigger event IDs must be unique")
        event_set = set(event_ids)
        for zone in self.zones:
            for event_id in (
                zone.enter_event_id,
                zone.stay_event_id,
                zone.exit_event_id,
            ):
                if event_id is not None and event_id not in event_set:
                    raise ValueError(f"zone references unknown event: {event_id}")
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
        raise TriggerValidationError(
            f"trigger document cannot be serialized: {exc}"
        ) from exc
    encoded = (text + "\n").encode("utf-8")
    if len(encoded) > MAX_PROJECT_FILE_BYTES:
        raise TriggerValidationError("trigger document exceeds the project file limit")
    return encoded


def _validated_document(payload: object) -> TriggerDocumentV1:
    if isinstance(payload, TriggerDocumentV1):
        return payload
    if not isinstance(payload, Mapping):
        raise TriggerValidationError("trigger document root must be an object")
    try:
        return TriggerDocumentV1.model_validate(payload, strict=True)
    except Exception as exc:
        raise TriggerValidationError(str(exc)) from exc


def build_trigger_runtime_export(
    document: TriggerDocumentV1 | Mapping[str, Any],
) -> dict[str, Any]:
    return _validated_document(document).model_dump(mode="json")


def serialize_trigger_runtime_export(
    document: TriggerDocumentV1 | Mapping[str, Any],
) -> bytes:
    return _canonical_json_bytes(build_trigger_runtime_export(document))


def trigger_runtime_export_sha256(
    document: TriggerDocumentV1 | Mapping[str, Any],
) -> str:
    return hashlib.sha256(serialize_trigger_runtime_export(document)).hexdigest()


def validate_trigger_runtime_export(payload: Mapping[str, Any]) -> TriggerDocumentV1:
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


def load_trigger_runtime_export_bytes(raw: bytes) -> TriggerDocumentV1:
    if not isinstance(raw, bytes):
        raise TriggerFormatError("trigger manifest bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise TriggerFormatError("trigger manifest exceeds the file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise TriggerFormatError("UTF-8 BOM is not allowed")
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
        raise TriggerFormatError(f"invalid trigger JSON: {exc}") from exc
    try:
        document = _validated_document(payload)
    except TriggerValidationError as exc:
        raise TriggerFormatError(f"invalid trigger manifest: {exc}") from exc
    if raw != serialize_trigger_runtime_export(document):
        raise TriggerFormatError("trigger manifest bytes are not canonical")
    return document


def load_trigger_runtime_export(path: str | Path) -> TriggerDocumentV1:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise TriggerFormatError(f"trigger manifest cannot be read: {exc}") from exc
    return load_trigger_runtime_export_bytes(raw)


def save_trigger_runtime_export(
    document: TriggerDocumentV1 | Mapping[str, Any],
    destination: str | Path,
) -> None:
    path = Path(destination)
    if path.exists() and path.is_dir():
        raise TriggerValidationError("trigger export destination is a directory")
    if not path.parent.exists() or not path.parent.is_dir():
        raise TriggerValidationError("trigger export parent directory does not exist")
    payload = serialize_trigger_runtime_export(document)
    transaction = AtomicOutputTransaction()
    try:
        with transaction as active:
            staged = active.stage_path(str(path))
            Path(staged).write_bytes(payload)
            active.commit()
    except (OSError, ValueError) as exc:
        raise TriggerValidationError(f"failed to save trigger export: {exc}") from exc


def verify_trigger_source_binding(
    document: TriggerDocumentV1 | Mapping[str, Any],
    source_bytes: bytes,
) -> None:
    if not isinstance(source_bytes, bytes):
        raise TriggerValidationError("source bytes must be bytes")
    validated = _validated_document(document)
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != validated.source.sha256:
        raise TriggerValidationError("trigger sidecar is not bound to source bytes")


@dataclass(frozen=True)
class TriggerObservation:
    """One object position and its deterministic condition context."""

    object_id: str
    position: Point3Record
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TriggerEvent:
    """One emitted transition event."""

    event_id: str
    transition: TriggerTransition
    zone_id: str
    object_id: str
    priority: int
    tick_index: int
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class TriggerRuntimeSnapshot:
    phase: Literal["ready", "running", "paused", "stopped"]
    document_sha256: str
    fixed_dt: float
    tick_index: int
    simulation_time: float
    accumulator: float
    active_pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class TriggerStepResult:
    elapsed: float
    steps: int
    tick_index: int
    simulation_time: float
    accumulator: float
    events: tuple[TriggerEvent, ...]


@dataclass(frozen=True)
class TriggerReplayFrame:
    elapsed: float
    observations: tuple[TriggerObservation, ...]


@dataclass(frozen=True)
class TriggerReplayTape:
    """Transient replay tape bound to one exact authorial document."""

    format_id: str
    algorithm_version: int
    document_sha256: str
    fixed_dt: float
    initial_tick_index: int
    initial_simulation_time: float
    initial_accumulator: float
    initial_active_pairs: tuple[tuple[str, str], ...]
    frames: tuple[TriggerReplayFrame, ...]


def _validated_replay_tape(tape: TriggerReplayTape) -> TriggerReplayTape:
    if not isinstance(tape, TriggerReplayTape):
        raise TriggerExecutionError("replay tape must be TriggerReplayTape")
    if tape.format_id != TRIGGERS_FORMAT_ID:
        raise TriggerExecutionError("replay tape format is not supported")
    if tape.algorithm_version != TRIGGERS_ALGORITHM_VERSION:
        raise TriggerExecutionError("replay tape algorithm is not supported")
    if not isinstance(tape.document_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", tape.document_sha256
    ):
        raise TriggerExecutionError("replay tape document hash is invalid")
    _bounded(tape.fixed_dt, "replay.fixed_dt", 0.000001, MAX_TRIGGER_FIXED_DT)
    if (
        isinstance(tape.initial_tick_index, bool)
        or not isinstance(tape.initial_tick_index, int)
        or tape.initial_tick_index < 0
    ):
        raise TriggerExecutionError("replay initial tick index is invalid")
    _finite(tape.initial_simulation_time, "replay.initial_simulation_time")
    _finite(tape.initial_accumulator, "replay.initial_accumulator")
    if len(tape.frames) > MAX_TRIGGER_REPLAY_FRAMES:
        raise TriggerExecutionError("trigger replay frame limit exceeded")
    for pair in tape.initial_active_pairs:
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or any(
                not isinstance(value, str)
                or not value
                or len(value) > MAX_TRIGGER_ID_LENGTH
                for value in pair
            )
        ):
            raise TriggerExecutionError("replay active pair is invalid")
    for frame in tape.frames:
        if not isinstance(frame, TriggerReplayFrame):
            raise TriggerExecutionError("replay frame is invalid")
        elapsed = _finite(frame.elapsed, "replay.frame.elapsed")
        if elapsed < 0 or elapsed > MAX_TRIGGER_FIXED_DT * MAX_TRIGGER_SUBSTEPS:
            raise TriggerExecutionError("replay frame elapsed exceeds the limit")
    return tape


def _observation_payload(observation: TriggerObservation) -> dict[str, Any]:
    _validate_json_value(dict(observation.context), field_name="observation.context")
    return {
        "object_id": observation.object_id,
        "position": observation.position.model_dump(mode="json"),
        "context": copy.deepcopy(dict(observation.context)),
    }


def serialize_trigger_replay(tape: TriggerReplayTape) -> bytes:
    tape = _validated_replay_tape(tape)
    payload = {
        "format_id": tape.format_id,
        "algorithm_version": tape.algorithm_version,
        "document_sha256": tape.document_sha256,
        "fixed_dt": tape.fixed_dt,
        "initial_tick_index": tape.initial_tick_index,
        "initial_simulation_time": tape.initial_simulation_time,
        "initial_accumulator": tape.initial_accumulator,
        "initial_active_pairs": [list(pair) for pair in tape.initial_active_pairs],
        "frames": [
            {
                "elapsed": frame.elapsed,
                "observations": [
                    _observation_payload(item) for item in frame.observations
                ],
            }
            for frame in tape.frames
        ],
    }
    return _canonical_json_bytes(payload)


class TriggerRuntime:
    """Fixed-step deterministic trigger dispatcher with cancel and replay."""

    def __init__(self, document: TriggerDocumentV1) -> None:
        self._document = _validated_document(document)
        self._document_sha256 = trigger_runtime_export_sha256(self._document)
        self._phase: Literal["ready", "running", "paused", "stopped"] = "ready"
        self._tick_index = 0
        self._simulation_time = 0.0
        self._accumulator = 0.0
        self._active_pairs: set[tuple[str, str]] = set()
        self._recording = False
        self._recorded_frames: list[TriggerReplayFrame] = []
        self._recording_initial: TriggerReplayTape | None = None
        self._events = {event.id: event for event in self._document.events}

    @property
    def document(self) -> TriggerDocumentV1:
        return self._document

    @property
    def snapshot(self) -> TriggerRuntimeSnapshot:
        return TriggerRuntimeSnapshot(
            phase=self._phase,
            document_sha256=self._document_sha256,
            fixed_dt=self._document.fixed_dt,
            tick_index=self._tick_index,
            simulation_time=self._simulation_time,
            accumulator=self._accumulator,
            active_pairs=tuple(sorted(self._active_pairs)),
        )

    def start(self) -> TriggerRuntimeSnapshot:
        if self._phase not in {"ready", "paused", "stopped"}:
            raise TriggerExecutionError(f"cannot start from phase {self._phase}")
        self._phase = "running"
        return self.snapshot

    def pause(self) -> TriggerRuntimeSnapshot:
        if self._phase != "running":
            raise TriggerExecutionError("pause requires a running trigger runtime")
        self._phase = "paused"
        return self.snapshot

    def resume(self) -> TriggerRuntimeSnapshot:
        if self._phase != "paused":
            raise TriggerExecutionError("resume requires a paused trigger runtime")
        self._phase = "running"
        return self.snapshot

    def stop(self) -> TriggerRuntimeSnapshot:
        if self._phase not in {"ready", "running", "paused", "stopped"}:
            raise TriggerExecutionError("invalid trigger runtime phase")
        self._phase = "stopped"
        return self.snapshot

    @staticmethod
    def _normalize_observations(
        observations: Iterable[TriggerObservation],
    ) -> tuple[TriggerObservation, ...]:
        try:
            normalized = tuple(observations)
        except TypeError as exc:
            raise TriggerExecutionError("observations must be iterable") from exc
        if len(normalized) > MAX_TRIGGER_ZONES * 4:
            raise TriggerExecutionError("observation count exceeds the trigger limit")
        if any(not isinstance(item, TriggerObservation) for item in normalized):
            raise TriggerExecutionError("observations must use TriggerObservation")
        ids = [item.object_id for item in normalized]
        if any(not isinstance(item, str) or not item for item in ids):
            raise TriggerExecutionError(
                "observation object IDs must be non-empty strings"
            )
        if any(len(item) > MAX_TRIGGER_ID_LENGTH for item in ids):
            raise TriggerExecutionError("observation object IDs exceed the limit")
        if len(ids) != len(set(ids)):
            raise TriggerExecutionError("observation object IDs must be unique")
        try:
            for item in normalized:
                _observation_payload(item)
        except ValueError as exc:
            raise TriggerExecutionError(str(exc)) from exc
        return tuple(sorted(normalized, key=lambda item: item.object_id))

    @staticmethod
    def _inside(zone: TriggerZoneRecord, position: Point3Record) -> bool:
        return all(
            abs(float(getattr(position, axis)) - float(getattr(zone.center, axis)))
            <= float(getattr(zone.size, axis)) / 2.0
            for axis in ("x", "y", "z")
        )

    @staticmethod
    def _condition_matches(
        condition: TriggerConditionRecord, context: Mapping[str, Any]
    ) -> bool:
        if condition.key not in context:
            return False
        current = context[condition.key]
        if condition.operator == "truthy":
            return bool(current)
        if condition.operator == "falsy":
            return not bool(current)
        if condition.operator == "eq":
            return current == condition.value
        if condition.operator == "neq":
            return current != condition.value
        try:
            if condition.operator == "gt":
                return float(current) > float(condition.value)
            if condition.operator == "gte":
                return float(current) >= float(condition.value)
            if condition.operator == "lt":
                return float(current) < float(condition.value)
            return float(current) <= float(condition.value)
        except (TypeError, ValueError, OverflowError):
            return False

    def _zone_matches(
        self, zone: TriggerZoneRecord, observation: TriggerObservation
    ) -> bool:
        if not zone.enabled:
            return False
        return self._inside(zone, observation.position) and all(
            self._condition_matches(condition, observation.context)
            for condition in zone.conditions
        )

    def _events_for_transition(
        self,
        zone: TriggerZoneRecord,
        object_id: str,
        transition: TriggerTransition,
        tick_index: int,
    ) -> TriggerEvent | None:
        event_id = {
            "enter": zone.enter_event_id,
            "stay": zone.stay_event_id,
            "exit": zone.exit_event_id,
        }[transition]
        if event_id is None:
            return None
        definition = self._events[event_id]
        if not definition.enabled:
            return None
        return TriggerEvent(
            event_id=event_id,
            transition=transition,
            zone_id=zone.id,
            object_id=object_id,
            priority=zone.priority,
            tick_index=tick_index,
            payload=copy.deepcopy(definition.payload),
        )

    def advance(
        self,
        elapsed: float,
        observations: Iterable[TriggerObservation],
        cancellation: Any | None = None,
    ) -> TriggerStepResult:
        if self._phase != "running":
            raise TriggerExecutionError("advance requires a running trigger runtime")
        if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)):
            raise TriggerExecutionError("elapsed must be a finite non-negative number")
        try:
            elapsed_value = _finite(elapsed, "elapsed")
        except ValueError as exc:
            raise TriggerExecutionError(str(exc)) from exc
        if (
            elapsed_value < 0
            or elapsed_value > self._document.fixed_dt * self._document.max_substeps
        ):
            raise TriggerExecutionError("elapsed exceeds the fixed-step catch-up limit")
        normalized = self._normalize_observations(observations)
        if cancellation is not None and bool(getattr(cancellation, "cancelled", False)):
            raise TriggerCancellationError("trigger step was cancelled")

        candidate_accumulator = self._accumulator + elapsed_value
        steps = int(math.floor(candidate_accumulator / self._document.fixed_dt + 1e-12))
        if steps > self._document.max_substeps:
            raise TriggerExecutionError("fixed-step catch-up limit would be exceeded")
        candidate_active = set(self._active_pairs)
        candidate_tick = self._tick_index
        candidate_time = self._simulation_time
        emitted: list[TriggerEvent] = []
        if self._recording and len(self._recorded_frames) >= MAX_TRIGGER_REPLAY_FRAMES:
            raise TriggerExecutionError("trigger replay frame limit exceeded")
        zones = tuple(
            sorted(self._document.zones, key=lambda item: (-item.priority, item.id))
        )
        zone_by_id = {zone.id: zone for zone in zones}
        for _ in range(steps):
            if cancellation is not None and bool(
                getattr(cancellation, "cancelled", False)
            ):
                raise TriggerCancellationError("trigger step was cancelled")
            candidate_tick += 1
            candidate_time += self._document.fixed_dt
            matched: set[tuple[str, str]] = set()
            for observation in normalized:
                for zone in zones:
                    pair = (zone.id, observation.object_id)
                    if self._zone_matches(zone, observation):
                        matched.add(pair)
                        transition: TriggerTransition = (
                            "stay" if pair in candidate_active else "enter"
                        )
                    else:
                        continue
                    event = self._events_for_transition(
                        zone, observation.object_id, transition, candidate_tick
                    )
                    if event is not None:
                        emitted.append(event)
            for zone_id, object_id in sorted(candidate_active - matched):
                event = self._events_for_transition(
                    zone_by_id[zone_id], object_id, "exit", candidate_tick
                )
                if event is not None:
                    emitted.append(event)
            candidate_active = matched
        emitted.sort(
            key=lambda event: (
                -event.priority,
                event.zone_id,
                event.object_id,
                event.transition,
                event.tick_index,
            )
        )
        candidate_accumulator -= steps * self._document.fixed_dt
        self._active_pairs = candidate_active
        self._accumulator = candidate_accumulator
        self._tick_index = candidate_tick
        self._simulation_time = candidate_time
        if self._recording:
            self._recorded_frames.append(TriggerReplayFrame(elapsed_value, normalized))
        return TriggerStepResult(
            elapsed=elapsed_value,
            steps=steps,
            tick_index=candidate_tick,
            simulation_time=candidate_time,
            accumulator=candidate_accumulator,
            events=tuple(emitted),
        )

    def start_recording(self) -> None:
        self._recording = True
        self._recorded_frames = []
        snapshot = self.snapshot
        self._recording_initial = TriggerReplayTape(
            format_id=TRIGGERS_FORMAT_ID,
            algorithm_version=TRIGGERS_ALGORITHM_VERSION,
            document_sha256=self._document_sha256,
            fixed_dt=self._document.fixed_dt,
            initial_tick_index=snapshot.tick_index,
            initial_simulation_time=snapshot.simulation_time,
            initial_accumulator=snapshot.accumulator,
            initial_active_pairs=snapshot.active_pairs,
            frames=(),
        )

    def stop_recording(self) -> TriggerReplayTape:
        if not self._recording or self._recording_initial is None:
            raise TriggerExecutionError("trigger replay recording is not active")
        initial = self._recording_initial
        tape = TriggerReplayTape(
            format_id=initial.format_id,
            algorithm_version=initial.algorithm_version,
            document_sha256=initial.document_sha256,
            fixed_dt=initial.fixed_dt,
            initial_tick_index=initial.initial_tick_index,
            initial_simulation_time=initial.initial_simulation_time,
            initial_accumulator=initial.initial_accumulator,
            initial_active_pairs=initial.initial_active_pairs,
            frames=tuple(self._recorded_frames),
        )
        self._recording = False
        self._recorded_frames = []
        self._recording_initial = None
        return tape

    @classmethod
    def replay(
        cls,
        document: TriggerDocumentV1,
        tape: TriggerReplayTape,
    ) -> tuple[TriggerEvent, ...]:
        tape = _validated_replay_tape(tape)
        runtime = cls(document)
        if tape.document_sha256 != runtime._document_sha256:
            raise TriggerExecutionError("replay tape is not bound to this document")
        if tape.fixed_dt != document.fixed_dt:
            raise TriggerExecutionError("replay fixed_dt does not match the document")
        runtime._tick_index = tape.initial_tick_index
        runtime._simulation_time = tape.initial_simulation_time
        runtime._accumulator = tape.initial_accumulator
        runtime._active_pairs = set(tape.initial_active_pairs)
        runtime.start()
        events: list[TriggerEvent] = []
        for frame in tape.frames:
            events.extend(runtime.advance(frame.elapsed, frame.observations).events)
        return tuple(events)
