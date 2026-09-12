"""Deterministic, non-destructive prefab operations for E07-C."""

from __future__ import annotations

from typing import Any

from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    ScenePrefabAuthoringRecord,
    ScenePrefabInstanceAuthoringRecord,
    ScenePrefabOverrideRecord,
    validate_scene_authoring_document,
)


def _v2(document: Any) -> SceneAuthoringDocumentV2:
    if not isinstance(document, SceneAuthoringDocumentV2):
        raise ValueError("prefab authoring requires scene schema V2")
    return document


def create_prefab(
    document: SceneAuthoringDocumentV2,
    prefab_id: str,
    name: str,
    source_entity_ids: list[str],
) -> SceneAuthoringDocumentV2:
    document = _v2(document)
    if any(item.id == prefab_id for item in document.prefabs):
        raise ValueError("prefab ID already exists")
    known = {item.id for item in document.entities}
    if any(item not in known for item in source_entity_ids):
        raise ValueError("prefab source entity does not exist")
    candidate = document.model_copy(
        update={
            "prefabs": [
                *document.prefabs,
                ScenePrefabAuthoringRecord(
                    id=prefab_id,
                    name=name,
                    source_entity_ids=source_entity_ids,
                ),
            ]
        }
    )
    return validate_scene_authoring_document(candidate)  # type: ignore[return-value]


def instantiate_prefab(
    document: SceneAuthoringDocumentV2,
    prefab_id: str,
    instance_id: str,
    root_entity_id: str,
) -> SceneAuthoringDocumentV2:
    document = _v2(document)
    if not any(item.id == prefab_id for item in document.prefabs):
        raise ValueError("prefab does not exist")
    if any(item.id == instance_id for item in document.prefab_instances):
        raise ValueError("prefab instance ID already exists")
    if not any(item.id == root_entity_id for item in document.entities):
        raise ValueError("prefab instance root entity does not exist")
    instance = ScenePrefabInstanceAuthoringRecord(
        id=instance_id, prefab_id=prefab_id, root_entity_id=root_entity_id
    )
    candidate = document.model_copy(
        update={"prefab_instances": [*document.prefab_instances, instance]}
    )
    return validate_scene_authoring_document(candidate)  # type: ignore[return-value]


def set_prefab_override(
    document: SceneAuthoringDocumentV2,
    instance_id: str,
    path: str,
    value: str | int | float | bool | None,
) -> SceneAuthoringDocumentV2:
    document = _v2(document)
    instances = list(document.prefab_instances)
    for index, instance in enumerate(instances):
        if instance.id != instance_id:
            continue
        overrides = [item for item in instance.overrides if item.path != path]
        overrides.append(ScenePrefabOverrideRecord(path=path, value=value))
        instances[index] = instance.model_copy(update={"overrides": overrides})
        candidate = document.model_copy(update={"prefab_instances": instances})
        return validate_scene_authoring_document(  # type: ignore[return-value]
            candidate
        )
    raise KeyError(instance_id)


def revert_prefab_override(
    document: SceneAuthoringDocumentV2, instance_id: str, path: str
) -> SceneAuthoringDocumentV2:
    document = _v2(document)
    instances = list(document.prefab_instances)
    for index, instance in enumerate(instances):
        if instance.id != instance_id:
            continue
        instances[index] = instance.model_copy(
            update={
                "overrides": [item for item in instance.overrides if item.path != path]
            }
        )
        candidate = document.model_copy(update={"prefab_instances": instances})
        return validate_scene_authoring_document(  # type: ignore[return-value]
            candidate
        )
    raise KeyError(instance_id)


def update_prefab_sources(
    document: SceneAuthoringDocumentV2,
    prefab_id: str,
    source_entity_ids: list[str],
) -> SceneAuthoringDocumentV2:
    document = _v2(document)
    prefabs = list(document.prefabs)
    for index, prefab in enumerate(prefabs):
        if prefab.id != prefab_id:
            continue
        prefabs[index] = prefab.model_copy(
            update={
                "source_entity_ids": source_entity_ids,
                "version": prefab.version + 1,
            }
        )
        candidate = document.model_copy(update={"prefabs": prefabs})
        return validate_scene_authoring_document(  # type: ignore[return-value]
            candidate
        )
    raise KeyError(prefab_id)


def detach_prefab_instance(
    document: SceneAuthoringDocumentV2, instance_id: str
) -> SceneAuthoringDocumentV2:
    document = _v2(document)
    instances = list(document.prefab_instances)
    for index, instance in enumerate(instances):
        if instance.id != instance_id:
            continue
        instances[index] = instance.model_copy(update={"detached": True})
        candidate = document.model_copy(update={"prefab_instances": instances})
        return validate_scene_authoring_document(  # type: ignore[return-value]
            candidate
        )
    raise KeyError(instance_id)
