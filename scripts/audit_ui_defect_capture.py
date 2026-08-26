"""Reproducible UI defect audit for the dedicated scenario editor and Mask Viewer."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtTest import QTest
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "artifacts" / "ui-defect-fix-2026-08-18"
VIEWPORTS = {
    "compact_1280x720": (1280, 720),
    "compact_1366x768": (1366, 768),
    "desktop_1920x1080": (1920, 1080),
}


class AuditConfig:
    def get(self, key: str, default: Any = None) -> Any:
        del key
        return default

    def set(self, key: str, value: Any) -> None:
        del key, value

    def save(self) -> None:
        return None


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_scene() -> Scene:
    image = np.zeros((360, 540, 4), dtype=np.uint8)
    for y in range(image.shape[0]):
        image[y, :, :3] = (18 + y // 30, 22 + y // 28, 31 + y // 24)
    image[:, :, 3] = 255
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image = image
    scene.add_object(
        "audit_object",
        [(90, 70), (280, 70), (280, 240), (90, 240)],
        select=True,
    )
    scene.cmd.clear()
    return scene


def settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(180)
    app.processEvents()


def capture(widget: QWidget, path: Path) -> dict[str, Any]:
    if not widget.grab().save(str(path), "PNG"):
        raise RuntimeError(f"capture failed: {path.name}")
    with Image.open(path) as source:
        image = source.convert("RGBA")
        pixels = np.asarray(image)
        alpha = pixels[:, :, 3]
        border = np.concatenate(
            [pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]], axis=0
        )
        if image.width != widget.width() or image.height != widget.height():
            raise RuntimeError(f"Qt/PNG dimensions disagree for {path.name}")
        if int(alpha.min()) != 255 or int(alpha.max()) != 255:
            raise RuntimeError(f"alpha contract failed for {path.name}")
        if not np.any(border[:, :3] != 0):
            raise RuntimeError(f"empty PNG border for {path.name}")
        return {
            "file": path.name,
            "width": image.width,
            "height": image.height,
            "alpha": [int(alpha.min()), int(alpha.max())],
            "sha256": digest(path),
        }


def rect_in(widget: QWidget, parent: QWidget) -> QRect:
    point = widget.mapTo(parent, QPoint(0, 0))
    return QRect(point.x(), point.y(), widget.width(), widget.height())


def widget_clipping(widget: QWidget) -> list[dict[str, Any]]:
    failures = []
    for child in widget.findChildren(QWidget):
        if not child.isVisible() or child.width() <= 0 or child.height() <= 0:
            continue
        hint = child.minimumSizeHint()
        if hint.width() > child.width() + 1 or hint.height() > child.height() + 1:
            failures.append(
                {
                    "object": child.objectName() or child.__class__.__name__,
                    "geometry": [child.width(), child.height()],
                    "minimum_size_hint": [hint.width(), hint.height()],
                }
            )
    return failures


def annotated(path: Path, boxes: dict[str, QRect]) -> dict[str, Any]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    colors = [(0, 255, 120, 255), (255, 210, 40, 255), (255, 80, 160, 255)]
    for index, (name, rect) in enumerate(boxes.items()):
        draw.rectangle(
            [rect.left(), rect.top(), rect.right(), rect.bottom()],
            outline=colors[index % len(colors)],
            width=3,
        )
        draw.text((rect.left() + 5, rect.top() + 5), name, fill=colors[index % len(colors)])
    output = path.with_name(path.stem + "_annotated.png")
    image.save(output, "PNG")
    return {"file": output.name, "sha256": digest(output)}


def run(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    project = output / "ui_fixture.ndtproj"
    project.write_bytes(b"ui-defect-audit-fixture-v1\n")
    scene = fixture_scene()
    window = MainWindow(scene, AuditConfig())
    window._project_path = project
    window.scenario_authoring.bind_project(project)
    window.scenario_authoring.reset()
    window.show()
    settle(app)
    source_parent_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    results: dict[str, Any] = {
        "source_parent_commit": source_parent_commit,
        "viewports": {},
        "source_files": {},
    }
    try:
        if window.layers.tabs.count() != 1:
            raise RuntimeError("scenario authoring is still embedded in MainWindow Layers")
        if (
            window.act_gizmo not in window.top_command_contract.items("context")
        ):
            raise RuntimeError(
                "gizmo action is missing from the semantic context group"
            )
        window.open_scenario_editor()
        editor = window.scenario_editor_window
        if editor is None:
            raise RuntimeError("dedicated scenario editor was not created")
        editor.show()
        settle(app)
        for label, size in VIEWPORTS.items():
            window.resize(QSize(*size))
            settle(app)
            main_path = output / f"{label}_main.png"
            main_capture = capture(window, main_path)
            main_boxes = {
                "canvas": rect_in(window.canvas, window),
                "reference_top_toolbar": rect_in(window.reference_top_toolbar, window),
            }
            if main_boxes["canvas"].intersects(
                main_boxes["reference_top_toolbar"]
            ):
                raise RuntimeError(
                    f"main canvas overlaps visible top toolbar at {label}"
                )
            main_clipping = widget_clipping(window)
            window.canvas._gizmo_feedback = "T: (10.0, -2.0, 0.0)  S: (1.0, 1.0, 1.0)"
            window.canvas.update()
            settle(app)
            feedback_path = output / f"{label}_gizmo_feedback.png"
            feedback_capture = capture(window, feedback_path)
            feedback_image = QImage(640, 480, QImage.Format.Format_ARGB32)
            feedback_painter = QPainter(feedback_image)
            try:
                feedback_rect = window.canvas._gizmo_feedback_rect(feedback_painter)
            finally:
                feedback_painter.end()
            if window.canvas.gizmo is None:
                raise RuntimeError(f"gizmo was not initialized at {label}")
            center = window.canvas.gizmo.screen_pos
            radius = (
                float(window.canvas.gizmo.arm_length)
                + float(window.canvas.gizmo.arrow_size)
                + 12.0
            )
            gizmo_rect = QRect(
                int(center.x() - radius),
                int(center.y() - radius),
                int(radius * 2),
                int(radius * 2),
            )
            feedback_qrect = QRect(
                int(feedback_rect.left()),
                int(feedback_rect.top()),
                int(feedback_rect.width()),
                int(feedback_rect.height()),
            )
            if feedback_qrect.intersects(gizmo_rect):
                raise RuntimeError(f"gizmo feedback overlaps gizmo at {label}")
            canvas_origin = main_boxes["canvas"].topLeft()
            feedback_window_rect = feedback_qrect.translated(canvas_origin)
            gizmo_window_rect = gizmo_rect.translated(canvas_origin)
            feedback_annotation = annotated(
                feedback_path,
                {"feedback": feedback_window_rect, "gizmo": gizmo_window_rect},
            )
            window.canvas._gizmo_feedback = ""
            editor.resize(QSize(*size))
            settle(app)
            editor_path = output / f"{label}_scenario_editor.png"
            editor_capture = capture(editor, editor_path)
            splitter = editor.centralWidget()
            editor_boxes = {
                "scenario_canvas": rect_in(editor.canvas, editor),
                "scenario_inspector": rect_in(editor.scenario_panel.parentWidget(), editor),
            }
            if editor_boxes["scenario_canvas"].intersects(editor_boxes["scenario_inspector"]):
                raise RuntimeError(f"scenario canvas overlaps inspector at {label}")
            editor_clipping = widget_clipping(editor)
            if editor.scenario_panel.name_edit.height() < 20:
                raise RuntimeError(f"scenario inspector clipped at {label}")
            results["viewports"][label] = {
                "main": main_capture,
                "main_annotated": annotated(main_path, main_boxes),
                "main_clipping": main_clipping,
                "gizmo_feedback": feedback_capture,
                "gizmo_feedback_annotated": feedback_annotation,
                "gizmo_feedback_geometry": {
                    "feedback": [feedback_qrect.x(), feedback_qrect.y(), feedback_qrect.width(), feedback_qrect.height()],
                    "gizmo": [gizmo_rect.x(), gizmo_rect.y(), gizmo_rect.width(), gizmo_rect.height()],
                    "window_feedback": [feedback_window_rect.x(), feedback_window_rect.y(), feedback_window_rect.width(), feedback_window_rect.height()],
                    "window_gizmo": [gizmo_window_rect.x(), gizmo_window_rect.y(), gizmo_window_rect.width(), gizmo_window_rect.height()],
                    "coordinate_space": "canvas-local for feedback/gizmo; window for window_* fields",
                    "overlap": False,
                },
                "scenario_editor": editor_capture,
                "scenario_annotated": annotated(editor_path, editor_boxes),
                "scenario_clipping": editor_clipping,
                "geometries": {
                    "main": {name: [r.x(), r.y(), r.width(), r.height()] for name, r in main_boxes.items()},
                    "scenario": {name: [r.x(), r.y(), r.width(), r.height()] for name, r in editor_boxes.items()},
                },
                "xray_buttons": len(window.scenario_editor_window.scenario_panel.findChildren(QWidget)),
            }

        mask = window.open_mask_viewer()
        settle(app)
        if mask is None:
            mask = window._mask_viewer_dialog
        if mask is None:
            raise RuntimeError("Mask Viewer did not open")
        mask_path = output / "mask_viewer_xray_controls.png"
        mask_capture = capture(mask, mask_path)
        modes = []
        for index, button in enumerate(mask.view_mode_buttons):
            button.click()
            settle(app)
            if mask.viewer.get_display_mode() != index:
                raise RuntimeError(f"Mask Viewer mode {index} did not activate")
            modes.append({"index": index, "text": button.text(), "checked": button.isChecked()})
        results["mask_viewer"] = {
            "capture": mask_capture,
            "annotated": annotated(mask_path, {"controls": rect_in(mask.findChild(QWidget, "mask_controls_scroll"), mask)}),
            "modes": modes,
            "controls_scroll_present": mask.findChild(QWidget, "mask_controls_scroll") is not None,
        }
        mask.close()
        results["checks"] = {
            "layers_scenario_separation": True,
            "gizmo_semantic_contract": True,
            "mask_xray_modes": True,
            "no_unexpected_clipping": all(
                not item["main_clipping"] and not item["scenario_clipping"]
                for item in results["viewports"].values()
            ),
        }
        if not results["checks"]["no_unexpected_clipping"]:
            details = {
                name: {
                    "main": item["main_clipping"],
                    "scenario": item["scenario_clipping"],
                }
                for name, item in results["viewports"].items()
                if item["main_clipping"] or item["scenario_clipping"]
            }
            raise RuntimeError(
                "Qt reported a visible widget smaller than minimumSizeHint: "
                + json.dumps(details, ensure_ascii=False)
            )
        results["fixture"] = {"file": project.name, "sha256": digest(project)}
        for relative in (
            "src/ui/scenario_editor_window.py",
            "src/ui/scenario_authoring_actions.py",
            "src/ui/scenario_panel.py",
            "src/ui/canvas_view.py",
            "src/ui/mask_viewer.py",
            "src/ui/main_window.py",
            "src/ui/top_command_contract.py",
            "src/ui/command_bindings.py",
            "tests/test_ui_defect_regressions.py",
        ):
            path = ROOT / relative
            results["source_files"][relative] = {"bytes": path.stat().st_size, "sha256": digest(path)}
        (output / "manifest.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return results
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        settle(app)


if __name__ == "__main__":
    output_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    result = run(output_arg)
    print(json.dumps(result, indent=2, ensure_ascii=False))
