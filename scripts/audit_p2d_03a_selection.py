"""Audit P2D-03A through the real professional scenario-editor flow.

The audit uses the visible ``ScenarioEditorWindow`` and Qt input events to
exercise deterministic selection, focus, empty-click clearing, marquee
containment/intersection and select-all.  It writes only to the caller-owned
output directory and refuses to reuse an existing directory.
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


def _click_scene(
    window: ScenarioEditorWindow,
    scene_point: QPointF,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    viewport = window.professional_viewport
    if viewport is None:
        raise RuntimeError("professional viewport was not initialized")
    QTest.mouseClick(
        viewport.viewport(),
        Qt.MouseButton.LeftButton,
        modifiers,
        viewport.mapFromScene(scene_point),
    )


def _marquee_scene(
    window: ScenarioEditorWindow,
    origin: QPointF,
    current: QPointF,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    viewport = window.professional_viewport
    if viewport is None:
        raise RuntimeError("professional viewport was not initialized")
    start = viewport.mapFromScene(origin)
    end = viewport.mapFromScene(current)
    QTest.mousePress(
        viewport.viewport(),
        Qt.MouseButton.LeftButton,
        modifiers,
        start,
    )
    QTest.mouseMove(viewport.viewport(), end)
    QTest.mouseRelease(
        viewport.viewport(),
        Qt.MouseButton.LeftButton,
        modifiers,
        end,
    )


def run(output: Path) -> dict[str, object]:
    output = output.resolve()
    if output.exists():
        raise RuntimeError(f"audit output directory already exists: {output}")
    output.mkdir(parents=True)
    fixture = output / "fixture"
    captures = output / "captures"
    fixture.mkdir()
    captures.mkdir()

    project_path = fixture / "p2d-03a-flow.ndtproj"
    image_path = fixture / "scene.png"
    project_path.write_bytes(b"P2D-03A selection audit fixture\n")
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
    scene.add_object(
        "c", [(180, -20), (220, -20), (220, 20), (180, 20)], layer_id="layer_default"
    )
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project_path)

    app = QApplication.instance() or QApplication(sys.argv)
    window = ScenarioEditorWindow(authoring, scene)
    window.resize(1280, 820)
    window.show()
    app.processEvents()
    viewport = window.professional_viewport
    if viewport is None or window.professional_session is None:
        raise RuntimeError("professional editor was not initialized")

    result: dict[str, object] = {
        "stage": "P2D-03A",
        "qt_platform": os.environ.get("QT_QPA_PLATFORM", ""),
        "resolution": [window.width(), window.height()],
        "device_pixel_ratio": window.devicePixelRatio(),
        "initial_focus": viewport.hasFocus(),
        "captures": [],
    }

    try:
        result["captures"].append(_capture(window, captures, "00-initial-focus.png"))

        _click_scene(window, QPointF(0.0, 0.0))
        result["click_a"] = _selection(window)
        result["captures"].append(_capture(window, captures, "01-click-a.png"))

        _click_scene(window, QPointF(100.0, 0.0), Qt.KeyboardModifier.ControlModifier)
        _click_scene(window, QPointF(200.0, 0.0), Qt.KeyboardModifier.ShiftModifier)
        result["ctrl_shift_selection"] = _selection(window)
        result["captures"].append(_capture(window, captures, "02-ctrl-shift-selection.png"))

        _marquee_scene(window, QPointF(-30.0, -30.0), QPointF(30.0, 30.0))
        result["marquee_left_to_right"] = _selection(window)
        result["captures"].append(_capture(window, captures, "03-marquee-contained.png"))

        _marquee_scene(window, QPointF(125.0, 10.0), QPointF(105.0, -10.0))
        result["marquee_right_to_left"] = _selection(window)
        result["captures"].append(_capture(window, captures, "04-marquee-intersected.png"))

        _click_scene(window, QPointF(300.0, 120.0))
        result["empty_click_selection"] = _selection(window)
        result["captures"].append(_capture(window, captures, "05-empty-click.png"))

        QTest.keyClick(viewport, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        result["select_all"] = _selection(window)
        result["captures"].append(_capture(window, captures, "06-select-all.png"))
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
    if (
        not report.get("initial_focus")
        or report.get("click_a") != ["a"]
        or report.get("ctrl_shift_selection") != ["b", "c"]
        or report.get("marquee_left_to_right") != ["a"]
        or report.get("marquee_right_to_left") != ["b"]
        or report.get("empty_click_selection") != []
        or report.get("select_all") != ["a", "b", "c"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
