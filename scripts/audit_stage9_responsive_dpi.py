"""Reproducible Stage 9 resolution and DPI audit."""

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

ROOT = Path(__file__).resolve().parents[1]
RESOLUTIONS = {
    "720p_Compacta": (1280, 720),
    "768p_Minima": (1366, 768),
    "1080p_FHD": (1920, 1080),
}
DPI_CASES = (("100", 1.0), ("125", 1.25), ("150", 1.5), ("200", 2.0))
CRITICAL_WIDGETS = (
    "main_splitter",
    "reference_tool_palette",
    "canvas",
    "panel_stack",
)
REQUIRED_TABS = ("Objects", "Layers", "Groups", "Collision")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def source_state() -> dict[str, Any]:
    status = git("status", "--porcelain")
    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _run_functional_isolated(output: Path, scale: float) -> dict[str, Any]:
    """Run the functional audit without sharing its QApplication instance."""

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-c",
        (
            "import sys; "
            "from pathlib import Path; "
            "from scripts.audit_stage9_functional_ui import run; "
            "result = run(Path(sys.argv[1])); "
            "print('AUTOMATED_STATUS=' + result.get('automated_status', 'FAIL'))"
        ),
        str(output),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "QT_SCALE_FACTOR": str(scale),
            "QT_AUTO_SCREEN_SCALE_FACTOR": "0",
        },
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        (output / "functional-worker.stdout.log").write_text(
            completed.stdout, encoding="utf-8", newline="\n"
        )
    if completed.stderr:
        (output / "functional-worker.stderr.log").write_text(
            completed.stderr, encoding="utf-8", newline="\n"
        )
    report_path = output / "report.json"
    if not report_path.is_file():
        return {
            "automated_status": "FAIL",
            "fatal_error": {
                "type": "FunctionalAuditProcessError",
                "message": "The isolated functional audit did not produce report.json.",
            },
            "process_returncode": completed.returncode,
        }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["process_returncode"] = completed.returncode
    if completed.returncode != 0:
        report["automated_status"] = "FAIL"
    return report


def widget_presence(manifest: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    states: dict[str, Any] = {}
    for resolution, capture in manifest.get("captures", {}).items():
        geometry = capture.get("widget_geometry", {}).get("projeto_paineis", {})
        tab_visibility = geometry.get("tab_visibility", {})
        state: dict[str, Any] = {}
        for name in CRITICAL_WIDGETS:
            snapshot = geometry.get(name)
            valid = (
                isinstance(snapshot, dict)
                and snapshot.get("visible") is True
                and isinstance(snapshot.get("geometry"), list)
                and len(snapshot["geometry"]) == 4
                and snapshot["geometry"][2] > 0
                and snapshot["geometry"][3] > 0
            )
            state[name] = {"status": "PASS" if valid else "FAIL", "snapshot": snapshot}
            if not valid:
                failures.append(
                    {"resolution": resolution, "widget": name, "snapshot": snapshot}
                )
        active_tab_containers = []
        for container in ("reference_panel_tabs", "compact_panel_tabs"):
            tabs = tab_visibility.get(container, {})
            if tabs.get("visible_to_root") is True:
                active_tab_containers.append(container)
            pages = tabs.get("pages", [])
            titles = [page.get("title") for page in pages if isinstance(page, dict)]
            pages_valid = all(title in titles for title in REQUIRED_TABS)
            page_geometry_valid = all(
                isinstance(page.get("geometry"), list)
                and len(page["geometry"]) == 4
                and page["geometry"][2] > 0
                and page["geometry"][3] > 0
                for page in pages
                if isinstance(page, dict) and page.get("title") in REQUIRED_TABS
            )
            active_pages_valid = (
                pages_valid and page_geometry_valid
                if tabs.get("visible_to_root") is True
                else True
            )
            state[f"{container}_pages"] = {
                "status": "PASS" if active_pages_valid else "FAIL",
                "active": tabs.get("visible_to_root") is True,
                "titles": titles,
                "pages": pages,
            }
            if not active_pages_valid:
                failures.append(
                    {
                        "resolution": resolution,
                        "widget": f"{container}_pages",
                        "titles": titles,
                        "pages": pages,
                    }
                )
        state["active_panel_tabs"] = {
            "status": "PASS" if len(active_tab_containers) == 1 else "FAIL",
            "active": active_tab_containers,
        }
        if len(active_tab_containers) != 1:
            failures.append(
                {
                    "resolution": resolution,
                    "widget": "active_panel_tabs",
                    "active": active_tab_containers,
                }
            )
        states[resolution] = state
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "states": states,
    }


def capture_dimensions(manifest: dict[str, Any], scale: float) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    states: dict[str, Any] = {}
    for label, (width, height) in RESOLUTIONS.items():
        capture = manifest.get("captures", {}).get(label, {})
        actual_window = capture.get("actual_window_size")
        actual_capture = capture.get("actual_capture_size")
        expected_logical = [width, height]
        expected_physical = [round(width * scale), round(height * scale)]
        passed = (
            actual_window == expected_logical and actual_capture == expected_physical
        )
        states[label] = {
            "requested_logical": expected_logical,
            "expected_physical": expected_physical,
            "actual_window_size": actual_window,
            "actual_capture_size": actual_capture,
            "status": "PASS" if passed else "FAIL",
        }
        if not passed:
            failures.append(states[label])
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "states": states,
    }


def run_worker(output: Path, dpi_label: str, scale: float) -> int:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_SCALE_FACTOR"] = str(scale)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    from PySide6.QtWidgets import QApplication

    from scripts.audit_ui_capture import run as run_capture
    from scripts.audit_visual_artifacts import run_audit

    output.mkdir(parents=True, exist_ok=True)
    functional = _run_functional_isolated(output / "functional", scale)
    manifest = run_capture(output / "visual-input")
    visual = run_audit(output / "visual-input", output / "visual-audit")
    dimensions = capture_dimensions(manifest, scale)
    widgets = widget_presence(manifest)
    checks = {
        "functional_actions": functional.get("checks", {}).get("functional_actions")
        is True,
        "visual_geometry": functional.get("checks", {}).get("visual_geometry") is True,
        "visual_artifacts": visual.get("status") == "PASS"
        and visual.get("finding_count") == 0,
        "capture_dimensions": dimensions["status"] == "PASS",
        "critical_widgets": widgets["status"] == "PASS",
    }
    app = QApplication.instance()
    report = {
        "schema_version": 1,
        "dpi": {"label": dpi_label, "requested_scale": scale},
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
            "qt_scale_factor": os.environ.get("QT_SCALE_FACTOR"),
            "observed_dpr": app.devicePixelRatio() if app else None,
        },
        "checks": checks,
        "automated_status": "PASS" if all(checks.values()) else "FAIL",
        "functional_summary": {
            "checks": functional.get("checks"),
            "visual_findings": functional.get("visual", {}).get("findings", []),
            "report": "functional/report.json",
        },
        "visual_summary": {
            "status": visual.get("status"),
            "finding_count": visual.get("finding_count"),
            "report": "visual-audit/visual-audit-report.json",
        },
        "capture_dimensions": dimensions,
        "critical_widgets": widgets,
        "source": source_state(),
    }
    report_path = output / "stage9-worker-report.json"
    report["report"] = {"file": report_path.name, "sha256": ""}
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report["report"]["sha256"] = sha256(report_path)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if report["automated_status"] == "PASS" else 1


def run_parent(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    workers: list[dict[str, Any]] = []
    for dpi_label, scale in DPI_CASES:
        worker_dir = output / ("dpi_" + dpi_label)
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--output",
            str(worker_dir),
            "--dpi-label",
            dpi_label,
            "--scale",
            str(scale),
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            capture_output=True,
            text=True,
        )
        worker_report_path = worker_dir / "stage9-worker-report.json"
        worker_report = (
            json.loads(worker_report_path.read_text(encoding="utf-8"))
            if worker_report_path.is_file()
            else {"automated_status": "FAIL", "missing_report": True}
        )
        worker_report["process_returncode"] = completed.returncode
        if completed.stderr:
            (worker_dir / "worker.stderr.log").write_text(
                completed.stderr, encoding="utf-8", newline="\n"
            )
        workers.append(worker_report)
    automated_status = (
        "PASS"
        if workers and all(item.get("automated_status") == "PASS" for item in workers)
        else "FAIL"
    )
    report = {
        "schema_version": 1,
        "scope": "Etapa 9 - responsividade e DPI",
        "matrix": {
            "resolutions": {
                label: {
                    "width": size[0],
                    "height": size[1],
                    "mode": "desktop" if size[0] >= 1920 else "compact",
                }
                for label, size in RESOLUTIONS.items()
            },
            "dpi": [{"label": label, "scale": scale} for label, scale in DPI_CASES],
        },
        "automated_status": automated_status,
        "decision": "PARCIAL",
        "reason": (
            "Automacao concluida; revisao humana, CI e "
            "pos-merge ainda nao foram executados."
        ),
        "human_review": "NOT_CONFIRMED",
        "source": source_state(),
        "workers": workers,
        "limitations": [
            (
                "DPI e renderizacao dependentes de driver continuam informativos; "
                "a matriz valida o contrato Qt/offscreen."
            ),
            "Aprovacao visual humana nao e inferida a partir de PASS automatico.",
            "Worktree sujo nao e convertido em PASS.",
        ],
    }
    report_path = output / "stage9-responsive-dpi-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    index = {
        "schema_version": 1,
        "report": {"file": report_path.name, "sha256": sha256(report_path)},
        "workers": [],
    }
    for item in workers:
        label = item.get("dpi", {}).get("label", "unknown")
        worker_path = output / ("dpi_" + label) / "stage9-worker-report.json"
        index["workers"].append(
            {
                "dpi": item.get("dpi"),
                "file": str(worker_path.relative_to(output)),
                "sha256": sha256(worker_path) if worker_path.is_file() else None,
            }
        )
    (output / "artifact-index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    lines = [
        "# Etapa 9 - Auditoria de responsividade e DPI",
        "",
        f"Automated status: **{automated_status}**",
        "",
        "The automated matrix is not a human visual approval.",
        "",
        "## Matrix",
        "",
        "| DPI | Scale | Status |",
        "|---:|---:|:---|",
    ]
    for item in workers:
        dpi = item.get("dpi", {})
        lines.append(
            (
                f"| {dpi.get('label', '?')} | {dpi.get('requested_scale', '?')} | "
                f"{item.get('automated_status', 'FAIL')} |"
            )
        )
    lines.extend(
        [
            "",
            "## Required human review",
            "",
            "- [ ] 1280x720 compact",
            "- [ ] 1366x768 compact",
            "- [ ] 1920x1080 desktop",
            "- [ ] DPI 100%, 125%, 150%, 200%",
            "- [ ] text, panels, canvas, gizmo, toolbars, menus and palette",
            "",
            "Source worktree state is recorded in the JSON report.",
        ]
    )
    (output / "stage9-responsive-dpi-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    return 0 if automated_status == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--dpi-label", default="")
    parser.add_argument("--scale", type=float, default=1.0)
    args = parser.parse_args()
    if args.worker:
        return run_worker(args.output.resolve(), args.dpi_label, args.scale)
    return run_parent(args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
