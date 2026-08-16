from src.core.commands import AddPolygonCommand, CommandManager
from src.models.scene import Scene


def test_create_undo_redo_preserves_multiselection_context():
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object("one", [(0, 0), (10, 0), (10, 10)])
    scene.add_object("two", [(20, 0), (30, 0), (30, 10)])
    scene.select_objects(["one", "two"], primary="two")
    command = AddPolygonCommand([(40, 0), (50, 0), (50, 10)])

    assert scene.cmd.execute(command, scene).changed
    assert scene.cmd.undo(scene).changed
    assert scene.selected_id == "two"
    assert scene.selected_ids == ["one", "two"]
    assert scene.cmd.redo(scene).changed
    assert scene.selected_ids == [command.object_id]
