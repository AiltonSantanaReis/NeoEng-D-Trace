"""Strict export and consumer-contract tests for Stage 4B.4."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.core.scenario_authoring import ScenarioAuthoringState
from src.exporters.scenario_exporter import (
    SCENARIO_EXPORT_FORMAT_ID,
    ScenarioExportError,
    build_scenario_runtime_export,
    save_scenario_runtime_export,
    serialize_scenario_runtime_export,
    validate_scenario_runtime_export,
)
from src.models.scene import Scene
from src.persistence.project_schema import PointRecord
from src.persistence.scenario_io import scenario_sha256
from src.persistence.scenario_schema import (
    ProjectReferenceRecord,
    ScenarioCameraRecord,
    ScenarioDocumentV1,
    ScenarioLayerRecord,
    ScenarioParallaxRecord,
    default_scenario_metadata,
)


def _document() -> ScenarioDocumentV1:
    return ScenarioDocumentV1(
        metadata=default_scenario_metadata("Runtime Fixture"),
        project=ProjectReferenceRecord(sha256="a" * 64),
        camera=ScenarioCameraRecord(
            position=PointRecord(x=12.0, y=-4.0),
            zoom=1.5,
        ),
        layers=[
            ScenarioLayerRecord(
                id="layer_foreground",
                name="Foreground",
                visible=True,
                object_ids=["object_a"],
                parallax=ScenarioParallaxRecord(
                    depth=0.25,
                    translation_strength=0.75,
                    zoom_strength=0.8,
                ),
            ),
            ScenarioLayerRecord(
                id="layer_background",
                name="Background",
                visible=False,
                object_ids=[],
                parallax=ScenarioParallaxRecord(
                    depth=1.0,
                    translation_strength=0.5,
                    zoom_strength=0.4,
                ),
            ),
        ],
    )


def test_runtime_export_is_deterministic_and_hash_bound():
    document = _document()
    first = serialize_scenario_runtime_export(document)
    second = serialize_scenario_runtime_export(document)
    assert first == second
    payload = json.loads(first)
    assert payload["format_id"] == SCENARIO_EXPORT_FORMAT_ID
    assert payload["source"]["sha256"] == scenario_sha256(document)
    assert payload["project"]["sha256"] == "a" * 64
    validate_scenario_runtime_export(payload)
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.clear(),
        lambda payload: payload.__setitem__("format_id", "wrong"),
        lambda payload: payload.__setitem__("schema_version", 2),
        lambda payload: payload.__setitem__("generator", None),
        lambda payload: payload["generator"].__setitem__("version", 1),
        lambda payload: payload.__setitem__("source", None),
        lambda payload: payload["source"].__setitem__("sha256", "short"),
        lambda payload: payload.__setitem__("project", None),
        lambda payload: payload["project"].__setitem__("sha256", "short"),
        lambda payload: payload.__setitem__("camera", None),
        lambda payload: payload["camera"].__setitem__("position", None),
        lambda payload: payload["camera"].__setitem__("zoom", "bad"),
        lambda payload: payload["camera"].__setitem__("zoom", 0),
        lambda payload: payload.__setitem__("layers", None),
        lambda payload: payload.__setitem__("layers", [None]),
        lambda payload: payload["layers"][0].__setitem__("id", ""),
        lambda payload: payload["layers"][0].__setitem__("name", 1),
        lambda payload: payload["layers"][0].__setitem__("visible", 1),
        lambda payload: payload["layers"][0].__setitem__("object_ids", [1]),
        lambda payload: payload["layers"][0].__setitem__("parallax", None),
        lambda payload: payload["layers"][0]["parallax"].__setitem__("depth", "bad"),
        lambda payload: payload["layers"][0]["parallax"].__setitem__("depth", -1),
    ],
)
def test_runtime_export_rejects_invalid_runtime_payloads(mutate):
    payload = build_scenario_runtime_export(_document())
    mutate(payload)
    with pytest.raises(ScenarioExportError):
        validate_scenario_runtime_export(payload)


def test_runtime_export_rejects_invalid_document_input():
    with pytest.raises(ScenarioExportError):
        build_scenario_runtime_export(object())


def test_runtime_export_preserves_order_and_rejects_contract_drift():
    payload = build_scenario_runtime_export(_document())
    assert [layer["id"] for layer in payload["layers"]] == [
        "layer_foreground",
        "layer_background",
    ]
    invalid = copy.deepcopy(payload)
    invalid["layers"][1]["object_ids"] = ["object_a"]
    with pytest.raises(ScenarioExportError, match="invalid reference"):
        validate_scenario_runtime_export(invalid)

    invalid = copy.deepcopy(payload)
    invalid["unexpected"] = True
    with pytest.raises(ScenarioExportError, match="keys"):
        validate_scenario_runtime_export(invalid)

    invalid = copy.deepcopy(payload)
    invalid["layers"][0]["parallax"]["depth"] = 2.0
    with pytest.raises(ScenarioExportError, match="between 0 and 1"):
        validate_scenario_runtime_export(invalid)


def test_runtime_export_atomic_save_and_failure_preserves_previous_bytes(tmp_path):
    destination = tmp_path / "scenario.runtime.json"
    document = _document()
    save_scenario_runtime_export(document, destination)
    before = destination.read_bytes()
    assert hashlib.sha256(before).hexdigest()

    with pytest.raises(ScenarioExportError):
        save_scenario_runtime_export(document, tmp_path / "missing" / destination.name)
    assert destination.read_bytes() == before

    destination.write_bytes(b"manual bytes")
    with pytest.raises(ScenarioExportError):
        save_scenario_runtime_export(document, tmp_path / "missing" / destination.name)
    assert destination.read_bytes() == b"manual bytes"


def test_authoring_state_exports_next_to_bound_sidecar(tmp_path):
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"scenario project fixture\n")
    state = ScenarioAuthoringState(Scene())
    state.bind_project(project)
    destination = state.export_runtime()
    assert destination.name == "scene.ndtscenario.runtime.json"
    assert destination.is_file()
    payload = json.loads(destination.read_text(encoding="utf-8"))
    validate_scenario_runtime_export(payload)
    assert (
        payload["project"]["sha256"] == hashlib.sha256(project.read_bytes()).hexdigest()
    )


def test_native_consumer_sources_expose_the_same_runtime_contract():
    root = Path(__file__).resolve().parents[1]
    godot = (
        root / "integrations/godot/addons/neoeng_d_trace/scenario_importer.gd"
    ).read_text(encoding="utf-8")
    unity = (
        root / "integrations/unity/package/com.neoeng.dtrace/Editor/"
        "ScenarioImportGenerator.cs"
    ).read_text(encoding="utf-8")
    for source in (godot, unity):
        assert "neoeng-d-trace-scenario-runtime" in source
        assert "schema_version" in source
        assert "object_ids" in source
        assert "parallax" in source
        assert "generator" in source
        assert "format_id" in source
        assert "scenario" in source.lower()
    assert "_exact_keys" in godot
    assert "_lower_hex_hash" in godot
    assert "object_reference_count" in godot
    assert "GeneratorData" in unity
    assert "RequireHash" in unity
    assert "objectReferenceCount" in unity
