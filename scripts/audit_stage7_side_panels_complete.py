"""Native Windows Qt audit for all Stage 7 side panels."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractItemView,
    QApplication,
    QComboBox,
    QScrollArea,
    QToolBar,
)

from scripts.audit_ui_capture import (  # noqa: E402
    _capture,
    _new_window,
    _prepare_project,
    _settle,
)

ROOT = Path(__file__).resolve().parents[1]
RESOLUTIONS = {
    "1080p_FHD": (1920, 1080),
    "768p_Minima": (1366, 768),
    "720p_Compacta": (1280, 720),
}
PANEL_NAMES = ("objects", "layers", "groups", "collision")


def _rect(widget: Any) -> list[int]:
    rect = widget.geometry()
    return [rect.x(), rect.y(), rect.width(), rect.height()]


def _digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def _toolbar(toolbar: QToolBar) -> tuple[dict[str, Any], list[str]]:
    findings: list[str] = []
    actions = []
    if not toolbar.isVisible():
        findings.append(f"{toolbar.objectName()} is not visible")
    if toolbar.iconSize() != QSize(16, 16):
        findings.append(f"{toolbar.objectName()} icon size is not 16x16")
    for index, action in enumerate(toolbar.actions()):
        rect = toolbar.actionGeometry(action)
        if not toolbar.rect().contains(rect):
            findings.append(f"{toolbar.objectName()} action {index} is outside")
        if action.icon().isNull():
            findings.append(f"{toolbar.objectName()} action {index} has no icon")
        if not action.toolTip():
            findings.append(f"{toolbar.objectName()} action {index} has no tooltip")
        if not action.property("commandKey"):
            findings.append(f"{toolbar.objectName()} action {index} has no command key")
        actions.append(
            {
                "index": index,
                "command_key": action.property("commandKey"),
                "text": action.text(),
                "tooltip": action.toolTip(),
                "icon_null": action.icon().isNull(),
                "geometry": [
                    rect.x(),
                    rect.y(),
                    rect.width(),
                    rect.height(),
                ],
            }
        )
    return {"geometry": _rect(toolbar), "actions": actions}, findings


def _panel(panel: Any, name: str) -> tuple[dict[str, Any], list[str]]:
    findings: list[str] = []
    result: dict[str, Any] = {
        "class": type(panel).__name__,
        "geometry": _rect(panel),
        "visible": panel.isVisibleTo(panel.window()),
        "toolbars": {},
        "lists": [],
        "scroll_areas": [],
    }
    if panel.width() <= 0 or panel.height() <= 0:
        findings.append(f"{name} has invalid geometry")
    if not result["visible"]:
        findings.append(f"{name} is not visible in active tab")
    for toolbar in panel.findChildren(QToolBar):
        data, errors = _toolbar(toolbar)
        result["toolbars"][toolbar.objectName()] = data
        findings.extend(f"{name}: {error}" for error in errors)
    for widget in panel.findChildren(QAbstractItemView):
        result["lists"].append(
            {
                "name": widget.objectName(),
                "geometry": _rect(widget),
                "visible": widget.isVisibleTo(panel),
                "count": (
                    widget.count()
                    if hasattr(widget, "count")
                    else widget.model().rowCount()
                ),
            }
        )
        if widget.width() <= 0 or widget.height() <= 0:
            findings.append(f"{name} list has invalid geometry")
    for scroll in panel.findChildren(QScrollArea):
        result["scroll_areas"].append(
            {
                "name": scroll.objectName(),
                "geometry": _rect(scroll),
                "visible": scroll.isVisibleTo(panel),
                "vertical_range": [
                    scroll.verticalScrollBar().minimum(),
                    scroll.verticalScrollBar().maximum(),
                ],
                "horizontal_range": [
                    scroll.horizontalScrollBar().minimum(),
                    scroll.horizontalScrollBar().maximum(),
                ],
            }
        )
    required = {
        "objects": (
            "objects_properties_action_toolbar",
            "objects_modify_action_toolbar",
            "objects_export_action_toolbar",
        ),
        "layers": ("layers_action_toolbar",),
        "groups": ("groups_action_toolbar",),
        "collision": ("collision_action_toolbar",),
    }[name]
    for object_name in required:
        if object_name not in result["toolbars"]:
            findings.append(f"{name} missing {object_name}")
    if name == "objects":
        legacy = (
            panel.btn_rename,
            panel.btn_delete,
            panel.btn_expand,
            panel.btn_contract,
            panel.btn_invert,
            panel.btn_collision,
            panel.btn_apply,
            panel.btn_cancel,
            panel.btn_export,
            panel.btn_export_now,
        )
        if any(button.isVisible() for button in legacy):
            findings.append("objects legacy text command is visible")
        result["selection_state"] = {
            "rename_enabled": panel.btn_rename.isEnabled(),
            "transform_enabled": panel.transform_group.isEnabled(),
            "collision_enabled": panel.btn_collision.isEnabled(),
        }
    if name == "collision":
        if not isinstance(panel.strategy_combo, QComboBox):
            findings.append("collision strategy selector missing")
        elif not panel.strategy_combo.isVisibleTo(panel):
            findings.append("collision strategy selector is not visible")
    result["status"] = "PASS" if not findings else "FAIL"
    return result, findings


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    if app.platformName().lower() != "windows":
        raise RuntimeError(
            f"native Windows Qt backend required, got {app.platformName()}"
        )
    scene, project_path = _prepare_project(output)
    report = {
        "schema_version": 2,
        "stage": 7,
        "scope": "all_side_panels",
        "platform": platform.platform(),
        "python": sys.version,
        "qt_platform": app.platformName(),
        "source_state": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean": not bool(_git("status", "--porcelain")),
        },
        "captures": {},
        "findings": [],
    }
    for label, (width, height) in RESOLUTIONS.items():
        window = _new_window(scene, project_path=project_path, project_loaded=True)
        try:
            window.resize(QSize(width, height))
            _settle(app)
            tabs = (
                window.compact_panel_tabs
                if window._compact_layout
                else window.reference_panel_tabs
            )
            data = {
                "requested_size": [width, height],
                "actual_window_size": [window.width(), window.height()],
                "panels": {},
            }
            for index, name in enumerate(PANEL_NAMES):
                tabs.setCurrentIndex(index)
                _settle(app)
                panel = tabs.widget(index)
                capture = output / f"{label}_{index + 1:02d}_{name}.png"
                _capture(window, capture)
                contract, errors = _panel(panel, name)
                data["panels"][name] = {
                    "capture": {"path": capture.name, **_digest(capture)},
                    "contract": contract,
                }
                report["findings"].extend(
                    {"resolution": label, "panel": name, "message": error}
                    for error in errors
                )
            report["captures"][label] = data
        finally:
            window.close()
            _settle(app, 20)
    report["status"] = "PASS" if not report["findings"] else "FAIL"
    report_path = output / "stage7-side-panels-complete-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
