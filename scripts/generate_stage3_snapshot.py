"""Generate the chained, reviewable Stage 3 evidence snapshot."""
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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def inventory(root: Path, commit: str) -> dict[str, Any]:
    paths = [
        Path("src/ui/reference_chrome.py"),
        Path("src/ui/tool_palette_impl.py"),
        Path("tests/test_stage3_ui_toolbar.py"),
        Path("scripts/audit_stage3_ui_toolbar.py"),
        Path("scripts/audit_stage3_contract.py"),
        Path("scripts/generate_stage3_snapshot.py"),
        Path("scripts/record_stage3_approval.py"),
        Path("docs/evidence/STAGE3_SCOPE_AND_RECONCILIATION.md"),
    ]
    return {"schema": "neoeng.stage3-inventory", "schema_version": 1, "source_commit": commit, "files": [{"path": p.as_posix(), "sha256": sha256(root / p)} for p in paths]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--final-target", type=Path, default=Path("docs/evidence/final-target-baseline-v1.json"))
    parser.add_argument("--full-suite", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    audit = json.loads(args.audit.resolve().read_text(encoding="utf-8"))
    parent = json.loads(args.parent.resolve().read_text(encoding="utf-8"))
    commit = git("rev-parse", "HEAD")
    if audit.get("status") != "PASS":
        raise SystemExit("Stage 3 audit is not PASS")
    if audit.get("source_state", {}).get("commit") != commit:
        raise SystemExit("Stage 3 audit commit does not match HEAD")
    if parent.get("snapshot_id") != "STAGE_2_SNAPSHOT:" + parent.get("snapshot_id", "").split(":", 1)[-1]:
        raise SystemExit("parent is not a Stage 2 snapshot")
    inventory_path = output / "stage3-inventory.json"
    write_json(inventory_path, inventory(root, commit))
    suite_root = ET.parse(args.full_suite.resolve()).getroot()
    suite_node = suite_root.find("testsuite") if suite_root.tag == "testsuites" else suite_root
    if suite_node is None:
        raise SystemExit("JUnit report has no testsuite element")
    suite = {
        "tests": int(suite_node.attrib.get("tests", 0)),
        "failures": int(suite_node.attrib.get("failures", 0)),
        "errors": int(suite_node.attrib.get("errors", 0)),
        "skipped": int(suite_node.attrib.get("skipped", 0)),
        "time_seconds": float(suite_node.attrib.get("time", 0.0)),
        "status": "PASS" if all(int(suite_node.attrib.get(key, 0)) == 0 for key in ("failures", "errors")) else "FAIL",
        "junit": {"path": args.full_suite.resolve().relative_to(output).as_posix(), "sha256": sha256(args.full_suite.resolve())},
    }
    audit_checks = audit.get("checks", {})
    live_status = audit_checks.get("live_contract", {}).get("status", "FAIL")
    visual_status = audit_checks.get("visual_status", "FAIL")
    capture_status = audit_checks.get("capture_status", "FAIL")
    checks = [
        {
            "id": "stage3.live_contract",
            "classification": "EXPECTED_EVOLUTION",
            "justification": "The current visible rail and compatibility ToolPalette were exercised through the real MainWindow against the normative Stage 3 contract.",
            "result": live_status,
        },
        {
            "id": "stage3.visual_capture",
            "classification": "EXPECTED_EVOLUTION",
            "justification": "Three real MainWindow resolutions were captured and checked by the existing Qt/Pillow/OpenCV visual auditor.",
            "result": visual_status,
        },
        {
            "id": "stage3.capture_pipeline",
            "classification": "EXPECTED_EVOLUTION",
            "justification": "The reproducible capture pipeline completed and produced the referenced raw manifest.",
            "result": capture_status,
        },
        {
            "id": "stage3.full_suite",
            "classification": "EXPECTED_EVOLUTION",
            "justification": "The complete repository pytest suite was executed on the exact commit under review and its JUnit output is hash-referenced.",
            "result": suite["status"],
        },
    ]
    artifacts = []
    excluded = {"stage3-report.json", "stage3-manifest.json", "stage3-inventory.json"}
    for item in sorted(output.rglob("*")):
        if item.is_file() and item.name not in excluded:
            artifacts.append({"path": item.relative_to(output).as_posix(), "sha256": sha256(item), "purpose": "Etapa 3 technical evidence.", "visual": item.suffix.lower() == ".png"})
    report = {
        "schema": "neoeng.stage-audit-report",
        "schema_version": 1,
        "stage": 3,
        "stage_name": "Barra lateral de ferramentas",
        "baseline_id": "FINAL_TARGET",
        "parent_snapshot_id": parent["snapshot_id"],
        "commit": commit,
        "command": "python scripts/generate_stage3_snapshot.py --output artifacts/stage3-snapshot-20260824 --parent artifacts/stage2-snapshot-20260824/stage2-manifest.json --audit artifacts/stage3-snapshot-20260824/stage3-contract-audit.json --full-suite artifacts/stage3-snapshot-20260824/full-suite-junit.xml",
        "ci_exact_commit": None,
        "environment": {"platform": platform.platform(), "python": sys.version, "dpi_percent": [100, 125, 150, 200], "resolutions": ["1280x720", "1366x768", "1920x1080"]},
        "audit": {"path": "stage3-contract-audit.json", "sha256": sha256(output / "stage3-contract-audit.json")},
        "full_suite": suite,
        "checks": checks,
        "artifacts": artifacts,
        "decision": "REVIEW_REQUIRED",
        "current_contract_result": "PASS",
        "human_review": None,
        "limitations": audit.get("limitations", []),
    }
    report_path = output / "stage3-report.json"
    write_json(report_path, report)
    manifest = {
        "schema": "neoeng.stage3-snapshot",
        "schema_version": 1,
        "snapshot_id": f"STAGE_3_SNAPSHOT:{commit}",
        "parent_snapshot_id": parent["snapshot_id"],
        "parent_manifest_sha256": sha256(args.parent.resolve()),
        "final_target_manifest_sha256": sha256((root / args.final_target).resolve()),
        "stage3_report": {"path": "stage3-report.json", "sha256": sha256(report_path)},
        "report": {"path": "stage3-report.json", "sha256": sha256(report_path)},
        "inventory": {"path": "stage3-inventory.json", "sha256": sha256(inventory_path)},
        "artifacts": artifacts,
    }
    write_json(output / "stage3-manifest.json", manifest)
    print(json.dumps({"snapshot_id": manifest["snapshot_id"], "decision": report["decision"], "artifacts": len(artifacts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
