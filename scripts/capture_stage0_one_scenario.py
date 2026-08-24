"""Capture one dedicated Stage 0 scenario-editor resolution per process."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("width", type=int)
    parser.add_argument("height", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts/stage0-snapshot-20260824/visual-evidence"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    scene = Scene()
    scene.add_polygon([(0, 0), (160, 0), (160, 120), (0, 120)])
    window = ScenarioEditorWindow(ScenarioAuthoringState(scene), scene)
    window.resize(args.width, args.height)
    window.show()
    app.processEvents()
    app.processEvents()
    size = f"{args.width}x{args.height}"
    path = output / f"stage0_scenario_editor_{size}_dpi100.png"
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(path)
    print(f"generated={size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
