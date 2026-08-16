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
    "default": "ff055d3f625525d3495ca80805a4df0dcfa58482ec03b5d069f7cf74e64985a0",
    "unity": "a8042225b750d7b5314ea4ae1ad7a9be9a92a7fa32e947385e3e142e50f04cd0",
    "godot": "444d6cf73a429c918dad2997b5730c244d9d8b0046e059e1346ce75879b12611",
}
OBJECT_HASHES = {
    "generic": "cee13d76fc44dd6bb1c38a0c96fb23e76aa4f39b67c012b4013917b24df24abc",
    "unity": "0d45f5f7aa01bc463b014532893640f6b147590ad1108887a71471371f34db67",
    "godot": "43574483a34b38b74bd01e5bc1cef9cece2ec66ecf8ce38d1fc0f37eb257c204",
    "phaser": "09aa6d956028bd6ae8c632251eb9a64cdcd6e426eb8bedec630c1336321e5c9d",
}
SAVED_SCENE_HASHES = {
    "\n": "ff055d3f625525d3495ca80805a4df0dcfa58482ec03b5d069f7cf74e64985a0",
    "\r\n": "054873044a2ea83948a6c5620c1111f3b4f4bbc162a6eda97311ec1ecd920ee1",
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
