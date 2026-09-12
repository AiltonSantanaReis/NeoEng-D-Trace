"""E09-A controlled image import and contour detection contracts."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from src.core.vectorization import (
    VectorizationError,
    VectorizationRequest,
    vectorize_image_file,
)


def _write_rgba(path: Path, *, hole: bool = False, islands: bool = False) -> None:
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    if hole:
        image[40:56, 50:78, 3] = 0
    if islands:
        image[4:10, 4:10, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    assert ok
    path.write_bytes(encoded.tobytes())


def test_vectorization_is_deterministic_and_preserves_source_provenance(
    tmp_path: Path,
) -> None:
    source = tmp_path / "subject.png"
    _write_rgba(source)
    request = VectorizationRequest(
        channel="alpha", threshold=1, approximation_epsilon=1.0
    )

    first = vectorize_image_file(source, request)
    second = vectorize_image_file(source, request)

    assert first == second
    assert first.source_path == str(source.resolve())
    assert len(first.source_sha256) == 64
    assert first.image_width == 128 and first.image_height == 96
    assert first.polygon == ((24, 18), (103, 18), (103, 77), (24, 77))
    assert first.area2 > 0
    assert first.as_dict()["polygon"] == [[24, 18], [103, 18], [103, 77], [24, 77]]


def test_luminance_channel_detects_rgb_source(tmp_path: Path) -> None:
    source = tmp_path / "subject.png"
    image = np.zeros((40, 50, 3), dtype=np.uint8)
    image[5:35, 7:43] = (220, 220, 220)
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    assert ok
    source.write_bytes(encoded.tobytes())

    result = vectorize_image_file(
        source,
        VectorizationRequest(channel="luminance", threshold=10),
    )
    assert result.channel == "luminance"
    assert result.polygon == ((7, 5), (42, 5), (42, 34), (7, 34))


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"channel": "alpha", "threshold": 255}, "empty_mask"),
        ({"maximum_vertices": 2}, "invalid_vertex_limit"),
        ({"approximation_epsilon": -1}, "invalid_epsilon"),
    ],
)
def test_vectorization_rejects_invalid_or_empty_contracts(
    tmp_path: Path, kwargs: dict[str, object], code: str
) -> None:
    source = tmp_path / "subject.png"
    _write_rgba(source)
    with pytest.raises(VectorizationError, match=code):
        request = VectorizationRequest(**kwargs)  # type: ignore[arg-type]
        vectorize_image_file(source, request)


def test_vectorization_rejects_unreadable_and_unsupported_topology(
    tmp_path: Path,
) -> None:
    with pytest.raises(VectorizationError, match="invalid_image"):
        vectorize_image_file(tmp_path / "missing.png")

    for name, kwargs, code in (
        ("hole.png", {"hole": True}, "unsupported_holes"),
        ("islands.png", {"islands": True}, "unsupported_islands"),
    ):
        source = tmp_path / name
        _write_rgba(source, **kwargs)
        with pytest.raises(VectorizationError, match=code):
            vectorize_image_file(source)


def test_vectorization_rejects_source_mutation_between_calls(tmp_path: Path) -> None:
    source = tmp_path / "subject.png"
    _write_rgba(source)
    original = vectorize_image_file(source)
    source.write_bytes(source.read_bytes() + b"changed")
    mutated = vectorize_image_file(source)
    assert original.source_sha256 != mutated.source_sha256
    assert original.polygon == mutated.polygon
