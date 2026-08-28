"""Bridges between the professional scene document and runtime preview.

The V2 professional scene document is the canonical authored representation.
The older lateral scenario document remains a compatibility input only.  This
module keeps the conversion explicit and does not mutate either source.
"""

from __future__ import annotations

from pathlib import Path

from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scenario_preview import ScenarioPreviewLayer
from src.models.scene import Scene
from src.persistence.project_schema import PointRecord
from src.persistence.scenario_schema import ScenarioDocumentV1
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
    SceneParallaxLayerRecord,
)


def preview_layers_from_professional_document(
    document: SceneAuthoringDocumentV2,
) -> tuple[ScenarioPreviewLayer, ...]:
    """Build the main-editor preview bindings from a V2 document."""

    object_ids_by_layer: dict[str, list[str]] = {
        layer.id: [] for layer in document.layers
    }
    for authored_object in document.objects:
        object_ids_by_layer.setdefault(authored_object.layer_id, []).append(
            authored_object.id
        )
    parallax_by_layer = {
        item.layer_id: item for item in document.parallax_layers
    }
    preview_layers: list[ScenarioPreviewLayer] = []
    for layer in document.layers:
        parallax = parallax_by_layer.get(
            layer.id, SceneParallaxLayerRecord(layer_id=layer.id)
        )
        preview_layers.append(
            ScenarioPreviewLayer(
                layer.id,
                tuple(object_ids_by_layer.get(layer.id, ())),
                ParallaxLayer(
                    depth=float(parallax.depth),
                    translation_strength=float(parallax.translation_strength),
                    zoom_strength=float(parallax.zoom_strength),
                ),
                layer.visible,
            )
        )
    return tuple(preview_layers)


def preview_camera_from_professional_document(
    document: SceneAuthoringDocumentV2,
    viewport: tuple[float, float],
) -> OrthographicCamera:
    """Build the runtime preview camera from a V2 document."""

    return OrthographicCamera(
        viewport,
        position=(
            float(document.camera.position.x),
            float(document.camera.position.y),
        ),
        zoom=float(document.camera.zoom),
    )


def professional_document_from_scene(
    scene: Scene,
    project_path: Path,
    legacy_document: ScenarioDocumentV1 | None = None,
) -> SceneAuthoringDocumentV2:
    """Create V2 explicitly, optionally preserving a legacy V1 scenario.

    The legacy document has no object transforms or asset records, so those
    are sourced from the current project scene.  Its layer order, names,
    visibility, object assignments, parallax and camera are preserved where
    the corresponding V2 records exist.
    """

    from src.core.scene_authoring_factory import document_from_scene
    from src.persistence.scene_authoring_schema import (
        SceneLayerAuthoringRecord,
        SceneObjectAuthoringRecord,
        upgrade_scene_authoring_document,
    )

    document = upgrade_scene_authoring_document(
        document_from_scene(scene, project_path)
    )
    if legacy_document is None:
        return document

    current_layers = {item.id: item for item in document.layers}
    legacy_layers = {
        item.id: item for item in legacy_document.layers if item.id in current_layers
    }
    ordered_layers: list[SceneLayerAuthoringRecord] = []
    seen_layers: set[str] = set()
    for legacy_layer in legacy_document.layers:
        current = current_layers.get(legacy_layer.id)
        if current is None:
            continue
        ordered_layers.append(
            current.model_copy(
                update={
                    "name": legacy_layer.name,
                    "visible": legacy_layer.visible,
                }
            )
        )
        seen_layers.add(current.id)
    ordered_layers.extend(
        layer for layer in document.layers if layer.id not in seen_layers
    )

    object_layer: dict[str, str] = {}
    known_objects = {item.id for item in document.objects}
    for legacy_layer in legacy_document.layers:
        for object_id in legacy_layer.object_ids:
            if object_id in known_objects:
                object_layer[object_id] = legacy_layer.id
    objects: list[SceneObjectAuthoringRecord] = [
        item.model_copy(
            update={"layer_id": object_layer.get(item.id, item.layer_id)}
        )
        for item in document.objects
    ]

    parallax_layers = [
        SceneParallaxLayerRecord(
            layer_id=layer.id,
            depth=float(legacy_layers[layer.id].parallax.depth)
            if layer.id in legacy_layers
            else 0.0,
            translation_strength=float(
                legacy_layers[layer.id].parallax.translation_strength
            )
            if layer.id in legacy_layers
            else 1.0,
            zoom_strength=float(legacy_layers[layer.id].parallax.zoom_strength)
            if layer.id in legacy_layers
            else 1.0,
        )
        for layer in ordered_layers
    ]
    return document.model_copy(
        update={
            "layers": ordered_layers,
            "objects": objects,
            "camera": SceneCameraAuthoringRecord(
                position=PointRecord(
                    x=float(legacy_document.camera.position.x),
                    y=float(legacy_document.camera.position.y),
                ),
                zoom=float(legacy_document.camera.zoom),
            ),
            "parallax_layers": parallax_layers,
        }
    )


__all__ = [
    "preview_camera_from_professional_document",
    "preview_layers_from_professional_document",
    "professional_document_from_scene",
]
