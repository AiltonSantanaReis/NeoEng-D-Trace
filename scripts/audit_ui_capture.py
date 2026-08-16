"""Capture reproducible MainWindow states for the visual UI audit.

The script uses the same Scene, CommandManager and MainWindow contracts as the
application. It does not monkeypatch product widgets or fabricate validation
dialogs. The validation capture exercises CollisionPanel's real no-shapes
message path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PySide6.QtCore import QSize, QTimer  # noqa: E402
from PySide6.QtGui import QImage  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from src.core.commands import CommandManager  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "artifacts" / "ui-audit"
RESOLUTIONS = {
    "1080p_FHD": (1920, 1080),
    "768p_Minima": (1366, 768),
    "720p_Compacta": (1280, 720),
}


class AuditConfig:
    """Minimal config adapter implementing the MainWindow contract."""

    def get(self, key: str, default: Any = None) -> Any:
        return default

    def set(self, key: str, value: Any) -> None:
        del key, value

    def save(self) -> None:
        return None


def _source_image() -> np.ndarray:
    image = np.zeros((480, 720, 3), dtype=np.uint8)
    for y in range(image.shape[0]):
        image[y, :, :] = (18 + y // 20, 22 + y // 20, 30 + y // 18)
    cv2.rectangle(image, (80, 80), (315, 350), (180, 210, 230), thickness=-1)
    cv2.circle(image, (200, 215), 48, (65, 75, 85), thickness=-1)
    cv2.fillPoly(
        image,
        [
            np.asarray(
                [[410, 100], [620, 100], [620, 250], [520, 250], [520, 380], [410, 380]]
            )
        ],
        (220, 190, 145),
    )
    return image


def _prepare_project(output: Path) -> tuple[Scene, Path]:
    image_path = output / "ui-audit-fixture.png"
    project_path = output / "ui-audit-fixture.ndtproj"
    image = _source_image()
    if not cv2.imwrite(str(image_path), image):
        raise RuntimeError("could not write the UI audit fixture image")

    scene = Scene()
    scene.cmd = CommandManager()
    scene.load_image(image, str(image_path))
    scene.image_path = image_path.name
    scene.image_path_kind = "relative"
    scene.add_object(
        "rectangle-object",
        [(80, 80), (315, 80), (315, 350), (80, 350)],
        select=False,
    )
    scene.add_object(
        "concave-object",
        [(410, 100), (620, 100), (620, 250), (520, 250), (520, 380), (410, 380)],
        select=False,
    )
    scene.save_project(str(project_path))

    loaded = Scene()
    loaded.cmd = CommandManager()
    loaded.load_project(str(project_path))
    loaded.attach_project_image(image)
    return loaded, project_path


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _open_panels(window: MainWindow, width: int) -> None:
    if window._compact_layout:
        window.compact_panel_tabs.setCurrentWidget(window.side_panel)
        return

    collision_width = 360 if width >= 1280 else 320
    right_width = 320 if width >= 1366 else 290
    window.desktop_panel_splitter.setSizes([right_width, collision_width])
    window.right_splitter.setSizes([230, 180, 180])
    window.collision_panel.show()
    window.side_panel.show()
    window.layers.show()
    window.groups.show()


def _settle(app: QApplication, milliseconds: int = 180) -> None:
    app.processEvents()
    QTest.qWait(milliseconds)
    app.processEvents()


def _capture(window: MainWindow, path: Path) -> None:
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"could not save screenshot {path.name}")


def _capture_size(path: Path) -> list[int]:
    image = QImage(str(path))
    if image.isNull():
        raise RuntimeError(f"could not read screenshot {path.name}")
    return [image.width(), image.height()]


def _new_window(
    scene: Scene,
    *,
    project_path: Path | None = None,
    project_loaded: bool,
) -> MainWindow:
    window = MainWindow(scene, AuditConfig())
    if project_path is not None:
        window._project_path = project_path
        window._document_name = project_path.name
    window._refresh_document_views(project_loaded=project_loaded)
    window.show()
    return window


def _capture_validation_message(
    app: QApplication, window: MainWindow, path: Path
) -> dict[str, Any]:
    message_data: dict[str, Any] = {}

    def capture_and_close() -> None:
        boxes = [
            widget
            for widget in app.topLevelWidgets()
            if isinstance(widget, QMessageBox) and widget.isVisible()
        ]
        if not boxes:
            return
        box = boxes[-1]
        message_data.update(
            {
                "title": box.windowTitle(),
                "text": box.text(),
                "informative_text": box.informativeText(),
            }
        )
        if not box.grab().save(str(path), "PNG"):
            raise RuntimeError(f"could not save screenshot {path.name}")
        box.accept()

    QTimer.singleShot(100, capture_and_close)
    window.collision_panel._on_batch_test()
    _settle(app)
    if not message_data:
        raise RuntimeError("CollisionPanel did not open its real validation message")
    return message_data


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)

    scene, project_path = _prepare_project(output)

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generator": "scripts/audit_ui_capture.py",
        "platform": platform.platform(),
        "python": sys.version,
        "project_fixture": _digest(project_path),
        "image_fixture": _digest(output / "ui-audit-fixture.png"),
        "captures": {},
    }

    for label, (width, height) in RESOLUTIONS.items():
        base_path = output / f"{label}_01_sem_projeto.png"
        empty_scene = Scene()
        empty_scene.cmd = CommandManager()
        empty_window = _new_window(empty_scene, project_loaded=False)
        try:
            empty_window.resize(QSize(width, height))
            _open_panels(empty_window, width)
            _settle(app)
            _capture(empty_window, base_path)
            actual_window_size = [empty_window.width(), empty_window.height()]
            actual_capture_size = _capture_size(base_path)
        finally:
            empty_window.close()
            _settle(app, 20)

        project_window = _new_window(
            scene,
            project_path=project_path,
            project_loaded=True,
        )
        try:
            project_window.resize(QSize(width, height))
            _open_panels(project_window, width)
            scene.select_object("rectangle-object")
            _settle(app)

            project_path_capture = output / f"{label}_02_projeto_paineis.png"
            _capture(project_window, project_path_capture)

            # Exercise the real transform transaction to expose the live gizmo feedback.
            canvas = project_window.canvas
            feedback_path = output / f"{label}_04_gizmo_feedback.png"
            if not canvas._begin_gizmo_object_gesture():
                raise RuntimeError("Could not begin the real gizmo transaction")
            canvas._gizmo_active = True
            canvas._gizmo_operation = canvas.gizmo.ROTATE_Z
            canvas._preview_gizmo_transform(rotation=45.0)
            _settle(app)
            _capture(project_window, feedback_path)
            canvas._cancel_gizmo_gesture()
            _settle(app, 20)
            validation_window_path = output / f"{label}_03_validacao_janela.png"
            validation_modal_path = output / f"{label}_03_validacao_modal.png"
            if project_window._compact_layout:
                project_window.compact_panel_tabs.setCurrentWidget(
                    project_window.collision_panel
                )
                _settle(app)
            _capture(project_window, validation_window_path)
            message = _capture_validation_message(
                app, project_window, validation_modal_path
            )
            manifest["captures"][label] = {
                "requested_size": [width, height],
                "actual_window_size": actual_window_size,
                "actual_capture_size": actual_capture_size,
                "files": {
                    base_path.name: _digest(base_path),
                    project_path_capture.name: _digest(project_path_capture),
                    feedback_path.name: _digest(feedback_path),
                    validation_window_path.name: _digest(validation_window_path),
                    validation_modal_path.name: _digest(validation_modal_path),
                },
                "validation_message": message,
            }
        finally:
            project_window.close()
            _settle(app, 20)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="directory for PNGs, fixtures and manifest",
    )
    args = parser.parse_args()
    manifest = run(args.output.resolve())
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
