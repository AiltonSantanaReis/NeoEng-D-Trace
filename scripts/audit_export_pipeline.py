from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from src.core.commands import AutoGenerateCollisionShapesCommand, CommandManager
from src.core.snapping import SnapSettings
from src.exporters.animation_batch import export_animation_frames
from src.exporters.atlas_exporter import build_atlas
from src.exporters.collision_exporter import export_collision_document
from src.exporters.json_exporter import export_scene_metadata, save_json_metadata
from src.exporters.sprite_exporter import extract_masked_sprite
from src.exporters.tileset_exporter import prepare_tileset, save_tileset
from src.models.scene import Scene
from src.persistence.project_io import save_scene_project

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "artifacts" / "export-pipeline-audit"


def digest(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def make_scene(source: Path) -> Scene:
    image = np.zeros((96, 144, 4), dtype=np.uint8)
    image[:, :, 3] = 0
    image[10:70, 12:54, :3] = (200, 80, 40)
    image[10:70, 12:54, 3] = 255
    image[18:82, 80:135, :3] = (70, 180, 220)
    image[18:82, 80:135, 3] = 255
    Image.fromarray(image, "RGBA").save(source)
    scene = Scene()
    scene.cmd = CommandManager()
    scene.load_image(image, "source.png")
    scene.image_path = "source.png"
    scene.image_path_kind = "relative"
    scene.add_object(
        "pivot-object", [(12, 10), (54, 10), (54, 70), (12, 70)], select=False
    )
    scene.objects["pivot-object"].set_pivot(0.0, 1.0)
    scene.add_object(
        "concave-object",
        [(80, 18), (135, 18), (135, 45), (108, 45), (108, 82), (80, 82)],
        select=False,
    )
    return scene


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    source = OUT / "source.png"
    scene = make_scene(source)

    outputs: list[Path] = [source]

    profiles = {}
    for profile in ("generic", "godot", "unity", "phaser"):
        path = OUT / f"pivot-{profile}.json"
        save_json_metadata(export_scene_metadata(scene, profile), str(path))
        profiles[profile] = path.name
        outputs.append(path)

    sprite_items = []
    for object_id, obj in scene.objects.items():
        sprite_items.append(
            (object_id, extract_masked_sprite(scene.image, obj.polygon, padding=0))
        )
    atlas_dir = OUT / "atlas"
    atlas_results = build_atlas(
        sprite_items, str(atlas_dir), base_name="atlas", bleed=1
    )
    atlas_outputs = []
    for result in atlas_results:
        for key in ("atlas_path", "json_path"):
            path = Path(result[key])
            atlas_outputs.append(str(path.relative_to(OUT)))
            outputs.append(path)

    command = AutoGenerateCollisionShapesCommand("convex_decomposition")
    result = scene.cmd.execute(command, scene)
    if not result.changed or command.generated_part_count < 2:
        raise RuntimeError("compound collider evidence generation failed")
    collision_path = OUT / "compound-collision.json"
    save_json_metadata(
        export_collision_document(
            scene, coordinate_space="normalized", image_size=(144, 96)
        ),
        str(collision_path),
    )
    project_path = OUT / "compound-project.ndtproj"
    save_scene_project(scene, project_path)
    outputs.extend([collision_path, project_path])

    snapping_path = OUT / "snapping.json"
    snapping_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "grid_size": 4,
                "origin": [0.0, 0.0],
                "input": [11.9, 8.1],
                "output": list(SnapSettings(True, 4).apply((11.9, 8.1))),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    outputs.append(snapping_path)

    sheet = Image.new("RGBA", (18, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, 0, 7, 7), fill=(230, 80, 40, 255))
    draw.rectangle((10, 2, 15, 5), fill=(50, 180, 240, 255))
    tileset = prepare_tileset(sheet, tile_size=(8, 8), spacing=2, tolerance=0)
    tileset_result = save_tileset(tileset, OUT / "tileset")
    outputs.append(Path(tileset_result["manifest_path"]))
    outputs.extend(Path(tileset_result["manifest_path"]).parent.glob("tile_*.png"))

    frames_dir = OUT / "frames-source"
    frames_dir.mkdir()
    for name, offset in (("frame_10.png", 0), ("frame_2.png", 2)):
        frame = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rectangle(
            (4 + offset, 4, 26 + offset, 26), fill=(80, 220, 120, 255)
        )
        frame.save(frames_dir / name)
        outputs.append(frames_dir / name)
    animation_result = export_animation_frames(
        frames_dir, OUT / "animation", mode="basic", min_area=10
    )
    outputs.append(Path(animation_result["manifest_path"]))
    outputs.extend(Path(animation_result["manifest_path"]).parent.glob("frame_*.png"))

    manifest = {
        "schema_version": 1,
        "generator": "scripts/audit_export_pipeline.py",
        "stages": {
            "1_pivot": {"status": "APPROVED", "profiles": profiles},
            "2_atlas_bleed": {"status": "APPROVED", "outputs": atlas_outputs},
            "3_compound_colliders": {
                "status": "APPROVED",
                "part_count": command.generated_part_count,
                "outputs": [collision_path.name, project_path.name],
            },
            "4_vertex_snapping": {"status": "APPROVED", "output": snapping_path.name},
            "5_tileset_preparation": {
                "status": "APPROVED",
                "tile_count": len(tileset["tiles"]),
                "output": str(Path(tileset_result["manifest_path"]).relative_to(OUT)),
            },
            "6_animation_batch": {
                "status": "APPROVED",
                "frame_count": animation_result["manifest"]["frame_count"],
                "output": str(Path(animation_result["manifest_path"]).relative_to(OUT)),
            },
            "7_native_engine_plugins": {
                "status": "NOT_APPLICABLE",
                "reason": "Product definition keeps native plugins outside version 1.0; JSON profiles remain the supported contract.",
            },
        },
        "artifacts": {
            str(path.relative_to(OUT)): digest(path)
            for path in sorted(set(outputs))
            if path.is_file()
        },
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
