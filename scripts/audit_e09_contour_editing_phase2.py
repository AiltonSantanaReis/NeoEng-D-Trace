"""Official E09-B audit for reversible contour editing."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from src.core.contour_editing import ContourEditSession
from src.core.vectorization import VectorizationError, vectorize_image_file


def _source_tree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _write_source(path: Path) -> None:
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    if not ok:
        raise RuntimeError("cannot encode E09-B source")
    path.write_bytes(encoded.tobytes())


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    source = output / "e09-b-source.png"
    _write_source(source)
    detected = vectorize_image_file(source)
    session = ContourEditSession(detected)
    edited = session.move_vertex(1, (110, 20))
    undone = session.undo()
    redone = session.redo()
    if undone != session.original_polygon or redone != edited:
        raise AssertionError("undo/redo did not restore exact contour states")

    jagged = replace(
        detected,
        polygon=tuple(
            (float(x), float(y))
            for x, y in (
                (24, 18),
                (45, 18),
                (70, 18),
                (103, 18),
                (103, 40),
                (103, 77),
                (70, 77),
                (45, 77),
                (24, 77),
                (24, 40),
            )
        ),
    )
    simplified_session = ContourEditSession(jagged)
    simplified = simplified_session.simplify(3.0)
    if len(simplified) >= len(jagged.polygon):
        raise AssertionError("simplification did not reduce the jagged contour")

    cancelled = ContourEditSession(detected)
    cancelled.move_vertex(1, (110, 20))
    cancelled_polygon = cancelled.cancel()
    try:
        cancelled.result()
    except VectorizationError as exc:
        if exc.code != "session_cancelled":
            raise AssertionError(f"unexpected cancel code: {exc.code}") from exc
    else:
        raise AssertionError("cancelled session returned an editable result")

    clean = _source_tree_clean()
    report = {
        "schema_version": 1,
        "stage": "e09-b-reversible-contour-editing-phase2",
        "status": "PASS" if clean else "FAIL",
        "source": {
            "path": str(source),
            "source_sha256": detected.source_sha256,
            "tree_clean": clean,
        },
        "original_vertex_count": len(detected.polygon),
        "edited_vertex_count": len(edited),
        "simplified_vertex_count": len(simplified),
        "undo_redo_exact": undone == session.original_polygon and redone == edited,
        "provenance_preserved": session.result().source_sha256
        == detected.source_sha256,
        "cancelled_restores_original": cancelled_polygon == cancelled.original_polygon,
        "limitations": [
            "This phase proves the editing core, not a native contour-editing panel.",
            "Collision generation, scene-object integration, persistence and "
            "export remain E09-C.",
        ],
    }
    (output / "stage2-e09-b-contour-editing-report.json").write_text(
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
