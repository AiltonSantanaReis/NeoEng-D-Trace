"""Branch contracts for deterministic transform geometry."""

from __future__ import annotations

import pytest

from src.core.transform_geometry import (
    anchor_for_polygon,
    finite_float,
    polygon_bounds,
    transform_point,
    transform_points,
    validate_scale,
)


@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf")])
def test_geometry_rejects_non_finite_or_non_numeric_values(value) -> None:
    with pytest.raises(ValueError, match="finite number"):
        finite_float(value, "value")


def test_geometry_validates_bounds_pivots_scales_and_sequences() -> None:
    points = [(2.0, 4.0), (8.0, 10.0)]
    assert polygon_bounds(points) == (2.0, 4.0, 8.0, 10.0)
    assert anchor_for_polygon(points, (0.25, 0.5)) == (3.5, 7.0)
    assert validate_scale(2, -3, 0.5) == (2.0, -3.0)
    assert transform_points(points, (5.0, 7.0), translation=(1.0, 2.0)) == [
        (3.0, 6.0),
        (9.0, 12.0),
    ]

    with pytest.raises(ValueError, match="cannot be empty"):
        polygon_bounds([])
    with pytest.raises(ValueError, match="scale components cannot be zero"):
        validate_scale(1.0, 0.0)
    with pytest.raises(ValueError, match="pivot.x"):
        anchor_for_polygon(points, (float("nan"), 0.5))
    with pytest.raises(ValueError, match="point.x"):
        transform_point((float("inf"), 0.0), (0.0, 0.0))


def test_validation_event_sanitization_covers_nested_and_long_values() -> None:
    from src.core.validation_events import (
        _sanitize_text,
        _sanitize_value,
        file_evidence,
        object_token,
    )

    assert _sanitize_value(None) is None
    assert _sanitize_value(7) == 7
    assert (
        _sanitize_value({"value": ["line\nnext", {"nested": object()}]})["value"][0]
        == "line\\nnext"
    )
    assert _sanitize_value(object()).startswith("<object object at")
    sanitized = _sanitize_text("x" * 40000)
    assert len(sanitized) == 32768 + len("<TRUNCATED>")
    assert sanitized.endswith("<TRUNCATED>")
    assert object_token(None) is None
    assert len(object_token("object-id")) == 12
    assert file_evidence(None) == {"exists": False, "size": 0, "suffix": None}


def test_validation_recorder_rotates_and_is_idempotently_closed(
    tmp_path, monkeypatch
) -> None:
    import src.core.validation_events as validation_events

    path = tmp_path / "validation.jsonl"
    path.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(validation_events, "MAX_VALIDATION_LOG_FILE_BYTES", 1)
    recorder = validation_events._ValidationRecorder(path)
    assert path.with_name("validation.jsonl.1").exists()
    recorder.close()
    recorder.write("ignored")
    recorder.close()
