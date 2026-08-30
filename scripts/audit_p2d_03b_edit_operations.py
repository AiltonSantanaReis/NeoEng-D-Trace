"""Audit P2D-03B through the real professional scenario-editor flow.

The audit uses ``ScenarioEditorWindow`` and Qt keyboard events to exercise the
accepted editing contract without touching the legacy canvas.  It records
state transitions, captures, and hashes in a caller-owned directory.  The
output directory must be new so that evidence cannot be silently overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_authoring_clipboard import SCENE_CLIPBOARD_MIME
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow


def _write_fixture_image(path: Path) -> None:
    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(QColor("#2aa8d8"))
    if not image.save(str(path)):
        raise RuntimeError(f"could not write fixture image: {path}")


def _capture(window: ScenarioEditorWindow, captures: Path, name: str) -> dict[str, object]:
    path = captures / name
    if not window.grab().save(str(path)):
        raise RuntimeError(f"could not save capture: {path}")
    raw = path.read_bytes()
    image = QImage(str(path))
    if image.isNull():
        raise RuntimeError(f"could not read capture: {path}")
    return {
        "name": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "pixel_size": [image.width(), image.height()],
        "device_pixel_ratio": image.devicePixelRatio(),
    }


def _selection(window: ScenarioEditorWindow) -> list[str]:
    session = window.professional_session
    if session is None:
        raise RuntimeError("professional session was not initialized")
    return list(session.selection.ids)


def _object_ids(window: ScenarioEditorWindow) -> list[str]:
    session = window.professional_session
    if session is None:
        raise RuntimeError("professional session was not initialized")
    return [item.id for item in session.document.objects]


def _position(window: ScenarioEditorWindow, object_id: str) -> list[float]:
    session = window.professional_session
    if session is None:
        raise RuntimeError("professional session was not initialized")
    item = next(item for item in session.document.objects if item.id == object_id)
    point = item.transform.position
    return [point.x, point.y, point.z]


def _click_scene(window: ScenarioEditorWindow, scene_point: QPointF) -> None:
    viewport = window.professional_viewport
    if viewport is None:
        raise RuntimeError("professional viewport was not initialized")
    QTest.mouseClick(
        viewport.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        viewport.mapFromScene(scene_point),
    )


def _key(window: ScenarioEditorWindow, key: Qt.Key, modifiers=Qt.KeyboardModifier.NoModifier) -> None:
    viewport = window.professional_viewport
    if viewport is None:
        raise RuntimeError("professional viewport was not initialized")
    QTest.keyClick(viewport, key, modifiers)


def _settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(80)
    app.processEvents()


def run(output: Path) -> dict[str, object]:
    output = output.resolve()
    if output.exists():
        raise RuntimeError(f"audit output directory already exists: {output}")
    output.mkdir(parents=True)
    fixture = output / "fixture"
    captures = output / "captures"
    fixture.mkdir()
    captures.mkdir()

    project_path = fixture / "p2d-03b-flow.ndtproj"
    image_path = fixture / "scene.png"
    project_path.write_bytes(b"P2D-03B editing audit fixture\n")
    _write_fixture_image(image_path)

    scene = Scene()
    scene.cmd = CommandManager(max_history=30)
    scene.image_path = str(image_path)
    scene.add_object(
        "a", [(-20, -20), (20, -20), (20, 20), (-20, 20)], layer_id="layer_default"
    )
    scene.add_object(
        "b", [(80, -20), (120, -20), (120, 20), (80, 20)], layer_id="layer_default"
    )
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project_path)

    app = QApplication.instance() or QApplication(sys.argv)
    window = ScenarioEditorWindow(authoring, scene)
    window.resize(1280, 820)
    window.show()
    _settle(app)
    viewport = window.professional_viewport
    session = window.professional_session
    if viewport is None or session is None:
        raise RuntimeError("professional editor was not initialized")

    result: dict[str, object] = {
        "stage": "P2D-03B",
        "qt_platform": os.environ.get("QT_QPA_PLATFORM", ""),
        "resolution": [window.width(), window.height()],
        "device_pixel_ratio": window.devicePixelRatio(),
        "initial_focus": viewport.hasFocus(),
        "captures": [],
        "operations": {},
    }

    def capture(name: str) -> None:
        result["captures"].append(_capture(window, captures, name))

    try:
        capture("00-initial-focus.png")

        _click_scene(window, QPointF(0.0, 0.0))
        _settle(app)
        result["operations"]["click_a"] = {"selection": _selection(window)}
        capture("01-click-a.png")

        _key(window, Qt.Key.Key_Right)
        _settle(app)
        result["operations"]["nudge_right"] = {
            "selection": _selection(window),
            "position_a": _position(window, "a"),
            "undo_count": session.undo_count,
        }
        capture("02-nudge-right.png")

        _key(window, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
        _settle(app)
        result["operations"]["nudge_shift_down"] = {
            "selection": _selection(window),
            "position_a": _position(window, "a"),
            "undo_count": session.undo_count,
        }
        capture("03-nudge-shift-down.png")

        _key(window, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
        _settle(app)
        result["operations"]["duplicate"] = {
            "selection": _selection(window),
            "object_ids": _object_ids(window),
            "position_duplicate": _position(window, "a__copy"),
            "undo_count": session.undo_count,
        }
        capture("04-duplicate.png")

        before_copy = session.snapshot()
        _key(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        _settle(app)
        mime = app.clipboard().mimeData()
        result["operations"]["copy"] = {
            "selection": _selection(window),
            "document_unchanged": session.snapshot() == before_copy,
            "custom_mime_present": mime is not None and mime.hasFormat(SCENE_CLIPBOARD_MIME),
            "undo_count": session.undo_count,
        }
        capture("05-copy.png")

        _key(window, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        _settle(app)
        pasted_id = session.selection.primary
        if pasted_id is None:
            raise RuntimeError("paste did not leave a primary selection")
        result["operations"]["paste"] = {
            "selection": _selection(window),
            "object_ids": _object_ids(window),
            "pasted_id": pasted_id,
            "undo_count": session.undo_count,
        }
        capture("06-paste.png")

        _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        _settle(app)
        result["operations"]["undo_paste"] = {
            "selection": _selection(window),
            "object_ids": _object_ids(window),
            "undo_count": session.undo_count,
            "redo_count": session.redo_count,
        }
        capture("07-undo-paste.png")

        _key(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        _settle(app)
        result["operations"]["redo_paste"] = {
            "selection": _selection(window),
            "object_ids": _object_ids(window),
            "redo_count": session.redo_count,
        }
        capture("08-redo-paste.png")

        _key(window, Qt.Key.Key_Delete)
        _settle(app)
        result["operations"]["delete"] = {
            "selection": _selection(window),
            "object_ids": _object_ids(window),
            "undo_count": session.undo_count,
        }
        capture("09-delete.png")

        _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        _settle(app)
        result["operations"]["undo_delete"] = {
            "selection": _selection(window),
            "object_ids": _object_ids(window),
        }
        capture("10-undo-delete.png")

        if not window._save_professional():
            raise RuntimeError("professional save did not succeed")
        saved_ids = _object_ids(window)
        if not window._load_professional():
            raise RuntimeError("professional reload did not succeed")
        _settle(app)
        result["operations"]["save_reopen"] = {
            "saved_object_ids": saved_ids,
            "reopened_object_ids": _object_ids(window),
            "selection_after_reopen": _selection(window),
            "history_after_reopen": {
                "undo_count": session.undo_count,
                "redo_count": session.redo_count,
            },
        }
        capture("11-save-reopen.png")
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
        clipboard = app.clipboard()
        if clipboard is not None:
            clipboard.clear()
            app.processEvents()

    (output / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    operations = report["operations"]
    expected = {
        "click_a": ["a"],
        "nudge_right": ["a"],
        "nudge_shift_down": ["a"],
        "duplicate": ["a__copy"],
        "copy": True,
        "paste": ["a__copy__copy"],
        "undo_paste": ["a__copy"],
        "redo_paste": ["a__copy__copy"],
        "delete": [],
        "undo_delete": ["a__copy__copy"],
    }
    if not report.get("initial_focus"):
        return 1
    for operation, selection in expected.items():
        if operation == "copy":
            if not operations[operation]["document_unchanged"] or not operations[operation]["custom_mime_present"]:
                return 1
        elif operations[operation]["selection"] != selection:
            return 1
    save_reopen = operations["save_reopen"]
    if save_reopen["saved_object_ids"] != save_reopen["reopened_object_ids"]:
        return 1
    if save_reopen["selection_after_reopen"] != []:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
