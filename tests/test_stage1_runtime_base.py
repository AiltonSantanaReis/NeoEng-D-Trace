"""Real contract tests for the Phase 1 deterministic runtime base."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from src.exporters.scenario_exporter import build_scenario_runtime_export
from src.persistence.project_schema import PointRecord
from src.persistence.scenario_schema import (
    ProjectReferenceRecord,
    ScenarioCameraRecord,
    ScenarioDocumentV1,
    ScenarioLayerRecord,
    ScenarioParallaxRecord,
    default_scenario_metadata,
)
from src.runtime import (
    CapabilityRequest,
    Compatibility,
    RuntimeCancellationToken,
    RuntimeCancelledError,
    RuntimeCapabilityError,
    RuntimeClockError,
    RuntimeHost,
    RuntimeLifecycleError,
    RuntimeManifestFormatError,
    RuntimeManifestValidationError,
    RuntimePhase,
)


def _payload() -> dict[str, object]:
    document = ScenarioDocumentV1(
        metadata=default_scenario_metadata("Phase 1 Fixture"),
        project=ProjectReferenceRecord(sha256="a" * 64),
        camera=ScenarioCameraRecord(position=PointRecord(x=2, y=-3), zoom=1.25),
        layers=[
            ScenarioLayerRecord(
                id="layer_main",
                name="Main",
                visible=True,
                object_ids=["object_a"],
                parallax=ScenarioParallaxRecord(
                    depth=0.5,
                    translation_strength=0.8,
                    zoom_strength=0.9,
                ),
            )
        ],
    )
    return build_scenario_runtime_export(document)


def _canonical(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def test_runtime_load_is_versioned_hash_bound_and_defensive() -> None:
    payload = _payload()
    host = RuntimeHost(fixed_dt=0.1, max_substeps=4)

    snapshot = host.load_manifest(payload)

    assert snapshot.phase is RuntimePhase.READY
    assert snapshot.manifest_sha256 == hashlib.sha256(_canonical(payload)).hexdigest()
    payload["camera"] = None
    active = host.manifest_copy()
    assert active is not None
    assert active["camera"] is not None


def test_runtime_load_file_requires_exact_canonical_bytes(tmp_path) -> None:
    destination = tmp_path / "scene.ndtscenario.runtime.json"
    payload = _payload()
    destination.write_bytes(_canonical(payload))
    host = RuntimeHost()

    snapshot = host.load_file(destination)
    assert (
        snapshot.manifest_sha256 == hashlib.sha256(destination.read_bytes()).hexdigest()
    )

    destination.write_bytes(b"\xef\xbb\xbf" + _canonical(payload))
    with pytest.raises(RuntimeManifestFormatError, match="BOM"):
        host.load_file(destination)


def test_runtime_invalid_replacement_preserves_previous_activation() -> None:
    host = RuntimeHost()
    host.load_manifest(_payload())
    before = host.snapshot
    invalid = copy.deepcopy(_payload())
    invalid["schema_version"] = 2

    with pytest.raises(RuntimeManifestValidationError):
        host.load_manifest(invalid)

    assert host.snapshot == before
    assert host.manifest_copy() == _payload()


def test_runtime_capability_negotiation_requires_explicit_safe_fallback() -> None:
    host = RuntimeHost()
    report = host.negotiate(
        [
            CapabilityRequest("runtime.fixed_update"),
            CapabilityRequest(
                "runtime.lighting",
                required=False,
                fallback_mode="disabled",
                fallback_reason="lighting is not available in the base host",
            ),
            CapabilityRequest("runtime.particles", required=False),
        ]
    )

    assert [item.compatibility for item in report.decisions] == [
        Compatibility.NATIVE,
        Compatibility.NATIVE,
        Compatibility.INCOMPATIBLE,
    ]
    assert report.accepted is False

    with pytest.raises(RuntimeCapabilityError) as error:
        host.load_manifest(
            _payload(), requirements=[CapabilityRequest("runtime.particles")]
        )
    assert error.value.report.incompatible[0].required_capability == "runtime.particles"
    assert host.snapshot.phase is RuntimePhase.EMPTY


def test_runtime_lifecycle_and_fixed_step_clock_are_deterministic() -> None:
    first = RuntimeHost(fixed_dt=0.1, max_substeps=4)
    second = RuntimeHost(fixed_dt=0.1, max_substeps=4)
    first.load_manifest(_payload())
    second.load_manifest(_payload())
    first.start()
    second.start()

    first.tick(0.2)
    first.tick(0.2)
    second.tick(0.4)

    assert first.snapshot.tick_index == second.snapshot.tick_index == 4
    assert first.snapshot.simulation_time == second.snapshot.simulation_time == 0.4
    assert first.snapshot.accumulator == second.snapshot.accumulator == 0.0
    first.pause()
    with pytest.raises(RuntimeLifecycleError):
        first.tick(0.1)
    first.resume()
    first.stop()
    assert first.snapshot.phase is RuntimePhase.STOPPED


@pytest.mark.parametrize(
    "elapsed",
    [-0.1, float("nan"), float("inf"), 0.5, True],
)
def test_runtime_clock_rejects_unsafe_elapsed_without_mutation(elapsed) -> None:
    host = RuntimeHost(fixed_dt=0.1, max_substeps=4)
    host.load_manifest(_payload())
    host.start()
    before = host.snapshot

    with pytest.raises(RuntimeClockError):
        host.tick(elapsed)

    assert host.snapshot == before


def test_runtime_cancellation_leaves_tick_state_untouched() -> None:
    host = RuntimeHost(fixed_dt=0.1, max_substeps=4)
    host.load_manifest(_payload())
    host.start()
    before = host.snapshot
    token = RuntimeCancellationToken()
    token.cancel()

    with pytest.raises(RuntimeCancelledError):
        host.tick(0.2, token)

    assert host.snapshot == before
