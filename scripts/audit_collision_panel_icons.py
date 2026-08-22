"""Audit the real Collision panel icon contract on the Windows Qt backend."""

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

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from scripts.audit_ui_capture import (
    RESOLUTIONS,
    AuditConfig,
    _capture,
    _prepare_project,
    _settle,
)
from src.ui.main_window import MainWindow

os.environ.pop("QT_QPA_PLATFORM", None)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / "ui-modernization-stage5-20260822"
    / "collision-icon-audit"
)


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    ).strip()


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    scene, project_path = _prepare_project(output_dir)
    records: dict[str, Any] = {}
    findings: list[str] = []
    window = None
    try:
        for label, (width, height) in RESOLUTIONS.items():
            window = MainWindow(scene, AuditConfig())
            window._project_path = project_path
            window._document_name = project_path.name
            window._refresh_document_views(project_loaded=True)
            window.resize(width, height)
            window.show()
            _settle(app, 80)
            tabs = (
                window.reference_panel_tabs
                if window.reference_panel_tabs.isVisibleTo(window)
                else window.compact_panel_tabs
            )
            tabs.setCurrentWidget(window.collision_panel)
            _settle(app, 80)
            capture_path = output_dir / f"{label}_collision.png"
            _capture(window, capture_path)
            image = QImage(str(capture_path))
            if image.isNull():
                findings.append(f"{label}: capture is unreadable")
            buttons = {
                "batch_test": window.collision_panel.batch_test_btn,
                "export": window.collision_panel.export_btn,
                "auto_generate": window.collision_panel.auto_gen_btn,
            }
            button_records: dict[str, Any] = {}
            for name, button in buttons.items():
                text = button.text()
                record = {
                    "text": text,
                    "icon_key": button.property("iconKey"),
                    "icon_null": button.icon().isNull(),
                    "icon_fallback": button.property("iconFallback"),
                    "accessible_name": button.accessibleName(),
                    "visible_to_window": button.isVisibleTo(window),
                    "icon_size": [
                        button.iconSize().width(),
                        button.iconSize().height(),
                    ],
                }
                button_records[name] = record
                if record["icon_null"]:
                    findings.append(f"{label}/{name}: icon is null")
                if record["icon_fallback"] is not False:
                    findings.append(f"{label}/{name}: icon fallback is active")
                if not record["accessible_name"]:
                    findings.append(f"{label}/{name}: accessible name is missing")
                if any(ord(character) > 0xFFFF for character in text):
                    findings.append(f"{label}/{name}: emoji/nonportable glyph remains")
                if record["icon_size"] != [20, 20]:
                    findings.append(f"{label}/{name}: icon size is not 20x20")
                if not record["visible_to_window"]:
                    findings.append(f"{label}/{name}: button is not visible")
            records[label] = {
                "resolution": [width, height],
                "active_tabs": [tabs.tabText(index) for index in range(tabs.count())],
                "active_tab": tabs.tabText(tabs.currentIndex()),
                "capture": {
                    "file": capture_path.name,
                    "dimensions": [image.width(), image.height()],
                    **_digest(capture_path),
                },
                "buttons": button_records,
            }
            window.close()
            window = None
            _settle(app, 20)
    finally:
        if window is not None:
            window.close()
        _settle(app, 20)

    report = {
        "schema_version": 1,
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "qt_platform": app.platformName(),
        "platform": platform.platform(),
        "source_state": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean": not bool(_git("status", "--porcelain")),
        },
        "records": records,
    }
    report_path = output_dir / "collision-icon-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest = {
        "schema_version": 1,
        "files": {
            "collision-icon-report.json": _digest(report_path),
            **{
                record["capture"]["file"]: {
                    "bytes": record["capture"]["bytes"],
                    "sha256": record["capture"]["sha256"],
                }
                for record in records.values()
            },
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "finding_count": report["finding_count"],
                "records": len(report["records"]),
                "qt_platform": report["qt_platform"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
