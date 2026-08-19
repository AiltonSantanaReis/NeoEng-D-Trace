"""Capture and audit the Stage 3 professional scene editor.

The fixture is created inside a temporary directory and contains no user data.
The screenshots are produced by the real PySide6 widgets in offscreen mode;
the existing visual auditor then validates Pillow/OpenCV decoding, hashes,
dimensions, transparency, clipping, Qt geometry, overlap and QSS colors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

from PIL import Image
from PySide6.QtCore import QPoint, QRect, QRectF
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QWidget

from scripts.audit_visual_artifacts import run_audit
from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow
from src.ui.theme_qss import QSS

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git_state() -> dict[str, Any]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    return {
        "source_commit": head,
        "worktree_clean_at_capture_start": not bool(status.strip()),
    }


def _rect(value: QRect | QRectF) -> list[int]:
    return [int(value.x()), int(value.y()), int(value.width()), int(value.height())]


def _widget_record(widget: QWidget, root: QWidget) -> dict[str, Any]:
    return {
        "class": widget.metaObject().className(),
        "object_name": widget.objectName(),
        "visible": widget.isVisible(),
        "enabled": widget.isEnabled(),
        "geometry": _rect(widget.geometry()),
        "root_geometry": _rect(QRect(widget.mapTo(root, QPoint(0, 0)), widget.size())),
        "frame_geometry": _rect(widget.frameGeometry()),
    }


def _geometry(window: ScenarioEditorWindow) -> dict[str, Any]:
    root = window
    widgets = {
        "professional_viewport_pages": window.professional_pages,
        "scenario_right_pages": window.right_pages,
        "professional_viewport": window.professional_viewport,
        "professional_inspector": window.professional_inspector,
        "scenario_editor_splitter": window.centralWidget(),
        "scenario_editor_toolbar": window.toolbar,
    }
    profile = (
        "professional_scene_editor"
        if window.professional_session is not None
        else "professional_scene_empty"
    )
    return {
        "profile": profile,
        "professional_editor": {
            name: _widget_record(widget, root)
            for name, widget in widgets.items()
            if widget is not None
        },
    }


def _create_fixture(root: Path) -> tuple[Path, Path, Scene]:
    project = root / "fixture.ndtproj"
    project.write_bytes(b"stage3-fixture-project-v1\n")
    image_path = root / "assets" / "fixture.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(160, 100, QImage.Format.Format_RGBA8888)
    image.fill(0xFF204060)
    assert image.save(str(image_path))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image_path)
    scene.add_object("fixture_object", [(20, 20), (120, 20), (120, 80), (20, 80)])
    return project, image_path, scene


def _capture(
    window: ScenarioEditorWindow, path: Path, size: tuple[int, int]
) -> dict[str, Any]:
    window.resize(*size)
    window.show()
    QApplication.processEvents()
    assert window.size().width() == size[0] and window.size().height() == size[1]
    assert window.grab().save(str(path), "PNG")
    with Image.open(path) as image:
        image.verify()
        actual_size = [image.width, image.height]
    return {
        "requested_size": list(size),
        "actual_window_size": [window.width(), window.height()],
        "actual_capture_size": actual_size,
        "files": {path.name: _digest(path)},
        "widget_geometry": _geometry(window),
    }


def capture(output: Path) -> dict[str, Any]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    provenance = _git_state()
    capture_dir = output / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    captures: dict[str, Any] = {}
    app = QApplication.instance() or QApplication(sys.argv)
    cast(QApplication, app).setStyleSheet(QSS)
    with tempfile.TemporaryDirectory(prefix="neoeng-stage3-") as temp:
        project, image_path, scene = _create_fixture(Path(temp))
        authoring = ScenarioAuthoringState(scene)

        empty_window = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            captures["empty"] = _capture(
                empty_window,
                capture_dir / "stage3_01_sem_projeto.png",
                (1280, 720),
            )
        finally:
            empty_window.close()

        authoring.bind_project(project)
        loaded_window = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            session = loaded_window.professional_session
            inspector = loaded_window.professional_inspector
            assert session is not None
            assert inspector is not None
            session.set_selection(["fixture_object"])
            QApplication.processEvents()
            captures["loaded"] = _capture(
                loaded_window,
                capture_dir / "stage3_02_projeto_paineis.png",
                (1280, 720),
            )
            inspector.position_x.setValue(35.0)
            inspector.apply_transform()
            QApplication.processEvents()
            assert session.document.objects[0].transform.position.x == 35.0
            captures["transformed"] = _capture(
                loaded_window,
                capture_dir / "stage3_04_gizmo_feedback.png",
                (1280, 720),
            )
        finally:
            loaded_window.close()
        del image_path

    manifest = {
        "schema_version": 2,
        "generator": "scripts/audit_stage3_professional_editor_capture.py",
        **provenance,
        "privacy": {"absolute_paths_persisted": False, "fixture_is_temporary": True},
        "captures": captures,
    }
    manifest_path = capture_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report = run_audit(capture_dir, output / "audited")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = capture(args.output)
    print(
        json.dumps(
            {"status": report["status"], "finding_count": report["finding_count"]},
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
