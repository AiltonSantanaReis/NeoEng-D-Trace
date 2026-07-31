"""Lossless round-trip contracts for project persistence v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.models.scene import Scene
from src.persistence.project_io import load_project_document
from src.persistence.project_schema import PROJECT_FILE_EXTENSION


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _complete_scene(image_path: str) -> Scene:
    scene = Scene()
    second = scene.create_layer("Foreground")
    second.id = "layer_foreground"
    second.visible = False
    second.locked = True

    scene.add_object(
        "object-a",
        [(0, 0), (20, 0), (20, 20), (0, 20)],
        "layer_default",
    )
    scene.add_object(
        "object-b",
        [(1.5, 2.5), (11.5, 2.5), (11.5, 12.5)],
        "layer_foreground",
    )

    scene.collision_shapes["object-a"] = [
        (2, 2),
        (18, 2),
        (10, 17),
    ]
    scene.objects["object-b"].beziers = [
        ((1, 2), (3, 4), (5, 6), (7, 8)),
        ((7, 8), (9, 10), (11, 12), (13, 14)),
    ]

    group = scene.create_group("Pair")
    group.id = "group-pair"
    group.visible = False
    group.locked = True
    group.members = ["object-b", "object-a"]

    scene.image_path = image_path
    scene.selected_id = "object-b"
    return scene


def test_complete_scene_round_trip_preserves_persistent_state(tmp_path):
    image = tmp_path / "source image.png"
    image.write_bytes(b"controlled-image-bytes")

    path = tmp_path / f"complete{PROJECT_FILE_EXTENSION}"
    original = _complete_scene(image.name)
    original.save_project(str(path))

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["format_id"] == "neoeng-d-trace-project"
    assert raw["schema_version"] == 1
    assert raw["image"]["path"] == image.name
    assert raw["image"]["path_kind"] == "relative"
    assert raw["image"]["sha256"] == _sha256(image)
    assert "selected_id" not in raw
    assert "cmd" not in raw
    assert "auto_repair" not in raw

    loaded = Scene()
    loaded.selected_id = "transient-selection"
    warnings = loaded.load_project(str(path))

    assert warnings == ()
    assert loaded.image is None
    assert loaded.image_path == image.name
    assert loaded.selected_id is None

    assert [layer.id for layer in loaded.layers] == [
        "layer_default",
        "layer_foreground",
    ]
    assert loaded.layers[1].visible is False
    assert loaded.layers[1].locked is True

    assert list(loaded.objects) == ["object-a", "object-b"]
    assert loaded.objects["object-a"].polygon == [
        (0, 0),
        (20, 0),
        (20, 20),
        (0, 20),
    ]
    assert loaded.objects["object-b"].polygon == [
        (1.5, 2.5),
        (11.5, 2.5),
        (11.5, 12.5),
    ]
    assert loaded.collision_shapes["object-a"] == [
        (2.0, 2.0),
        (18.0, 2.0),
        (10.0, 17.0),
    ]
    assert loaded.objects["object-b"].beziers == [
        ((1, 2), (3, 4), (5, 6), (7, 8)),
        ((7, 8), (9, 10), (11, 12), (13, 14)),
    ]

    assert [group.id for group in loaded.groups] == ["group-pair"]
    assert loaded.groups[0].members == ["object-b", "object-a"]


def test_repeated_saves_and_save_load_save_are_byte_identical(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"image")

    first = tmp_path / "first.ndtproj"
    second = tmp_path / "second.ndtproj"
    third = tmp_path / "third.ndtproj"

    scene = _complete_scene(str(image))
    scene.save_project(str(first))
    scene.save_project(str(second))

    reloaded = Scene()
    reloaded.load_project(str(first))
    reloaded.save_project(str(third))

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() == third.read_bytes()


def test_image_hash_is_preserved_when_external_image_is_missing_or_changed(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"original-image")
    first = tmp_path / "first.ndtproj"
    missing_save = tmp_path / "missing-save.ndtproj"
    changed_save = tmp_path / "changed-save.ndtproj"

    original = _complete_scene(image.name)
    original.save_project(str(first))
    expected = json.loads(first.read_text(encoding="utf-8"))["image"]["sha256"]

    loaded = Scene()
    loaded.load_project(str(first))
    assert loaded.image_path_kind == "relative"
    assert loaded.image_sha256 == expected

    image.unlink()
    loaded.save_project(str(missing_save))
    assert missing_save.read_bytes() == first.read_bytes()

    image.write_bytes(b"changed-image")
    loaded.save_project(str(changed_save))
    assert changed_save.read_bytes() == first.read_bytes()


def test_explicitly_absent_image_hash_remains_absent_after_round_trip(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"available-image")
    first = tmp_path / "first.ndtproj"
    second = tmp_path / "second.ndtproj"

    scene = _complete_scene(image.name)
    scene.save_project(str(first))
    payload = json.loads(first.read_text(encoding="utf-8"))
    payload["image"]["sha256"] = None
    first.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    loaded = Scene()
    loaded.load_project(str(first))
    assert loaded.image_sha256 is None
    assert loaded._image_reference_loaded is True

    loaded.save_project(str(second))
    assert second.read_bytes() == first.read_bytes()


def test_loading_a_new_image_discards_the_previous_reference_hash(tmp_path):
    first_image = tmp_path / "first.png"
    first_image.write_bytes(b"first")
    project = tmp_path / "project.ndtproj"

    original = _complete_scene(first_image.name)
    original.save_project(str(project))

    loaded = Scene()
    loaded.load_project(str(project))
    previous_hash = loaded.image_sha256

    second_image = tmp_path / "second.png"
    second_image.write_bytes(b"second")
    loaded.load_image(object(), second_image.name)
    assert loaded.image_path_kind is None
    assert loaded.image_sha256 is None
    assert loaded._image_reference_loaded is False

    replacement = tmp_path / "replacement.ndtproj"
    loaded.save_project(str(replacement))
    new_hash = json.loads(replacement.read_text(encoding="utf-8"))["image"]["sha256"]
    assert new_hash != previous_hash
    assert new_hash == _sha256(second_image)


def test_empty_project_round_trip_is_valid(tmp_path):
    path = tmp_path / "empty.ndtproj"

    Scene().save_project(str(path))
    loaded = load_project_document(path)

    assert loaded.migrated_from_legacy is False
    assert loaded.warnings == ()
    assert [layer.id for layer in loaded.document.layers] == ["layer_default"]
    assert loaded.document.objects == []
    assert loaded.document.groups == []
