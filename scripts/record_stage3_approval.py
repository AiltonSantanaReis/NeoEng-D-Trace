"""Record human approval and exact CI evidence for Stage 3."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--reviewer", default="project owner")
    parser.add_argument("--ci-commit", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    commit = report.get("commit")
    if args.ci_commit != commit:
        raise SystemExit(f"CI commit diverges from report commit: {args.ci_commit} != {commit}")
    report["human_review"] = {"decision": "APROVADO", "reviewer": args.reviewer, "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "snapshot": f"STAGE_3_SNAPSHOT:{commit}"}
    report["ci_exact_commit"] = args.ci_commit
    report["decision"] = "FORMALLY_COMPLETE"
    report["consolidated_decision"] = "FORMALLY_COMPLETE"
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report_hash = sha256(args.report)
    manifest["stage3_report"]["sha256"] = report_hash
    manifest["report"]["sha256"] = report_hash
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": report["decision"], "snapshot": report["human_review"]["snapshot"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
