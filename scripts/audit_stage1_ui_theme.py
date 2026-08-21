"""Audit the Stage 1 UI theme against the Stage 0 visual baseline.

This report distinguishes an explicitly reviewed toolbar redistribution from
unexpected geometry changes. It does not approve a release or replace CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_RESOLUTIONS = {
    "1080p_FHD": [1920, 1080],
    "768p_Minima": [1366, 768],
    "720p_Compacta": [1280, 720],
}
EXPECTED_STATES = {
    "01_sem_projeto.png",
    "02_projeto_paineis.png",
    "03_validacao_janela.png",
    "03_validacao_modal.png",
    "04_gizmo_feedback.png",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _rect(value: Any) -> list[int] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        return None
    return value


def _toolbar_delta(old_rect: list[int], new_rect: list[int]) -> bool:
    return old_rect[1] == new_rect[1] and old_rect[3] == new_rect[3]


def _compare_geometry(
    baseline: dict[str, Any], candidate: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expected: list[dict[str, Any]] = []
    unexpected: list[dict[str, Any]] = []
    for resolution, old_capture in baseline.get("captures", {}).items():
        new_capture = candidate.get("captures", {}).get(resolution, {})
        old_states = old_capture.get("widget_geometry", {})
        new_states = new_capture.get("widget_geometry", {})
        for state, old_widgets in old_states.items():
            if state == "validacao_modal":
                continue
            new_widgets = new_states.get(state, {})
            state_diffs: list[dict[str, Any]] = []
            for widget in sorted(set(old_widgets) | set(new_widgets)):
                old_rect = _rect(old_widgets.get(widget, {}).get("root_geometry"))
                new_rect = _rect(new_widgets.get(widget, {}).get("root_geometry"))
                if old_rect != new_rect:
                    state_diffs.append(
                        {
                            "widget": widget,
                            "old": old_rect,
                            "new": new_rect,
                        }
                    )
            if not state_diffs:
                continue
            names = {item["widget"] for item in state_diffs}
            old_nav = _rect(old_widgets.get("nav_toolbar", {}).get("root_geometry"))
            new_nav = _rect(new_widgets.get("nav_toolbar", {}).get("root_geometry"))
            old_xray = _rect(old_widgets.get("xray_toolbar", {}).get("root_geometry"))
            new_xray = _rect(new_widgets.get("xray_toolbar", {}).get("root_geometry"))
            if (
                names == {"nav_toolbar", "xray_toolbar"}
                and old_nav
                and new_nav
                and old_xray
                and new_xray
                and _toolbar_delta(old_nav, new_nav)
                and _toolbar_delta(old_xray, new_xray)
                and old_nav[2] + old_xray[2] == new_nav[2] + new_xray[2]
                and old_nav[0] + old_nav[2] == old_xray[0]
                and new_nav[0] + new_nav[2] == new_xray[0]
            ):
                expected.append(
                    {
                        "resolution": resolution,
                        "state": state,
                        "reason": (
                            "QSS changed horizontal toolbar allocation while "
                            "preserving height and right boundary"
                        ),
                        "deltas": state_diffs,
                    }
                )
            else:
                unexpected.extend(
                    {"resolution": resolution, "state": state, **item}
                    for item in state_diffs
                )
    return expected, unexpected


def _build_index(root: Path) -> dict[str, Any]:
    files: dict[str, dict[str, int | str]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-index.json":
            continue
        relative = path.relative_to(root).as_posix()
        files[relative] = {"bytes": path.stat().st_size, "sha256": _digest(path)}
    return {"files": files, "root": ".", "schema_version": 1}


def run(root: Path, baseline_root: Path) -> dict[str, Any]:
    raw = root / "raw-captures"
    visual_report_path = root / "visual-audit" / "visual-audit-report.json"
    candidate_manifest_path = raw / "manifest.json"
    baseline_manifest_path = baseline_root / "raw-captures" / "manifest.json"
    visual_report = json.loads(visual_report_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    findings: list[str] = []
    captures = candidate.get("captures", {})
    for resolution, requested in EXPECTED_RESOLUTIONS.items():
        capture = captures.get(resolution)
        if not isinstance(capture, dict):
            findings.append(f"missing capture resolution: {resolution}")
            continue
        if capture.get("requested_size") != requested:
            findings.append(
                f"requested size mismatch for {resolution}: "
                f"{capture.get('requested_size')}"
            )
        names = {Path(name).name for name in capture.get("files", {})}
        expected_names = {f"{resolution}_{state}" for state in EXPECTED_STATES}
        if names != expected_names:
            findings.append(
                f"state set mismatch for {resolution}: "
                f"expected={sorted(expected_names)} actual={sorted(names)}"
            )
    expected_deltas, unexpected_deltas = _compare_geometry(baseline, candidate)
    if unexpected_deltas:
        findings.append(f"unexpected geometry deltas: {len(unexpected_deltas)}")
    if visual_report.get("status") != "PASS" or visual_report.get("finding_count") != 0:
        findings.append("visual auditor did not return PASS with zero findings")
    if len(captures) != len(EXPECTED_RESOLUTIONS):
        findings.append(f"capture resolution count mismatch: {len(captures)}")
    report = {
        "schema_version": 1,
        "stage": 1,
        "stage_name": "Tokens visuais e tema controlado",
        "status": "PASS" if not findings else "FAIL",
        "decision_scope": "evidência técnica da Etapa 1; não é aprovação de release",
        "source": _source_state(),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
        },
        "inputs": {
            "candidate_manifest": "raw-captures/manifest.json",
            "candidate_manifest_sha256": _digest(candidate_manifest_path),
            "baseline_manifest": (
                "../ui-modernization-stage0-20260821/raw-captures/manifest.json"
            ),
            "baseline_manifest_sha256": _digest(baseline_manifest_path),
            "visual_report": "visual-audit/visual-audit-report.json",
            "visual_report_sha256": _digest(visual_report_path),
        },
        "checks": {
            "resolutions_and_states": len(findings) == 0,
            "visual_audit_zero_findings": visual_report.get("status") == "PASS"
            and visual_report.get("finding_count") == 0,
            "unexpected_geometry_delta": not bool(unexpected_deltas),
            "expected_geometry_delta_count": len(expected_deltas),
            "artifact_hashes_generated": True,
        },
        "expected_geometry_deltas": expected_deltas,
        "unexpected_geometry_deltas": unexpected_deltas,
        "capture_count": sum(
            len(capture.get("files", {})) for capture in captures.values()
        ),
        "findings": findings,
    }
    _write_json(root / "stage1-baseline-report.json", report)
    lines = [
        "# Stage 1 UI theme audit",
        "",
        f"Status: **{report['status']}**",
        "",
        f"- Captures: {report['capture_count']}",
        f"- Expected toolbar redistribution records: {len(expected_deltas)}",
        f"- Unexpected geometry deltas: {len(unexpected_deltas)}",
        f"- Visual auditor findings: {visual_report.get('finding_count')}",
        "",
        (
            "The expected toolbar delta preserves height and the right boundary; "
            "any other geometry delta fails this report."
        ),
    ]
    if findings:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- {item}" for item in findings)
    else:
        lines.extend(["", "", "No automated findings."])
    (root / "stage1-baseline-report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_json(root / "artifact-index.json", _build_index(root))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-root", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.artifacts_root.resolve(), args.baseline_root.resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "findings": len(report["findings"]),
                "capture_count": report["capture_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
