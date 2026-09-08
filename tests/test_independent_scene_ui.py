"""Offscreen Qt tests for the real independent-scene user flow."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.independent_scene_window import IndependentSceneWindow


@pytest.fixture
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_independent_scene_window_new_save_save_as_reopen(
    tmp_path: Path,
    qt_app: QApplication,
) -> None:
    window = IndependentSceneWindow(language="pt")
    window.show()
    qt_app.processEvents()

    window.width_spin.setValue(1280)
    window.height_spin.setValue(720)
    window.camera_x_spin.setValue(18.5)
    window.zoom_spin.setValue(1.25)
    first = tmp_path / "flow.ndtscene"
    assert window._save_to(first)
    assert first.is_file()
    assert not window.session.is_modified
    assert "1280 × 720" in window.canvas_label.text()

    window.width_spin.setValue(800)
    second = tmp_path / "flow-copy.ndtscene"
    assert window._save_to(second)
    assert second.is_file()

    reopened = IndependentSceneWindow(language="en")
    reopened.show()
    assert reopened.session.load(second).resolution.width == 800
    reopened.refresh()
    qt_app.processEvents()
    assert reopened.width_spin.value() == 800
    assert reopened.camera_x_spin.value() == 18.5
    assert reopened.windowTitle().startswith("Independent Scene")

    reopened.close()
    window.close()


def test_independent_scene_window_is_reachable_from_main_window(
    qt_app: QApplication,
) -> None:
    from src.models.scene import Scene
    from src.ui.main_window import MainWindow

    main = MainWindow(Scene(), {})
    assert main.open_independent_scene()
    child = main._independent_scene_window
    assert child is not None
    assert child.session.path is None
    assert child.session.document.resolution.width == 1920
    child.close()
    main.close()


def test_independent_scene_action_opens_the_real_child_window(
    qt_app: QApplication,
) -> None:
    from src.models.scene import Scene
    from src.ui.main_window import MainWindow

    main = MainWindow(Scene(), {})
    main.open_independent_scene_action.trigger()
    qt_app.processEvents()

    child = main._independent_scene_window
    assert child is not None
    assert child.isVisible()
    assert child.windowTitle().startswith(("Independent Scene", "Novo Cenário"))

    child.close()
    main.close()


def test_independent_scene_save_as_cancel_preserves_unsaved_document(
    monkeypatch,
    qt_app: QApplication,
) -> None:
    from src.ui import independent_scene_window as window_module

    window = IndependentSceneWindow(language="pt")
    window.show()
    window.width_spin.setValue(1280)
    assert window.session.is_modified
    monkeypatch.setattr(
        window_module.QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *args, **kwargs: ("", "")),
    )

    assert window.save_scene_as() is False
    assert window.session.path is None
    assert window.session.is_modified
    window.session.new()
    window.close()


def test_independent_scene_window_creates_primitives_and_history(
    qt_app: QApplication,
) -> None:
    window = IndependentSceneWindow(language="pt")
    window.show()
    qt_app.processEvents()

    assert window.create_primitive("rectangle")
    assert window.create_primitive("ellipse")
    assert window.create_primitive("polygon")
    assert window.object_count == 3
    qt_app.processEvents()
    assert window.canvas.object_count == 3
    assert window.object_list.count() == 3
    assert window.object_list.item(0).text().startswith("Retângulo · rectangle")
    assert window.object_list.item(1).text().startswith("Elipse · ellipse")
    assert window.object_list.item(2).text().startswith("Polígono · polygon")
    assert window.rectangle_action.text() == "Retângulo"
    assert window.polygon_action.text() == "Polígono"
    assert window.rectangle_action.shortcut().toString() == "Ctrl+Shift+R"
    assert window.polygon_action.shortcut().toString() == "Ctrl+Shift+P"
    assert window.remove_action.shortcut().toString() == "Ctrl+Shift+Del"
    assert window.undo_action.isEnabled()

    assert window.undo_scene()
    assert window.object_count == 2
    assert window.redo_scene()
    assert window.object_count == 3

    window.session.new()
    window.close()


def test_independent_scene_window_selection_transform_duplicate_remove_reopen(
    tmp_path: Path,
    qt_app: QApplication,
) -> None:
    window = IndependentSceneWindow(language="pt")
    window.show()
    window.create_primitive("rectangle")
    window.create_primitive("ellipse")
    window.create_primitive("polygon")
    qt_app.processEvents()

    window.object_list.clearSelection()
    window.object_list.item(0).setSelected(True)
    qt_app.processEvents()
    selected_id = window.object_list.item(0).data(Qt.ItemDataRole.UserRole)
    assert window.session.selection == (selected_id,)
    assert window.canvas.selected_ids == (selected_id,)

    window.object_x_spin.setValue(42.0)
    qt_app.processEvents()
    selected = window.session.document.objects[0]
    assert selected.transform.position.x == 42.0

    assert window.duplicate_selected()
    assert window.object_count == 4
    assert window.remove_selected()
    assert window.object_count == 3

    path = tmp_path / "authoring-flow.ndtscene"
    assert window._save_to(path)
    reopened = IndependentSceneWindow(language="en")
    reopened.session.load(path)
    reopened.refresh()
    qt_app.processEvents()
    assert reopened.object_count == 3
    assert [item.geometry.kind for item in reopened.session.document.objects] == [
        "rectangle",
        "ellipse",
        "polygon",
    ]
    assert reopened.session.document.objects[0].transform.position.x == 42.0

    reopened.close()
    window.close()


def test_independent_scene_window_point_edit_commit_and_cancel(
    qt_app: QApplication,
) -> None:
    window = IndependentSceneWindow(language="pt")
    window.show()
    window.create_primitive("polygon")
    qt_app.processEvents()
    original = tuple(window.session.document.objects[0].geometry.points)

    assert window.toggle_point_edit()
    assert window.point_edit_active
    assert window.edit_action.text() == "Editar pontos"
    window._preview_point(1, original[1].model_copy(update={"x": original[1].x + 50}))
    assert window.finalize_point_edit()
    assert window.session.document.objects[0].geometry.points[1].x == original[1].x + 50

    assert window.toggle_point_edit()
    window._preview_point(1, original[1])
    assert window.cancel_point_edit()
    assert window.session.document.objects[0].geometry.points[1].x == original[1].x + 50
    window.session.new()
    window.close()
