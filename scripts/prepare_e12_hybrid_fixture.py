"""Prepare one reproducible E12 hybrid package from the validated E11 fixture."""

# The script prepends the source root before importing product modules.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.exporters.animation_batch import export_animation_frames  # noqa: E402
from src.exporters.hybrid_composition_export import (  # noqa: E402
    build_hybrid_composition_package,
)

DEFAULT_COMPOSITION = (
    ROOT
    / "artifacts"
    / "e11-composition-fixture-r57-20260909"
    / "exports"
    / "composition-e11-r9"
)


def _scene() -> dict[str, object]:
    return {
        "format_id": "neoeng-d-trace-hybrid-3d-scene",
        "schema_version": 1,
        "support_status": "VERTICAL_SLICE_ONLY",
        "camera": {
            "projection": "perspective",
            "fov_degrees": 55.0,
            "near": 0.1,
            "far": 100.0,
            "position": [0.0, 0.0, 8.0],
            "target": [0.0, 0.0, 0.0],
        },
        "materials": [
            {
                "id": "hero-material",
                "metallic": 0.0,
                "roughness": 0.6,
                "base_color": [0.15, 0.72, 0.95, 1.0],
            }
        ],
        "meshes": [
            {
                "id": "hero-mesh",
                "material_id": "hero-material",
                "position": [0.0, 0.0, 0.0],
                "vertices": [[-1.0, -1.0, 0.0], [1.0, -1.0, 0.0], [0.0, 1.0, 0.0]],
                "triangles": [[0, 1, 2]],
            }
        ],
        "lights": [
            {
                "id": "key-light",
                "type": "directional",
                "intensity": 1.2,
                "position": [2.0, 3.0, 4.0],
            }
        ],
        "animation_clips": [
            {
                "id": "hero-bob",
                "mesh_id": "hero-mesh",
                "keyframes": [
                    {"time": 0.0, "position": [0.0, 0.0, 0.0]},
                    {"time": 1.0, "position": [0.0, 0.25, 0.0]},
                ],
            }
        ],
    }


def prepare(composition: Path, output: Path) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite E12 fixture: {output}")
    hero = composition / "assets" / "scene" / "hero.png"
    if not hero.is_file():
        raise FileNotFoundError(f"E11 fixture asset is missing: {hero}")
    output.mkdir(parents=True)
    input_dir = output / "animation-input"
    animation_dir = output / "animation"
    input_dir.mkdir()
    with Image.open(hero) as opened:
        image = opened.convert("RGBA")
        image.save(input_dir / "input_0000.png", format="PNG")
        second = image.copy()
        ImageDraw.Draw(second).point((0, 0), fill=(0, 255, 255, 255))
        second.save(input_dir / "input_0001.png", format="PNG")
    animation_result = export_animation_frames(
        input_dir, animation_dir, mode="basic", min_area=2
    )
    scene_path = output / "hybrid-scene.json"
    scene_path.write_text(
        json.dumps(_scene(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    package = output / "package"
    manifest = build_hybrid_composition_package(
        composition, animation_dir, scene_path, package
    )
    (output / "fixture-manifest.json").write_text(
        json.dumps(
            {
                "status": "SUCCESS",
                "composition": str(composition),
                "animation_manifest": animation_result["manifest_path"],
                "package": str(package),
                "package_manifest": manifest,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--composition", type=Path, default=DEFAULT_COMPOSITION)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.composition.resolve(), args.output.resolve())
    print(
        json.dumps(
            {
                "status": "SUCCESS",
                "support_status": manifest["support_status"],
                "package": str(args.output.resolve() / "package"),
                "components": len(manifest["components"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
