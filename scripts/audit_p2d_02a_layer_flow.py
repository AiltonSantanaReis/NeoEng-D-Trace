"""Exercise the P2D-02A flow through the professional Qt editor surface.

The script intentionally drives the same visible controls a user would use:
the layer list, Up button, visibility/lock controls, Save and Reload actions.
It writes only to the caller-provided evidence directory.
"""

from __future__ import annotations

import argparse
import os
import json
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow


def _write_fixture_image(path: Path) -> None:
    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2aa8d8"))
    if not image.save(str(path)):
        raise RuntimeError(f"could not write fixture image: {path}")


def _snapshot(window: ScenarioEditorWindow) -> dict[str, object]:
    viewport = window.professional_viewport
    stack = window.layer_stack
    session = window.professional_session
    if viewport is None or stack is None or session is None:
        raise RuntimeError("professional editor was not initialized")
    return {
        "layers": [layer.id for layer in session.document.layers],
        "objects": [item.id for item in session.document.objects],
        "viewport_items": list(viewport._items),
        "z_values": {
            object_id: visual.zValue()
            for object_id, visual in viewport._items.items()
        },
        "selected_layer": stack.layer_list.currentItem().data(
            Qt.ItemDataRole.UserRole
        )
        if stack.layer_list.currentItem() is not None
        else None,
        "status": window.status_label.text(),
    }


def run(output: Path) -> dict[str, object]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture_dir = output / "fixture"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    project_path = fixture_dir / "p2d-02a-flow.ndtproj"
    image_path = fixture_dir / "scene.png"
    sidecar_path = project_path.with_suffix(".ndtscene.json")
    if sidecar_path.exists():
        raise RuntimeError("the audit output directory must be new")
    project_path.write_bytes(b"P2D-02A user-flow fixture\n")
    _write_fixture_image(image_path)

    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image_path)
    scene.add_object(
        "background_object",
        [(-72, -72), (72, -72), (72, 72), (-72, 72)],
        layer_id="layer_default",
    )
    foreground_layer = scene.create_layer("Foreground")
    scene.add_object(
        "foreground_object",
        [(0, -48), (48, 0), (0, 48), (-48, 0)],
        layer_id=foreground_layer.id,
    )
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project_path)

    app = QApplication.instance() or QApplication(sys.argv)
    window = ScenarioEditorWindow(authoring, scene)
    window.resize(1280, 820)
    window.show()
    app.processEvents()
    viewport = window.professional_viewport
    stack = window.layer_stack
    session = window.professional_session
    if viewport is None or stack is None or session is None:
        raise RuntimeError("professional editor was not initialized")

    captures = output / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "stage": "P2D-02A",
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

        # User flow: select the foreground layer and move it toward the back.
        stack.layer_list.setCurrentRow(1)
        stack.up_button.click()
        app.processEvents()
        result["after_reorder"] = _snapshot(window)
        capture("01-after-reorder.png")

        # User flow: hide and restore the selected layer.
        stack.visible_box.click()
        app.processEvents()
        result["after_visibility_off"] = _snapshot(window)
        capture("02-layer-hidden.png")
        stack.visible_box.click()
        app.processEvents()

        # User flow: lock the selected layer and attempt to move its object.
        stack.locked_box.click()
        app.processEvents()
        before = session.document
        history_before = session.undo_count
        exception_text = None
        try:
            viewport._object_pressed(
                "foreground_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier
            )
            viewport._object_moved("foreground_object", QPointF(24.0, 24.0))
            viewport._gizmo_started("translate", QPointF(0.0, 0.0))
        except Exception as exc:  # evidence must make unexpected failures explicit
            exception_text = f"{type(exc).__name__}: {exc}"
        app.processEvents()
        result["locked_attempt"] = {
            "exception": exception_text,
            "document_unchanged": session.document == before,
            "history_unchanged": session.undo_count == history_before,
            "gesture_active": session._gesture_before is not None,
            "status": window.status_label.text(),
        }
        result["after_locked_attempt"] = _snapshot(window)
        capture("03-locked-rejected.png")

        # User flow: save, reload and verify that ordering/lock state survives.
        window.save_action.trigger()
        app.processEvents()
        saved = window.professional_scene_path
        result["saved_sidecar"] = saved.name if saved is not None else None
        window.load_action.trigger()
        app.processEvents()
        result["after_reload"] = _snapshot(window)
        capture("04-after-reload.png")
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
    locked = report.get("locked_attempt", {})
    if (
        locked.get("exception") is not None
        or not locked.get("document_unchanged")
        or not locked.get("history_unchanged")
        or locked.get("gesture_active")
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
