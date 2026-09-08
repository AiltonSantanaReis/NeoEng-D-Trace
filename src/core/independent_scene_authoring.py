"""Deterministic authoring operations for independent-scene primitives."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from uuid import uuid4

from src.persistence.independent_scene_schema import (
    IndependentSceneDocumentV2,
    IndependentScenePrimitiveGeometryRecord,
    IndependentScenePrimitiveRecord,
    IndependentScenePrimitiveTransformRecord,
)
from src.persistence.project_schema import PointRecord


class IndependentSceneAuthoringModel:
    """Validated immutable-document operations for the E02 authoring core."""

    def __init__(self, document: IndependentSceneDocumentV2) -> None:
        self.document = IndependentSceneDocumentV2.model_validate(
            document,
            strict=True,
        )
        self.selection: tuple[str, ...] = ()

    def _replace(self, **changes: object) -> None:
        self.document = IndependentSceneDocumentV2.model_validate(
            self.document.model_copy(update=changes),
            strict=True,
        )

    def _primitive(self, primitive_id: str) -> IndependentScenePrimitiveRecord:
        for item in self.document.objects:
            if item.id == primitive_id:
                return item
        raise KeyError(primitive_id)

    def _assert_editable(self, primitive_id: str) -> None:
        if self._primitive(primitive_id).locked:
            raise PermissionError(f"primitive {primitive_id!r} is locked")

    def set_selection(self, primitive_ids: Iterable[str]) -> tuple[str, ...]:
        selected = tuple(dict.fromkeys(primitive_ids))
        known = {item.id for item in self.document.objects}
        missing = [item for item in selected if item not in known]
        if missing:
            raise KeyError(missing[0])
        self.selection = selected
        return selected

    def clear_selection(self) -> None:
        self.selection = ()

    def add_primitive(
        self,
        *,
        kind: str,
        points: Sequence[PointRecord],
        name: str | None = None,
        primitive_id: str | None = None,
        closed: bool | None = None,
        filled: bool | None = None,
        transform: IndependentScenePrimitiveTransformRecord | None = None,
    ) -> IndependentScenePrimitiveRecord:
        chosen_id = primitive_id or f"primitive_{uuid4().hex[:12]}"
        if any(item.id == chosen_id for item in self.document.objects):
            raise ValueError(f"primitive ID already exists: {chosen_id}")
        if closed is None:
            closed = kind != "path"
        if filled is None:
            filled = closed
        geometry = IndependentScenePrimitiveGeometryRecord(
            kind=kind,
            points=list(points),
            closed=closed,
            filled=filled,
        )
        primitive = IndependentScenePrimitiveRecord(
            id=chosen_id,
            name=name or kind.title(),
            geometry=geometry,
            transform=transform or IndependentScenePrimitiveTransformRecord(),
        )
        self._replace(objects=[*self.document.objects, primitive])
        self.set_selection([primitive.id])
        return primitive

    def update_geometry(
        self,
        primitive_id: str,
        *,
        points: Sequence[PointRecord],
        closed: bool | None = None,
        filled: bool | None = None,
    ) -> IndependentScenePrimitiveRecord:
        self._assert_editable(primitive_id)
        current = self._primitive(primitive_id)
        geometry = current.geometry.model_copy(
            update={
                "points": list(points),
                "closed": current.geometry.closed if closed is None else closed,
                "filled": current.geometry.filled if filled is None else filled,
            }
        )
        updated = current.model_copy(update={"geometry": geometry})
        self._replace(
            objects=[
                updated if item.id == primitive_id else item
                for item in self.document.objects
            ]
        )
        return updated

    def update_transform(
        self,
        primitive_id: str,
        transform: IndependentScenePrimitiveTransformRecord,
    ) -> IndependentScenePrimitiveRecord:
        self._assert_editable(primitive_id)
        current = self._primitive(primitive_id)
        updated = current.model_copy(update={"transform": transform})
        self._replace(
            objects=[
                updated if item.id == primitive_id else item
                for item in self.document.objects
            ]
        )
        return updated

    def remove_primitive(self, primitive_id: str) -> None:
        self._assert_editable(primitive_id)
        self._replace(
            objects=[item for item in self.document.objects if item.id != primitive_id]
        )
        self.set_selection(item for item in self.selection if item != primitive_id)

    def duplicate_primitive(
        self,
        primitive_id: str,
        *,
        new_id: str | None = None,
    ) -> IndependentScenePrimitiveRecord:
        source = self._primitive(primitive_id)
        transform = source.transform.model_copy(
            update={
                "position": PointRecord(
                    x=source.transform.position.x + 16.0,
                    y=source.transform.position.y + 16.0,
                )
            }
        )
        return self.add_primitive(
            kind=source.geometry.kind,
            points=source.geometry.points,
            name=f"{source.name} Copy",
            primitive_id=new_id,
            closed=source.geometry.closed,
            filled=source.geometry.filled,
            transform=transform,
        )


__all__ = ["IndependentSceneAuthoringModel"]
