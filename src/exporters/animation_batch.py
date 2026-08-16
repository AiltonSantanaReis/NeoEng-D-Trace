"""Real folder-based animation frame detection and export."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image

from src.tools.auto_detect import detect_polygons

FORMAT_ID = "neoeng-d-trace-animation"
SCHEMA_VERSION = 1


def _natural_key(path: Path) -> tuple[Any, ...]:
    return tuple(
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    )


def discover_frames(
    input_dir: str | os.PathLike[str], pattern: str = "*.png"
) -> list[Path]:
    root = Path(input_dir)
    if not root.is_dir():
        raise ValueError("input_dir must be an existing directory")
    frames = sorted(
        (path for path in root.glob(pattern) if path.is_file()), key=_natural_key
    )
    if not frames:
        raise ValueError("no animation frames matched the pattern")
    return frames


def detect_frame(
    image: Image.Image, *, mode: str = "basic", **kwargs: Any
) -> dict[str, Any]:
    rgba = image.convert("RGBA")
    result = detect_polygons(np.asarray(rgba), mode=mode, **kwargs)
    polygons = list(result)
    if not polygons:
        raise ValueError("frame detection produced no polygon")
    detected = max(polygons, key=lambda item: float(item.get("area", 0.0)))
    polygon = detected.get("polygon")
    if not polygon or len(polygon) < 3:
        raise ValueError("frame detection produced an invalid polygon")
    return {
        "polygon": [[float(point[0]), float(point[1])] for point in polygon],
        "holes": detected.get("holes", []),
        "quality_metrics": detected.get("quality_metrics", {}),
        "feedback": result.feedback,
    }


def _signed_area(polygon: Sequence[Sequence[float]]) -> float:
    return 0.5 * sum(
        polygon[index][0] * polygon[(index + 1) % len(polygon)][1]
        - polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
        for index in range(len(polygon))
    )


def _resample_closed_polygon(
    polygon: Sequence[Sequence[float]], vertex_count: int
) -> list[list[float]]:
    if len(polygon) < 3:
        raise ValueError("polygon must contain at least three points")
    if vertex_count < 3:
        raise ValueError("vertex_count must be at least three")
    points = [(float(point[0]), float(point[1])) for point in polygon]
    lengths = [
        math.hypot(
            points[(index + 1) % len(points)][0] - points[index][0],
            points[(index + 1) % len(points)][1] - points[index][1],
        )
        for index in range(len(points))
    ]
    perimeter = sum(lengths)
    if perimeter <= 0.0:
        raise ValueError("polygon perimeter must be positive")
    result: list[list[float]] = []
    for sample_index in range(vertex_count):
        target = perimeter * sample_index / vertex_count
        travelled = 0.0
        for index, edge_length in enumerate(lengths):
            if target <= travelled + edge_length:
                ratio = (
                    0.0 if edge_length == 0.0 else (target - travelled) / edge_length
                )
                start = points[index]
                end = points[(index + 1) % len(points)]
                result.append(
                    [
                        start[0] + (end[0] - start[0]) * ratio,
                        start[1] + (end[1] - start[1]) * ratio,
                    ]
                )
                break
            travelled += edge_length
    return result


def _align_polygon_to_previous(
    polygon: list[list[float]], previous: Sequence[Sequence[float]]
) -> list[list[float]]:
    if _signed_area(polygon) * _signed_area(previous) < 0.0:
        polygon = list(reversed(polygon))
    count = len(polygon)
    return min(
        (polygon[offset:] + polygon[:offset] for offset in range(count)),
        key=lambda candidate: sum(
            (candidate[index][0] - previous[index][0]) ** 2
            + (candidate[index][1] - previous[index][1]) ** 2
            for index in range(count)
        ),
    )


def stabilize_animation_detections(
    frame_records: list[dict[str, Any]], *, vertex_count: int | None = None
) -> int:
    """Give all frame contours a stable vertex count and winding/alignment."""

    if not frame_records:
        raise ValueError("frame_records must not be empty")
    target = vertex_count or max(len(record["polygon"]) for record in frame_records)
    if target < 3 or target > 256:
        raise ValueError("vertex_count must be between 3 and 256")
    previous: list[list[float]] | None = None
    for record in frame_records:
        polygon = _resample_closed_polygon(record["polygon"], target)
        if previous is not None:
            polygon = _align_polygon_to_previous(polygon, previous)
        record["polygon"] = polygon
        previous = polygon
    return target


def export_animation_frames(
    input_dir: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *,
    pattern: str = "*.png",
    mode: str = "basic",
    **kwargs: Any,
) -> dict[str, Any]:
    """Detect every frame and write copied frame PNGs plus a JSON manifest."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    frame_records: list[dict[str, Any]] = []
    for index, source_path in enumerate(discover_frames(input_dir, pattern)):
        with Image.open(source_path) as opened:
            image = opened.convert("RGBA")
            detection = detect_frame(image, mode=mode, **kwargs)
            output_name = f"frame_{index:04d}.png"
            output_path = destination / output_name
            image.save(output_path, format="PNG")
            frame_records.append(
                {
                    "index": index,
                    "source": source_path.name,
                    "texture": output_name,
                    "size": {"w": image.width, "h": image.height},
                    **detection,
                }
            )
    coherent_vertex_count = stabilize_animation_detections(frame_records)
    manifest = {
        "format_id": FORMAT_ID,
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "coherence": {
            "enabled": True,
            "vertex_count": coherent_vertex_count,
            "method": "closed_perimeter_resampling_and_previous_frame_alignment",
        },
        "frame_count": len(frame_records),
        "frames": frame_records,
    }
    manifest_path = destination / "animation.json"
    fd, temporary = tempfile.mkstemp(
        prefix="tmp_animation_", suffix=".json", dir=str(destination), text=True
    )
    os.close(fd)
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, manifest_path)
        temporary = ""
    finally:
        if temporary and os.path.exists(temporary):
            os.remove(temporary)
    return {"manifest_path": str(manifest_path), "manifest": manifest}
