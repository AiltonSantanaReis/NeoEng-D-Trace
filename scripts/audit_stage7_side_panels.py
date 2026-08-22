"""Audit the real Qt geometry and action contract of the Stage 7 panels."""

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
from PySide6.QtWidgets import QApplication, QToolBar  # noqa: E402

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


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def _rect(widget: Any) -> list[int]:
    geometry = widget.geometry()
    return [geometry.x(), geometry.y(), geometry.width(), geometry.height()]


def _group_contract(window: Any) -> dict[str, Any]:
    panel = window.groups
    toolbar = panel.action_toolbar
    findings: list[str] = []
    if not isinstance(toolbar, QToolBar):
        findings.append("groups action toolbar is not a QToolBar")
    if toolbar is not None and len(toolbar.actions()) != 8:
        findings.append(f"expected 8 group actions, got {len(toolbar.actions())}")
    if toolbar is not None:
        for index, action in enumerate(toolbar.actions()):
            action_rect = toolbar.actionGeometry(action)
            if not toolbar.rect().contains(action_rect):
                findings.append(f"action {index} is outside toolbar geometry")
            if not action.toolTip():
                findings.append(f"action {index} has no tooltip")
    legacy = (
        panel.btn_new,
        panel.btn_delete,
        panel.btn_add,
        panel.btn_remove,
        panel.btn_up,
        panel.btn_down,
        panel.btn_vis,
        panel.btn_lock,
    )
    if any(button.isVisible() for button in legacy):
        findings.append("legacy group button is still visible")
    if not panel.isVisibleTo(window):
        findings.append("groups panel is not rendered in the active page")
    if not panel.list.isVisibleTo(window):
        findings.append("groups list is not rendered in the active page")
    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "panel_geometry": _rect(panel),
        "toolbar_geometry": _rect(toolbar),
        "list_geometry": _rect(panel.list),
        "toolbar_icon_size": [toolbar.iconSize().width(), toolbar.iconSize().height()],
        "action_count": len(toolbar.actions()),
        "legacy_buttons_visible": [button.isVisible() for button in legacy],
    }


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    if app.platformName().lower() != "windows":
        raise RuntimeError(
            f"native Windows Qt backend required, got {app.platformName()}"
        )
    scene, project_path = _prepare_project(output)
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": 7,
        "scope": "side_panels_groups_toolbar",
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
                window.reference_panel_tabs
                if not window._compact_layout
                else window.compact_panel_tabs
            )
            tabs.setCurrentWidget(window.groups)
            _settle(app)
            capture = output / f"{label}_05_grupos_painel.png"
            _capture(window, capture)
            contract = _group_contract(window)
            report["captures"][label] = {
                "requested_size": [width, height],
                "actual_window_size": [window.width(), window.height()],
                "capture": {"path": capture.name, **_digest(capture)},
                "contract": contract,
            }
            report["findings"].extend(
                {"resolution": label, "message": finding}
                for finding in contract["findings"]
            )
        finally:
            window.close()
            _settle(app, 20)
    report["status"] = "PASS" if not report["findings"] else "FAIL"
    report_path = output / "stage7-side-panels-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
