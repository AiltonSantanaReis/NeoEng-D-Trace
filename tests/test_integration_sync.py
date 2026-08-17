from __future__ import annotations

import copy
from pathlib import Path

import pytest
from PIL import Image

from src.exporters.integration_manifest import build_integration_manifest
from src.exporters.integration_sync import (
    IntegrationPlanError,
    IntegrationSecurityError,
    _inside,
    apply_plan,
    manifest_payload_hash,
    plan_outputs,
    validate_manifest_sources,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene


def _manifest(tmp_path: Path) -> dict:
    source = tmp_path / "source.png"
    Image.new("RGBA", (4, 4), (1, 2, 3, 255)).save(source)
    scene = Scene()
    scene.add_object("hero", [(0, 0), (3, 0), (3, 3), (0, 3)])
    return build_integration_manifest(
        export_scene_metadata(scene),
        engine="godot",
        image_path=source,
        image_reference="assets/source.png",
    )


def test_dry_run_does_not_create_root_or_outputs(tmp_path):
    root = tmp_path / "NeoEngGenerated"
    plan = plan_outputs(root, {"hero.tscn": "generated"})

    assert plan.root == root
    assert plan.outputs[0].action == "CREATE"
    assert not root.exists()


def test_inside_rejects_destination_outside_root(tmp_path):
    root = tmp_path / "generated"
    outside = tmp_path / "outside" / "file.txt"

    assert not _inside(root, outside)


def test_plan_is_deterministic_and_reports_unchanged_content(tmp_path):
    root = tmp_path / "generated"
    root.mkdir()
    (root / "b.txt").write_text("same", encoding="utf-8")
    (root / "a.txt").write_text("old", encoding="utf-8")

    plan = plan_outputs(root, {"b.txt": "same", "a.txt": "new"})

    assert [item.relative_path for item in plan.outputs] == ["a.txt", "b.txt"]
    assert [item.action for item in plan.outputs] == ["UPDATE", "UNCHANGED"]
    assert [item.relative_path for item in plan.changed] == ["a.txt"]


@pytest.mark.parametrize(
    "path",
    [
        "",
        "../escape.txt",
        "nested/../../escape.txt",
        "/absolute.txt",
        "C:/escape.txt",
        "nested/",
    ],
)
def test_plan_rejects_unsafe_destinations(tmp_path, path):
    with pytest.raises(IntegrationSecurityError, match="relative and safe"):
        plan_outputs(tmp_path / "generated", {path: "x"})


def test_plan_rejects_symlink_escape(tmp_path):
    root = tmp_path / "generated"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(IntegrationSecurityError, match="symlink"):
        plan_outputs(root, {"link/escape.txt": "x"})


def test_plan_rejects_duplicate_normalized_destinations(tmp_path):
    with pytest.raises(IntegrationPlanError, match="duplicate output"):
        plan_outputs(
            tmp_path / "generated",
            {"nested/output.json": "one", r"nested\output.json": "two"},
        )


def test_plan_rejects_existing_file_as_generated_root(tmp_path):
    root = tmp_path / "generated"
    root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(IntegrationSecurityError, match="generated root"):
        plan_outputs(root, {"hero.tscn": "x"})


def test_plan_rejects_symlink_destination(tmp_path):
    root = tmp_path / "generated"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("protected", encoding="utf-8")
    link = root / "hero.tscn"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(IntegrationSecurityError, match="symlink"):
        plan_outputs(root, {"hero.tscn": "x"})


def test_apply_plan_commits_all_outputs_and_is_repeatable(tmp_path):
    root = tmp_path / "generated"
    outputs = {"hero.tscn": "one", "hero.json": "two"}
    plan = plan_outputs(root, outputs)
    apply_plan(plan, outputs)
    first = {name: (root / name).read_bytes() for name in outputs}

    repeat = plan_outputs(root, outputs)
    apply_plan(repeat, outputs)

    assert {name: (root / name).read_bytes() for name in outputs} == first
    assert not list(root.glob(".neoeng-*"))


def test_apply_plan_rejects_payload_drift_without_mutation(tmp_path):
    root = tmp_path / "generated"
    root.mkdir()
    destination = root / "hero.tscn"
    destination.write_text("old", encoding="utf-8")
    plan = plan_outputs(root, {"hero.tscn": "new"})

    with pytest.raises(IntegrationPlanError, match="payload changed"):
        apply_plan(plan, {"hero.tscn": "tampered"})

    assert destination.read_text(encoding="utf-8") == "old"
    assert not list(root.glob(".neoeng-*"))


def test_apply_plan_rejects_changed_output_set_without_mutation(tmp_path):
    root = tmp_path / "generated"
    plan = plan_outputs(root, {"hero.tscn": "new"})

    with pytest.raises(IntegrationPlanError, match="output set changed"):
        apply_plan(plan, {"hero.tscn": "new", "extra.json": "unexpected"})

    assert not root.exists()


def test_apply_plan_rolls_back_when_second_output_fails(tmp_path, monkeypatch):
    root = tmp_path / "generated"
    root.mkdir()
    first = root / "first.txt"
    second = root / "second.txt"
    first.write_text("old-one", encoding="utf-8")
    second.write_text("old-two", encoding="utf-8")
    outputs = {"first.txt": "new-one", "second.txt": "new-two"}
    plan = plan_outputs(root, outputs)

    from src.core import atomic_outputs

    original = atomic_outputs.AtomicOutputTransaction._replace

    def fail_second(transaction, source, destination):
        if Path(destination) == second:
            raise OSError("controlled second output failure")
        return original(transaction, source, destination)

    monkeypatch.setattr(atomic_outputs.AtomicOutputTransaction, "_replace", fail_second)
    with pytest.raises(OSError, match="controlled second output failure"):
        apply_plan(plan, outputs)

    assert first.read_text(encoding="utf-8") == "old-one"
    assert second.read_text(encoding="utf-8") == "old-two"
    assert not list(root.glob(".neoeng-*"))


def test_validate_manifest_sources_checks_actual_image_hash(tmp_path):
    manifest = _manifest(tmp_path)
    source = tmp_path / "source.png"
    validate_manifest_sources(manifest, image_path=source)
    source.write_bytes(source.read_bytes() + b"drift")

    with pytest.raises(IntegrationPlanError, match="source image hash"):
        validate_manifest_sources(manifest, image_path=source)


def test_validate_manifest_sources_rejects_atlas_hash_drift(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["schema_version"] = 2
    manifest["advanced"] = {
        "schema_version": 1,
        "coordinate_system": {
            "image_origin": "top-left",
            "polygon_origin": "sprite-top-left",
            "engine_y_axis": "up",
            "pixels_per_unit": {"godot": 1.0, "unity": 100.0},
        },
        "atlas": {
            "bleed": 0,
            "pages": [
                {
                    "id": "atlas_0",
                    "path": "atlas/atlas_0.png",
                    "sha256": "0" * 64,
                    "width": 4,
                    "height": 4,
                    "sprites": [
                        {
                            "id": "hero",
                            "rect": {"x": 0.0, "y": 0.0, "w": 3.0, "h": 3.0},
                            "packed_rect": {"x": 0.0, "y": 0.0, "w": 3.0, "h": 3.0},
                            "extrusion": 0,
                            "rotated": False,
                        }
                    ],
                }
            ],
        },
        "engine_properties": {
            "godot": {
                "texture_filter": "nearest",
                "texture_repeat": "disabled",
                "centered": True,
                "z_index": 0,
            },
            "unity": {
                "pixels_per_unit": 100.0,
                "filter_mode": "Point",
                "wrap_mode": "Clamp",
                "sorting_layer": "Default",
                "sorting_order": 0,
                "z_depth": 0.0,
            },
        },
    }
    with pytest.raises(ValueError):
        validate_manifest_sources(
            manifest,
            image_path=tmp_path / "source.png",
            atlas_paths={"atlas_0": tmp_path / "source.png"},
        )


def test_validate_manifest_sources_rejects_missing_atlas_path(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["schema_version"] = 2
    manifest["advanced"] = {
        "schema_version": 1,
        "coordinate_system": {
            "image_origin": "top-left",
            "polygon_origin": "sprite-top-left",
            "engine_y_axis": "up",
            "pixels_per_unit": {"godot": 1.0, "unity": 100.0},
        },
        "atlas": {
            "bleed": 0,
            "pages": [
                {
                    "id": "atlas_0",
                    "path": "atlas/atlas_0.png",
                    "sha256": "0" * 64,
                    "width": 4,
                    "height": 4,
                    "sprites": [
                        {
                            "id": "hero",
                            "rect": {"x": 0.0, "y": 0.0, "w": 3.0, "h": 3.0},
                            "packed_rect": {
                                "x": 0.0,
                                "y": 0.0,
                                "w": 3.0,
                                "h": 3.0,
                            },
                            "extrusion": 0,
                            "rotated": False,
                        }
                    ],
                }
            ],
        },
        "engine_properties": {
            "godot": {
                "texture_filter": "nearest",
                "texture_repeat": "disabled",
                "centered": True,
                "z_index": 0,
            },
            "unity": {
                "pixels_per_unit": 100.0,
                "filter_mode": "Point",
                "wrap_mode": "Clamp",
                "sorting_layer": "Default",
                "sorting_order": 0,
                "z_depth": 0.0,
            },
        },
    }

    with pytest.raises(IntegrationPlanError, match="atlas page path is missing"):
        validate_manifest_sources(manifest, image_path=tmp_path / "source.png")


def test_manifest_payload_hash_is_canonical_and_detects_mutation(tmp_path):
    manifest = _manifest(tmp_path)
    first = manifest_payload_hash(manifest)
    mutated = copy.deepcopy(manifest)
    mutated["metadata"]["sprites"][0]["id"] = "changed"

    assert first != manifest_payload_hash(mutated)


def test_manifest_payload_hash_rejects_missing_metadata(tmp_path):
    manifest = _manifest(tmp_path)
    manifest.pop("metadata")

    with pytest.raises(IntegrationPlanError, match="metadata is invalid"):
        manifest_payload_hash(manifest)
