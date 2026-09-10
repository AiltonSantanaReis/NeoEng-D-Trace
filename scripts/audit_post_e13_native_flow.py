"""Native-window flow audit for the post-E13 scene/parallax studio.

This audit deliberately does not set ``QT_QPA_PLATFORM=offscreen``.  It creates
the same Qt windows used by the application, drives real widgets, and captures
the visible native window after each meaningful transition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS


class AuditConfig:
    def get(self, _key: str, default=None):
        return default

    def set(self, _key: str, _value) -> None:
        return None

    def save(self) -> None:
        return None


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fixture_image(path: Path) -> None:
    image = QImage(640, 360, QImage.Format.Format_ARGB32)
    image.fill(QColor("#17324d"))
    for x in range(40, 600, 80):
        for y in range(40, 320, 80):
            image.setPixelColor(x, y, QColor("#58c7d9"))
    if not image.save(str(path), "PNG"):
        raise RuntimeError(f"could not write fixture image: {path}")


def _snapshot(editor) -> dict[str, object]:
    session = editor.professional_session
    if session is None or editor.layer_stack is None or editor.sequence_panel is None:
        raise RuntimeError("native studio did not initialize")
    return {
        "layers": [layer.model_dump(mode="json") for layer in session.document.layers],
        "objects": [obj.model_dump(mode="json") for obj in session.document.objects],
        "parallax": [item.model_dump(mode="json") for item in session.document.parallax_layers],
        "sequence": session.document.sequence.model_dump(mode="json") if session.document.sequence else None,
        "selected_layer": editor.layer_stack.layer_list.currentItem().data(Qt.ItemDataRole.UserRole)
        if editor.layer_stack.layer_list.currentItem() is not None else None,
        "timeline_position": editor.sequence_panel.position,
        "preview_active": editor.sequence_panel.preview is not None,
        "window_visible": editor.isVisible(),
        "window_size": [editor.width(), editor.height()],
    }


def run(output: Path) -> dict[str, object]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture = output / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    project = fixture / "native-studio.ndtproj"
    image = fixture / "scene.png"
    project.write_bytes(b"post-e13-native-studio-fixture-v1\n")
    _write_fixture_image(image)

    scene = Scene()
    scene.cmd = CommandManager(max_history=40)
    scene.image_path = str(image)
    scene.add_object(
        "background_object",
        [(0, 0), (640, 0), (640, 360), (0, 360)],
        layer_id="layer_default",
    )
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    main = MainWindow(scene, AuditConfig())
    main._project_path = project
    main.scenario_authoring.bind_project(project)
    main.scenario_authoring.reset()
    main.show()
    main.open_scenario_editor()
    editor = main.scenario_editor_window
    if editor is None:
        raise RuntimeError("main application did not open the scenario editor")
    editor.resize(QSize(1500, 980))
    editor.show()
    editor.raise_()
    editor.activateWindow()
    app.processEvents()
    QTest.qWait(500)
    app.processEvents()

    capture_dir = output / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, object]] = []

    def capture(name: str, action: str) -> None:
        path = capture_dir / name
        if not editor.grab().save(str(path), "PNG"):
            raise RuntimeError(f"could not save native capture: {path}")
        events.append({"action": action, "capture": name, "sha256": _digest(path), "state": _snapshot(editor)})

    capture("01-native-loaded.png", "open project and scenario editor")
    stack = editor.layer_stack
    inspector = editor.professional_inspector
    sequence = editor.sequence_panel
    viewport = editor.professional_viewport
    library = editor.asset_library
    if stack is None or inspector is None or sequence is None or viewport is None or library is None:
        raise RuntimeError("native studio panels are incomplete")

    # Real widget flow: create and name a depth frame, then reorder it.
    stack.add_button.click()
    app.processEvents()
    stack.layer_list.setCurrentRow(stack.layer_list.count() - 1)
    stack.name_edit.setText("Moldura Meio")
    stack.name_edit.editingFinished.emit()
    stack.up_button.click()
    app.processEvents()
    capture("02-native-frame-reorder.png", "add, rename and reorder depth frame")

    # Real widget flow: select the layer inspector and apply parallax values.
    layer_id = stack.layer_list.currentItem().data(Qt.ItemDataRole.UserRole)
    index = inspector.layer_combo.findData(layer_id)
    inspector.layer_combo.setCurrentIndex(index)
    inspector.parallax_depth.setValue(0.65)
    inspector.parallax_translation.setValue(0.35)
    inspector.parallax_scroll_x.setValue(0.40)
    inspector.parallax_scroll_y.setValue(0.15)
    inspector.parallax_apply_button.click()
    app.processEvents()
    capture("03-native-parallax-applied.png", "apply layer parallax inspector values")

    # Real asset path through the library-to-viewport integration.
    if library.asset_list.count() == 0:
        raise RuntimeError("asset library did not expose the fixture asset")
    library.asset_list.setCurrentRow(0)
    asset_id = library.selected_asset_id
    if not asset_id:
        raise RuntimeError("fixture asset selection did not resolve an id")
    viewport.set_active_layer(layer_id)
    if not viewport.place_asset_from_library(asset_id):
        raise RuntimeError("asset placement was not accepted by the native viewport")
    app.processEvents()
    capture("04-native-asset-placed.png", "select library asset and place into active frame")

    # Real timeline flow: add camera and particle clips, seek, play, pause and stop.
    sequence.kind.setCurrentIndex(sequence.kind.findData("camera"))
    sequence.add_button.click()
    sequence.kind.setCurrentIndex(sequence.kind.findData("rain"))
    sequence.add_button.click()
    app.processEvents()
    sequence.seek(1.25)
    if not sequence.preview:
        raise RuntimeError("timeline seek did not create a preview viewport")
    capture("05-native-timeline-seek.png", "add timeline clips and seek preview")
    sequence.play.click()
    QTest.qWait(180)
    sequence.play.click()
    played_position = sequence.position
    sequence.stop_button.click()
    app.processEvents()
    if played_position <= 1.25:
        raise RuntimeError("timeline play did not advance the native position")
    capture("06-native-timeline-play-pause-stop.png", "play, pause and stop timeline")

    # Persistence flow: save, close the editor, reopen it and compare authored data.
    saved_before = _snapshot(editor)
    if not editor._save_professional():
        raise RuntimeError("native professional save returned false")
    sidecar = project.with_suffix(".ndtscene.json")
    if not sidecar.is_file():
        raise RuntimeError("native save did not create the authoring sidecar")
    editor.close()
    app.processEvents()
    main.open_scenario_editor()
    reopened = main.scenario_editor_window
    if reopened is None:
        raise RuntimeError("native scenario editor did not reopen")
    reopened.resize(QSize(1500, 980))
    reopened.show()
    reopened.raise_()
    reopened.activateWindow()
    app.processEvents()
    QTest.qWait(450)
    after_reopen = _snapshot(reopened)
    if after_reopen["parallax"] != saved_before["parallax"]:
        raise RuntimeError("parallax data changed after native save/reopen")
    if after_reopen["sequence"] != saved_before["sequence"]:
        raise RuntimeError("sequence data changed after native save/reopen")
    if not after_reopen["window_visible"]:
        raise RuntimeError("reopened native editor is not visible")
    path = capture_dir / "07-native-reopened-persisted.png"
    if not reopened.grab().save(str(path), "PNG"):
        raise RuntimeError("could not save reopened native capture")
    events.append({"action": "save, close, reopen and verify persisted document", "capture": path.name, "sha256": _digest(path), "state": after_reopen})

    manifest = {
        "status": "PASS",
        "scope": "post-E13 studio native source execution and user-flow harness",
        "qt_platform": os.environ.get("QT_QPA_PLATFORM", "native-default"),
        "native_window": True,
        "process_id": os.getpid(),
        "fixture_project": str(project.relative_to(output)),
        "fixture_asset": str(image.relative_to(output)),
        "sidecar": str(sidecar.relative_to(output)),
        "events": events,
        "source_commit": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], text=True).strip(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    reopened.close()
    main.close()
    app.processEvents()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
