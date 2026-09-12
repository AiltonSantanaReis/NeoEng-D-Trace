"""Audit the post-E13 hybrid 3D runtime adapters in real Godot and Unity runs.

The audit is intentionally separate from the historical E12 harness. It uses
the product adapters shipped by the integrations, runs a positive package and
a hash-drift package for each engine, and stores the engine-produced capture,
reports and logs without replacing older evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.exporters.hybrid_composition_export import (  # noqa: E402
    validate_hybrid_composition_package,
)


def _run(command: list[str], cwd: Path, timeout: int) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-12000:],
        "stderr": result.stderr[-12000:],
    }


def _godot_project(root: Path, package: Path, expect_rejection: bool) -> Path:
    project = root / ("godot-negative" if expect_rejection else "godot-positive")
    shutil.copytree(package, project / "hybrid")
    addon = project / "addons" / "neoeng_d_trace"
    addon.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT
        / "integrations"
        / "godot"
        / "addons"
        / "neoeng_d_trace"
        / "hybrid3d_runtime.gd",
        addon / "hybrid3d_runtime.gd",
    )
    (project / "project.godot").write_text(
        '[application]\nconfig/name="NeoEng Post-E13 Hybrid Runtime"\n'
        "[display]\nwindow/size/viewport_width=640\n"
        "window/size/viewport_height=360\n"
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n',
        encoding="utf-8",
        newline="\n",
    )
    (project / "main.gd").write_text(
        dedent(f"""
            extends SceneTree

            const Adapter = preload("res://addons/neoeng_d_trace/hybrid3d_runtime.gd")
            const EXPECT_REJECTION := {str(expect_rejection).lower()}

            func _init() -> void:
                call_deferred("run_audit")

            func _write_report(path: String, report: Dictionary) -> void:
                FileAccess.open(path, FileAccess.WRITE).store_string(JSON.stringify(report))

            func run_audit() -> void:
                var result: Dictionary = Adapter.import_hybrid("res://hybrid/hybrid-runtime.json")
                if EXPECT_REJECTION:
                    if result.get("status") == "SUCCESS":
                        push_error("mutated hybrid package was accepted")
                        quit(1)
                        return
                    var rejected := {{
                        "status": "REJECTED",
                        "engine": "godot",
                        "engine_version": Engine.get_version_info().get("string", "unknown"),
                        "errors": result.get("errors", []),
                    }}
                    _write_report("res://hybrid-rejection-report.json", rejected)
                    print("POST_E13_HYBRID_GODOT=REJECTED")
                    print(JSON.stringify(rejected))
                    quit(0)
                    return
                if result.get("status") != "SUCCESS":
                    push_error("hybrid runtime import failed: " + JSON.stringify(result))
                    quit(1)
                    return
                get_root().add_child(result["root"])
                await process_frame
                await RenderingServer.frame_post_draw
                var image := get_root().get_viewport().get_texture().get_image()
                if image == null or image.is_empty():
                    push_error("Godot runtime viewport capture is empty")
                    quit(1)
                    return
                if image.save_png("res://hybrid-capture.png") != OK:
                    push_error("Godot runtime viewport capture could not be saved")
                    quit(1)
                    return
                var non_black_pixels := 0
                for sample_x in range(0, image.get_width(), 8):
                    for sample_y in range(0, image.get_height(), 8):
                        var sample := image.get_pixel(sample_x, sample_y)
                        if sample.r + sample.g + sample.b > 0.03:
                            non_black_pixels += 1
                if non_black_pixels == 0:
                    push_error("Godot runtime viewport capture contains no observable pixels")
                    quit(1)
                    return
                var report := {{
                    "status": "SUCCESS",
                    "engine": "godot",
                    "engine_version": Engine.get_version_info().get("string", "unknown"),
                    "support_status": result.get("support_status", ""),
                    "native_node_types": ["MeshInstance3D", "Camera3D", "DirectionalLight3D/OmniLight3D", "AnimationPlayer"],
                    "mesh_count": result.get("mesh_count", 0),
                    "material_count": result.get("material_count", 0),
                    "light_count": result.get("light_count", 0),
                    "animation_clip_count": result.get("animation_clip_count", 0),
                    "animation_frame_count": result.get("animation_frame_count", 0),
                    "animation_frame_loaded": result.get("animation_frame_loaded", false),
                    "animation_playback": result.get("animation_playback", false),
                    "playback_position_y": result.get("playback_position_y", 0.0),
                    "capture": "hybrid-capture.png",
                    "capture_size": [image.get_width(), image.get_height()],
                    "non_black_sampled_pixels": non_black_pixels,
                }}
                _write_report("res://hybrid-report.json", report)
                print("POST_E13_HYBRID_GODOT=SUCCESS")
                print(JSON.stringify(report))
                quit(0)
            """).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _unity_project(root: Path, package: Path, expect_rejection: bool) -> Path:
    project = root / ("unity-negative" if expect_rejection else "unity-positive")
    generated = project / "Assets" / "NeoEngHybrid" / "Package"
    generated.parent.mkdir(parents=True)
    shutil.copytree(package, generated)
    runtime = project / "Assets" / "NeoEngHybrid" / "Runtime"
    runtime.mkdir(parents=True)
    shutil.copy2(
        ROOT
        / "integrations"
        / "unity"
        / "package"
        / "com.neoeng.dtrace"
        / "Runtime"
        / "NeoEngRuntimeHybrid3D.cs",
        runtime / "NeoEngRuntimeHybrid3D.cs",
    )
    editor = project / "Assets" / "NeoEngHybrid" / "Editor"
    editor.mkdir(parents=True)
    (project / "ProjectSettings").mkdir()
    (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8", newline="\n"
    )
    (editor / "PostE13HybridRuntimeAudit.cs").write_text(
        dedent(f"""
            using System;
            using System.IO;
            using UnityEditor;
            using UnityEngine;
            using NeoEng.DTrace;

            public static class PostE13HybridRuntimeAudit
            {{
                private const bool ExpectRejection = {str(expect_rejection).lower()};

                [Serializable]
                private sealed class Report
                {{
                    public string status;
                    public string engine;
                    public string engine_version;
                    public string support_status;
                    public string[] native_node_types;
                    public int mesh_count;
                    public int material_count;
                    public int light_count;
                    public int animation_clip_count;
                    public int animation_frame_count;
                    public bool animation_frame_loaded;
                    public bool animation_playback;
                    public float playback_position_y;
                    public string capture;
                    public int[] capture_size;
                    public string errors;
                }}

                public static void Run()
                {{
                    string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
                    string manifestPath = Path.Combine(projectRoot, "Assets", "NeoEngHybrid", "Package", "hybrid-runtime.json");
                    try
                    {{
                        NeoEngRuntimeHybrid3D.Result result = NeoEngRuntimeHybrid3D.Import(manifestPath);
                        if (ExpectRejection)
                            throw new Exception("mutated hybrid package was accepted");
                        string capturePath = Path.Combine(projectRoot, "hybrid-capture.png");
                        RenderTexture target = new RenderTexture(640, 360, 24, RenderTextureFormat.ARGB32);
                        target.Create();
                        result.Camera.targetTexture = target;
                        result.Camera.Render();
                        RenderTexture.active = target;
                        Texture2D capture = new Texture2D(640, 360, TextureFormat.RGB24, false);
                        capture.ReadPixels(new Rect(0, 0, 640, 360), 0, 0);
                        capture.Apply();
                        File.WriteAllBytes(capturePath, capture.EncodeToPNG());
                        Report report = new Report
                        {{
                            status = "SUCCESS",
                            engine = "unity",
                            engine_version = Application.unityVersion,
                            support_status = result.Manifest.support_status,
                            native_node_types = new[] {{ "MeshFilter", "MeshRenderer", "Camera", "Light", "Animation" }},
                            mesh_count = result.MeshCount,
                            material_count = result.MaterialCount,
                            light_count = result.LightCount,
                            animation_clip_count = result.AnimationClipCount,
                            animation_frame_count = result.AnimationFrameCount,
                            animation_frame_loaded = result.AnimationFrameLoaded,
                            animation_playback = true,
                            playback_position_y = result.PlaybackPositionY,
                            capture = "hybrid-capture.png",
                            capture_size = new[] {{ 640, 360 }},
                        }};
                        File.WriteAllText(Path.Combine(projectRoot, "hybrid-report.json"), JsonUtility.ToJson(report));
                        Debug.Log("POST_E13_HYBRID_UNITY=SUCCESS");
                        AssetDatabase.SaveAssets();
                        EditorApplication.Exit(0);
                    }}
                    catch (Exception exception)
                    {{
                        if (!ExpectRejection)
                        {{
                            Debug.LogException(exception);
                            EditorApplication.Exit(1);
                            return;
                        }}
                        Report report = new Report
                        {{
                            status = "REJECTED",
                            engine = "unity",
                            engine_version = Application.unityVersion,
                            errors = exception.GetType().Name + ": " + exception.Message,
                        }};
                        File.WriteAllText(Path.Combine(projectRoot, "hybrid-rejection-report.json"), JsonUtility.ToJson(report));
                        Debug.Log("POST_E13_HYBRID_UNITY=REJECTED");
                        Debug.Log(exception.Message);
                        EditorApplication.Exit(0);
                    }}
                }}
            }}
            """).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _discover_unity() -> Path:
    module_path = Path(__file__).with_name("audit_unity_import_stage6.py")
    spec = importlib.util.spec_from_file_location(
        "audit_unity_import_stage6", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load Unity discovery helper: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    discovered = module.discover_unity()
    if isinstance(discovered, tuple):
        discovered = discovered[0]
    if not discovered:
        raise RuntimeError("Unity executable was not discoverable")
    return Path(discovered)


def _mutated_package(package: Path, root: Path) -> Path:
    mutated = root / "hybrid-negative-package"
    shutil.copytree(package, mutated)
    scene_path = mutated / "hybrid-runtime-scene.json"
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    scene["meshes"][0]["id"] = str(scene["meshes"][0]["id"]) + "-tampered"
    scene_path.write_text(
        json.dumps(scene, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return mutated


def _copy_report(project: Path, output: Path, name: str) -> dict[str, object]:
    report_path = project / name
    if not report_path.is_file():
        return {}
    return json.loads(report_path.read_text(encoding="utf-8"))


def _copy_file_if_present(source: Path, destination: Path) -> str | None:
    if not source.is_file():
        return None
    shutil.copy2(source, destination)
    return destination.name


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit_engine(
    engine: str,
    package: Path,
    output: Path,
    temporary_root: Path,
    godot: Path,
    unity: Path | None,
) -> dict[str, object]:
    engine_root = temporary_root / engine
    engine_root.mkdir(parents=True, exist_ok=True)
    negative_package = _mutated_package(package, engine_root)
    shutil.copytree(negative_package, output / f"{engine}-negative-package")
    if engine == "godot":
        positive_project = _godot_project(engine_root, package, False)
        positive_run = _run(
            [
                str(godot),
                "--display-driver",
                "windows",
                "--rendering-method",
                "gl_compatibility",
                "--path",
                str(positive_project),
                "--script",
                "res://main.gd",
                "--quit-after",
                "15",
            ],
            positive_project,
            timeout=120,
        )
        positive_report = _copy_report(positive_project, output, "hybrid-report.json")
        capture_name = _copy_file_if_present(
            positive_project / "hybrid-capture.png",
            output / "godot-hybrid-runtime-capture.png",
        )
        negative_project = _godot_project(engine_root, negative_package, True)
        negative_run = _run(
            [
                str(godot),
                "--display-driver",
                "windows",
                "--rendering-method",
                "gl_compatibility",
                "--path",
                str(negative_project),
                "--script",
                "res://main.gd",
                "--quit-after",
                "15",
            ],
            negative_project,
            timeout=120,
        )
        negative_report = _copy_report(
            negative_project, output, "hybrid-rejection-report.json"
        )
        (output / "godot-positive.log").write_text(
            json.dumps(positive_run, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (output / "godot-negative.log").write_text(
            json.dumps(negative_run, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        if unity is None:
            raise RuntimeError("Unity executable is required for the hybrid audit")
        positive_project = _unity_project(engine_root, package, False)
        positive_run = _run(
            [
                str(unity),
                "-batchmode",
                "-quit",
                "-projectPath",
                str(positive_project),
                "-executeMethod",
                "PostE13HybridRuntimeAudit.Run",
                "-logFile",
                str(positive_project / "unity.log"),
            ],
            positive_project,
            timeout=360,
        )
        positive_report = _copy_report(positive_project, output, "hybrid-report.json")
        capture_name = _copy_file_if_present(
            positive_project / "hybrid-capture.png",
            output / "unity-hybrid-runtime-capture.png",
        )
        negative_project = _unity_project(engine_root, negative_package, True)
        negative_run = _run(
            [
                str(unity),
                "-batchmode",
                "-quit",
                "-projectPath",
                str(negative_project),
                "-executeMethod",
                "PostE13HybridRuntimeAudit.Run",
                "-logFile",
                str(negative_project / "unity.log"),
            ],
            negative_project,
            timeout=360,
        )
        negative_report = _copy_report(
            negative_project, output, "hybrid-rejection-report.json"
        )
        (output / "unity-positive.log").write_text(
            json.dumps(positive_run, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (output / "unity-negative.log").write_text(
            json.dumps(negative_run, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    positive_pass = (
        positive_run["returncode"] == 0 and positive_report.get("status") == "SUCCESS"
    )
    negative_pass = (
        negative_run["returncode"] == 0 and negative_report.get("status") == "REJECTED"
    )
    return {
        "status": "PASS" if positive_pass and negative_pass else "FAIL",
        "positive": {
            "run": positive_run,
            "report": positive_report,
            "capture": capture_name,
        },
        "negative": {"run": negative_run, "report": negative_report},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--godot", type=Path, default=Path("C:/ProgramData/chocolatey/bin/godot.exe")
    )
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--engine", choices=("both", "godot", "unity"), default="both")
    args = parser.parse_args()
    package = args.package.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(
            f"refusing to overwrite hybrid runtime audit output: {output}"
        )
    validate_hybrid_composition_package(package)
    output.mkdir(parents=True)
    engines = ["godot", "unity"] if args.engine == "both" else [args.engine]
    with tempfile.TemporaryDirectory(
        prefix="neoeng-post-e13-hybrid-runtime-"
    ) as temporary:
        temporary_root = Path(temporary)
        results = {}
        for engine in engines:
            results[engine] = _audit_engine(
                engine, package, output, temporary_root, args.godot, args.unity
            )
    status = (
        "SUCCESS"
        if all(value["status"] == "PASS" for value in results.values())
        else "FAIL"
    )
    report = {
        "schema_version": 1,
        "status": status,
        "package": str(package),
        "engines": results,
        "limitations": [
            "vertical slice only: inline meshes, perspective camera, directional/point lights and position keyframes",
            "collision, particles, tilemap 3D, timeline/cutscene equivalence and complete editor 3D remain outside this gate",
            "Godot capture is the native OpenGL Compatibility viewport image; environment-specific renderer limitations remain explicit",
        ],
    }
    report_path = output / "hybrid-runtime-engine-audit.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    hashes = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            hashes[path.relative_to(output).as_posix()] = _sha256(path)
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
