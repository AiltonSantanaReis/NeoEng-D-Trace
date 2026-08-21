"""Audit captured Qt UI PNGs without human inspection.

The capture manifest is the source of the live Qt geometry. This auditor is
intentionally fail-closed: an absent digest, widget geometry, PNG decoder,
palette color, or expected state is a failure, not a warning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw

from src.ui.theme_qss import QSS
from src.ui.theme_tokens import THEME_TOKENS

COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")
MAIN_WIDGETS = (
    "main_splitter",
    "tool_palette",
    "canvas",
    "panel_stack",
    "desktop_panel_splitter",
    "right_splitter",
    "compact_panel_tabs",
    "side_panel",
    "layers",
    "groups",
    "collision_panel",
    "toolbar",
    "nav_toolbar",
    "xray_toolbar",
)
PARENT_RELATIONS = {
    "tool_palette": "main_splitter",
    "canvas": "main_splitter",
    "panel_stack": "main_splitter",
    "desktop_panel_splitter": "panel_stack",
    "compact_panel_tabs": "panel_stack",
    "right_splitter": "desktop_panel_splitter",
    "collision_panel": "desktop_panel_splitter",
    "side_panel": "right_splitter",
    "layers": "right_splitter",
    "groups": "right_splitter",
}
SIBLING_RELATIONS = (
    ("tool_palette", "canvas"),
    ("canvas", "panel_stack"),
    ("right_splitter", "collision_panel"),
    ("side_panel", "layers"),
    ("side_panel", "groups"),
    ("layers", "groups"),
)
SCENARIO_WIDGETS = (
    "scenario_editor_toolbar",
    "scenario_editor_splitter",
    "professional_viewport_pages",
    "scenario_right_pages",
    "professional_viewport",
    "professional_inspector",
)
SCENARIO_BASE_WIDGETS = ("scenario_editor_toolbar", "scenario_editor_splitter", "professional_viewport_pages", "scenario_right_pages")
SCENARIO_PARENT_RELATIONS = (
    ("professional_viewport_pages", "scenario_editor_splitter"),
    ("scenario_right_pages", "scenario_editor_splitter"),
    ("professional_viewport", "professional_viewport_pages"),
    ("professional_inspector", "scenario_right_pages"),
)
STATE_BY_SUFFIX = {
    "_01_sem_projeto.png": "sem_projeto",
    "_02_projeto_paineis.png": "projeto_paineis",
    "_03_validacao_janela.png": "validacao_janela",
    "_03_validacao_modal.png": "validacao_modal",
    "_04_gizmo_feedback.png": "gizmo_feedback",
}
CORE_PALETTE = (
    THEME_TOKENS.window,
    THEME_TOKENS.surface,
    THEME_TOKENS.surface_alt,
    THEME_TOKENS.border,
    THEME_TOKENS.text_primary,
)
MODAL_PALETTE = (THEME_TOKENS.window, THEME_TOKENS.text_primary)
INTERACTIVE_PALETTE = (THEME_TOKENS.accent,)


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _rect(value: Any) -> tuple[int, int, int, int] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    if any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        return None
    return tuple(value)


def _intersection_area(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> int:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[0] + first[2], second[0] + second[2])
    bottom = min(first[1] + first[3], second[1] + second[3])
    return max(0, right - left) * max(0, bottom - top)


def _within(child: tuple[int, int, int, int], parent: tuple[int, int, int, int]) -> bool:
    return (
        child[0] >= parent[0]
        and child[1] >= parent[1]
        and child[0] + child[2] <= parent[0] + parent[2]
        and child[1] + child[3] <= parent[1] + parent[3]
    )


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _image_data(path: Path) -> tuple[Image.Image, np.ndarray, dict[str, Any]]:
    with Image.open(path) as source:
        source.verify()
    with Image.open(path) as source:
        image = source.copy()
    image.load()
    decoded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if decoded is None:
        raise ValueError("OpenCV could not decode the PNG")
    if decoded.ndim == 2:
        rgb = cv2.cvtColor(decoded, cv2.COLOR_GRAY2RGB)
    elif decoded.shape[2] == 4:
        rgb = cv2.cvtColor(decoded, cv2.COLOR_BGRA2RGB)
    else:
        rgb = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
    if tuple(rgb.shape[:2][::-1]) != image.size:
        raise ValueError("Pillow/OpenCV dimensions disagree")
    has_alpha = "A" in image.getbands() or "transparency" in image.info
    alpha = None
    if has_alpha:
        alpha = np.asarray(image.convert("RGBA").getchannel("A"), dtype=np.uint8)
    metadata = {
        "size": [image.width, image.height],
        "mode": image.mode,
        "has_alpha": has_alpha,
        "alpha_min": int(alpha.min()) if alpha is not None else None,
        "alpha_max": int(alpha.max()) if alpha is not None else None,
        "opencv_shape": list(decoded.shape),
        "rgb": rgb,
    }
    return image, rgb, metadata


def _finding(
    findings: list[dict[str, Any]],
    check: str,
    message: str,
    *,
    image: str | None = None,
    rects: list[dict[str, Any]] | None = None,
) -> None:
    findings.append(
        {
            "check": check,
            "message": message,
            "image": image,
            "rects": rects or [],
        }
    )


def _validate_hashes(
    input_dir: Path, manifest: dict[str, Any], findings: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    expected: dict[str, dict[str, Any]] = {}
    for capture in manifest.get("captures", {}).values():
        for name, digest in capture.get("files", {}).items():
            if name in expected:
                _finding(findings, "hash", f"duplicate manifest file reference: {name}")
            expected[name] = digest
    fixture = manifest.get("image_fixture")
    if isinstance(fixture, dict):
        expected["ui-audit-fixture.png"] = fixture
    actual = {path.name: path for path in input_dir.glob("*.png")}
    for name in sorted(set(expected) - set(actual)):
        _finding(findings, "hash", f"manifest PNG is missing: {name}")
    for name in sorted(set(actual) - set(expected)):
        _finding(findings, "hash", f"unmanifested PNG exists: {name}")
    for name in sorted(set(expected) & set(actual)):
        digest = expected[name]
        if not isinstance(digest, dict) or not isinstance(digest.get("sha256"), str):
            _finding(findings, "hash", f"invalid digest record: {name}")
            continue
        actual_digest = _digest(actual[name])
        if actual_digest != {"bytes": digest.get("bytes"), "sha256": digest.get("sha256")}:
            _finding(findings, "hash", f"digest mismatch: {name}")
    return expected


def _capture_state(name: str) -> str | None:
    for suffix, state in STATE_BY_SUFFIX.items():
        if name.endswith(suffix):
            return state
    return None


def _geometry_checks(
    filename: str,
    state: str,
    geometry: Any,
    image_size: tuple[int, int],
    findings: list[dict[str, Any]],
) -> None:
    if not isinstance(geometry, dict):
        _finding(findings, "geometry", "missing widget_geometry state", image=filename)
        return
    if state == "validacao_modal":
        widget = geometry.get("validacao_modal")
        rect = _rect(widget.get("root_geometry")) if isinstance(widget, dict) else None
        capture_size = (
            tuple(widget.get("capture_size"))
            if isinstance(widget, dict) and isinstance(widget.get("capture_size"), list)
            else None
        )
        expected_size = capture_size or (rect[2:] if rect is not None else None)
        if expected_size is None or tuple(expected_size) != image_size:
            _finding(findings, "geometry", "modal Qt geometry differs from PNG size", image=filename)
        return
    profile = geometry.get("profile")
    if profile in {"professional_scene_empty", "professional_scene_editor"}:
        state_widgets = geometry.get("professional_editor")
        if not isinstance(state_widgets, dict):
            _finding(findings, "geometry", "missing professional editor geometry", image=filename)
            return
        rects: dict[str, tuple[int, int, int, int]] = {}
        visible: set[str] = set()
        width, height = image_size
        required_widgets = SCENARIO_BASE_WIDGETS if profile == "professional_scene_empty" else SCENARIO_WIDGETS
        for name in required_widgets:
            widget = state_widgets.get(name)
            if not isinstance(widget, dict):
                _finding(findings, "geometry", f"missing Qt widget geometry: {name}", image=filename)
                continue
            root_rect = _rect(widget.get("root_geometry"))
            local_rect = _rect(widget.get("geometry"))
            if root_rect is None or local_rect is None or root_rect[2:] != local_rect[2:]:
                _finding(findings, "geometry", f"invalid or inconsistent geometry: {name}", image=filename)
                continue
            rects[name] = root_rect
            if bool(widget.get("visible")):
                visible.add(name)
                if root_rect[2] <= 0 or root_rect[3] <= 0 or not _within(root_rect, (0, 0, width, height)):
                    _finding(findings, "clipping", f"visible widget is clipped by capture bounds: {name}", image=filename, rects=[{"name": name, "rect": list(root_rect), "severity": "error"}])
        for child, parent in SCENARIO_PARENT_RELATIONS:
            if child in visible and parent in visible and child in rects and parent in rects and not _within(rects[child], rects[parent]):
                _finding(findings, "geometry", f"Qt child is outside its recorded parent: {child} -> {parent}", image=filename, rects=[{"name": child, "rect": list(rects[child]), "severity": "error"}, {"name": parent, "rect": list(rects[parent]), "severity": "error"}])
        return
    state_widgets = geometry.get(state)
    if not isinstance(state_widgets, dict):
        _finding(findings, "geometry", f"missing widget state: {state}", image=filename)
        return
    rects: dict[str, tuple[int, int, int, int]] = {}
    visible: set[str] = set()
    width, height = image_size
    for name in MAIN_WIDGETS:
        widget = state_widgets.get(name)
        if not isinstance(widget, dict):
            _finding(findings, "geometry", f"missing Qt widget geometry: {name}", image=filename)
            continue
        root_rect = _rect(widget.get("root_geometry"))
        local_rect = _rect(widget.get("geometry"))
        if root_rect is None or local_rect is None or root_rect[2:] != local_rect[2:]:
            _finding(findings, "geometry", f"invalid or inconsistent geometry: {name}", image=filename)
            continue
        rects[name] = root_rect
        if bool(widget.get("visible")):
            visible.add(name)
            if root_rect[2] <= 0 or root_rect[3] <= 0 or not _within(root_rect, (0, 0, width, height)):
                _finding(
                    findings,
                    "clipping",
                    f"visible widget is clipped by capture bounds: {name}",
                    image=filename,
                    rects=[{"name": name, "rect": list(root_rect), "severity": "error"}],
                )
    for child, parent in PARENT_RELATIONS.items():
        if child in visible and parent in visible and child in rects and parent in rects and not _within(rects[child], rects[parent]):
            _finding(
                findings,
                "geometry",
                f"Qt child is outside its recorded parent: {child} -> {parent}",
                image=filename,
                rects=[
                    {"name": child, "rect": list(rects[child]), "severity": "error"},
                    {"name": parent, "rect": list(rects[parent]), "severity": "error"},
                ],
            )
    for first, second in SIBLING_RELATIONS:
        if first in visible and second in visible and first in rects and second in rects:
            area = _intersection_area(rects[first], rects[second])
            if area:
                _finding(
                    findings,
                    "overlap",
                    f"visible sibling widgets overlap: {first} / {second} ({area}px²)",
                    image=filename,
                    rects=[
                        {"name": first, "rect": list(rects[first]), "severity": "error"},
                        {"name": second, "rect": list(rects[second]), "severity": "error"},
                    ],
                )


def _palette_checks(
    filename: str,
    rgb: np.ndarray,
    is_modal: bool,
    findings: list[dict[str, Any]],
    profile: str | None = None,
) -> dict[str, Any]:
    colors = sorted(set(COLOR_RE.findall(QSS)))
    required = MODAL_PALETTE if is_modal else (("#1e1e1e", "#3c3c3c", "#e6e6e6") if profile == "professional_scene_empty" else CORE_PALETTE)
    counts: dict[str, int] = {}
    for value in required:
        color = tuple(bytes.fromhex(value[1:]))
        counts[value] = int(np.all(rgb == color, axis=2).sum())
        if counts[value] == 0:
            _finding(findings, "palette", f"required QSS color absent from screenshot: {value}", image=filename)
    for value in INTERACTIVE_PALETTE:
        color = tuple(bytes.fromhex(value[1:]))
        counts[value] = int(np.all(rgb == color, axis=2).sum())
    luminance = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2])
    dark_ratio = float((luminance <= 100).mean())
    if dark_ratio < 0.55:
        _finding(findings, "palette", f"dark-theme pixel ratio too low: {dark_ratio:.4f}", image=filename)
    return {"qss_colors": colors, "required_counts": counts, "dark_pixel_ratio": dark_ratio}


def _annotate(input_path: Path, output_path: Path, findings: list[dict[str, Any]], status: str) -> None:
    with Image.open(input_path) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    relevant = [item for item in findings if item.get("image") == input_path.name]
    for item in relevant:
        color = (220, 50, 47) if item["check"] in {"clipping", "overlap", "geometry"} else (245, 166, 35)
        for entry in item.get("rects", []):
            rect = entry.get("rect")
            if isinstance(rect, list) and len(rect) == 4:
                x, y, w, h = rect
                label = str(entry.get("name", item["check"]))
                if w <= 0 or h <= 0:
                    # Keep the finding visible without allowing malformed Qt
                    # geometry to crash annotation and hide the real FAIL.
                    marker_x = max(0, min(image.width - 1, x))
                    marker_y = max(0, min(image.height - 1, y))
                    draw.ellipse(
                        (marker_x - 5, marker_y - 5, marker_x + 5, marker_y + 5),
                        outline=color,
                        width=4,
                    )
                    draw.text(
                        (max(0, marker_x + 6), max(0, marker_y + 4)),
                        label,
                        fill=color,
                    )
                    continue
                left = max(0, min(image.width - 1, x))
                top = max(0, min(image.height - 1, y))
                right = max(left, min(image.width - 1, x + w - 1))
                bottom = max(top, min(image.height - 1, y + h - 1))
                draw.rectangle((left, top, right, bottom), outline=color, width=4)
                draw.text((max(0, left + 4), max(0, top + 4)), label, fill=color)
    banner = (18, 130, 80) if status == "PASS" and not relevant else (190, 40, 35)
    draw.rectangle((0, 0, min(image.width, 260), 24), fill=banner)
    draw.text((6, 5), f"VISUAL AUDIT {status}", fill=(255, 255, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")


def run_audit(input_dir: Path, output_dir: Path) -> dict[str, Any]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    if not input_dir.is_dir():
        raise FileNotFoundError(input_dir)
    if output_dir == input_dir or input_dir in output_dir.parents:
        raise ValueError("output directory must not be inside the input capture directory")
    manifest_path = input_dir / "manifest.json"
    findings: list[dict[str, Any]] = []
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid manifest: {exc}") from exc
    if manifest.get("schema_version", 0) < 2:
        _finding(findings, "contract", "manifest schema 2 with Qt geometry is required")
    expected = _validate_hashes(input_dir, manifest, findings)
    captures = manifest.get("captures", {})
    image_reports: dict[str, Any] = {}
    for filename in sorted(expected):
        path = input_dir / filename
        if not path.is_file():
            continue
        state = _capture_state(filename)
        try:
            image, rgb, metadata = _image_data(path)
        except Exception as exc:
            _finding(findings, "decode", f"PNG decode failed: {exc}", image=filename)
            continue
        is_screenshot = state is not None
        is_modal = state == "validacao_modal"
        if metadata["has_alpha"] and metadata["alpha_min"] != 255:
            if is_screenshot:
                _finding(findings, "transparency", "screenshot contains transparent pixels", image=filename)
            elif metadata["alpha_min"] == 0:
                _finding(findings, "transparency", "fixture is fully or partially transparent", image=filename)
        if metadata["has_alpha"] and metadata["alpha_min"] != metadata["alpha_max"]:
            _finding(findings, "transparency", "mixed alpha values are not deterministic for an audit PNG", image=filename)
        expected_size: list[int] | None = None
        for capture in captures.values():
            if filename in capture.get("files", {}):
                if is_modal:
                    widget = capture.get("widget_geometry", {}).get("validacao_modal", {})
                    if isinstance(widget, dict) and isinstance(widget.get("capture_size"), list):
                        expected_size = widget["capture_size"]
                    else:
                        expected_size = _rect(widget.get("root_geometry"))[2:] if isinstance(widget, dict) and _rect(widget.get("root_geometry")) else None
                else:
                    expected_size = capture.get("actual_capture_size")
                break
        if expected_size is not None and tuple(metadata["size"]) != tuple(expected_size):
            _finding(findings, "dimensions", f"PNG dimensions {metadata['size']} != Qt capture {expected_size}", image=filename)
        capture = next((item for item in captures.values() if filename in item.get("files", {})), {})
        if state is not None:
            _geometry_checks(filename, state, capture.get("widget_geometry"), tuple(metadata["size"]), findings)
        palette_profile = capture.get("widget_geometry", {}).get("profile") if isinstance(capture.get("widget_geometry"), dict) else None
        palette = _palette_checks(filename, rgb, is_modal, findings, profile=palette_profile) if is_screenshot else {"skipped": True}
        edge = np.concatenate((rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]), axis=0)
        edge_activity = float((edge.max(axis=1) > 180).mean())
        image_reports[filename] = {key: value for key, value in metadata.items() if key != "rgb"} | {
            "sha256": _digest(path)["sha256"],
            "edge_activity": edge_activity,
            "palette": palette,
        }
    non_modal = [
        report
        for name, report in image_reports.items()
        if not name.endswith("_03_validacao_modal.png")
    ]
    for value in INTERACTIVE_PALETTE:
        if not any(
            report.get("palette", {}).get("required_counts", {}).get(value, 0) > 0
            for report in non_modal
        ):
            _finding(
                findings,
                "palette",
                f"interactive QSS color absent from all non-modal screenshots: {value}",
            )
    status = "PASS" if not findings else "FAIL"
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in sorted(image_reports):
        _annotate(input_dir / filename, output_dir / f"{Path(filename).stem}_annotated.png", findings, status)
    report = {
        "schema_version": 1,
        "status": status,
        "input": {"manifest": "manifest.json", "manifest_sha256": _digest(manifest_path)["sha256"]},
        "environment": {"platform": platform.platform(), "python": sys.version},
        "checks": ["pillow_decode", "opencv_decode", "dimensions", "transparency", "sha256", "clipping", "qt_geometry", "overlap", "qss_palette_contextual", "qss_palette_aggregate", "annotated_output"],
        "images": image_reports,
        "findings": findings,
        "finding_count": len(findings),
    }
    report_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    (output_dir / "visual-audit-report.json").write_text(report_text, encoding="utf-8", newline="\n")
    lines = ["# Reproducible visual audit", "", f"Status: **{status}**", "", f"Findings: {len(findings)}", "", "## Checks", "", "- " + "\n- ".join(report["checks"])]
    if findings:
        lines.extend(["", "## Findings", ""])
        lines.extend(f"- **{item['check']}**: {item['message']}" for item in findings)
    else:
        lines.extend(["", "No automated findings."])
    (output_dir / "visual-audit-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="capture directory containing manifest.json")
    parser.add_argument("--output", type=Path, required=True, help="directory for annotated PNGs and reports")
    args = parser.parse_args()
    report = run_audit(args.input, args.output)
    print(json.dumps({"status": report["status"], "finding_count": report["finding_count"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
