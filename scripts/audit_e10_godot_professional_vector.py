"""Run the E10 Godot import/runtime gate with an exported E09 vector object."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from src.exporters.scene_authoring_export import save_scene_authoring_export
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    SceneVectorGeometryRecord,
    SceneVectorImageSizeRecord,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(path: Path) -> None:
    image = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
    ImageDraw.Draw(image).polygon(
        [(24, 18), (104, 18), (110, 78), (24, 78)],
        fill=(30, 180, 240, 255),
    )
    image.save(path, format="PNG")


def _document(asset: Path) -> SceneAuthoringDocumentV2:
    asset_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
    polygon = [
        PointRecord(x=24, y=18),
        PointRecord(x=104, y=18),
        PointRecord(x=110, y=78),
        PointRecord(x=24, y=78),
    ]
    geometry = SceneVectorGeometryRecord(
        algorithm="e09-grabcut-contour-v1",
        source_sha256=asset_hash,
        image_size=SceneVectorImageSizeRecord(width=128, height=96),
        original_polygon=polygon,
        polygon=polygon,
        collision_polygon=polygon,
        detection_parameters={"channel": "alpha", "threshold": 1},
    )
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="E10 Godot vector round-trip",
            generator="NeoEng-D-Trace E10",
            app_version="0.3.0",
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[
            AssetReferenceRecord(
                id="subject",
                path="assets/scene/subject.png",
                sha256=asset_hash,
            )
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[
            SceneObjectAuthoringRecord(
                id="subject-object",
                asset_id="subject",
                layer_id="foreground",
                transform=SceneTransformRecord(
                    position=Point3Record(x=20, y=30, z=0),
                    rotation=Point3Record(x=0, y=0, z=0),
                    scale=Point3Record(x=1, y=1, z=1),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
                vector_geometry=geometry,
            )
        ],
        groups=[],
        parallax_layers=[],
        sockets=[],
    )


def run(output: Path, godot: str) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    asset = output / "assets" / "scene" / "subject.png"
    asset.parent.mkdir(parents=True)
    _write_fixture(asset)
    export_path = output / "scene.godot.runtime.json"
    save_scene_authoring_export(_document(asset), export_path, target="godot")
    shutil.copy2(
        ROOT
        / "integrations/godot/addons/neoeng_d_trace/professional_scene_importer.gd",
        output / "professional_scene_importer.gd",
    )
    (output / "project.godot").write_text(
        '[application]\nconfig/name="E10 Godot Vector Round Trip"\n'
        "[display]\nwindow/size/viewport_width=320\nwindow/size/viewport_height=240\n"
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
        encoding="utf-8",
        newline="\n",
    )
    (output / "validate.gd").write_text(
        (ROOT / "tools/godot_professional_vector_validator.gd").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
        newline="\n",
    )
    commands = [
        [
            godot,
            "--headless",
            "--editor",
            "--path",
            str(output),
            "--quit",
        ],
        [godot, "--headless", "--path", str(output), "--script", "validate.gd"],
    ]
    command_outputs: list[str] = []
    returncode = 0
    for command in commands:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        command_outputs.append(completed.stdout + completed.stderr)
        returncode = completed.returncode
        if returncode:
            break
    original_asset_bytes = asset.read_bytes()
    asset.write_bytes(b"tampered after export")
    negative = subprocess.run(
        commands[-1],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    asset.write_bytes(original_asset_bytes)
    negative_output = negative.stdout + negative.stderr
    negative_hash_rejected = (
        negative.returncode != 0 and "hash does not match" in negative_output.lower()
    )
    report = {
        "schema_version": 1,
        "stage": "E10-C-godot-professional-vector",
        "status": "PASS" if returncode == 0 and negative_hash_rejected else "FAIL",
        "godot": godot,
        "commands": [[Path(item[0]).name, *item[1:]] for item in commands],
        "returncode": returncode,
        "output": "\n".join(command_outputs),
        "negative_hash": {
            "returncode": negative.returncode,
            "rejected": negative_hash_rejected,
            "output": negative_output,
        },
        "export": {
            "path": export_path.name,
            "sha256": hashlib.sha256(export_path.read_bytes()).hexdigest(),
        },
        "asset": {
            "path": "assets/scene/subject.png",
            "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if completed.returncode:
        raise RuntimeError(report["output"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--godot", default="godot")
    args = parser.parse_args()
    report = run(args.output, args.godot)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
