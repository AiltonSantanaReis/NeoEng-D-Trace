"""Tests for the deterministic runtime trigger sidecar."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace

import pytest

from src.persistence.project_schema import Point3Record
from src.runtime.scene_runtime import RuntimeCancellationToken, RuntimeHost
from src.runtime.triggers import (
    TRIGGERS_FORMAT_ID,
    TriggerCancellationError,
    TriggerConditionRecord,
    TriggerDocumentV1,
    TriggerEventRecord,
    TriggerExecutionError,
    TriggerFormatError,
    TriggerObservation,
    TriggerReplayFrame,
    TriggerRuntime,
    TriggerSourceBindingRecord,
    TriggerValidationError,
    TriggerZoneRecord,
    build_trigger_runtime_export,
    load_trigger_runtime_export,
    load_trigger_runtime_export_bytes,
    save_trigger_runtime_export,
    serialize_trigger_replay,
    serialize_trigger_runtime_export,
    trigger_runtime_export_sha256,
    validate_trigger_runtime_export,
    verify_trigger_source_binding,
)


def _point(x: float, y: float = 0.0, z: float = 0.0) -> Point3Record:
    return Point3Record(x=x, y=y, z=z)


def _document() -> TriggerDocumentV1:
    return TriggerDocumentV1(
        source=TriggerSourceBindingRecord(sha256="a" * 64),
        fixed_dt=1.0 / 60.0,
        max_substeps=4,
        events=[
            TriggerEventRecord(id="enter", payload={"kind": "entered"}),
            TriggerEventRecord(id="stay", payload={"kind": "stayed"}),
            TriggerEventRecord(id="exit", payload={"kind": "exited"}),
        ],
        zones=[
            TriggerZoneRecord(
                id="high",
                priority=20,
                center=_point(0.0),
                size=_point(10.0, 10.0, 10.0),
                conditions=[
                    TriggerConditionRecord(key="mode", operator="eq", value="active")
                ],
                enter_event_id="enter",
                stay_event_id="stay",
                exit_event_id="exit",
            ),
            TriggerZoneRecord(
                id="low",
                priority=10,
                center=_point(0.0),
                size=_point(20.0, 20.0, 20.0),
                enter_event_id="enter",
            ),
        ],
    )


def _observation(x: float, mode: str = "active") -> TriggerObservation:
    return TriggerObservation("actor", _point(x), {"mode": mode})


def test_trigger_contract_is_canonical_and_hash_bound() -> None:
    document = _document()
    raw = serialize_trigger_runtime_export(document)
    assert raw.endswith(b"\n")
    assert load_trigger_runtime_export_bytes(raw) == document
    assert trigger_runtime_export_sha256(document) == hashlib.sha256(raw).hexdigest()
    source = b"scenario-runtime-bytes"
    bound = document.model_copy(
        update={
            "source": TriggerSourceBindingRecord(
                sha256=hashlib.sha256(source).hexdigest()
            )
        }
    )
    verify_trigger_source_binding(bound, source)
    with pytest.raises(TriggerValidationError):
        verify_trigger_source_binding(document, source)


def test_trigger_loader_rejects_bom_duplicates_nan_and_noncanonical_bytes() -> None:
    document = _document()
    raw = serialize_trigger_runtime_export(document)
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export_bytes(b"\xef\xbb\xbf" + raw)
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export_bytes(
            raw.replace(b'"zones":', b'"zones":', 1) + b" "
        )
    duplicate = b'{"format_id":"x","format_id":"y"}'
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export_bytes(duplicate)
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export_bytes(b'{"fixed_dt":NaN}')


def test_trigger_contract_rejects_invalid_limits_and_references() -> None:
    with pytest.raises(ValueError):
        TriggerZoneRecord(
            id="bad",
            center=_point(0.0),
            size=_point(0.0, 1.0, 1.0),
        )
    with pytest.raises(ValueError):
        TriggerConditionRecord(key="score", operator="gt", value="not-number")
    payload = build_trigger_runtime_export(_document())
    payload["zones"][0]["enter_event_id"] = "missing"
    with pytest.raises(TriggerValidationError):
        build_trigger_runtime_export(payload)


def test_trigger_dispatch_is_priority_ordered_and_emits_transitions() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    first = runtime.advance(1.0 / 60.0, [_observation(0.0)])
    assert [(event.zone_id, event.transition) for event in first.events] == [
        ("high", "enter"),
        ("low", "enter"),
    ]
    second = runtime.advance(1.0 / 60.0, [_observation(0.0)])
    assert [(event.zone_id, event.transition) for event in second.events] == [
        ("high", "stay")
    ]
    third = runtime.advance(1.0 / 60.0, [_observation(20.0)])
    assert [(event.zone_id, event.transition) for event in third.events] == [
        ("high", "exit")
    ]
    assert runtime.snapshot.active_pairs == ()


def test_trigger_conditions_and_disabled_events_are_explicit() -> None:
    document = _document().model_copy(
        update={
            "events": [
                TriggerEventRecord(id="enter", enabled=False),
                TriggerEventRecord(id="stay"),
                TriggerEventRecord(id="exit"),
            ]
        }
    )
    runtime = TriggerRuntime(document)
    runtime.start()
    inactive = runtime.advance(1.0 / 60.0, [_observation(0.0, "inactive")])
    assert inactive.events == ()
    active = runtime.advance(1.0 / 60.0, [_observation(0.0, "active")])
    assert active.events == ()


def test_trigger_cancel_preserves_state_without_partial_events() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    runtime.advance(1.0 / 60.0, [_observation(0.0)])
    before = runtime.snapshot
    token = RuntimeCancellationToken()
    token.cancel()
    with pytest.raises(TriggerCancellationError):
        runtime.advance(1.0 / 60.0, [_observation(20.0)], token)
    assert runtime.snapshot == before


def test_trigger_fixed_step_limits_reject_without_mutation() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    before = runtime.snapshot
    with pytest.raises(TriggerExecutionError):
        runtime.advance(5.0 / 60.0, [_observation(0.0)])
    assert runtime.snapshot == before


def test_trigger_replay_is_deterministic_and_serializable() -> None:
    document = _document()
    runtime = TriggerRuntime(document)
    runtime.start()
    runtime.start_recording()
    first = runtime.advance(1.0 / 60.0, [_observation(0.0)])
    second = runtime.advance(1.0 / 60.0, [_observation(20.0)])
    tape = runtime.stop_recording()
    replayed = TriggerRuntime.replay(document, tape)
    assert replayed == first.events + second.events
    replay_bytes = serialize_trigger_replay(tape)
    assert replay_bytes.endswith(b"\n")
    assert json.loads(replay_bytes)["format_id"] == TRIGGERS_FORMAT_ID
    with pytest.raises(TriggerExecutionError):
        TriggerRuntime.replay(
            document.model_copy(
                update={
                    "source": TriggerSourceBindingRecord(sha256="b" * 64),
                }
            ),
            tape,
        )


def test_trigger_sidecar_save_is_atomic_and_runtime_host_advertises_capability(
    tmp_path,
) -> None:
    destination = tmp_path / "triggers.json"
    save_trigger_runtime_export(_document(), destination)
    assert load_trigger_runtime_export_bytes(destination.read_bytes()) == _document()
    assert "runtime.triggers" in RuntimeHost().supported_capabilities


def test_trigger_emits_exit_when_an_object_is_no_longer_observed() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    runtime.advance(1.0 / 60.0, [_observation(0.0)])
    result = runtime.advance(1.0 / 60.0, [])
    assert [(event.zone_id, event.transition) for event in result.events] == [
        ("high", "exit")
    ]
    assert runtime.snapshot.active_pairs == ()


def test_trigger_pause_and_resume_preserve_lifecycle_contract() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    paused = runtime.pause()
    with pytest.raises(TriggerExecutionError):
        runtime.advance(1.0 / 60.0, [_observation(0.0)])
    assert runtime.snapshot == paused
    runtime.resume()
    result = runtime.advance(1.0 / 60.0, [_observation(0.0)])
    assert result.steps == 1


def test_trigger_replay_contract_is_validated_before_replay() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    runtime.start_recording()
    runtime.advance(1.0 / 60.0, [_observation(0.0)])
    tape = runtime.stop_recording()
    with pytest.raises(TriggerExecutionError):
        TriggerRuntime.replay(
            _document(), replace(tape, format_id="unsupported-format")
        )
    with pytest.raises(TriggerExecutionError):
        serialize_trigger_replay(replace(tape, algorithm_version=99))


def test_trigger_replay_limit_is_checked_before_state_mutation(monkeypatch) -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    runtime.start_recording()
    before = runtime.snapshot
    monkeypatch.setattr("src.runtime.triggers.MAX_TRIGGER_REPLAY_FRAMES", 0)
    with pytest.raises(TriggerExecutionError):
        runtime.advance(1.0 / 60.0, [_observation(0.0)])
    assert runtime.snapshot == before


@pytest.mark.parametrize(
    ("operator", "value", "context", "expected"),
    [
        ("eq", 3, {"score": 3}, True),
        ("neq", 3, {"score": 4}, True),
        ("gt", 3, {"score": 4}, True),
        ("gte", 3, {"score": 3}, True),
        ("lt", 3, {"score": 2}, True),
        ("lte", 3, {"score": 3}, True),
        ("truthy", None, {"score": "yes"}, True),
        ("falsy", None, {"score": 0}, True),
    ],
)
def test_trigger_condition_operators_are_deterministic(
    operator, value, context, expected
) -> None:
    condition = TriggerConditionRecord(key="score", operator=operator, value=value)
    assert TriggerRuntime._condition_matches(condition, context) is expected
    assert TriggerRuntime._condition_matches(condition, {}) is False


def test_trigger_condition_numeric_failure_and_payload_limits_are_rejected() -> None:
    numeric = TriggerConditionRecord(key="score", operator="gt", value=3)
    assert TriggerRuntime._condition_matches(numeric, {"score": "not-number"}) is False
    TriggerEventRecord(
        id="valid",
        payload={
            "flag": True,
            "count": 1,
            "ratio": 0.5,
            "items": [None, {"ok": "yes"}],
        },
    )
    with pytest.raises(ValueError):
        TriggerConditionRecord(value=float("nan"), key="value", operator="eq")
    nested: object = None
    for _ in range(10):
        nested = {"nested": nested}
    with pytest.raises(ValueError):
        TriggerConditionRecord(value=nested, key="value", operator="eq")
    with pytest.raises(ValueError):
        TriggerConditionRecord(value=object(), key="value", operator="eq")
    with pytest.raises(ValueError):
        TriggerEventRecord(
            id="too-many", payload={str(index): index for index in range(33)}
        )
    with pytest.raises(ValueError):
        TriggerConditionRecord(key="value", operator="truthy", value=True)


def test_trigger_contract_rejects_duplicate_ids_and_strict_limits() -> None:
    document = _document()
    zone = document.zones[0]
    event = document.events[0]
    with pytest.raises(ValueError):
        TriggerDocumentV1(
            source=document.source,
            zones=[zone, zone],
            events=document.events,
        )
    with pytest.raises(ValueError):
        TriggerDocumentV1(
            source=document.source,
            zones=document.zones,
            events=[event, event],
        )
    with pytest.raises(ValueError):
        TriggerZoneRecord(
            id="priority-bool",
            priority=True,
            center=_point(0.0),
            size=_point(1.0, 1.0, 1.0),
        )
    with pytest.raises(ValueError):
        TriggerZoneRecord(
            id="priority-float",
            priority=1.5,  # type: ignore[arg-type]
            center=_point(0.0),
            size=_point(1.0, 1.0, 1.0),
        )
    with pytest.raises(ValueError):
        TriggerZoneRecord(
            id="priority-large",
            priority=1_000_001,
            center=_point(0.0),
            size=_point(1.0, 1.0, 1.0),
        )
    with pytest.raises(ValueError):
        TriggerDocumentV1(
            source=document.source,
            fixed_dt=0.0,
            zones=document.zones,
            events=document.events,
        )
    with pytest.raises(ValueError):
        TriggerDocumentV1(
            source=document.source,
            max_substeps=True,
            zones=document.zones,
            events=document.events,
        )
    with pytest.raises(ValueError):
        TriggerDocumentV1(
            source=document.source,
            max_substeps=9,
            zones=document.zones,
            events=document.events,
        )


def test_trigger_io_rejects_invalid_types_and_preserves_paths(tmp_path) -> None:
    document = _document()
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export_bytes("not-bytes")  # type: ignore[arg-type]
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export_bytes(b"\xff")
    with pytest.raises(TriggerFormatError):
        load_trigger_runtime_export(tmp_path / "missing.json")
    with pytest.raises(TriggerValidationError):
        save_trigger_runtime_export(document, tmp_path / "missing" / "out.json")
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(TriggerValidationError):
        save_trigger_runtime_export(document, directory)
    with pytest.raises(TriggerValidationError):
        verify_trigger_source_binding(document, "not-bytes")  # type: ignore[arg-type]
    with pytest.raises(TriggerValidationError):
        validate_trigger_runtime_export([])  # type: ignore[arg-type]


def test_trigger_lifecycle_rejects_invalid_transitions() -> None:
    runtime = TriggerRuntime(_document())
    with pytest.raises(TriggerExecutionError):
        runtime.pause()
    with pytest.raises(TriggerExecutionError):
        runtime.resume()
    with pytest.raises(TriggerExecutionError):
        runtime.advance(0.0, [])
    runtime.start()
    with pytest.raises(TriggerExecutionError):
        runtime.start()
    runtime.pause()
    with pytest.raises(TriggerExecutionError):
        runtime.pause()
    runtime.resume()
    runtime.stop()
    with pytest.raises(TriggerExecutionError):
        runtime.pause()
    runtime.start()
    runtime.stop()
    with pytest.raises(TriggerExecutionError):
        runtime.stop_recording()


def test_trigger_observation_and_elapsed_limits_are_controlled() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    invalid_elapsed = [True, "1", math.nan, -0.1, 5.0 / 60.0]
    for elapsed in invalid_elapsed:
        with pytest.raises(TriggerExecutionError):
            runtime.advance(elapsed, [])  # type: ignore[arg-type]
    with pytest.raises(TriggerExecutionError):
        runtime.advance(0.0, None)  # type: ignore[arg-type]
    with pytest.raises(TriggerExecutionError):
        runtime.advance(0.0, [object()])  # type: ignore[list-item]
    with pytest.raises(TriggerExecutionError):
        runtime.advance(0.0, [_observation(0.0), _observation(0.0)])
    with pytest.raises(TriggerExecutionError):
        runtime.advance(0.0, [TriggerObservation("x" * 129, _point(0.0))])
    with pytest.raises(TriggerExecutionError):
        runtime.advance(
            0.0,
            [TriggerObservation("bad-context", _point(0.0), {"value": object()})],
        )
    too_many = (
        TriggerObservation(f"object-{index}", _point(100.0)) for index in range(4_097)
    )
    with pytest.raises(TriggerExecutionError):
        runtime.advance(0.0, too_many)


def test_trigger_cancellation_during_fixed_steps_is_atomic() -> None:
    class ToggleCancellation:
        calls = 0

        @property
        def cancelled(self) -> bool:
            self.calls += 1
            return self.calls > 2

    runtime = TriggerRuntime(_document())
    runtime.start()
    before = runtime.snapshot
    with pytest.raises(TriggerCancellationError):
        runtime.advance(2.0 / 60.0, [_observation(0.0)], ToggleCancellation())
    assert runtime.snapshot == before


def test_trigger_replay_rejects_invalid_tape_fields() -> None:
    runtime = TriggerRuntime(_document())
    runtime.start()
    runtime.start_recording()
    runtime.advance(1.0 / 60.0, [_observation(0.0)])
    tape = runtime.stop_recording()
    with pytest.raises(TriggerExecutionError):
        serialize_trigger_replay(replace(tape, document_sha256="invalid"))
    with pytest.raises(TriggerExecutionError):
        serialize_trigger_replay(replace(tape, initial_tick_index=-1))
    with pytest.raises(TriggerExecutionError):
        serialize_trigger_replay(
            replace(tape, frames=(object(),))  # type: ignore[arg-type]
        )
    with pytest.raises(TriggerExecutionError):
        TriggerRuntime.replay(_document(), replace(tape, fixed_dt=0.5))
    with pytest.raises(TriggerExecutionError):
        TriggerRuntime.replay(
            _document(),
            replace(tape, frames=(TriggerReplayFrame(2.0, ()),)),
        )
