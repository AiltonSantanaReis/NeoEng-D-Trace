"""Run the reproducible Stage 4 top-toolbar audit.

The audit exercises the real ``MainWindow`` and records the semantic Stage 4
command-family contract plus PNG captures. A green result requires stable
command-group membership, action/menu identity, accessibility metadata and
successful execution of the existing visual-audit pipeline. Physical legacy
``QToolBar`` geometry and parentage are deliberately not product contracts.
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

from PySide6.QtWidgets import QApplication  # noqa: E402

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



def _live_contract() -> dict[str, Any]:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    window = MainWindow(Scene(), AuditConfig())
    window.show()
    app.processEvents()
    failures: list[str] = []

    contract = window.top_command_contract
    groups = window.top_command_groups
    descriptor = contract.descriptor()
    expected_order = ("file", "edit", "view", "export", "context", "render")
    expected_roles = {
        "file": "commands",
        "edit": "commands",
        "view": "commands",
        "export": "commands",
        "context": "context",
        "render": "render",
    }
    if contract.group_names() != expected_order:
        failures.append("semantic command group order drifted")
    if descriptor.get("group_roles") != expected_roles:
        failures.append("semantic command group roles drifted")
    if descriptor.get("physical_toolbar_required") is not False:
        failures.append("semantic contract unexpectedly requires physical toolbars")
    if groups != contract.as_mapping():
        failures.append("top command groups drifted from semantic contract")

    expected_groups = {
        "file": (
            window.open_project_action,
            window.open_image_action,
            window.save_project_action,
            window.save_project_as_action,
        ),
        "edit": (window.undo_action, window.redo_action, window.settings_action),
        "view": (
            window.mask_viewer_action,
            window.collision_overlay_action,
            window.act_fit,
            window.act_100,
            window.act_grid,
            window.act_snap,
        ),
        "export": (
            window.act_export,
            window.act_export_collision_json,
            window.act_export_collision_txt,
        ),
        "context": (
            window.canvas.gizmo_toggle,
            window.tool_palette.navigation_actions["focus_selected"],
            window.act_clean,
            window.language_button,
        ),
        "render": (
            window.act_lit,
            window.act_xray1,
            window.act_xray2,
            window.act_xray3,
        ),
    }
    for name, expected in expected_groups.items():
        if contract.items(name) != expected:
            failures.append(f"semantic command membership/order drifted: {name}")

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

    group_records = {
        group.name: {
            "role": group.role,
            "item_count": len(group.items),
            "item_types": [type(item).__name__ for item in group.items],
        }
        for group in contract.groups
    }
    window.close()
    app.processEvents()
    return {
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "contract": descriptor,
        "groups": group_records,
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
