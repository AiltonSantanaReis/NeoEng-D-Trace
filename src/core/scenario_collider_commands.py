"""Transactional authoring commands for independent scenario colliders."""

from __future__ import annotations

from dataclasses import dataclass, replace

from src.core.scenario_colliders import Collider, ColliderDocument, ColliderError, Point


@dataclass(frozen=True)
class ColliderDelta:
    collider_id: str
    before: Collider | None
    after: Collider | None
    label: str


class ColliderEditHistory:
    """Apply one-collider deltas with stale-state protection and Undo/Redo."""

    def __init__(self, document: ColliderDocument):
        self.document = document
        self._undo: list[ColliderDelta] = []
        self._redo: list[ColliderDelta] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def _current(self, collider_id: str) -> Collider | None:
        return self.document.colliders.get(collider_id)

    def _set(self, collider_id: str, value: Collider | None) -> None:
        if value is None:
            self.document.colliders.pop(collider_id, None)
        else:
            self.document.colliders[collider_id] = value

    def _apply_delta(self, delta: ColliderDelta, expected: Collider | None) -> None:
        current = self._current(delta.collider_id)
        if current != expected:
            raise ColliderError(
                "stale_state",
                "collider changed before the transaction could be applied",
                collider_id=delta.collider_id,
            )
        if delta.after is not None and delta.after.id != delta.collider_id:
            raise ColliderError("id_mismatch", "delta ID does not match its collider")
        self._set(delta.collider_id, delta.after)

    def apply(self, delta: ColliderDelta) -> None:
        self._apply_delta(delta, delta.before)
        self._undo.append(delta)
        self._redo.clear()

    def undo(self) -> ColliderDelta:
        if not self._undo:
            raise ColliderError("empty_undo", "no collider edit is available to undo")
        delta = self._undo[-1]
        self._apply_delta(
            ColliderDelta(delta.collider_id, delta.after, delta.before, delta.label),
            delta.after,
        )
        self._undo.pop()
        self._redo.append(delta)
        return delta

    def redo(self) -> ColliderDelta:
        if not self._redo:
            raise ColliderError("empty_redo", "no collider edit is available to redo")
        delta = self._redo[-1]
        self._apply_delta(delta, delta.before)
        self._redo.pop()
        self._undo.append(delta)
        return delta

    def create(self, collider: Collider) -> None:
        self.apply(ColliderDelta(collider.id, None, collider, "create"))

    def update(self, collider: Collider) -> None:
        current = self._current(collider.id)
        if current is None:
            raise ColliderError(
                "missing_id", "collider does not exist", collider_id=collider.id
            )
        self.apply(ColliderDelta(collider.id, current, collider, "update"))

    def move(self, collider_id: str, position: Point) -> None:
        current = self._current(collider_id)
        if current is None:
            raise ColliderError(
                "missing_id", "collider does not exist", collider_id=collider_id
            )
        self.update(replace(current, position=position))

    def set_visible(self, collider_id: str, visible: bool) -> None:
        current = self._current(collider_id)
        if current is None:
            raise ColliderError(
                "missing_id", "collider does not exist", collider_id=collider_id
            )
        self.update(replace(current, visible=bool(visible)))

    def duplicate(self, collider_id: str, new_id: str) -> None:
        current = self._current(collider_id)
        if current is None:
            raise ColliderError(
                "missing_id", "collider does not exist", collider_id=collider_id
            )
        self.create(replace(current, id=new_id))

    def remove(self, collider_id: str) -> None:
        current = self._current(collider_id)
        if current is None:
            raise ColliderError(
                "missing_id", "collider does not exist", collider_id=collider_id
            )
        self.apply(ColliderDelta(collider_id, current, None, "remove"))


__all__ = ["ColliderDelta", "ColliderEditHistory"]
