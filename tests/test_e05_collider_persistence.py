from __future__ import annotations

import json

import pytest

from src.core.scenario_collider_queries import check_overlap
from src.core.scenario_colliders import Collider, ColliderDocument, ColliderKind
from src.persistence.scenario_collider_io import (
    COLLIDER_FORMAT_ID,
    ColliderPersistenceError,
    load_colliders,
    save_colliders,
)


def test_save_reopen_preserves_independent_colliders_and_trigger_consumer(
    tmp_path,
) -> None:
    document = ColliderDocument()
    document.add(Collider("wall", ColliderKind.BOX, size=(8, 2), position=(2, 0)))
    document.add(
        Collider(
            "sensor", ColliderKind.CIRCLE, radius=2, position=(2, 0), is_trigger=True
        )
    )
    path = save_colliders(document, tmp_path / "scenario.colliders.json")
    reopened = load_colliders(path)

    assert set(reopened.colliders) == {"wall", "sensor"}
    contact = check_overlap(reopened.colliders["wall"], reopened.colliders["sensor"])
    assert contact.overlaps is True
    assert contact.trigger is True


def test_loader_rejects_unknown_format_duplicate_ids_and_invalid_geometry(
    tmp_path,
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps({"format_id": "other", "schema_version": 1}), encoding="utf-8"
    )
    with pytest.raises(ColliderPersistenceError, match="unsupported_format"):
        load_colliders(path)

    duplicate = {
        "format_id": COLLIDER_FORMAT_ID,
        "schema_version": 1,
        "id": "scenario-colliders",
        "version": 1,
        "colliders": [
            Collider("same", ColliderKind.BOX, size=(1, 1)).to_dict(),
            Collider("same", ColliderKind.BOX, size=(2, 2)).to_dict(),
        ],
    }
    path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ColliderPersistenceError, match="duplicate_id"):
        load_colliders(path)

    invalid = Collider("bad", ColliderKind.BOX, size=(1, 1)).to_dict()
    invalid["size"] = {"x": 0, "y": 1}
    duplicate["colliders"] = [invalid]
    path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ColliderPersistenceError, match="invalid_box"):
        load_colliders(path)


def test_category_mask_can_block_a_contact_before_consumer_reports_it() -> None:
    first = Collider("first", ColliderKind.BOX, size=(2, 2), category=2, mask=4)
    second = Collider("second", ColliderKind.BOX, size=(2, 2), category=8, mask=2)
    assert check_overlap(first, second).overlaps is False
