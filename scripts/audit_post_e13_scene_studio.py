"""Diagnostic-only real Qt captures for the post-E13 scene studio."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.persistence.project_schema import Point3Record
from src.persistence.scene_authoring_schema import SceneLayerAuthoringRecord
from src.ui.scenario_editor_window import ScenarioEditorWindow


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/post-e13-studio-capture")
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="neoeng-studio-") as root:
        root_path = Path(root)
        asset = root_path / "sprite.png"
        image = QImage(240, 150, QImage.Format.Format_RGBA8888)
        image.fill(0xff5b8890)
        image.save(str(asset))
        scene = Scene()
        scene.cmd = CommandManager(max_history=40)
        scene.image_path = str(asset)
        scene.add_object("sprite", [(0, 0), (240, 0), (240, 150), (0, 150)])
        project = root_path / "studio.ndtproj"
        scene.save_project(str(project))
        authoring = ScenarioAuthoringState(scene)
        authoring.bind_project(project)
        window = ScenarioEditorWindow(authoring, scene, language="pt")
        window.resize(1600, 1000)
        window.show()
        app.processEvents()

        captures: list[dict[str, object]] = []

        def capture(name: str) -> None:
            path = output / f"{name}.png"
            window.grab().save(str(path))
            captures.append({"name": name, "path": str(path), "size": [path.stat().st_size]})

        capture("01-loaded-studio")
        session = window.professional_session
        session.add_layer(SceneLayerAuthoringRecord(id="middle", name="Meio"))
        session.add_layer(SceneLayerAuthoringRecord(id="foreground", name="Frente"))
        window.layer_stack.layer_list.setCurrentRow(1)
        window.professional_viewport.place_asset_from_library(session.document.assets[0].id)
        window.sequence_panel.add_clip("camera")
        session.set_selection([session.document.objects[-1].id])
        window.sequence_panel.add_clip("motion")
        app.processEvents()
        capture("02-layers-assets-timeline")
        window.sequence_panel.seek(2.0)
        app.processEvents()
        capture("03-sequence-preview")
        window.sequence_panel.stop_button.click()
        window.professional_inspector.category_tabs.setCurrentIndex(1)
        app.processEvents()
        capture("04-parallax-category")
        metadata = {
            "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
            "window_size": [window.width(), window.height()],
            "captures": captures,
            "layer_count": len(session.document.layers),
            "object_count": len(session.document.objects),
            "sequence_clips": len(session.document.sequence.clips),
            "parallax_layers": len(session.document.parallax_layers),
        }
        (output / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        window.sequence_panel.stop()
        window.close()
        window.deleteLater()
        app.processEvents()
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
