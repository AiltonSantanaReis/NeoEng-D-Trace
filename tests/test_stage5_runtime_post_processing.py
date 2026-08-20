"""Tests for the deterministic post-processing runtime sidecar."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from src.runtime.post_processing import (
    POST_PROCESSING_BACKEND,
    PostProcessingCapabilityError,
    PostProcessingDocumentV1,
    PostProcessingEffectRecord,
    PostProcessingFallbackRecord,
    PostProcessingFormatError,
    PostProcessingPreviewError,
    PostProcessingRuntime,
    PostProcessingSourceBindingRecord,
    PostProcessingValidationError,
    load_post_processing_runtime_export_bytes,
    post_processing_runtime_export_sha256,
    save_post_processing_runtime_export,
    serialize_post_processing_runtime_export,
    verify_post_processing_source_binding,
)
from src.runtime.scene_runtime import CapabilityRequest, RuntimeHost


def _effect(
    effect_id: str,
    kind: str,
    order: int,
    parameters: dict[str, object],
    *,
    enabled: bool = True,
) -> PostProcessingEffectRecord:
    return PostProcessingEffectRecord(
        id=effect_id,
        kind=kind,
        order=order,
        enabled=enabled,
        parameters=parameters,
    )


def _document(*, fallback_mode: str = "cpu-preview") -> PostProcessingDocumentV1:
    return PostProcessingDocumentV1(
        source=PostProcessingSourceBindingRecord(sha256="a" * 64),
        fallback=PostProcessingFallbackRecord(
            mode=fallback_mode,
            reason="The requested engine has no Stage 5 adapter yet.",
        ),
        effects=[
            _effect("vignette", "vignette", 20, {"amount": 0.5, "radius": 0.5}),
            _effect("exposure", "exposure", 10, {"stops": 1.0}),
            _effect(
                "gray-disabled",
                "grayscale",
                30,
                {"amount": 1.0},
                enabled=False,
            ),
        ],
    )


def _image() -> np.ndarray:
    return np.array(
        [
            [[0.2, 0.4, 0.6, 0.25], [0.8, 0.3, 0.1, 0.5]],
            [[0.1, 0.7, 0.2, 0.75], [0.4, 0.5, 0.9, 1.0]],
        ],
        dtype=np.float64,
    )


def test_post_processing_contract_is_canonical_and_hash_bound() -> None:
    document = _document()
    raw = serialize_post_processing_runtime_export(document)
    assert raw.endswith(b"\n")
    assert load_post_processing_runtime_export_bytes(raw) == document
    assert (
        post_processing_runtime_export_sha256(document)
        == hashlib.sha256(raw).hexdigest()
    )
    with pytest.raises(PostProcessingValidationError):
        verify_post_processing_source_binding(document, b"not-the-bound-source")
    bound = document.model_copy(
        update={
            "source": PostProcessingSourceBindingRecord(
                sha256=hashlib.sha256(b"bound-source").hexdigest()
            )
        }
    )
    verify_post_processing_source_binding(bound, b"bound-source")


def test_post_processing_loader_rejects_noncanonical_bom_duplicates_and_nan() -> None:
    document = _document()
    raw = serialize_post_processing_runtime_export(document)
    with pytest.raises(PostProcessingFormatError):
        load_post_processing_runtime_export_bytes(b"\xef\xbb\xbf" + raw)
    with pytest.raises(PostProcessingFormatError):
        load_post_processing_runtime_export_bytes(raw.replace(b"\n", b"\r\n"))
    with pytest.raises(PostProcessingFormatError):
        load_post_processing_runtime_export_bytes(b'{"format_id":1,"format_id":2}')
    payload = json.loads(raw)
    payload["effects"][0]["parameters"]["amount"] = float("nan")
    with pytest.raises(PostProcessingValidationError):
        serialize_post_processing_runtime_export(payload)  # type: ignore[arg-type]


def test_post_processing_rejects_duplicate_order_unknown_parameters_and_limits() -> (
    None
):
    with pytest.raises(ValueError):
        PostProcessingDocumentV1(
            source=PostProcessingSourceBindingRecord(sha256="a" * 64),
            fallback=PostProcessingFallbackRecord(
                mode="cpu-preview", reason="duplicate order rejection"
            ),
            effects=[
                _effect("a", "exposure", 1, {"stops": 0.0}),
                _effect("b", "exposure", 1, {"stops": 0.0}),
            ],
        )
    with pytest.raises(ValueError):
        _effect("bad", "exposure", 0, {"stops": 0.0, "unexpected": 1.0})
    with pytest.raises(ValueError):
        _effect("bad", "box_blur", 0, {"radius": 9})


def test_post_processing_preview_is_deterministic_ordered_and_preserves_alpha() -> None:
    runtime = PostProcessingRuntime()
    runtime.load_manifest(_document())
    first = runtime.preview(_image())
    second = runtime.preview(_image())
    assert first.backend == POST_PROCESSING_BACKEND
    assert first.compatibility == "native"
    assert first.applied_effect_ids == ("exposure", "vignette")
    assert first.skipped_effect_ids == ("gray-disabled",)
    assert first.output_sha256 == second.output_sha256
    assert np.array_equal(first.image, second.image)
    assert np.array_equal(first.image[:, :, 3], _image()[:, :, 3])
    assert np.all(first.image[:, :, :3] >= 0.0)
    assert np.all(first.image[:, :, :3] <= 1.0)


def test_post_processing_effects_cover_tint_grayscale_and_blur() -> None:
    document = PostProcessingDocumentV1(
        source=PostProcessingSourceBindingRecord(sha256="a" * 64),
        fallback=PostProcessingFallbackRecord(
            mode="cpu-preview", reason="safe preview fallback"
        ),
        effects=[
            _effect("tint", "tint", 0, {"amount": 1.0, "color": [1.0, 0.0, 0.0]}),
            _effect("gray", "grayscale", 1, {"amount": 1.0}),
            _effect("blur", "box_blur", 2, {"radius": 1}),
        ],
    )
    runtime = PostProcessingRuntime()
    runtime.load_manifest(document)
    result = runtime.preview(np.ones((3, 3, 4), dtype=np.float64))
    assert result.applied_effect_ids == ("tint", "gray", "blur")
    assert result.image.shape == (3, 3, 4)
    assert np.allclose(result.image[:, :, 3], 1.0)
    assert np.all(np.isfinite(result.image))


def test_post_processing_fallback_is_explicit_for_unknown_backend() -> None:
    runtime = PostProcessingRuntime()
    runtime.load_manifest(_document(fallback_mode="cpu-preview"))
    degraded = runtime.preview(_image(), backend="godot")
    assert degraded.compatibility == "degraded"
    assert degraded.backend == POST_PROCESSING_BACKEND
    assert degraded.fallback_mode == POST_PROCESSING_BACKEND
    assert degraded.fallback_reason

    disabled = PostProcessingRuntime()
    disabled.load_manifest(_document(fallback_mode="disable"))
    result = disabled.preview(_image(), backend="unity")
    assert result.compatibility == "degraded"
    assert result.backend == "disable"
    assert result.applied_effect_ids == ()
    assert np.array_equal(result.image, _image())

    rejected = PostProcessingRuntime()
    rejected.load_manifest(_document(fallback_mode="reject"))
    with pytest.raises(PostProcessingCapabilityError):
        rejected.preview(_image(), backend="godot")


def test_post_processing_requires_loaded_document_and_valid_image() -> None:
    runtime = PostProcessingRuntime()
    with pytest.raises(PostProcessingPreviewError):
        runtime.preview(_image())
    runtime.load_manifest(_document())
    with pytest.raises(PostProcessingPreviewError):
        runtime.preview(np.zeros((2, 2, 3), dtype=np.float64))
    invalid = _image().copy()
    invalid[0, 0, 0] = np.nan
    with pytest.raises(PostProcessingPreviewError):
        runtime.preview(invalid)


def test_post_processing_persistence_is_atomic_and_rejects_invalid_replacement(
    tmp_path,
) -> None:
    document = _document()
    destination = tmp_path / "post-processing.json"
    save_post_processing_runtime_export(document, destination)
    previous = destination.read_bytes()
    assert load_post_processing_runtime_export_bytes(previous) == document
    invalid = document.model_dump(mode="json")
    invalid["effects"][0]["parameters"]["unknown"] = 1.0
    with pytest.raises(PostProcessingValidationError):
        save_post_processing_runtime_export(
            invalid, destination  # type: ignore[arg-type]
        )
    assert destination.read_bytes() == previous


def test_post_processing_runtime_host_advertises_capability() -> None:
    report = RuntimeHost().negotiate(
        [CapabilityRequest(required_capability="runtime.post_processing")]
    )
    assert report.accepted
    assert report.decisions[0].mode == "native"
