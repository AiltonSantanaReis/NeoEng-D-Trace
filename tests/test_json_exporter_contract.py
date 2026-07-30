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
    "default": "71a33f0ae7d4b95dc8b673c8246f9952d2bb540633c2abf6fa9ac8745065e86c",
    "unity": "6863285c913a69f1c7373d575798147fd6bb6b682327b8a1e6ccab95165aee4e",
    "godot": "71a33f0ae7d4b95dc8b673c8246f9952d2bb540633c2abf6fa9ac8745065e86c",
}
OBJECT_HASHES = {
    "generic": "90fea459a1df99b750870082db5ff518a49f19a9d0f17519e2de70327b0468fa",
    "unity": "ed3517aa8bd71a24658dff8340d6422054f7c5099f529823e25948ae34e9a387",
    "godot": "ca90b14c50f53ab3912f6977b2008c777bdceb6bc2818784f2a1d61297f3d37c",
    "phaser": "b49f06445f7295df44105b16aaef1b44a807c02844ac673a25fa54c1b67343ae",
}
SAVED_SCENE_HASHES = {
    "\n": "71a33f0ae7d4b95dc8b673c8246f9952d2bb540633c2abf6fa9ac8745065e86c",
    "\r\n": "62b804b741b0e653d4680ffd2e6998637d53a4c53ff7f455a87a12b12d56d3cb",
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
