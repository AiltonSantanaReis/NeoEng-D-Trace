from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from src.exporters.integration_manifest import (
    INTEGRATION_FORMAT_ID,
    INTEGRATION_SCHEMA_VERSION,
    build_integration_manifest,
    save_integration_manifest,
    validate_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene


def _metadata() -> dict:
    scene = Scene()
    scene.add_object("hero", [(1, 2), (9, 2), (9, 10), (1, 10)])
    return export_scene_metadata(scene)


def _manifest(tmp_path: Path, engine: str = "godot") -> dict:
    image = tmp_path / "source.png"
    Image.new("RGBA", (8, 8), (10, 20, 30, 255)).save(image)
    return build_integration_manifest(
        _metadata(),
        engine=engine,
        image_path=image,
        image_reference="assets/source.png",
    )


def test_manifest_contains_real_image_and_metadata_hashes(tmp_path):
    manifest = _manifest(tmp_path)

    assert manifest["format_id"] == INTEGRATION_FORMAT_ID
    assert manifest["schema_version"] == INTEGRATION_SCHEMA_VERSION
    assert manifest["engine"] == "godot"
    assert len(manifest["source"]["image"]["sha256"]) == 64
    assert len(manifest["source"]["metadata"]["sha256"]) == 64
    validate_integration_manifest(manifest)


def test_manifest_supports_unity_without_changing_the_payload(tmp_path):
    manifest = _manifest(tmp_path, engine="UNITY")

    assert manifest["engine"] == "unity"
    assert manifest["sync"]["direction"] == "dtrace-to-engine"
    validate_integration_manifest(manifest)


def test_manifest_save_is_deterministic_and_atomic(tmp_path):
    manifest = _manifest(tmp_path)
    destination = tmp_path / "NeoEngGenerated" / "hero.ndt.integration.json"

    save_integration_manifest(manifest, destination)
    first = destination.read_bytes()
    save_integration_manifest(manifest, destination)
    second = destination.read_bytes()

    assert first == second
    assert json.loads(first)["metadata"]["sprites"][0]["id"] == "hero"
    assert not list(destination.parent.glob(".neoeng-integration-*.json"))


@pytest.mark.parametrize(
    "reference",
    ["", "../source.png", "/absolute/source.png", "C:\\source.png"],
)
def test_manifest_rejects_unsafe_image_references(tmp_path, reference):
    image = tmp_path / "source.png"
    Image.new("RGBA", (2, 2), (1, 2, 3, 255)).save(image)

    with pytest.raises(ValueError, match="relative and safe"):
        build_integration_manifest(
            _metadata(),
            engine="godot",
            image_path=image,
            image_reference=reference,
        )


def test_manifest_rejects_payload_hash_drift(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["metadata"]["sprites"][0]["id"] = "changed"

    with pytest.raises(ValueError, match="metadata hash"):
        validate_integration_manifest(manifest)


def test_manifest_rejects_unknown_engine_and_schema_drift(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["engine"] = "phaser"
    with pytest.raises(ValueError, match="engine"):
        validate_integration_manifest(manifest)

    manifest = _manifest(tmp_path)
    manifest["schema_version"] = 2
    with pytest.raises(ValueError, match="schema"):
        validate_integration_manifest(manifest)


def test_manifest_build_rejects_invalid_inputs(tmp_path):
    image = tmp_path / "source.png"
    Image.new("RGBA", (2, 2), (1, 2, 3, 255)).save(image)

    with pytest.raises(ValueError, match="mapping"):
        build_integration_manifest(
            [], engine="godot", image_path=image, image_reference="source.png"
        )
    with pytest.raises(ValueError, match="unsupported integration engine"):
        build_integration_manifest(
            _metadata(), engine=None, image_path=image, image_reference="source.png"
        )
    with pytest.raises(ValueError, match="generator_version"):
        build_integration_manifest(
            _metadata(),
            engine="godot",
            image_path=image,
            image_reference="source.png",
            generator_version="",
        )
    with pytest.raises(ValueError, match="format_id"):
        build_integration_manifest(
            {"schema_version": 1},
            engine="godot",
            image_path=image,
            image_reference="source.png",
        )
    with pytest.raises(ValueError, match="regular file"):
        build_integration_manifest(
            _metadata(),
            engine="godot",
            image_path=tmp_path / "missing.png",
            image_reference="source.png",
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda manifest: manifest.pop("metadata"),
        lambda manifest: manifest.__setitem__("format_id", "wrong"),
        lambda manifest: manifest.__setitem__("schema_version", 2),
        lambda manifest: manifest.__setitem__("generator", {}),
        lambda manifest: manifest["generator"].__setitem__("version", ""),
        lambda manifest: manifest.__setitem__("engine", "phaser"),
        lambda manifest: manifest.__setitem__("source", {}),
        lambda manifest: manifest["source"].__setitem__("image", {}),
        lambda manifest: manifest["source"]["image"].__setitem__("sha256", "short"),
        lambda manifest: manifest["source"].__setitem__("metadata", None),
        lambda manifest: manifest["source"]["metadata"].__setitem__(
            "format_id", "wrong"
        ),
        lambda manifest: manifest["source"]["metadata"].__setitem__(
            "schema_version", 99
        ),
        lambda manifest: manifest["source"]["metadata"].__setitem__("sha256", "short"),
        lambda manifest: manifest["sync"].__setitem__("destructive_update", True),
    ],
)
def test_manifest_validation_rejects_contract_mutations(tmp_path, mutation):
    import copy

    manifest = copy.deepcopy(_manifest(tmp_path))
    mutation(manifest)
    with pytest.raises((ValueError, KeyError)):
        validate_integration_manifest(manifest)


def test_manifest_validation_rejects_non_mapping_generator_and_metadata(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["generator"] = None
    with pytest.raises(ValueError, match="generator identity"):
        validate_integration_manifest(manifest)

    manifest = _manifest(tmp_path)
    manifest["generator"]["version"] = 1
    with pytest.raises(ValueError, match="generator version"):
        validate_integration_manifest(manifest)

    manifest = _manifest(tmp_path)
    manifest["metadata"] = None
    with pytest.raises(ValueError, match="metadata source"):
        validate_integration_manifest(manifest)
