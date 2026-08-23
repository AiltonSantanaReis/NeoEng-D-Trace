"""Reproducible real-Qt Stage 6 gizmo audit on Windows."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

# The shared headless capture module sets a default at import time.
# This auditor must exercise the native Windows Qt backend.
os.environ["QT_QPA_PLATFORM"] = "windows"

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from PySide6.QtCore import QPoint, QPointF, QRect, QSize  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from scripts.audit_ui_capture import (  # noqa: E402
    RESOLUTIONS,
    _capture,
    _new_window,
    _prepare_project,
    _settle,
)
from src.tools.polygon_edit_tool import PolygonEditTool  # noqa: E402
from src.ui import canvas_view as canvas_module  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402
from src.ui.theme_tokens import THEME_TOKENS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = (
    ROOT / "docs" / "evidence" / "artifacts" / "ui-modernization-stage6-20260822"
)
RAW_ROOT = EVIDENCE_ROOT / "windows-captures"
ANNOTATED_ROOT = EVIDENCE_ROOT / "windows-visual-audit"
REPORT_PATH = EVIDENCE_ROOT / "stage6-gizmo-report.json"


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _rect_in(child: Any, root: Any) -> QRect:
    top_left = child.mapTo(root, QPoint(0, 0))
    return QRect(top_left.x(), top_left.y(), child.width(), child.height())


def _rect_payload(rect: QRect) -> list[int]:
    return [rect.x(), rect.y(), rect.width(), rect.height()]


def _scale_rect(rect: QRect, scale: float) -> QRect:
    return QRect(
        round(rect.x() * scale),
        round(rect.y() * scale),
        round(rect.width() * scale),
        round(rect.height() * scale),
    )


def _inside(inner: QRect, outer: QRect) -> bool:
    return outer.contains(inner.topLeft()) and outer.contains(inner.bottomRight())


def _intersection_area(first: QRect, second: QRect) -> int:
    intersection = first.intersected(second)
    return max(0, intersection.width()) * max(0, intersection.height())


def _png_contract(path: Path, expected_size: tuple[int, int]) -> dict[str, Any]:
    with Image.open(path) as source:
        source.verify()
    with Image.open(path) as source:
        image = source.convert("RGBA")
        info_keys = sorted(source.info)
    decoded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if decoded is None:
        raise RuntimeError(f"OpenCV could not decode {path.name}")
    if (image.width, image.height) != expected_size:
        raise RuntimeError(f"unexpected dimensions for {path.name}")
    if tuple(decoded.shape[:2][::-1]) != expected_size:
        raise RuntimeError(f"Pillow/OpenCV dimensions disagree for {path.name}")
    pixels = np.asarray(image)
    alpha = pixels[:, :, 3]
    if int(alpha.min()) != 255 or int(alpha.max()) != 255:
        raise RuntimeError(f"alpha contract failed for {path.name}")
    return {
        "size": [image.width, image.height],
        "mode": image.mode,
        "alpha": [int(alpha.min()), int(alpha.max())],
        "png_info_keys": info_keys,
        **_digest(path),
    }


def _palette_check(path: Path) -> dict[str, Any]:
    with Image.open(path) as source:
        rgb = np.asarray(source.convert("RGB"))
    colors = {tuple(int(channel) for channel in color) for color in rgb.reshape(-1, 3)}
    expected = []
    for token in THEME_TOKENS.audit_palette:
        expected.append(
            {
                "token": token,
                "present": tuple(bytes.fromhex(token[1:])) in colors,
            }
        )
    present = sum(1 for item in expected if item["present"])
    if present < 4:
        raise RuntimeError(f"theme palette coverage too low for {path.name}")
    return {"present_count": present, "expected": expected}


def _annotate(path: Path, boxes: dict[str, QRect]) -> dict[str, Any]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    colors = [(80, 220, 255, 255), (255, 225, 80, 255), (255, 100, 190, 255)]
    for index, (name, rect) in enumerate(boxes.items()):
        color = colors[index % len(colors)]
        draw.rectangle(
            [rect.left(), rect.top(), rect.right(), rect.bottom()],
            outline=color,
            width=3,
        )
        draw.text((rect.left() + 5, rect.top() + 5), name, fill=color)
    target = ANNOTATED_ROOT / f"{path.stem}_annotated.png"
    image.save(target, "PNG")
    return {"file": target.name, **_digest(target)}


def _transform_panel_contract(window: Any, failures: list[str]) -> dict[str, Any]:
    panel = window.side_panel
    panel_rect = _rect_in(panel, window)
    if not _inside(panel_rect, window.rect()):
        failures.append("transform panel escapes main window")
    fields = (
        "position_x",
        "position_y",
        "position_z",
        "rotation_x",
        "rotation_y",
        "rotation_z",
        "scale_x",
        "scale_y",
        "scale_z",
    )
    geometry: dict[str, list[int]] = {}
    for name in fields:
        widget = getattr(panel, name)
        rect = _rect_in(widget, window)
        geometry[name] = _rect_payload(rect)
        if not widget.isVisible():
            failures.append(f"transform field is not visible: {name}")
        if not _inside(rect, panel_rect):
            failures.append(f"transform field escapes side panel: {name}")
        if rect.width() < 40 or rect.height() < 12:
            failures.append(f"transform field is clipped: {name}")
    return {
        "side_panel_geometry": _rect_payload(panel_rect),
        "transform_group_geometry": _rect_payload(
            _rect_in(panel.transform_group, window)
        ),
        "transform_fields_geometry": geometry,
    }


def _state_capture(
    app: QApplication,
    window: Any,
    scene: Any,
    label: str,
    state: str,
    failures: list[str],
) -> dict[str, Any]:
    canvas = window.canvas
    panel_contract = _transform_panel_contract(window, failures)
    path = RAW_ROOT / f"{label}_{state}.png"
    _settle(app, 60)
    _capture(window, path)
    scale = float(window.devicePixelRatio())
    expected_size = (
        round(window.width() * scale),
        round(window.height() * scale),
    )
    png = _png_contract(path, expected_size)
    palette = _palette_check(path)
    canvas_rect = _rect_in(canvas, window)
    gizmo_rect = QRect()
    gizmo_bounds = QRect()
    if canvas.gizmo is None:
        failures.append(f"{label}/{state}: production gizmo was not created")
    else:
        canvas._update_gizmo_screen_position()
        gizmo_bounds = canvas.gizmo.visual_bounds().toRect()
        gizmo_rect = gizmo_bounds.translated(canvas_rect.topLeft())
        if not _inside(gizmo_bounds, canvas.rect()):
            failures.append(f"{label}/{state}: gizmo bounds escape canvas")
    feedback_rect = QRect()
    if canvas._gizmo_feedback:
        painter = canvas_module.QPainter()
        painter.begin(canvas)
        feedback_rect = canvas._gizmo_feedback_rect(painter).toRect()
        painter.end()
        if not _inside(feedback_rect, canvas.rect()):
            failures.append(f"{label}/{state}: feedback escapes canvas")
        if _intersection_area(feedback_rect, gizmo_bounds) > 0:
            failures.append(f"{label}/{state}: feedback overlaps gizmo")
    boxes = {"canvas": _scale_rect(canvas_rect, scale)}
    if gizmo_rect.isValid():
        boxes["gizmo"] = _scale_rect(gizmo_rect, scale)
    annotation = _annotate(path, boxes)
    return {
        "state": state,
        "file": path.relative_to(EVIDENCE_ROOT).as_posix(),
        "logical_window_size": [window.width(), window.height()],
        "device_pixel_ratio": scale,
        "physical_capture_size": expected_size,
        "png": png,
        "palette": palette,
        "canvas_geometry": _rect_payload(canvas_rect),
        "gizmo_geometry_canvas": _rect_payload(gizmo_bounds),
        "gizmo_geometry_window": _rect_payload(gizmo_rect),
        "feedback_geometry_canvas": _rect_payload(feedback_rect),
        "feedback": canvas._gizmo_feedback,
        "annotation": annotation,
        "selected_ids": list(canvas._selected_object_ids()),
        "scene_object_count": len(scene.objects),
        **panel_contract,
    }


def run() -> dict[str, Any]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    ANNOTATED_ROOT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    if app.platformName().lower() != "windows":
        raise RuntimeError(
            f"Stage6 real-Qt audit requires Windows backend, got {app.platformName()}"
        )
    scene, project_path = _prepare_project(RAW_ROOT)
    failures: list[str] = []
    captures: dict[str, Any] = {}
    for label, (width, height) in RESOLUTIONS.items():
        window = _new_window(scene, project_path=project_path, project_loaded=True)
        window.resize(QSize(width, height))
        _settle(app, 80)
        scene.select_object("rectangle-object")
        window.canvas._gizmo_enabled = True
        window.canvas.update()
        _settle(app, 80)
        try:
            captures[f"{label}/selected"] = _state_capture(
                app, window, scene, label, "01_selected", failures
            )
            center = window.canvas._update_gizmo_screen_position()
            if center is None:
                failures.append(f"{label}: no gizmo center for hover")
            else:
                window.canvas.gizmo.update_hover(
                    QPointF(
                        center.x() + window.canvas.gizmo.rotation_radius,
                        center.y(),
                    )
                )
            window.canvas.update()
            captures[f"{label}/hover"] = _state_capture(
                app, window, scene, label, "02_hover", failures
            )
            if not window.canvas._begin_gizmo_object_gesture():
                failures.append(f"{label}: could not begin real gizmo transaction")
            else:
                window.canvas._gizmo_active = True
                window.canvas._gizmo_operation = window.canvas.gizmo.ROTATE_Z
                window.canvas._preview_gizmo_transform(rotation=45.0)
                captures[f"{label}/feedback"] = _state_capture(
                    app, window, scene, label, "03_feedback", failures
                )
                result = window.canvas._finish_gizmo_gesture()
                if result is None or result.status.name != "APPLIED":
                    failures.append(f"{label}: real gizmo commit was not applied")
                undo = scene.cmd.undo(scene)
                if undo.status.name != "APPLIED":
                    failures.append(f"{label}: real gizmo undo was not applied")
                window.canvas.update()
                captures[f"{label}/undo"] = _state_capture(
                    app, window, scene, label, "04_undo", failures
                )

            panel = window.side_panel
            panel.position_x.setValue(
                float(scene.objects["rectangle-object"].position[0]) + 18.0
            )
            panel.position_y.setValue(
                float(scene.objects["rectangle-object"].position[1]) + 9.0
            )
            panel.position_z.setValue(7.0)
            panel.rotation_z.setValue(12.0)
            panel.scale_x.setValue(1.1)
            panel.scale_y.setValue(0.9)
            panel._on_apply_transform()
            actual_position = tuple(scene.objects["rectangle-object"].position)
            expected_position = (
                panel.position_x.value(),
                panel.position_y.value(),
                7.0,
            )
            if any(
                abs(actual - expected) > 1e-6
                for actual, expected in zip(actual_position, expected_position)
            ):
                failures.append(f"{label}: numeric transform was not applied")
            window.canvas.update()
            captures[f"{label}/numeric"] = _state_capture(
                app, window, scene, label, "05_numeric", failures
            )
            numeric_undo = scene.cmd.undo(scene)
            if numeric_undo.status.name != "APPLIED":
                failures.append(f"{label}: numeric transform undo was not applied")
            window.canvas.update()
            captures[f"{label}/numeric_undo"] = _state_capture(
                app, window, scene, label, "06_numeric_undo", failures
            )

            vertex_tool = PolygonEditTool(window.canvas)
            window.canvas.set_tool(vertex_tool.interface())
            vertex_tool.selected_polygon_id = "rectangle-object"
            vertex_tool.selected_vertex = 0
            window.canvas._gizmo_enabled = True
            window.canvas._update_gizmo_screen_position()
            window.canvas._gizmo_operation = window.canvas.gizmo.TRANSLATE_XY
            vertex_origin = tuple(scene.objects["rectangle-object"].polygon[0])
            if not window.canvas._begin_gizmo_vertex_gesture():
                failures.append(f"{label}: vertex gizmo transaction did not begin")
            else:
                target = (vertex_origin[0] + 11, vertex_origin[1] + 7)
                window.canvas._preview_gizmo_vertex(
                    window.canvas.image_to_widget(*target)
                )
                captures[f"{label}/vertex"] = _state_capture(
                    app, window, scene, label, "07_vertex", failures
                )
                vertex_result = window.canvas._finish_gizmo_gesture()
                if vertex_result is None or vertex_result.status.name != "APPLIED":
                    failures.append(f"{label}: vertex gizmo commit was not applied")
                vertex_undo = scene.cmd.undo(scene)
                if vertex_undo.status.name != "APPLIED":
                    failures.append(f"{label}: vertex gizmo undo was not applied")
                window.canvas.update()
                captures[f"{label}/vertex_undo"] = _state_capture(
                    app, window, scene, label, "08_vertex_undo", failures
                )
        finally:
            window.close()
            _settle(app, 30)
    report = {
        "schema_version": 1,
        "stage": "Etapa 6 — Gizmo profissional",
        "decision": "PASS" if not failures else "FAIL",
        "source_state": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean": not bool(_git("status", "--porcelain")),
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "qt_platform": app.platformName(),
        },
        "resolutions": {name: list(size) for name, size in RESOLUTIONS.items()},
        "states_per_resolution": [
            "selected",
            "hover",
            "feedback",
            "undo",
            "numeric",
            "numeric_undo",
            "vertex",
            "vertex_undo",
        ],
        "capture_count": len(captures),
        "captures": captures,
        "failures": failures,
        "raw_capture_directory": "windows-captures",
        "annotated_capture_directory": "windows-visual-audit",
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "decision": report["decision"],
                "capture_count": report["capture_count"],
                "failure_count": len(failures),
                "qt_platform": app.platformName(),
                "report": REPORT_PATH.relative_to(ROOT).as_posix(),
            },
            sort_keys=True,
        )
    )
    return report


if __name__ == "__main__":
    raise SystemExit(0 if run()["decision"] == "PASS" else 1)
