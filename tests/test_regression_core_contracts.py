import json

import pytest

from src.exporters.json_exporter import export_metadata
from src.models.scene import Scene
from src.physics.sat2d import polygon_edges, project, sat_polygon_vs_polygon


@pytest.fixture()
def square_scene():
    scene = Scene()
    scene.add_object(
        "obj1",
        [(10, 10), (50, 10), (50, 50), (10, 50)],
    )
    return scene


@pytest.mark.parametrize(
    ("profile", "required_keys"),
    [
        ("unity", {"name", "rect", "pivot", "border"}),
        ("godot", {"name", "rect", "offset"}),
        (
            "phaser",
            {
                "filename",
                "frame",
                "rotated",
                "trimmed",
                "spriteSourceSize",
                "sourceSize",
            },
        ),
    ],
)
def test_export_metadata_dispatches_engine_profile(
    tmp_path, square_scene, profile, required_keys
):
    output = tmp_path / f"{profile}.json"

    metadata = export_metadata(
        "obj1", square_scene, str(output), profile=profile
    )

    assert required_keys.issubset(metadata)
    assert json.loads(output.read_text(encoding="utf-8")) == metadata


def test_export_metadata_rejects_unknown_profile(tmp_path, square_scene):
    with pytest.raises(ValueError, match="Unsupported export profile"):
        export_metadata(
            "obj1",
            square_scene,
            str(tmp_path / "unknown.json"),
            profile="unknown",
        )


def test_sat_legacy_projection_and_edges_are_available():
    rectangle = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]

    assert project([], (1.0, 0.0)) == (0.0, 0.0)
    assert project(rectangle, (1.0, 0.0)) == (0.0, 2.0)
    assert polygon_edges(rectangle) == [
        (2.0, 0.0),
        (0.0, 1.0),
        (-2.0, 0.0),
        (0.0, -1.0),
    ]


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ([], []),
        (
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
            [],
        ),
        ([(0.0, 0.0)], [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]),
    ],
)
def test_sat_incomplete_geometry_is_non_colliding(first, second):
    assert sat_polygon_vs_polygon(first, second) == (False, None)
