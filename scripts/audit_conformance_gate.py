"""CLI for the canonical NeoEng multiaxis conformance gate."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.conformance.gate import GateInput, run_aggregate_gate

_PRODUCER = "scripts/audit_conformance_gate.py"


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} must contain a JSON object")
    return dict(raw)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate atomic G/V/B auditor evidence into one NeoEng "
            "conformance gate."
        )
    )
    parser.add_argument("--source-baseline", required=True)
    parser.add_argument("--geometry-report", type=Path, required=True)
    parser.add_argument("--visual-report", type=Path, required=True)
    parser.add_argument("--behavior-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        geometry = _load_json_object(args.geometry_report, "geometry report")
        visual = _load_json_object(args.visual_report, "visual report")
        behavior = _load_json_object(args.behavior_report, "behavior report")
        gate = run_aggregate_gate(
            source_baseline=args.source_baseline,
            geometry=GateInput(geometry, args.geometry_report.as_posix()),
            visual=GateInput(visual, args.visual_report.as_posix()),
            behavior=GateInput(behavior, args.behavior_report.as_posix()),
        )
        document = gate.write_evidence(args.output, producer=_PRODUCER)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "EXECUTION_ERROR",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": document["status"],
                "blocking": document["blocking"],
                "axes": {
                    axis: document["axes"][axis]["status"]
                    for axis in ("G", "V", "B")
                },
                "output": args.output.as_posix(),
            },
            sort_keys=True,
        )
    )
    return gate.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
