"""Capture one Stage 0 main-editor resolution per process.

Qt's offscreen platform can retain native resources after repeatedly creating
large windows. One process per resolution keeps the evidence deterministic.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from src.models.scene import Scene
from src.ui.main_window import MainWindow


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("width", type=int)
    parser.add_argument("height", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts/stage0-snapshot-20260824/visual-evidence"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    size = f"{args.width}x{args.height}"
    scene = Scene()
    window = MainWindow(scene, {})
    window.resize(args.width, args.height)
    window.show()
    app.processEvents()

    def save(widget, name: str) -> None:
        app.processEvents()
        path = output / f"stage0_{name}_{size}_dpi100.png"
        if not widget.grab().save(str(path), "PNG"):
            raise RuntimeError(path)

    save(window, "no_project")
    scene.add_polygon([(0, 0), (160, 0), (160, 120), (0, 120)])
    app.processEvents()
    save(window, "project_open")
    save(window, "panels")
    window.act_xray1.trigger()
    save(window, "xray")
    button = window.findChild(QPushButton, "gizmo_toggle")
    if button is None:
        raise RuntimeError("gizmo_toggle not found")
    button.click()
    save(window, "gizmo")
    tabs = getattr(window, "reference_panel_tabs", None)
    if tabs is not None:
        for index in range(tabs.count()):
            if "collision" in tabs.tabText(index).lower() or "validation" in tabs.tabText(index).lower():
                tabs.setCurrentIndex(index)
                break
    save(window, "validation")
    window.open_mask_viewer()
    app.processEvents()
    dialog = window._mask_viewer_dialog
    if dialog is None:
        raise RuntimeError("mask viewer did not open")
    dialog.resize(args.width, args.height)
    save(dialog, "mask_viewer")
    print(f"generated={size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
