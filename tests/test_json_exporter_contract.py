from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path

import pytest

from src.models.scene import Group, Layer, Scene

MODULE_NAME = "src.exporters.json_exporter"

SCENE_HASHES = {
    "default": "f5bd6958deb04add3b822968f7996c6d56cbc7a27c972db92da7606d772e7c70",
    "unity": "873db693a96cc7382f79f217f20d2395d2e3203625cc7c6b3d5af4a2e65d5948",
    "godot": "6927c420b750b1445c4d9c5369b24dda6e86e844fa75b9ec37cb9e0cf10841a2",
}
OBJECT_HASHES = {
    "generic": "000e8bfc730ff9f361b60a635a61ff301723d481ef17fd0d9491f0a13d2154dd",
    "unity": "709cd0cd249410e60258160ae6ac7bdb08bc66cfce446513e5ed0e41353a1051",
    "godot": "8a6e913089cd27240f6422d02c4184ac8123bf529a5df3489e6c0bcacf4c3f31",
    "phaser": "b49f06445f7295df44105b16aaef1b44a807c02844ac673a25fa54c1b67343ae",
}
SAVED_SCENE_HASHES = {
    "\n": "f5bd6958deb04add3b822968f7996c6d56cbc7a27c972db92da7606d772e7c70",
    "\r\n": "b42d94421d96aa9c94f567adea212130d236453cbc59644bd484bc9465dccd2c",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fixture_scene() -> Scene:
    scene = Scene()
    scene.layers.append(
        Layer(id="layer_fx", name="Efeitos Ágeis", visible=False, locked=True)
    )
    scene.add_object(
        "obj_player", [(10, 20), (30, 20), (30, 50), (10, 50)], layer_id="layer_fx"
    )
    scene.add_object(
        "obj_prop", [(100, 5), (112, 5), (112, 13), (100, 13)], layer_id="layer_default"
    )
    group = Group(id="group_main", name="Grupo Principal", visible=True, locked=False)
    group.members = ["obj_player"]
    scene.groups.append(group)
    return scene


def test_json_exporter_uses_single_src_implementation() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert module.__file__.replace("\\", "/").endswith("src/exporters/json_exporter.py")
    assert module.export_scene_metadata.__module__ == MODULE_NAME


@pytest.mark.parametrize("profile", ["default", "unity", "godot"])
def test_json_scene_metadata_contract_is_frozen(profile: str) -> None:
    module = importlib.import_module(MODULE_NAME)
    serialized = json.dumps(
        module.export_scene_metadata(_fixture_scene(), profile=profile),
        indent=2,
    ).encode("utf-8")
    assert _sha256(serialized) == SCENE_HASHES[profile]


@pytest.mark.parametrize("profile", ["generic", "unity", "godot", "phaser"])
def test_json_object_profile_contract_is_frozen(profile: str) -> None:
    module = importlib.import_module(MODULE_NAME)
    serialized = json.dumps(
        module.export_metadata(
            "obj_player",
            _fixture_scene(),
            "",
            profile=profile,
        ),
        indent=2,
    ).encode("utf-8")
    assert _sha256(serialized) == OBJECT_HASHES[profile]


def test_json_saved_json_bytes_and_atomic_replacement_contract_are_preserved(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    output = tmp_path / "nested" / "scene.json"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"old-content")

    module.save_json_metadata(
        module.export_scene_metadata(_fixture_scene()),
        str(output),
    )

    raw = output.read_bytes()
    expected_hash = SAVED_SCENE_HASHES[os.linesep]
    assert _sha256(raw) == expected_hash
    assert json.loads(raw.decode("utf-8"))["sprites"][0]["id"] == "obj_player"
    assert [path.name for path in output.parent.iterdir()] == ["scene.json"]


def test_json_errors_and_optional_path_contracts_are_preserved(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    scene = _fixture_scene()

    assert (
        module.export_metadata("obj_player", scene, "", profile="generic")["id"]
        == "obj_player"
    )
    with pytest.raises(ValueError, match="Object missing not found in scene"):
        module.export_metadata("missing", scene, "", profile="generic")
    with pytest.raises(ValueError, match="Unsupported export profile: unknown"):
        module.export_metadata(
            "obj_player",
            scene,
            str(tmp_path / "unknown.json"),
            profile="unknown",
        )
