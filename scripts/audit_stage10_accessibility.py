"""Fail-closed real-window evidence audit for Stage 10 accessibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QLineEdit,
    QSlider,
    QTabBar,
    QWidget,
)

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_tokens import token_contrast_ratios

REQUIREMENT_ID = "REQ-F10-UI-ACCESSIBILITY"
FEATURE_ID = "FEAT-UI-ACCESSIBILITY"
TEST_IDS = {
    "metadata": "TEST-UI-ACCESSIBILITY-METADATA",
    "keyboard": "TEST-UI-KEYBOARD-FOCUS",
    "mouse": "TEST-UI-MOUSE-FEEDBACK",
    "errors": "TEST-UI-ERROR-FEEDBACK",
    "contrast": "TEST-UI-CONTRAST-STATES",
}
EVIDENCE_ID = "EVID-F10-ACCESSIBILITY-AUDIT"


class Config:
    def get(self, key, default=None):
        return default


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def interactive_controls(root: QWidget) -> list[QWidget]:
    classes = (
        QAbstractButton,
        QAbstractSpinBox,
        QLineEdit,
        QSlider,
        QCheckBox,
        QTabBar,
    )
    return [
        widget
        for widget in root.findChildren(QWidget)
        if widget.isVisibleTo(root) and isinstance(widget, classes)
    ]


def settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(80)
    app.processEvents()


def capture(window: MainWindow, output: Path, name: str) -> Path:
    path = output / "visual" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not window.grab().save(str(path)):
        raise RuntimeError(f"failed to save capture: {path}")
    return path


def run_audit(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"evidence output must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    scene = Scene()
    scene.cmd = CommandManager()
    window = MainWindow(scene, Config())
    window.show()
    settle(app)
    failures: list[str] = []
    captures: list[Path] = []

    try:
        controls = interactive_controls(window)
        if not controls:
            failures.append("no visible interactive controls were discovered")
        for widget in controls:
            if not widget.accessibleName():
                failures.append(f"missing accessible name: {widget.objectName()}")
            if not widget.accessibleDescription():
                failures.append(f"missing accessible description: {widget.objectName()}")
            if isinstance(widget, QAbstractButton):
                if not widget.toolTip():
                    failures.append(f"missing tooltip: {widget.objectName()}")
                if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
                    failures.append(f"missing keyboard focus: {widget.objectName()}")

        ratios = token_contrast_ratios()
        if ratios["primary_on_window"] < 4.5:
            failures.append("primary text contrast below 4.5")
        if ratios["secondary_on_surface"] < 4.5:
            failures.append("secondary text contrast below 4.5")
        if ratios["focus_on_window"] < 3.0:
            failures.append("focus contrast below 3.0")

        window.resize(1920, 1080)
        settle(app)
        captures.append(capture(window, output, "desktop-1920x1080"))

        window.tool_palette.setEnabled(True)
        window.reference_tool_palette.setEnabled(True)
        window.setFocus()
        QTest.keyClick(window, Qt.Key.Key_1)
        settle(app)
        if not window.tool_palette.btn_polygonal_lasso.isChecked():
            failures.append("keyboard shortcut 1 did not select polygonal lasso")

        window.canvas.set_view_mode(window.canvas.VIEW_LIT)
        QTest.keyClick(window, Qt.Key.Key_X)
        settle(app)
        if window.canvas._view_mode != window.canvas.VIEW_XRAY_1:
            failures.append("keyboard shortcut X did not activate X-Ray 1")
        captures.append(capture(window, output, "desktop-xray-keyboard"))

        tab_pairs = (
            (window.reference_open_button, window.reference_save_button),
            (window.reference_save_button, window.reference_export_button),
            (window.reference_export_button, window.reference_fit_button),
            (window.reference_fit_button, window.reference_focus_button),
        )
        for source, target in tab_pairs:
            source.setFocus()
            QTest.keyClick(source, Qt.Key.Key_Tab)
            settle(app)
            if app.focusWidget() is not target:
                failures.append(
                    f"tab order mismatch: {source.objectName()} -> "
                    f"{getattr(app.focusWidget(), 'objectName', lambda: '')()}"
                )

        QTest.mouseClick(window.reference_pan_button, Qt.MouseButton.LeftButton)
        settle(app)
        if not window.canvas.is_pan_mode():
            failures.append("mouse pan control did not activate viewport pan")
        QTest.mouseClick(window.reference_select_button, Qt.MouseButton.LeftButton)
        settle(app)
        if window.canvas.is_pan_mode():
            failures.append("mouse select control did not leave viewport pan")

        snap = window.viewport_chrome.overlay.snap_button
        before = snap.isChecked()
        QTest.mouseClick(snap, Qt.MouseButton.LeftButton)
        settle(app)
        if snap.isChecked() is before:
            failures.append("mouse snap control did not change state")
        if "current state:" not in snap.accessibleDescription():
            failures.append("snap state feedback is not exposed accessibly")
        captures.append(capture(window, output, "desktop-mouse-state"))

        window.resize(1280, 720)
        settle(app)
        captures.append(capture(window, output, "compact-1280x720"))
        window.side_panel.search_input.setFocus()
        settle(app)
        captures.append(capture(window, output, "compact-inspector-focus"))

        result = {
            "status": "PASS" if not failures else "FAIL",
            "requirement_id": REQUIREMENT_ID,
            "feature_ids": [FEATURE_ID],
            "test_ids": list(TEST_IDS.values()),
            "evidence_id": EVIDENCE_ID,
            "commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_status": git("status", "--porcelain"),
            "environment": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "pyside6": pyside_version,
                "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
            },
            "controls_discovered": len(controls),
            "failures": failures,
            "contrast_ratios": ratios,
            "captures": [],
            "limitations": [
                "The offscreen Qt backend proves deterministic Qt behavior and pixels; native monitor DPI switching remains an environment-specific check.",
                "This package proves Stage 10 accessibility/usability only; it does not prove renderer, scenario runtime, particles, lights or later stages.",
            ],
        }
        for path in captures:
            result["captures"].append(
                {
                    "path": path.relative_to(output).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
        report_path = output / "report.json"
        report_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "schema": "neoeng.stage10.accessibility",
            "schema_version": 1,
            "evidence_id": EVIDENCE_ID,
            "status": result["status"],
            "commit": result["commit"],
            "requirement_id": REQUIREMENT_ID,
            "feature_ids": [FEATURE_ID],
            "test_ids": list(TEST_IDS.values()),
            "report": {"path": "report.json", "sha256": sha256(report_path)},
            "captures": result["captures"],
        }
        manifest_path = output / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        hashed = [manifest_path, report_path, *captures]
        hashes_path = output / "hashes.sha256"
        hashes_path.write_text(
            "".join(
                f"{sha256(path)}  {path.relative_to(output).as_posix()}\n"
                for path in sorted(hashed, key=lambda item: item.relative_to(output).as_posix())
            ),
            encoding="utf-8",
        )
        return result
    finally:
        window.close()
        settle(app)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run_audit(args.output)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())