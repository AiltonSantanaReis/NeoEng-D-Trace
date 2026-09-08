"""Validate the single source of truth for project continuity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "docs" / "CONTROLE_CONTINUIDADE_ATUAL.json"
ALLOWED_STATUSES = {
    "BLOCKED",
    "IN_PROGRESS",
    "NOT_STARTED",
    "PASS_AUTOMATED_CAPTURE_ONLY",
    "PASS_LOCAL",
    "PASS_SANDBOX_DIAGNOSTIC_ONLY",
    "PENDING_PROVENANCE",
    "PLANNED",
    "SKIP_PRIVILEGE_LIMITATION",
}


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"missing required key: {key}")
    return data[key]


def validate_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if _require(data, "schema_version") != 1:
        raise ValueError("unsupported schema_version")

    authority = _require(data, "authority")
    if not authority["master_plan_commit"]:
        raise ValueError("master_plan_commit must be explicit")

    active = _require(data, "active_work")
    if active["stage"] != "E00":
        raise ValueError("continuity registry must remain anchored at E00")
    if active["implementation_allowed"]:
        raise ValueError("E00 preparatory registry cannot allow implementation")

    checkout = _require(data, "checkout_under_audit")
    if not checkout["branch"] or not checkout["head"]:
        raise ValueError("checkout branch and head must be explicit")

    gates = _require(data, "gates")
    visual = gates["visual"]
    if visual["native_human_status"] == "PENDING_EVIDENCE" and not visual.get(
        "human_review_required_before_close", False
    ):
        raise ValueError("deferred human review must remain required before close")
    symlink = gates["symlink"]
    if (
        symlink["sandbox_status"] == "PASS_SANDBOX_DIAGNOSTIC_ONLY"
        and symlink["sandbox_skips"]
    ):
        raise ValueError("sandbox PASS cannot contain skips")
    if (
        symlink["local_suite_status"] == "SKIP_PRIVILEGE_LIMITATION"
        and not symlink["local_suite_skips"]
    ):
        raise ValueError("local skip status requires a non-zero skip count")

    provenance = gates["build_provenance"]
    if provenance["status"] == "PENDING_PROVENANCE" and provenance["source_commit"]:
        raise ValueError("pending provenance cannot claim source_commit")

    stages = _require(data, "stage_status")
    if stages.get("E00") != "IN_PROGRESS" or stages.get("E01") != "NOT_STARTED":
        raise ValueError("stage progression is inconsistent with E00 gate")
    invalid = [
        (stage, status)
        for stage, status in stages.items()
        if status not in ALLOWED_STATUSES
    ]
    if invalid:
        raise ValueError(f"unknown stage status: {invalid}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    validate_registry(args.path)
    print(f"CONTINUITY_REGISTRY=PASS path={args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
