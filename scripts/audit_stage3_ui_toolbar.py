"""Run the reproducible Stage 3 left-toolbar audit.

The audit uses the real MainWindow, real Qt widgets and the existing PNG
capture/visual auditors. It checks the structural toolbar contract separately
so a visually plausible screenshot cannot hide a broken action or focus state.
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

from PySide6.QtWidgets import QApplication, QToolBar  # noqa: E402

from scripts.audit_ui_capture import AuditConfig  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = (
    ROOT / "docs" / "evidence" / "artifacts" / "ui-modernization-stage3-20260821"
)
RAW_ROOT = EVIDENCE_ROOT / "raw-captures"
VISUAL_ROOT = EVIDENCE_ROOT / "visual-audit"
REPORT_PATH = EVIDENCE_ROOT / "stage3-toolbar-report.json"
REPORT_MD_PATH = EVIDENCE_ROOT / "stage3-toolbar-report.md"
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
    toolbar = window.tool_palette
    failures: list[str] = []
    actions = toolbar.actions()
    tool_actions = [action for action in actions if not action.isSeparator()]
    buttons = toolbar.tool_buttons

    if not isinstance(toolbar, QToolBar):
        failures.append("tool_palette is not a QToolBar")
    if toolbar.objectName() != "left_tool_toolbar":
        failures.append("object name drifted")
    if toolbar.orientation().name != "Vertical":
        failures.append("toolbar is not vertical")
    if toolbar.toolButtonStyle().name != "ToolButtonIconOnly":
        failures.append("toolbar is not icon-first")
    if toolbar.isMovable() or toolbar.isFloatable():
        failures.append("toolbar is user-movable")
    if len(tool_actions) != 9 or sum(action.isSeparator() for action in actions) != 2:
        failures.append("tool action grouping changed")
    if not toolbar.action_group.isExclusive() or not toolbar.button_group.exclusive():
        failures.append("exclusive selection groups are disabled")

    records: dict[str, Any] = {}
    for name, button in buttons.items():
        records[name] = {
            "text": button.text(),
            "tooltip": button.toolTip(),
            "accessible_name": button.accessibleName(),
            "icon_null": button.icon().isNull(),
            "focus_policy": button.focusPolicy().name,
            "geometry": [button.x(), button.y(), button.width(), button.height()],
        }
        if button.icon().isNull():
            failures.append(f"{name}: icon missing")
        if not button.text() or not button.toolTip() or not button.accessibleName():
            failures.append(f"{name}: textual/accessibility metadata missing")
        if button.focusPolicy().name == "NoFocus":
            failures.append(f"{name}: keyboard focus disabled")

    toolbar.setEnabled(False)
    app.processEvents()
    if not all("Open an image" in button.toolTip() for button in buttons.values()):
        failures.append("disabled feedback is missing")
    toolbar.setEnabled(True)
    window.set_language("pt")
    app.processEvents()
    if toolbar.btn_lasso.text() != "Laço":
        failures.append("Portuguese tool label did not update")
    window.close()
    app.processEvents()
    return {
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "toolbar": {
            "class": type(toolbar).__name__,
            "object_name": toolbar.objectName(),
            "orientation": toolbar.orientation().name,
            "tool_button_style": toolbar.toolButtonStyle().name,
            "minimum_width": toolbar.minimumWidth(),
            "maximum_width": toolbar.maximumWidth(),
            "action_count": len(tool_actions),
            "separator_count": sum(action.isSeparator() for action in actions),
        },
        "buttons": records,
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
        "stage": "Etapa 3 — Barra esquerda de ferramentas",
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
            "raw_manifest": {"path": "raw-captures/manifest.json"},
            "visual_report": {
                "path": "visual-audit/visual-audit-report.json",
            },
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
                "Visual captures use Qt offscreen; independent human aesthetic review "
                "is not automated."
            ),
            (
                "The Gizmo and Mask Viewer remain in their existing contexts; they are "
                "outside this stage's structural migration."
            ),
        ],
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_MD_PATH.write_text(
        "# Auditoria da Etapa 3 — Barra esquerda\n\n"
        f"- Status: `{report['status']}`\n"
        f"- Commit observado: `{report['source_state']['commit']}`\n"
        f"- Captura: `{capture['returncode']}`; "
        f"auditor visual: `{visual['returncode']}`\n"
        f"- Contrato Qt: `{live['status']}` com {live['failure_count']} achados.\n"
        "- A revisão humana estética independente permanece não automatizada e não foi "
        "convertida em PASS.\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_index()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
