"""Isolated E01-B backend bench; it never changes the product renderer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from PySide6 import __version__ as PYSIDE6_VERSION
from PySide6.QtCore import Qt, qVersion
from PySide6.QtGui import (
    QColor,
    QImage,
    QPainter,
    QRadialGradient,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication

SCENE = {
    "resolution": {"width": 640, "height": 360},
    "coordinates": {"origin": "top_left", "unit": "pixel", "x": "right", "y": "down"},
    "camera": {"projection": "orthographic", "position": [320.0, 180.0], "zoom": 1.0},
    "depth_layers": ["background", "textured_alpha", "particles", "light_overlay"],
    "texture": {"format": "RGBA8", "alpha": True, "size": [96, 96]},
    "particles": {"count": 48, "seed": 17, "visible": True},
    "light": {"mode": "radial_overlay", "alters_pixels": True},
}


def _draw_fixture(painter: QPainter, width: int, height: int) -> None:
    """Draw the same deterministic scene into either a raster or GL painter."""

    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.fillRect(0, 0, width, height, QColor("#111827"))

    # Background grid establishes a visible orthographic coordinate contract.
    painter.setPen(QColor("#26364b"))
    for x in range(0, width + 1, 40):
        painter.drawLine(x, 0, x, height)
    for y in range(0, height + 1, 40):
        painter.drawLine(0, y, width, y)

    # A deterministic RGBA texture with transparent corners and an alpha body.
    texture = QImage(96, 96, QImage.Format.Format_ARGB32_Premultiplied)
    texture.fill(Qt.GlobalColor.transparent)
    texture_painter = QPainter(texture)
    texture_painter.fillRect(0, 0, 96, 96, QColor(37, 99, 235, 180))
    texture_painter.setBrush(QColor(251, 191, 36, 210))
    texture_painter.setPen(Qt.PenStyle.NoPen)
    texture_painter.drawEllipse(12, 12, 72, 72)
    texture_painter.end()
    painter.drawImage(272, 132, texture)

    # Depth-order proxy: the documented layer order is painted in that order.
    painter.setPen(QColor("#e5e7eb"))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(240, 100, 160, 160)
    painter.drawText(20, 28, "E01-B backend fixture")

    # Fixed-seed particles; their positions are intentionally stable.
    painter.setPen(Qt.PenStyle.NoPen)
    for index in range(48):
        x = 40 + ((index * 73 + 17) % (width - 80))
        y = 48 + ((index * 47 + 29) % (height - 80))
        radius = 2 + (index % 3)
        painter.setBrush(QColor(244, 114, 182, 190))
        painter.drawEllipse(x, y, radius, radius)

    # Light pass visibly changes pixels and remains deterministic.
    gradient = QRadialGradient(320, 180, 170)
    gradient.setColorAt(0.0, QColor(253, 224, 71, 95))
    gradient.setColorAt(1.0, QColor(253, 224, 71, 0))
    painter.setBrush(gradient)
    painter.drawEllipse(150, 10, 340, 340)


def _sha256_image(image: QImage, path: Path) -> str:
    image.save(str(path), "PNG")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stats(samples_ms: list[float]) -> dict[str, float]:
    ordered = sorted(samples_ms)

    def percentile(percent: float) -> float:
        position = (len(ordered) - 1) * percent
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        fraction = position - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction

    return {
        "samples": float(len(ordered)),
        "p50_ms": percentile(0.50),
        "p95_ms": percentile(0.95),
        "p99_ms": percentile(0.99),
        "worst_ms": max(ordered),
    }


def _render_raster(output: Path) -> dict[str, Any]:
    image = QImage(640, 360, QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(image)
    start = time.perf_counter()
    _draw_fixture(painter, 640, 360)
    painter.end()
    first_ms = (time.perf_counter() - start) * 1000.0
    frame_path = output / "raster-frame.png"
    frame_hash = _sha256_image(image, frame_path)

    samples: list[float] = []
    for _ in range(35):
        candidate = QImage(640, 360, QImage.Format.Format_ARGB32_Premultiplied)
        candidate_painter = QPainter(candidate)
        start = time.perf_counter()
        _draw_fixture(candidate_painter, 640, 360)
        candidate_painter.end()
        samples.append((time.perf_counter() - start) * 1000.0)

    return {
        "backend": "qt-raster",
        "status": "PASS_LOCAL",
        "first_frame_ms": first_ms,
        "frame": {"path": frame_path.name, "sha256": frame_hash, "size": [640, 360]},
        "timing": _stats(samples),
        "resize": {"status": "NOT_APPLICABLE", "reason": "image backend"},
        "context_recovery": {"status": "NOT_APPLICABLE", "reason": "image backend"},
    }


class _OpenGLFixture(QOpenGLWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(320, 180)
        self.resize(640, 360)
        self.context_snapshot: dict[str, Any] = {}
        self.fixture = QImage(640, 360, QImage.Format.Format_ARGB32_Premultiplied)
        fixture_painter = QPainter(self.fixture)
        _draw_fixture(fixture_painter, 640, 360)
        fixture_painter.end()

    def initializeGL(self) -> None:  # noqa: N802 - Qt override
        context = self.context()
        depth_test_enabled = False
        if context is not None:
            functions = context.functions()
            functions.glEnable(0x0B71)  # GL_DEPTH_TEST
            functions.glDepthFunc(0x0203)  # GL_LEQUAL
            depth_test_enabled = True
        self.context_snapshot = {
            "api": "OpenGL",
            "vendor": None,
            "renderer": None,
            "version": None,
            "major": None,
            "minor": None,
            "profile": None,
            "depth_buffer_size": None,
            "samples": None,
            "depth_test_enabled": depth_test_enabled,
        }

    def paintGL(self) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.fixture)
        painter.end()


def _render_opengl(app: QApplication, output: Path) -> dict[str, Any]:
    widget = _OpenGLFixture()
    widget.show()
    app.processEvents()
    if not widget.isValid():
        widget.close()
        return {
            "backend": "qt-opengl-widget",
            "status": "NOT_TESTED",
            "reason": "QOpenGLWidget did not expose a valid context",
        }

    app.processEvents()
    start = time.perf_counter()
    frame = widget.grabFramebuffer()
    first_ms = (time.perf_counter() - start) * 1000.0
    frame_path = output / "opengl-frame.png"
    frame_hash = _sha256_image(frame, frame_path)
    samples: list[float] = []
    for _ in range(35):
        widget.update()
        app.processEvents()
        start = time.perf_counter()
        frame = widget.grabFramebuffer()
        samples.append((time.perf_counter() - start) * 1000.0)

    before_resize = [frame.width(), frame.height()]
    widget.resize(800, 450)
    app.processEvents()
    resized = widget.grabFramebuffer()
    resize_ok = [resized.width(), resized.height()] == [1600, 900]

    widget.makeCurrent()
    widget.doneCurrent()
    widget.show()
    widget.update()
    app.processEvents()
    recovered = widget.grabFramebuffer()
    recovery_ok = not recovered.isNull() and [
        recovered.width(),
        recovered.height(),
    ] == [1600, 900]
    widget.close()

    result = {
        "backend": "qt-opengl-widget",
        "status": "PASS_LOCAL" if resize_ok and recovery_ok else "FAIL",
        "first_frame_ms": first_ms,
        "frame": {"path": frame_path.name, "sha256": frame_hash, "size": [640, 360]},
        "timing": _stats(samples),
        "resize": {
            "status": "PASS_LOCAL" if resize_ok else "FAIL",
            "before": before_resize,
            "after": [resized.width(), resized.height()],
        },
        "context_recovery": {
            "status": "PASS_LOCAL" if recovery_ok else "FAIL",
            "frame_size": [recovered.width(), recovered.height()],
        },
        "context": widget.context_snapshot,
    }
    return result


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    raster = _render_raster(output)
    opengl = _render_opengl(app, output)
    result = {
        "schema": "neoeng.e01.backend-bench",
        "schema_version": 1,
        "status": (
            "PASS_LOCAL"
            if raster["status"] == "PASS_LOCAL" and opengl["status"] == "PASS_LOCAL"
            else "NOT_TESTED"
        ),
        "classification": "local-hardware-observation",
        "python": platform.python_version(),
        "pyside6": PYSIDE6_VERSION,
        "qt": qVersion(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "environment": {
            "QT_QPA_PLATFORM": os.environ.get("QT_QPA_PLATFORM", "default"),
            "scene": SCENE,
        },
        "candidates": [raster, opengl],
        "limits": [
            "local hardware observation is not a universal performance claim",
            "pixel hashes are recorded per backend and are not required to match "
            "across raster and OpenGL",
            "no product renderer or scene document was modified by this bench",
        ],
    }
    (output / "backend-bench.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output.resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS_LOCAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
