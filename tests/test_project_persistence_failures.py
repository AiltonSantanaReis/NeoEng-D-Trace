"""Failure and migration contracts for project persistence v1."""

from __future__ import annotations

import json

import pytest

from src.models.scene import Scene
from src.persistence.errors import (
    LegacyProjectMigrationError,
    ProjectFormatError,
    ProjectReadError,
    ProjectValidationError,
    UnsupportedProjectVersionError,
)


def _write_json(path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _valid_document():
    return {
        "format_id": "neoeng-d-trace-project",
        "schema_version": 1,
        "metadata": {
            "generator": "NeoEng-D-Trace",
            "app_version": "0.2.0",
        },
        "image": None,
        "layers": [
            {
                "id": "layer_default",
                "name": "Default",
                "visible": True,
                "locked": False,
            }
        ],
        "objects": [],
        "groups": [],
    }


def test_known_legacy_project_is_migrated_with_explicit_warnings(tmp_path):
    path = tmp_path / "legacy.json"
    _write_json(
        path,
        {
            "layers": [
                {
                    "id": "layer_default",
                    "name": "Default",
                    "visible": True,
                    "locked": False,
                }
            ],
            "objects": {
                "object-1": {
                    "polygon": [[0, 0], [10, 0], [0, 10]],
                    "layer_id": "layer_default",
                }
            },
            "groups": [
                {
                    "id": "group-1",
                    "name": "Group",
                    "visible": True,
                    "locked": False,
                    "members": ["object-1"],
                }
            ],
            "collisions": ["object-1"],
        },
    )

    scene = Scene()
    warnings = scene.load_project(str(path))

    assert warnings == (
        "legacy_project_migrated_to_schema_v1",
        "legacy_format_does_not_store_image_or_bezier_data",
        "legacy_collision_geometry_reconstructed_from_visual_polygon",
    )
    assert scene.collision_shapes["object-1"] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (0.0, 10.0),
    ]
    assert scene.objects["object-1"].beziers is None
    assert scene.image_path is None


@pytest.mark.parametrize("version", [0, 2, 999])
def test_unsupported_versions_are_rejected(tmp_path, version):
    path = tmp_path / "future.ndtproj"
    payload = _valid_document()
    payload["schema_version"] = version
    _write_json(path, payload)

    with pytest.raises(UnsupportedProjectVersionError):
        Scene().load_project(str(path))


def test_wrong_format_identifier_is_rejected(tmp_path):
    path = tmp_path / "wrong.ndtproj"
    payload = _valid_document()
    payload["format_id"] = "other"
    _write_json(path, payload)

    with pytest.raises(ProjectFormatError):
        Scene().load_project(str(path))


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"\xef\xbb\xbf{}",
        b"\xff",
        b'{"format_id":"neoeng-d-trace-project","schema_version":1,'
        b'"metadata":{"generator":"x","app_version":"1"},'
        b'"image":null,"layers":[],"objects":[],"groups":[],"x":NaN}',
    ],
)
def test_malformed_encoding_bom_and_non_finite_json_are_rejected(tmp_path, raw):
    path = tmp_path / "invalid.ndtproj"
    path.write_bytes(raw)

    with pytest.raises(ProjectFormatError):
        Scene().load_project(str(path))


def test_unknown_fields_and_wrong_types_are_rejected(tmp_path):
    unknown = tmp_path / "unknown.ndtproj"
    payload = _valid_document()
    payload["unexpected"] = True
    _write_json(unknown, payload)

    with pytest.raises(ProjectValidationError):
        Scene().load_project(str(unknown))

    wrong_type = tmp_path / "wrong-type.ndtproj"
    payload = _valid_document()
    payload["layers"][0]["visible"] = "true"
    _write_json(wrong_type, payload)

    with pytest.raises(ProjectValidationError):
        Scene().load_project(str(wrong_type))


def test_invalid_references_are_rejected_without_mutating_scene(tmp_path):
    path = tmp_path / "invalid-reference.ndtproj"
    payload = _valid_document()
    payload["objects"] = [
        {
            "id": "object-1",
            "layer_id": "missing",
            "polygon": [{"x": 0, "y": 0}],
            "collision": None,
            "beziers": None,
        }
    ]
    _write_json(path, payload)

    scene = Scene()
    scene.add_object(
        "preserved",
        [(0, 0), (10, 0), (0, 10)],
        "layer_default",
    )
    original_layers = scene.layers
    original_objects = scene.objects
    original_groups = scene.groups
    original_collisions = scene.collision_shapes

    with pytest.raises(ProjectValidationError):
        scene.load_project(str(path))

    assert scene.layers is original_layers
    assert scene.objects is original_objects
    assert scene.groups is original_groups
    assert scene.collision_shapes is original_collisions
    assert list(scene.objects) == ["preserved"]


def test_legacy_unknown_references_are_not_silently_dropped(tmp_path):
    path = tmp_path / "legacy-invalid.json"
    _write_json(
        path,
        {
            "layers": [],
            "objects": {},
            "groups": [],
            "collisions": ["missing"],
        },
    )

    with pytest.raises(LegacyProjectMigrationError):
        Scene().load_project(str(path))


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"layers": []},
        {
            "layers": [],
            "objects": {},
            "groups": [],
        },
    ],
)
def test_unversioned_json_requires_the_exact_known_legacy_root(tmp_path, payload):
    path = tmp_path / "ambiguous.json"
    _write_json(path, payload)

    with pytest.raises(LegacyProjectMigrationError):
        Scene().load_project(str(path))


def test_missing_file_is_reported_as_read_error(tmp_path):
    with pytest.raises(ProjectReadError):
        Scene().load_project(str(tmp_path / "missing.ndtproj"))


def test_duplicate_json_object_keys_are_rejected(tmp_path):
    path = tmp_path / "duplicate.ndtproj"
    path.write_text(
        '{"format_id":"neoeng-d-trace-project",'
        '"format_id":"neoeng-d-trace-project",'
        '"schema_version":1}',
        encoding="utf-8",
    )

    with pytest.raises(ProjectFormatError):
        Scene().load_project(str(path))


def test_invalid_in_memory_references_are_rejected_before_save(tmp_path):
    orphan = Scene()
    orphan.collision_shapes["missing"] = [(0.0, 0.0)]

    with pytest.raises(ProjectValidationError):
        orphan.save_project(str(tmp_path / "orphan.ndtproj"))

    mismatch = Scene()
    mismatch.add_object(
        "object-1",
        [(0, 0), (10, 0), (0, 10)],
        "layer_default",
    )
    mismatch.objects["object-1"].id = "other"

    with pytest.raises(ProjectValidationError):
        mismatch.save_project(str(tmp_path / "mismatch.ndtproj"))
