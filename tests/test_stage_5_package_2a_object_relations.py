from src.core.commands import (
    ClearSceneCommand,
    CommandManager,
    CommandStatus,
    DeleteObjectCommand,
    RenameObjectCommand,
    ToggleCollisionCommand,
    UpdatePolygonCommand,
)
from src.models.scene import Scene


def _square(offset=0):
    return [
        (offset, offset),
        (offset + 20, offset),
        (offset + 20, offset + 20),
        (offset, offset + 20),
    ]


def _scene():
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    return scene


def test_rename_round_trip_preserves_order_references_and_selection():
    scene = _scene()
    scene.add_object("before", _square(), select=True)
    scene.add_object("second", _square(40))
    group = scene.create_group("group")
    group.members = ["before", "second"]
    custom = [(1.25, 2.5), (9.0, 3.0), (4.0, 8.0)]
    scene.collision_shapes["before"] = list(custom)

    result = scene.cmd.execute(
        RenameObjectCommand("before", "after"),
        scene,
    )
    assert result.status is CommandStatus.APPLIED
    assert list(scene.objects) == ["after", "second"]
    assert scene.objects["after"].id == "after"
    assert scene.selected_id == "after"
    assert group.members == ["after", "second"]
    assert scene.collision_shapes["after"] == custom

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["before", "second"]
    assert scene.selected_id == "before"
    assert group.members == ["before", "second"]
    assert scene.collision_shapes["before"] == custom

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["after", "second"]


def test_duplicate_rename_is_rejected_without_history():
    scene = _scene()
    scene.add_object("first", _square())
    scene.add_object("second", _square(40))

    result = scene.cmd.execute(
        RenameObjectCommand("first", "second"),
        scene,
    )
    assert result.status is CommandStatus.REJECTED
    assert list(scene.objects) == ["first", "second"]
    assert scene.cmd.undo_count == 0
    assert scene.cmd.redo_count == 0


def test_delete_round_trip_restores_all_object_relationships():
    scene = _scene()
    scene.add_object("first", _square())
    scene.add_object("target", _square(40), select=True)
    scene.add_object("last", _square(80))
    group_a = scene.create_group("a")
    group_b = scene.create_group("b")
    group_a.members = ["first", "target"]
    group_b.members = ["target", "last"]
    custom = [(41.5, 42.5), (55.0, 44.0), (50.0, 58.0)]
    scene.collision_shapes["target"] = list(custom)

    assert (
        scene.cmd.execute(
            DeleteObjectCommand("target"),
            scene,
        ).status
        is CommandStatus.APPLIED
    )
    assert list(scene.objects) == ["first", "last"]
    assert group_a.members == ["first"]
    assert group_b.members == ["last"]
    assert scene.selected_id is None

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["first", "target", "last"]
    assert scene.collision_shapes["target"] == custom
    assert group_a.members == ["first", "target"]
    assert group_b.members == ["target", "last"]
    assert scene.selected_id == "target"

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["first", "last"]


def test_toggle_collision_restores_exact_custom_shape():
    scene = _scene()
    scene.add_object("object", _square())
    custom = [(2.25, 3.5), (16.0, 5.0), (8.0, 18.5)]
    scene.collision_shapes["object"] = list(custom)

    assert (
        scene.cmd.execute(
            ToggleCollisionCommand("object"),
            scene,
        ).status
        is CommandStatus.APPLIED
    )
    assert "object" not in scene.collision_shapes

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.collision_shapes["object"] == custom

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert "object" not in scene.collision_shapes


def test_polygon_update_restores_exact_prior_collision():
    scene = _scene()
    old_polygon = _square()
    new_polygon = _square(10)
    scene.add_object("object", old_polygon)
    custom = [(0.5, 0.5), (19.5, 1.0), (9.0, 17.0)]
    scene.collision_shapes["object"] = list(custom)

    command = UpdatePolygonCommand(
        "object",
        old_polygon,
        new_polygon,
    )
    assert (
        scene.cmd.execute(
            command,
            scene,
        ).status
        is CommandStatus.APPLIED
    )
    assert scene.objects["object"].polygon == new_polygon
    assert scene.collision_shapes["object"] == [
        (float(x), float(y)) for x, y in new_polygon
    ]

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == old_polygon
    assert scene.collision_shapes["object"] == custom

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene.objects["object"].polygon == new_polygon


def test_stale_polygon_update_is_rejected_without_history():
    scene = _scene()
    scene.add_object("object", _square())

    result = scene.cmd.execute(
        UpdatePolygonCommand(
            "object",
            _square(40),
            _square(80),
        ),
        scene,
    )
    assert result.status is CommandStatus.REJECTED
    assert scene.objects["object"].polygon == _square()
    assert scene.cmd.undo_count == 0


def test_clear_scene_round_trip_restores_removed_state():
    scene = _scene()
    scene.add_object("object", _square(), select=True)
    group = scene.create_group("group")
    group.members = ["object"]
    custom = [(1.0, 1.0), (5.0, 1.0), (3.0, 5.0)]
    scene.collision_shapes["object"] = list(custom)

    assert (
        scene.cmd.execute(
            ClearSceneCommand(),
            scene,
        ).status
        is CommandStatus.APPLIED
    )
    assert scene.objects == {}
    assert scene.groups == []
    assert scene.collision_shapes == {}
    assert scene.selected_id is None

    assert scene.cmd.undo(scene).status is CommandStatus.APPLIED
    assert list(scene.objects) == ["object"]
    assert scene.groups[0].members == ["object"]
    assert scene.collision_shapes["object"] == custom
    assert scene.selected_id == "object"

    assert scene.cmd.redo(scene).status is CommandStatus.APPLIED
    assert scene.objects == {}
