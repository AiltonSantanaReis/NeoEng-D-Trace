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

from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
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
REFERENCE_PATH = EVIDENCE_ROOT / "reference" / "reference-chrome.png"


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _reference_fixture_metadata() -> dict[str, Any]:
    """Read and fingerprint the user-provided chrome reference fixture."""
    if not REFERENCE_PATH.is_file():
        return {
            "status": "FAIL",
            "file": "reference/reference-chrome.png",
            "reason": "reference fixture is missing",
        }
    raw = REFERENCE_PATH.read_bytes()
    image = QImage(str(REFERENCE_PATH))
    if image.isNull():
        return {
            "status": "FAIL",
            "file": "reference/reference-chrome.png",
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "reason": "reference fixture is unreadable",
        }
    return {
        "status": "PASS",
        "file": "reference/reference-chrome.png",
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "dimensions": [image.width(), image.height()],
        "comparison_method": (
            "chrome geometry and interaction contract; central illustrative scene "
            "pixels excluded"
        ),
    }


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


def _reference_shell_contract() -> dict[str, Any]:
    """Validate the reference chrome against live Qt geometry and actions."""
    app = QApplication.instance() or QApplication(sys.argv)
    fixture = _reference_fixture_metadata()
    if fixture["status"] != "PASS":
        return {
            "status": "FAIL",
            "failure_count": 1,
            "failures": [fixture.get("reason", "invalid reference fixture")],
            "platform": app.platformName(),
            "reference_fixture": fixture,
        }
    scene, project_path = _prepare_project(RAW_ROOT)
    window = MainWindow(scene, AuditConfig())
    window._project_path = project_path
    window._document_name = project_path.name
    window._refresh_document_views(project_loaded=True)
    window.resize(QSize(1920, 1080))
    window.show()
    _settle(app, 120)
    failures: list[str] = []
    try:
        if app.platformName().lower() != "windows":
            failures.append(f"reference shell ran on {app.platformName()}, not Windows")
        if not window.reference_top_toolbar.isVisibleTo(window):
            failures.append("reference top toolbar is not visible")
        if window.menuBar().isVisibleTo(window):
            failures.append("legacy menu bar remains visible beside reference toolbar")
        if not window.reference_command_search.isVisibleTo(window):
            failures.append("reference command search is not visible")
        desktop_panel = window.desktop_panel_splitter
        desktop_tabs = window.reference_panel_tabs
        if window.panel_stack.currentWidget() is not desktop_panel:
            failures.append("desktop panel stack is not the active 1920px layout")
        expected_tabs = ["Objects", "Layers", "Groups", "Collision"]
        desktop_tab_labels = [
            desktop_tabs.tabText(i) for i in range(desktop_tabs.count())
        ]
        if not desktop_tabs.isVisibleTo(window):
            failures.append("reference desktop tabbed dock is not visible")
        if desktop_tab_labels != expected_tabs:
            failures.append(
                f"desktop reference tabs {desktop_tab_labels!r} != {expected_tabs!r}"
            )

        sizes = window.main_splitter.sizes()
        if len(sizes) != 3:
            failures.append(f"reference workspace has {len(sizes)} splitter regions")
        else:
            tool_width, canvas_width, panel_width = sizes
            if not 72 <= tool_width <= 84:
                failures.append(
                    f"left reference tool width {tool_width} outside 72..84"
                )
            if not 480 <= panel_width <= 900:
                failures.append(f"right panel width {panel_width} outside 480..900")
            if canvas_width <= tool_width or canvas_width <= panel_width:
                failures.append("viewport is not the dominant workspace region")

        chrome = getattr(window, "viewport_chrome", None)
        if chrome is None:
            failures.append("viewport chrome wrapper is missing")
        else:
            overlay = getattr(chrome, "overlay", None)
            horizontal = getattr(chrome, "horizontal_ruler", None)
            vertical = getattr(chrome, "vertical_ruler", None)
            if overlay is None or not overlay.isVisibleTo(window):
                failures.append("viewport overlay bar is not visible")
            if horizontal is None or vertical is None:
                failures.append("viewport rulers are incomplete")
            elif horizontal.height() <= 0 or vertical.width() <= 0:
                failures.append("viewport rulers have zero geometry")
            if overlay is not None and not chrome.rect().contains(overlay.geometry()):
                failures.append("viewport overlay escapes its chrome bounds")

        window.resize(QSize(1280, 720))
        _settle(app, 50)
        panel_tabs = window.compact_panel_tabs
        expected_tabs = ["Objects", "Layers", "Groups", "Collision"]
        actual_tabs = [panel_tabs.tabText(i) for i in range(panel_tabs.count())]
        if actual_tabs != expected_tabs:
            failures.append(
                f"compact responsive panel tabs {actual_tabs!r} != {expected_tabs!r}"
            )
        panel_tabs.setCurrentWidget(window.layers)
        _settle(app, 50)
        if not window.layers.action_toolbar.isVisibleTo(window):
            failures.append(
                "Layers action toolbar is not visible when Layers is selected"
            )
        if len(window.layers.action_toolbar.actions()) != 6:
            failures.append("Layers action toolbar does not expose six real actions")
        if any(
            button.isVisible()
            for button in (
                window.layers.btn_new,
                window.layers.btn_delete,
                window.layers.btn_up,
                window.layers.btn_down,
                window.layers.btn_vis,
                window.layers.btn_lock,
            )
        ):
            failures.append("legacy text layer buttons remain visible")
        if (
            window.layers.list.count()
            and window.layers.list.item(0).font().family() != "Segoe UI"
        ):
            failures.append("layer item delegate is not pinned to Segoe UI")
        window.reference_pan_button.click()
        if (
            not window.canvas.is_pan_mode()
            or not window.reference_pan_button.isChecked()
        ):
            failures.append("Pan button did not enable the live canvas pan mode")
        window.reference_select_button.click()
        if window.canvas.is_pan_mode() or window.reference_pan_button.isChecked():
            failures.append("Select button did not disable the live canvas pan mode")

        return {
            "status": "PASS" if not failures else "FAIL",
            "failure_count": len(failures),
            "failures": failures,
            "platform": app.platformName(),
            "tabs": actual_tabs,
            "desktop_tabs": desktop_tab_labels,
            "splitter_sizes": sizes,
            "desktop_panel_widget": type(desktop_tabs).__name__,
            "left_toolbar_width": sizes[0],
            "toolbar_actions": len(window.layers.action_toolbar.actions()),
            "reference_fixture": fixture,
        }
    finally:
        window.close()
        _settle(app, 20)


def _reference_visual_match(reference_shell: dict[str, Any]) -> dict[str, Any]:
    """Compare the live chrome structure with the supplied reference target.

    This is intentionally stricter than the functional shell contract.  A
    passing interaction/layout contract does not prove visual parity with the
    target image, so known structural differences remain a real gate.
    """
    gaps: list[str] = []
    if reference_shell.get("desktop_panel_widget") != "QTabWidget":
        gaps.append(
            "desktop right region is still the historical splitter layout; "
            "the reference requires one tabbed inspector dock"
        )
    left_width = reference_shell.get("left_toolbar_width")
    if not isinstance(left_width, int) or left_width > 100:
        gaps.append(
            "left toolbar remains wider than the narrow icon-toolbar target "
            f"(live width={left_width!r})"
        )
    return {
        "status": "PASS" if not gaps else "FAIL",
        "method": "live Qt structure compared with reference chrome contract",
        "central_scene_excluded": True,
        "gaps": gaps,
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
    reference_fixture = _reference_fixture_metadata()
    reference_shell = _reference_shell_contract()
    reference_match = _reference_visual_match(reference_shell)
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
            "reference-aligned toolbar, viewport rulers, HUD overlay and live "
            "Pan/Select controls",
            "historical desktop panel splitters preserved; compact panel tabs "
            "and Layers action toolbar verified",
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
        "reference_shell_contract": reference_shell,
        "reference_fixture": reference_fixture,
        "reference_visual_match": reference_match,
        "decision": (
            "PASS"
            if visual_report["status"] == "PASS"
            and functional["status"] == "PASS"
            and reference_shell["status"] == "PASS"
            and reference_fixture["status"] == "PASS"
            and reference_match["status"] == "PASS"
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
                "reference_failures": reference_shell["failure_count"],
                "qt_platform": functional["qt_platform"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
