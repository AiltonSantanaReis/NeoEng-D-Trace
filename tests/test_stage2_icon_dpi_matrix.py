from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts.audit_stage2_icon_dpi_matrix import (
    DPI_CASES,
    ICON_SIZES,
    _validate_cases,
    _validate_gallery_png,
)


def test_stage2_dpi_matrix_is_exact_and_ordered():
    _validate_cases()
    assert tuple(percent for percent, _ in DPI_CASES) == ("100", "125", "150", "200")
    assert tuple(factor for _, factor in DPI_CASES) == (1.0, 1.25, 1.5, 2.0)
    assert ICON_SIZES == (16, 20, 24, 32)


def test_stage2_dpi_matrix_rejects_non_positive_or_unsorted_cases(monkeypatch):
    import scripts.audit_stage2_icon_dpi_matrix as matrix

    monkeypatch.setattr(
        matrix,
        "DPI_CASES",
        (("100", 1.0), ("125", 1.25), ("150", 1.5), ("200", 1.4)),
    )
    with pytest.raises(AssertionError, match="strictly increasing"):
        matrix._validate_cases()


def test_stage2_dpi_matrix_rejects_missing_required_percent(monkeypatch):
    import scripts.audit_stage2_icon_dpi_matrix as matrix

    monkeypatch.setattr(matrix, "DPI_CASES", (("100", 1.0), ("150", 1.5), ("200", 2.0)))
    with pytest.raises(AssertionError, match="100/125/150/200"):
        matrix._validate_cases()


def _gallery_runtime() -> dict[str, object]:
    return {
        "observed_device_pixel_ratio": 1.0,
        "buttons": [
            {
                "key": "test",
                "size": 16,
                "logical_geometry": [4, 4, 12, 12],
            }
        ],
    }


def test_gallery_validation_accepts_non_clipped_icon(tmp_path: Path):
    pixels = np.full((20, 20, 3), (32, 38, 46), dtype=np.uint8)
    pixels[8:12, 8:12] = (235, 240, 245)
    path = tmp_path / "gallery.png"
    Image.fromarray(pixels, mode="RGB").save(path)

    result = _validate_gallery_png(path, _gallery_runtime())

    assert result["status"] == "PASS"
    assert result["checked_cells"] == 1


def test_gallery_validation_rejects_content_touching_outer_border(tmp_path: Path):
    pixels = np.full((20, 20, 3), (32, 38, 46), dtype=np.uint8)
    pixels[0, 0] = (235, 240, 245)
    path = tmp_path / "gallery-border.png"
    Image.fromarray(pixels, mode="RGB").save(path)

    with pytest.raises(AssertionError, match="outer border"):
        _validate_gallery_png(path, _gallery_runtime())
