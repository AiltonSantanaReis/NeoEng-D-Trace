"""Record human approval and exact CI evidence for a Stage 2 report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--reviewer", default="project owner")
    parser.add_argument("--ci-commit", required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    commit = report.get("commit") or git_commit()
    if args.ci_commit != commit:
        raise SystemExit(f"CI commit diverges from report commit: {args.ci_commit} != {commit}")
    report["human_review"] = {
        "decision": "APROVADO",
        "reviewer": args.reviewer,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": f"STAGE_2_SNAPSHOT:{commit}",
    }
    report["ci_exact_commit"] = args.ci_commit
    report["decision"] = "FORMALLY_COMPLETE"
    report["consolidated_decision"] = "FORMALLY_COMPLETE"
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        report_hash = sha256(args.report)
        for key in ("stage2_report", "report"):
            if key in manifest:
                manifest[key]["sha256"] = report_hash
        args.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps({"decision": report["decision"], "snapshot": report["human_review"]["snapshot"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
