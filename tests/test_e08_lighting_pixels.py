from __future__ import annotations

from src.core.scene_lighting import (
    SceneLightingMaterial,
    SceneLightingSettings,
    ScenePointLight,
    shade_color,
)
from src.persistence.project_schema import Point3Record
from src.persistence.scene_authoring_schema import SceneLightSocketRecord


def test_zero_intensity_is_observable_and_deterministic() -> None:
    material = SceneLightingMaterial(albedo=(1.0, 0.5, 0.25))
    settings = SceneLightingSettings(
        ambient_intensity=0.0,
        lights=(ScenePointLight("key", (10.0, 0.0), intensity=0.0),),
    )
    first = shade_color((0.0, 0.0), material, settings)
    second = shade_color((0.0, 0.0), material, settings)

    assert first == second == ((0.0, 0.0, 0.0), 1.0, ())


def test_normal_map_perturbation_changes_lit_pixels() -> None:
    settings = SceneLightingSettings(
        ambient_intensity=0.0,
        lights=(ScenePointLight("key", (0.0, 100.0), intensity=1.0, radius=200.0),),
    )
    flat, _, _ = shade_color(
        (0.0, 0.0), SceneLightingMaterial(albedo=(1.0, 1.0, 1.0)), settings
    )
    tilted, _, _ = shade_color(
        (0.0, 0.0),
        SceneLightingMaterial(albedo=(1.0, 1.0, 1.0), normal_xy=(0.8, 0.0)),
        settings,
    )

    assert flat != tilted
    assert flat[0] > tilted[0]


def test_occluder_blocks_light_but_emission_survives() -> None:
    material = SceneLightingMaterial(
        albedo=(1.0, 1.0, 1.0),
        emission=(0.1, 0.0, 0.0),
        emission_strength=1.0,
    )
    settings = SceneLightingSettings(
        ambient_intensity=0.0,
        lights=(ScenePointLight("key", (100.0, 0.0), intensity=1.0, radius=200.0),),
        occluders=(((40.0, -20.0), (60.0, -20.0), (60.0, 20.0), (40.0, 20.0)),),
    )

    color, opacity, contributors = shade_color((0.0, 0.0), material, settings)

    assert color == (0.1, 0.0, 0.0)
    assert opacity == 1.0
    assert contributors == ()


def test_authored_light_socket_parameters_are_valid_renderer_inputs() -> None:
    socket = SceneLightSocketRecord(
        id="key-light",
        layer_id="layer",
        position=Point3Record(x=10.0, y=20.0, z=0.0),
        color="#ff8040",
        intensity=1.5,
        radius=300.0,
    )
    color = tuple(
        int(socket.color[index : index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    light = ScenePointLight(
        socket.id,
        (socket.position.x, socket.position.y),
        color=color,
        intensity=socket.intensity,
        radius=socket.radius,
    )

    assert light.position == (10.0, 20.0)
    assert light.color == (1.0, 128.0 / 255.0, 64.0 / 255.0)
    assert light.intensity == 1.5
