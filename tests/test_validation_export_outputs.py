from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from src.core.validation_events import (
    start_validation_session,
    stop_validation_session,
    validation_output_path,
)
from src.exporters.atlas_exporter import build_atlas
from src.exporters.gltf_exporter import export_object_to_gltf, export_scene_to_gltf
from src.exporters.json_exporter import export_metadata
from src.exporters.sprite_exporter import extract_masked_sprite, save_sprite
from src.models.scene import Scene


def _glb_is_valid(path: Path) -> bool:
    raw = path.read_bytes()
    return (
        len(raw) >= 12
        and raw[:4] == b"glTF"
        and int.from_bytes(raw[4:8], "little") == 2
        and int.from_bytes(raw[8:12], "little") == len(raw)
    )


def test_validation_sandbox_generates_real_export_outputs(tmp_path):
    log = tmp_path / "validation.jsonl"
    scene = Scene()
    scene.image = np.zeros((64, 64, 4), dtype=np.uint8)
    scene.image[:, :, 0] = 20
    scene.image[:, :, 1] = 100
    scene.image[:, :, 2] = 220
    scene.image[:, :, 3] = 255
    scene.add_object(
        "object/main",
        [(8, 8), (50, 8), (52, 40), (30, 55), (8, 40)],
    )
    scene.select_object("object/main")
    obj = scene.objects["object/main"]

    start_validation_session(log)
    try:
        sprite_path = validation_output_path("selected-sprite.png")
        metadata_path = validation_output_path("selected-generic-metadata.json")
        atlas_dir = validation_output_path("atlas", directory=True)
        scene_path = validation_output_path("scene.glb")
        object_path = validation_output_path("selected-object.glb")

        assert all(
            path is not None
            for path in (
                sprite_path,
                metadata_path,
                atlas_dir,
                scene_path,
                object_path,
            )
        )

        sprite = extract_masked_sprite(scene.image, obj.polygon, padding=4)
        save_sprite(sprite, str(sprite_path))
        export_metadata(
            "object/main",
            scene,
            str(metadata_path),
            profile="generic",
        )
        atlas_results = build_atlas(
            [("object/main", sprite)],
            str(atlas_dir),
            base_name="atlas",
        )
        assert export_scene_to_gltf(scene, str(scene_path)) is True
        assert export_object_to_gltf(
            "object/main", scene, str(object_path)
        ) is True

        assert Image.open(sprite_path).format == "PNG"
        assert json.loads(metadata_path.read_text(encoding="utf-8"))["id"] == "object/main"
        assert atlas_results
        for result in atlas_results:
            assert Image.open(result["atlas_path"]).format == "PNG"
            assert isinstance(
                json.loads(Path(result["json_path"]).read_text(encoding="utf-8")),
                list,
            )
        assert _glb_is_valid(scene_path)
        assert _glb_is_valid(object_path)
    finally:
        stop_validation_session(exit_code=0)


def test_validation_sandbox_is_disabled_in_normal_mode():
    assert validation_output_path("selected-sprite.png") is None
