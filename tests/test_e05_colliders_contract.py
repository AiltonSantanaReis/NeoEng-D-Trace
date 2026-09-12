from __future__ import annotations

import math

import pytest

from src.core.scenario_colliders import (
    Collider,
    ColliderDocument,
    ColliderError,
    ColliderKind,
)


def test_all_e05_geometry_kinds_are_explicit_and_serializable() -> None:
    values = (
        Collider("box", ColliderKind.BOX, size=(20, 10)),
        Collider("circle", ColliderKind.CIRCLE, radius=5),
        Collider("polygon", ColliderKind.POLYGON, points=((0, 0), (4, 0), (0, 4))),
        Collider("segment", ColliderKind.SEGMENT, points=((0, 0), (4, 0))),
        Collider("chain", ColliderKind.CHAIN, points=((0, 0), (4, 0), (4, 4))),
    )

    assert [value.kind for value in values] == list(ColliderKind)
    assert values[0].to_dict()["size"] == {"x": 20.0, "y": 10.0}
    assert values[2].to_dict()["points"][-1] == {"x": 0.0, "y": 4.0}


def test_validation_rejects_degenerate_and_nonrepresentable_shapes() -> None:
    cases = (
        ("invalid_box", dict(kind=ColliderKind.BOX, size=(0, 10))),
        ("non_positive", dict(kind=ColliderKind.CIRCLE, radius=0)),
        ("circle_scale", dict(kind=ColliderKind.CIRCLE, radius=2, scale=(2, 1))),
        (
            "invalid_polygon",
            dict(kind=ColliderKind.POLYGON, points=((0, 0), (2, 2), (2, 0))),
        ),
        ("invalid_segment", dict(kind=ColliderKind.SEGMENT, points=((1, 1), (1, 1)))),
        ("invalid_chain", dict(kind=ColliderKind.CHAIN, points=((0, 0), (0, 0)))),
    )
    for code, kwargs in cases:
        with pytest.raises(ColliderError, match=code):
            Collider(code, **kwargs)

    with pytest.raises(ColliderError, match="finite"):
        Collider("nan", ColliderKind.BOX, size=(math.nan, 1))


def test_masks_entities_and_transforms_are_bounded() -> None:
    collider = Collider(
        "trigger",
        ColliderKind.CIRCLE,
        radius=3,
        entity_id="player",
        category=2,
        mask=4,
        is_trigger=True,
        position=(2, -3),
        rotation_degrees=45,
    )
    assert collider.entity_id == "player"
    assert collider.is_trigger is True
    assert collider.position == (2.0, -3.0)

    with pytest.raises(ColliderError, match="65535"):
        Collider("bad-mask", ColliderKind.BOX, size=(1, 1), category=65536)


def test_document_mutations_are_bounded_and_duplicate_safe() -> None:
    document = ColliderDocument()
    box = Collider("box", ColliderKind.BOX, size=(1, 1))
    document.add(box)
    with pytest.raises(ColliderError, match="already exists"):
        document.add(box)
    assert document.remove("box") == box
    with pytest.raises(ColliderError, match="does not exist"):
        document.remove("box")

    with pytest.raises(ColliderError, match="unique"):
        document.replace_all((box, box))
