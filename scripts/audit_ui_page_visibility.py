"""Audit real Qt page visibility across the main and scenario editors.

The audit fails closed if an inactive QTabWidget/QStackedWidget page is visible
in the live Windows Qt hierarchy. It records only runtime geometry/visibility
facts and does not alter the product or its gates.
"""

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

from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from scripts.audit_ui_capture import (  # noqa: E402
    AuditConfig,
    _prepare_project,
    _settle,
)

os.environ.pop("QT_QPA_PLATFORM", None)
from src.ui.main_window import MainWindow  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / "ui-modernization-stage5-20260822"
    / "page-visibility-audit"
)


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    ).strip()


def _snapshot_stack(stack: Any, root: Any) -> dict[str, Any]:
    return {
        "current_index": stack.currentIndex(),
        "visible_to_root": stack.isVisibleTo(root),
        "pages": [
            {
                "index": index,
                "title": (
                    stack.tabText(index)
                    if hasattr(stack, "tabText")
                    else stack.widget(index).objectName()
                ),
                "current": index == stack.currentIndex(),
                "visible": stack.widget(index).isVisible(),
                "visible_to_root": stack.widget(index).isVisibleTo(root),
                "geometry": [
                    stack.widget(index).x(),
                    stack.widget(index).y(),
                    stack.widget(index).width(),
                    stack.widget(index).height(),
                ],
            }
            for index in range(stack.count())
        ],
    }


def _visibility_findings(name: str, snapshot: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    container_visible = bool(snapshot["visible_to_root"])
    current_index = snapshot["current_index"]
    for page in snapshot["pages"]:
        rendered = bool(page["visible"]) and bool(page["visible_to_root"])
        expected = container_visible and page["index"] == current_index
        if rendered != expected:
            findings.append(
                f"{name}: page {page['index']} rendered={rendered} expected={expected}"
            )
    return findings


def _record(
    name: str, stack: Any, root: Any, records: dict[str, Any], findings: list[str]
) -> None:
    snapshot = _snapshot_stack(stack, root)
    records[name] = snapshot
    findings.extend(_visibility_findings(name, snapshot))


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    scene, _project = _prepare_project(output_dir)
    records: dict[str, Any] = {}
    findings: list[str] = []
    window = MainWindow(scene, AuditConfig())
    try:
        window.show()
        for label, size in (
            ("desktop", QSize(1920, 1080)),
            ("compact", QSize(1280, 720)),
        ):
            window.resize(size)
            _settle(app, 80)
            tabs = (
                window.reference_panel_tabs
                if window.reference_panel_tabs.isVisibleTo(window)
                else window.compact_panel_tabs
            )
            for index in range(tabs.count()):
                tabs.setCurrentIndex(index)
                _settle(app, 30)
                _record(
                    f"main/{label}/{tabs.tabText(index)}",
                    tabs,
                    window,
                    records,
                    findings,
                )
        window.open_scenario_editor()
        _settle(app, 80)
        editor = window.scenario_editor_window
        if editor is None:
            findings.append("scenario editor was not created")
        else:
            _record(
                "scenario/viewport_pages",
                editor.professional_pages,
                editor,
                records,
                findings,
            )
            _record(
                "scenario/right_pages",
                editor.right_pages,
                editor,
                records,
                findings,
            )
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
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
    report_path = output_dir / "page-visibility-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    raw = report_path.read_bytes()
    manifest = {
        "schema_version": 1,
        "report": {
            "file": report_path.name,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
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
