"""Deterministic, real-image quality and performance audit for polygon detection."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.core.operational_limits import MAX_POLYGON_POINTS
from src.tools.auto_detect import detect_polygons

Point = Tuple[int, int]


@dataclass(frozen=True)
class Case:
    name: str
    image: np.ndarray
    ground_truth: np.ndarray
    roi: Optional[Tuple[int, int, int, int]] = None
    expected_objects: int = 1
    expected_holes: int = 0
    grabcut_ground_truth: Optional[np.ndarray] = None


def _sha256_array(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _draw_case(
    name: str, size: Tuple[int, int] = (256, 192)
) -> Tuple[np.ndarray, np.ndarray]:
    width, height = size
    image = np.zeros((height, width, 3), dtype=np.uint8)
    ground_truth = np.zeros((height, width), dtype=np.uint8)
    background = np.zeros_like(image)
    yy, xx = np.mgrid[0:height, 0:width]

    if name == "clean_rectangle":
        cv2.rectangle(image, (35, 28), (220, 164), (230, 230, 230), -1)
        cv2.rectangle(ground_truth, (35, 28), (220, 164), 255, -1)
    elif name == "concave_l":
        points = np.array(
            [(35, 28), (130, 28), (130, 80), (205, 80), (205, 164), (35, 164)]
        )
        cv2.fillPoly(image, [points], (230, 230, 230))
        cv2.fillPoly(ground_truth, [points], 255)
    elif name == "shadow_texture":
        cv2.rectangle(image, (35, 28), (220, 164), (205, 205, 205), -1)
        shadow = ((xx - 40) / width * 70 + (yy / height) * 30).astype(np.uint8)
        image = np.clip(image.astype(np.int16) - shadow[:, :, None], 0, 255).astype(
            np.uint8
        )
        cv2.circle(image, (120, 100), 28, (90, 90, 90), -1)
        cv2.fillPoly(
            ground_truth, [np.array([(35, 28), (220, 28), (220, 164), (35, 164)])], 255
        )
    elif name == "gradient_low_contrast":
        gradient = np.clip(65 + 70 * xx / width, 0, 255).astype(np.uint8)
        image = np.repeat(gradient[:, :, None], 3, axis=2)
        cv2.ellipse(image, (128, 96), (75, 55), 0, 0, 360, (112, 112, 112), -1)
        cv2.ellipse(ground_truth, (128, 96), (75, 55), 0, 0, 360, 255, -1)
    elif name == "ring_hole":
        cv2.circle(image, (128, 96), 70, (235, 235, 235), -1)
        cv2.circle(image, (128, 96), 28, (0, 0, 0), -1)
        cv2.circle(ground_truth, (128, 96), 70, 255, -1)
        cv2.circle(ground_truth, (128, 96), 28, 0, -1)
    elif name == "curved_blob":
        points = []
        for index in range(180):
            angle = 2 * np.pi * index / 180
            radius_x = 76 + 12 * np.sin(5 * angle)
            radius_y = 51 + 8 * np.cos(4 * angle)
            points.append(
                (
                    int(128 + radius_x * np.cos(angle)),
                    int(96 + radius_y * np.sin(angle)),
                )
            )
        points_array = np.asarray(points, dtype=np.int32)
        cv2.fillPoly(image, [points_array], (230, 230, 230))
        cv2.fillPoly(ground_truth, [points_array], 255)
    elif name == "two_objects":
        cv2.circle(image, (75, 96), 38, (230, 230, 230), -1)
        cv2.rectangle(image, (145, 50), (215, 142), (230, 230, 230), -1)
        cv2.circle(ground_truth, (75, 96), 38, 255, -1)
        cv2.rectangle(ground_truth, (145, 50), (215, 142), 255, -1)
    elif name == "touching_objects":
        cv2.circle(image, (98, 96), 45, (230, 230, 230), -1)
        cv2.circle(image, (158, 96), 45, (230, 230, 230), -1)
        cv2.circle(ground_truth, (98, 96), 45, 255, -1)
        cv2.circle(ground_truth, (158, 96), 45, 255, -1)
    elif name == "rgba_alpha":
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        cv2.ellipse(rgba, (128, 96), (75, 52), 15, 0, 360, (220, 150, 50, 255), -1)
        cv2.ellipse(ground_truth, (128, 96), (75, 52), 15, 0, 360, 255, -1)
        return rgba, ground_truth
    elif name == "noisy_background":
        rng = np.random.default_rng(20260816)
        background[:] = rng.integers(0, 70, size=background.shape, dtype=np.uint8)
        image = background
        cv2.ellipse(image, (128, 96), (75, 52), -20, 0, 360, (210, 210, 210), -1)
        cv2.ellipse(ground_truth, (128, 96), (75, 52), -20, 0, 360, 255, -1)
    elif name == "high_detail_boundary":
        points = []
        for index in range(2400):
            angle = 2 * np.pi * index / 2400
            radius = 70 + 7 * np.sin(31 * angle) + 4 * np.sin(73 * angle)
            points.append(
                (int(128 + radius * np.cos(angle)), int(96 + radius * np.sin(angle)))
            )
        points_array = np.asarray(points, dtype=np.int32)
        cv2.fillPoly(image, [points_array], (235, 235, 235))
        cv2.fillPoly(ground_truth, [points_array], 255)
    else:
        raise ValueError(f"unknown case: {name}")

    if name != "rgba_alpha":
        image[ground_truth == 0] = np.minimum(image[ground_truth == 0], 35)
    return image, ground_truth


def build_cases() -> List[Case]:
    names = (
        "clean_rectangle",
        "concave_l",
        "shadow_texture",
        "gradient_low_contrast",
        "ring_hole",
        "curved_blob",
        "two_objects",
        "touching_objects",
        "rgba_alpha",
        "noisy_background",
        "high_detail_boundary",
    )
    cases = []
    for name in names:
        image, ground_truth = _draw_case(name)
        roi = (20, 15, 216, 162) if name != "two_objects" else (30, 35, 90, 125)
        grabcut_ground_truth = None
        if name == "two_objects":
            grabcut_ground_truth = np.zeros_like(ground_truth)
            cv2.circle(grabcut_ground_truth, (75, 96), 38, 255, -1)
        expected_objects = 2 if name == "two_objects" else 1
        expected_holes = 1 if name == "ring_hole" else 0
        cases.append(
            Case(
                name,
                image,
                ground_truth,
                roi,
                expected_objects,
                expected_holes,
                grabcut_ground_truth,
            )
        )
    return cases


def _polygons_mask(
    polygons: List[Dict[str, Any]], shape: Tuple[int, int]
) -> np.ndarray:
    result = np.zeros(shape, dtype=np.uint8)
    for item in polygons:
        points = item.get("polygon", [])
        if item.get("is_hole", False):
            cv2.fillPoly(result, [np.asarray(points, dtype=np.int32)], 0)
        else:
            cv2.fillPoly(result, [np.asarray(points, dtype=np.int32)], 255)
            for hole in item.get("holes", []):
                cv2.fillPoly(result, [np.asarray(hole, dtype=np.int32)], 0)
    return result


def _boundary_f1(predicted: np.ndarray, truth: np.ndarray, tolerance: int = 2) -> float:
    pred_edges = (
        cv2.morphologyEx(predicted, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    )
    truth_edges = (
        cv2.morphologyEx(truth, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    )
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * tolerance + 1, 2 * tolerance + 1)
    )
    pred_near = cv2.dilate(pred_edges.astype(np.uint8), kernel) > 0
    truth_near = cv2.dilate(truth_edges.astype(np.uint8), kernel) > 0
    precision = float(np.count_nonzero(pred_edges & truth_near)) / max(
        1, int(np.count_nonzero(pred_edges))
    )
    recall = float(np.count_nonzero(truth_edges & pred_near)) / max(
        1, int(np.count_nonzero(truth_edges))
    )
    return 2.0 * precision * recall / max(1e-12, precision + recall)


def _metrics(
    predicted: np.ndarray,
    truth: np.ndarray,
    polygons: List[Dict[str, Any]],
    expected_objects: int,
    expected_holes: int,
) -> Dict[str, Any]:
    pred = predicted > 0
    ref = truth > 0
    intersection = int(np.count_nonzero(pred & ref))
    union = int(np.count_nonzero(pred | ref))
    dice = (2.0 * intersection) / max(
        1, int(np.count_nonzero(pred)) + int(np.count_nonzero(ref))
    )
    vertices = [len(item.get("polygon", [])) for item in polygons]
    holes = sum(
        len(item.get("holes", []))
        for item in polygons
        if not item.get("is_hole", False)
    )
    if holes == 0:
        holes = sum(1 for item in polygons if item.get("is_hole", False))
    return {
        "iou": intersection / max(1, union),
        "dice": dice,
        "boundary_f1": _boundary_f1(predicted, truth),
        "object_count": len(
            [item for item in polygons if not item.get("is_hole", False)]
        ),
        "expected_objects": expected_objects,
        "hole_count": holes,
        "expected_holes": expected_holes,
        "vertex_counts": vertices,
        "max_vertices": max(vertices, default=0),
        "within_vertex_limit": max(vertices, default=0) <= MAX_POLYGON_POINTS,
    }


def _run_one(
    case: Case,
    mode: str,
    repeats: int,
    artifact_output: Optional[Path] = None,
) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {"min_area": 25.0}
    if mode == "grabcut":
        kwargs.update(roi=case.roi, detect_holes=True, grabcut_iterations=5)
    elif mode == "perfect":
        kwargs.update(downscale=1.0, separate_touching=False)
    elif mode == "enhanced":
        kwargs.update(downscale=1.0, detect_holes=True, morph_kernel_size=3)

    timings: List[float] = []
    peaks: List[int] = []
    hashes: List[str] = []
    last_polygons: List[Dict[str, Any]] = []
    errors: List[str] = []
    for _ in range(repeats):
        tracemalloc.start()
        started = time.perf_counter()
        try:
            result = detect_polygons(case.image, mode=mode, **kwargs)
            last_polygons = list(result)
            predicted = _polygons_mask(last_polygons, case.ground_truth.shape)
            hashes.append(_sha256_array(predicted))
        except Exception as exc:  # report real failures rather than hiding them
            errors.append(f"{type(exc).__name__}: {exc}")
            predicted = np.zeros_like(case.ground_truth)
        timings.append(time.perf_counter() - started)
        _, peak = tracemalloc.get_traced_memory()
        peaks.append(int(peak))
        tracemalloc.stop()

    evaluation_truth = (
        case.grabcut_ground_truth
        if mode == "grabcut" and case.grabcut_ground_truth is not None
        else case.ground_truth
    )
    evaluation_expected_objects = (
        1
        if mode == "grabcut" and case.grabcut_ground_truth is not None
        else case.expected_objects
    )
    metrics = _metrics(
        predicted,
        evaluation_truth,
        last_polygons,
        evaluation_expected_objects,
        case.expected_holes,
    )
    if artifact_output is not None:
        prediction_dir = artifact_output / "predictions"
        prediction_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(
            str(prediction_dir / f"{case.name}_{mode}_predicted.png"),
            predicted,
        )
        if case.image.ndim == 2:
            source_bgr = cv2.cvtColor(case.image, cv2.COLOR_GRAY2BGR)
        elif case.image.shape[2] == 4:
            source_bgr = cv2.cvtColor(case.image, cv2.COLOR_RGBA2BGR)
        else:
            source_bgr = cv2.cvtColor(case.image, cv2.COLOR_RGB2BGR)
        tint = np.zeros_like(source_bgr)
        tint[:, :, 1] = 255
        overlay = source_bgr.copy()
        selected = predicted > 0
        overlay[selected] = cv2.addWeighted(
            source_bgr[selected], 0.55, tint[selected], 0.45, 0
        )
        cv2.imwrite(str(prediction_dir / f"{case.name}_{mode}_overlay.png"), overlay)
    return {
        "mode": mode,
        "case": case.name,
        "image_sha256": _sha256_array(case.image),
        "ground_truth_sha256": _sha256_array(evaluation_truth),
        "prediction_sha256": hashes[-1] if hashes else None,
        "deterministic": len(set(hashes)) <= 1,
        "median_seconds": float(np.median(timings)),
        "p95_seconds": float(np.percentile(timings, 95)),
        "peak_python_bytes_max": max(peaks, default=0),
        "peak_memory_note": (
            "tracemalloc cobre alocações Python; "
            "memória nativa do OpenCV pode não aparecer."
        ),
        "errors": errors,
        "metrics": metrics,
    }


def _write_images(output: Path, cases: List[Case]) -> None:
    images = output / "images"
    images.mkdir(parents=True, exist_ok=True)
    for case in cases:
        cv2.imwrite(str(images / f"{case.name}_source.png"), case.image)
        cv2.imwrite(str(images / f"{case.name}_ground_truth.png"), case.ground_truth)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evidence/artifacts/auto-detection-quality/baseline"),
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--cases", nargs="*", default=None)
    parser.add_argument("--modes", nargs="*", default=None)
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats > 20:
        raise SystemExit("repeats must be between 1 and 20")
    cases = build_cases()
    if args.cases:
        selected = set(args.cases)
        unknown = selected - {case.name for case in cases}
        if unknown:
            raise SystemExit(f"unknown cases: {sorted(unknown)}")
        cases = [case for case in cases if case.name in selected]
    args.output.mkdir(parents=True, exist_ok=True)
    _write_images(args.output, cases)
    modes = tuple(args.modes or ("basic", "perfect", "enhanced", "grabcut"))
    invalid_modes = set(modes) - {"basic", "perfect", "enhanced", "grabcut"}
    if invalid_modes:
        raise SystemExit(f"unknown modes: {sorted(invalid_modes)}")
    rows = []
    for case in cases:
        for mode in modes:
            print(f"running {case.name}/{mode}", flush=True)
            rows.append(_run_one(case, mode, args.repeats, args.output))
    report = {
        "schema": 1,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "opencv": cv2.__version__,
        "numpy": np.__version__,
        "repeats": args.repeats,
        "corpus": [
            {
                "name": case.name,
                "image_sha256": _sha256_array(case.image),
                "ground_truth_sha256": _sha256_array(case.ground_truth),
                "grabcut_ground_truth_sha256": (
                    _sha256_array(case.grabcut_ground_truth)
                    if case.grabcut_ground_truth is not None
                    else None
                ),
                "shape": list(case.ground_truth.shape),
                "roi": list(case.roi) if case.roi else None,
                "expected_objects": case.expected_objects,
                "expected_holes": case.expected_holes,
            }
            for case in cases
        ],
        "results": rows,
        "summary": {
            "runs": len(rows),
            "errors": sum(bool(row["errors"]) for row in rows),
            "nondeterministic": sum(not row["deterministic"] for row in rows),
        },
    }
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
