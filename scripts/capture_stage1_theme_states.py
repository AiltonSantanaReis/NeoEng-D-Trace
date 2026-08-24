"""Capture runtime evidence for the Stage 1 QSS interaction states.

This is an isolated verification fixture.  It imports the production QSS but
does not alter production widgets or source files.
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

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QVBoxLayout, QWidget

from src.ui.theme_qss import QSS
from src.ui.theme_tokens import THEME_TOKENS

RESOLUTIONS = {
    "720p_Compacta": (1280, 720),
    "768p_Minima": (1366, 768),
    "1080p_FHD": (1920, 1080),
}
STATES = ("normal", "hover", "pressed", "checked", "disabled", "focus")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rgb(image: Any, point: QPoint) -> list[int]:
    color = QColor(image.pixel(point))
    return [color.red(), color.green(), color.blue(), color.alpha()]


def _capture_state(window: QWidget, button: QPushButton, edit: QLineEdit, state: str) -> Any:
    button.setEnabled(state != "disabled")
    button.setCheckable(state == "checked")
    button.setChecked(state == "checked")
    edit.clearFocus()
    button.clearFocus()
    window.show()
    window.activateWindow()
    QApplication.processEvents()
    if state == "focus":
        QTest.mouseClick(edit, Qt.LeftButton)  # type: ignore[name-defined]
        edit.setFocus(Qt.FocusReason.OtherFocusReason)
        QApplication.processEvents()
    if state == "hover":
        QTest.mouseMove(button, button.rect().center())
    elif state == "pressed":
        QTest.mouseMove(button, button.rect().center())
        QTest.mousePress(button, Qt.LeftButton)  # type: ignore[name-defined]
    QApplication.processEvents()
    image = window.grab().toImage()
    point = button.mapTo(window, QPoint(8, button.height() // 2))
    focus_point = edit.mapTo(window, QPoint(1, 0))
    evidence = {
        "state": state,
        "button_geometry": [button.x(), button.y(), button.width(), button.height()],
        "focus_widget_geometry": [edit.x(), edit.y(), edit.width(), edit.height()],
        "button_background_sample_rgba": _rgb(image, point),
        "focus_border_sample_rgba": _rgb(image, focus_point),
        "focus_widget_has_focus": edit.hasFocus(),
    }
    if state == "pressed":
        QTest.mouseRelease(button, Qt.LeftButton)  # type: ignore[name-defined]
    return image, evidence


def capture(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    files: dict[str, dict[str, Any]] = {}
    all_evidence: list[dict[str, Any]] = []
    for resolution, (width, height) in RESOLUTIONS.items():
        window = QWidget()
        window.setObjectName("stage1_state_fixture")
        window.resize(width, height)
        layout = QVBoxLayout(window)
        layout.setContentsMargins(24, 24, 24, 24)
        button = QPushButton("Stage 1 state")
        button.setObjectName("stage1_state_button")
        button.setMinimumSize(180, 44)
        edit = QLineEdit()
        edit.setObjectName("stage1_focus_target")
        edit.setPlaceholderText("Focus target")
        layout.addWidget(button)
        layout.addWidget(edit)
        for state in STATES:
            image, evidence = _capture_state(window, button, edit, state)
            filename = f"{resolution}_stage1_{state}.png"
            path = output / filename
            image.save(str(path), "PNG")
            entry = {
                "path": filename,
                "sha256": _sha256(path),
                "resolution": [width, height],
                "dpi_percent": 100,
                **evidence,
            }
            files[filename] = entry
            all_evidence.append(entry)
        window.close()
        window.deleteLater()
    samples_by_state: dict[str, set[tuple[int, ...]]] = {}
    for item in all_evidence:
        samples_by_state.setdefault(item["state"], set()).add(tuple(item["button_background_sample_rgba"]))
    state_samples = {
        state: sorted(samples_by_state.get(state, set())) for state in STATES
    }
    state_distinctness = {
        "normal": bool(state_samples["normal"]),
        "hover": bool(state_samples["hover"]) and state_samples["hover"] != state_samples["normal"],
        "pressed": bool(state_samples["pressed"]) and state_samples["pressed"] != state_samples["normal"],
        "checked": bool(state_samples["checked"]) and state_samples["checked"] != state_samples["normal"],
        "disabled": bool(state_samples["disabled"]) and state_samples["disabled"] != state_samples["normal"],
        "focus": all(
            item["focus_widget_has_focus"]
            and item["focus_border_sample_rgba"] != all_evidence[0]["focus_border_sample_rgba"]
            for item in all_evidence
            if item["state"] == "focus"
        ),
    }
    manifest = {
        "schema": "neoeng.stage1-theme-state-captures",
        "schema_version": 1,
        "source_commit": os.environ.get("NEOENG_SOURCE_COMMIT", "unknown"),
        "environment": {"platform": platform.platform(), "python": sys.version, "dpi_percent": 100},
        "qss_sha256": hashlib.sha256(QSS.encode("utf-8")).hexdigest(),
        "token_values": {name: getattr(THEME_TOKENS, name) for name in THEME_TOKENS.__dataclass_fields__},
        "states": list(STATES),
        "resolutions": {name: list(size) for name, size in RESOLUTIONS.items()},
        "files": files,
        "state_evidence_present": state_distinctness,
        "state_samples": state_samples,
        "status": "PASS" if all(state_distinctness.values()) and len(files) == 18 else "FAIL",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Imported late to keep the fixture's import error explicit if Qt changes.
    from PySide6.QtCore import Qt
    globals()["Qt"] = Qt
    manifest = capture(args.output.resolve())
    print(json.dumps({"status": manifest["status"], "files": len(manifest["files"])}, sort_keys=True))
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
