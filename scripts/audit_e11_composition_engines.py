"""Consume one exported E11 composition package in real Godot and Unity runs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], cwd: Path, timeout: int = 180) -> dict[str, object]:
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
        "stdout": result.stdout[:2000] + result.stdout[-4000:],
        "stderr": result.stderr[:2000] + result.stderr[-4000:],
    }


def _godot_project(root: Path, package: Path) -> Path:
    project = root / "godot"
    (project / "composition").mkdir(parents=True)
    shutil.copytree(package, project / "composition", dirs_exist_ok=True)
    (project / "project.godot").write_text(
        '[application]\nconfig/name="NeoEng E11 Composition Godot"\n'
        "[display]\nwindow/size/viewport_width=640\n"
        "window/size/viewport_height=360\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "composition_canvas.gd").write_text(
        dedent(
            """
            extends Node2D
            var tile_count := 0
            var collider_count := 0
            var nav_count := 0

            func _draw() -> void:
                draw_rect(Rect2(0, 0, 640, 360), Color("101820"))
                draw_rect(Rect2(48, 210, 360, 34), Color("263d4c"), true)
                draw_rect(Rect2(48, 210, 360, 34), Color("5ed8ff"), false, 2.0)
                draw_circle(Vector2(230, 130), 46.0, Color("f0c630"))
                draw_circle(Vector2(230, 130), 46.0, Color("5ed8ff"), false, 3.0)
                draw_string(ThemeDB.fallback_font, Vector2(32, 42),
                    "E11 COMPOSITION | GODOT 4.7", HORIZONTAL_ALIGNMENT_LEFT,
                    -1, 22, Color("a9f2ff"))
                draw_string(ThemeDB.fallback_font, Vector2(32, 78),
                    "scene + tilemap + colliders + navmesh", HORIZONTAL_ALIGNMENT_LEFT,
                    -1, 16, Color("dbe7ef"))
                draw_string(ThemeDB.fallback_font, Vector2(32, 316),
                    "tiles: %d  colliders: %d  nav regions: %d" %
                    [tile_count, collider_count, nav_count], HORIZONTAL_ALIGNMENT_LEFT,
                    -1, 17, Color("dbe7ef"))
            """
        ).strip()
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "main.gd").write_text(
        dedent(
            """
            extends SceneTree

            func read_json(path: String) -> Dictionary:
                var value = JSON.parse_string(FileAccess.get_file_as_string(path))
                if typeof(value) != TYPE_DICTIONARY:
                    push_error("invalid JSON: " + path)
                    quit(1)
                return value

            func _init() -> void:
                var manifest := read_json("res://composition/composition.json")
                var scene := read_json("res://composition/scene-godot.runtime.json")
                var tilemap := read_json("res://composition/tilemap.json")
                var colliders := read_json("res://composition/colliders.json")
                var navmesh := read_json("res://composition/navmesh.json")
                var asset = Image.new()
                if asset.load("res://composition/assets/scene/hero.png") != OK:
                    quit(1); return
                if manifest.get("format_id") != "neoeng-d-trace-composition-package":
                    quit(1); return
                var root := Node2D.new()
                root.name = "NeoEngE11Composition"
                var scene_node := Node2D.new()
                scene_node.name = "SceneExport"
                scene_node.set_meta("objects", scene.get("scene", {}).get("objects", []).size())
                root.add_child(scene_node)
                var map_node := Node2D.new()
                map_node.name = "TileMapLayer"
                map_node.set_meta("cells", tilemap.get("cells", []).size())
                root.add_child(map_node)
                for cell in tilemap.get("cells", []):
                    var cell_node := Node2D.new()
                    cell_node.name = "TileCell_%s_%s" % [cell.get("x", 0), cell.get("y", 0)]
                    map_node.add_child(cell_node)
                var collision_node := Node2D.new()
                collision_node.name = "Colliders"
                root.add_child(collision_node)
                for collider in colliders.get("colliders", []):
                    var body := StaticBody2D.new()
                    body.name = str(collider.get("id", "Collider"))
                    body.set_meta("kind", collider.get("kind", "unknown"))
                    collision_node.add_child(body)
                var navigation := NavigationRegion2D.new()
                navigation.name = "NavigationRegion2D"
                navigation.set_meta("regions", navmesh.get("regions", []).size())
                navigation.set_meta("obstacles", navmesh.get("obstacles", []).size())
                root.add_child(navigation)
                var canvas = load("res://composition_canvas.gd").new()
                canvas.tile_count = tilemap.get("cells", []).size()
                canvas.collider_count = colliders.get("colliders", []).size()
                canvas.nav_count = navmesh.get("regions", []).size()
                root.add_child(canvas)
                get_root().add_child(root)
                var report := {
                    "status": "SUCCESS",
                    "engine": "godot",
                    "nodes": root.get_child_count(),
                    "tile_cells": map_node.get_child_count(),
                    "colliders": collision_node.get_child_count(),
                    "nav_regions": navmesh.get("regions", []).size()
                }
                var report_file = FileAccess.open("res://e11-composition-report.json", FileAccess.WRITE)
                report_file.store_string(JSON.stringify(report))
                print("E11_COMPOSITION_GODOT=SUCCESS")
                print(JSON.stringify(report))
                quit(0)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _unity_project(root: Path, package: Path) -> Path:
    project = root / "unity"
    generated = project / "Assets/NeoEngComposition"
    generated.mkdir(parents=True)
    shutil.copytree(package, generated / "Package", dirs_exist_ok=True)
    editor = project / "Assets/NeoEngComposition/Editor"
    editor.mkdir()
    (project / "ProjectSettings").mkdir()
    (project / "ProjectSettings/ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8", newline="\n"
    )
    (editor / "E11CompositionAudit.cs").write_text(
        dedent(
            """
            using System;
            using System.IO;
            using UnityEditor;
            using UnityEngine;

            public static class E11CompositionAudit
            {
                [Serializable] private class Cell { public int x; public int y; }
                [Serializable] private class Tilemap { public Cell[] cells; }
                [Serializable] private class Collider { public string id; public string kind; public bool is_trigger; public Size size; public float radius; }
                [Serializable] private class Size { public float x; public float y; }
                [Serializable] private class Colliders { public Collider[] colliders; }
                [Serializable] private class Region { public string id; public float[] bounds; }
                [Serializable] private class Navmesh { public Region[] regions; public Region[] obstacles; }

                public static void Run()
                {
                    try
                    {
                        string root = "Assets/NeoEngComposition/Package";
                        string manifest = File.ReadAllText(root + "/composition.json");
                        if (!manifest.Contains("neoeng-d-trace-composition-package")) throw new Exception("composition manifest format is invalid");
                        Tilemap tilemap = JsonUtility.FromJson<Tilemap>(File.ReadAllText(root + "/tilemap.json"));
                        Colliders colliders = JsonUtility.FromJson<Colliders>(File.ReadAllText(root + "/colliders.json"));
                        Navmesh navmesh = JsonUtility.FromJson<Navmesh>(File.ReadAllText(root + "/navmesh.json"));
                        Texture2D asset = AssetDatabase.LoadAssetAtPath<Texture2D>(root + "/assets/scene/hero.png");
                        if (asset == null) throw new Exception("composition asset could not be imported");
                        if (tilemap == null || tilemap.cells == null || colliders == null || colliders.colliders == null || navmesh == null || navmesh.regions == null)
                            throw new Exception("composition payload is incomplete");
                        GameObject rootObject = new GameObject("NeoEngE11Composition");
                        GameObject scene = new GameObject("SceneExport");
                        scene.transform.SetParent(rootObject.transform, false);
                        GameObject tileRoot = new GameObject("Tilemap");
                        tileRoot.transform.SetParent(rootObject.transform, false);
                        foreach (Cell cell in tilemap.cells)
                        {
                            GameObject tile = new GameObject("TileCell_" + cell.x + "_" + cell.y);
                            tile.transform.SetParent(tileRoot.transform, false);
                            tile.transform.localPosition = new Vector3(cell.x * 16f, cell.y * 16f, 0f);
                        }
                        GameObject colliderRoot = new GameObject("Colliders");
                        colliderRoot.transform.SetParent(rootObject.transform, false);
                        foreach (Collider source in colliders.colliders)
                        {
                            GameObject body = new GameObject(source.id);
                            body.transform.SetParent(colliderRoot.transform, false);
                            if (source.kind == "circle")
                            {
                                CircleCollider2D circle = body.AddComponent<CircleCollider2D>();
                                circle.radius = source.radius;
                                circle.isTrigger = source.is_trigger;
                            }
                            else
                            {
                                BoxCollider2D box = body.AddComponent<BoxCollider2D>();
                                box.size = source.size == null ? Vector2.one : new Vector2(source.size.x, source.size.y);
                                box.isTrigger = source.is_trigger;
                            }
                        }
                        GameObject nav = new GameObject("NavigationRegion2D");
                        nav.transform.SetParent(rootObject.transform, false);
                        NeoEngE11NavigationMetadata metadata = nav.AddComponent<NeoEngE11NavigationMetadata>();
                        metadata.regionCount = navmesh.regions.Length;
                        File.WriteAllText("e11-composition-report.json", "{\\\"status\\\":\\\"SUCCESS\\\",\\\"engine\\\":\\\"unity\\\",\\\"tile_cells\\\":" + tilemap.cells.Length + ",\\\"colliders\\\":" + colliders.colliders.Length + ",\\\"nav_regions\\\":" + navmesh.regions.Length + "}");
                        Debug.Log("E11_COMPOSITION_UNITY=SUCCESS");
                        Debug.Log("E11_COMPOSITION_TILE_CELLS=" + tilemap.cells.Length);
                        Debug.Log("E11_COMPOSITION_COLLIDERS=" + colliders.colliders.Length);
                        Debug.Log("E11_COMPOSITION_NAV_REGIONS=" + navmesh.regions.Length);
                        UnityEngine.Object.DestroyImmediate(rootObject);
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

            public sealed class NeoEngE11NavigationMetadata : MonoBehaviour
            {
                public int regionCount;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _discover_unity() -> Path:
    try:
        from scripts.audit_unity_import_stage6 import discover_unity
    except ModuleNotFoundError as exc:
        if exc.name != "scripts":
            raise
        module_path = Path(__file__).with_name("audit_unity_import_stage6.py")
        spec = importlib.util.spec_from_file_location("audit_unity_import_stage6", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not load Unity discovery helper: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        discover_unity = module.discover_unity

    discovered = discover_unity()
    if isinstance(discovered, tuple):
        discovered = discovered[0]
    if not discovered:
        raise RuntimeError("Unity executable was not discoverable")
    return Path(discovered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--godot", type=Path, default=Path("C:/ProgramData/chocolatey/bin/godot.exe"))
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--engine", choices=("both", "godot", "unity"), default="both")
    args = parser.parse_args()
    package = args.package.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {output}")
    if not (package / "composition.json").is_file():
        raise FileNotFoundError("composition manifest is missing")
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-e11-engine-") as temporary:
        temporary_root = Path(temporary)
        if args.engine in {"both", "godot"}:
            godot_project = _godot_project(temporary_root, package)
            godot_run = _run(
                [str(args.godot), "--headless", "--path", str(godot_project), "--script", "res://main.gd", "--quit-after", "15"],
                godot_project,
                timeout=60,
            )
            godot_report = godot_project / "e11-composition-report.json"
            godot_capture = godot_project / "e11-composition-capture.png"
            if godot_report.is_file():
                shutil.copy2(godot_report, output / godot_report.name)
                godot_run["composition_report"] = json.loads(godot_report.read_text(encoding="utf-8"))
                godot_run["composition_success"] = godot_run["composition_report"].get("status") == "SUCCESS"
            if godot_capture.is_file(): shutil.copy2(godot_capture, output / godot_capture.name)
        else:
            godot_run = {"returncode": 0, "status": "NOT_RUN"}

        if args.engine in {"both", "unity"}:
            unity = args.unity or _discover_unity()
            unity_project = _unity_project(temporary_root, package)
            unity_run = _run(
                [str(unity), "-batchmode", "-nographics", "-quit", "-projectPath", str(unity_project), "-executeMethod", "E11CompositionAudit.Run"],
                unity_project,
                timeout=300,
            )
            unity_report = unity_project / "e11-composition-report.json"
            if unity_report.is_file():
                shutil.copy2(unity_report, output / "e11-composition-unity-report.json")
                unity_run["composition_report"] = json.loads(unity_report.read_text(encoding="utf-8"))
                unity_run["composition_success"] = unity_run["composition_report"].get("status") == "SUCCESS"
        else:
            unity_run = {"returncode": 0, "status": "NOT_RUN"}
    godot_pass = args.engine == "unity" or (
        godot_run["returncode"] == 0
        and godot_run.get("composition_success", False)
        and "SCRIPT ERROR" not in str(godot_run.get("stderr", ""))
    )
    unity_pass = args.engine == "godot" or (
        unity_run["returncode"] == 0
        and unity_run.get("composition_success", False)
    )
    report = {
        "schema_version": 1,
        "package": str(package),
        "package_manifest_sha256": _sha256(package / "composition.json"),
        "godot": godot_run,
        "unity": unity_run,
        "status": "SUCCESS" if godot_pass and unity_pass else "FAIL",
    }
    (output / "e11-engine-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
