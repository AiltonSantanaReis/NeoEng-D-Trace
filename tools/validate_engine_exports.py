#!/usr/bin/env python3
"""Generate and validate real exporter outputs in declared target engines."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from pygltflib import GLTF2

ROOT = Path(__file__).resolve().parents[1]
UNITY_GLTF_PACKAGE = "com.unity.cloud.gltfast=6.19.0"
PROBE_ID = "sprite_ação"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _fixture_scene() -> Any:
    from src.models.scene import Scene

    scene = Scene()
    scene.add_object(PROBE_ID, [(100, 50), (140, 50), (140, 70), (100, 70)])
    scene.collision_shapes[PROBE_ID] = [
        (100, 50),
        (140, 50),
        (140, 70),
        (100, 70),
    ]
    return scene


def _write_source_image(path: Path) -> None:
    image = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 50, 139, 69), fill=(30, 180, 240, 255))
    image.save(path, format="PNG")


def _write_fixture(
    directory: Path,
    profile: str,
    fixture_dir: Path | None = None,
) -> dict[str, Path]:
    from src.exporters.gltf_exporter import export_scene_to_gltf
    from src.exporters.json_exporter import export_metadata, save_json_metadata

    directory.mkdir(parents=True, exist_ok=True)
    image_path = directory / "source.png"
    metadata_path = directory / f"probe-{profile}.json"
    glb_path = directory / "scene.glb"
    if fixture_dir is None:
        scene = _fixture_scene()
        _write_source_image(image_path)
        save_json_metadata(
            export_metadata(PROBE_ID, scene, "", profile=profile),
            str(metadata_path),
        )
        if not export_scene_to_gltf(scene, str(glb_path)):
            raise RuntimeError("GLB exporter reported failure")
    else:
        fixture_dir = fixture_dir.resolve()
        sources = {
            image_path: fixture_dir / image_path.name,
            metadata_path: fixture_dir / metadata_path.name,
            glb_path: fixture_dir / glb_path.name,
        }
        for destination, source in sources.items():
            if not source.is_file():
                raise FileNotFoundError(f"external fixture file missing: {source.name}")
            shutil.copy2(source, destination)

    document = GLTF2().load(str(glb_path))
    if document.asset is None or document.asset.version != "2.0":
        raise RuntimeError("external GLB structure validation failed")
    if not document.meshes or not document.nodes:
        raise RuntimeError("external GLB geometry validation failed")
    return {"image": image_path, "metadata": metadata_path, "glb": glb_path}


def _run(command: list[str], timeout: int = 240, check: bool = True) -> dict[str, Any]:
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
    output = completed.stdout
    portable_output = re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", output)
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"engine command failed with {completed.returncode}:\n"
            f"{portable_output[-4000:]}"
        )
    return {
        "executable": Path(command[0]).name,
        "arguments": [
            Path(argument).name if Path(argument).is_absolute() else argument
            for argument in command[1:]
        ],
        "returncode": completed.returncode,
        "output": portable_output,
    }


def _resolve_executable(engine: str, requested: str | None) -> str:
    candidate = requested or shutil.which(engine)
    if not candidate or not Path(candidate).is_file():
        raise FileNotFoundError(f"{engine} executable not found")
    return str(Path(candidate).resolve())


def _prepare_godot(workspace: Path, fixture_dir: Path | None = None) -> dict[str, Path]:
    files = _write_fixture(workspace, "godot", fixture_dir)
    shutil.copy2(
        ROOT / "tools" / "godot_engine_validator.gd", workspace / "validate.gd"
    )
    (workspace / "project.godot").write_text(
        '[application]\nconfig/name="EngineExportValidation"\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
        encoding="utf-8",
    )
    return files


def _validate_godot(executable: str, workspace: Path) -> list[dict[str, Any]]:
    commands = [
        [executable, "--headless", "--editor", "--path", str(workspace), "--import"],
        [
            executable,
            "--headless",
            "--path",
            str(workspace),
            "--script",
            "validate.gd",
        ],
    ]
    results = [_run(command) for command in commands]
    if "ENGINE_VALIDATION=SUCCESS" not in results[-1]["output"]:
        raise RuntimeError("Godot validator did not emit its success marker")
    return results


def _prepare_unity(project: Path, fixture_dir: Path | None = None) -> dict[str, Path]:
    assets = project / "Assets"
    files = _write_fixture(assets, "unity", fixture_dir)
    editor = assets / "Editor"
    editor.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "tools" / "unity_engine_validator.cs",
        editor / "EngineExportValidator.cs",
    )
    return files


def _add_unity_package(project: Path, package: str) -> None:
    if "=" not in package:
        raise ValueError("Unity package must use NAME=VERSION")
    name, version = package.split("=", 1)
    manifest_path = project / "Packages" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("dependencies", {})[name] = version
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _validate_unity(
    executable: str,
    workspace: Path,
    package: str | None,
    fixture_dir: Path | None = None,
) -> list[dict[str, Any]]:
    project = workspace / "unity-project"
    create_log = workspace / "unity-create.log"
    create = _run(
        [
            executable,
            "-batchmode",
            "-nographics",
            "-quit",
            "-createProject",
            str(project),
            "-logFile",
            str(create_log),
        ],
        timeout=600,
        check=False,
    )
    commands = [create]
    if create["returncode"] != 0 and (project / "Assets").is_dir():
        retry_log = workspace / "unity-create-retry.log"
        commands.append(
            _run(
                [
                    executable,
                    "-batchmode",
                    "-nographics",
                    "-quit",
                    "-projectPath",
                    str(project),
                    "-logFile",
                    str(retry_log),
                ],
                timeout=600,
            )
        )
    elif create["returncode"] != 0:
        raise RuntimeError(f"Unity project creation failed with {create['returncode']}")
    if not (project / "Assets").is_dir() or not (project / "ProjectSettings").is_dir():
        raise RuntimeError("Unity reported success without creating a complete project")
    _prepare_unity(project, fixture_dir)
    if package:
        _add_unity_package(project, package)
    validation_log = workspace / "unity-validation.log"
    validate = _run(
        [
            executable,
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            "EngineExportValidator.Run",
            "-logFile",
            str(validation_log),
        ],
        timeout=900,
    )
    result_path = project / "engine-validation-result.txt"
    if not result_path.is_file():
        raise RuntimeError("Unity validator did not write a result file")
    result = result_path.read_text(encoding="utf-8")
    if "ENGINE_VALIDATION=SUCCESS" not in result:
        raise RuntimeError(f"Unity validator failed:\n{result}")
    validate["output"] += result
    commands.append(validate)
    return commands


def _write_report(path: Path | None, report: dict[str, Any]) -> None:
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if path is None:
        print(serialized, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("godot", "unity"), required=True)
    parser.add_argument("--executable")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--unity-package", default=UNITY_GLTF_PACKAGE)
    parser.add_argument("--fixture-dir", type=Path)
    args = parser.parse_args()

    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.work_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="neoeng-engine-validation-")
        workspace = Path(temporary.name)
    else:
        workspace = args.work_dir.resolve()
        workspace.mkdir(parents=True, exist_ok=False)

    report: dict[str, Any] = {
        "schema_version": 1,
        "engine": args.engine,
        "status": "FAILED",
        "checks": ["metadata", "texture", "collision", "glb-external", "glb-engine"],
    }
    if args.engine == "unity":
        report["unity_package"] = args.unity_package
    report["fixture_origin"] = (
        "external-release" if args.fixture_dir is not None else "source-harness"
    )
    if args.fixture_dir is not None:
        fixture_dir = args.fixture_dir.resolve()
        report["fixture_files"] = {
            path.name: {
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(fixture_dir.iterdir())
            if path.is_file()
        }
    try:
        if args.engine == "godot":
            _prepare_godot(workspace, args.fixture_dir)
            project = workspace
        else:
            project = workspace / "unity-project"
            if args.prepare_only:
                project.mkdir(parents=True)
                _prepare_unity(project, args.fixture_dir)
        if args.prepare_only:
            report["status"] = "PREPARED_NOT_VALIDATED"
            report["project"] = project.name
        else:
            executable = _resolve_executable(args.engine, args.executable)
            if args.engine == "godot":
                commands = _validate_godot(executable, workspace)
            else:
                commands = _validate_unity(
                    executable,
                    workspace,
                    args.unity_package,
                    args.fixture_dir,
                )
            report["status"] = "SUCCESS"
            report["commands"] = commands
        _write_report(args.report, report)
        return 0
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        _write_report(args.report, report)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
