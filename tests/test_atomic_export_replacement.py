from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from src.exporters import atlas_exporter, gltf_exporter, json_exporter, sprite_exporter
from src.models.scene import Scene


def _deny_destination_remove(monkeypatch, module, destinations):
    real_remove = module.os.remove
    blocked = {str(Path(path)) for path in destinations}

    def guarded_remove(path):
        assert str(Path(path)) not in blocked, (
            "Exporter pre-deleted a destination instead of using os.replace"
        )
        return real_remove(path)

    monkeypatch.setattr(module.os, "remove", guarded_remove)


def test_json_replaces_existing_destination_without_predelete(tmp_path, monkeypatch):
    destination = tmp_path / "metadata.json"
    destination.write_text("old", encoding="utf-8")
    _deny_destination_remove(monkeypatch, json_exporter, [destination])

    json_exporter.save_json_metadata({"value": 1}, str(destination))

    assert json.loads(destination.read_text(encoding="utf-8")) == {"value": 1}
    assert not list(tmp_path.glob("*.tmp"))


def test_sprite_replaces_existing_destination_without_predelete(tmp_path, monkeypatch):
    destination = tmp_path / "sprite.png"
    destination.write_bytes(b"old")
    _deny_destination_remove(monkeypatch, sprite_exporter, [destination])

    sprite_exporter.save_sprite(
        Image.new("RGBA", (4, 4), (255, 0, 0, 255)),
        str(destination),
    )

    assert Image.open(destination).format == "PNG"
    assert not list(tmp_path.glob("tmp_sprite_*"))


def test_atlas_replaces_existing_outputs_without_predelete(tmp_path, monkeypatch):
    atlas_path = tmp_path / "atlas.png"
    json_path = tmp_path / "atlas.json"
    atlas_path.write_bytes(b"old-image")
    json_path.write_text("old-json", encoding="utf-8")
    _deny_destination_remove(monkeypatch, atlas_exporter, [atlas_path, json_path])

    atlas_exporter.save_atlas(
        Image.new("RGBA", (8, 8), (0, 255, 0, 255)),
        [{"name": "item"}],
        str(atlas_path),
        str(json_path),
    )

    assert Image.open(atlas_path).format == "PNG"
    assert json.loads(json_path.read_text(encoding="utf-8")) == [{"name": "item"}]
    assert not list(tmp_path.glob("tmp_atlas_*"))


def test_gltf_replaces_existing_destination_without_predelete(tmp_path, monkeypatch):
    destination = tmp_path / "scene.glb"
    destination.write_bytes(b"old")
    _deny_destination_remove(monkeypatch, gltf_exporter, [destination])

    scene = Scene()
    scene.image = np.zeros((16, 16, 4), dtype=np.uint8)
    scene.add_object("object", [(0, 0), (10, 0), (10, 10), (0, 10)])

    assert gltf_exporter.export_scene_to_gltf(scene, str(destination)) is True
    raw = destination.read_bytes()
    assert raw[:4] == b"glTF"
    assert int.from_bytes(raw[4:8], "little") == 2
