"""Generate the chained, reviewable Stage 5 evidence snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--full-suite", type=Path, required=True)
    parser.add_argument(
        "--final-target",
        type=Path,
        default=Path("docs/evidence/final-target-baseline-v1.json"),
    )
    args = parser.parse_args()
    root = Path.cwd().resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    audit = json.loads(args.audit.resolve().read_text(encoding="utf-8"))
    parent = json.loads(args.parent.resolve().read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise SystemExit("Stage 5 audit is not PASS")
    if audit.get("source_state", {}).get("commit") != commit:
        raise SystemExit("Stage 5 audit is not bound to current HEAD")
    if not str(parent.get("snapshot_id", "")).startswith("STAGE_4_SNAPSHOT:"):
        raise SystemExit("parent is not a Stage 4 snapshot")

    suite_root = ET.parse(args.full_suite.resolve()).getroot()
    suite_node = suite_root.find("testsuite") if suite_root.tag == "testsuites" else suite_root
    if suite_node is None:
        raise SystemExit("JUnit has no testsuite")
    suite = {
        "tests": int(suite_node.attrib.get("tests", 0)),
        "failures": int(suite_node.attrib.get("failures", 0)),
        "errors": int(suite_node.attrib.get("errors", 0)),
        "skipped": int(suite_node.attrib.get("skipped", 0)),
        "time_seconds": float(suite_node.attrib.get("time", 0.0)),
        "status": "PASS"
        if all(int(suite_node.attrib.get(key, 0)) == 0 for key in ("failures", "errors"))
        else "FAIL",
        "junit": {
            "path": args.full_suite.resolve().relative_to(output).as_posix(),
            "sha256": sha256(args.full_suite.resolve()),
        },
    }
    inventory_path = output / "stage5-inventory.json"
    inventory = {
        "schema": "neoeng.stage5-inventory",
        "schema_version": 1,
        "source_commit": commit,
        "files": [
            {
                "path": path.as_posix(),
                "sha256": sha256(root / path),
            }
            for path in (
                Path("src/ui/canvas_view.py"),
                Path("src/ui/viewport_chrome.py"),
                Path("src/ui/viewport_status.py"),
                Path("src/ui/mask_viewer.py"),
                Path("tests/test_stage5_viewport_hud.py"),
                Path("tests/test_stage5_viewport_hud_contract.py"),
                Path("tests/test_mask_viewer.py"),
                Path("tests/test_mask_viewer_compatibility.py"),
                Path("scripts/audit_stage5_contract.py"),
                Path("scripts/generate_stage5_snapshot.py"),
                 Path("scripts/record_stage5_approval.py"),
                 Path("docs/evidence/STAGE5_SCOPE_AND_RECONCILIATION.md"),
            )
        ],
    }
    write_json(inventory_path, inventory)
    excluded = {"stage5-report.json", "stage5-manifest.json", "stage5-inventory.json"}
    artifacts = [
        {
            "path": path.relative_to(output).as_posix(),
            "sha256": sha256(path),
            "purpose": "Etapa 5 technical evidence.",
            "visual": path.suffix.lower() == ".png",
        }
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name not in excluded
    ]
    report = {
        "schema": "neoeng.stage-audit-report",
        "schema_version": 1,
        "stage": 5,
        "stage_name": "Viewport e HUD",
        "baseline_id": "FINAL_TARGET",
        "parent_snapshot_id": parent["snapshot_id"],
        "commit": commit,
        "command": "python scripts/generate_stage5_snapshot.py --output artifacts/stage5-snapshot-20260824 --parent artifacts/stage4-snapshot-20260824/stage4-manifest.json --audit artifacts/stage5-snapshot-20260824/stage5-contract-audit.json --full-suite artifacts/stage5-snapshot-20260824/full-suite-junit.xml",
        "ci_exact_commit": None,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "resolutions": ["1280x720", "1366x768", "1920x1080"],
        },
        "audit": {
            "path": "stage5-contract-audit.json",
            "sha256": sha256(args.audit.resolve()),
        },
        "full_suite": suite,
        "checks": [
            {
                "id": "stage5.viewport_hud",
                "classification": "EXPECTED_EVOLUTION",
                "justification": "Real Qt interaction and geometry checks cover the required Viewport/HUD states across three logical resolutions.",
                "result": audit["tracks"]["viewport_hud"]["status"],
            },
            {
                "id": "stage5.mask_viewer",
                "classification": "EXPECTED_EVOLUTION",
                "justification": "Real Mask Viewer modes, input paths, invalid state and clipping checks cover the Stage 5 contract.",
                "result": audit["tracks"]["mask_viewer"]["status"],
            },
            {
                "id": "stage5.visual_audit",
                "classification": "EXPECTED_EVOLUTION",
                "justification": "Independent visual audit consumed the hashed captures and reported no findings.",
                "result": audit["visual_audit"]["status"],
            },
            {
                "id": "stage5.full_suite",
                "classification": "EXPECTED_EVOLUTION",
                "justification": "The full repository suite protects existing behavior while the Stage 5 UI changes are introduced.",
                "result": suite["status"],
            },
        ],
        "artifacts": artifacts,
        "current_contract_result": "PASS",
        "decision": "REVIEW_REQUIRED",
        "human_review": None,
        "limitations": audit.get("limitations", []),
    }
    report_path = output / "stage5-report.json"
    write_json(report_path, report)
    manifest = {
        "schema": "neoeng.stage5-snapshot",
        "schema_version": 1,
        "snapshot_id": f"STAGE_5_SNAPSHOT:{commit}",
        "parent_snapshot_id": parent["snapshot_id"],
        "parent_manifest_sha256": sha256(args.parent.resolve()),
        "final_target_manifest_sha256": sha256((root / args.final_target).resolve()),
        "stage5_report": {
            "path": "stage5-report.json",
            "sha256": sha256(report_path),
        },
        "report": {
            "path": "stage5-report.json",
            "sha256": sha256(report_path),
        },
        "inventory": {
            "path": "stage5-inventory.json",
            "sha256": sha256(inventory_path),
        },
        "artifacts": artifacts,
    }
    write_json(output / "stage5-manifest.json", manifest)
    print(json.dumps({
        "snapshot_id": manifest["snapshot_id"],
        "decision": report["decision"],
        "artifacts": len(artifacts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
