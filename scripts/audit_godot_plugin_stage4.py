"""Build and execute a real Godot project for stage-four core import."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.exporters.integration_manifest import (
    build_integration_manifest,
    save_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene

ROOT = Path(__file__).resolve().parents[1]
ADDON_SOURCE = ROOT / "integrations" / "godot" / "addons" / "neoeng_d_trace"
VALIDATOR_SOURCE = ROOT / "tools" / "godot_plugin_stage4_validator.gd"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(executable: str, arguments: list[str], workspace: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [executable, *arguments],
        cwd=workspace,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    output = re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", completed.stdout)
    portable_arguments = [
        re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", argument)
        for argument in arguments
    ]
    return {
        "executable": Path(executable).name,
        "arguments": portable_arguments,
        "returncode": completed.returncode,
        "output": output,
    }


def _prepare(workspace: Path) -> dict[str, Any]:
    addon_destination = workspace / "addons" / "neoeng_d_trace"
    addon_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ADDON_SOURCE, addon_destination)
    generated = workspace / "NeoEngGenerated"
    generated.mkdir()

    image_path = workspace / "source.png"
    image = Image.new("RGBA", (34, 14), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 16, 12), fill=(30, 180, 240, 255))
    draw.rectangle((18, 1, 33, 12), fill=(240, 120, 30, 255))
    image.save(image_path, format="PNG")

    frames_dir = workspace / "frames"
    frames_dir.mkdir()
    animation_frames = []
    for index, x_offset in enumerate((0, 1)):
        frame = Image.new("RGBA", (16, 12), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rectangle(
            (x_offset, 0, 15, 11), fill=(30 + index * 80, 180, 240, 255)
        )
        frame_path = frames_dir / f"frame_{index:04d}.png"
        frame.save(frame_path, format="PNG")
        animation_frames.append(
            {
                "texture": f"frames/frame_{index:04d}.png",
                "size": {"w": 16, "h": 12},
                "polygon": [[0, 0], [16, 0], [16, 12], [0, 12]],
            }
        )

    scene = Scene()
    polygon = [(0, 0), (16, 0), (16, 12), (0, 12)]
    scene.add_object("hero", polygon)
    scene.collision_shapes["hero"] = polygon
    compound_polygon = [(16, 0), (32, 0), (32, 12), (16, 12)]
    scene.add_object("compound", compound_polygon)
    scene.collision_shapes["compound"] = compound_polygon
    scene.collision_parts["compound"] = [
        [(16, 0), (24, 0), (24, 12), (16, 12)],
        [(24, 0), (32, 0), (32, 12), (24, 12)],
    ]
    metadata = export_scene_metadata(scene)
    metadata["tileset"] = {
        "format_id": "neoeng-d-trace-tileset",
        "schema_version": 1,
        "tile_size": {"w": 16, "h": 12},
        "spacing": 1,
        "margin": 1,
        "tiles": [
            {
                "id": "tile_0000",
                "index": 0,
                "row": 0,
                "column": 0,
                "source_rect": {"x": 1, "y": 1, "w": 16, "h": 12},
                "collision": [[0, 0], [16, 0], [16, 12], [0, 12]],
            },
            {
                "id": "tile_0001",
                "index": 1,
                "row": 0,
                "column": 1,
                "source_rect": {"x": 18, "y": 1, "w": 16, "h": 12},
                "collision": [[1, 1], [15, 1], [15, 11], [1, 11]],
            },
        ],
    }
    metadata["animation"] = {
        "format_id": "neoeng-d-trace-animation",
        "schema_version": 1,
        "mode": "basic",
        "speed": 12.0,
        "loop": True,
        "frame_count": len(animation_frames),
        "frames": animation_frames,
    }
    manifest = build_integration_manifest(
        metadata,
        engine="godot",
        image_path=image_path,
        image_reference="source.png",
    )
    manifest_path = generated / "hero.ndt.integration.json"
    save_integration_manifest(manifest, manifest_path)
    shutil.copy2(VALIDATOR_SOURCE, workspace / "validate_stage4.gd")
    (workspace / "project.godot").write_text(
        '[application]\nconfig/name="NeoEngDTracePluginStage4"\n'
        "[editor_plugins]\n"
        'enabled=PackedStringArray("res://addons/neoeng_d_trace/plugin.cfg")\n',
        encoding="utf-8",
    )
    return {
        "image": image_path,
        "manifest": manifest_path,
        "frames": [
            frames_dir / f"frame_{index:04d}.png"
            for index in range(len(animation_frames))
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.work_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="neoeng-godot-plugin-stage4-")
        workspace = Path(temporary.name)
    else:
        workspace = args.work_dir.resolve()
        workspace.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": 4,
        "status": "FAILED",
        "plugin": "neoeng_d_trace",
        "import_scope": (
            "Sprite2D, AtlasTexture, properties, compound CollisionPolygon2D, "
            "TileSet, AnimatedSprite2D, frame collisions, determinism, manual conflict"
        ),
    }
    try:
        fixture = _prepare(workspace)
        commands = [
            _run(
                args.executable,
                ["--headless", "--editor", "--path", str(workspace), "--import"],
                workspace,
            ),
            _run(
                args.executable,
                [
                    "--headless",
                    "--path",
                    str(workspace),
                    "--script",
                    "validate_stage4.gd",
                ],
                workspace,
            ),
        ]
        report["commands"] = commands
        report["fixture_files"] = {
            "source.png": {
                "size": fixture["image"].stat().st_size,
                "sha256": _sha256(fixture["image"]),
            },
            "hero.ndt.integration.json": {
                "size": fixture["manifest"].stat().st_size,
                "sha256": _sha256(fixture["manifest"]),
            },
            "animation_frames": [
                {
                    "name": frame.name,
                    "size": frame.stat().st_size,
                    "sha256": _sha256(frame),
                }
                for frame in fixture["frames"]
            ],
        }
        if any(command["returncode"] != 0 for command in commands):
            raise RuntimeError("Godot stage-four command failed")
        if "NATIVE_PLUGIN_STAGE4_CORE=SUCCESS" not in commands[-1]["output"]:
            raise RuntimeError("stage-four success marker missing")
        report["status"] = "SUCCESS"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return 0
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
