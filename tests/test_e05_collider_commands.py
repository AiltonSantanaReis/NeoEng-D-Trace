from __future__ import annotations

import pytest

from src.core.scenario_collider_commands import ColliderEditHistory
from src.core.scenario_colliders import (
    Collider,
    ColliderDocument,
    ColliderError,
    ColliderKind,
)


def _box(identifier: str = "box") -> Collider:
    return Collider(identifier, ColliderKind.BOX, size=(4, 2))


def test_create_move_duplicate_visibility_remove_and_undo_redo_use_deltas() -> None:
    history = ColliderEditHistory(ColliderDocument())
    history.create(_box())
    history.move("box", (10, -4))
    history.duplicate("box", "box-copy")
    history.set_visible("box-copy", False)
    assert history.document.colliders["box"].position == (10.0, -4.0)
    assert history.document.colliders["box-copy"].visible is False

    history.remove("box-copy")
    history.undo()
    assert "box-copy" in history.document.colliders
    history.redo()
    assert "box-copy" not in history.document.colliders

    history.undo()
    history.undo()
    assert history.document.colliders["box-copy"].visible is True


def test_stale_state_rejects_before_mutation_and_clears_redo_after_new_edit() -> None:
    document = ColliderDocument()
    history = ColliderEditHistory(document)
    history.create(_box())
    history.move("box", (2, 0))
    history.undo()
    assert history.can_redo
    history.move("box", (3, 0))
    assert not history.can_redo

    document.colliders["box"] = _box("box")
    with pytest.raises(ColliderError, match="stale_state"):
        history.undo()
    assert document.colliders["box"].position == (0.0, 0.0)


def test_missing_and_empty_history_operations_are_explicit() -> None:
    history = ColliderEditHistory(ColliderDocument())
    with pytest.raises(ColliderError, match="empty_undo"):
        history.undo()
    with pytest.raises(ColliderError, match="missing_id"):
        history.move("missing", (1, 1))
