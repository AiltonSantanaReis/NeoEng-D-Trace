from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.audit_runtime_particles_phase4 import _document as particle_document
from scripts.audit_runtime_post_processing_phase5 import _document as post_document
from scripts.audit_runtime_shaders_phase3 import _document as shader_document
from scripts.audit_runtime_streaming_phase7 import _asset
from scripts.audit_runtime_streaming_phase7 import _document as streaming_document
from scripts.audit_runtime_triggers_phase6 import _document as trigger_document
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.exporters.scenario_exporter import serialize_scenario_runtime_export
from src.runtime.engine_adapters import (
    CAPABILITIES,
    AdapterBundleFormatError,
    AdapterBundleValidationError,
    build_adapter_bundle,
    load_adapter_bundle,
    serialize_adapter_bundle,
    write_adapter_bundle,
)
from src.runtime.lighting import (
    LightingSourceBindingRecord,
    serialize_lighting_runtime_export,
)
from src.runtime.particles import (
    ParticleSourceBindingRecord,
    serialize_particle_runtime_export,
)
from src.runtime.post_processing import (
    PostProcessingSourceBindingRecord,
    serialize_post_processing_runtime_export,
)
from src.runtime.shaders import (
    ShaderSourceBindingRecord,
    serialize_shader_runtime_export,
)
from src.runtime.streaming import (
    StreamingSourceBindingRecord,
    serialize_streaming_runtime_export,
)
from src.runtime.triggers import (
    TriggerSourceBindingRecord,
    serialize_trigger_runtime_export,
)
from tests.test_stage2_runtime_lighting import _document as lighting_document
from tests.test_stage4b4_scenario_export import _document as scenario_document


def _matrix() -> dict[str, dict[str, object]]:
    support = [
        {
            "id": capability,
            "compatibility": (
                "native"
                if capability
                in {
                    "runtime.scene_loading",
                    "runtime.lifecycle",
                    "runtime.fixed_update",
                }
                else "degraded"
            ),
            "mode": (
                "scene-tree-fixed-tick"
                if capability
                in {
                    "runtime.scene_loading",
                    "runtime.lifecycle",
                    "runtime.fixed_update",
                }
                else "validated-sidecar-metadata"
            ),
            "reason": "The adapter executes the declared contract in this scope.",
        }
        for capability in CAPABILITIES
    ]
    return {
        engine: {
            "adapter_id": f"neoeng.dtrace.{engine}.runtime",
            "adapter_version": 1,
            "support": copy.deepcopy(support),
        }
        for engine in ("godot", "unity")
    }


def _fixture(tmp_path: Path) -> tuple[dict[str, object], bytes, dict[str, bytes]]:
    scenario = serialize_scenario_runtime_export(scenario_document())
    scenario_hash = hashlib.sha256(scenario).hexdigest()
    lighting = lighting_document().model_copy(
        update={"source": LightingSourceBindingRecord(sha256=scenario_hash)}
    )
    lighting_bytes = serialize_lighting_runtime_export(lighting)
    shader = shader_document().model_copy(
        update={
            "source": ShaderSourceBindingRecord(
                sha256=hashlib.sha256(lighting_bytes).hexdigest()
            )
        }
    )
    particle = particle_document().model_copy(
        update={"source": ParticleSourceBindingRecord(sha256=scenario_hash)}
    )
    post = post_document().model_copy(
        update={"source": PostProcessingSourceBindingRecord(sha256=scenario_hash)}
    )
    trigger = trigger_document().model_copy(
        update={"source": TriggerSourceBindingRecord(sha256=scenario_hash)}
    )
    streaming = streaming_document(
        _asset("smoke", "textures/smoke.bin", b"smoke")
    ).model_copy(update={"source": StreamingSourceBindingRecord(sha256=scenario_hash)})
    sidecars = {
        "runtime.lighting": lighting_bytes,
        "runtime.shaders": serialize_shader_runtime_export(shader),
        "runtime.particles": serialize_particle_runtime_export(particle),
        "runtime.post_processing": serialize_post_processing_runtime_export(post),
        "runtime.triggers": serialize_trigger_runtime_export(trigger),
        "runtime.streaming": serialize_streaming_runtime_export(streaming),
    }
    payload = build_adapter_bundle(
        source_path="runtime/scenario.ndtscenario.runtime.json",
        source_bytes=scenario,
        sidecars={
            capability: (f"runtime/{capability.split('.', 1)[1]}.json", raw)
            for capability, raw in sidecars.items()
        },
        capabilities=_matrix(),
    )
    return payload, scenario, sidecars


def _write_fixture(
    tmp_path: Path,
    payload: dict[str, object],
    scenario: bytes,
    sidecars: dict[str, bytes],
) -> Path:
    (tmp_path / "runtime").mkdir(exist_ok=True)
    (tmp_path / "runtime" / "scenario.ndtscenario.runtime.json").write_bytes(scenario)
    for capability, raw in sidecars.items():
        (tmp_path / "runtime" / f"{capability.split('.', 1)[1]}.json").write_bytes(raw)
    bundle = tmp_path / "runtime" / "adapters.json"
    bundle.write_bytes(serialize_adapter_bundle(payload))
    return bundle


def test_bundle_round_trip_verifies_all_sidecars_for_both_engines(
    tmp_path: Path,
) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)

    for engine in ("godot", "unity"):
        loaded, report = load_adapter_bundle(tmp_path, bundle, engine=engine)
        assert loaded == payload
        assert report.engine == engine
        assert report.scenario_sha256 == hashlib.sha256(scenario).hexdigest()
        assert report.sidecar_capabilities == tuple(sorted(sidecars))
        assert all(
            report.decisions[capability]["compatibility"] in {"native", "degraded"}
            for capability in CAPABILITIES
        )


def test_bundle_rejects_sidecar_byte_drift(tmp_path: Path) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    target = tmp_path / "runtime" / "particles.json"
    drifted = bytearray(target.read_bytes())
    drifted[-2] = ord("X") if drifted[-2] != ord("X") else ord("Y")
    target.write_bytes(bytes(drifted))

    with pytest.raises(AdapterBundleValidationError, match="hash mismatch"):
        load_adapter_bundle(tmp_path, bundle, engine="unity")


def test_bundle_rejects_path_traversal_and_noncanonical_bytes(tmp_path: Path) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    traversal = copy.deepcopy(payload)
    traversal["source"]["path"] = "../scenario.json"
    with pytest.raises(AdapterBundleValidationError, match="escapes"):
        serialize_adapter_bundle(traversal)

    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    raw = bundle.read_bytes()
    bundle.write_bytes(b"\xef\xbb\xbf" + raw)
    with pytest.raises(AdapterBundleFormatError, match="BOM"):
        load_adapter_bundle(tmp_path, bundle)


def test_bundle_rejects_missing_capability_and_dependency_binding(
    tmp_path: Path,
) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    missing = copy.deepcopy(payload)
    missing["capabilities"]["godot"]["support"] = missing["capabilities"]["godot"][
        "support"
    ][:-1]
    with pytest.raises(AdapterBundleValidationError, match="matrix"):
        serialize_adapter_bundle(missing)

    broken_sidecars = dict(sidecars)
    broken = json.loads(broken_sidecars["runtime.shaders"].decode("utf-8"))
    broken["source"]["sha256"] = "0" * 64
    broken_sidecars["runtime.shaders"] = (
        json.dumps(broken, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with pytest.raises(AdapterBundleValidationError, match="not bound"):
        build_adapter_bundle(
            source_path="runtime/scenario.ndtscenario.runtime.json",
            source_bytes=scenario,
            sidecars={
                capability: (f"runtime/{capability.split('.', 1)[1]}.json", raw)
                for capability, raw in broken_sidecars.items()
            },
            capabilities=_matrix(),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.pop("api_version"), "keys"),
        (lambda payload: payload.__setitem__("format_id", "other"), "format"),
        (lambda payload: payload.__setitem__("schema_version", 99), "schema"),
        (lambda payload: payload.__setitem__("api_version", 99), "API"),
        (lambda payload: payload.__setitem__("generator", {}), "generator"),
        (
            lambda payload: payload["generator"].__setitem__("id", "other"),
            "identity",
        ),
        (
            lambda payload: payload["generator"].__setitem__("version", 1),
            "identity",
        ),
        (lambda payload: payload["source"].pop("bytes"), "source"),
        (
            lambda payload: payload["source"].__setitem__("format_id", "other"),
            "source contract",
        ),
        (
            lambda payload: payload["source"].__setitem__("sha256", "0"),
            "SHA-256",
        ),
        (lambda payload: payload.__setitem__("sidecars", []), "six sidecars"),
        (lambda payload: payload["sidecars"][0].pop("required"), "invalid"),
        (
            lambda payload: payload["sidecars"][0].__setitem__("format_id", "other"),
            "contract",
        ),
        (
            lambda payload: payload["sidecars"][0].__setitem__("required", False),
            "required",
        ),
        (
            lambda payload: payload["sidecars"][0].__setitem__("bytes", True),
            "bytes",
        ),
        (
            lambda payload: payload["sidecars"][0].__setitem__("bytes", 0),
            "exceeds",
        ),
        (
            lambda payload: payload["sidecars"][0].__setitem__(
                "path", payload["source"]["path"]
            ),
            "duplicated",
        ),
        (
            lambda payload: payload["capabilities"]["godot"].__setitem__(
                "adapter_version", True
            ),
            "version",
        ),
        (
            lambda payload: payload["capabilities"]["godot"].__setitem__("support", []),
            "matrix",
        ),
        (
            lambda payload: payload["capabilities"].pop("unity"),
            "Godot and Unity",
        ),
        (
            lambda payload: payload["capabilities"]["godot"]["support"][0].__setitem__(
                "compatibility", "unknown"
            ),
            "compatibility",
        ),
        (
            lambda payload: payload["capabilities"]["godot"]["support"][0].__setitem__(
                "mode", ""
            ),
            "mode",
        ),
        (
            lambda payload: payload["capabilities"]["godot"]["support"][0].__setitem__(
                "reason", ""
            ),
            "reason",
        ),
    ],
)
def test_bundle_rejects_invalid_contract_variants(
    mutation, message: str, tmp_path: Path
) -> None:
    payload, _, _ = _fixture(tmp_path)
    candidate = copy.deepcopy(payload)
    mutation(candidate)
    with pytest.raises(AdapterBundleValidationError, match=message):
        serialize_adapter_bundle(candidate)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"duplicate": 1, "duplicate": 2}',
        b'{"value": NaN}',
        b"[1, 2, 3]",
        b"\xff",
    ],
)
def test_bundle_rejects_invalid_json_forms(tmp_path: Path, raw: bytes) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    bundle.write_bytes(raw)
    with pytest.raises(
        AdapterBundleFormatError, match="invalid adapter bundle JSON|root"
    ):
        load_adapter_bundle(tmp_path, bundle)


def test_bundle_rejects_oversized_and_escaping_bundle_paths(tmp_path: Path) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    bundle.write_bytes(b" " * (MAX_PROJECT_FILE_BYTES + 1))
    with pytest.raises(AdapterBundleFormatError, match="file limit"):
        load_adapter_bundle(tmp_path, bundle)

    with pytest.raises(AdapterBundleFormatError, match="escapes"):
        load_adapter_bundle(tmp_path, tmp_path.parent / "outside-adapters.json")


def test_bundle_rejects_missing_file_size_and_source_hash(tmp_path: Path) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    (tmp_path / "runtime" / "particles.json").unlink()
    with pytest.raises(AdapterBundleValidationError, match="missing"):
        load_adapter_bundle(tmp_path, bundle)

    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    changed = copy.deepcopy(payload)
    changed["sidecars"][0]["bytes"] += 1
    bundle.write_bytes(serialize_adapter_bundle(changed))
    with pytest.raises(AdapterBundleValidationError, match="exact bytes"):
        load_adapter_bundle(tmp_path, bundle)

    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    source_file = tmp_path / "runtime" / "scenario.ndtscenario.runtime.json"
    source_file.write_bytes(source_file.read_bytes() + b" ")
    changed = copy.deepcopy(payload)
    changed["source"]["bytes"] += 1
    bundle.write_bytes(serialize_adapter_bundle(changed))
    with pytest.raises(AdapterBundleValidationError, match="source hash"):
        load_adapter_bundle(tmp_path, bundle)


def test_bundle_rejects_loaded_sidecar_and_dependency_mismatch(tmp_path: Path) -> None:
    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    invalid = b"{}\n"
    target = tmp_path / "runtime" / "particles.json"
    target.write_bytes(invalid)
    changed = copy.deepcopy(payload)
    record = next(
        item
        for item in changed["sidecars"]
        if item["capability"] == "runtime.particles"
    )
    record["sha256"] = hashlib.sha256(invalid).hexdigest()
    record["bytes"] = len(invalid)
    bundle.write_bytes(serialize_adapter_bundle(changed))
    with pytest.raises(AdapterBundleValidationError, match="cannot be loaded"):
        load_adapter_bundle(tmp_path, bundle)

    payload, scenario, sidecars = _fixture(tmp_path)
    bundle = _write_fixture(tmp_path, payload, scenario, sidecars)
    lighting_file = tmp_path / "runtime" / "lighting.json"
    lighting = json.loads(lighting_file.read_text(encoding="utf-8"))
    lighting["source"]["sha256"] = "0" * 64
    drifted = (
        json.dumps(lighting, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    lighting_file.write_bytes(drifted)
    changed = copy.deepcopy(payload)
    record = next(
        item for item in changed["sidecars"] if item["capability"] == "runtime.lighting"
    )
    record["sha256"] = hashlib.sha256(drifted).hexdigest()
    record["bytes"] = len(drifted)
    bundle.write_bytes(serialize_adapter_bundle(changed))
    with pytest.raises(AdapterBundleValidationError, match="dependency binding"):
        load_adapter_bundle(tmp_path, bundle)


def test_write_adapter_bundle_is_atomic_and_rejects_invalid_destinations(
    tmp_path: Path,
) -> None:
    payload, _, _ = _fixture(tmp_path)
    (tmp_path / "runtime").mkdir()
    bundle = tmp_path / "runtime" / "written.json"
    write_adapter_bundle(bundle, payload)
    assert bundle.read_bytes() == serialize_adapter_bundle(payload)

    with pytest.raises(AdapterBundleValidationError, match="writable"):
        write_adapter_bundle(tmp_path / "missing" / "bundle.json", payload)
    with pytest.raises(AdapterBundleValidationError, match="writable"):
        write_adapter_bundle(tmp_path / "runtime", payload)
