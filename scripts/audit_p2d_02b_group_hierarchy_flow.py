"""Exercise P2D-02B through the professional scenario editor surface.

The audit drives visible controls and real viewport selection in the same
sequence a user would use: select objects, create/rename groups, create a
subgroup, isolate it, toggle visibility, lock an ancestor, attempt an edit and
save/reload the scene.  It writes only to the caller-provided directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QTreeWidgetItem, QTreeWidgetItemIterator

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow


def _write_fixture_image(path: Path) -> None:
    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2aa8d8"))
    if not image.save(str(path)):
        raise RuntimeError(f"could not write fixture image: {path}")


def _tree_item(window: ScenarioEditorWindow, kind: str, item_id: str) -> QTreeWidgetItem:
    stack = window.group_stack
    if stack is None:
        raise RuntimeError("professional group stack was not initialized")
    cursor = QTreeWidgetItemIterator(stack.tree)
    while cursor.value() is not None:
        item = cursor.value()
        if (
            item.data(0, stack._KIND_ROLE) == kind
            and item.data(0, stack._ID_ROLE) == item_id
        ):
            return item
        cursor += 1
    raise RuntimeError(f"tree item not found: {kind}:{item_id}")


def _snapshot(window: ScenarioEditorWindow) -> dict[str, object]:
    viewport = window.professional_viewport
    stack = window.group_stack
    session = window.professional_session
    if viewport is None or stack is None or session is None:
        raise RuntimeError("professional editor was not initialized")
    return {
        "groups": [
            {
                "id": group.id,
                "name": group.name,
                "parent_group_id": getattr(group, "parent_group_id", None),
                "members": list(group.members),
                "visible": group.visible,
                "locked": group.locked,
            }
            for group in session.document.groups
        ],
        "objects": [item.id for item in session.document.objects],
        "viewport_items": list(viewport._items),
        "isolated_group_id": session.isolated_group_id,
        "selection": list(session.selection.ids),
        "tree_top_level_count": stack.tree.topLevelItemCount(),
        "status": window.status_label.text(),
    }


def run(output: Path) -> dict[str, object]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture_dir = output / "fixture"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    project_path = fixture_dir / "p2d-02b-flow.ndtproj"
    image_path = fixture_dir / "scene.png"
    sidecar_path = project_path.with_suffix(".ndtscene.json")
    if sidecar_path.exists():
        raise RuntimeError("the audit output directory must be new")
    project_path.write_bytes(b"P2D-02B user-flow fixture\n")
    _write_fixture_image(image_path)

    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    scene.image_path = str(image_path)
    scene.add_object(
        "background_object",
        [(-72, -72), (72, -72), (72, 72), (-72, 72)],
        layer_id="layer_default",
    )
    scene.add_object(
        "foreground_object",
        [(0, -48), (48, 0), (0, 48), (-48, 0)],
        layer_id="layer_default",
    )
    scene.add_object(
        "unassigned_object",
        [(-20, -20), (20, -20), (20, 20), (-20, 20)],
        layer_id="layer_default",
    )
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project_path)

    app = QApplication.instance() or QApplication(sys.argv)
    window = ScenarioEditorWindow(authoring, scene)
    window.resize(1280, 820)
    window.show()
    app.processEvents()
    viewport = window.professional_viewport
    stack = window.group_stack
    session = window.professional_session
    if viewport is None or stack is None or session is None:
        raise RuntimeError("professional editor was not initialized")

    captures = output / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "stage": "P2D-02B",
        "qt_platform": os.environ.get("QT_QPA_PLATFORM", ""),
        "resolution": [window.width(), window.height()],
        "captures": [],
    }

    def capture(name: str) -> None:
        path = captures / name
        if not window.grab().save(str(path)):
            raise RuntimeError(f"could not save capture: {path}")
        result["captures"].append(path.name)

    try:
        result["initial"] = _snapshot(window)
        capture("00-initial.png")

        # User flow: select two objects in the viewport and create a group.
        viewport._object_pressed(
            "background_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier
        )
        viewport._object_released("background_object", QPointF(0.0, 0.0))
        viewport._object_pressed(
            "foreground_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.ControlModifier
        )
        viewport._object_released("foreground_object", QPointF(0.0, 0.0))
        app.processEvents()
        result["selection_before_group"] = list(session.selection.ids)
        stack.new_button.click()
        app.processEvents()
        root_id = session.document.groups[0].id
        root_item = _tree_item(window, "group", root_id)
        stack.tree.setCurrentItem(root_item)
        app.processEvents()
        stack.name_edit.setText("Composition")
        stack.name_edit.editingFinished.emit()
        app.processEvents()
        capture("01-group-created.png")

        # User flow: select one member and create a nested subgroup.
        viewport._object_pressed(
            "foreground_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier
        )
        viewport._object_released("foreground_object", QPointF(0.0, 0.0))
        app.processEvents()
        root_item = _tree_item(window, "group", root_id)
        stack.tree.setCurrentItem(root_item)
        app.processEvents()
        viewport._object_pressed(
            "foreground_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier
        )
        viewport._object_released("foreground_object", QPointF(0.0, 0.0))
        app.processEvents()
        stack.new_button.click()
        app.processEvents()
        child = next(
            group for group in session.document.groups if group.id != root_id
        )
        child_item = _tree_item(window, "group", child.id)
        parent_item = child_item.parent()
        result["hierarchy"] = {
            "root_id": root_id,
            "child_id": child.id,
            "child_parent_id": getattr(child, "parent_group_id", None),
            "tree_parent_id": parent_item.data(0, stack._ID_ROLE)
            if parent_item is not None
            else None,
            "child_members": list(child.members),
        }
        capture("02-hierarchy.png")

        # User flow: isolate the subgroup in the viewport.
        stack.tree.setCurrentItem(_tree_item(window, "group", child.id))
        app.processEvents()
        stack.isolate_button.click()
        app.processEvents()
        result["after_isolation"] = _snapshot(window)
        capture("03-isolated-subgroup.png")

        # User flow: restore isolation, hide/show the root group and lock it.
        stack.isolate_button.click()
        app.processEvents()
        stack.tree.setCurrentItem(_tree_item(window, "group", root_id))
        app.processEvents()
        stack.visible_box.click()
        app.processEvents()
        result["after_group_hidden"] = _snapshot(window)
        capture("04-group-hidden.png")
        stack.visible_box.click()
        app.processEvents()
        stack.locked_box.click()
        app.processEvents()

        # User flow: try to edit a member through the viewport and gizmo.
        before_document = session.document
        history_before = session.undo_count
        exception_text = None
        try:
            viewport._object_pressed(
                "foreground_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier
            )
            viewport._object_moved("foreground_object", QPointF(24.0, 24.0))
            viewport._gizmo_started("translate", QPointF(0.0, 0.0))
        except Exception as exc:  # evidence must expose unexpected failures
            exception_text = f"{type(exc).__name__}: {exc}"
        app.processEvents()
        result["locked_attempt"] = {
            "exception": exception_text,
            "document_unchanged": session.document == before_document,
            "history_unchanged": session.undo_count == history_before,
            "gesture_active": session._gesture_before is not None,
            "status": window.status_label.text(),
        }
        result["after_locked_attempt"] = _snapshot(window)
        capture("05-locked-inherited-rejected.png")

        # User flow: save/reload. Isolation must remain transient and flags
        # plus parentage/membership must survive.
        window.save_action.trigger()
        app.processEvents()
        saved = window.professional_scene_path
        result["saved_sidecar"] = saved.name if saved is not None else None
        window.load_action.trigger()
        app.processEvents()
        result["after_reload"] = _snapshot(window)
        capture("06-after-reload.png")
    finally:
        window.close()
        app.processEvents()

    (output / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    hierarchy = report.get("hierarchy", {})
    locked = report.get("locked_attempt", {})
    after_reload = report.get("after_reload", {})
    if (
        hierarchy.get("child_parent_id") != hierarchy.get("root_id")
        or hierarchy.get("tree_parent_id") != hierarchy.get("root_id")
        or locked.get("exception") is not None
        or not locked.get("document_unchanged")
        or not locked.get("history_unchanged")
        or locked.get("gesture_active")
        or after_reload.get("isolated_group_id") is not None
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
