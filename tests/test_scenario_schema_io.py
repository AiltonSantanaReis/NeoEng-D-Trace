"""Real contract, hash, round-trip and rollback tests for lateral scenarios."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import src.persistence.scenario_schema as scenario_schema
from src.core.atomic_outputs import AtomicOutputTransaction
from src.persistence.scenario_io import (
    ScenarioFormatError,
    ScenarioReadError,
    ScenarioValidationError,
    ScenarioWriteError,
    hash_project_file,
    load_scenario,
    project_reference_for,
    save_scenario,
    scenario_sha256,
    serialize_scenario,
    verify_project_reference,
)
from src.persistence.scenario_schema import (
    SCENARIO_FORMAT_ID,
    SCENARIO_SCHEMA_VERSION,
    ScenarioCameraRecord,
    ScenarioDocumentV1,
    ScenarioLayerRecord,
    ScenarioParallaxRecord,
    _finite_number,
    default_scenario_metadata,
)


def _project(path: Path, content: bytes = b"project-v1\n") -> Path:
    path.write_bytes(content)
    return path


def _document(project: Path) -> ScenarioDocumentV1:
    return ScenarioDocumentV1(
        metadata=default_scenario_metadata("Parallax test"),
        project=project_reference_for(project),
        camera=ScenarioCameraRecord(position={"x": 12.5, "y": -4.0}, zoom=1.25),
        layers=[
            ScenarioLayerRecord(
                id="background",
                name="Background",
                visible=True,
                object_ids=["object-background"],
                parallax=ScenarioParallaxRecord(
                    depth=1.0, translation_strength=1.0, zoom_strength=0.5
                ),
            ),
            ScenarioLayerRecord(
                id="foreground",
                name="Foreground",
                visible=False,
                object_ids=["object-foreground"],
                parallax=ScenarioParallaxRecord(depth=0.0),
            ),
        ],
    )


def test_schema_has_explicit_identity_and_does_not_change_project_contract(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    document = _document(project)

    assert document.format_id == SCENARIO_FORMAT_ID
    assert document.schema_version == SCENARIO_SCHEMA_VERSION
    assert document.project.format_id == "neoeng-d-trace-project"
    assert document.project.schema_version == 1
    assert document.layers[0].parallax.depth == 1.0
    assert document.layers[0].object_ids == ["object-background"]
    assert document.model_dump(mode="json").get("position") is None
    assert project.read_bytes() == b"project-v1\n"


def test_serialization_is_canonical_and_hash_matches_exact_bytes(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    document = _document(project)
    first = serialize_scenario(document)
    second = serialize_scenario(document)
    sidecar = tmp_path / "scene.ndtscenario.json"
    save_scenario(document, sidecar)

    assert first == second == sidecar.read_bytes()
    assert first.endswith(b"\n")
    assert scenario_sha256(document) == hashlib.sha256(first).hexdigest()
    payload = json.loads(first)
    assert payload["format_id"] == SCENARIO_FORMAT_ID
    assert payload["schema_version"] == 1
    assert "project" in payload and "sha256" in payload["project"]


def test_round_trip_and_hash_bound_load_use_real_files(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    sidecar = tmp_path / "scene.ndtscenario.json"
    document = _document(project)
    save_scenario(document, sidecar)

    loaded = load_scenario(sidecar, project_path=project)

    assert loaded == document
    assert scenario_sha256(loaded) == scenario_sha256(document)
    assert (
        hash_project_file(project) == hashlib.sha256(project.read_bytes()).hexdigest()
    )


def test_valid_load_without_optional_project_verification(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    sidecar = tmp_path / "scene.ndtscenario.json"
    document = _document(project)
    save_scenario(document, sidecar)

    assert load_scenario(sidecar) == document


def test_project_hash_mismatch_is_rejected_without_mutating_any_file(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    sidecar = tmp_path / "scene.ndtscenario.json"
    document = _document(project)
    save_scenario(document, sidecar)
    before_project = project.read_bytes()
    project.write_bytes(b"changed-project-v1\n")
    before_sidecar = sidecar.read_bytes()

    with pytest.raises(ScenarioValidationError, match="hash does not match"):
        load_scenario(sidecar, project_path=project)

    assert project.read_bytes() == b"changed-project-v1\n"
    assert sidecar.read_bytes() == before_sidecar
    assert before_project != project.read_bytes()


def test_explicit_reference_verification_accepts_original_project(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    document = _document(project)

    verify_project_reference(document, project)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("depth", -0.01),
        ("depth", 1.01),
        ("translation_strength", 2),
        ("zoom_strength", float("inf")),
    ],
)
def test_parallax_values_are_bounded_and_finite(field, value):
    with pytest.raises(ValueError, match="between 0 and 1|finite"):
        ScenarioParallaxRecord(**{field: value})


def test_camera_zoom_must_be_finite_and_positive():
    with pytest.raises(ValueError, match="positive"):
        ScenarioCameraRecord(position={"x": 0, "y": 0}, zoom=0)
    with pytest.raises(ValueError, match="finite"):
        ScenarioCameraRecord(position={"x": 0, "y": 0}, zoom=float("nan"))


def test_finite_number_helper_rejects_boolean_inputs():
    with pytest.raises(ValueError, match="finite number"):
        _finite_number(True, "test")


def test_invalid_object_ids_and_reference_limit_are_rejected(tmp_path, monkeypatch):
    project = _project(tmp_path / "scene.ndtproj")
    with pytest.raises(ValueError, match="non-empty"):
        ScenarioLayerRecord(
            id="layer",
            name="Layer",
            object_ids=[""],
            parallax=ScenarioParallaxRecord(),
        )
    with pytest.raises(ValueError, match="unique within a layer"):
        ScenarioLayerRecord(
            id="layer",
            name="Layer",
            object_ids=["object", "object"],
            parallax=ScenarioParallaxRecord(),
        )

    monkeypatch.setattr(scenario_schema, "MAX_SCENARIO_OBJECT_REFERENCES", 1)
    with pytest.raises(ValueError, match="object reference limit"):
        ScenarioDocumentV1(
            metadata=default_scenario_metadata(),
            project=project_reference_for(project),
            camera=ScenarioCameraRecord(position={"x": 0, "y": 0}),
            layers=[
                ScenarioLayerRecord(
                    id="layer",
                    name="Layer",
                    object_ids=["object-a", "object-b"],
                    parallax=ScenarioParallaxRecord(),
                )
            ],
        )


def test_duplicate_layer_and_object_references_are_rejected(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    reference = project_reference_for(project)
    layer = ScenarioLayerRecord(
        id="layer",
        name="Layer",
        object_ids=["object"],
        parallax=ScenarioParallaxRecord(),
    )
    with pytest.raises(ValueError, match="layer IDs"):
        ScenarioDocumentV1(
            metadata=default_scenario_metadata(),
            project=reference,
            camera=ScenarioCameraRecord(position={"x": 0, "y": 0}),
            layers=[layer, layer],
        )
    with pytest.raises(ValueError, match="object references"):
        ScenarioDocumentV1(
            metadata=default_scenario_metadata(),
            project=reference,
            camera=ScenarioCameraRecord(position={"x": 0, "y": 0}),
            layers=[
                layer,
                ScenarioLayerRecord(
                    id="layer-2",
                    name="Layer 2",
                    object_ids=["object"],
                    parallax=ScenarioParallaxRecord(),
                ),
            ],
        )


@pytest.mark.parametrize(
    "payload",
    [
        b'\xef\xbb\xbf{"format_id":"neoeng-d-trace-scenario"}',
        b'{"format_id":"neoeng-d-trace-scenario","format_id":"duplicate"}',
        b'{"format_id":"neoeng-d-trace-scenario","schema_version":1,',
        b"\xff\xfe\xfd",
    ],
)
def test_malformed_json_utf8_bom_and_duplicate_keys_are_rejected(tmp_path, payload):
    path = tmp_path / "invalid.ndtscenario.json"
    path.write_bytes(payload)

    with pytest.raises(ScenarioFormatError):
        load_scenario(path)


def test_root_format_and_non_finite_json_are_rejected(tmp_path):
    path = tmp_path / "invalid.ndtscenario.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ScenarioFormatError, match="root"):
        load_scenario(path)

    path.write_text('{"format_id":"wrong","schema_version":1}', encoding="utf-8")
    with pytest.raises(ScenarioFormatError, match="format identifier"):
        load_scenario(path)

    path.write_text('{"value": NaN}', encoding="utf-8")
    with pytest.raises(ScenarioFormatError, match="non-finite"):
        load_scenario(path)


def test_missing_directory_and_oversized_scenario_are_rejected(tmp_path):
    with pytest.raises(ScenarioReadError, match="not found"):
        load_scenario(tmp_path / "missing.ndtscenario.json")

    directory = tmp_path / "scenario-directory"
    directory.mkdir()
    with pytest.raises(ScenarioReadError, match="not a file"):
        load_scenario(directory)

    oversized = tmp_path / "oversized.ndtscenario.json"
    with oversized.open("wb") as handle:
        handle.truncate(scenario_schema.MAX_SCENARIO_FILE_BYTES + 1)
    with pytest.raises(ScenarioReadError, match="exceeds"):
        load_scenario(oversized)


def test_wrong_version_and_unknown_fields_are_rejected(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    payload = json.loads(serialize_scenario(_document(project)))
    payload["schema_version"] = 2
    path = tmp_path / "wrong-version.ndtscenario.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ScenarioFormatError, match="schema version"):
        load_scenario(path)

    payload = json.loads(serialize_scenario(_document(project)))
    payload["unexpected"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ScenarioValidationError, match="extra"):
        load_scenario(path)


def test_missing_or_invalid_project_reference_is_rejected(tmp_path):
    missing = tmp_path / "missing.ndtproj"
    with pytest.raises(ScenarioReadError, match="not found"):
        hash_project_file(missing)
    wrong_suffix = tmp_path / "scene.json"
    wrong_suffix.write_bytes(b"project")
    with pytest.raises(ScenarioReadError, match=".ndtproj"):
        hash_project_file(wrong_suffix)


def test_save_requires_existing_parent_and_never_creates_partial_output(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    document = _document(project)
    target = tmp_path / "missing" / "scene.ndtscenario.json"

    with pytest.raises(ScenarioWriteError, match="does not exist"):
        save_scenario(document, target)
    assert not target.exists()


def test_save_rolls_back_existing_sidecar_when_replace_fails(tmp_path, monkeypatch):
    project = _project(tmp_path / "scene.ndtproj")
    document = _document(project)
    sidecar = tmp_path / "scene.ndtscenario.json"
    save_scenario(document, sidecar)
    old_bytes = sidecar.read_bytes()

    original_replace = AtomicOutputTransaction._replace

    def fail_replace(transaction, source, destination):
        if Path(destination) == sidecar:
            raise OSError("controlled scenario replace failure")
        return original_replace(transaction, source, destination)

    monkeypatch.setattr(AtomicOutputTransaction, "_replace", fail_replace)
    changed = _document(project).model_copy(
        update={"metadata": default_scenario_metadata("Changed")}
    )

    with pytest.raises(ScenarioWriteError, match="controlled scenario replace failure"):
        save_scenario(changed, sidecar)

    assert sidecar.read_bytes() == old_bytes
    assert not list(tmp_path.glob(".neoeng-*"))


def test_save_rejects_destination_directory(tmp_path):
    project = _project(tmp_path / "scene.ndtproj")
    destination = tmp_path / "directory"
    destination.mkdir()

    with pytest.raises(ScenarioWriteError, match="destination is a directory"):
        save_scenario(_document(project), destination)
