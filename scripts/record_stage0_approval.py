"""Record human approval and, optionally, the exact CI commit in Stage 0 evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--reviewer", default="project owner")
    parser.add_argument("--ci-commit")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    report["human_review"] = {
        "decision": "APROVADO",
        "reviewer": args.reviewer,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": f"STAGE_0_SNAPSHOT:{report.get('commit')}",
    }
    if args.ci_commit:
        report["ci_exact_commit"] = args.ci_commit
    if report.get("human_review", {}).get("decision") == "APROVADO" and report.get("ci_exact_commit"):
        report["decision"] = "FORMALLY_COMPLETE"
        report["consolidated_decision"] = "FORMALLY_COMPLETE"
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "ci_exact_commit": report.get("ci_exact_commit")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
