"""Capture reproducible Qt and sidecar evidence for Stage 4B.3."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from PySide6.QtCore import QPoint, QRect, QSize  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.core.commands import CommandManager  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "artifacts" / "stage4b3-authoring-window-2026-08-18"
VIEWPORTS = {"compact_1280x720": (1280, 720), "desktop_1920x1080": (1920, 1080)}


class AuditConfig:
    def get(self, key: str, default: Any = None) -> Any:
        del key
        return default

    def set(self, key: str, value: Any) -> None:
        del key, value

    def save(self) -> None:
        return None


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _source_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _fixture_scene() -> Scene:
    image = np.zeros((360, 540, 4), dtype=np.uint8)
    for y in range(image.shape[0]):
        image[y, :, :3] = (18 + y // 30, 22 + y // 28, 31 + y // 24)
    image[:, :, 3] = 255
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = image
    scene.add_object(
        "authoring_object",
        [(90, 70), (280, 70), (280, 240), (90, 240)],
        select=True,
    )
    scene.cmd.clear()
    return scene


def _settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(220)
    app.processEvents()


def _capture(window: MainWindow, path: Path) -> None:
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"could not save {path.name}")


def _rect(widget, window: MainWindow) -> list[int]:
    origin = widget.mapTo(window, QPoint(0, 0))
    return [origin.x(), origin.y(), widget.width(), widget.height()]


def _inspect_png(path: Path, expected: tuple[int, int]) -> dict[str, Any]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        pixels = np.asarray(rgba)
        if (rgba.width, rgba.height) != expected:
            raise RuntimeError(f"unexpected dimensions in {path.name}")
        alpha = pixels[:, :, 3]
        border = np.concatenate(
            [pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]], axis=0
        )
        dark_pixels = int(np.all(pixels[:, :, :3] < 80, axis=2).sum())
        non_empty = int(np.any(pixels[:, :, :3] != 0, axis=2).sum())
        if int(alpha.min()) != 255 or int(alpha.max()) != 255:
            raise RuntimeError(f"alpha contract failed for {path.name}")
        if int(np.any(border[:, :3] != 0, axis=1).sum()) <= 0:
            raise RuntimeError(f"empty border in {path.name}")
        if dark_pixels <= 1000 or non_empty <= 1000:
            raise RuntimeError(f"theme/canvas pixels missing in {path.name}")
        return {
            "size": [rgba.width, rgba.height],
            "mode": image.mode,
            "alpha": [int(alpha.min()), int(alpha.max())],
            "dark_pixels": dark_pixels,
            "non_empty_pixels": non_empty,
            "digest": _digest(path),
        }


def _annotate(path: Path, window: MainWindow) -> tuple[str, dict[str, Any]]:
    canvas_rect = _rect(window.canvas, window)
    inspector = window.scenario_panel.parentWidget()
    scenario_rect = _rect(inspector, window)
    window_rect = [0, 0, window.width(), window.height()]
    canvas_qrect = QRect(*canvas_rect)
    scenario_qrect = QRect(*scenario_rect)
    if canvas_qrect.intersects(scenario_qrect):
        raise RuntimeError("canvas and scenario panel overlap")
    for name, rect in (("canvas", canvas_rect), ("scenario_inspector", scenario_rect)):
        x, y, width, height = rect
        if x < 0 or y < 0 or x + width > window.width() or y + height > window.height():
            raise RuntimeError(f"{name} is clipped by the window")

    with Image.open(path) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle(
        [
            canvas_rect[0],
            canvas_rect[1],
            canvas_rect[0] + canvas_rect[2],
            canvas_rect[1] + canvas_rect[3],
        ],
        outline=(0, 255, 120, 255),
        width=3,
    )
    draw.rectangle(
        [
            scenario_rect[0],
            scenario_rect[1],
            scenario_rect[0] + scenario_rect[2],
            scenario_rect[1] + scenario_rect[3],
        ],
        outline=(255, 210, 40, 255),
        width=3,
    )
    annotated = path.with_name(path.stem + "_annotated.png")
    image.save(annotated, "PNG")
    return annotated.name, {
        "window": window_rect,
        "canvas": canvas_rect,
        "scenario_inspector": scenario_rect,
        "overlap": False,
        "clipping": False,
    }


def run() -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    scene = _fixture_scene()
    project = OUTPUT / "authoring_fixture.ndtproj"
    project.write_bytes(b"stage4b3-authoring-fixture-v1\n")
    window = MainWindow(scene, AuditConfig())
    window._project_path = project
    window.scenario_authoring.bind_project(project)
    window.scenario_authoring.reset()
    window.show()
    window.open_scenario_editor()
    editor = window.scenario_editor_window
    if editor is None:
        raise RuntimeError("dedicated scenario editor did not open")
    editor.show()
    _settle(app)
    captures: dict[str, dict[str, Any]] = {}
    try:
        state = window.scenario_authoring
        if not state.is_available:
            raise RuntimeError("scenario authoring did not bind to the fixture")
        for label, size in VIEWPORTS.items():
            editor.resize(QSize(*size))
            _settle(app)
            normal = OUTPUT / f"{label}_01_authoring.png"
            _capture(editor, normal)
            annotated_name, geometry = _annotate(normal, editor)
            captures[label] = {
                "mode": "compact" if window._compact_layout else "desktop",
                "authoring": _inspect_png(normal, size),
                "annotated": {
                    "name": annotated_name,
                    "digest": _digest(OUTPUT / annotated_name),
                },
                "geometry": geometry,
                "main_layers_tabs": window.layers.tabs.count(),
                "scenario_editor_separate": True,
            }

        layer_id = state.document.layers[0].id
        editor.scenario_panel.name_edit.setText("Captured Layer")
        editor.scenario_panel._rename()
        editor.scenario_panel.depth_spin.setValue(0.7)
        editor.scenario_panel._set_parallax()
        assert state.commands.undo_count == 2
        before_undo = state.document
        state.undo()
        after_undo = state.document
        state.redo()
        assert state.document == before_undo
        state.save()
        sidecar = state.scenario_path
        if sidecar is None or not sidecar.is_file():
            raise RuntimeError("scenario sidecar was not saved")
        captures["authoring_transaction"] = {
            "layer_id": layer_id,
            "after_undo_name": after_undo.layers[0].name,
            "restored_name": state.document.layers[0].name,
            "undo_count_after_redo": state.commands.undo_count,
            "redo_count_after_redo": state.commands.redo_count,
            "saved_digest": _digest(sidecar),
            "project_digest": _digest(project),
            "scene_polygon": [
                list(point) for point in scene.objects["authoring_object"].polygon
            ],
            "scene_undo_count": scene.cmd.undo_count,
            "preview_enabled": window.canvas.is_scenario_preview_enabled(),
        }
        manifest = {
            "schema_version": 1,
            "generator": "scripts/audit_scenario_authoring.py",
            "scope": (
                "scenario layer stack, inspector, isolated Undo/Redo "
                "and sidecar persistence"
            ),
            "viewport_states": captures,
            "artifacts": {
                "authoring_fixture.ndtproj": _digest(project),
                "authoring_fixture.ndtscenario.json": _digest(sidecar),
            },
            "source_commit": _source_commit(),
            "source_files": {
                "scenario_authoring.py": _digest(
                    ROOT / "src/core/scenario_authoring.py"
                ),
                "scenario_panel.py": _digest(ROOT / "src/ui/scenario_panel.py"),
                "scenario_authoring_actions.py": _digest(
                    ROOT / "src/ui/scenario_authoring_actions.py"
                ),
                "layers_panel.py": _digest(ROOT / "src/ui/layers_panel.py"),
                "responsive_layout.py": _digest(ROOT / "src/ui/responsive_layout.py"),
                "main_window.py": _digest(ROOT / "src/ui/main_window.py"),
                "command_bindings.py": _digest(ROOT / "src/ui/command_bindings.py"),
                "test_stage2_command_registry.py": _digest(
                    ROOT / "tests/test_stage2_command_registry.py"
                ),
                "test_stage4b3_scenario_authoring.py": _digest(
                    ROOT / "tests/test_stage4b3_scenario_authoring.py"
                ),
                "audit_scenario_authoring.py": _digest(Path(__file__)),
            },
        }
        manifest_path = OUTPUT / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return manifest
    finally:
        window._mark_document_clean()
        window.close()
        _settle(app)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
