"""Official E09-A audit for controlled image import and contour detection."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from src.core.vectorization import (
    VectorizationError,
    VectorizationRequest,
    vectorize_image_file,
)


def _source_tree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _write_image(path: Path, *, hole: bool = False, islands: bool = False) -> None:
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    if hole:
        image[40:56, 50:78, 3] = 0
    if islands:
        image[4:10, 4:10, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    if not ok:
        raise RuntimeError(f"cannot encode audit fixture {path}")
    path.write_bytes(encoded.tobytes())


def _expect_error(path: Path, code: str) -> dict[str, str]:
    try:
        vectorize_image_file(path)
    except VectorizationError as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc.code}") from exc
        return {"code": exc.code, "message": str(exc)}
    raise AssertionError(f"expected vectorization error {code}")


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    source = output / "e09-a-solid-subject.png"
    _write_image(source)
    request = VectorizationRequest(
        channel="alpha", threshold=1, approximation_epsilon=1.0, minimum_area=16.0
    )
    first = vectorize_image_file(source, request)
    second = vectorize_image_file(source, request)
    expected_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if first != second or first.source_sha256 != expected_hash:
        raise AssertionError("E09-A result is not deterministic or hash-bound")
    if first.polygon != ((24, 18), (103, 18), (103, 77), (24, 77)):
        raise AssertionError(f"unexpected detected polygon: {first.polygon}")

    mutated = output / "e09-a-mutated.png"
    mutated.write_bytes(source.read_bytes() + b"mutation")
    mutated_result = vectorize_image_file(mutated, request)
    if mutated_result.source_sha256 == first.source_sha256:
        raise AssertionError("changed source retained the previous provenance hash")

    hole = output / "e09-a-hole.png"
    islands = output / "e09-a-islands.png"
    unreadable = output / "e09-a-unreadable.png"
    _write_image(hole, hole=True)
    _write_image(islands, islands=True)
    unreadable.write_bytes(b"not-an-image")
    negatives = {
        "holes": _expect_error(hole, "unsupported_holes"),
        "islands": _expect_error(islands, "unsupported_islands"),
        "unreadable": _expect_error(unreadable, "invalid_image"),
    }
    clean = _source_tree_clean()
    report = {
        "schema_version": 1,
        "stage": "e09-a-controlled-vectorization-phase1",
        "status": "PASS" if clean else "FAIL",
        "source": {
            "path": str(source),
            "sha256": first.source_sha256,
            "tree_clean": clean,
        },
        "request": {
            "channel": request.channel,
            "threshold": request.threshold,
            "approximation_epsilon": request.approximation_epsilon,
            "minimum_area": request.minimum_area,
        },
        "result": first.as_dict(),
        "repeat_equal": first == second,
        "mutation_changes_hash": mutated_result.source_sha256 != first.source_sha256,
        "negative_cases": negatives,
        "limitations": [
            "E09-A detects exactly one solid external component.",
            "Islands and holes are diagnosed explicitly and are not silently "
            "discarded.",
            "Manual contour correction, collision generation, scene-object "
            "persistence and export remain E09-B/C work.",
        ],
    }
    (output / "stage1-e09-a-vectorization-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
