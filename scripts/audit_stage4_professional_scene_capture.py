"""Capture and audit the Stage 4 professional scenario preview."""

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

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication  # noqa: E402

from scripts.audit_stage3_professional_editor_capture import _geometry  # noqa: E402
from scripts.audit_visual_artifacts import run_audit  # noqa: E402
from src.core.commands import CommandManager  # noqa: E402
from src.core.scenario_authoring import ScenarioAuthoringState  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.ui.scenario_editor_window import ScenarioEditorWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

RESOLUTIONS = {
    "1280x720": (1280, 720),
    "1366x768": (1366, 768),
    "1920x1080": (1920, 1080),
}


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


def _fixture(root: Path) -> tuple[Path, Scene]:
    project = root / "fixture.ndtproj"
    project.write_bytes(b"stage4-professional-fixture-v1\n")
    image = root / "assets" / "fixture.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    from PySide6.QtGui import QImage

    rendered = QImage(180, 120, QImage.Format.Format_RGBA8888)
    rendered.fill(0xFF204060)
    assert rendered.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object(
        "fixture_object",
        [(20, 20), (140, 20), (140, 100), (20, 100)],
        select=False,
    )
    return project, scene


def _capture(
    window: ScenarioEditorWindow, path: Path, size: tuple[int, int]
) -> dict[str, Any]:
    window.resize(QSize(*size))
    window.show()
    QApplication.processEvents()
    if (window.width(), window.height()) != size:
        raise RuntimeError(f"Qt did not apply requested size {size}")
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"could not save {path.name}")
    with Image.open(path) as image:
        image.verify()
        actual = [image.width, image.height]
    return {
        "requested_size": list(size),
        "actual_window_size": [window.width(), window.height()],
        "actual_capture_size": actual,
        "files": {path.name: _digest(path)},
        "widget_geometry": _geometry(window),
    }


def capture(output: Path) -> dict[str, Any]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    captures_dir = output / "captures"
    captures_dir.mkdir(parents=True, exist_ok=True)
    provenance = _git_state()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    captures: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="neoeng-stage4-") as temp:
        project, scene = _fixture(Path(temp))
        authoring = ScenarioAuthoringState(scene)
        empty = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            for label, size in RESOLUTIONS.items():
                name = f"stage4_{label}_01_sem_projeto.png"
                captures[f"empty_{label}"] = _capture(empty, captures_dir / name, size)
        finally:
            empty.close()

        authoring.bind_project(project)
        window = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            session = window.professional_session
            inspector = window.professional_inspector
            viewport = window.professional_viewport
            if session is None or inspector is None or viewport is None:
                raise RuntimeError("professional Stage 4 widgets were not created")
            session.set_selection(["fixture_object"])
            inspector.parallax_depth.setValue(0.75)
            inspector.parallax_translation.setValue(1.0)
            inspector.parallax_zoom.setValue(0.5)
            inspector.parallax_apply_button.click()
            inspector.camera_x.setValue(42.0)
            inspector.camera_zoom.setValue(1.25)
            inspector.camera_apply_button.click()
            inspector.socket_id.setText("lamp")
            inspector.socket_type.setCurrentText("light")
            inspector.socket_x.setValue(50.0)
            inspector.socket_y.setValue(20.0)
            inspector.add_socket_button.click()
            inspector.socket_id.setText("smoke")
            inspector.socket_type.setCurrentText("vfx")
            inspector.socket_x.setValue(90.0)
            inspector.socket_y.setValue(24.0)
            inspector.add_socket_button.click()
            inspector.socket_id.setText("entry")
            inspector.socket_type.setCurrentText("trigger")
            inspector.socket_x.setValue(70.0)
            inspector.socket_y.setValue(80.0)
            inspector.add_socket_button.click()
            QApplication.processEvents()
            if len(session.document.sockets) != 3:
                raise RuntimeError("socket controls did not create all typed markers")
            for label, size in RESOLUTIONS.items():
                loaded = f"stage4_{label}_02_projeto_paineis.png"
                captures[f"loaded_{label}"] = _capture(
                    window, captures_dir / loaded, size
                )
                preview = f"stage4_{label}_04_gizmo_feedback.png"
                before_preview = viewport._items["fixture_object"].pos()
                inspector.camera_x.setValue(80.0)
                inspector.camera_apply_button.click()
                QTest.qWait(120)
                QApplication.processEvents()
                after_preview = viewport._items["fixture_object"].pos()
                if before_preview == after_preview:
                    raise RuntimeError(
                        f"camera update did not move fixture object at {label}"
                    )
                captures[f"preview_{label}"] = _capture(
                    window, captures_dir / preview, size
                )
        finally:
            window.close()

    manifest = {
        "schema_version": 2,
        "generator": "scripts/audit_stage4_professional_scene_capture.py",
        **provenance,
        "privacy": {"absolute_paths_persisted": False, "fixture_is_temporary": True},
        "captures": captures,
    }
    manifest_path = captures_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report = run_audit(captures_dir, output / "audited")
    report["source_commit"] = provenance["source_commit"]
    report["worktree_clean_at_capture_start"] = provenance[
        "worktree_clean_at_capture_start"
    ]
    (output / "stage4-capture-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
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
    return (
        0
        if report["status"] == "PASS" and report["worktree_clean_at_capture_start"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
