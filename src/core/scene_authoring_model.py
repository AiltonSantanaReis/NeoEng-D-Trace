"""Qt-independent editing model for professional scene authoring.

The model is deliberately independent from the existing lateral scenario and
from Qt. It provides deterministic selection, object/group operations and
snapping for the future editor window; persistence and rendering are separate
plan stages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from src.core.scene_authoring_groups import (
    group_ancestry,
    group_parent_id,
    locked_group_for_object,
)
from src.persistence.project_schema import Point3Record
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocument,
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
    SceneGroupAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneSnapRecord,
    SceneSocketRecord,
    SceneTransformRecord,
    validate_scene_authoring_document,
)


@dataclass(frozen=True)
class SceneSelection:
    ids: tuple[str, ...] = ()
    primary: str | None = None

    def __post_init__(self) -> None:
        if len(self.ids) != len(set(self.ids)):
            raise ValueError("selection IDs must be unique")
        if self.primary is not None and self.primary not in self.ids:
            raise ValueError("selection primary must belong to selection")

    @classmethod
    def from_ids(
        cls, object_ids: Iterable[str], primary: str | None = None
    ) -> "SceneSelection":
        ids = tuple(dict.fromkeys(object_ids))
        chosen = primary if primary is not None else (ids[0] if ids else None)
        return cls(ids=ids, primary=chosen)


def snap_value(value: int | float, spacing: int | float) -> float:
    """Snap one finite coordinate using symmetric nearest-grid rounding."""

    if (
        isinstance(value, bool)
        or isinstance(spacing, bool)
        or not math.isfinite(float(value))
        or not math.isfinite(float(spacing))
        or spacing <= 0
    ):
        raise ValueError("snap value must be finite and spacing positive")
    return float(round(float(value) / float(spacing)) * float(spacing))


def snap_transform(
    transform: SceneTransformRecord,
    snap: SceneSnapRecord,
) -> SceneTransformRecord:
    """Return a validated transform with position snapped when enabled."""

    if not snap.enabled:
        return transform
    return SceneTransformRecord(
        position=transform.position.model_copy(
            update={
                "x": snap_value(transform.position.x, snap.spacing.x),
                "y": snap_value(transform.position.y, snap.spacing.y),
            }
        ),
        rotation=transform.rotation,
        scale=transform.scale,
        pivot=transform.pivot,
        flip_x=transform.flip_x,
        flip_y=transform.flip_y,
    )


class SceneAuthoringModel:
    """Validated document plus non-persistent selection state."""

    def __init__(self, document: SceneAuthoringDocument) -> None:
        self.document = validate_scene_authoring_document(document)
        self.selection = SceneSelection()

    def _replace(self, **changes: object) -> None:
        candidate = self.document.model_copy(update=changes)
        self.document = validate_scene_authoring_document(candidate)

    def _object(self, object_id: str) -> SceneObjectAuthoringRecord:
        for item in self.document.objects:
            if item.id == object_id:
                return item
        raise KeyError(object_id)

    def _assert_editable(self, object_id: str) -> None:
        item = self._object(object_id)
        if item.locked:
            raise PermissionError(f"object {object_id!r} is locked")
        for layer in self.document.layers:
            if layer.id == item.layer_id and layer.locked:
                raise PermissionError(f"layer {layer.id!r} is locked")
        locked_group = locked_group_for_object(self.document, object_id)
        if locked_group is not None:
            raise PermissionError(f"group {locked_group.id!r} is locked")

    def assert_editable(self, object_id: str) -> None:
        """Validate that one object can participate in a mutating command."""

        self._assert_editable(object_id)

    def set_selection(
        self, object_ids: Iterable[str], primary: str | None = None
    ) -> SceneSelection:
        selected = SceneSelection.from_ids(object_ids, primary)
        known = {item.id for item in self.document.objects}
        missing = [item for item in selected.ids if item not in known]
        if missing:
            raise KeyError(missing[0])
        self.selection = selected
        return selected

    def clear_selection(self) -> None:
        self.selection = SceneSelection()

    def add_asset(self, asset: AssetReferenceRecord) -> None:
        if asset.id in {item.id for item in self.document.assets}:
            raise ValueError("asset ID exists")
        self._replace(assets=[*self.document.assets, asset])

    def update_asset(self, asset: AssetReferenceRecord) -> None:
        current = next(
            (item for item in self.document.assets if item.id == asset.id), None
        )
        if current is None:
            raise KeyError(asset.id)
        if asset.id != current.id:
            raise ValueError("asset ID cannot change")
        self._replace(
            assets=[
                asset if item.id == asset.id else item for item in self.document.assets
            ]
        )

    def add_object(
        self, obj: SceneObjectAuthoringRecord, *, select: bool = False
    ) -> None:
        if obj.id in {item.id for item in self.document.objects}:
            raise ValueError("object ID exists")
        self._replace(objects=[*self.document.objects, obj])
        if select:
            self.set_selection([obj.id])

    def remove_object(self, object_id: str) -> None:
        self._assert_editable(object_id)
        self._replace(
            objects=[item for item in self.document.objects if item.id != object_id],
            groups=[
                group.model_copy(
                    update={
                        "members": [
                            member for member in group.members if member != object_id
                        ]
                    }
                )
                for group in self.document.groups
            ],
        )
        self.set_selection(
            [item for item in self.selection.ids if item != object_id],
            primary=(
                self.selection.primary if self.selection.primary != object_id else None
            ),
        )

    def remove_objects(self, object_ids: Iterable[str]) -> None:
        """Remove a complete selection after pre-validating every target."""

        ids = tuple(object_ids)
        if len(ids) != len(set(ids)):
            raise ValueError("object IDs must be unique")
        if not ids:
            return
        for object_id in ids:
            self._assert_editable(object_id)
        removed = set(ids)
        self._replace(
            objects=[item for item in self.document.objects if item.id not in removed],
            groups=[
                group.model_copy(
                    update={
                        "members": [
                            member for member in group.members if member not in removed
                        ]
                    }
                )
                for group in self.document.groups
            ],
        )
        remaining = [item for item in self.selection.ids if item not in removed]
        primary = (
            self.selection.primary if self.selection.primary in remaining else None
        )
        self.set_selection(remaining, primary)

    def update_transform(self, object_id: str, transform: SceneTransformRecord) -> None:
        self._assert_editable(object_id)
        objects = [
            (
                item.model_copy(update={"transform": transform})
                if item.id == object_id
                else item
            )
            for item in self.document.objects
        ]
        self._replace(objects=objects)

    def translate_selected(self, delta: Point3Record) -> None:
        """Translate selected objects while preserving their relative positions."""

        for object_id in self.selection.ids:
            self._assert_editable(object_id)
        selected = set(self.selection.ids)
        objects = []
        for item in self.document.objects:
            if item.id not in selected:
                objects.append(item)
                continue
            position = item.transform.position
            translated = Point3Record(
                x=position.x + delta.x,
                y=position.y + delta.y,
                z=position.z + delta.z,
            )
            transform = SceneTransformRecord(
                position=translated,
                rotation=item.transform.rotation,
                scale=item.transform.scale,
                pivot=item.transform.pivot,
                flip_x=item.transform.flip_x,
                flip_y=item.transform.flip_y,
            )
            objects.append(
                item.model_copy(
                    update={"transform": snap_transform(transform, self.document.snap)}
                )
            )
        self._replace(objects=objects)

    def transform_selected(
        self,
        *,
        translation: Point3Record = Point3Record(x=0.0, y=0.0, z=0.0),
        rotation_z: float = 0.0,
        scale_factor: float = 1.0,
    ) -> None:
        """Apply one validated 2D transform to the current selection.

        Rotation and uniform scale are calculated around the geometric center
        of the selection, preserving the relative arrangement of objects.
        The operation is deliberately model-only; the editor session decides
        whether it is a preview or an undoable command.
        """

        if not math.isfinite(float(rotation_z)):
            raise ValueError("rotation_z must be finite")
        if not math.isfinite(float(scale_factor)) or scale_factor <= 0:
            raise ValueError("scale_factor must be finite and positive")
        for object_id in self.selection.ids:
            self._assert_editable(object_id)
        if not self.selection.ids:
            return

        selected = set(self.selection.ids)
        selected_objects = [
            item for item in self.document.objects if item.id in selected
        ]
        center_x = sum(item.transform.position.x for item in selected_objects) / len(
            selected_objects
        )
        center_y = sum(item.transform.position.y for item in selected_objects) / len(
            selected_objects
        )
        angle = math.radians(float(rotation_z))
        cosine, sine = math.cos(angle), math.sin(angle)
        objects = []
        for item in self.document.objects:
            if item.id not in selected:
                objects.append(item)
                continue
            position = item.transform.position
            relative_x = (position.x - center_x) * scale_factor
            relative_y = (position.y - center_y) * scale_factor
            rotated_x = relative_x * cosine - relative_y * sine
            rotated_y = relative_x * sine + relative_y * cosine
            transform = SceneTransformRecord(
                position=Point3Record(
                    x=center_x + rotated_x + translation.x,
                    y=center_y + rotated_y + translation.y,
                    z=position.z + translation.z,
                ),
                rotation=item.transform.rotation.model_copy(
                    update={"z": item.transform.rotation.z + rotation_z}
                ),
                scale=Point3Record(
                    x=item.transform.scale.x * scale_factor,
                    y=item.transform.scale.y * scale_factor,
                    z=item.transform.scale.z * scale_factor,
                ),
                pivot=item.transform.pivot,
                flip_x=item.transform.flip_x,
                flip_y=item.transform.flip_y,
            )
            objects.append(item.model_copy(update={"transform": transform}))
        self._replace(objects=objects)

    def set_snap(self, snap: SceneSnapRecord) -> None:
        self._replace(snap=snap)

    def _layer(self, layer_id: str) -> SceneLayerAuthoringRecord:
        for item in self.document.layers:
            if item.id == layer_id:
                return item
        raise KeyError(layer_id)

    def add_layer(self, layer: SceneLayerAuthoringRecord) -> None:
        if layer.id in {item.id for item in self.document.layers}:
            raise ValueError("layer ID exists")
        self._replace(layers=[*self.document.layers, layer])

    def remove_layer(self, layer_id: str) -> None:
        self._layer(layer_id)
        if len(self.document.layers) <= 1:
            raise ValueError("at least one layer is required")
        if any(item.layer_id == layer_id for item in self.document.objects):
            raise ValueError("cannot remove a layer with assigned objects")
        if isinstance(self.document, SceneAuthoringDocumentV2):
            if any(item.layer_id == layer_id for item in self.document.sockets):
                raise ValueError("cannot remove a layer with assigned sockets")
            parallax = [
                item
                for item in self.document.parallax_layers
                if item.layer_id != layer_id
            ]
            self._replace(
                layers=[item for item in self.document.layers if item.id != layer_id],
                parallax_layers=parallax,
            )
            return
        self._replace(
            layers=[item for item in self.document.layers if item.id != layer_id]
        )

    def rename_layer(self, layer_id: str, name: str) -> None:
        layer = self._layer(layer_id)
        self._replace(
            layers=[
                layer.model_copy(update={"name": name}) if item.id == layer_id else item
                for item in self.document.layers
            ]
        )

    def reorder_layer(self, layer_id: str, target_index: int) -> None:
        self._layer(layer_id)
        layers = list(self.document.layers)
        item = layers.pop(
            next(index for index, value in enumerate(layers) if value.id == layer_id)
        )
        target = max(0, min(int(target_index), len(layers)))
        layers.insert(target, item)
        self._replace(layers=layers)

    def set_layer_visibility(self, layer_id: str, visible: bool) -> None:
        layer = self._layer(layer_id)
        self._replace(
            layers=[
                (
                    layer.model_copy(update={"visible": visible})
                    if item.id == layer_id
                    else item
                )
                for item in self.document.layers
            ]
        )

    def set_layer_locked(self, layer_id: str, locked: bool) -> None:
        layer = self._layer(layer_id)
        self._replace(
            layers=[
                (
                    layer.model_copy(update={"locked": locked})
                    if item.id == layer_id
                    else item
                )
                for item in self.document.layers
            ]
        )

    def _stage4_document(self) -> SceneAuthoringDocumentV2:
        if not isinstance(self.document, SceneAuthoringDocumentV2):
            raise ValueError("stage 4 properties require scene authoring schema v2")
        return self.document

    def set_camera(self, camera: SceneCameraAuthoringRecord) -> None:
        self._stage4_document()
        self._replace(camera=camera)

    def set_parallax_layer(self, parallax: SceneParallaxLayerRecord) -> None:
        document = self._stage4_document()
        if parallax.layer_id not in {item.id for item in document.layers}:
            raise KeyError(parallax.layer_id)
        records = [
            item
            for item in document.parallax_layers
            if item.layer_id != parallax.layer_id
        ]
        self._replace(parallax_layers=[*records, parallax])

    def add_socket(self, socket: SceneSocketRecord) -> None:
        document = self._stage4_document()
        if socket.layer_id not in {item.id for item in document.layers}:
            raise KeyError(socket.layer_id)
        self._replace(sockets=[*document.sockets, socket])

    def update_socket_position(self, socket_id: str, position: Point3Record) -> None:
        document = self._stage4_document()
        if not any(item.id == socket_id for item in document.sockets):
            raise KeyError(socket_id)
        sockets = [
            (
                item.model_copy(update={"position": position})
                if item.id == socket_id
                else item
            )
            for item in document.sockets
        ]
        self._replace(sockets=sockets)

    def remove_socket(self, socket_id: str) -> None:
        document = self._stage4_document()
        if not any(item.id == socket_id for item in document.sockets):
            raise KeyError(socket_id)
        self._replace(
            sockets=[item for item in document.sockets if item.id != socket_id]
        )

    def add_group(self, group: SceneGroupAuthoringRecord) -> None:
        if group.id in {item.id for item in self.document.groups}:
            raise ValueError("group ID exists")
        known = {item.id for item in self.document.objects}
        if any(member not in known for member in group.members):
            raise KeyError("group member object not found")
        self._replace(groups=[*self.document.groups, group])

    def group_selection(self, group: SceneGroupAuthoringRecord) -> None:
        if not self.selection.ids:
            raise ValueError("cannot group an empty selection")
        group = group.model_copy(update={"members": list(self.selection.ids)})
        self.add_group(group)

    def _group(self, group_id: str) -> SceneGroupAuthoringRecord:
        for item in self.document.groups:
            if item.id == group_id:
                return item
        raise KeyError(group_id)

    def _replace_group(self, group_id: str, **changes: object) -> None:
        self._group(group_id)
        self._replace(
            groups=[
                item.model_copy(update=changes) if item.id == group_id else item
                for item in self.document.groups
            ]
        )

    def rename_group(self, group_id: str, name: str) -> None:
        if not name.strip():
            raise ValueError("group name cannot be blank")
        self._replace_group(group_id, name=name.strip())

    def remove_group(self, group_id: str) -> None:
        group = self._group(group_id)
        parent_id = group_parent_id(group)
        groups = [item for item in self.document.groups if item.id != group_id]
        if hasattr(group, "parent_group_id"):
            groups = [
                (
                    item.model_copy(update={"parent_group_id": parent_id})
                    if group_parent_id(item) == group_id
                    else item
                )
                for item in groups
            ]
        self._replace(groups=groups)

    def reorder_group(self, group_id: str, target_index: int) -> None:
        group = self._group(group_id)
        siblings = [
            item
            for item in self.document.groups
            if group_parent_id(item) == group_parent_id(group)
        ]
        positions = [
            index
            for index, item in enumerate(self.document.groups)
            if group_parent_id(item) == group_parent_id(group)
        ]
        sibling_ids = [item.id for item in siblings]
        current_index = sibling_ids.index(group_id)
        moved_id = sibling_ids.pop(current_index)
        target = max(0, min(int(target_index), len(sibling_ids)))
        sibling_ids.insert(target, moved_id)
        by_id = {item.id: item for item in self.document.groups}
        groups = list(self.document.groups)
        for position, sibling_id in zip(positions, sibling_ids):
            groups[position] = by_id[sibling_id]
        self._replace(groups=groups)

    def set_group_parent(self, group_id: str, parent_group_id: str | None) -> None:
        document = self.document
        group = self._group(group_id)
        if not hasattr(group, "parent_group_id"):
            if parent_group_id is not None:
                raise ValueError("nested groups require schema V2")
            return
        if parent_group_id == group_id:
            raise ValueError("group cannot be its own parent")
        if parent_group_id is not None:
            self._group(parent_group_id)
            if parent_group_id in group_ancestry(document, group_id):
                raise ValueError("group hierarchy contains a cycle")
        self._replace_group(group_id, parent_group_id=parent_group_id)

    def set_group_visibility(self, group_id: str, visible: bool) -> None:
        self._replace_group(group_id, visible=bool(visible))

    def set_group_locked(self, group_id: str, locked: bool) -> None:
        self._replace_group(group_id, locked=bool(locked))

    def add_objects_to_group(self, group_id: str, object_ids: Iterable[str]) -> None:
        group = self._group(group_id)
        selected = list(dict.fromkeys(object_ids))
        known = {item.id for item in self.document.objects}
        missing = [item for item in selected if item not in known]
        if missing:
            raise KeyError(missing[0])
        members = list(group.members)
        members.extend(item for item in selected if item not in members)
        self._replace_group(group_id, members=members)

    def remove_objects_from_group(
        self,
        group_id: str,
        object_ids: Iterable[str],
    ) -> None:
        group = self._group(group_id)
        selected = set(object_ids)
        self._replace_group(
            group_id,
            members=[item for item in group.members if item not in selected],
        )
