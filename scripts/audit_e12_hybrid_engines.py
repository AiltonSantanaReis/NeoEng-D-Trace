"""Materialize and validate the E12 hybrid package in real Godot and Unity runs."""

# The script prepends the source root before importing product modules.
# flake8: noqa: E501

from __future__ import annotations

import argparse
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
        "stdout": result.stdout[-6000:],
        "stderr": result.stderr[-6000:],
    }


def _godot_project(root: Path, package: Path) -> Path:
    project = root / "godot"
    shutil.copytree(package, project / "hybrid")
    (project / "project.godot").write_text(
        '[application]\nconfig/name="NeoEng E12 Hybrid Godot"\n'
        "[display]\nwindow/size/viewport_width=640\n"
        "window/size/viewport_height=360\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "main.gd").write_text(
        dedent("""
            extends SceneTree

            func read_json(path: String) -> Dictionary:
                var value = JSON.parse_string(FileAccess.get_file_as_string(path))
                if typeof(value) != TYPE_DICTIONARY:
                    push_error("invalid JSON: " + path)
                    quit(1)
                return value

            func fail(message: String) -> void:
                push_error(message)
                quit(1)

            func _init() -> void:
                call_deferred("run_audit")

            func run_audit() -> void:
                var manifest := read_json("res://hybrid/hybrid-composition.json")
                var scene := read_json("res://hybrid/hybrid3d.json")
                var animation_manifest := read_json("res://hybrid/animation/animation.json")
                var image := Image.new()
                var image_status := image.load("res://hybrid/animation/frame_0000.png")
                if image_status != OK:
                    fail("animation frame could not be loaded")
                    return
                if manifest.get("support_status") != "VERTICAL_SLICE_ONLY":
                    fail("E12 support status is not explicit")
                    return
                var root := Node3D.new()
                root.name = "NeoEngE12Hybrid"
                get_root().add_child(root)
                var camera_data: Dictionary = scene.get("camera", {})
                var camera := Camera3D.new()
                camera.name = "PerspectiveCamera"
                camera.projection = Camera3D.PROJECTION_PERSPECTIVE
                camera.fov = float(camera_data.get("fov_degrees", 55.0))
                camera.near = float(camera_data.get("near", 0.1))
                camera.far = float(camera_data.get("far", 100.0))
                camera.position = Vector3(camera_data.get("position", [0, 0, 8])[0], camera_data.get("position", [0, 0, 8])[1], camera_data.get("position", [0, 0, 8])[2])
                camera.current = true
                root.add_child(camera)
                camera.look_at(Vector3(0, 0, 0))
                var material_by_id := {}
                for material_data in scene.get("materials", []):
                    var material := StandardMaterial3D.new()
                    material.metallic = float(material_data.get("metallic", 0.0))
                    material.roughness = float(material_data.get("roughness", 0.5))
                    var color_values = material_data.get("base_color", [0.15, 0.72, 0.95, 1.0])
                    material.albedo_color = Color(color_values[0], color_values[1], color_values[2], color_values[3])
                    material_by_id[material_data.get("id", "")] = material
                var mesh_nodes := {}
                for mesh_data in scene.get("meshes", []):
                    var vertices := PackedVector3Array()
                    for vertex in mesh_data.get("vertices", []):
                        vertices.append(Vector3(vertex[0], vertex[1], vertex[2]))
                    var indices := PackedInt32Array()
                    for triangle in mesh_data.get("triangles", []):
                        indices.append(int(triangle[0]))
                        indices.append(int(triangle[1]))
                        indices.append(int(triangle[2]))
                    var arrays := []
                    arrays.resize(Mesh.ARRAY_MAX)
                    arrays[Mesh.ARRAY_VERTEX] = vertices
                    arrays[Mesh.ARRAY_INDEX] = indices
                    var array_mesh := ArrayMesh.new()
                    array_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
                    var mesh_node := MeshInstance3D.new()
                    mesh_node.name = str(mesh_data.get("id", "Mesh"))
                    mesh_node.mesh = array_mesh
                    var position = mesh_data.get("position", [0, 0, 0])
                    mesh_node.position = Vector3(position[0], position[1], position[2])
                    mesh_node.set_surface_override_material(0, material_by_id.get(mesh_data.get("material_id", "")))
                    root.add_child(mesh_node)
                    mesh_nodes[mesh_node.name] = mesh_node
                for light_data in scene.get("lights", []):
                    var light: Light3D
                    if light_data.get("type") == "point":
                        light = OmniLight3D.new()
                    else:
                        light = DirectionalLight3D.new()
                    light.name = str(light_data.get("id", "Light"))
                    light.light_energy = float(light_data.get("intensity", 1.0))
                    root.add_child(light)
                var player := AnimationPlayer.new()
                var library := AnimationLibrary.new()
                for clip_data in scene.get("animation_clips", []):
                    var clip := Animation.new()
                    var track := clip.add_track(Animation.TYPE_POSITION_3D)
                    var mesh_id := str(clip_data.get("mesh_id", ""))
                    clip.track_set_path(track, NodePath(mesh_id + ":position"))
                    for keyframe in clip_data.get("keyframes", []):
                        var point = keyframe.get("position", [0, 0, 0])
                        clip.track_insert_key(track, float(keyframe.get("time", 0.0)), Vector3(point[0], point[1], point[2]))
                    clip.length = float(clip_data.get("keyframes", [])[-1].get("time", 1.0))
                    library.add_animation(str(clip_data.get("id", "clip")), clip)
                player.add_animation_library("", library)
                root.add_child(player)
                var first_clip = scene.get("animation_clips", [])[0]
                var clip_name := str(first_clip.get("id", "clip"))
                player.play(clip_name)
                player.advance(0.5)
                var first_mesh = mesh_nodes.get(str(first_clip.get("mesh_id", "")))
                if first_mesh == null or not is_finite(first_mesh.position.y):
                    fail("animation playback did not produce a finite position")
                    return
                await process_frame
                var capture_path := ""
                var report := {
                    "status": "SUCCESS",
                    "engine": "godot",
                    "engine_version": Engine.get_version_info().get("string", "unknown"),
                    "asset_loaded": true,
                    "camera_projection": "perspective",
                    "mesh_count": scene.get("meshes", []).size(),
                    "material_count": scene.get("materials", []).size(),
                    "light_count": scene.get("lights", []).size(),
                    "animation_clip_count": scene.get("animation_clips", []).size(),
                    "animation_frame_count": animation_manifest.get("frame_count", 0),
                    "animation_playback": true,
                    "playback_position_y": first_mesh.position.y,
                    "capture": capture_path,
                }
                FileAccess.open("res://e12-hybrid-report.json", FileAccess.WRITE).store_string(JSON.stringify(report))
                print("E12_HYBRID_GODOT=SUCCESS")
                print(JSON.stringify(report))
                quit(0)
            """).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _unity_project(root: Path, package: Path) -> Path:
    project = root / "unity"
    generated = project / "Assets" / "NeoEngHybrid" / "Package"
    generated.parent.mkdir(parents=True)
    shutil.copytree(package, generated)
    editor = project / "Assets" / "NeoEngHybrid" / "Editor"
    editor.mkdir(parents=True)
    (project / "ProjectSettings").mkdir()
    (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8", newline="\n"
    )
    (editor / "E12HybridAudit.cs").write_text(
        dedent("""
            using System;
            using System.IO;
            using System.Text.Json;
            using UnityEditor;
            using UnityEngine;

            public static class E12HybridAudit
            {
                [Serializable] private class AnimationDoc { public int frame_count; }
                [Serializable] private class ReportDoc { public string status; public string engine; public string engine_version; public bool asset_loaded; public string camera_projection; public int mesh_count; public int material_count; public int light_count; public int animation_clip_count; public int animation_frame_count; public bool animation_playback; public float playback_position_y; public string capture; }

                private static Vector3 Point(JsonElement value) { return new Vector3((float)value[0].GetDouble(), (float)value[1].GetDouble(), (float)value[2].GetDouble()); }

                public static void Run()
                {
                    try
                    {
                        string root = "Assets/NeoEngHybrid/Package";
                        string hybridJson = File.ReadAllText(root + "/hybrid3d.json");
                        using JsonDocument sceneDocument = JsonDocument.Parse(hybridJson);
                        JsonElement scene = sceneDocument.RootElement;
                        AnimationDoc animation = JsonUtility.FromJson<AnimationDoc>(File.ReadAllText(root + "/animation/animation.json"));
                        JsonElement cameraDoc = scene.GetProperty("camera");
                        if (scene.GetProperty("support_status").GetString() != "VERTICAL_SLICE_ONLY" || cameraDoc.GetProperty("projection").GetString() != "perspective") throw new Exception("hybrid scene contract is invalid");
                        byte[] textureBytes = File.ReadAllBytes(root + "/animation/frame_0000.png");
                        Texture2D texture = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                        if (!texture.LoadImage(textureBytes)) throw new Exception("animation asset could not be decoded");
                        GameObject rootObject = new GameObject("NeoEngE12Hybrid");
                        GameObject cameraObject = new GameObject("PerspectiveCamera");
                        cameraObject.transform.SetParent(rootObject.transform, false);
                        Camera camera = cameraObject.AddComponent<Camera>();
                        camera.orthographic = false;
                        camera.fieldOfView = (float)cameraDoc.GetProperty("fov_degrees").GetDouble();
                        camera.nearClipPlane = (float)cameraDoc.GetProperty("near").GetDouble();
                        camera.farClipPlane = (float)cameraDoc.GetProperty("far").GetDouble();
                        camera.transform.position = Point(cameraDoc.GetProperty("position"));
                        camera.transform.LookAt(Vector3.zero);
                        JsonElement materialsDoc = scene.GetProperty("materials");
                        Material[] materials = new Material[materialsDoc.GetArrayLength()];
                        for (int index = 0; index < materials.Length; index++)
                        {
                            JsonElement source = materialsDoc[index];
                            Material material = new Material(Shader.Find("Standard"));
                            material.name = source.GetProperty("id").GetString();
                            material.SetFloat("_Metallic", (float)source.GetProperty("metallic").GetDouble());
                            material.SetFloat("_Glossiness", 1f - (float)source.GetProperty("roughness").GetDouble());
                            materials[index] = material;
                        }
                        JsonElement meshesDoc = scene.GetProperty("meshes");
                        GameObject[] meshes = new GameObject[meshesDoc.GetArrayLength()];
                        for (int index = 0; index < meshes.Length; index++)
                        {
                            JsonElement source = meshesDoc[index];
                            GameObject meshObject = new GameObject(source.GetProperty("id").GetString());
                            meshObject.transform.SetParent(rootObject.transform, false);
                            meshObject.transform.localPosition = Point(source.GetProperty("position"));
                            Mesh mesh = new Mesh();
                            JsonElement verticesDoc = source.GetProperty("vertices");
                            Vector3[] vertices = new Vector3[verticesDoc.GetArrayLength()];
                            for (int vertex = 0; vertex < vertices.Length; vertex++) vertices[vertex] = Point(verticesDoc[vertex]);
                            JsonElement trianglesDoc = source.GetProperty("triangles");
                            int[] triangles = new int[trianglesDoc.GetArrayLength() * 3];
                            for (int triangle = 0; triangle < trianglesDoc.GetArrayLength(); triangle++)
                            {
                                triangles[triangle * 3] = trianglesDoc[triangle][0].GetInt32();
                                triangles[triangle * 3 + 1] = trianglesDoc[triangle][1].GetInt32();
                                triangles[triangle * 3 + 2] = trianglesDoc[triangle][2].GetInt32();
                            }
                            mesh.vertices = vertices;
                            mesh.triangles = triangles;
                            mesh.RecalculateNormals();
                            meshObject.AddComponent<MeshFilter>().sharedMesh = mesh;
                            MeshRenderer renderer = meshObject.AddComponent<MeshRenderer>();
                            for (int material = 0; material < materials.Length; material++) if (materialsDoc[material].GetProperty("id").GetString() == source.GetProperty("material_id").GetString()) renderer.sharedMaterial = materials[material];
                            meshes[index] = meshObject;
                        }
                        JsonElement lightsDoc = scene.GetProperty("lights");
                        foreach (JsonElement source in lightsDoc.EnumerateArray())
                        {
                            GameObject lightObject = new GameObject(source.GetProperty("id").GetString());
                            lightObject.transform.SetParent(rootObject.transform, false);
                            Light light = lightObject.AddComponent<Light>();
                            light.type = source.GetProperty("type").GetString() == "point" ? LightType.Point : LightType.Directional;
                            light.intensity = (float)source.GetProperty("intensity").GetDouble();
                            lightObject.transform.position = Point(source.GetProperty("position"));
                        }
                        JsonElement clipsDoc = scene.GetProperty("animation_clips");
                        JsonElement clipSource = clipsDoc[0];
                        GameObject animated = GameObject.Find(clipSource.GetProperty("mesh_id").GetString());
                        if (animated == null) throw new Exception("animated mesh is missing");
                        AnimationClip clip = new AnimationClip();
                        clip.name = clipSource.GetProperty("id").GetString();
                        clip.legacy = true;
                        JsonElement keyframesDoc = clipSource.GetProperty("keyframes");
                        UnityEngine.Keyframe[] keys = new UnityEngine.Keyframe[keyframesDoc.GetArrayLength()];
                        for (int key = 0; key < keys.Length; key++) keys[key] = new UnityEngine.Keyframe((float)keyframesDoc[key].GetProperty("time").GetDouble(), (float)keyframesDoc[key].GetProperty("position")[1].GetDouble());
                        clip.SetCurve("", typeof(Transform), "localPosition.y", new AnimationCurve(keys));
                        Animation animationPlayer = animated.AddComponent<Animation>();
                        animationPlayer.AddClip(clip, clip.name);
                        animationPlayer.Play(clip.name);
                        animationPlayer[clip.name].time = 0.5f;
                        animationPlayer.Sample();
                        if (float.IsNaN(animated.transform.localPosition.y) || float.IsInfinity(animated.transform.localPosition.y)) throw new Exception("animation playback is not finite");
                        string capturePath = Path.GetFullPath("e12-hybrid-capture.png");
                        RenderTexture target = new RenderTexture(640, 360, 24);
                        camera.targetTexture = target;
                        camera.Render();
                        RenderTexture.active = target;
                        Texture2D capture = new Texture2D(640, 360, TextureFormat.RGB24, false);
                        capture.ReadPixels(new Rect(0, 0, 640, 360), 0, 0);
                        capture.Apply();
                        File.WriteAllBytes(capturePath, capture.EncodeToPNG());
                        ReportDoc report = new ReportDoc { status = "SUCCESS", engine = "unity", engine_version = "6000.5.7f1", asset_loaded = true, camera_projection = "perspective", mesh_count = meshes.Length, material_count = materials.Length, light_count = lightsDoc.GetArrayLength(), animation_clip_count = clipsDoc.GetArrayLength(), animation_frame_count = animation.frame_count, animation_playback = true, playback_position_y = animated.transform.localPosition.y, capture = "e12-hybrid-capture.png" };
                        File.WriteAllText("e12-hybrid-report.json", JsonUtility.ToJson(report));
                        Debug.Log("E12_HYBRID_UNITY=SUCCESS");
                        AssetDatabase.SaveAssets();
                        EditorApplication.Exit(0);
                    }
                    catch (Exception exception)
                    {
                        Debug.LogException(exception);
                        EditorApplication.Exit(1);
                    }
                }
            }
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
        raise FileExistsError(f"refusing to overwrite E12 audit output: {output}")
    validate_hybrid_composition_package(package)
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-e12-engine-") as temporary:
        temporary_root = Path(temporary)
        if args.engine in {"both", "godot"}:
            godot_project = _godot_project(temporary_root, package)
            godot_run = _run(
                [
                    str(args.godot),
                    "--headless",
                    "--path",
                    str(godot_project),
                    "--script",
                    "res://main.gd",
                    "--quit-after",
                    "15",
                ],
                godot_project,
                timeout=90,
            )
            report_path = godot_project / "e12-hybrid-report.json"
            if report_path.is_file():
                shutil.copy2(report_path, output / "e12-hybrid-godot-report.json")
                godot_run["hybrid_report"] = json.loads(
                    report_path.read_text(encoding="utf-8")
                )
                godot_run["hybrid_success"] = (
                    godot_run["hybrid_report"].get("status") == "SUCCESS"
                )
            capture = godot_project / "e12-hybrid-capture.png"
            if capture.is_file():
                shutil.copy2(capture, output / "e12-hybrid-godot-capture.png")
        else:
            godot_run = {"returncode": 0, "status": "NOT_RUN"}
        if args.engine in {"both", "unity"}:
            unity = args.unity or _discover_unity()
            unity_project = _unity_project(temporary_root, package)
            unity_run = _run(
                [
                    str(unity),
                    "-batchmode",
                    "-quit",
                    "-projectPath",
                    str(unity_project),
                    "-executeMethod",
                    "E12HybridAudit.Run",
                    "-logFile",
                    str(unity_project / "unity.log"),
                ],
                unity_project,
                timeout=300,
            )
            report_path = unity_project / "e12-hybrid-report.json"
            if report_path.is_file():
                shutil.copy2(report_path, output / "e12-hybrid-unity-report.json")
                unity_run["hybrid_report"] = json.loads(
                    report_path.read_text(encoding="utf-8")
                )
                unity_run["hybrid_success"] = (
                    unity_run["hybrid_report"].get("status") == "SUCCESS"
                )
            unity_log = unity_project / "unity.log"
            if unity_log.is_file():
                shutil.copy2(unity_log, output / "unity-editor.log")
            capture = unity_project / "e12-hybrid-capture.png"
            if capture.is_file():
                shutil.copy2(capture, output / "e12-hybrid-unity-capture.png")
        else:
            unity_run = {"returncode": 0, "status": "NOT_RUN"}
    godot_pass = args.engine == "unity" or (
        godot_run["returncode"] == 0 and godot_run.get("hybrid_success", False)
    )
    unity_pass = args.engine == "godot" or (
        unity_run["returncode"] == 0 and unity_run.get("hybrid_success", False)
    )
    report = {
        "schema_version": 1,
        "package": str(package),
        "status": "SUCCESS" if godot_pass and unity_pass else "FAIL",
        "godot": godot_run,
        "unity": unity_run,
    }
    (output / "e12-engine-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
