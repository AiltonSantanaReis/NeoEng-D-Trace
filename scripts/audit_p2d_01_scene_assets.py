"""Capture P2D-01A scene assets in the real professional editor window.

This focused capture uses the canonical visual auditor but records the current
scenario widget names and a real overlay state.  It is intentionally separate
from historical Stage 3/4 capturers whose geometry contracts predate the
professional viewport names.
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
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QPoint, QRect, QSize  # noqa: E402
from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

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


def _widget_record(widget: QWidget, root: QWidget) -> dict[str, Any]:
    rect = widget.geometry()
    top_left = widget.mapTo(root, QPoint(0, 0))
    frame = widget.frameGeometry()
    return {
        "class": widget.metaObject().className(),
        "object_name": widget.objectName(),
        "visible": widget.isVisible(),
        "enabled": widget.isEnabled(),
        "geometry": [rect.x(), rect.y(), rect.width(), rect.height()],
        "root_geometry": [top_left.x(), top_left.y(), widget.width(), widget.height()],
        "frame_geometry": [frame.x(), frame.y(), frame.width(), frame.height()],
    }


def _scenario_geometry(window: ScenarioEditorWindow) -> dict[str, Any]:
    widgets: dict[str, QWidget] = {
        "scenario_editor_toolbar": window.toolbar,
        "scenario_editor_splitter": window.centralWidget(),
        "professional_viewport_pages": window.professional_pages,
        "scenario_right_pages": window.right_pages,
    }
    if window.professional_viewport is not None:
        widgets["professional_scene_viewport"] = window.professional_viewport
    if window.professional_inspector_scroll is not None:
        widgets["professional_inspector_scroll"] = window.professional_inspector_scroll
    if window.professional_inspector is not None:
        widgets["professional_scene_inspector"] = window.professional_inspector

    records = {name: _widget_record(widget, window) for name, widget in widgets.items()}
    if "professional_inspector_scroll" in records:
        records["professional_inspector_scroll"]["scroll_area"] = True
    if "professional_scene_inspector" in records:
        records["professional_scene_inspector"].update(
            {"scrollable": True, "scroll_area_parent": "professional_inspector_scroll"}
        )
    return {
        "profile": (
            "professional_scene_editor"
            if window.professional_session is not None
            else "professional_scene_empty"
        ),
        "professional_editor": records,
    }


def _fixture(root: Path) -> tuple[Path, Scene]:
    project = root / "fixture.ndtproj"
    project.write_bytes(b"p2d-01a-scene-asset-fixture-v1\n")
    image_path = root / "assets" / "scene" / "fixture.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(180, 120, QImage.Format.Format_RGBA8888)
    image.fill(QColor("#d4a36a"))
    assert image.save(str(image_path))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image_path)
    scene.add_object(
        "fixture_object",
        [(20, 20), (160, 20), (160, 100), (20, 100)],
        select=False,
    )
    return project, scene


def _capture(
    window: ScenarioEditorWindow,
    path: Path,
    size: tuple[int, int],
) -> dict[str, Any]:
    window.resize(QSize(*size))
    window.show()
    QApplication.processEvents()
    QTest.qWait(160)
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
        "widget_geometry": _scenario_geometry(window),
    }


def capture(output: Path) -> dict[str, Any]:
    output = output.resolve()
    capture_dir = output / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    state = _git_state()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    captures: dict[str, Any] = {}
    asset_rendering: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="neoeng-p2d-01a-") as temp:
        project, scene = _fixture(Path(temp))
        authoring = ScenarioAuthoringState(scene)
        empty = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            for label, size in RESOLUTIONS.items():
                captures[f"empty_{label}"] = _capture(
                    empty,
                    capture_dir / f"{label}_scenario_empty.png",
                    size,
                )
        finally:
            empty.close()

        authoring.bind_project(project)
        window = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            viewport = window.professional_viewport
            session = window.professional_session
            if viewport is None or session is None:
                raise RuntimeError("professional viewport was not created")
            session.set_selection(["fixture_object"])
            window.overlay_action.setChecked(True)
            window._toggle_overlays()
            QApplication.processEvents()
            real_item = viewport._items.get("fixture_object")
            if real_item is None or real_item._pixmap is None:
                raise RuntimeError("fixture asset was not loaded as a real pixmap")
            asset_rendering = {
                "object_id": "fixture_object",
                "real_pixmap": True,
                "pixmap_size": [real_item._pixmap.width(), real_item._pixmap.height()],
                "overlay_enabled": viewport.is_overlay_visible(),
            }
            for label, size in RESOLUTIONS.items():
                captures[f"authoring_{label}"] = _capture(
                    window,
                    capture_dir / f"{label}_scenario_authoring.png",
                    size,
                )
        finally:
            window.close()

    manifest = {
        "schema_version": 2,
        "generator": "scripts/audit_p2d_01_scene_assets.py",
        **state,
        "privacy": {"absolute_paths_persisted": False, "fixture_is_temporary": True},
        "asset_rendering": asset_rendering,
        "captures": captures,
    }
    manifest_path = capture_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report = run_audit(capture_dir, output / "audited")
    report["source_commit"] = state["source_commit"]
    report["asset_rendering"] = asset_rendering
    (output / "p2d-01a-capture-report.json").write_text(
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
            {
                "status": report["status"],
                "finding_count": report["finding_count"],
                "asset_rendering": report["asset_rendering"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
