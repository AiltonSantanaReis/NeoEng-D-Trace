"""Positive, negative and rollback tests for runtime lighting phase 2."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from src.persistence.project_schema import Point3Record
from src.runtime import (
    AmbientLightRecord,
    LightingColorRecord,
    LightingDocumentV1,
    LightingFormatError,
    LightingRuntime,
    LightingRuntimeError,
    LightingSourceBindingRecord,
    LightingSourceRecord,
    LightingValidationError,
    LightSocketRecord,
    MaterialBindingRecord,
    MaterialRecord,
    RuntimeHost,
    serialize_lighting_runtime_export,
    validate_lighting_runtime_export,
)


def _color(r: float, g: float, b: float) -> LightingColorRecord:
    return LightingColorRecord(r=r, g=g, b=b)


def _document() -> LightingDocumentV1:
    return LightingDocumentV1(
        source=LightingSourceBindingRecord(sha256="a" * 64),
        ambient=AmbientLightRecord(color=_color(1.0, 1.0, 1.0), intensity=0.1),
        lights=[
            LightingSourceRecord(
                id="lamp",
                kind="point",
                color=_color(1.0, 0.0, 0.0),
                intensity=1.0,
                position=Point3Record(x=0.0, y=0.0, z=0.0),
                range=10.0,
            ),
            LightingSourceRecord(
                id="sun",
                kind="directional",
                color=_color(0.0, 0.0, 1.0),
                intensity=0.2,
            ),
        ],
        materials=[
            MaterialRecord(
                id="lit-material",
                lighting_mode="lit",
                albedo=_color(1.0, 1.0, 1.0),
                emission=_color(0.0, 0.0, 0.0),
            ),
            MaterialRecord(
                id="unlit-material",
                lighting_mode="unlit",
                albedo=_color(0.2, 0.3, 0.4),
                emission=_color(0.1, 0.0, 0.0),
                emission_strength=0.5,
            ),
        ],
        material_bindings=[
            MaterialBindingRecord(object_id="object-lit", material_id="lit-material"),
            MaterialBindingRecord(
                object_id="object-unlit", material_id="unlit-material"
            ),
        ],
        sockets=[
            LightSocketRecord(
                id="socket-lamp",
                object_id="object-lit",
                source_id="lamp",
                position=Point3Record(x=0.0, y=0.0, z=0.0),
            )
        ],
    )


def test_lighting_contract_is_versioned_canonical_and_hash_bound() -> None:
    document = _document()
    first = serialize_lighting_runtime_export(document)
    second = serialize_lighting_runtime_export(document)

    assert first == second
    assert first.endswith(b"\n")
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    payload = json.loads(first)
    assert payload["format_id"] == "neoeng-d-trace-runtime-lighting"
    assert payload["schema_version"] == 1
    assert payload["source"]["sha256"] == "a" * 64
    validate_lighting_runtime_export(payload)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update(schema_version=2),
        lambda payload: payload["source"].update(sha256="bad"),
        lambda payload: payload["lights"][0].update(intensity=-1.0),
        lambda payload: payload["materials"][0].update(unknown=True),
    ],
)
def test_lighting_contract_rejects_invalid_payloads(mutate) -> None:
    payload = _document().model_dump(mode="json")
    mutate(payload)
    with pytest.raises(LightingValidationError):
        validate_lighting_runtime_export(payload)


def test_lighting_contract_rejects_duplicate_and_unknown_references() -> None:
    payload = _document().model_dump(mode="json")
    duplicate = copy.deepcopy(payload)
    duplicate["lights"].append(copy.deepcopy(duplicate["lights"][0]))
    with pytest.raises(LightingValidationError, match="source IDs"):
        validate_lighting_runtime_export(duplicate)

    unknown = copy.deepcopy(payload)
    unknown["sockets"][0]["source_id"] = "missing"
    with pytest.raises(LightingValidationError, match="unknown source"):
        validate_lighting_runtime_export(unknown)


def test_lighting_preview_is_deterministic_and_reports_contributors() -> None:
    runtime = LightingRuntime()
    runtime.load_manifest(_document().model_dump(mode="json"))

    first = runtime.preview(Point3Record(x=0.0, y=0.0, z=0.0), object_id="object-lit")
    second = runtime.preview(Point3Record(x=0.0, y=0.0, z=0.0), object_id="object-lit")

    assert first == second
    assert first.color == (1.0, 0.1, 0.3)
    assert first.opacity == 1.0
    assert first.material_id == "lit-material"
    assert first.contributing_light_ids == ("lamp", "sun")


def test_unlit_material_ignores_lights_but_keeps_emission() -> None:
    runtime = LightingRuntime()
    runtime.load_manifest(_document().model_dump(mode="json"))

    preview = runtime.preview(
        Point3Record(x=0.0, y=0.0, z=0.0), object_id="object-unlit"
    )

    assert preview.color == (0.25, 0.3, 0.4)
    assert preview.contributing_light_ids == ()


def test_spot_light_has_deterministic_cone_falloff() -> None:
    document = _document()
    document = document.model_copy(
        update={
            "lights": [
                LightingSourceRecord(
                    id="spot",
                    kind="spot",
                    color=_color(1.0, 1.0, 1.0),
                    intensity=1.0,
                    position=Point3Record(x=0.0, y=0.0, z=0.0),
                    direction_degrees=0.0,
                    range=10.0,
                    cone_angle_degrees=60.0,
                )
            ],
            "sockets": [],
        }
    )
    runtime = LightingRuntime()
    runtime.load_manifest(document.model_dump(mode="json"))

    inside = runtime.preview(Point3Record(x=5.0, y=0.0, z=0.0))
    outside = runtime.preview(Point3Record(x=0.0, y=5.0, z=0.0))

    assert inside.contributing_light_ids == ("spot",)
    assert outside.contributing_light_ids == ()


def test_socket_preview_resolves_position_and_disabled_socket_is_safe() -> None:
    runtime = LightingRuntime()
    runtime.load_manifest(_document().model_dump(mode="json"))

    preview = runtime.preview_socket("socket-lamp")
    assert preview.contributing_light_ids == ("lamp", "sun")

    disabled = _document().model_copy(
        update={
            "sockets": [_document().sockets[0].model_copy(update={"enabled": False})]
        }
    )
    runtime.load_manifest(disabled.model_dump(mode="json"))
    assert runtime.preview_socket("socket-lamp").color == (0.0, 0.0, 0.0)


def test_lighting_runtime_preserves_previous_document_on_invalid_replacement() -> None:
    runtime = LightingRuntime()
    runtime.load_manifest(_document().model_dump(mode="json"))
    before = runtime.manifest_copy()
    invalid = _document().model_dump(mode="json")
    invalid["schema_version"] = 2

    with pytest.raises(LightingValidationError):
        runtime.load_manifest(invalid)

    assert runtime.manifest_copy() == before


def test_lighting_file_requires_canonical_bytes_and_preserves_state(tmp_path) -> None:
    destination = tmp_path / "lighting.json"
    destination.write_bytes(serialize_lighting_runtime_export(_document()))
    runtime = LightingRuntime()
    runtime.load_file(destination)
    before = runtime.manifest_copy()

    destination.write_bytes(
        b"\xef\xbb\xbf" + serialize_lighting_runtime_export(_document())
    )
    with pytest.raises(LightingFormatError, match="BOM"):
        runtime.load_file(destination)
    assert runtime.manifest_copy() == before


def test_lighting_runtime_requires_loaded_document_and_valid_position() -> None:
    runtime = LightingRuntime()
    with pytest.raises(LightingRuntimeError, match="required"):
        runtime.preview(Point3Record(x=0.0, y=0.0, z=0.0))
    runtime.load_manifest(_document().model_dump(mode="json"))
    with pytest.raises(LightingRuntimeError, match="Point3Record"):
        runtime.preview((0.0, 0.0, 0.0))


def test_runtime_host_advertises_lighting_as_native_capability() -> None:
    host = RuntimeHost()
    assert "runtime.lighting" in host.supported_capabilities
