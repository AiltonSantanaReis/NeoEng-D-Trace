"""Independent current-snapshot audit for Interface Modernization Stage 3.

The audit exercises the real MainWindow and the visible reference rail. Historical
Stage 3 reports are not used as current evidence. The output directory is supplied
by the caller so this audit cannot silently overwrite an earlier stage artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QApplication, QToolBar

from scripts.audit_ui_capture import AuditConfig
from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS

ROOT = Path(__file__).resolve().parents[1]
HOST_PATH_RE = re.compile(r"(?i)[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\r\n\"<>]+")
TOOL_ORDER = [
    "selection",
    "rect_selection",
    "ellipse_selection",
    "lasso_tool",
    "polygonal_lasso",
    "magnetic_lasso",
    "pen_tool",
    "polygon_edit",
    "collision_brush",
]
AUX_ORDER = ["validation", "move_viewport", "zoom_viewport", "fit_view", "focus_selected"]
SHORTCUTS = {"1": "polygonal_lasso", "2": "lasso_tool", "3": "rect_selection", "4": "ellipse_selection", "5": "pen_tool", "6": "magnetic_lasso"}
RESOLUTIONS = {"1280x720": (1280, 720), "1366x768": (1366, 768), "1920x1080": (1920, 1080)}


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def safe(value: str) -> str:
    return HOST_PATH_RE.sub("<host-path-redacted>", value)


def run(command: list[str], cwd: Path, log: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    log.write_text(safe(result.stdout + result.stderr), encoding="utf-8", newline="\n")
    return {"command": [".venv/Scripts/python.exe" if item == sys.executable else item for item in command], "returncode": result.returncode, "log": log.name}


def rect(item: Any) -> list[int]:
    geometry = item.geometry()
    return [geometry.x(), geometry.y(), geometry.width(), geometry.height()]


def metadata(item: Any) -> dict[str, Any]:
    return {
        "object_name": item.objectName(),
        "text": item.text(),
        "tooltip": item.toolTip(),
        "accessible_name": item.accessibleName(),
        "focus_policy": item.focusPolicy().name,
        "icon_null": item.icon().isNull(),
        "icon_key": item.property("iconKey"),
        "geometry": rect(item),
    }


def contract() -> dict[str, Any]:
    app = QApplication.instance() or QApplication(sys.argv)
    cast(Any, app).setStyleSheet(QSS)
    failures: list[str] = []
    resolutions: dict[str, Any] = {}
    interaction: dict[str, Any] = {}
    shortcut_results: dict[str, Any] = {}

    for label, (width, height) in RESOLUTIONS.items():
        scene = Scene()
        scene.cmd = CommandManager()
        window = MainWindow(scene, AuditConfig())
        window._refresh_document_views(project_loaded=False)
        window.resize(width, height)
        window.show()
        app.processEvents()
        rail = window.reference_tool_palette
        rail_width = rail.width()
        rail_record = {
            "window_size": [width, height],
            "rail_geometry": rect(rail),
            "rail_minimum_width": rail.minimumWidth(),
            "rail_maximum_width": rail.maximumWidth(),
            "source_toolbar_geometry": rect(window.tool_palette),
            "source_toolbar_visible": window.tool_palette.isVisible(),
            "rail_visible": rail.isVisibleTo(window),
            "button_count": 0,
            "out_of_bounds": [],
        }
        if not (56 <= rail_width <= 72):
            failures.append(f"{label}: visible rail width {rail_width} outside 56..72")
        if not rail.isVisibleTo(window):
            failures.append(f"{label}: visible reference rail is hidden")
        for action in rail.actions():
            if action.isSeparator():
                continue
            button = rail.widgetForAction(action)
            if button is None:
                failures.append(f"{label}: missing visible button for {action.objectName()}")
                continue
            rail_record["button_count"] += 1
            geometry = button.geometry()
            inside = geometry.left() >= 0 and geometry.top() >= 0 and geometry.right() < rail.width() and geometry.bottom() < rail.height()
            if not inside:
                rail_record["out_of_bounds"].append(action.objectName())
                failures.append(f"{label}: {action.objectName()} clips outside visible rail")
            if button.accessibleName() == "":
                failures.append(f"{label}: {action.objectName()} visible accessible name missing")
            if button.focusPolicy() == Qt.FocusPolicy.NoFocus:
                failures.append(f"{label}: {action.objectName()} visible focus disabled")
        resolutions[label] = rail_record
        if label == "1280x720":
            source = window.tool_palette
            source.setEnabled(True)
            rail.setEnabled(True)
            app.processEvents()
            actions = source.actions()
            tool_actions = [action for action in actions if action.objectName().startswith("tool_action_")]
            aux_actions = [action for action in actions if action.objectName().startswith("rail_action_")]
            separator_positions = [index for index, action in enumerate(actions) if action.isSeparator()]
            if not isinstance(source, QToolBar):
                failures.append("source toolbar is not QToolBar")
            if source.objectName() != "left_tool_toolbar" or source.orientation() != Qt.Orientation.Vertical:
                failures.append("source toolbar identity/orientation drifted")
            if source.toolButtonStyle() != Qt.ToolButtonStyle.ToolButtonIconOnly:
                failures.append("source toolbar is not icon-only")
            if source.isMovable() or source.isFloatable():
                failures.append("source toolbar became movable/floatable")
            if [action.data() for action in tool_actions] != TOOL_ORDER:
                failures.append("tool action order does not match normative groups")
            if [action.data() for action in aux_actions] != AUX_ORDER:
                failures.append("auxiliary action order does not match normative groups")
            if len(separator_positions) != 3:
                failures.append(f"expected 3 group separators, got {len(separator_positions)}")
            if not source.action_group.isExclusive() or not source.button_group.exclusive():
                failures.append("exclusive selection groups disabled")
            for name in TOOL_ORDER:
                button = source.tool_buttons.get(name)
                if button is None:
                    failures.append(f"missing public tool button {name}")
                    continue
                record = metadata(button)
                if record["icon_null"] or not record["text"] or not record["tooltip"] or not record["accessible_name"]:
                    failures.append(f"{name}: icon/text/tooltip/accessibility incomplete")
                if record["focus_policy"] == "NoFocus":
                    failures.append(f"{name}: source focus disabled")
                button.click()
                app.processEvents()
                checked = [candidate for candidate in source.tool_buttons.values() if candidate.isChecked()]
                if checked != [button] or source.button_group.checkedButton() is not button or window.canvas._tool is None:
                    failures.append(f"{name}: selection is not exclusive or did not create a real canvas tool")
            source.setEnabled(False)
            app.processEvents()
            if not all("Open an image" in source.tool_buttons[name].toolTip() for name in TOOL_ORDER):
                failures.append("disabled tool feedback missing")
            source.setEnabled(True)
            window.set_language("pt")
            app.processEvents()
            if source.btn_lasso.text() != "Laço" or "ferramenta" not in source.btn_lasso.toolTip().casefold():
                failures.append("Portuguese label/tooltip contract failed")
            source.setEnabled(True)
            for key, expected in SHORTCUTS.items():
                shortcut_results[key] = key in [shortcut.key().toString() for shortcut in window.findChildren(QShortcut)]
            if not all(shortcut_results.values()):
                failures.append("one or more Stage 3 tool shortcuts are missing")
            visible_selection = rail.widgetForAction(source._tool_actions["selection"])
            if visible_selection is None:
                failures.append("visible selection action is not materialized")
            else:
                visible_selection.click()
                app.processEvents()
                if not visible_selection.isChecked() or not source.tool_buttons["selection"].isChecked():
                    failures.append("visible rail selection did not preserve shared action state")
            interaction = {
                "tool_count": len(tool_actions),
                "auxiliary_count": len(aux_actions),
                "separator_positions": separator_positions,
                "source_tool_metadata": {name: metadata(source.tool_buttons[name]) for name in TOOL_ORDER},
                "visible_rail_metadata": {action.objectName(): metadata(rail.widgetForAction(action)) for action in rail.actions() if not action.isSeparator() and rail.widgetForAction(action) is not None},
            }
        window.close()
        app.processEvents()

    return {
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "resolutions": resolutions,
        "interaction": interaction,
        "shortcuts": shortcut_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    raw = output / "raw-captures"
    visual = output / "visual-audit"
    raw.mkdir(exist_ok=True)
    visual.mkdir(exist_ok=True)
    capture = run([sys.executable, "scripts/audit_ui_capture.py", "--output", str(raw)], ROOT, output / "capture.log")
    visual_run = run([sys.executable, "scripts/audit_visual_artifacts.py", "--input", str(raw), "--output", str(visual)], ROOT, output / "visual-audit.log")
    visual_report_path = visual / "visual-audit-report.json"
    visual_report = json.loads(visual_report_path.read_text(encoding="utf-8")) if visual_report_path.is_file() else {"status": "MISSING", "finding_count": None}
    live = contract()
    report = {
        "schema": "neoeng.stage3-contract-audit",
        "schema_version": 1,
        "stage": 3,
        "stage_name": "Barra lateral de ferramentas",
        "source_state": {"commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"), "worktree_clean": not bool(git("status", "--porcelain"))},
        "environment": {"platform": platform.platform(), "python": platform.python_version(), "qt_platform": os.environ.get("QT_QPA_PLATFORM"), "dpi_matrix": [100, 125, 150, 200]},
        "commands": {"capture": capture, "visual_audit": visual_run},
        "checks": {"capture_status": "PASS" if capture["returncode"] == 0 else "FAIL", "visual_status": visual_report.get("status"), "visual_finding_count": visual_report.get("finding_count"), "live_contract": live},
        "historical_reference": {"path": "docs/evidence/artifacts/ui-modernization-stage3-20260821/stage3-toolbar-report.json", "classification": "HISTORICAL_ONLY"},
        "limitations": ["Offscreen captures prove current Qt geometry and automated visual invariants; they do not replace human aesthetic review.", "DPI 100/125/150/200 is validated by the chained Stage 2 matrix and remains a prerequisite compatibility gate; this Stage 3 live rail matrix covers the three normative resolutions.", "Gizmo, masks, inspector, parallax, camera/light/particles and scenario behaviors belong to later stages and are explicitly not counted as Stage 3 evidence."],
    }
    report["status"] = "PASS" if capture["returncode"] == 0 and visual_run["returncode"] == 0 and visual_report.get("status") == "PASS" and live["status"] == "PASS" else "FAIL"
    report_path = output / "stage3-contract-audit.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output / "stage3-contract-audit.md").write_text("\n".join(["# Auditoria atual da Etapa 3", "", f"- Status: `{report['status']}`", f"- Commit: `{report['source_state']['commit']}`", f"- Captura real: `{report['checks']['capture_status']}`", f"- Auditor visual: `{report['checks']['visual_status']}` com `{report['checks']['visual_finding_count']}` achados", f"- Contrato live: `{live['status']}` com `{live['failure_count']}` achados", "", "A referência histórica não é usada como prova do estado atual. A revisão humana continua obrigatória."]) + "\n", encoding="utf-8", newline="\n")
    entries = {}
    for item in sorted(output.rglob("*")):
        if item.is_file() and item.name != "stage3-artifact-index.json":
            entries[item.relative_to(output).as_posix()] = digest(item)
    (output / "stage3-artifact-index.json").write_text(json.dumps({"schema": "neoeng.stage3-artifact-index", "schema_version": 1, "files": entries}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "live": live["status"], "visual": visual_report.get("status"), "failures": live["failure_count"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
