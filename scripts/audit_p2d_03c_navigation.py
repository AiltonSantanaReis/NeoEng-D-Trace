"""Capture the accepted P2D-03C professional navigation and state matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from scripts.audit_visual_artifacts import run_audit
from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow
from src.ui.theme_qss import QSS


RESOLUTIONS = {
    "professional_1280x820": (1280, 820),
    "canonical_1366x768": (1366, 768),
    "canonical_1920x1080": (1920, 1080),
}


def _digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _fixture(root: Path) -> tuple[Path, Scene, ScenarioAuthoringState]:
    project = root / "scenario.ndtproj"
    project.write_bytes(b"p2d-03c-navigation-fixture-v1\n")
    image_path = root / "scenario.png"
    image = QImage(180, 120, QImage.Format.Format_RGBA8888)
    image.fill(0xFF24435A)
    if not image.save(str(image_path)):
        raise RuntimeError("could not create the P2D-03C fixture image")
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image_path)
    scene.add_object("near_object", [(20, 20), (100, 20), (100, 80), (20, 80)])
    scene.add_object("far_object", [(460, 260), (620, 260), (620, 360), (460, 360)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    return project, scene, authoring


def _source_state() -> dict[str, Any]:
    import subprocess

    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True)
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, text=True
    )
    tracked = subprocess.check_output(
        ["git", "status", "--short", "--untracked-files=no"], cwd=root, text=True
    )
    return {
        "commit": head.strip(),
        "branch": branch.strip(),
        "tracked_clean_at_capture": not bool(tracked.strip()),
    }


def _geometry(window: ScenarioEditorWindow) -> dict[str, Any]:
    names = (
        "scenario_editor_toolbar",
        "scenario_editor_splitter",
        "professional_viewport_pages",
        "scenario_right_pages",
        "professional_scene_viewport",
        "professional_inspector_scroll",
        "professional_scene_inspector",
    )
    records: dict[str, Any] = {}
    for name in names:
        widget = window.findChild(type(window), name)
        if widget is None:
            from PySide6.QtWidgets import QWidget

            widget = window.findChild(QWidget, name)
        if widget is None:
            raise RuntimeError(f"required widget not found: {name}")
        position = widget.mapTo(window, QPoint(0, 0))
        geometry = widget.geometry()
        records[name] = {
            "geometry": [0, 0, geometry.width(), geometry.height()],
            "root_geometry": [
                position.x(),
                position.y(),
                geometry.width(),
                geometry.height(),
            ],
            "visible": bool(widget.isVisible()),
        }
    records["professional_inspector_scroll"]["scroll_area"] = True
    records["professional_scene_inspector"]["scrollable"] = True
    records["professional_scene_inspector"]["scroll_area_parent"] = "professional_inspector_scroll"
    return {"profile": "professional_scene_editor", "professional_editor": records}


def _capture(
    window: ScenarioEditorWindow,
    output: Path,
    name: str,
    size: tuple[int, int],
    state: str,
) -> dict[str, Any]:
    window.resize(*size)
    window.show()
    QApplication.processEvents()
    path = output / name
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"capture failed: {name}")
    with Image.open(path) as image:
        image.verify()
        actual_size = [image.width, image.height]
    viewport = window.professional_viewport
    inspector = window.professional_inspector
    if viewport is None or inspector is None:
        raise RuntimeError("professional P2D-03C widgets are unavailable")
    return {
        "state": state,
        "logical_window_size": [window.width(), window.height()],
        "actual_capture_size": actual_size,
        "navigation_zoom": viewport.navigation_zoom,
        "navigation_center": [
            viewport.navigation_center.x(),
            viewport.navigation_center.y(),
        ],
        "viewport_has_focus": viewport.hasFocus(),
        "pan_active": viewport._pan_origin is not None,
        "preview_checked": window.preview_action.isChecked(),
        "authoring_checked": window.authoring_action.isChecked(),
        "fit_selection_enabled": inspector.fit_button.isEnabled(),
        "fit_all_enabled": inspector.fit_all_button.isEnabled(),
        "files": {name: _digest(path)},
        "widget_geometry": _geometry(window),
    }


def capture(output: Path) -> dict[str, Any]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    captures: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="neoeng-p2d03c-") as temp:
        _project, _scene, authoring = _fixture(Path(temp))
        window = ScenarioEditorWindow(authoring, _scene, language="en")
        try:
            viewport = window.professional_viewport
            inspector = window.professional_inspector
            inspector_scroll = window.professional_inspector_scroll
            session = window.professional_session
            if (
                viewport is None
                or inspector is None
                or inspector_scroll is None
                or session is None
            ):
                raise RuntimeError("P2D-03C professional surface was not built")
            session.set_selection(["near_object"], "near_object")
            window.overlay_action.setChecked(True)
            window._toggle_overlays()
            viewport.setFocus(Qt.FocusReason.OtherFocusReason)
            captures["focus_authoring"] = _capture(
                window,
                output,
                "01_focus_authoring_scenario_authoring.png",
                RESOLUTIONS["professional_1280x820"],
                "focus-authoring",
            )

            inspector.fit_button.click()
            QTest.mouseMove(inspector.fit_button, inspector.fit_button.rect().center())
            app.processEvents()
            captures["fit_selection_hover"] = _capture(
                window,
                output,
                "02_fit_selection_hover_scenario_authoring.png",
                RESOLUTIONS["professional_1280x820"],
                "fit-selection-hover",
            )

            inspector.fit_all_button.click()
            app.processEvents()
            captures["fit_all"] = _capture(
                window,
                output,
                "03_fit_all_scenario_authoring.png",
                RESOLUTIONS["professional_1280x820"],
                "fit-all",
            )

            viewport.setFocus(Qt.FocusReason.OtherFocusReason)
            pan_point = viewport.viewport().rect().center()
            QTest.mousePress(
                viewport.viewport(),
                Qt.MouseButton.MiddleButton,
                Qt.KeyboardModifier.NoModifier,
                pan_point,
            )
            app.processEvents()
            captures["pan_pressed"] = _capture(
                window,
                output,
                "04_pan_pressed_scenario_authoring.png",
                RESOLUTIONS["professional_1280x820"],
                "pan-pressed",
            )
            QTest.mouseMove(viewport.viewport(), pan_point + QPoint(64, 36))
            app.processEvents()
            QTest.mouseRelease(
                viewport.viewport(),
                Qt.MouseButton.MiddleButton,
                Qt.KeyboardModifier.NoModifier,
                pan_point + QPoint(64, 36),
            )
            app.processEvents()

            window.preview_action.trigger()
            app.processEvents()
            captures["preview_disabled"] = _capture(
                window,
                output,
                "05_preview_disabled_scenario_preview.png",
                RESOLUTIONS["professional_1280x820"],
                "preview-disabled-inspector",
            )

            for key, size in (
                ("canonical_1366x768", RESOLUTIONS["canonical_1366x768"]),
                ("canonical_1920x1080", RESOLUTIONS["canonical_1920x1080"]),
            ):
                captures[key] = _capture(
                    window,
                    output,
                    f"06_{key}_scenario_preview.png" if key.endswith("768") else f"07_{key}_scenario_preview.png",
                    size,
                    key,
                )
        finally:
            window.close()

    manifest = {
        "schema_version": 4,
        "purpose": "P2D-03C accepted navigation, fit and visual-state matrix",
        "environment": {
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "qt_qpa_platform": os.environ.get("QT_QPA_PLATFORM"),
            "qt_scale_factor": os.environ.get("QT_SCALE_FACTOR"),
        },
        "source": _source_state(),
        "decisions": ["D03C-01", "D03C-02", "D03C-03", "D03C-04", "D03C-05", "D03C-06"],
        "captures": captures,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    visual_dir = output.parent / (output.name + "-visual-audit")
    visual_report = run_audit(output, visual_dir)
    report = {
        "schema_version": 4,
        "status": "PASS" if visual_report["status"] == "PASS" else "FAIL",
        "visual_audit": {
            "status": visual_report["status"],
            "finding_count": visual_report["finding_count"],
            "report": "../" + visual_dir.name + "/visual-audit-report.json",
        },
        "source": manifest["source"],
        "manifest": {"file": manifest_path.name, **_digest(manifest_path)},
        "human_review": "REQUIRED",
        "captures": captures,
    }
    (output / "p2d03c-capture-report.json").write_text(
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
    print(json.dumps({"status": report["status"], "finding_count": report["visual_audit"]["finding_count"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
