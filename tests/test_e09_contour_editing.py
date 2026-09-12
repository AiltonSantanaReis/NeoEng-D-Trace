"""E09-B safe contour correction, simplification and cancellation contracts."""

from __future__ import annotations

from pathlib import Path
from dataclasses import replace

import cv2
import numpy as np
import pytest

from src.core.contour_editing import ContourEditSession
from src.core.vectorization import VectorizationError, vectorize_image_file


def _result(tmp_path: Path):
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    assert ok
    source = tmp_path / "subject.png"
    source.write_bytes(encoded.tobytes())
    return vectorize_image_file(source)


def test_manual_edit_undo_redo_and_provenance_are_preserved(tmp_path: Path) -> None:
    result = _result(tmp_path)
    session = ContourEditSession(result)
    original_hash = result.source_sha256
    edited = session.move_vertex(1, (110, 20))

    assert edited[1] == (110.0, 20.0)
    assert session.can_undo
    assert session.result().source_sha256 == original_hash
    assert session.undo() == result.polygon
    assert session.redo() == edited


def test_invalid_manual_edit_is_rejected_without_mutating_state(tmp_path: Path) -> None:
    session = ContourEditSession(_result(tmp_path))
    before = session.current_polygon
    with pytest.raises(VectorizationError, match="invalid_geometry"):
        session.move_vertex(1, (10, 90))
    assert session.current_polygon == before
    assert not session.can_undo


def test_simplification_is_transactional_and_recorded(tmp_path: Path) -> None:
    result = _result(tmp_path)
    result = replace(
        result,
        polygon=tuple(
            (float(x), float(y))
            for x, y in (
                (24, 18),
                (45, 18),
                (70, 18),
                (103, 18),
                (103, 40),
                (103, 77),
                (70, 77),
                (45, 77),
                (24, 77),
                (24, 40),
            )
        ),
    )
    session = ContourEditSession(result)
    simplified = session.simplify(3.0)
    assert len(simplified) < len(result.polygon)
    assert session.history[-1].operation == "simplify"
    assert session.undo() == result.polygon


def test_cancel_restores_original_and_blocks_later_mutation(tmp_path: Path) -> None:
    result = _result(tmp_path)
    session = ContourEditSession(result)
    session.move_vertex(1, (110, 20))
    assert session.cancel() == result.polygon
    assert session.cancelled
    with pytest.raises(VectorizationError, match="session_cancelled"):
        session.result()


def test_remove_and_insert_keep_polygon_valid_and_report_limits(tmp_path: Path) -> None:
    session = ContourEditSession(_result(tmp_path))
    session.remove_vertex(0)
    with pytest.raises(VectorizationError, match="invalid_geometry"):
        session.remove_vertex(0)
    session = ContourEditSession(_result(tmp_path))
    inserted = session.insert_vertex(0, (50, 18))
    assert len(inserted) == 5
    assert session.undo() == session.original_polygon
    with pytest.raises(VectorizationError, match="invalid_epsilon"):
        session.simplify(0)
