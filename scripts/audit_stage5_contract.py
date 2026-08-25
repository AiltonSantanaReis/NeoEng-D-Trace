"""Fail-closed Stage 5 audit for the live Viewport/HUD and Mask Viewer tracks."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QScrollArea

from scripts.audit_ui_capture import _capture, _main_window_widgets, _prepare_project, _settle
from scripts.audit_visual_artifacts import run_audit
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.mask_viewer import MaskViewer, MaskViewerDialog
from src.ui.theme_qss import QSS

ROOT = Path(__file__).resolve().parents[1]
RESOLUTIONS = {
    "1920x1080": (1920, 1080),
    "1366x768": (1366, 768),
    "1280x720": (1280, 720),
}
CAPTURE_GEOMETRY: dict[str, Any] = {}


class _ConfigStub:
    def get(self, _key, default=None):
        return default


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def _rect(widget, root) -> dict[str, Any]:
    local = widget.geometry()
    top_left = widget.mapTo(root, QPoint(0, 0))
    return {
        "geometry": [local.x(), local.y(), local.width(), local.height()],
        "root_geometry": [
            top_left.x(),
            top_left.y(),
            local.width(),
            local.height(),
        ],
        "visible": widget.isVisible(),
        "visible_to_root": widget.isVisibleTo(root),
    }


def _inside(inner: list[int], outer: list[int]) -> bool:
    return (
        inner[0] >= outer[0]
        and inner[1] >= outer[1]
        and inner[0] + inner[2] <= outer[0] + outer[2]
        and inner[1] + inner[3] <= outer[1] + outer[3]
    )


def _bgr_fixture() -> np.ndarray:
    image = np.zeros((160, 240, 3), dtype=np.uint8)
    image[:, :] = (30, 20, 10)
    image[35:125, 60:180] = (0, 0, 255)
    return image


def _viewport_track(app: QApplication, raw: Path) -> dict[str, Any]:
    scene, project_path = _prepare_project(raw)
    failures: list[str] = []
    states: dict[str, Any] = {}
    for label, (width, height) in RESOLUTIONS.items():
        window = MainWindow(scene, _ConfigStub())
        window._project_path = project_path
        window._document_name = project_path.name
        window._refresh_document_views(project_loaded=True)
        window.resize(QSize(width, height))
        window.show()
        _settle(app, 80)
        scene.select_object("rectangle-object")
        window.canvas.update_image()
        window.canvas.gizmo_toggle.setChecked(True)
        window.canvas._toggle_gizmo()
        QTest.mouseMove(window.canvas, QPoint(max(30, window.canvas.width() // 3), 80))
        window.canvas.set_vertex_snapping(True, grid_size=16)
        CAPTURE_GEOMETRY[label] = {"projeto_paineis": _main_window_widgets(window)}
        window.canvas.set_grid_visible(False)
        window.reference_pan_button.click()
        action_states = (
            ("lit", window.act_lit),
            ("xray1", window.act_xray1),
            ("xray2", window.act_xray2),
            ("xray3", window.act_xray3),
        )
        for state_name, action in action_states:
            action.trigger()
            _settle(app, 180)
            path = raw / f"stage5_viewport_{label}_{state_name}_02_projeto_paineis.png"
            _capture(window, path)
            status = window.viewport_status
            status_rect = _rect(status, window)
            bar_rect = _rect(window.statusBar(), window)
            chrome_rect = _rect(window.viewport_chrome, window)
            overlay = window.viewport_chrome.overlay
            overlay_rect = _rect(overlay, window)
            viewport_state = window.canvas.viewport_state()
            expected_modes = {
                "lit": "LIT",
                "xray1": "X-RAY 1",
                "xray2": "X-RAY 2",
                "xray3": "X-RAY 3",
            }
            expected_mode = expected_modes[state_name]
            if viewport_state.view_mode != expected_mode:
                failures.append(
                    f"{label}/{state_name}: view mode "
                    f"{viewport_state.view_mode!r} != {expected_mode!r}"
                )
            if not viewport_state.snap_enabled or viewport_state.snap_grid_size != 16:
                failures.append(
                    f"{label}/{state_name}: structured snap state is invalid"
                )
            if viewport_state.grid_visible:
                failures.append(
                    f"{label}/{state_name}: structured grid state should be disabled"
                )
            if viewport_state.selection_count < 1:
                failures.append(
                    f"{label}/{state_name}: structured selection state is empty"
                )
            if not _inside(status_rect["root_geometry"], bar_rect["root_geometry"]):
                failures.append(f"{label}/{state_name}: status escapes QStatusBar")
            if not _inside(overlay_rect["root_geometry"], chrome_rect["root_geometry"]):
                failures.append(f"{label}/{state_name}: HUD overlay escapes viewport")
            if window.canvas.findChildren(type(window.viewport_status)):
                failures.append(f"{label}/{state_name}: QLabel HUD entered canvas")
            states[f"{label}/{state_name}"] = {
                "size": [width, height],
                "status": status.text(),
                "tooltip": status.toolTip(),
                "viewport_state": asdict(viewport_state),
                "viewport": window.canvas.viewport_details_text(),
                "status_geometry": status_rect,
                "status_bar_geometry": bar_rect,
                "chrome_geometry": chrome_rect,
                "overlay_geometry": overlay_rect,
                "file": path.name,
                "digest": _digest(path),
            }
        window.close()
        _settle(app, 20)
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "states": states}


def _mask_track(app: QApplication, raw: Path) -> dict[str, Any]:
    failures: list[str] = []
    states: dict[str, Any] = {}
    source = _bgr_fixture()
    for label, (width, height) in RESOLUTIONS.items():
        scene = Scene()
        scene.load_image(source, "stage5-mask-fixture.png")
        dialog = MaskViewerDialog(scene)
        dialog.resize(width, height)
        dialog.show()
        _settle(app, 80)
        scroll = dialog.findChild(QScrollArea, "mask_controls_scroll")
        if scroll is None or not scroll.isVisibleTo(dialog):
            failures.append(f"{label}: mask controls scroll missing")
        if scroll is not None and not _inside(
            _rect(scroll, dialog)["root_geometry"], [0, 0, width, height]
        ):
            failures.append(f"{label}: mask controls clipped")
        if not _inside(
            _rect(dialog.viewer, dialog)["root_geometry"], [0, 0, width, height]
        ):
            failures.append(f"{label}: mask viewer clipped")
        for mode, name in enumerate(("original", "sobel", "canny", "laplacian")):
            dialog.view_mode_buttons[mode].click()
            _settle(app, 180)
            if dialog.viewer.get_display_mode() != mode:
                failures.append(f"{label}/{name}: mode did not apply")
            if dialog.viewer._get_qimage() is None:
                failures.append(f"{label}/{name}: rendered image missing")
            path = raw / f"stage5_mask_{label}_{name}.png"
            _capture(dialog, path)
            states[f"{label}/{name}"] = {
                "mode": mode,
                "size": [width, height],
                "viewer_geometry": _rect(dialog.viewer, dialog),
                "controls_geometry": _rect(scroll, dialog) if scroll else None,
                "file": path.name,
                "digest": _digest(path),
            }
        if label == "1280x720":
            QTest.mousePress(dialog.viewer, Qt.MouseButton.MiddleButton, pos=QPoint(100, 100))
            QTest.mouseMove(dialog.viewer, QPoint(130, 125))
            QTest.mouseRelease(dialog.viewer, Qt.MouseButton.MiddleButton, pos=QPoint(130, 125))
            pan_after_mouse = dialog.viewer.get_pan()
            QTest.keyClick(dialog.viewer, Qt.Key.Key_R)
            if pan_after_mouse == dialog.viewer.get_pan():
                failures.append("Mask Viewer keyboard reset did not change pan")
            dialog.viewer.set_roi_mode(True)
            QTest.mousePress(dialog.viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
            QTest.mouseMove(dialog.viewer, QPoint(220, 180))
            QTest.mouseRelease(dialog.viewer, Qt.MouseButton.LeftButton, pos=QPoint(220, 180))
            if dialog.viewer.get_roi() is None:
                failures.append("Mask Viewer ROI interaction produced no result")
        dialog.close()

    invalid = MaskViewer()
    invalid.resize(400, 300)
    invalid.show()
    invalid.set_display_mode(99)
    if invalid.get_display_mode() != 3:
        failures.append("invalid Mask Viewer mode was not clamped")
    invalid_path = raw / "stage5_mask_invalid_no_image.png"
    _capture(invalid, invalid_path)
    if invalid._get_qimage() is not None:
        failures.append("empty Mask Viewer unexpectedly returned an image")
    invalid.close()

    warnings: list[tuple[Any, ...]] = []
    original_warning = QMessageBox.warning
    QMessageBox.warning = staticmethod(lambda *args: warnings.append(args))
    try:
        empty_dialog = MaskViewerDialog(Scene())
        empty_dialog._run_detection()
        empty_dialog.close()
    finally:
        QMessageBox.warning = original_warning
    if not warnings or "No image" not in str(warnings[0][2]):
        failures.append("empty Mask Viewer detection has no actionable error feedback")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "states": states}


def _write_manifest(raw: Path) -> dict[str, Any]:
    files = sorted(path for path in raw.glob("*.png"))
    captures = {}
    for label in RESOLUTIONS:
        captures[label] = {
            "files": {
                path.name: _digest(path)
                for path in files
                if f"_{label}_" in path.name
            },
            "widget_geometry": CAPTURE_GEOMETRY.get(label, {}),
        }
    negative_files = {
        path.name: _digest(path)
        for path in files
        if path.name.endswith("no_image.png")
    }
    if negative_files:
        captures["negative"] = {"files": negative_files}
    manifest = {
        "schema_version": 2,
        "generator": "scripts/audit_stage5_contract.py",
        "platform": platform.platform(),
        "python": sys.version,
        "image_fixture": _digest(raw / "ui-audit-fixture.png")
        if (raw / "ui-audit-fixture.png").is_file() else None,
        "captures": captures,
    }
    (raw / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    os.environ.pop("QT_QPA_PLATFORM", None)
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/stage5-snapshot-20260824").resolve()
    raw = output / "raw-captures"
    visual = output / "visual-audit"
    raw.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    viewport = _viewport_track(app, raw)
    mask = _mask_track(app, raw)
    manifest = _write_manifest(raw)
    visual_report = run_audit(raw, visual)
    failures = viewport["failures"] + mask["failures"]
    report = {
        "schema": "neoeng.stage5-contract-audit",
        "schema_version": 1,
        "stage": 5,
        "stage_name": "Viewport e HUD",
        "source_state": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean": not bool(_git("status", "--porcelain")),
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "qt_platform": app.platformName(),
            "resolutions": list(RESOLUTIONS),
        },
        "tracks": {
            "viewport_hud": viewport,
            "mask_viewer": mask,
        },
        "visual_audit": {
            "status": visual_report["status"],
            "report": "visual-audit/visual-audit-report.json",
        },
        "capture_manifest": {
            "path": "raw-captures/manifest.json",
            "sha256": _digest(raw / "manifest.json")["sha256"],
        },
        "failures": failures,
        "limitations": [
            "The DPI matrix is a separate Stage 9 gate; this Stage 5 audit proves the three required logical resolutions.",
            "The professional gizmo mathematics remains Stage 6 scope; Stage 5 verifies only visibility/state and non-overlap.",
            "Automated visual PASS does not replace human visual review.",
        ],
        "status": "PASS" if not failures and visual_report["status"] == "PASS" else "FAIL",
    }
    (output / "stage5-contract-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "failures": len(failures),
                "visual_findings": visual_report["finding_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
