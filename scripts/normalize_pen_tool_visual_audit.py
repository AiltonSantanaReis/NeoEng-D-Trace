"""Complete the manifest for a Pen tool visual-audit package.

The capture producer owns the real Qt flow.  This companion command makes the
package self-contained by recording every generated input/output file and the
final digest of ``report.json``; the index itself is intentionally excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _record(path: Path, relative: str) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": relative,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def run(output: Path, source_commit: str, source_branch: str) -> dict[str, object]:
    report_path = output / "report.json"
    index_path = output / "artifact-index.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source = report.get("source", {})
    if source.get("commit") != source_commit or source.get("branch") != source_branch:
        raise ValueError("report source identity does not match requested identity")

    inputs = [
        _record(output / "positive-work" / "fixture.png", "positive-work/fixture.png"),
        _record(output / "invalid-work" / "fixture.png", "invalid-work/fixture.png"),
        _record(
            output / "double-click-work" / "fixture.png",
            "double-click-work/fixture.png",
        ),
    ]
    report["inputs"] = inputs
    report["manifest_normalization"] = {
        "producer": "scripts/audit_pen_tool_visual.py",
        "normalizer": "scripts/normalize_pen_tool_visual_audit.py",
        "status": "PASS",
    }
    _write_json(report_path, report)

    files = [
        _record(path, path.relative_to(output).as_posix())
        for path in sorted(output.rglob("*"))
        if path.is_file() and path != index_path
    ]
    index: dict[str, object] = {
        "schema": "neoeng.evidence-artifact-index",
        "package": output.name,
        "status": report["status"],
        "audited_commit": source_commit,
        "audited_branch": source_branch,
        "files": files,
        "index_excludes_itself": True,
    }
    _write_json(index_path, index)
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-branch", required=True)
    args = parser.parse_args()
    result = run(args.output.resolve(), args.source_commit, args.source_branch)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
