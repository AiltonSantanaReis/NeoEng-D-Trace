from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scripts.audit_visual_artifacts import run_audit
from src.ui.theme_tokens import THEME_TOKENS


def _digest(path: Path) -> dict[str, int | str]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _widget(x: int, y: int, width: int, height: int, visible: bool = True) -> dict:
    rect = [x, y, width, height]
    return {
        "class": "QWidget",
        "object_name": "",
        "visible": visible,
        "enabled": True,
        "geometry": rect,
        "root_geometry": rect,
        "frame_geometry": rect,
    }


def _color(token: str, *, rgba: bool) -> tuple[int, ...]:
    rgb = tuple(int(token[index : index + 2], 16) for index in (1, 3, 5))
    return (*rgb, 128) if rgba else rgb


def _make_capture(root: Path, *, rgba: bool = False) -> Path:
    root.mkdir()
    image_path = root / "1080p_FHD_01_sem_projeto.png"
    background = _color(THEME_TOKENS.window, rgba=rgba)
    image = Image.new("RGBA" if rgba else "RGB", (320, 200), background)
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (0, 0, 319, 19),
        fill=_color(THEME_TOKENS.surface_alt, rgba=rgba),
    )
    draw.rectangle(
        (0, 20, 39, 199),
        fill=_color(THEME_TOKENS.surface_raised, rgba=rgba),
    )
    draw.rectangle(
        (40, 20, 219, 199),
        fill=_color(THEME_TOKENS.surface, rgba=rgba),
    )
    draw.rectangle(
        (220, 20, 319, 199),
        fill=_color(THEME_TOKENS.border, rgba=rgba),
    )
    draw.point((50, 30), fill=_color(THEME_TOKENS.text_primary, rgba=rgba))
    draw.point((51, 30), fill=_color(THEME_TOKENS.accent, rgba=rgba))
    draw.point((319, 199), fill=_color(THEME_TOKENS.window, rgba=rgba))
    image.save(image_path, "PNG")

    widgets = {
        "main_splitter": _widget(0, 20, 320, 180),
        "tool_palette": _widget(0, 20, 40, 180),
        "reference_tool_palette": _widget(0, 20, 40, 180),
        "canvas": _widget(40, 20, 180, 180),
        "panel_stack": _widget(220, 20, 100, 180),
        "desktop_panel_splitter": _widget(220, 20, 100, 180),
        "reference_panel_tabs": _widget(220, 20, 100, 180),
        "right_splitter": _widget(220, 20, 60, 180),
        "compact_panel_tabs": _widget(220, 20, 100, 180, False),
        "side_panel": _widget(220, 20, 60, 60),
        "layers": _widget(220, 80, 60, 60, False),
        "groups": _widget(220, 140, 60, 60, False),
        "collision_panel": _widget(280, 20, 40, 180, False),
        "toolbar": _widget(0, 0, 100, 20),
        "nav_toolbar": _widget(100, 0, 100, 20),
        "xray_toolbar": _widget(200, 0, 120, 20),
        "tab_visibility": {
            "reference_panel_tabs": {
                "current_index": 0,
                "visible_to_root": True,
                "pages": [
                    {"index": 0, "visible": True, "visible_to_root": True},
                    {"index": 1, "visible": False, "visible_to_root": False},
                    {"index": 2, "visible": False, "visible_to_root": False},
                    {"index": 3, "visible": False, "visible_to_root": False},
                ],
            },
            "compact_panel_tabs": {
                "current_index": -1,
                "visible_to_root": False,
                "pages": [],
            },
        },
    }
    manifest = {
        "schema_version": 2,
        "generator": "tests",
        "captures": {
            "1080p_FHD": {
                "requested_size": [320, 200],
                "actual_window_size": [320, 200],
                "actual_capture_size": [320, 200],
                "files": {image_path.name: _digest(image_path)},
                "widget_geometry": {"sem_projeto": widgets},
            }
        },
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return image_path


def test_visual_auditor_uses_contextual_palette_for_modal(
    tmp_path: Path,
) -> None:
    from scripts.audit_visual_artifacts import _palette_checks

    rgb = np.zeros((4, 4, 3), dtype=np.uint8)
    rgb[:, :] = _color(THEME_TOKENS.window, rgba=False)
    rgb[0, 0] = _color(THEME_TOKENS.text_primary, rgba=False)
    findings: list[dict] = []

    palette = _palette_checks(
        "validacao_modal.png",
        rgb,
        is_modal=True,
        findings=findings,
    )

    assert findings == []
    assert palette["required_counts"][THEME_TOKENS.window] > 0
    assert THEME_TOKENS.surface not in palette["required_counts"]


def test_visual_auditor_passes_valid_png_and_generates_annotation(
    tmp_path: Path,
) -> None:
    _make_capture(tmp_path / "input")
    report = run_audit(tmp_path / "input", tmp_path / "output")

    assert report["status"] == "PASS"
    assert report["finding_count"] == 0
    annotation = tmp_path / "output" / "1080p_FHD_01_sem_projeto_annotated.png"
    assert annotation.is_file()
    assert (tmp_path / "output" / "visual-audit-report.json").is_file()


def test_visual_auditor_detects_inactive_tab_page_visible(tmp_path: Path) -> None:
    _make_capture(tmp_path / "input")
    manifest_path = tmp_path / "input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    page = manifest["captures"]["1080p_FHD"]["widget_geometry"]["sem_projeto"][
        "tab_visibility"
    ]["reference_panel_tabs"]["pages"][1]
    page["visible"] = True
    page["visible_to_root"] = True
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    report = run_audit(tmp_path / "input", tmp_path / "output")

    assert report["status"] == "FAIL"
    assert any(
        item["check"] == "geometry"
        and "inactive tab page visibility" in item["message"]
        for item in report["findings"]
    )


def test_visual_auditor_fails_closed_on_hash_mismatch(tmp_path: Path) -> None:
    image_path = _make_capture(tmp_path / "input")
    image = np.asarray(Image.open(image_path).convert("RGB")).copy()
    image[30, 50] = (255, 255, 255)
    Image.fromarray(image).save(image_path, "PNG")

    report = run_audit(tmp_path / "input", tmp_path / "output")

    assert report["status"] == "FAIL"
    assert any(item["check"] == "hash" for item in report["findings"])


def test_visual_auditor_fails_closed_on_transparency(tmp_path: Path) -> None:
    _make_capture(tmp_path / "input", rgba=True)
    report = run_audit(tmp_path / "input", tmp_path / "output")

    assert report["status"] == "FAIL"
    assert any(item["check"] == "transparency" for item in report["findings"])


def test_visual_auditor_detects_sibling_overlap(tmp_path: Path) -> None:
    _make_capture(tmp_path / "input")
    manifest_path = tmp_path / "input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    canvas = manifest["captures"]["1080p_FHD"]["widget_geometry"]["sem_projeto"]
    canvas = canvas["canvas"]
    canvas["root_geometry"][0] = 0
    canvas["geometry"][0] = 0
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    report = run_audit(tmp_path / "input", tmp_path / "output")

    assert report["status"] == "FAIL"
    assert any(item["check"] == "overlap" for item in report["findings"])


def test_visual_auditor_annotates_nonpositive_geometry_without_crashing(
    tmp_path: Path,
) -> None:
    _make_capture(tmp_path / "input")
    manifest_path = tmp_path / "input" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reference_panel_tabs = manifest["captures"]["1080p_FHD"]["widget_geometry"][
        "sem_projeto"
    ]["reference_panel_tabs"]
    reference_panel_tabs["root_geometry"][2] = 0
    reference_panel_tabs["geometry"][2] = 0
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    report = run_audit(tmp_path / "input", tmp_path / "output")

    assert report["status"] == "FAIL"
    assert any(item["check"] == "geometry" for item in report["findings"])
    assert (tmp_path / "output" / "1080p_FHD_01_sem_projeto_annotated.png").is_file()
