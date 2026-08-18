"""Capture and validate the real command palette in both supported languages."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2  # noqa: E402
from PIL import Image  # noqa: E402
from PySide6.QtCore import QSize, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from src.models.scene import Scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESOLUTIONS = {
    "1080p_FHD": (1920, 1080),
    "768p_Minima": (1366, 768),
    "720p_Compacta": (1280, 720),
}
LANGUAGES = ("en", "pt")


class AuditConfig:
    def get(self, key: str, default: Any = None) -> Any:
        del key
        return default

    def set(self, key: str, value: Any) -> None:
        del key, value

    def save(self) -> None:
        return None


def _source_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _worktree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(80)
    app.processEvents()


def _capture(widget: QWidget, path: Path) -> None:
    if not widget.grab().save(str(path), "PNG"):
        raise RuntimeError(f"could not save capture {path.name}")


def _rect(widget: QWidget) -> list[int]:
    geometry = widget.geometry()
    return [geometry.x(), geometry.y(), geometry.width(), geometry.height()]


def _inside(child: QWidget, parent: QWidget) -> bool:
    child_rect = child.geometry()
    parent_rect = parent.rect()
    return parent_rect.contains(child_rect.topLeft()) and parent_rect.contains(
        child_rect.bottomRight()
    )


def _image_metadata(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    with Image.open(path) as image:
        image.load()
        size = [image.width, image.height]
        mode = image.mode
    decoded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if decoded is None:
        raise RuntimeError(f"OpenCV could not decode {path.name}")
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "dimensions": size,
        "mode": mode,
        "opencv_shape": list(decoded.shape),
    }


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generator": "scripts/audit_command_palette_capture.py",
        "source_head": _source_head(),
        "worktree_clean_at_capture": _worktree_clean(),
        "requested_resolutions": {
            name: list(size) for name, size in RESOLUTIONS.items()
        },
        "languages": list(LANGUAGES),
        "captures": {},
    }

    for resolution_name, (width, height) in RESOLUTIONS.items():
        window = MainWindow(Scene(), AuditConfig())
        try:
            window.resize(QSize(width, height))
            window.show()
            window.activateWindow()
            window.raise_()
            window.canvas.setFocus()
            _settle(app)
            for language in LANGUAGES:
                window.set_language(language)
                window.activateWindow()
                window.raise_()
                _settle(app)
                window.canvas.setFocus()
                _settle(app)
                if not window.canvas.hasFocus():
                    raise RuntimeError(
                        f"canvas did not receive focus for {resolution_name}/{language}"
                    )
                QTest.keyClick(
                    window.canvas,
                    Qt.Key.Key_K,
                    Qt.KeyboardModifier.ControlModifier,
                )
                _settle(app)
                palette = window.command_palette
                if not palette.isVisible() or not palette.search_input.hasFocus():
                    raise RuntimeError(
                        "Ctrl+K did not open focused palette for "
                        f"{resolution_name}/{language}"
                    )
                if palette.results.count() != 19:
                    raise RuntimeError(
                        f"unexpected command count for {resolution_name}/{language}"
                    )
                if not _inside(palette.title_label, palette):
                    raise RuntimeError("palette title is clipped by its dialog")
                if not _inside(palette.search_input, palette):
                    raise RuntimeError("palette search input is clipped")
                if not _inside(palette.results, palette):
                    raise RuntimeError("palette results are clipped")

                palette_path = output / f"{resolution_name}_{language}_palette.png"
                window_path = output / f"{resolution_name}_{language}_window.png"
                _capture(palette, palette_path)
                _capture(window, window_path)
                palette_capture = _image_metadata(palette_path)
                window_capture = _image_metadata(window_path)
                manifest["captures"][f"{resolution_name}/{language}"] = {
                    "resolution": [width, height],
                    "files": {
                        palette_path.name: palette_capture,
                        window_path.name: window_capture,
                    },
                    "window": {
                        "geometry": _rect(window),
                        "capture": window_capture,
                    },
                    "palette": {
                        "visible": palette.isVisible(),
                        "focused_search": palette.search_input.hasFocus(),
                        "geometry": _rect(palette),
                        "title_geometry": _rect(palette.title_label),
                        "search_geometry": _rect(palette.search_input),
                        "results_geometry": _rect(palette.results),
                        "command_count": palette.results.count(),
                        "capture": palette_capture,
                    },
                }
                QTest.keyClick(palette.search_input, Qt.Key.Key_Escape)
                _settle(app)
                if palette.isVisible():
                    raise RuntimeError(
                        f"Escape did not close palette for {resolution_name}/{language}"
                    )
        finally:
            window.close()
            _settle(app)

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = run(args.output.resolve())
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
