"""Run the complete local quality gate for the professional scenario editor.

This stage-level audit composes the real Qt captures, the existing visual
auditor, the professional-editor capture, and the deterministic preview/export
benchmark.  It is fail-closed: a dirty source tree, missing state, visual
finding, non-deterministic output, leaked host path, or timing over a safety
ceiling produces ``FAIL``.  The engine adapters remain separate contracts;
their real Stage 5 evidence is referenced rather than silently reclassified.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from scripts.audit_stage4_professional_scene_capture import capture as capture_scene
from scripts.audit_stage4b5_quality import (
    _benchmark,
    _determinism_checks,
    _fixture,
)
from scripts.audit_ui_capture import run as capture_main_window
from scripts.audit_visual_artifacts import run_audit
from tools.evidence_integrity import digest_path, write_json_lf

ROOT = Path(__file__).resolve().parents[1]
STAGE5_EVIDENCE = "docs/evidence/ETAPA_5_CENARIOS_PROFISSIONAIS_2026-08-19.md"
MAX_REPORT_BYTES = 2_000_000
USER_PATH_SEGMENT_RE = re.escape("Users")
HOST_PATH_RE = re.compile(
    rf"(?:[A-Za-z]:[\\/]{USER_PATH_SEGMENT_RE}[\\/]"
    rf"|/{USER_PATH_SEGMENT_RE}/|/home/|\\\\[^\\/]+[\\/])"
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path.name}")
    return value


def _assert_report(path: Path, *, expected: str) -> dict[str, Any]:
    report = _read_json(path)
    if report.get("status") != expected:
        raise ValueError(f"unexpected report status in {path.name}")
    if path.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError(f"report is unexpectedly large: {path.name}")
    return report


def _path_leaks(root: Path) -> list[str]:
    leaks: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {
            ".json",
            ".md",
            ".log",
            ".txt",
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if HOST_PATH_RE.search(text) or str(ROOT).replace("\\", "/") in text:
            leaks.append(path.relative_to(root).as_posix())
    return leaks


def _files_index(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): digest_path(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "artifact-index.json"
    }


def _write_stage6_report(
    output: Path,
    *,
    source: dict[str, Any],
    ui_report: dict[str, Any],
    scene_report: dict[str, Any],
    determinism: dict[str, Any],
    benchmark: dict[str, Any],
    leaks: list[str],
) -> dict[str, Any]:
    checks = {
        "source_tree_clean": source["worktree_clean"],
        "main_window_visual_audit": ui_report.get("status") == "PASS",
        "professional_editor_visual_audit": scene_report.get("status") == "PASS",
        "professional_editor_clean_capture": scene_report.get(
            "worktree_clean_at_capture_start", False
        ),
        "determinism": determinism.get("passed") is True,
        "performance_safety_ceilings": benchmark.get("passed") is True,
        "privacy": not leaks,
        "stage5_engine_contract_remains_explicit": Path(
            ROOT / STAGE5_EVIDENCE
        ).is_file(),
    }
    report = {
        "schema_version": 1,
        "stage": "6",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "source": source,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
        },
        "commands": [
            "python scripts/audit_stage6_scenario_quality.py --output <output>",
            "python -m pytest -q tests/test_stage6_scenario_quality.py",
            "python -m pytest -q",
            "python tools/check_coverage_policy.py <coverage.xml>",
        ],
        "checks": checks,
        "reports": {
            "main_window": "main-window/audited/visual-audit-report.json",
            "professional_editor": "professional-editor/stage4-capture-report.json",
        },
        "performance": benchmark,
        "determinism": determinism,
        "engine_boundary": {
            "stage5_evidence": STAGE5_EVIDENCE,
            "statement": (
                "Godot and Unity native adapter execution remains a separate "
                "real-engine contract from this editor-side audit."
            ),
        },
        "limitations": [
            "Benchmark uses a safety ceiling, not an FPS or historical claim.",
            "No runtime particles, streaming, or non-deterministic VFX are added.",
            (
                "Engine support is reported by separate real adapter evidence; "
                "missing native capability is not treated as an editor failure."
            ),
        ],
        "privacy_leaks": leaks,
    }
    write_json_lf(output / "stage6-report.json", report)
    return report


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(
            f"output must be a new directory; refusing to overwrite: {output.name}"
        )
    source = _source_state()

    with tempfile.TemporaryDirectory(prefix="neoeng-stage6-evidence-") as temporary:
        staging = Path(temporary)
        main_root = staging / "main-window"
        main_captures = main_root / "captures"
        main_captures.mkdir(parents=True)
        capture_main_window(main_captures)
        ui_report = run_audit(main_captures, main_root / "audited")

        scene_report = capture_scene(staging / "professional-editor")

        document = _fixture()
        determinism = _determinism_checks(document)
        benchmark = _benchmark(document)

        leaks_before_report = _path_leaks(staging)
        report = _write_stage6_report(
            staging,
            source=source,
            ui_report=ui_report,
            scene_report=scene_report,
            determinism=determinism,
            benchmark=benchmark,
            leaks=leaks_before_report,
        )
        index = {
            "schema_version": 1,
            "stage": "6",
            "files": _files_index(staging),
        }
        write_json_lf(staging / "artifact-index.json", index)
        # The index itself is intentionally excluded from its own digest set.
        if _path_leaks(staging):
            report["status"] = "FAIL"
            report["checks"]["privacy"] = False
            report["privacy_leaks"] = _path_leaks(staging)
            write_json_lf(staging / "stage6-report.json", report)
        shutil.copytree(staging, output)
        return report


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = run(args.output)
    except Exception as exc:
        print(f"STAGE6=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]},
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
