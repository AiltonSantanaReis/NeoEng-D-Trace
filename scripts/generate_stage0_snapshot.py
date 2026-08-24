"""Generate the root snapshot for the chained Stage 0 baseline.

The script inventories the exact checkout and copies only pre-existing visual
evidence into a new, isolated Stage 0 folder. It never changes production
files. Missing evidence is recorded as REVIEW_REQUIRED rather than inferred.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESOLUTIONS = ["1280x720", "1366x768", "1920x1080"]
DPI = [100, 125, 150, 200]
REQUIRED_STATES = [
    "no_project",
    "project_open",
    "panels",
    "mask_viewer",
    "xray",
    "gizmo",
    "validation",
    "scenario_editor",
]


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/stage0-snapshot-20260824"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (root / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    evidence_dir = output / "visual-evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    target_manifest = root / "docs/evidence/final-target-baseline-v1.json"
    target_sha = digest(target_manifest)
    commit = run_git(root, "rev-parse", "HEAD")
    tracked_status = run_git(root, "status", "--porcelain", "--untracked-files=no")
    tracked_files = run_git(root, "ls-files").splitlines()

    source_evidence = root / "artifacts/stage0-9-final-audit-20260824/source-ui-capture/visual-audit"
    copied: list[dict[str, Any]] = []
    if source_evidence.is_dir():
        for source in sorted(source_evidence.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(source_evidence)
            destination = evidence_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append({
                "path": str(destination.relative_to(output)).replace("\\", "/"),
                "source": str(source.relative_to(root)).replace("\\", "/"),
                "sha256": digest(destination),
                "suffix": destination.suffix.lower(),
            })

    names = " ".join(item["path"].lower() for item in copied)
    evidence_checks = []
    for state in REQUIRED_STATES:
        present = state in names
        evidence_checks.append({
            "id": f"stage0.visual.{state}",
            "result": "PASS" if present else "REVIEW_REQUIRED",
            "classification": "HISTORICAL_ONLY" if present else "UNCLASSIFIED_CHANGE",
            "justification": (
                "A matching isolated capture was found and hash-recorded."
                if present else
                "No isolated capture with an unambiguous state identifier was found; new capture required."
            ),
        })

    inventory = {
        "schema": "neoeng.stage0-inventory",
        "schema_version": 1,
        "commit": commit,
        "tracked_file_count": len(tracked_files),
        "tracked_files_sha256": hashlib.sha256("\n".join(tracked_files).encode("utf-8")).hexdigest(),
        "top_level_tracked_files": sorted({file.split("/", 1)[0] for file in tracked_files}),
        "required_visual_states": REQUIRED_STATES,
        "resolutions": RESOLUTIONS,
        "dpi_percent": DPI,
    }
    inventory_path = output / "stage0-inventory.json"
    write_json(inventory_path, inventory)

    report = {
        "schema": "neoeng.stage-audit-report",
        "schema_version": 1,
        "baseline_id": "FINAL_TARGET",
        "stage": 0,
        "parent_snapshot_id": None,
        "final_target_manifest": {
            "path": "../../docs/evidence/final-target-baseline-v1.json",
            "sha256": target_sha,
        },
        "commit": commit,
        "environment": {
            "platform": "windows",
            "resolution": "1920x1080",
            "dpi_percent": 100,
            "python": run_git(root, "describe", "--always", "--dirty"),
        },
        "command": "python scripts/generate_stage0_snapshot.py --output artifacts/stage0-snapshot-20260824",
        "decision": "AUTOMATED_PASS" if not tracked_status and all(check["result"] == "PASS" for check in evidence_checks) else "REVIEW_REQUIRED",
        "historical_result": "NOT_APPLICABLE",
        "current_contract_result": "PASS" if not tracked_status else "REVIEW_REQUIRED",
        "consolidated_decision": "PASS" if not tracked_status and all(check["result"] == "PASS" for check in evidence_checks) else "REVIEW_REQUIRED",
        "checks": [
            {
                "id": "stage0.tracked_tree_clean",
                "result": "PASS" if not tracked_status else "REVIEW_REQUIRED",
                "classification": "HISTORICAL_ONLY" if not tracked_status else "UNCLASSIFIED_CHANGE",
                "justification": "Tracked product tree is clean." if not tracked_status else tracked_status,
            },
            *evidence_checks,
        ],
        "artifacts": [
            {"path": "stage0-inventory.json", "sha256": digest(inventory_path), "visual": False, "purpose": "Complete root inventory."},
            *[{"path": item["path"], "sha256": item["sha256"], "visual": item["suffix"] == ".png", "purpose": "Existing visual evidence copied without modification."} for item in copied],
        ],
        "limitations": [
            "This root snapshot does not infer missing visual states from a generic screenshot.",
            "The final decision remains REVIEW_REQUIRED until every required state has an unambiguous capture.",
        ],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_path = output / "stage0-report.json"
    write_json(report_path, report)
    write_json(output / "stage0-manifest.json", {
        "schema": "neoeng.stage0-snapshot",
        "snapshot_id": f"STAGE_0_SNAPSHOT:{commit}",
        "parent_snapshot_id": None,
        "final_target_manifest_sha256": target_sha,
        "stage0_report": {"path": "stage0-report.json", "sha256": digest(report_path)},
        "inventory": {"path": "stage0-inventory.json", "sha256": digest(inventory_path)},
        "artifacts": report["artifacts"],
    })
    print(json.dumps({"output": str(output), "decision": report["decision"], "copied_artifacts": len(copied), "commit": commit}, ensure_ascii=False, indent=2))
    return 0 if report["decision"] == "AUTOMATED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
