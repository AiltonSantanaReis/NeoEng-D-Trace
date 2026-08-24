"""Generate the chained, reproducible Stage 1 evidence snapshot."""

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

from scripts.audit_stage1_contract import run as run_contract_audit


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
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def inventory(repo_root: Path, commit: str) -> dict[str, Any]:
    paths = [
        Path("src/ui/theme_tokens.py"),
        Path("src/ui/theme_qss.py"),
        Path("tests/test_stage1_ui_theme.py"),
        Path("tests/test_stage1_contract_audit.py"),
        Path("scripts/audit_stage1_contract.py"),
        Path("scripts/capture_stage1_theme_states.py"),
        Path("scripts/generate_stage1_snapshot.py"),
        Path("docs/evidence/STAGE1_SCOPE_AND_RECONCILIATION.md"),
    ]
    files = []
    for relative in paths:
        path = repo_root / relative
        files.append({"path": relative.as_posix(), "sha256": sha256(path)})
    return {
        "schema": "neoeng.stage1-inventory",
        "schema_version": 1,
        "source_commit": commit,
        "files": files,
    }


def build_report(
    output: Path,
    repo_root: Path,
    commit: str,
    parent_snapshot_id: str,
    final_target: Path,
    audit: dict[str, Any],
    capture_manifest: Path,
    historical_copy: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for check_id, result in sorted(audit["checks"].items()):
        checks.append(
            {
                "id": f"stage1.contract.{check_id}",
                "classification": "EXPECTED_EVOLUTION",
                "justification": "Stage 1 current-target contract is the approved tokenized evolution and remains within FINAL_TARGET invariants.",
                "result": "PASS" if result else "FAIL",
            }
        )
    historical = audit["historical_result"]
    checks.append(
        {
            "id": "stage1.historical_comparator",
            "classification": "HISTORICAL_ONLY",
            "justification": (
                "The retained comparator reports the exact historical result separately; "
                "its 192 geometry deltas are not silently discarded and are not used as the "
                "current token-contract verdict."
            ),
            "result": "FAIL" if historical.get("status") == "FAIL" else "PASS",
        }
    )
    artifacts: list[dict[str, Any]] = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name in {"stage1-report.json", "stage1-manifest.json", "stage1-inventory.json"}:
            continue
        relative = path.relative_to(output).as_posix()
        artifacts.append(
            {
                "path": relative,
                "sha256": sha256(path),
                "purpose": "Stage 1 technical evidence.",
                "visual": path.suffix.lower() == ".png",
            }
        )
    report = {
        "schema": "neoeng.stage-audit-report",
        "schema_version": 1,
        "stage": 1,
        "stage_name": "Sistema visual e tokens de tema",
        "baseline_id": "FINAL_TARGET",
        "parent_snapshot_id": parent_snapshot_id,
        "commit": commit,
        "ci_exact_commit": None,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "dpi_percent": 100,
            "resolutions": ["1280x720", "1366x768", "1920x1080"],
        },
        "command": "python scripts/generate_stage1_snapshot.py --output artifacts/stage1-snapshot-20260824 --parent artifacts/stage0-snapshot-20260824/stage0-manifest.json",
        "decision": "REVIEW_REQUIRED" if audit["current_contract_result"] == "PASS" else "FAIL",
        "current_contract_result": audit["current_contract_result"],
        "historical_result": historical,
        "consolidated_decision": audit["consolidated_decision"],
        "checks": checks,
        "artifacts": artifacts,
        "final_target_manifest": {
            "path": "../../docs/evidence/final-target-baseline-v1.json",
            "sha256": sha256(final_target),
        },
        "historical_reference": {
            "path": historical_copy.relative_to(output).as_posix(),
            "sha256": sha256(historical_copy),
        },
        "human_review": None,
        "limitations": audit["limitations"],
    }
    return report


def generate(args: argparse.Namespace) -> None:
    repo_root = args.repo_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    commit = git("rev-parse", "HEAD")
    parent = json.loads(args.parent.read_text(encoding="utf-8"))
    parent_snapshot_id = str(parent["snapshot_id"])
    historical_copy = output / "historical-reference" / "stage1-baseline-report.json"
    historical_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.historical_report.resolve(), historical_copy)
    capture_manifest = output / "theme-state-captures" / "manifest.json"
    if not capture_manifest.is_file():
        raise FileNotFoundError(f"missing capture manifest: {capture_manifest}")
    audit = run_contract_audit(repo_root, historical_copy)
    write_json(output / "stage1-contract-audit.json", audit)
    inv = inventory(repo_root, commit)
    write_json(output / "stage1-inventory.json", inv)
    final_target = (repo_root / args.final_target).resolve()
    report = build_report(output, repo_root, commit, parent_snapshot_id, final_target, audit, capture_manifest, historical_copy)
    write_json(output / "stage1-report.json", report)
    report_hash = sha256(output / "stage1-report.json")
    inventory_hash = sha256(output / "stage1-inventory.json")
    artifacts = []
    for item in report["artifacts"]:
        artifacts.append(item)
    manifest = {
        "schema": "neoeng.stage1-snapshot",
        "schema_version": 1,
        "snapshot_id": f"STAGE_1_SNAPSHOT:{commit}",
        "parent_snapshot_id": parent_snapshot_id,
        "parent_manifest_sha256": sha256(args.parent.resolve()),
        "final_target_manifest_sha256": sha256(final_target),
        "stage1_report": {"path": "stage1-report.json", "sha256": report_hash},
        "report": {"path": "stage1-report.json", "sha256": report_hash},
        "inventory": {"path": "stage1-inventory.json", "sha256": inventory_hash},
        "artifacts": artifacts,
    }
    write_json(output / "stage1-manifest.json", manifest)
    print(json.dumps({"snapshot_id": manifest["snapshot_id"], "decision": report["decision"], "artifacts": len(artifacts)}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--historical-report", type=Path, required=True)
    parser.add_argument("--final-target", type=Path, default=Path("docs/evidence/final-target-baseline-v1.json"))
    args = parser.parse_args()
    generate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
