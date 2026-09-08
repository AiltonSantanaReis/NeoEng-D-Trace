"""Contract and lifecycle tests for the E01 independent empty scene."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.independent_scene_session import IndependentSceneSession
from src.persistence.independent_scene_io import (
    IndependentSceneFormatError,
    IndependentSceneValidationError,
    IndependentSceneWriteError,
    independent_scene_sha256,
    load_independent_scene,
    save_independent_scene,
    serialize_independent_scene,
)
from src.persistence.independent_scene_schema import (
    INDEPENDENT_SCENE_FORMAT_ID,
    default_independent_scene_document,
)


def test_empty_scene_is_independent_and_has_explicit_canvas_contract() -> None:
    document = default_independent_scene_document(
        name="Prototype",
        width=1280,
        height=720,
    )

    payload = document.model_dump(mode="json")
    assert payload["format_id"] == INDEPENDENT_SCENE_FORMAT_ID
    assert payload["schema_version"] == 1
    assert payload["resolution"] == {"width": 1280, "height": 720}
    assert payload["coordinates"] == {
        "origin": "top_left",
        "unit": "pixel",
        "x_axis": "right",
        "y_axis": "down",
    }
    assert payload["assets_root"] == "assets"
    assert payload["compatibility"] == {
        "reader_min_schema_version": 1,
        "writer_schema_version": 1,
    }
    assert payload["camera"]["zoom"] == 1.0
    assert "project" not in payload
    assert "sha256" not in payload


def test_canonical_round_trip_and_exact_hash(tmp_path: Path) -> None:
    document = default_independent_scene_document(width=1600, height=900)
    path = tmp_path / "empty.ndtscene"

    save_independent_scene(document, path)
    loaded = load_independent_scene(path)

    assert loaded == document
    assert path.read_bytes() == serialize_independent_scene(document)
    assert independent_scene_sha256(loaded)


def test_session_new_update_save_save_as_and_reopen(tmp_path: Path) -> None:
    session = IndependentSceneSession(last_folder=str(tmp_path))
    session.new(name="Arena", width=1024, height=576)
    session.set_camera(x=12.5, y=-4.0, zoom=1.25)
    assert session.is_modified

    first = session.save(tmp_path / "arena")
    assert first.name == "arena.ndtscene"
    assert not session.is_modified

    session.set_resolution(800, 450)
    second = session.save_as(tmp_path / "arena-copy.ndtscene")
    assert second.name == "arena-copy.ndtscene"
    assert not session.is_modified

    reopened = IndependentSceneSession()
    reopened.load(second)
    assert reopened.path == second.resolve()
    assert reopened.document.resolution.width == 800
    assert reopened.document.camera.zoom == 1.25
    assert not reopened.is_modified


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("width", 0),
        ("height", 32_769),
    ],
)
def test_resolution_limits_are_rejected(field: str, value: int) -> None:
    with pytest.raises(ValueError):
        default_independent_scene_document(**{field: value})


def test_invalid_version_and_unknown_fields_are_rejected(tmp_path: Path) -> None:
    payload = json.loads(
        serialize_independent_scene(default_independent_scene_document())
    )
    payload["schema_version"] = 2
    path = tmp_path / "future.ndtscene"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IndependentSceneFormatError, match="schema version"):
        load_independent_scene(path)

    payload["schema_version"] = 1
    payload["unexpected"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(IndependentSceneValidationError, match="extra"):
        load_independent_scene(path)


def test_malformed_json_bom_and_wrong_extension_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.ndtscene"
    path.write_bytes(b"\xef\xbb\xbf{}")
    with pytest.raises(IndependentSceneFormatError, match="BOM"):
        load_independent_scene(path)

    with pytest.raises(IndependentSceneWriteError, match="extension"):
        save_independent_scene(
            default_independent_scene_document(),
            tmp_path / "wrong.json",
        )
