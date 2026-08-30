#!/usr/bin/env python3
"""Materialize and render a P2D-04 professional scene in Godot and Unity."""

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

ROOT = Path(__file__).resolve().parents[1]
GODOT_IMPORTER = (
    ROOT / "integrations/godot/addons/neoeng_d_trace/professional_scene_importer.gd"
)
UNITY_EDITOR_IMPORTER = (
    ROOT
    / "integrations/unity/package/com.neoeng.dtrace/Editor/"
    "ProfessionalSceneImportGenerator.cs"
)
UNITY_METADATA = (
    ROOT
    / "integrations/unity/package/com.neoeng.dtrace/Runtime/"
    "NeoEngProfessionalSceneMetadata.cs"
)
UNITY_PARALLAX = (
    ROOT
    / "integrations/unity/package/com.neoeng.dtrace/Runtime/"
    "NeoEngProfessionalParallax.cs"
)


def _run(
    command: list[str], *, timeout: int = 900, check: bool = True
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    output = re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", completed.stdout)
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"engine command failed with {completed.returncode}:\n{output[-5000:]}"
        )
    return {
        "executable": Path(command[0]).name,
        "arguments": [
            Path(argument).name if Path(argument).is_absolute() else argument
            for argument in command[1:]
        ],
        "returncode": completed.returncode,
        "output": output,
    }


def _write_fixture(workspace: Path) -> tuple[Path, Path, Path]:
    from src.persistence.project_schema import Point3Record, PointRecord
    from src.persistence.scenario_schema import ProjectReferenceRecord
    from src.persistence.scene_authoring_io import save_scene_authoring
    from src.persistence.scene_authoring_schema import (
        AssetReferenceRecord,
        SceneAuthoringDocumentV1,
        SceneAuthoringMetadataRecord,
        SceneCameraAuthoringRecord,
        SceneGroupAuthoringRecordV2,
        SceneLayerAuthoringRecord,
        SceneParallaxLayerRecord,
        SceneTransformRecord,
        SceneObjectAuthoringRecord,
        upgrade_scene_authoring_document,
    )
    from src.exporters.scene_authoring_export import save_scene_authoring_export

    workspace.mkdir(parents=True, exist_ok=True)
    project = workspace / "scene.ndtproj"
    project.write_bytes(b"p2d-04 engine fixture project")
    asset = workspace / "assets" / "hero.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, 59, 27), fill=(37, 190, 235, 255))
    draw.polygon([(8, 24), (32, 4), (56, 24)], fill=(247, 169, 54, 255))
    image.save(asset, format="PNG")
    asset_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
    project_hash = hashlib.sha256(project.read_bytes()).hexdigest()
    v1 = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-04 asymmetric engine fixture",
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        project=ProjectReferenceRecord(sha256=project_hash),
        assets=[
            AssetReferenceRecord(
                id="hero_asset", path="assets/hero.png", sha256=asset_hash
            )
        ],
        layers=[
            SceneLayerAuthoringRecord(id="background", name="Background"),
            SceneLayerAuthoringRecord(id="foreground", name="Foreground"),
        ],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero",
                asset_id="hero_asset",
                layer_id="foreground",
                transform=SceneTransformRecord(
                    position=Point3Record(x=0.8, y=0.4, z=2.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=17.0),
                    scale=Point3Record(x=1.2, y=0.75, z=1.0),
                    pivot=PointRecord(x=0.2, y=0.8),
                    flip_x=True,
                ),
            )
        ],
        groups=[
            SceneGroupAuthoringRecordV2(
                id="hero_group", name="Hero Group", members=["hero"]
            )
        ],
    )
    document = upgrade_scene_authoring_document(v1).model_copy(
        update={
            "camera": SceneCameraAuthoringRecord(
                position=PointRecord(x=0.8, y=0.4), zoom=1.25
            ),
            "parallax_layers": [
                SceneParallaxLayerRecord(
                    layer_id="background",
                    depth=0.4,
                    translation_strength=0.7,
                    zoom_strength=0.8,
                ),
                SceneParallaxLayerRecord(
                    layer_id="foreground",
                    depth=0.2,
                    translation_strength=0.9,
                    zoom_strength=0.85,
                ),
            ],
        }
    )
    source = workspace / "scene.ndtscene.json"
    save_scene_authoring(document, source)
    godot_export = workspace / "scene.godot.runtime.json"
    unity_export = workspace / "scene.unity.runtime.json"
    save_scene_authoring_export(
        document,
        godot_export,
        target="godot",
        source_document_path=source,
    )
    save_scene_authoring_export(
        document,
        unity_export,
        target="unity",
        source_document_path=source,
    )
    return project, asset, source


def _prepare_godot(workspace: Path) -> None:
    shutil.copy2(GODOT_IMPORTER, workspace / "professional_scene_importer.gd")
    shutil.copy2(
        ROOT / "tools/godot_professional_scene_validator.gd",
        workspace / "validate_professional_scene.gd",
    )
    (workspace / "project.godot").write_text(
        "[application]\n"
        'config/name="NeoEng P2D-04 Godot Validation"\n'
        "[display]\n"
        "window/size/viewport_width=640\n"
        "window/size/viewport_height=360\n"
        "[rendering]\n"
        'renderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n',
        encoding="utf-8",
        newline="\n",
    )


def _prepare_unity(workspace: Path, executable: str) -> Path:
    project = workspace / "unity-project"
    _run(
        [
            executable,
            "-batchmode",
            "-quit",
            "-createProject",
            str(project),
            "-logFile",
            str(workspace / "unity-create.log"),
        ],
        timeout=900,
    )
    assets = project / "Assets"
    generated = assets / "NeoEngGenerated"
    generated.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        workspace / "scene.unity.runtime.json", generated / "scene-authoring.unity.json"
    )
    asset_destination = assets / "assets" / "hero.png"
    asset_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workspace / "assets" / "hero.png", asset_destination)
    runtime = assets / "NeoEngDTrace" / "Runtime"
    editor = assets / "NeoEngDTrace" / "Editor"
    runtime.mkdir(parents=True, exist_ok=True)
    editor.mkdir(parents=True, exist_ok=True)
    for source in (UNITY_METADATA, UNITY_PARALLAX):
        shutil.copy2(source, runtime / source.name)
    shutil.copy2(UNITY_EDITOR_IMPORTER, editor / UNITY_EDITOR_IMPORTER.name)
    shutil.copy2(
        ROOT / "tools/unity_professional_scene_validator.cs",
        editor / "ProfessionalSceneValidation.cs",
    )
    return project


def _validate_godot(executable: str, workspace: Path) -> list[dict[str, Any]]:
    return [
        _run(
            [
                executable,
                "--headless",
                "--editor",
                "--path",
                str(workspace),
                "--import",
            ]
        ),
        _run(
            [
                executable,
                "--path",
                str(workspace),
                "--display-driver",
                "windows",
                "--rendering-method",
                "gl_compatibility",
                "--script",
                "validate_professional_scene.gd",
            ]
        ),
    ]


def _validate_unity(executable: str, project: Path) -> dict[str, Any]:
    command = [
        executable,
        "-batchmode",
        "-force-d3d11",
        "-projectPath",
        str(project),
        "-executeMethod",
        "NeoEng.DTrace.Editor.ProfessionalSceneValidation.Run",
        "-logFile",
        str(project.parent / "unity-validation.log"),
    ]
    failed_attempts: list[dict[str, Any]] = []
    result = project / "unity-professional-validation-result.txt"
    for attempt_index in range(3):
        attempt = _run(command, timeout=1200, check=False)
        result_text = result.read_text(encoding="utf-8") if result.is_file() else ""
        if attempt["returncode"] == 0:
            attempt["output"] += result_text
            if failed_attempts:
                attempt["previous_attempts"] = failed_attempts
            return attempt
        if "P2D04_UNITY_VALIDATION=SUCCESS" not in result_text:
            raise RuntimeError(
                "Unity professional validator failed before a functional success: "
                + (result_text[-4000:] or attempt["output"][-4000:])
            )
        failed_attempts.append(
            {
                "attempt": attempt_index + 1,
                "returncode": attempt["returncode"],
                "classification": "first_boot_environment_failure_with_"
                "successful_validation",
            }
        )
    raise RuntimeError(
        "Unity professional validator kept returning a nonzero exit code after "
        "three functional-success attempts"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("godot", "unity"), required=True)
    parser.add_argument("--executable", required=True)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.work_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="neoeng-p2d04-engine-")
        workspace = Path(temporary.name)
    else:
        workspace = args.work_dir.resolve()
        if workspace.exists():
            raise FileExistsError(
                f"validation work directory already exists: {workspace}"
            )
        workspace.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "contract": "P2D-04",
        "engine": args.engine,
        "status": "FAILED",
        "fixture": "asymmetric-real-png",
    }
    try:
        project, _asset, _source = _write_fixture(workspace)
        if args.engine == "godot":
            _prepare_godot(workspace)
            commands = _validate_godot(args.executable, workspace)
            if "P2D04_GODOT_VALIDATION=SUCCESS" not in commands[-1]["output"]:
                raise RuntimeError(
                    "Godot professional validator did not emit success marker"
                )
            report["capture"] = "godot-professional-capture.png"
            report["artifacts"] = [
                "assets/hero.png",
                "godot-professional-capture.png",
            ]
        else:
            unity_project = _prepare_unity(workspace, args.executable)
            validation = _validate_unity(args.executable, unity_project)
            if "P2D04_UNITY_VALIDATION=SUCCESS" not in validation["output"]:
                result = unity_project / "unity-professional-validation-result.txt"
                details = (
                    result.read_text(encoding="utf-8")
                    if result.is_file()
                    else validation["output"]
                )
                raise RuntimeError(
                    f"Unity professional validator failed: {details[-4000:]}"
                )
            commands = [validation]
            report["capture"] = "unity-professional-capture.png"
            report["artifacts"] = [
                "Assets/assets/hero.png",
                "unity-professional-capture.png",
                "unity-professional-validation-result.txt",
            ]
        report["status"] = "SUCCESS"
        version_match = re.search(
            rf"P2D04_{args.engine.upper()}_VERSION=([^\r\n]+)",
            "\n".join(command["output"] for command in commands),
        )
        report["engine_version"] = (
            version_match.group(1) if version_match else "unknown"
        )
        report["commands"] = commands
        exit_code = 0
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", str(exc))
        exit_code = 1
    if args.report is None:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    if temporary is not None:
        temporary.cleanup()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
