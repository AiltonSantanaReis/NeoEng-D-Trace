"""Produce reproducible real-Qt evidence for the Pen tool user flows.

The script deliberately leaves human visual review pending.  It records the
exact source identity supplied by the caller, the real Qt event flows, the
model/history assertions, PNG hashes and a UTF-8/LF report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
from PIL import Image
from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QPoint, Qt, qVersion
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

import src.tools.base_tool as base_tool_module
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _Config:
    def get(self, key: str, default=None):
        del key
        return default

    def set(self, key: str, value) -> None:
        del key, value

    def save(self) -> None:
        return None


def _settle(app: QApplication, milliseconds: int = 80) -> None:
    app.processEvents()
    QTest.qWait(milliseconds)
    app.processEvents()


def _make_window(work: Path, app: QApplication) -> MainWindow:
    work.mkdir(parents=True, exist_ok=True)
    source = work / "fixture.png"
    pixels = np.zeros((220, 320, 4), dtype=np.uint8)
    pixels[:, :, :3] = (24, 28, 38)
    pixels[:, :, 3] = 255
    pixels[40:100, 40:100, :3] = (235, 235, 235)
    pixels[118:184, 132:212, :3] = (44, 170, 220)
    Image.fromarray(pixels, "RGBA").save(source)

    scene = Scene()
    scene.cmd = CommandManager(max_history=40)
    scene.image = pixels
    scene.image_path = str(source)
    scene.add_object("seed", [(40, 40), (100, 40), (100, 100), (40, 100)])
    scene.cmd.clear()

    window = MainWindow(scene, _Config())
    window._refresh_document_views(project_loaded=False)
    window.show()
    window.activateWindow()
    window.canvas.setFocus()
    _settle(app)
    return window


def _screen_point(window: MainWindow, point: tuple[int, int]) -> QPoint:
    converted = window.canvas.image_to_widget(*point)
    return QPoint(round(converted.x()), round(converted.y()))


def _click_image(window: MainWindow, point: tuple[int, int]) -> None:
    QTest.mouseClick(
        window.canvas,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _screen_point(window, point),
    )


def _save_capture(window: MainWindow, output: Path, name: str) -> dict[str, object]:
    path = output / name
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"Could not save capture: {name}")
    data = path.read_bytes()
    with Image.open(path) as image:
        dimensions = [int(image.width), int(image.height)]
    return {
        "path": name,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "dimensions": dimensions,
    }


def _close_window(window: MainWindow, app: QApplication) -> None:
    window._mark_document_clean()
    window.close()
    window.deleteLater()
    _settle(app, 40)


def _write_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def run(output: Path, source_commit: str, source_branch: str) -> dict[str, object]:
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []
    captures: list[dict[str, object]] = []
    checks: dict[str, object] = {}
    app = QApplication.instance() or QApplication([])

    def log(message: str) -> None:
        log_lines.append(message)

    try:
        log("start real-Qt Pen tool audit")
        positive = _make_window(output / "positive-work", app)
        try:
            positive.tool_palette.tool_buttons["pen_tool"].click()
            tool = positive.canvas._active_tool_object()
            before = set(positive.scene.objects)
            for point in ((225, 35), (305, 35), (305, 115)):
                _click_image(positive, point)
            QTest.mouseMove(
                positive.canvas,
                _screen_point(positive, (225, 35)),
            )
            _settle(app)
            if not tool._is_near_first_anchor((225.0, 35.0)):
                raise AssertionError("first anchor was not close-ready")
            captures.append(_save_capture(positive, output, "pen-close-preview.png"))
            _click_image(positive, (225, 35))
            _settle(app)
            created = set(positive.scene.objects) - before
            if len(created) != 1:
                raise AssertionError(f"expected one created object, got {created}")
            object_id = next(iter(created))
            beziers = positive.scene.objects[object_id].beziers
            if not beziers or beziers[-1][3] != beziers[0][0]:
                raise AssertionError("closed path terminal does not equal first anchor")
            if positive.scene.cmd.undo_count != 1:
                raise AssertionError("close did not create exactly one history entry")
            captures.append(_save_capture(positive, output, "pen-closed-persisted.png"))
            positive.reference_undo_button.click()
            _settle(app)
            if object_id in positive.scene.objects:
                raise AssertionError("Undo did not remove the Pen object")
            captures.append(_save_capture(positive, output, "pen-after-undo.png"))
            positive.reference_redo_button.click()
            _settle(app)
            if object_id not in positive.scene.objects:
                raise AssertionError("Redo did not restore the Pen object")
            captures.append(_save_capture(positive, output, "pen-after-redo.png"))
            checks["closed_path"] = "PASS"
            checks["undo_redo"] = "PASS"
            log("closed path, undo and redo: PASS")
        finally:
            _close_window(positive, app)

        invalid = _make_window(output / "invalid-work", app)
        original_warning = base_tool_module.QMessageBox.warning
        try:
            base_tool_module.QMessageBox.warning = (
                lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok
            )
            invalid.tool_palette.tool_buttons["pen_tool"].click()
            tool = invalid.canvas._active_tool_object()
            before_objects = set(invalid.scene.objects)
            before_history = invalid.scene.cmd.undo_count
            for point in ((225, 35), (285, 35), (285, 95)):
                _click_image(invalid, point)
            before_nodes = tuple(node.anchor for node in tool._nodes)
            _click_image(invalid, (225, 35))
            _settle(app)
            if set(invalid.scene.objects) != before_objects:
                raise AssertionError("invalid close mutated the scene")
            if tuple(node.anchor for node in tool._nodes) != before_nodes:
                raise AssertionError("invalid close discarded the preview nodes")
            if invalid.scene.cmd.undo_count != before_history:
                raise AssertionError("invalid close changed history")
            if "Invalid sampled" not in tool._last_error:
                raise AssertionError(
                    f"unexpected invalid-close error: {tool._last_error!r}"
                )
            captures.append(_save_capture(invalid, output, "pen-invalid-close.png"))
            checks["invalid_close_preserves_state"] = "PASS"
            log("invalid close preserves preview, model and history: PASS")
        finally:
            base_tool_module.QMessageBox.warning = original_warning
            _close_window(invalid, app)

        double_click = _make_window(output / "double-click-work", app)
        try:
            double_click.tool_palette.tool_buttons["pen_tool"].click()
            before = set(double_click.scene.objects)
            for point in ((225, 35), (305, 35), (305, 115)):
                _click_image(double_click, point)
            QTest.mouseDClick(
                double_click.canvas,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                _screen_point(double_click, (265, 75)),
            )
            _settle(app)
            created = set(double_click.scene.objects) - before
            if len(created) != 1:
                raise AssertionError("double-click did not create an open path")
            object_id = next(iter(created))
            beziers = double_click.scene.objects[object_id].beziers
            if not beziers or beziers[-1][3] == beziers[0][0]:
                raise AssertionError("double-click unexpectedly closed the path")
            captures.append(
                _save_capture(double_click, output, "pen-double-click-open.png")
            )
            checks["double_click_open_path"] = "PASS"
            log("double-click open path: PASS")
        finally:
            _close_window(double_click, app)

        log("QApplication lifecycle: PASS")
        status = "PASS_AUTOMATED_PENDING_HUMAN_VISUAL"
    except Exception as exc:
        status = "FAIL"
        log(f"failure: {type(exc).__name__}: {exc}")
        raise
    finally:
        app.processEvents()
        (output / "run.log").write_text(
            "\n".join(log_lines) + "\n", encoding="utf-8", newline="\n"
        )

    artifacts = captures + [
        _artifact_record(output / "run.log", "run.log"),
    ]
    report: dict[str, object] = {
        "schema": "neoeng.pen-tool-visual-audit",
        "status": status,
        "human_visual_review": "PENDING_USER_REVIEW",
        "source": {"commit": source_commit, "branch": source_branch},
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "pyside6": pyside_version,
            "qt": qVersion(),
            "qt_platform": __import__("os").environ.get("QT_QPA_PLATFORM"),
        },
        "checks": checks,
        "artifacts": artifacts,
        "limitations": [
            "Automated Qt assertions do not replace human visual review.",
            "The screenshots must be reviewed by the project owner on this exact SHA.",
        ],
    }
    _write_json(output / "report.json", report)
    _write_json(
        output / "artifact-index.json",
        {
            "schema": "neoeng.evidence-artifact-index",
            "package": output.name,
            "status": status,
            "audited_commit": source_commit,
            "files": artifacts + [{"path": "report.json"}],
            "index_excludes_itself": True,
        },
    )
    return report


def _artifact_record(path: Path, relative: str) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": relative,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-branch", required=True)
    args = parser.parse_args()
    report = run(args.output.resolve(), args.source_commit, args.source_branch)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
