"""Generate the chained, reproducible Stage 2 evidence snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def inventory(repo_root: Path, commit: str) -> dict[str, Any]:
    paths = [
        Path("src/ui/icon_library.py"),
        Path("src/ui/top_toolbar.py"),
        Path("tests/test_stage2_ui_icons.py"),
        Path("tests/test_stage2_icon_dpi_matrix.py"),
        Path("tests/test_stage2_contract_audit.py"),
        Path("scripts/audit_stage2_contract.py"),
        Path("scripts/audit_stage2_icon_dpi_matrix.py"),
        Path("scripts/generate_stage2_snapshot.py"),
        Path("docs/evidence/STAGE2_SCOPE_AND_RECONCILIATION.md"),
    ]
    return {
        "schema": "neoeng.stage2-inventory",
        "schema_version": 1,
        "source_commit": commit,
        "files": [{"path": path.as_posix(), "sha256": sha256(repo_root / path)} for path in paths],
    }


def generate(args: argparse.Namespace) -> None:
    repo_root = args.repo_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    parent = json.loads(args.parent.read_text(encoding="utf-8"))
    parent_snapshot_id = str(parent["snapshot_id"])
    historical_copy = output / "historical-reference" / "stage2-dpi-matrix-report.json"
    historical_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.historical_report.resolve(), historical_copy)
    contract_path = output / "stage2-contract-audit.json"
    dpi_root = args.dpi_root.resolve()
    if not contract_path.is_file() or not (dpi_root / "stage2-dpi-matrix-report.json").is_file():
        raise FileNotFoundError("Stage 2 contract or DPI report is missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    dpi_report_path = dpi_root / "stage2-dpi-matrix-report.json"
    dpi_report = json.loads(dpi_report_path.read_text(encoding="utf-8"))
    write_json(output / "stage2-inventory.json", inventory(repo_root, commit))
    checks = [
        {
            "id": f"stage2.contract.{key}",
            "classification": "EXPECTED_EVOLUTION",
            "justification": "Stage 2 current-target icon contract is the approved vector-library evolution and remains within FINAL_TARGET invariants.",
            "result": "PASS" if value else "FAIL",
        }
        for key, value in sorted(contract["checks"].items())
    ]
    checks.append(
        {
            "id": "stage2.dpi_matrix",
            "classification": "EXPECTED_EVOLUTION",
            "justification": "The four-scale Qt matrix validates the current icon library and production MainWindow independently of the historical report.",
            "result": "PASS" if dpi_report.get("status") == "PASS" else "FAIL",
        }
    )
    historical = contract["historical_result"]
    checks.append(
        {
            "id": "stage2.historical_reference",
            "classification": "HISTORICAL_ONLY",
            "justification": "The earlier DPI report is retained diagnostically and is not silently substituted for the current-target contract.",
            "result": "PASS" if historical.get("status") == "PASS" else "FAIL",
        }
    )
    artifacts: list[dict[str, Any]] = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name in {"stage2-report.json", "stage2-manifest.json", "stage2-inventory.json"}:
            continue
        artifacts.append(
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": sha256(path),
                "purpose": "Stage 2 technical evidence.",
                "visual": path.suffix.lower() == ".png",
            }
        )
    final_target = (repo_root / args.final_target).resolve()
    report = {
        "schema": "neoeng.stage-audit-report",
        "schema_version": 1,
        "stage": 2,
        "stage_name": "Biblioteca de ícones própria",
        "baseline_id": "FINAL_TARGET",
        "parent_snapshot_id": parent_snapshot_id,
        "commit": commit,
        "ci_exact_commit": None,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "dpi_percent": [100, 125, 150, 200],
            "resolutions": ["1280x720", "1366x768", "1920x1080"],
        },
        "command": "python scripts/generate_stage2_snapshot.py --output artifacts/stage2-snapshot-20260824 --parent artifacts/stage1-snapshot-20260824/stage1-manifest.json",
        "decision": "REVIEW_REQUIRED" if contract["current_contract_result"] == "PASS" and dpi_report.get("status") == "PASS" else "FAIL",
        "current_contract_result": contract["current_contract_result"],
        "historical_result": historical,
        "consolidated_decision": contract["consolidated_decision"],
        "checks": checks,
        "artifacts": artifacts,
        "final_target_manifest": {"path": "../../docs/evidence/final-target-baseline-v1.json", "sha256": sha256(final_target)},
        "historical_reference": {"path": historical_copy.relative_to(output).as_posix(), "sha256": sha256(historical_copy)},
        "human_review": None,
        "limitations": contract["limitations"],
    }
    write_json(output / "stage2-report.json", report)
    report_hash = sha256(output / "stage2-report.json")
    inventory_hash = sha256(output / "stage2-inventory.json")
    manifest = {
        "schema": "neoeng.stage2-snapshot",
        "schema_version": 1,
        "snapshot_id": f"STAGE_2_SNAPSHOT:{commit}",
        "parent_snapshot_id": parent_snapshot_id,
        "parent_manifest_sha256": sha256(args.parent.resolve()),
        "final_target_manifest_sha256": sha256(final_target),
        "stage2_report": {"path": "stage2-report.json", "sha256": report_hash},
        "report": {"path": "stage2-report.json", "sha256": report_hash},
        "inventory": {"path": "stage2-inventory.json", "sha256": inventory_hash},
        "artifacts": artifacts,
    }
    write_json(output / "stage2-manifest.json", manifest)
    print(json.dumps({"snapshot_id": manifest["snapshot_id"], "decision": report["decision"], "artifacts": len(artifacts)}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--historical-report", type=Path, required=True)
    parser.add_argument("--dpi-root", type=Path, required=True)
    parser.add_argument("--final-target", type=Path, default=Path("docs/evidence/final-target-baseline-v1.json"))
    args = parser.parse_args()
    generate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
