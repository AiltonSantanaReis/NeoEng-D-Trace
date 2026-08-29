"""Deterministic visual ordering for professional scene authoring.

Layer order is an authoring concern and is deliberately separate from the
persisted ``transform.position.z`` field.  The first layer is drawn first
(back) and the last layer is drawn last (front).  Object order inside a layer
is the stable order in ``document.objects``.
"""

from __future__ import annotations

from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocument,
    SceneObjectAuthoringRecord,
)


def ordered_scene_objects(
    document: SceneAuthoringDocument,
) -> tuple[SceneObjectAuthoringRecord, ...]:
    """Return objects in deterministic back-to-front layer order.

    The document schema already validates layer and object references.  The
    explicit sort keeps the rendering and preview contracts independent from
    incidental object-list ordering while preserving object order within each
    layer.
    """

    layer_order = {layer.id: index for index, layer in enumerate(document.layers)}
    return tuple(
        item
        for _, item in sorted(
            enumerate(document.objects),
            key=lambda pair: (layer_order[pair[1].layer_id], pair[0]),
        )
    )


def layer_visual_priority(
    layer_index: int,
    object_index_in_layer: int,
    object_count: int,
) -> float:
    """Return a strictly ordered graphics priority for one authored object.

    The value is transient and exists only for the Qt scene.  It gives every
    object in a later layer a greater priority than every object in an earlier
    layer, while retaining document order for objects in the same layer.
    """

    if (
        isinstance(layer_index, bool)
        or isinstance(object_index_in_layer, bool)
        or isinstance(object_count, bool)
        or layer_index < 0
        or object_index_in_layer < 0
        or object_count < 1
        or object_index_in_layer >= object_count
    ):
        raise ValueError("visual ordering indexes are invalid")
    stride = object_count + 1
    return float(layer_index * stride + object_index_in_layer)


def layer_index_by_id(document: SceneAuthoringDocument) -> dict[str, int]:
    """Return the current persisted layer order for UI consumers."""

    return {layer.id: index for index, layer in enumerate(document.layers)}
