"""Record an explicit human review for a reproducible Pen audit package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_HASHES = {
    "pen-close-preview.png": (
        29020,
        "37279f8377e6b9413b72c86352ea505683c95da8a190ccb3c2b454e54b0b62f0",
    ),
    "pen-closed-persisted.png": (
        33373,
        "edb88d53511d983f434c4c2cec83a229197160f5e90d061570c5cd3d7bcfe9cf",
    ),
    "pen-invalid-close.png": (
        28526,
        "f99a5a1923783c6aa3c14728409053ba036ec1eab04e73ac938c88a211f87f62",
    ),
    "pen-after-undo.png": (
        23683,
        "cb71c1071a1a9f56e9090ebc10c93a6126d3d1f8cc5156c25518680d38504ebc",
    ),
    "pen-after-redo.png": (
        30470,
        "c8bd261434ef8781406ff742753f860dc5aa11dc0516aa2eab69ae2739a999ce",
    ),
    "pen-double-click-open.png": (
        31965,
        "4be1941dcad4fc9caabf2716b3cb5a1d3474307fb892692fe4e6629baeb32ead",
    ),
}


def _write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _digest(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def run(
    output: Path,
    source_commit: str,
    source_branch: str,
    reviewer: str,
    reviewed_on: str,
    confirmation: str,
) -> dict[str, object]:
    report_path = output / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source = report.get("source", {})
    if source.get("commit") != source_commit or source.get("branch") != source_branch:
        raise ValueError("report source identity does not match requested identity")

    reviewed_artifacts = []
    for name, expected in CAPTURE_HASHES.items():
        path = output / name
        actual = _digest(path)
        if actual != expected:
            raise ValueError(f"capture digest mismatch for {name}: {actual!r}")
        reviewed_artifacts.append(
            {"bytes": actual[0], "path": name, "sha256": actual[1]}
        )

    review = {
        "schema": "neoeng.pen-tool-human-visual-review",
        "status": "PASS",
        "reviewed_on": reviewed_on,
        "reviewer": reviewer,
        "source": {"branch": source_branch, "commit": source_commit},
        "confirmation": confirmation,
        "artifacts": reviewed_artifacts,
        "scope": (
            "Human visual inspection of the six reproducible Qt capture states; "
            "this does not approve merge, release, or the global correction plan."
        ),
    }
    _write_json(output / "human-review.json", review)

    report["human_visual_review"] = {
        "status": "PASS",
        "reviewed_on": reviewed_on,
        "reviewer": reviewer,
        "record": "human-review.json",
        "source_commit": source_commit,
    }
    report["status"] = "PASS_AUTOMATED_AND_HUMAN_VISUAL"
    report["limitations"] = [
        "This package covers the Pen visual-flow audit only.",
        "Repository-wide gates and CI remain separate acceptance criteria.",
    ]
    _write_json(report_path, report)
    return review


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-branch", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reviewed-on", required=True)
    parser.add_argument("--confirmation", required=True)
    args = parser.parse_args()
    result = run(
        args.output.resolve(),
        args.source_commit,
        args.source_branch,
        args.reviewer,
        args.reviewed_on,
        args.confirmation,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
