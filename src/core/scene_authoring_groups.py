"""Pure group and hierarchy semantics for the professional scene editor.

The helpers in this module deliberately contain no Qt and no mutation.  They
are shared by the model, deterministic preview and professional viewport so
visibility, lock inheritance and isolation cannot drift between surfaces.
"""

from __future__ import annotations

from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocument,
    SceneGroupAuthoringRecord,
)


def groups_by_id(
    document: SceneAuthoringDocument,
) -> dict[str, SceneGroupAuthoringRecord]:
    """Return the document groups indexed by stable ID."""

    return {group.id: group for group in document.groups}


def group_parent_id(group: SceneGroupAuthoringRecord) -> str | None:
    """Read the optional V2 parent without changing the V1 record contract."""

    return getattr(group, "parent_group_id", None)


def group_ancestry(
    document: SceneAuthoringDocument,
    group_id: str,
) -> tuple[str, ...]:
    """Return a group and its ancestors, nearest first."""

    by_id = groups_by_id(document)
    if group_id not in by_id:
        raise KeyError(group_id)
    result: list[str] = []
    current: str | None = group_id
    while current is not None:
        if current in result:
            raise ValueError("group hierarchy contains a cycle")
        group = by_id.get(current)
        if group is None:
            raise ValueError(f"group hierarchy references unknown parent {current!r}")
        result.append(current)
        current = group_parent_id(group)
    return tuple(result)


def root_group_ids(document: SceneAuthoringDocument) -> tuple[str, ...]:
    """Return root groups in their persisted order."""

    return tuple(
        group.id for group in document.groups if group_parent_id(group) is None
    )


def child_group_ids(
    document: SceneAuthoringDocument,
    parent_group_id: str | None,
) -> tuple[str, ...]:
    """Return direct child groups in their persisted sibling order."""

    if parent_group_id is not None and parent_group_id not in groups_by_id(document):
        raise KeyError(parent_group_id)
    return tuple(
        group.id
        for group in document.groups
        if group_parent_id(group) == parent_group_id
    )


def object_group_ids(
    document: SceneAuthoringDocument,
    object_id: str,
) -> tuple[str, ...]:
    """Return direct memberships plus all of their group ancestors."""

    direct = [group.id for group in document.groups if object_id in group.members]
    result: list[str] = []
    for group_id in direct:
        for ancestor_id in group_ancestry(document, group_id):
            if ancestor_id not in result:
                result.append(ancestor_id)
    return tuple(result)


def object_ids_for_group(
    document: SceneAuthoringDocument,
    group_id: str,
) -> tuple[str, ...]:
    """Return all object descendants of a group in document object order."""

    group_ancestry(document, group_id)  # validates the requested group exists
    group_ids = {
        candidate.id
        for candidate in document.groups
        if group_id in group_ancestry(document, candidate.id)
    }
    return tuple(
        item.id
        for item in document.objects
        if any(
            item.id in group.members
            for group in document.groups
            if group.id in group_ids
        )
    )


def group_is_effectively_visible(
    document: SceneAuthoringDocument,
    group_id: str,
) -> bool:
    """Return whether a group and every ancestor are visible."""

    by_id = groups_by_id(document)
    return all(by_id[item].visible for item in group_ancestry(document, group_id))


def group_is_effectively_locked(
    document: SceneAuthoringDocument,
    group_id: str,
) -> bool:
    """Return whether a group or any ancestor is locked."""

    by_id = groups_by_id(document)
    return any(by_id[item].locked for item in group_ancestry(document, group_id))


def object_is_effectively_visible(
    document: SceneAuthoringDocument,
    object_id: str,
    *,
    isolated_group_id: str | None = None,
) -> bool:
    """Apply object, layer, group and optional isolation visibility."""

    item = next((value for value in document.objects if value.id == object_id), None)
    if item is None or not item.visible:
        return False
    layers = {layer.id: layer for layer in document.layers}
    layer = layers.get(item.layer_id)
    if layer is None or not layer.visible:
        return False
    memberships = object_group_ids(document, object_id)
    if any(
        not group_is_effectively_visible(document, group_id) for group_id in memberships
    ):
        return False
    if isolated_group_id is not None:
        if isolated_group_id not in groups_by_id(document):
            raise KeyError(isolated_group_id)
        if isolated_group_id not in memberships:
            return False
    return True


def locked_group_for_object(
    document: SceneAuthoringDocument,
    object_id: str,
) -> SceneGroupAuthoringRecord | None:
    """Return the first locked group affecting an object, if any."""

    by_id = groups_by_id(document)
    for group_id in object_group_ids(document, object_id):
        for affected_id in group_ancestry(document, group_id):
            group = by_id[affected_id]
            if group.locked:
                return group
    return None


def object_is_effectively_locked(
    document: SceneAuthoringDocument,
    object_id: str,
) -> bool:
    """Apply object, layer and group lock inheritance."""

    item = next((value for value in document.objects if value.id == object_id), None)
    if item is None:
        raise KeyError(object_id)
    if item.locked:
        return True
    layers = {layer.id: layer for layer in document.layers}
    layer = layers.get(item.layer_id)
    if layer is None:
        raise ValueError(f"object {object_id!r} references unknown layer")
    return layer.locked or locked_group_for_object(document, object_id) is not None
