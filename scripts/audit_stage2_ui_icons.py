"""Run the complete reproducible audit for Interface Moderna Etapa 2.

This command regenerates real MainWindow captures, audits them with Pillow/OpenCV
and validates the embedded icon/action contract against live Qt widgets.
It never changes governance, baselines or test assertions.
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
from typing import Any, cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QShortcut  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = (
    ROOT / "docs" / "evidence" / "artifacts" / "ui-modernization-stage2-20260821"
)
RAW_ROOT = EVIDENCE_ROOT / "raw-captures"
VISUAL_ROOT = EVIDENCE_ROOT / "visual-audit"
REPORT_PATH = EVIDENCE_ROOT / "stage2-icon-report.json"
REPORT_MD_PATH = EVIDENCE_ROOT / "stage2-icon-report.md"
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


def _source_state() -> dict[str, Any]:
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(_git("status", "--porcelain")),
    }


def _sanitize_text(value: str) -> str:
    return HOST_PATH_RE.sub("<host-path-redacted>", value)


def _safe_command(command: list[str]) -> list[str]:
    safe: list[str] = []
    for value in command:
        if value == sys.executable:
            safe.append(".venv/Scripts/python.exe")
            continue
        try:
            resolved = Path(value).resolve()
            safe.append(resolved.relative_to(ROOT).as_posix())
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
        _sanitize_text(result.stdout + result.stderr),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "command": _safe_command(command),
        "returncode": result.returncode,
        "log": log_name,
    }


def _runtime_icon_contract() -> dict[str, Any]:
    from scripts.audit_ui_capture import AuditConfig
    from src.core.commands import CommandManager
    from src.models.scene import Scene
    from src.ui.icon_library import ICON_SPECS
    from src.ui.main_window import MainWindow
    from src.ui.theme_qss import QSS

    app = QApplication.instance() or QApplication(sys.argv)
    app = cast(Any, app)
    app.setStyleSheet(QSS)
    scene = Scene()
    scene.cmd = CommandManager()
    window = MainWindow(scene, AuditConfig())
    window.show()
    app.processEvents()

    failures: list[str] = []
    action_names = (
        "open_project_action",
        "open_image_action",
        "save_project_action",
        "save_project_as_action",
        "act_export",
        "act_export_collision_json",
        "act_export_collision_txt",
        "act_fit",
        "act_100",
        "act_lit",
        "act_xray1",
        "act_xray2",
        "act_xray3",
        "act_clean",
        "language_action",
    )
    widget_names = (
        "canvas.gizmo_toggle",
    )
    action_checks: dict[str, Any] = {}
    widget_checks: dict[str, Any] = {}

    def check_icon(name: str, item: Any) -> dict[str, Any]:
        icon = item.icon()
        accessible_method = getattr(item, "accessibleName", None)
        accessible_name = (
            accessible_method()
            if callable(accessible_method)
            else item.property("accessibleName")
        )
        record = {
            "text": item.text(),
            "tooltip": item.toolTip(),
            "accessible_name": accessible_name,
            "icon_key": item.property("iconKey"),
            "icon_fallback": bool(item.property("iconFallback")),
            "icon_null": icon.isNull(),
            "icon_sizes": [
                [size.width(), size.height()] for size in icon.availableSizes()
            ],
        }
        if not record["text"]:
            failures.append(f"{name}: textual label missing")
        if not record["tooltip"]:
            failures.append(f"{name}: tooltip missing")
        if not record["accessible_name"]:
            failures.append(f"{name}: accessible name missing")
        if record["icon_null"] or not record["icon_sizes"]:
            failures.append(f"{name}: embedded icon did not render")
        if record["icon_fallback"]:
            failures.append(f"{name}: textual fallback was used unexpectedly")
        if not record["icon_key"]:
            failures.append(f"{name}: icon key missing")
        return record

    for name in action_names:
        action_checks[name] = check_icon(name, getattr(window, name))
    action_checks["tool:focus_selected"] = check_icon(
        "tool:focus_selected",
        window.tool_palette.navigation_actions["focus_selected"],
    )
    for name in widget_names:
        target: Any = window
        for part in name.split("."):
            target = getattr(target, part)
        widget_checks[name] = check_icon(name, target)

    for name, button in window.tool_palette.tool_buttons.items():
        action_checks[f"tool:{name}"] = check_icon(f"tool:{name}", button)

    command_contract = window.top_command_contract.descriptor()
    if command_contract["physical_toolbar_required"]:
        failures.append(
            "semantic command contract unexpectedly requires legacy toolbars"
        )
    if tuple(command_contract["group_order"]) != (
        "file",
        "edit",
        "view",
        "export",
        "context",
        "render",
    ):
        failures.append("semantic command group order drifted")

    visible_toolbar = window.reference_top_toolbar
    toolbar_checks = {
        "reference_top_toolbar": {
            "object_name": visible_toolbar.objectName(),
            "visible": visible_toolbar.isVisibleTo(window),
            "tool_button_style": visible_toolbar.toolButtonStyle().name,
            "icon_size": [
                visible_toolbar.iconSize().width(),
                visible_toolbar.iconSize().height(),
            ],
        }
    }
    if (
        toolbar_checks["reference_top_toolbar"]["object_name"]
        != "reference_top_toolbar"
    ):
        failures.append("visible reference toolbar object name drifted")
    if not toolbar_checks["reference_top_toolbar"]["visible"]:
        failures.append("visible reference toolbar is hidden")
    if toolbar_checks["reference_top_toolbar"]["icon_size"] != [24, 24]:
        failures.append("visible reference toolbar icon size drifted")

    shortcut_sequences = sorted(
        str(shortcut.key().toString())
        for shortcut in window.findChildren(QShortcut)
        if not shortcut.key().isEmpty()
    )
    required_shortcuts = {"F", "X", "A", "1", "2", "3", "4", "5", "6", "Ctrl+K"}
    missing_shortcuts = sorted(required_shortcuts - set(shortcut_sequences))
    if missing_shortcuts:
        failures.append(f"shortcuts missing: {', '.join(missing_shortcuts)}")

    window.current_lang = "pt"
    window.update_language()
    translated_icon_checks = {
        "open_image_action": check_icon(
            "translated:open_image_action", window.open_image_action
        ),
        "gizmo_toggle": check_icon(
            "translated:gizmo_toggle", window.canvas.gizmo_toggle
        ),
        "language_action": check_icon(
            "translated:language_action", window.language_action
        ),
    }
    window.close()
    return {
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "catalog_size": len(ICON_SPECS),
        "actions": action_checks,
        "widgets": widget_checks,
        "translated": translated_icon_checks,
        "top_command_contract": command_contract,
        "toolbars": toolbar_checks,
        "shortcuts": {
            "actual": shortcut_sequences,
            "required": sorted(required_shortcuts),
            "missing": missing_shortcuts,
        },
    }


def _write_index() -> None:
    entries: dict[str, Any] = {}
    for path in sorted(EVIDENCE_ROOT.rglob("*")):
        if not path.is_file() or path == INDEX_PATH:
            continue
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
    visual_report = json.loads(
        (VISUAL_ROOT / "visual-audit-report.json").read_text(encoding="utf-8")
    )
    runtime = _runtime_icon_contract()
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": "Etapa 2 — Biblioteca de ícones e ações",
        "source_state": _source_state(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        },
        "commands": {
            "capture": capture,
            "visual_audit": visual,
        },
        "artifacts": {
            "raw_manifest": {
                "path": "raw-captures/manifest.json",
                **_digest(RAW_ROOT / "manifest.json"),
            },
            "visual_report": {
                "path": "visual-audit/visual-audit-report.json",
                **_digest(VISUAL_ROOT / "visual-audit-report.json"),
            },
        },
        "checks": {
            "capture_status": "PASS" if capture["returncode"] == 0 else "FAIL",
            "visual_status": visual_report["status"],
            "visual_finding_count": visual_report["finding_count"],
            "runtime_icon_contract": runtime,
        },
    }
    report["status"] = (
        "PASS"
        if capture["returncode"] == 0
        and visual["returncode"] == 0
        and runtime["status"] == "PASS"
        else "FAIL"
    )
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    lines = [
        "# Etapa 2 — Auditoria de ícones e ações",
        "",
        f"Status local: **{report['status']}**",
        "",
        "## Execução",
        "",
        "- Captura real da MainWindow: capture.log.",
        "- Auditoria Pillow/OpenCV/Qt: visual-audit/visual-audit-report.json.",
        "- Contrato live Qt de ícones, acessibilidade e atalhos: "
        "stage2-icon-report.json.",
        "",
        "## Resultado",
        "",
        f"- Captura: {report['checks']['capture_status']}.",
        f"- Auditoria visual: {report['checks']['visual_status']} "
        f"({report['checks']['visual_finding_count']} achados).",
        f"- Contrato de ícones: {runtime['status']}.",
        f"- Árvore limpa no momento da coleta: "
        f"{report['source_state']['worktree_clean']}.",
        "",
        "A árvore pode estar modificada durante a implementação; isso não é "
        "tratado como PASS de limpeza. A limpeza e a validação Git-blob serão "
        "executadas antes do commit.",
    ]
    REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    _write_index()
    print(json.dumps({"status": report["status"], "runtime": runtime["status"]}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
