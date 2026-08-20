"""Hardening tests for source provenance and strict JSON loading."""

from __future__ import annotations

import hashlib

import pytest

from src.runtime import (
    AmbientLightRecord,
    LightingColorRecord,
    LightingDocumentV1,
    LightingFormatError,
    LightingRuntime,
    LightingSourceBindingRecord,
    LightingValidationError,
    verify_lighting_source_binding,
)


def _document() -> LightingDocumentV1:
    return LightingDocumentV1(
        source=LightingSourceBindingRecord(
            sha256=hashlib.sha256(b"expected-source").hexdigest()
        ),
        ambient=AmbientLightRecord(
            color=LightingColorRecord(r=0.1, g=0.1, b=0.1), intensity=0.5
        ),
        lights=[],
        materials=[],
        material_bindings=[],
        sockets=[],
    )


def test_source_binding_requires_exact_scenario_runtime_bytes() -> None:
    document = _document()
    verify_lighting_source_binding(document, b"expected-source")
    with pytest.raises(LightingValidationError, match="source hash"):
        verify_lighting_source_binding(document, b"different-source")


def test_load_manifest_verifies_source_bytes_before_activation() -> None:
    runtime = LightingRuntime()
    document = _document()
    runtime.load_manifest(
        document.model_dump(mode="json"), source_bytes=b"expected-source"
    )
    before = runtime.manifest_copy()

    with pytest.raises(LightingValidationError, match="source hash"):
        runtime.load_manifest(document.model_dump(mode="json"), source_bytes=b"wrong")
    assert runtime.manifest_copy() == before


def test_loader_rejects_duplicate_keys(tmp_path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_bytes(
        b'{"format_id":"neoeng-d-trace-runtime-lighting",'
        b'"format_id":"neoeng-d-trace-runtime-lighting"}'
    )

    with pytest.raises(LightingFormatError, match="duplicate"):
        LightingRuntime().load_file(path)


def test_loader_rejects_non_finite_json(tmp_path) -> None:
    path = tmp_path / "non-finite.json"
    path.write_bytes(b'{"value":NaN}')

    with pytest.raises(LightingFormatError, match="non-finite"):
        LightingRuntime().load_file(path)


def test_point_position_type_is_strictly_runtime_owned() -> None:
    runtime = LightingRuntime()
    runtime.load_manifest(
        _document().model_dump(mode="json"), source_bytes=b"expected-source"
    )
    with pytest.raises(ValueError, match="Point3Record"):
        runtime.preview((0.0, 0.0, 0.0))
