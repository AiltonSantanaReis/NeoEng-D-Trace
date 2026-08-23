"""Capture and audit the dedicated professional scenario editor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image
from PySide6.QtCore import QPoint
from PySide6.QtGui import QFont, QFontDatabase, QImage
from PySide6.QtWidgets import QApplication, QWidget

from scripts.audit_visual_artifacts import run_audit
from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow
from src.ui.theme_qss import QSS


def _digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def _source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _rect(widget: QWidget, window: ScenarioEditorWindow) -> dict[str, Any]:
    position = widget.mapTo(window, QPoint(0, 0))
    geometry = widget.geometry()
    return {
        "geometry": [0, 0, geometry.width(), geometry.height()],
        "root_geometry": [
            position.x(),
            position.y(),
            geometry.width(),
            geometry.height(),
        ],
        "visible": bool(widget.isVisible()),
    }


def _geometry(window: ScenarioEditorWindow, *, profile: str) -> dict[str, Any]:
    names = [
        "scenario_editor_toolbar",
        "scenario_editor_splitter",
        "professional_viewport_pages",
        "scenario_right_pages",
    ]
    if profile == "professional_scene_editor":
        names.extend(
            (
                "professional_scene_viewport",
                "professional_inspector_scroll",
                "professional_scene_inspector",
            )
        )
    records = {}
    for name in names:
        widget = window.findChild(QWidget, name)
        if widget is None:
            raise RuntimeError(f"required Qt widget not found: {name}")
        records[name] = _rect(widget, window)
    if profile == "professional_scene_editor":
        records["professional_inspector_scroll"]["scroll_area"] = True
        records["professional_scene_inspector"]["scrollable"] = True
        records["professional_scene_inspector"][
            "scroll_area_parent"
        ] = "professional_inspector_scroll"
    return {"profile": profile, "professional_editor": records}


def _configure_capture_font(app: QApplication) -> None:
    windows_dir = Path(os.environ.get("WINDIR", "C:/Windows"))
    font_path = windows_dir / "Fonts" / "arial.ttf"
    if not font_path.is_file():
        raise RuntimeError("the QSS font Arial is not available on this Windows host")
    if QFontDatabase.addApplicationFont(str(font_path)) < 0:
        raise RuntimeError("Qt could not load the existing Arial font for capture")
    app.setFont(QFont("Arial", 10))


def _fixture(root: Path) -> tuple[Path, Scene, ScenarioAuthoringState]:
    project = root / "scenario.ndtproj"
    project.write_bytes(b"stage8-real-project")
    image_path = root / "scenario.png"
    image = QImage(96, 64, QImage.Format.Format_RGBA8888)
    image.fill(0xFF24435A)
    if not image.save(str(image_path)):
        raise RuntimeError("could not create the real Qt image fixture")
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image_path)
    scene.add_object("scenario_object", [(0, 0), (96, 0), (96, 64), (0, 64)])
    authoring = ScenarioAuthoringState(scene)
    return project, scene, authoring


def _capture(
    window: ScenarioEditorWindow,
    output: Path,
    name: str,
    size: tuple[int, int],
    *,
    profile: str,
) -> dict[str, Any]:
    window.resize(*size)
    window.show()
    QApplication.processEvents()
    path = output / name
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"Qt grab failed: {name}")
    with Image.open(path) as image:
        image.verify()
        if image.size != size:
            raise RuntimeError(f"capture size mismatch for {name}: {image.size}")
    return {
        "actual_capture_size": list(size),
        "files": {name: _digest(path)},
        "widget_geometry": _geometry(window, profile=profile),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    _configure_capture_font(app)
    app.setStyleSheet(QSS)

    with tempfile.TemporaryDirectory(prefix="neoeng_stage8_") as temp:
        project, scene, authoring = _fixture(Path(temp))
        window = ScenarioEditorWindow(authoring, scene)
        window.show()
        app.processEvents()
        captures = {
            "scenario_empty": _capture(
                window,
                output,
                "stage8_01_scenario_empty.png",
                (1280, 720),
                profile="professional_scene_empty",
            )
        }
        authoring.bind_project(project)
        app.processEvents()
        captures["scenario_authoring"] = _capture(
            window,
            output,
            "stage8_02_scenario_authoring.png",
            (1280, 720),
            profile="professional_scene_editor",
        )
        window.overlay_action.setChecked(True)
        window._toggle_overlays()
        captures["scenario_overlays"] = _capture(
            window,
            output,
            "stage8_03_scenario_overlays.png",
            (1366, 768),
            profile="professional_scene_editor",
        )
        window.preview_action.trigger()
        app.processEvents()
        captures["scenario_preview"] = _capture(
            window,
            output,
            "stage8_04_scenario_preview.png",
            (1920, 1080),
            profile="professional_scene_editor",
        )
        fixture = output / "ui-audit-fixture.png"
        fixture_image = QImage(8, 8, QImage.Format.Format_RGBA8888)
        fixture_image.fill(0xFF336699)
        if not fixture_image.save(str(fixture), "PNG"):
            raise RuntimeError("fixture PNG save failed")
        manifest = {
            "schema_version": 2,
            "purpose": "stage8-dedicated-scenario-editor",
            "source": _source_state(),
            "captures": captures,
            "image_fixture": _digest(fixture),
        }
        manifest_path = output / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        report = run_audit(output, output.parent / (output.name + "-annotated"))
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "finding_count": report["finding_count"],
                    "manifest_sha256": _digest(manifest_path)["sha256"],
                    "source_commit": manifest["source"]["commit"],
                    "worktree_clean": manifest["source"]["worktree_clean"],
                },
                sort_keys=True,
            )
        )
        window.close()
        return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
