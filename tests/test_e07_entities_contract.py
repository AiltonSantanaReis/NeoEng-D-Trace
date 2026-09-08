from __future__ import annotations

import pytest

from src.persistence.project_schema import Point3Record, PointRecord
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.prefab_authoring import (
    create_prefab,
    detach_prefab_instance,
    instantiate_prefab,
    revert_prefab_override,
    set_prefab_override,
    update_prefab_sources,
)
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import load_scene_authoring, save_scene_authoring
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneComponentAuthoringRecord,
    SceneEntityAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneTransformRecord,
)


SHA = "1" * 64


def _transform() -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=4.0, y=8.0, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document(*entities: SceneEntityAuthoringRecord) -> SceneAuthoringDocumentV2:
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="E07 entities", generator="test", app_version="0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[],
        groups=[],
        entities=list(entities),
    )


def _entity(
    entity_id: str = "hero", *, instance_of: str | None = None
) -> SceneEntityAuthoringRecord:
    return SceneEntityAuthoringRecord(
        id=entity_id,
        name="Hero",
        layer_id="layer",
        transform=_transform(),
        components=[
            SceneComponentAuthoringRecord(
                id="transform-extra",
                type="gameplay.mover",
                version=1,
                properties={"speed": 2.5, "enabled": True},
            )
        ],
        instance_of=instance_of,
    )


def test_e07_entities_roundtrip_preserves_identity_components_and_instance_source(
    tmp_path,
):
    document = _document(_entity("prefab-source"), _entity("hero", instance_of="prefab-source"))
    path = tmp_path / "scene.ndtscene.json"

    save_scene_authoring(document, path)
    reopened = load_scene_authoring(path, verify_assets=False)

    assert isinstance(reopened, SceneAuthoringDocumentV2)
    assert [entity.id for entity in reopened.entities] == ["prefab-source", "hero"]
    assert reopened.entities[1].instance_of == "prefab-source"
    assert reopened.entities[0].components[0].type == "gameplay.mover"
    assert reopened.entities[0].components[0].properties["speed"] == 2.5


def test_e07_rejects_duplicate_entity_and_component_ids():
    with pytest.raises(ValueError, match="entity IDs must be unique"):
        _document(_entity("same"), _entity("same"))

    duplicate_components = _entity("hero").model_copy(
        update={"components": [_entity("a").components[0], _entity("b").components[0]]}
    )
    with pytest.raises(ValueError, match="entity component IDs must be unique"):
        _document(duplicate_components)


def test_e07_rejects_invalid_component_version_layer_and_instance_source():
    with pytest.raises(ValueError):
        SceneComponentAuthoringRecord(id="c", type="test", version=0)

    with pytest.raises(ValueError, match="unknown layer"):
        SceneAuthoringDocumentV2(
            metadata=SceneAuthoringMetadataRecord(
                name="invalid", generator="test", app_version="0"
            ),
            project=ProjectReferenceRecord(sha256=SHA),
            assets=[],
            layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
            objects=[],
            groups=[],
            entities=[_entity("hero").model_copy(update={"layer_id": "missing"})],
        )

    with pytest.raises(ValueError, match="unknown source entity"):
        _document(_entity("hero", instance_of="missing"))

    with pytest.raises(ValueError, match="cannot instance itself"):
        _document(_entity("hero", instance_of="hero"))


def test_e07_spatial_parent_is_distinct_and_cycle_safe():
    root = _entity("root")
    child = _entity("child").model_copy(update={"parent_entity_id": "root"})
    document = _document(root, child)
    model = SceneAuthoringModel(document)

    model.set_entity_parent("root", None)
    assert model.document.entities[1].parent_entity_id == "root"
    assert model.document.groups == []

    with pytest.raises(ValueError, match="entity hierarchy contains a cycle"):
        model.set_entity_parent("root", "child")

    with pytest.raises(ValueError, match="unknown parent entity"):
        _document(_entity("child").model_copy(update={"parent_entity_id": "missing"}))


def test_e07_prefab_lifecycle_preserves_overrides_and_detaches(tmp_path):
    document = _document(_entity("root"))
    document = create_prefab(document, "enemy", "Enemy", ["root"])
    document = instantiate_prefab(document, "enemy", "enemy-instance", "root")
    document = set_prefab_override(document, "enemy-instance", "speed", 4.0)
    document = update_prefab_sources(document, "enemy", ["root"])

    assert document.prefabs[0].version == 2
    assert document.prefab_instances[0].overrides[0].value == 4.0

    document = revert_prefab_override(document, "enemy-instance", "speed")
    document = detach_prefab_instance(document, "enemy-instance")
    path = tmp_path / "prefab-scene.ndtscene.json"
    save_scene_authoring(document, path)
    reopened = load_scene_authoring(path, verify_assets=False)

    assert isinstance(reopened, SceneAuthoringDocumentV2)
    assert reopened.prefab_instances[0].detached is True
    assert reopened.prefab_instances[0].overrides == []


def test_e07_prefab_operations_reject_missing_and_duplicate_identity():
    document = _document(_entity("root"))
    with pytest.raises(ValueError, match="source entity does not exist"):
        create_prefab(document, "enemy", "Enemy", ["missing"])

    document = create_prefab(document, "enemy", "Enemy", ["root"])
    with pytest.raises(ValueError, match="prefab ID already exists"):
        create_prefab(document, "enemy", "Enemy 2", ["root"])
    with pytest.raises(ValueError, match="prefab does not exist"):
        instantiate_prefab(document, "missing", "instance", "root")
