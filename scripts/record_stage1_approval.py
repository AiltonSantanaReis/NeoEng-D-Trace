"""Record human approval and exact CI evidence for a Stage 1 report."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--reviewer", default="project owner")
    parser.add_argument("--ci-commit", required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    commit = report.get("commit") or git_commit()
    if args.ci_commit != commit:
        raise SystemExit(f"CI commit diverges from report commit: {args.ci_commit} != {commit}")
    report["human_review"] = {
        "decision": "APROVADO",
        "reviewer": args.reviewer,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": f"STAGE_1_SNAPSHOT:{commit}",
    }
    report["ci_exact_commit"] = args.ci_commit
    report["decision"] = "FORMALLY_COMPLETE"
    report["consolidated_decision"] = "FORMALLY_COMPLETE"
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"decision": report["decision"], "snapshot": report["human_review"]["snapshot"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
