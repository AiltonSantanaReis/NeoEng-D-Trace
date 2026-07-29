from src.core.commands import CommandManager, CreateObjectCommand
from src.models.scene import Scene


SQUARE = [(0, 0), (20, 0), (20, 20), (0, 20)]


def test_add_polygon_selects_new_object_with_one_notification():
    scene = Scene()
    notifications = []
    scene.subscribe(lambda: notifications.append(scene.selected_id))

    object_id = scene.add_polygon(SQUARE)

    assert scene.selected_id == object_id
    assert object_id in scene.objects
    assert notifications == [object_id]


def test_add_object_does_not_select_imported_object_by_default():
    scene = Scene()

    scene.add_object("imported-object", SQUARE)

    assert scene.selected_id is None


def test_create_object_command_selects_object_on_execute_and_redo():
    scene = Scene()
    manager = CommandManager()
    command = CreateObjectCommand(SQUARE)

    manager.execute(command, scene)
    first_id = command.object_id
    assert scene.selected_id == first_id

    manager.undo(scene)
    assert scene.selected_id is None
    assert first_id not in scene.objects

    manager.redo(scene)
    assert command.object_id == first_id
    assert scene.selected_id == first_id
    assert first_id in scene.objects
