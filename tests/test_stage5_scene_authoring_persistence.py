"""Positive and negative tests for professional scene Stage 5 contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.exporters.scene_authoring_export import (
    SceneAuthoringExportError,
    build_scene_authoring_export,
    save_scene_authoring_export,
    serialize_scene_authoring_export,
    validate_scene_authoring_export,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import (
    SceneAuthoringAssetError,
    SceneAuthoringFormatError,
    SceneAuthoringReadError,
    SceneAuthoringValidationError,
    SceneAuthoringWriteError,
    load_scene_authoring,
    load_scene_authoring_v2,
    save_scene_authoring,
    scene_authoring_sha256,
    serialize_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)


def _document(tmp_path: Path) -> tuple[SceneAuthoringDocumentV2, Path]:
    asset = tmp_path / "assets" / "hero.bin"
    asset.parent.mkdir()
    asset.write_bytes(b"real asset bytes")
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    v1 = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Stage 5 fixture", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[
            AssetReferenceRecord(id="hero_asset", path="assets/hero.bin", sha256=digest)
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero",
                asset_id="hero_asset",
                layer_id="foreground",
                transform=SceneTransformRecord(
                    position=Point3Record(x=10.0, y=20.0, z=3.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=15.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=1.0),
                    flip_x=True,
                ),
            )
        ],
        groups=[],
    )
    return (
        upgrade_scene_authoring_document(v1).model_copy(
            update={
                "parallax_layers": [
                    SceneParallaxLayerRecord(
                        layer_id="foreground",
                        depth=0.2,
                        translation_strength=0.8,
                        zoom_strength=0.9,
                    )
                ]
            }
        ),
        asset,
    )


def test_v2_save_load_is_deterministic_and_verifies_real_asset(tmp_path: Path) -> None:
    document, _ = _document(tmp_path)
    path = tmp_path / "scene.ndtscene.json"

    save_scene_authoring(document, path)
    first = path.read_bytes()
    loaded = load_scene_authoring_v2(path)
    save_scene_authoring(loaded, path)

    assert loaded == document
    assert path.read_bytes() == first
    assert hashlib.sha256(first).hexdigest() == scene_authoring_sha256(document)
    assert serialize_scene_authoring(document) == first


def _as_v1(document: SceneAuthoringDocumentV2) -> SceneAuthoringDocumentV1:
    data = document.model_dump()
    data["schema_version"] = 1
    for field in ("camera", "parallax_layers", "sockets"):
        data.pop(field)
    return SceneAuthoringDocumentV1.model_validate(data, strict=True)


def test_v1_roundtrip_is_preserved_and_v2_upgrade_is_explicit(tmp_path: Path) -> None:
    document, _ = _document(tmp_path)
    v1 = _as_v1(document)
    path = tmp_path / "legacy.ndtscene.json"
    save_scene_authoring(v1, path)

    assert isinstance(load_scene_authoring(path), SceneAuthoringDocumentV1)
    with pytest.raises(SceneAuthoringValidationError, match="explicit upgrade"):
        load_scene_authoring_v2(path)


def test_asset_hash_drift_is_rejected_without_mutating_the_document(
    tmp_path: Path,
) -> None:
    document, asset = _document(tmp_path)
    path = tmp_path / "scene.ndtscene.json"
    save_scene_authoring(document, path)
    asset.write_bytes(b"tampered asset bytes")

    with pytest.raises(SceneAuthoringAssetError, match="asset hash"):
        load_scene_authoring(path)


@pytest.mark.parametrize(
    "raw, error",
    [
        (b"\xef\xbb\xbf{}", SceneAuthoringFormatError),
        (b'{"format_id": 1, "format_id": 2}', SceneAuthoringFormatError),
        (b"not-json", SceneAuthoringFormatError),
    ],
)
def test_scene_reader_rejects_unsafe_json_bytes(
    tmp_path: Path, raw: bytes, error: type[Exception]
) -> None:
    path = tmp_path / "invalid.ndtscene.json"
    path.write_bytes(raw)
    with pytest.raises(error):
        load_scene_authoring(path, verify_assets=False)


def test_scene_save_rolls_back_existing_destination_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document, _ = _document(tmp_path)
    path = tmp_path / "scene.ndtscene.json"
    path.write_bytes(b"old scene")

    from src.core import atomic_outputs

    original = atomic_outputs.AtomicOutputTransaction._replace

    def fail(_transaction: object, _destination_source: str, _destination: str) -> None:
        raise OSError("controlled scene replacement failure")

    monkeypatch.setattr(atomic_outputs.AtomicOutputTransaction, "_replace", fail)
    with pytest.raises(
        SceneAuthoringWriteError, match="controlled scene replacement failure"
    ):
        save_scene_authoring(document, path)
    assert path.read_bytes() == b"old scene"
    assert not list(tmp_path.glob(".neoeng-*"))
    monkeypatch.setattr(atomic_outputs.AtomicOutputTransaction, "_replace", original)


@pytest.mark.parametrize("target", ["generic", "godot", "unity"])
def test_target_exports_are_deterministic_and_complete(
    tmp_path: Path, target: str
) -> None:
    document, _ = _document(tmp_path)
    first = serialize_scene_authoring_export(
        document, target=target  # type: ignore[arg-type]
    )
    second = serialize_scene_authoring_export(
        document, target=target  # type: ignore[arg-type]
    )
    payload = json.loads(first)

    assert first == second
    assert payload["target"] == target
    assert payload["source"]["sha256"] == scene_authoring_sha256(document)
    assert payload["scene"]["objects"][0]["id"] == "hero"
    assert payload["scene"]["sockets"] == []
    validate_scene_authoring_export(payload)


def test_export_rejects_v1_and_hash_or_capability_drift(tmp_path: Path) -> None:
    document, _ = _document(tmp_path)
    v1 = _as_v1(document)
    with pytest.raises(SceneAuthoringExportError, match="schema V2"):
        build_scene_authoring_export(v1, target="godot")  # type: ignore[arg-type]

    payload = build_scene_authoring_export(document, target="godot")
    mutated = copy.deepcopy(payload)
    mutated["source"]["sha256"] = "f" * 64
    with pytest.raises(SceneAuthoringExportError, match="source hash"):
        validate_scene_authoring_export(mutated)

    mutated = copy.deepcopy(payload)
    mutated["capabilities"]["unsupported"].append("objects")
    with pytest.raises(SceneAuthoringExportError, match="capabilit"):
        validate_scene_authoring_export(mutated)


@pytest.mark.parametrize(
    "raw, error",
    [
        (b'{"number": NaN}', SceneAuthoringFormatError),
        (b"\\xff", SceneAuthoringFormatError),
        (b"[]", SceneAuthoringFormatError),
    ],
)
def test_scene_reader_rejects_nonfinite_invalid_utf8_and_non_object(
    tmp_path: Path, raw: bytes, error: type[Exception]
) -> None:
    path = tmp_path / "unsafe.ndtscene.json"
    path.write_bytes(raw)
    with pytest.raises(error):
        load_scene_authoring(path, verify_assets=False)


def test_scene_reader_rejects_missing_directory_and_oversized_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(SceneAuthoringReadError, match="not found"):
        load_scene_authoring(tmp_path / "missing.ndtscene.json", verify_assets=False)

    directory = tmp_path / "scene-directory"
    directory.mkdir()
    with pytest.raises(SceneAuthoringReadError, match="not a file"):
        load_scene_authoring(directory, verify_assets=False)

    oversized = tmp_path / "oversized.ndtscene.json"
    oversized.write_bytes(b"{}")
    monkeypatch.setattr("src.persistence.scene_authoring_io.MAX_PROJECT_FILE_BYTES", 1)
    with pytest.raises(SceneAuthoringReadError, match="exceeds"):
        load_scene_authoring(oversized, verify_assets=False)


def test_asset_paths_reject_escape_and_missing_asset(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from src.persistence.scene_authoring_io import _asset_path, verify_scene_assets

    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(SceneAuthoringAssetError, match="escapes"):
        _asset_path(
            tmp_path / "scene.ndtscene.json",
            SimpleNamespace(path="../outside.bin"),
        )

    document, _ = _document(tmp_path)

    missing = document.model_copy(
        update={
            "assets": [
                AssetReferenceRecord(
                    id="missing",
                    path="assets/missing.bin",
                    sha256="a" * 64,
                )
            ]
        }
    )
    with pytest.raises(SceneAuthoringAssetError, match="not found"):
        verify_scene_assets(missing, tmp_path / "scene.ndtscene.json")


def test_scene_and_export_save_reject_invalid_destinations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document, _ = _document(tmp_path)
    with pytest.raises(SceneAuthoringWriteError, match="does not exist"):
        save_scene_authoring(document, tmp_path / "missing" / "scene.json")
    with pytest.raises(SceneAuthoringWriteError, match="directory"):
        save_scene_authoring(document, tmp_path)

    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    with pytest.raises(SceneAuthoringExportError, match="does not exist"):
        save_scene_authoring_export(
            document, export_dir / "missing" / "scene.json", target="generic"
        )
    with pytest.raises(SceneAuthoringExportError, match="directory"):
        save_scene_authoring_export(document, export_dir, target="generic")

    monkeypatch.setattr(
        "src.exporters.scene_authoring_export.AtomicOutputTransaction._replace",
        lambda *_args: (_ for _ in ()).throw(OSError("controlled export failure")),
    )
    with pytest.raises(SceneAuthoringExportError, match="controlled export failure"):
        save_scene_authoring_export(
            document, export_dir / "scene.json", target="generic"
        )


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda p: p.pop("scene"), "keys do not match"),
        (lambda p: p.update(format_id="wrong"), "unsupported scene export format"),
        (lambda p: p.update(schema_version=99), "unsupported scene export version"),
        (lambda p: p.update(target="unsupported"), "unsupported scene export target"),
        (lambda p: p.update(generator={}), "generator is invalid"),
        (lambda p: p["source"].update(sha256="x"), "lowercase SHA-256"),
        (lambda p: p["source"].update(schema_version=1), "source binding is invalid"),
        (
            lambda p: p["coordinate_mapping"].update(position_y_sign=0),
            "coordinate mapping",
        ),
        (lambda p: p["capabilities"].update(supported=[1]), "capabilities are invalid"),
        (lambda p: p.update(scene={}), "scene export document is invalid"),
        (
            lambda p: p["coordinate_mapping"].update(target_origin="drift"),
            "coordinate mapping drifted",
        ),
    ],
)
def test_export_validator_rejects_structural_and_mapping_drift(
    tmp_path: Path, mutation: object, message: str
) -> None:
    document, _ = _document(tmp_path)
    payload = build_scene_authoring_export(document, target="godot")
    mutated = copy.deepcopy(payload)
    mutation(mutated)  # type: ignore[operator]
    with pytest.raises(SceneAuthoringExportError, match=message):
        validate_scene_authoring_export(mutated)


def test_export_validator_rejects_generator_identity_capability_and_scene_hash_drift(
    tmp_path: Path,
) -> None:
    document, _ = _document(tmp_path)
    payload = build_scene_authoring_export(document, target="godot")
    cases = [
        (lambda p: p["generator"].update(id="other"), "generator identity"),
        (
            lambda p: p["capabilities"]["supported"].__setitem__(0, "changed"),
            "capability declaration",
        ),
        (
            lambda p: p["scene"]["metadata"].update(name="changed"),
            "source hash does not match",
        ),
    ]
    for mutation, message in cases:
        mutated = copy.deepcopy(payload)
        mutation(mutated)
        with pytest.raises(SceneAuthoringExportError, match=message):
            validate_scene_authoring_export(mutated)
