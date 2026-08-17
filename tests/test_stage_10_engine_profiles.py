from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from src.exporters import atlas_exporter
from src.exporters.json_exporter import export_metadata, export_scene_metadata
from src.exporters.profiles.godot import format_metadata as format_godot
from src.exporters.profiles.unity import format_metadata as format_unity
from src.models.scene import Scene
from tools.validate_engine_exports import (
    UNITY_GLTF_PACKAGE,
    _add_unity_package,
    _prepare_godot,
    _prepare_unity,
    _write_fixture,
)


def _scene() -> Scene:
    scene = Scene()
    scene.add_object(
        "probe",
        [(100, 50), (140, 50), (140, 70), (100, 70)],
    )
    scene.collision_shapes["probe"] = [
        (100, 50),
        (140, 50),
        (140, 70),
        (100, 70),
    ]
    return scene


def test_godot_offset_uses_local_pivot_and_correct_direction() -> None:
    metadata = format_godot(
        {
            "id": "probe",
            "rect": {"x": 100, "y": 50, "w": 40, "h": 20},
            "pivot": {"x": 10, "y": 5},
        }
    )

    assert metadata["offset"] == {"x": 10.0, "y": 5.0}
    assert metadata["rect"] == {"x": 100.0, "y": 50.0, "w": 40.0, "h": 20.0}


def test_scene_profiles_use_the_same_engine_formatters() -> None:
    scene = _scene()

    godot_sprite = export_scene_metadata(scene, "godot")["sprites"][0]
    unity_sprite = export_scene_metadata(scene, "unity")["sprites"][0]

    assert godot_sprite["schema"] == "neoeng-d-trace-godot-sprite"
    assert godot_sprite["offset"] == {"x": 0.0, "y": 0.0}
    assert unity_sprite["schema"] == "neoeng-d-trace-unity-sprite"
    assert unity_sprite["pivot"] == {"x": 0.5, "y": 0.5}
    assert godot_sprite["collision"]["shape_type"] == "polygon"
    assert unity_sprite["collision"]["shape_type"] == "polygon"


def test_compound_collision_is_preserved_by_unity_profile() -> None:
    scene = _scene()
    scene.collision_parts["probe"] = [
        [(100, 50), (120, 50), (120, 70), (100, 70)],
        [(120, 50), (140, 50), (140, 70), (120, 70)],
    ]
    metadata = export_scene_metadata(scene, "unity")["sprites"][0]
    collision = metadata["collision"]
    assert collision["shape_type"] == "compound"
    assert collision["coordinate_space"] == "image"
    assert len(collision["parts"]) == 2
    assert collision["parts"][1][0] == [120.0, 50.0]


def test_custom_scene_pivot_is_exported_consistently_by_all_profiles() -> None:
    scene = _scene()
    scene.objects["probe"].set_pivot(0.0, 1.0)

    generic = export_scene_metadata(scene)["sprites"][0]
    godot = export_scene_metadata(scene, "godot")["sprites"][0]
    unity = export_scene_metadata(scene, "unity")["sprites"][0]
    phaser = export_scene_metadata(scene, "phaser")["sprites"][0]

    assert generic["pivot"] == {"x": 0.0, "y": 20.0}
    assert generic["pivot_normalized"] == {"x": 0.0, "y": 1.0}
    assert godot["pivot"] == generic["pivot"]
    assert godot["offset"] == {"x": 20.0, "y": -10.0}
    assert unity["pivot"] == {"x": 0.0, "y": 1.0}
    assert phaser["pivot"] == {"x": 0.0, "y": 1.0}
    assert phaser["pivotPixels"] == {"x": 0.0, "y": 20.0}


@pytest.mark.parametrize("profile", ["godot", "unity"])
def test_object_and_scene_profiles_share_schema(profile: str) -> None:
    scene = _scene()

    object_metadata = export_metadata("probe", scene, "", profile)
    scene_metadata = export_scene_metadata(scene, profile)["sprites"][0]

    assert object_metadata["schema"] == scene_metadata["schema"]
    assert object_metadata["schema_version"] == 1
    assert scene_metadata["schema_version"] == 1
    assert object_metadata["pivot"] == scene_metadata["pivot"]


@pytest.mark.parametrize("formatter", [format_godot, format_unity])
@pytest.mark.parametrize(
    "metadata",
    [
        {"rect": {"x": 0, "y": 0, "w": 0, "h": 10}},
        {"rect": {"x": 0, "y": 0, "w": 10, "h": float("nan")}},
        {
            "rect": {"x": 0, "y": 0, "w": 10, "h": 10},
            "pivot": [1],
        },
        {
            "rect": {"x": 0, "y": 0, "w": 10, "h": 10},
            "pivot": {"x": True, "y": 5},
        },
    ],
)
def test_profiles_reject_invalid_geometry(formatter, metadata) -> None:
    with pytest.raises(ValueError):
        formatter(metadata)


def _fail_second_atlas_commit(monkeypatch, json_path: Path) -> None:
    real_replace = atlas_exporter.os.replace
    failed = False

    def controlled_replace(source, destination):
        nonlocal failed
        if Path(destination) == json_path and not failed:
            failed = True
            raise OSError("controlled second-file failure")
        return real_replace(source, destination)

    monkeypatch.setattr(atlas_exporter.os, "replace", controlled_replace)


def test_atlas_transaction_restores_existing_output_set(tmp_path, monkeypatch) -> None:
    atlas_path = tmp_path / "atlas.png"
    json_path = tmp_path / "atlas.json"
    atlas_path.write_bytes(b"previous-image")
    json_path.write_bytes(b"previous-json")
    _fail_second_atlas_commit(monkeypatch, json_path)

    with pytest.raises(OSError, match="controlled second-file failure"):
        atlas_exporter.save_atlas(
            Image.new("RGBA", (8, 8), (10, 20, 30, 255)),
            [{"name": "probe"}],
            str(atlas_path),
            str(json_path),
        )

    assert atlas_path.read_bytes() == b"previous-image"
    assert json_path.read_bytes() == b"previous-json"
    assert not list(tmp_path.glob("tmp_atlas_*"))


def test_atlas_transaction_removes_new_partial_output(tmp_path, monkeypatch) -> None:
    atlas_path = tmp_path / "atlas.png"
    json_path = tmp_path / "atlas.json"
    _fail_second_atlas_commit(monkeypatch, json_path)

    with pytest.raises(OSError, match="controlled second-file failure"):
        atlas_exporter.save_atlas(
            Image.new("RGBA", (8, 8), (10, 20, 30, 255)),
            [{"name": "probe"}],
            str(atlas_path),
            str(json_path),
        )

    assert not atlas_path.exists()
    assert not json_path.exists()
    assert not list(tmp_path.glob("tmp_atlas_*"))


def test_godot_harness_prepares_real_exporter_outputs(tmp_path) -> None:
    files = _prepare_godot(tmp_path)
    metadata = json.loads(files["metadata"].read_text(encoding="utf-8"))

    assert metadata["schema"] == "neoeng-d-trace-godot-sprite"
    assert metadata["name"] == "sprite_ação"
    assert metadata["collision"]["shape_type"] == "polygon"
    assert files["image"].read_bytes().startswith(b"\x89PNG")
    assert files["glb"].read_bytes().startswith(b"glTF")
    assert (tmp_path / "validate.gd").is_file()
    assert (tmp_path / "project.godot").is_file()


def test_unity_harness_prepares_real_outputs_and_pinned_package(tmp_path) -> None:
    project = tmp_path / "unity-project"
    packages = project / "Packages"
    packages.mkdir(parents=True)
    (packages / "manifest.json").write_text('{"dependencies": {}}', encoding="utf-8")

    files = _prepare_unity(project)
    _add_unity_package(project, UNITY_GLTF_PACKAGE)
    metadata = json.loads(files["metadata"].read_text(encoding="utf-8"))
    manifest = json.loads((packages / "manifest.json").read_text(encoding="utf-8"))

    assert metadata["schema"] == "neoeng-d-trace-unity-sprite"
    assert metadata["name"] == "sprite_ação"
    assert metadata["pivot"] == {"x": 0.5, "y": 0.5}
    assert files["image"].read_bytes().startswith(b"\x89PNG")
    assert files["glb"].read_bytes().startswith(b"glTF")
    assert manifest["dependencies"]["com.unity.cloud.gltfast"] == "6.19.0"
    assert (project / "Assets" / "Editor" / "EngineExportValidator.cs").is_file()


@pytest.mark.parametrize("profile", ["godot", "unity"])
def test_external_engine_fixture_is_copied_without_regeneration(tmp_path, profile):
    source = tmp_path / "release"
    generated = _write_fixture(source, profile)
    sprite = json.loads(generated["metadata"].read_text(encoding="utf-8"))
    generated["metadata"].write_text(
        json.dumps({"profile": profile, "sprites": [sprite]}, ensure_ascii=False),
        encoding="utf-8",
    )
    target = tmp_path / "engine"

    copied = _write_fixture(target, profile, fixture_dir=source)

    assert copied["image"].read_bytes() == generated["image"].read_bytes()
    assert copied["glb"].read_bytes() == generated["glb"].read_bytes()
    assert json.loads(copied["metadata"].read_text(encoding="utf-8"))["sprites"][0][
        "schema"
    ].endswith(f"{profile}-sprite")


def test_atlas_transaction_cleans_failed_backup_preparation(
    tmp_path, monkeypatch
) -> None:
    atlas_path = tmp_path / "atlas.png"
    json_path = tmp_path / "atlas.json"
    atlas_path.write_bytes(b"previous-image")
    json_path.write_bytes(b"previous-json")

    def fail_copy(*_args, **_kwargs):
        raise OSError("controlled backup failure")

    monkeypatch.setattr(atlas_exporter.shutil, "copy2", fail_copy)

    with pytest.raises(OSError, match="controlled backup failure"):
        atlas_exporter.save_atlas(
            Image.new("RGBA", (8, 8), (10, 20, 30, 255)),
            [{"name": "probe"}],
            str(atlas_path),
            str(json_path),
        )

    assert atlas_path.read_bytes() == b"previous-image"
    assert json_path.read_bytes() == b"previous-json"
    assert not list(tmp_path.glob("tmp_atlas_*"))
