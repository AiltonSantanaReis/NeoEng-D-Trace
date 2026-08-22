"""Reproducible Stage 5 viewport/HUD audit on the real Windows Qt backend."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QRect, QSize
from PySide6.QtWidgets import QApplication, QLabel

# The shared capture module defaults to offscreen for CI. Remove that default
# after import so this audit intentionally exercises the Windows backend.
from scripts.audit_ui_capture import (
    RESOLUTIONS,
    AuditConfig,
    _capture,
    _prepare_project,
    _settle,
)
from scripts.audit_ui_capture import run as capture_main_window
from scripts.audit_visual_artifacts import run_audit
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = (
    ROOT / "docs" / "evidence" / "artifacts" / "ui-modernization-stage5-20260822"
)
RAW_ROOT = EVIDENCE_ROOT / "windows-captures"
VISUAL_ROOT = EVIDENCE_ROOT / "windows-visual-audit"
FUNCTIONAL_ROOT = EVIDENCE_ROOT / "functional-captures"
REPORT_PATH = EVIDENCE_ROOT / "stage5-viewport-hud-report.json"


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
    ).strip()


def _functional_contract() -> dict[str, Any]:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    scene, project_path = _prepare_project(RAW_ROOT)
    records: dict[str, Any] = {}
    failures: list[str] = []

    for label, (width, height) in RESOLUTIONS.items():
        window = MainWindow(scene, AuditConfig())
        window._project_path = project_path
        window._document_name = project_path.name
        window._refresh_document_views(project_loaded=True)
        window.resize(QSize(width, height))
        window.show()
        _settle(app, 40)

        actions = (
            ("lit_1to1", window.act_lit, window.act_100, "VIEW: LIT  |  ZOOM: 1.00x"),
            ("xray1", window.act_xray1, None, "VIEW: X-RAY 1  |  ZOOM: 1.00x"),
            ("fit", window.act_fit, None, None),
            (
                "xray1_1to1",
                window.act_xray1,
                window.act_100,
                "VIEW: X-RAY 1  |  ZOOM: 1.00x",
            ),
        )
        for state, first, second, expected in actions:
            first.trigger()
            if second is not None:
                second.trigger()
            _settle(app, 100 if "xray" in state else 40)
            capture_path = FUNCTIONAL_ROOT / f"{label}_{state}.png"
            _capture(window, capture_path)
            status = window.viewport_status
            actual = status.text()
            if expected is not None and actual != expected:
                failures.append(
                    f"{label}/{state}: status text {actual!r} != {expected!r}"
                )
            if not status.isVisibleTo(window):
                failures.append(f"{label}/{state}: status is not visible")
            if not window.statusBar().rect().contains(status.geometry()):
                failures.append(f"{label}/{state}: status geometry escapes status bar")
            if window.canvas.findChildren(QLabel):
                failures.append(f"{label}/{state}: canvas contains a QLabel HUD")
            records[f"{label}/{state}"] = {
                "size": [width, height],
                "status_text": actual,
                "view_mode": window.canvas._view_mode,
                "zoom": window.canvas.get_zoom(),
                "status_geometry": [
                    status.x(),
                    status.y(),
                    status.width(),
                    status.height(),
                ],
                "status_bar_geometry": [
                    window.statusBar().x(),
                    window.statusBar().y(),
                    window.statusBar().width(),
                    window.statusBar().height(),
                ],
                "canvas_geometry": [
                    window.canvas.x(),
                    window.canvas.y(),
                    window.canvas.width(),
                    window.canvas.height(),
                ],
                "file": capture_path.relative_to(EVIDENCE_ROOT).as_posix(),
                "digest": _digest(capture_path),
            }
        window.close()
        _settle(app, 20)

    return {
        "status": "PASS" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "states": records,
        "qt_platform": app.platformName(),
    }


def main() -> int:
    # audit_ui_capture installs an offscreen default at import time; this audit
    # must be run on the real Windows backend, not a headless substitution.
    os.environ.pop("QT_QPA_PLATFORM", None)
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    FUNCTIONAL_ROOT.mkdir(parents=True, exist_ok=True)

    capture_manifest = capture_main_window(RAW_ROOT)
    visual_report = run_audit(RAW_ROOT, VISUAL_ROOT)
    functional = _functional_contract()
    report = {
        "schema_version": 1,
        "stage": "Etapa 5 — Viewport e HUD",
        "source_state": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean": not bool(_git("status", "--porcelain")),
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "qt_platform": functional["qt_platform"],
        },
        "scope": [
            "viewport state moved to permanent status bar",
            "live Lit/X-Ray/zoom/Fit/1:1 status synchronization",
            "legacy canvas HUD not invoked by MainWindow",
            "gizmo, masks, side panels and scenario editor contracts preserved",
        ],
        "capture_manifest": {
            "file": "windows-captures/manifest.json",
            "sha256": _digest(RAW_ROOT / "manifest.json")["sha256"],
            "resolution_count": len(capture_manifest["captures"]),
        },
        "visual_audit": {
            "status": visual_report["status"],
            "finding_count": visual_report["finding_count"],
            "report": "windows-visual-audit/visual-audit-report.json",
        },
        "functional_contract": functional,
        "decision": (
            "PASS"
            if visual_report["status"] == "PASS" and functional["status"] == "PASS"
            else "FAIL"
        ),
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "decision": report["decision"],
                "visual_findings": visual_report["finding_count"],
                "functional_failures": functional["failure_count"],
                "qt_platform": functional["qt_platform"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
