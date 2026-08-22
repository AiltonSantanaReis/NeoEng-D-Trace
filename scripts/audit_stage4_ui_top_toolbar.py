"""Run the reproducible Stage 4 top-toolbar audit.

The audit exercises the real ``MainWindow`` and records both structural Qt
facts and PNG captures. A green result requires action identity, menu
identity, native separator boundaries, accessibility metadata and successful
execution of the existing visual-audit pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidgetAction  # noqa: E402

from scripts.audit_ui_capture import AuditConfig  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = (
    ROOT / "docs" / "evidence" / "artifacts" / "ui-modernization-stage4-20260822"
)
RAW_ROOT = EVIDENCE_ROOT / "raw-captures"
VISUAL_ROOT = EVIDENCE_ROOT / "visual-audit"
REPORT_PATH = EVIDENCE_ROOT / "stage4-top-toolbar-report.json"
REPORT_MD_PATH = EVIDENCE_ROOT / "stage4-top-toolbar-report.md"
INDEX_PATH = EVIDENCE_ROOT / "artifact-index.json"
HOST_PATH_RE = re.compile(
    r"(?i)[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\r\n\"<>]+"
)


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def _safe_command(command: list[str]) -> list[str]:
    safe: list[str] = []
    for value in command:
        if value == sys.executable:
            safe.append(".venv/Scripts/python.exe")
            continue
        try:
            safe.append(Path(value).resolve().relative_to(ROOT).as_posix())
        except (OSError, ValueError):
            safe.append(value)
    return safe


def _run(command: list[str], log_name: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (EVIDENCE_ROOT / log_name).write_text(
        HOST_PATH_RE.sub("<host-path-redacted>", result.stdout + result.stderr),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "command": _safe_command(command),
        "returncode": result.returncode,
        "log": log_name,
    }


def _toolbar_objects(toolbar):
    objects = []
    for action in toolbar.actions():
        if action.isSeparator():
            continue
        if isinstance(action, QWidgetAction):
            objects.append(action.defaultWidget())
        else:
            objects.append(action)
    return objects


def _live_contract() -> dict[str, Any]:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    window = MainWindow(Scene(), AuditConfig())
    window.show()
    app.processEvents()
    failures: list[str] = []

    groups = window.top_toolbar_groups
    expected_main = [
        item for name in ("file", "edit", "view", "export") for item in groups[name]
    ]
    if _toolbar_objects(window.toolbar) != expected_main:
        failures.append("main toolbar group order or membership drifted")
    if sum(action.isSeparator() for action in window.toolbar.actions()) != 3:
        failures.append("main toolbar does not have three native group boundaries")

    if window.undo_action not in window.edit_menu.actions():
        failures.append("Undo QAction is not shared with Edit menu")
    if window.redo_action not in window.edit_menu.actions():
        failures.append("Redo QAction is not shared with Edit menu")
    if window.mask_viewer_action not in window.view_menu.actions():
        failures.append("Mask Viewer QAction is not shared with View menu")
    if window.collision_overlay_action not in window.view_menu.actions():
        failures.append("Collision Overlay QAction is not shared with View menu")

    action_records: dict[str, Any] = {}
    for name in (
        "open_project_action",
        "open_image_action",
        "save_project_action",
        "save_project_as_action",
        "undo_action",
        "redo_action",
        "mask_viewer_action",
        "collision_overlay_action",
        "act_export",
        "act_fit",
        "act_100",
    ):
        action = getattr(window, name)
        record = {
            "text": action.text(),
            "icon_null": action.icon().isNull(),
            "tooltip": action.toolTip(),
            "accessible_name": action.property("accessibleName"),
            "icon_key": action.property("iconKey"),
        }
        action_records[name] = record
        if (
            action.icon().isNull()
            or not action.text()
            or not action.toolTip()
            or not action.property("accessibleName")
        ):
            failures.append(f"action metadata/icon incomplete: {name}")

    for name, toolbar in (
        ("main_toolbar", window.toolbar),
        ("navigation_toolbar", window.nav_toolbar),
        ("xray_toolbar", window.xray_toolbar),
    ):
        if toolbar.property("toolbarStage") != "stage4":
            failures.append(f"missing Stage 4 marker: {name}")
        if toolbar.isMovable() or toolbar.isFloatable():
            failures.append(f"toolbar unexpectedly movable: {name}")

    identities_before = (window.undo_action, window.mask_viewer_action, window.act_fit)
    window.set_language("pt")
    app.processEvents()
    if identities_before != (
        window.undo_action,
        window.mask_viewer_action,
        window.act_fit,
    ):
        failures.append("action identity changed during language update")
    if (
        window.undo_action not in window.edit_menu.actions()
        or window.mask_viewer_action not in window.view_menu.actions()
    ):
        failures.append("menu identity was lost during language update")

    records = {
        name: {
            "object_name": toolbar.objectName(),
            "role": toolbar.property("toolbarRole"),
            "geometry": [toolbar.x(), toolbar.y(), toolbar.width(), toolbar.height()],
            "action_count": len([a for a in toolbar.actions() if not a.isSeparator()]),
            "separator_count": sum(a.isSeparator() for a in toolbar.actions()),
        }
        for name, toolbar in (
            ("main_toolbar", window.toolbar),
            ("navigation_toolbar", window.nav_toolbar),
            ("xray_toolbar", window.xray_toolbar),
        )
    }
    window.close()
    app.processEvents()
    return {
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "contract": window.top_toolbar_contract,
        "toolbars": records,
        "actions": action_records,
    }


def _write_index() -> None:
    entries: dict[str, Any] = {}
    for path in sorted(EVIDENCE_ROOT.rglob("*")):
        if path.is_file() and path != INDEX_PATH:
            entries[path.relative_to(EVIDENCE_ROOT).as_posix()] = _digest(path)
    INDEX_PATH.write_text(
        json.dumps({"schema_version": 1, "files": entries}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    capture = _run(
        [sys.executable, "scripts/audit_ui_capture.py", "--output", str(RAW_ROOT)],
        "capture.log",
    )
    visual = _run(
        [
            sys.executable,
            "scripts/audit_visual_artifacts.py",
            "--input",
            str(RAW_ROOT),
            "--output",
            str(VISUAL_ROOT),
        ],
        "visual-audit.log",
    )
    live = _live_contract()
    report = {
        "schema_version": 1,
        "stage": "Etapa 4 — Barra superior",
        "source_state": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean": not bool(_git("status", "--porcelain")),
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        },
        "commands": {"capture": capture, "visual_audit": visual},
        "artifacts": {
            "raw_manifest": "raw-captures/manifest.json",
            "visual_report": "visual-audit/visual-audit-report.json",
        },
        "live_contract": live,
        "status": (
            "PASS"
            if capture["returncode"] == 0
            and visual["returncode"] == 0
            and live["status"] == "PASS"
            else "FAIL"
        ),
        "limitations": [
            (
                "The capture pipeline is real Qt offscreen rendering; native Windows "
                "DPI capture remains a separate environment-specific audit."
            ),
            (
                "Viewport HUD/Gizmo relocation and the separate scenario authoring "
                "window remain outside this toolbar stage."
            ),
        ],
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_MD_PATH.write_text(
        "# Auditoria da Etapa 4 — Barra superior\n\n"
        f"- Status: `{report['status']}`\n"
        f"- Commit observado: `{report['source_state']['commit']}`\n"
        f"- Captura: `{capture['returncode']}`; "
        f"auditor visual: `{visual['returncode']}`\n"
        f"- Contrato Qt: `{live['status']}` com {live['failure_count']} achados.\n"
        "- As limitações de captura não foram convertidas em PASS funcional.\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_index()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
