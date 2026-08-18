"""Capture and inspect the real Stage 4B.2 scenario preview states."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from PySide6.QtCore import QPoint, QSize  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.core.commands import CommandManager  # noqa: E402
from src.core.parallax_camera import OrthographicCamera, ParallaxLayer  # noqa: E402
from src.core.scenario_preview import ScenarioPreviewLayer  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "artifacts" / "stage4b2-preview-2026-08-18"
SIZE = (1280, 720)


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


def _fixture_scene() -> Scene:
    image = np.zeros((480, 720, 4), dtype=np.uint8)
    for y in range(image.shape[0]):
        image[y, :, :3] = (18 + y // 20, 22 + y // 20, 30 + y // 18)
    image[:, :, 3] = 255
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = image
    scene.add_object(
        "preview_object",
        [(120, 100), (350, 100), (350, 330), (120, 330)],
        select=True,
    )
    scene.cmd.clear()
    return scene


def _settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(120)
    app.processEvents()


def _capture(window: MainWindow, path: Path) -> None:
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"could not save {path.name}")


def _inspect_png(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        array = np.asarray(rgba)
        alpha_min = int(array[:, :, 3].min())
        alpha_max = int(array[:, :, 3].max())
        border = np.concatenate(
            [array[0, :, :3], array[-1, :, :3], array[:, 0, :3], array[:, -1, :3]]
        )
        border_nonblack = int(np.any(border != 0, axis=1).sum())
        return {
            "size": [rgba.width, rgba.height],
            "mode": image.mode,
            "alpha": [alpha_min, alpha_max],
            "border_nonblack_pixels": border_nonblack,
            "digest": _digest(path),
        }


def _annotate_overlay(path: Path, window: MainWindow) -> dict[str, Any]:
    canvas = window.canvas
    geometry = canvas._scenario_overlay_geometry
    if geometry is None:
        raise RuntimeError("overlay geometry was not produced")
    origin = canvas.mapTo(window, QPoint(0, 0))
    with Image.open(path) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    offset_x, offset_y = origin.x(), origin.y()
    x, y, width, height = geometry.frame
    draw.rectangle(
        [offset_x + x, offset_y + y, offset_x + x + width, offset_y + y + height],
        outline=(0, 255, 255, 255),
        width=2,
    )
    safe_x, safe_y, safe_width, safe_height = geometry.safe_area
    draw.rectangle(
        [
            offset_x + safe_x,
            offset_y + safe_y,
            offset_x + safe_x + safe_width,
            offset_y + safe_y + safe_height,
        ],
        outline=(255, 220, 80, 255),
        width=2,
    )
    annotated = path.with_name(path.stem + "_annotated.png")
    image.save(annotated, "PNG")
    return {
        "annotated": annotated.name,
        "canvas_origin": [offset_x, offset_y],
        "viewport_size": list(geometry.viewport_size),
        "frame": list(geometry.frame),
        "safe_area": list(geometry.safe_area),
        "crop_regions": [list(region) for region in geometry.crop_regions],
    }


def run() -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    scene = _fixture_scene()
    window = MainWindow(scene, AuditConfig())
    window.resize(QSize(*SIZE))
    window.show()
    _settle(app)
    try:
        window.canvas.set_scenario_preview_layers(
            [
                ScenarioPreviewLayer(
                    "far_background",
                    ("preview_object",),
                    ParallaxLayer(depth=0.8, translation_strength=1.0),
                )
            ]
        )
        window.canvas.set_scenario_camera(
            OrthographicCamera(
                (float(window.canvas.width()), float(window.canvas.height())),
                position=(16.0, 8.0),
                zoom=1.25,
            )
        )
        captures = {
            "normal_editing": OUTPUT / "01_normal_editing.png",
            "preview_read_only": OUTPUT / "02_preview_read_only.png",
            "preview_with_overlays": OUTPUT / "03_preview_with_overlays.png",
            "normal_after_preview": OUTPUT / "04_normal_after_preview.png",
        }
        _capture(window, captures["normal_editing"])
        window.scenario_preview_action.trigger()
        _settle(app)
        _capture(window, captures["preview_read_only"])
        window.scenario_overlays_action.trigger()
        _settle(app)
        _capture(window, captures["preview_with_overlays"])
        overlay_data = _annotate_overlay(captures["preview_with_overlays"], window)
        window.scenario_preview_action.trigger()
        _settle(app)
        _capture(window, captures["normal_after_preview"])

        png_data = {name: _inspect_png(path) for name, path in captures.items()}
        with Image.open(captures["preview_with_overlays"]) as image:
            pixels = np.asarray(image.convert("RGB"))
        cyan = (
            (pixels[:, :, 2] > 180) & (pixels[:, :, 1] > 150) & (pixels[:, :, 0] < 80)
        )
        yellow = (
            (pixels[:, :, 0] > 180) & (pixels[:, :, 1] > 150) & (pixels[:, :, 2] < 130)
        )
        if int(cyan.sum()) < 20 or int(yellow.sum()) < 20:
            raise RuntimeError("overlay colors were not detected in the real capture")
        canvas_origin = window.canvas.mapTo(window, QPoint(0, 0))
        manifest = {
            "schema_version": 1,
            "generator": "scripts/audit_scenario_preview.py",
            "viewport": list(SIZE),
            "states": {
                "normal_editing": {"preview": False, "overlays": False},
                "preview_read_only": {"preview": True, "overlays": False},
                "preview_with_overlays": {"preview": True, "overlays": True},
                "normal_after_preview": {"preview": False, "overlays": False},
            },
            "qt_geometry": {
                "canvas_origin": [canvas_origin.x(), canvas_origin.y()],
                "canvas_size": [window.canvas.width(), window.canvas.height()],
            },
            "overlay": overlay_data,
            "pixel_checks": {
                "cyan_pixels": int(cyan.sum()),
                "yellow_pixels": int(yellow.sum()),
            },
            "pngs": png_data,
            "scene_invariants": {
                "object_ids": sorted(scene.objects),
                "undo_count": scene.cmd.undo_count,
                "polygon": [
                    list(point) for point in scene.objects["preview_object"].polygon
                ],
            },
        }
        manifest_path = OUTPUT / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return manifest
    finally:
        window.close()
        _settle(app)


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, ensure_ascii=False))
