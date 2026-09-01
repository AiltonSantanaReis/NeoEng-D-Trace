"""Deterministic preview projection for the professional scene editor."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneLayerAuthoringRecord,
    SceneSocketRecord,
)

from .parallax_camera import OrthographicCamera, ParallaxLayer, Point2
from .scene_authoring_groups import group_ancestry
from .scene_authoring_order import ordered_scene_objects


@dataclass(frozen=True)
class ProjectedSceneObject:
    """One object polygon projected into viewport pixels."""

    object_id: str
    layer_id: str
    points: tuple[Point2, ...]
    origin: Point2
    zoom: float


@dataclass(frozen=True)
class ProjectedSceneSocket:
    """One declarative socket marker projected into viewport pixels."""

    socket_id: str
    socket_type: str
    position: Point2
    color: str


@dataclass(frozen=True)
class SceneAuthoringPreviewFrame:
    """Complete deterministic frame model consumed by the Qt viewport."""

    camera: OrthographicCamera
    objects: tuple[ProjectedSceneObject, ...]
    sockets: tuple[ProjectedSceneSocket, ...]


def _point(value: Sequence[float], field: str) -> tuple[float, float]:
    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError(f"{field} must contain exactly two coordinates")
    result = (float(value[0]), float(value[1]))
    if not all(math.isfinite(item) for item in result):
        raise ValueError(f"{field} must be finite")
    return result


def _parallax(document: SceneAuthoringDocumentV2, layer_id: str) -> ParallaxLayer:
    record = next(
        (item for item in document.parallax_layers if item.layer_id == layer_id),
        None,
    )
    if record is None:
        return ParallaxLayer()
    return ParallaxLayer(
        depth=float(record.depth),
        translation_strength=float(record.translation_strength),
        zoom_strength=float(record.zoom_strength),
    )


def _socket_color(socket: SceneSocketRecord) -> str:
    if socket.type == "light":
        return socket.color
    if socket.type == "vfx":
        return "#c78cff"
    return "#ffcf65"


def _build_visibility_index(
    document: SceneAuthoringDocumentV2,
    isolated_group_id: str | None,
) -> tuple[dict[str, SceneLayerAuthoringRecord], dict[str, bool]]:
    """Build one immutable visibility lookup for the current frame.

    The lookup preserves ``object_is_effectively_visible`` semantics while
    avoiding a full group/layer traversal for every object.  It is deliberately
    rebuilt for each frame so it cannot outlive document or isolation state.
    """

    layers = {item.id: item for item in document.layers}
    groups = {item.id: item for item in document.groups}
    object_ids = {item.id for item in document.objects}
    candidate_ids = {
        item.id
        for item in document.objects
        if item.visible and layers[item.layer_id].visible
    }
    ancestry_by_group: dict[str, tuple[str, ...]] = {}
    memberships_by_object: dict[str, list[str]] = {
        object_id: [] for object_id in candidate_ids
    }
    for group in document.groups:
        member_ids = [
            object_id
            for object_id in group.members
            if object_id in candidate_ids and object_id in object_ids
        ]
        if not member_ids:
            continue
        ancestry = ancestry_by_group.setdefault(
            group.id, group_ancestry(document, group.id)
        )
        for ancestor_id in ancestry:
            ancestry_by_group.setdefault(
                ancestor_id, group_ancestry(document, ancestor_id)
            )
        for object_id in member_ids:
            memberships = memberships_by_object[object_id]
            for ancestor_id in ancestry:
                if ancestor_id not in memberships:
                    memberships.append(ancestor_id)

    visible_groups = {
        group_id: all(groups[item_id].visible for item_id in ancestry)
        for group_id, ancestry in ancestry_by_group.items()
    }
    visible_objects: dict[str, bool] = {}
    for item in document.objects:
        # The caller historically indexes layers before checking visibility;
        # retain that fail-closed validation behavior.
        layer = layers[item.layer_id]
        if not item.visible or not layer.visible:
            visible_objects[item.id] = False
            continue
        memberships = memberships_by_object.get(item.id, [])
        if any(not visible_groups[group_id] for group_id in memberships):
            visible_objects[item.id] = False
            continue
        if isolated_group_id is not None:
            if isolated_group_id not in groups:
                raise KeyError(isolated_group_id)
            visible_objects[item.id] = isolated_group_id in memberships
        else:
            visible_objects[item.id] = True
    return layers, visible_objects


def _world_points(
    object_record,
    geometry: Iterable[Sequence[float]],
) -> tuple[Point2, ...]:
    transform = object_record.transform
    angle = math.radians(float(transform.rotation.z))
    cosine, sine = math.cos(angle), math.sin(angle)
    result: list[Point2] = []
    for raw_point in geometry:
        x, y = _point(raw_point, "object geometry")
        x *= float(transform.scale.x) * (-1.0 if transform.flip_x else 1.0)
        y *= float(transform.scale.y) * (-1.0 if transform.flip_y else 1.0)
        rotated_x = x * cosine - y * sine
        rotated_y = x * sine + y * cosine
        result.append(
            (
                float(transform.position.x) + rotated_x,
                float(transform.position.y) + rotated_y,
            )
        )
    return tuple(result)


def build_scene_authoring_preview(
    document: SceneAuthoringDocumentV2,
    viewport_size: Sequence[float],
    geometries: Mapping[str, Iterable[Sequence[float]]],
    *,
    isolated_group_id: str | None = None,
) -> SceneAuthoringPreviewFrame:
    """Project visible objects and sockets without mutating the document."""

    if not isinstance(document, SceneAuthoringDocumentV2):
        raise ValueError("professional preview requires scene authoring schema v2")
    viewport = _point(viewport_size, "viewport_size")
    if viewport[0] <= 0.0 or viewport[1] <= 0.0:
        raise ValueError("viewport_size must be positive")
    camera = OrthographicCamera(
        viewport_size=viewport,
        position=(float(document.camera.position.x), float(document.camera.position.y)),
        zoom=float(document.camera.zoom),
    )
    layers, visible_objects = _build_visibility_index(document, isolated_group_id)
    parallax_by_layer = {
        record.layer_id: ParallaxLayer(
            depth=float(record.depth),
            translation_strength=float(record.translation_strength),
            zoom_strength=float(record.zoom_strength),
        )
        for record in document.parallax_layers
    }
    projected_objects: list[ProjectedSceneObject] = []
    for item in ordered_scene_objects(document):
        layers[item.layer_id]
        if not visible_objects[item.id]:
            continue
        geometry = geometries.get(item.id, ())
        world = _world_points(item, geometry)
        if not world:
            continue
        parallax = parallax_by_layer.get(item.layer_id, ParallaxLayer())
        projected = tuple(camera.project(point, parallax) for point in world)
        projected_objects.append(
            ProjectedSceneObject(
                object_id=item.id,
                layer_id=item.layer_id,
                points=projected,
                origin=camera.project(
                    (
                        float(item.transform.position.x),
                        float(item.transform.position.y),
                    ),
                    parallax,
                ),
                zoom=camera.effective_zoom(parallax),
            )
        )
    projected_sockets: list[ProjectedSceneSocket] = []
    for socket in document.sockets:
        if not layers[socket.layer_id].visible:
            continue
        projected_sockets.append(
            ProjectedSceneSocket(
                socket_id=socket.id,
                socket_type=socket.type,
                position=camera.project(
                    (float(socket.position.x), float(socket.position.y)),
                    parallax_by_layer.get(socket.layer_id, ParallaxLayer()),
                ),
                color=_socket_color(socket),
            )
        )
    return SceneAuthoringPreviewFrame(
        camera=camera,
        objects=tuple(projected_objects),
        sockets=tuple(projected_sockets),
    )
