"""Run the real Godot Stage 5 professional-scene adapter audit.

The temporary engine project is created outside the repository tree.  Only
sanitized logs, the exact export fixture and SHA-256 metadata are retained as
reproducible evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from src.exporters.scene_authoring_export import save_scene_authoring_export
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/artifacts/stage5-professional-scene-2026-08-19"
IMPORTER = ROOT / "integrations/godot/addons/neoeng_d_trace"
VALIDATOR = ROOT / "tools/godot_professional_scene_stage5_validator.gd"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize(value: str, temporary_root: Path) -> str:
    result = value.replace(str(temporary_root), "<temporary-project>")
    result = result.replace(str(ROOT), "<repo>")
    return re.sub(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", result)


def _godot_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    found = shutil.which("godot")
    if found:
        return Path(found)
    fallback = Path("C:/ProgramData/chocolatey/bin/godot.exe")
    if fallback.is_file():
        return fallback
    raise RuntimeError("Godot executable was not found")


def _document(asset: Path) -> SceneAuthoringDocumentV2:
    digest = _sha256(asset)
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="Stage 5 native fixture",
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[
            AssetReferenceRecord(id="hero_asset", path="assets/hero.png", sha256=digest)
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero",
                asset_id="hero_asset",
                layer_id="foreground",
                transform=SceneTransformRecord(
                    position=Point3Record(x=10.0, y=20.0, z=3.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=15.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=1.0),
                    flip_x=True,
                ),
            )
        ],
        groups=[],
        camera=SceneCameraAuthoringRecord(
            position=PointRecord(x=2.0, y=4.0), zoom=1.25
        ),
        sockets=[
            SceneLightSocketRecord(
                id="lamp",
                layer_id="foreground",
                object_id="hero",
                position=Point3Record(x=3.0, y=4.0, z=1.0),
                color="#ffe082",
                intensity=1.5,
                radius=64.0,
            )
        ],
    )


def _run(
    godot: Path, project: Path, temporary_root: Path, label: str
) -> dict[str, object]:
    log = OUT / f"godot-{label}.log"
    preimport = subprocess.run(
        [
            str(godot),
            "--headless",
            "--editor",
            "--path",
            str(project),
            "--import",
            "--quit-after",
            "5",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    command = [
        str(godot),
        "--headless",
        "--path",
        str(project),
        "--script",
        "res://tools/godot_professional_scene_stage5_validator.gd",
        "--quit-after",
        "5",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = _sanitize(
        "PREIMPORT\n"
        + preimport.stdout
        + preimport.stderr
        + "\nVALIDATOR\n"
        + completed.stdout
        + completed.stderr,
        temporary_root,
    )
    log.write_text(output, encoding="utf-8", newline="\n")
    layer_match = re.search(r"GODOT_PROFESSIONAL_SCENE_LAYERS=(\d+)", output)
    object_match = re.search(r"GODOT_PROFESSIONAL_SCENE_OBJECTS=(\d+)", output)
    return {
        "preimport_returncode": preimport.returncode,
        "returncode": completed.returncode,
        "success_marker": "GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=SUCCESS" in output,
        "failure_marker": "GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=FAILURE" in output,
        "layers": int(layer_match.group(1)) if layer_match else None,
        "objects": int(object_match.group(1)) if object_match else None,
        "hash_rejection": "asset hash does not match" in output,
        "log_sha256": _sha256(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path)
    args = parser.parse_args()
    godot = _godot_path(args.godot)
    if not godot.is_file():
        raise RuntimeError("the requested Godot executable is not a regular file")
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-dtrace-stage5-godot-") as temp:
        temporary_root = Path(temp)
        project = temporary_root / "godot-project"
        (project / "addons/neoeng_d_trace").mkdir(parents=True)
        (project / "NeoEngGenerated").mkdir()
        (project / "assets").mkdir()
        (project / "tools").mkdir()
        (project / "project.godot").write_text(
            '[application]\nconfig/name="NeoEng Stage 5 Fixture"\n',
            encoding="utf-8",
            newline="\n",
        )
        shutil.copytree(IMPORTER, project / "addons/neoeng_d_trace", dirs_exist_ok=True)
        shutil.copy2(
            VALIDATOR, project / "tools/godot_professional_scene_stage5_validator.gd"
        )
        image = Image.new("RGBA", (8, 8), (30, 80, 120, 255))
        asset = project / "assets/hero.png"
        image.save(asset)
        document = _document(asset)
        export = project / "NeoEngGenerated/scene-authoring.godot.json"
        save_scene_authoring_export(document, export, target="godot")
        shutil.copy2(asset, OUT / "hero.png")
        shutil.copy2(export, OUT / "scene-authoring.godot.json")
        negative_project = temporary_root / "godot-project-negative"
        shutil.copytree(project, negative_project)
        (negative_project / "assets/hero.png").write_bytes(b"tampered after export")
        positive_run = _run(godot, project, temporary_root, "positive")
        negative_run = _run(godot, negative_project, temporary_root, "negative-hash")
        report = {
            "schema_version": 1,
            "engine": "godot",
            "engine_version": subprocess.run(
                [str(godot), "--version"], capture_output=True, text=True, check=True
            ).stdout.strip(),
            "positive": positive_run,
            "negative_hash": negative_run,
            "artifacts": {
                "asset": {
                    "bytes": (OUT / "hero.png").stat().st_size,
                    "sha256": _sha256(OUT / "hero.png"),
                },
                "export": {
                    "bytes": (OUT / "scene-authoring.godot.json").stat().st_size,
                    "sha256": _sha256(OUT / "scene-authoring.godot.json"),
                },
            },
        }
    (OUT / "stage5-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if (
        positive_run["returncode"] != 0
        or not positive_run["success_marker"]
        or positive_run["layers"] != 1
        or positive_run["objects"] != 1
        or negative_run["returncode"] == 0
        or not negative_run["failure_marker"]
        or not negative_run["hash_rejection"]
    ):
        raise RuntimeError(f"Godot Stage 5 adapter audit failed: {report}")
    print("GODOT_REAL_PROFESSIONAL_SCENE_STAGE5=PASS")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
