from src.models.scene import Scene


def test_removing_non_primary_selection_keeps_selection_ids_valid():
    scene = Scene()
    scene.add_object("one", [(0, 0), (10, 0), (10, 10)])
    scene.add_object("two", [(20, 0), (30, 0), (30, 10)])
    scene.select_objects(["one", "two"], primary="one")

    scene.remove_object("two")

    assert scene.selected_ids == ["one"]
    assert scene.selected_id == "one"


def test_renaming_non_primary_selection_preserves_selection_ids():
    scene = Scene()
    scene.add_object("one", [(0, 0), (10, 0), (10, 10)])
    scene.add_object("two", [(20, 0), (30, 0), (30, 10)])
    scene.select_objects(["one", "two"], primary="one")

    scene.rename_object("two", "renamed")

    assert scene.selected_ids == ["one", "renamed"]
    assert scene.selected_id == "one"
