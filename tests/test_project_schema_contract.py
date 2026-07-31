"""Contracts for the approved NeoEng-D-Trace project schema v1."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.core.app_identity import PROJECT_FORMAT_ID, PROJECT_FORMAT_VERSION
from src.persistence.project_schema import (
    PROJECT_FILE_EXTENSION,
    GroupRecord,
    ImageReferenceRecord,
    LayerRecord,
    PointRecord,
    ProjectDocumentV1,
    ProjectMetadataRecord,
    SceneObjectRecord,
)


def _document(**overrides):
    data = {
        "metadata": ProjectMetadataRecord(
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        "layers": [
            LayerRecord(
                id="layer_default",
                name="Default",
                visible=True,
                locked=False,
            )
        ],
        "objects": [],
        "groups": [],
    }
    data.update(overrides)
    return ProjectDocumentV1(**data)


def test_format_identity_and_extension_match_the_approved_adr():
    document = _document()

    assert PROJECT_FORMAT_ID == "neoeng-d-trace-project"
    assert PROJECT_FORMAT_VERSION == 1
    assert PROJECT_FILE_EXTENSION == ".ndtproj"
    assert document.format_id == PROJECT_FORMAT_ID
    assert document.schema_version == PROJECT_FORMAT_VERSION


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_coordinates_must_be_finite(value):
    with pytest.raises(ValidationError):
        PointRecord(x=value, y=0)


@pytest.mark.parametrize("value", [True, "1", None])
def test_coordinates_use_strict_numeric_types(value):
    with pytest.raises(ValidationError):
        PointRecord(x=value, y=0)


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        ProjectMetadataRecord(
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
            unexpected=True,
        )


def test_layer_default_is_required():
    with pytest.raises(ValidationError):
        _document(
            layers=[
                LayerRecord(
                    id="other",
                    name="Other",
                    visible=True,
                    locked=False,
                )
            ]
        )


def test_object_layer_reference_must_exist():
    item = SceneObjectRecord(
        id="object-1",
        layer_id="missing",
        polygon=[PointRecord(x=0, y=0)],
    )

    with pytest.raises(ValidationError):
        _document(objects=[item])


def test_group_members_must_be_unique_and_existing():
    item = SceneObjectRecord(
        id="object-1",
        layer_id="layer_default",
        polygon=[PointRecord(x=0, y=0)],
    )

    with pytest.raises(ValidationError):
        GroupRecord(
            id="group-1",
            name="Group",
            visible=True,
            locked=False,
            members=["object-1", "object-1"],
        )

    unknown = GroupRecord(
        id="group-1",
        name="Group",
        visible=True,
        locked=False,
        members=["missing"],
    )
    with pytest.raises(ValidationError):
        _document(objects=[item], groups=[unknown])


def test_duplicate_object_and_group_ids_are_rejected():
    item = SceneObjectRecord(
        id="object-1",
        layer_id="layer_default",
        polygon=[],
    )
    with pytest.raises(ValidationError):
        _document(objects=[item, item])

    first_group = GroupRecord(
        id="group-1",
        name="First",
        visible=True,
        locked=False,
        members=[],
    )
    second_group = GroupRecord(
        id="group-1",
        name="Second",
        visible=True,
        locked=False,
        members=[],
    )
    with pytest.raises(ValidationError):
        _document(groups=[first_group, second_group])


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("/absolute/image.png", "relative"),
        (r"C:\absolute\image.png", "relative"),
        ("relative/image.png", "absolute"),
    ],
)
def test_image_path_kind_must_match_path_syntax(path, kind):
    with pytest.raises(ValidationError):
        ImageReferenceRecord(
            path=path,
            path_kind=kind,
            sha256=None,
        )


@pytest.mark.parametrize(
    "path",
    [
        "../outside/image.png",
        r"..\outside\image.png",
        r"folder/..\outside/image.png",
        "folder/../image.png",
        "   ",
        "image\x00.png",
    ],
)
def test_relative_image_path_rejects_traversal_and_invalid_text(path):
    with pytest.raises(ValidationError):
        ImageReferenceRecord(
            path=path,
            path_kind="relative",
            sha256=None,
        )


def test_relative_image_path_accepts_internal_path():
    reference = ImageReferenceRecord(
        path="assets/source/image.png",
        path_kind="relative",
        sha256=None,
    )

    assert reference.path == "assets/source/image.png"
