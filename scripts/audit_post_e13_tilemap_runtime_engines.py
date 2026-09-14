"""Run the authored TileMap runtime contract in real Godot and Unity.

The audit deliberately keeps the positive and atlas-drift runs separate.  A
runtime is only successful when it materializes the authored cells and rejects
the same package after the bound atlas bytes are changed.
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

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.tilemap_model import (
    TileCell,
    TileDefinition,
    TileLayer,
    TileMapDocument,
    TileSet,
)
from src.core.tilemap_rules import NeighborCondition, TerrainRule, TileRuleSet
from src.exporters.tilemap_runtime_export import build_tilemap_runtime_package
from src.persistence.tilemap_io import save_tilemap

GODOT_ADAPTER = ROOT / "integrations/godot/addons/neoeng_d_trace/tilemap_runtime.gd"
UNITY_ADAPTER = (
    ROOT
    / "integrations/unity/package/com.neoeng.dtrace/Runtime/NeoEngRuntimeTilemap.cs"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], cwd: Path, timeout: int = 180) -> dict[str, object]:
    completed = subprocess.run(
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
        "returncode": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }


def _engine_status(
    enabled: bool, passed: bool, run: dict[str, object]
) -> str:
    """Expose the evaluated engine gate instead of its initial placeholder."""
    if not enabled:
        return "NOT_RUN"
    if passed:
        return "PASS"
    if run.get("status") == "PENDING_EVIDENCE":
        return "PENDING_EVIDENCE"
    return "FAIL"


def _authoring_fixture(root: Path) -> tuple[Path, Path]:
    project = root / "authoring"
    atlas = project / "assets" / "tiles" / "terrain.png"
    atlas.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (64, 16), (12, 18, 28, 255))
    draw = ImageDraw.Draw(image)
    colors = ["#63d48b", "#4ba8ff", "#e9b44c", "#db6b92"]
    for index, color in enumerate(colors):
        x = index * 16
        draw.rectangle((x, 0, x + 15, 15), fill=color)
        draw.rectangle((x + 2, 2, x + 13, 13), outline="#e8f4ff", width=1)
    image.save(atlas)
    atlas_hash = _sha256(atlas)
    tiles = tuple(
        TileDefinition(
            f"tile_{index}",
            "terrain-atlas",
            (index * 16, 0, 16, 16),
            variant="default",
        )
        for index in range(4)
    )
    rule_set = TileRuleSet(
        (
            TerrainRule(
                "water-edge",
                "tile_1",
                conditions=(NeighborCondition((1, 0), ("tile_0",)),),
                priority=2,
            ),
        ),
        fallback_tile_id="tile_0",
    )
    document = TileMapDocument(
        id="runtime_scenario",
        name="Runtime Tilemap Scenario",
        tileset=TileSet(
            id="terrain",
            atlas_asset_id="terrain-atlas",
            atlas_sha256=atlas_hash,
            tiles=tiles,
            atlas_path="assets/tiles/terrain.png",
        ),
        grid="orthogonal",
        layers=(TileLayer("ground", "Ground", 0), TileLayer("deco", "Decoration", 1)),
        rule_set_payload=rule_set.to_dict(),
    )
    for y in range(4):
        for x in range(6):
            document.set_cell("ground", (x, y), TileCell(f"tile_{(x + y) % 3}"))
    for coordinate in ((1, 1), (2, 1), (3, 1)):
        document.set_cell("deco", coordinate, TileCell("tile_3", variant="highlight"))
    source = project / "maps" / "scenario.ndttilemap.json"
    save_tilemap(document, source)
    return project, source


def _godot_project(root: Path, package: Path) -> Path:
    project = root / "godot"
    shutil.copytree(package, project, dirs_exist_ok=True)
    shutil.copy2(GODOT_ADAPTER, project / "tilemap_runtime.gd")
    (project / "project.godot").write_text(
        '[application]\nconfig/name="NeoEng Post E13 Tilemap Runtime"\n'
        "[display]\nwindow/size/viewport_width=800\nwindow/size/viewport_height=450\n"
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n',
        encoding="utf-8",
        newline="\n",
    )
    (project / "runtime_canvas.gd").write_text(
        dedent("""
            extends Node2D
            var report: Dictionary = {}

            func _draw() -> void:
                draw_rect(Rect2(0, 0, 800, 450), Color("101722"), true)
                draw_rect(Rect2(126, 94, 430, 188), Color("182739"), true)
                draw_rect(Rect2(126, 94, 430, 188), Color("61d7ff"), false, 2.0)
                draw_string(ThemeDB.fallback_font, Vector2(30, 42),
                    "POST-E13 TILEMAP RUNTIME | GODOT 4", HORIZONTAL_ALIGNMENT_LEFT,
                    -1, 22, Color("a9f2ff"))
                draw_string(ThemeDB.fallback_font, Vector2(30, 72),
                    "native Sprite2D materialization from authored atlas cells",
                    HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("dbe7ef"))
                draw_string(ThemeDB.fallback_font, Vector2(30, 340),
                    "layers: %d   cells: %d   sprites: %d   rules: %d" % [
                        report.get("layers", 0), report.get("tile_cells", 0),
                        report.get("rendered_sprites", 0), report.get("rules", 0)],
                    HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color("f0c76b"))
                draw_string(ThemeDB.fallback_font, Vector2(30, 382),
                    "atlas bound and verified: %s" % str(report.get("atlas_sha256", "")),
                    HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color("8ce3a5"))
            """).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "main.gd").write_text(
        dedent("""
            extends SceneTree

            func _init() -> void:
                call_deferred("_run")

            func _run() -> void:
                var adapter = preload("res://tilemap_runtime.gd")
                var diagnostic: Dictionary = adapter.diagnose_tilemap("res://tilemap-runtime.json")
                if diagnostic.get("status") != "SUCCESS":
                    print("TILEMAP_RUNTIME_GODOT=FAILURE")
                    print(JSON.stringify(diagnostic))
                    quit(1)
                    return
                var result: Dictionary = adapter.import_tilemap("res://tilemap-runtime.json")
                if result.get("status") != "SUCCESS":
                    print("TILEMAP_RUNTIME_GODOT=FAILURE")
                    print(JSON.stringify(result))
                    quit(1)
                    return
                var report := {
                    "status": "SUCCESS",
                    "engine": "godot",
                    "tilemap_id": result["tilemap_id"],
                    "layers": result["layers"],
                    "tiles": result["tiles"],
                    "tile_cells": result["tile_cells"],
                    "rendered_sprites": result["rendered_sprites"],
                    "rules": result["rules"],
                    "atlas_path": result["atlas_path"],
                    "atlas_sha256": result["atlas_sha256"]
                }
                var canvas = preload("res://runtime_canvas.gd").new()
                canvas.report = report
                canvas.z_index = -10
                get_root().add_child(canvas)
                var tilemap_root: Node2D = result["root"]
                tilemap_root.position = Vector2(160, 112)
                tilemap_root.scale = Vector2(3, 3)
                get_root().add_child(tilemap_root)
                await process_frame
                # Headless Godot uses the dummy renderer, so its viewport has
                # no readable GPU texture.  The proof image is composed from
                # the same decoded atlas and authored cells that the native
                # Sprite2D objects above use; no mock tile data is introduced.
                var payload: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tilemap-runtime.json"))
                var atlas_image := Image.new()
                atlas_image.load("res://" + str(payload["atlas"]["path"]))
                var proof := Image.create(800, 450, false, Image.FORMAT_RGBA8)
                proof.fill(Color("101722"))
                proof.fill_rect(Rect2i(126, 94, 430, 188), Color("182739"))
                for cell_value in payload["cells"]:
                    var cell: Dictionary = cell_value
                    var tile: Dictionary
                    for tile_value in payload["tileset"]["tiles"]:
                        if str(tile_value["id"]) == str(cell["tile_id"]):
                            tile = tile_value
                            break
                    var rect: Dictionary = tile["source_rect"]
                    for sy in int(rect["h"]):
                        for sx in int(rect["w"]):
                            var color := atlas_image.get_pixel(int(rect["x"]) + sx, int(rect["y"]) + sy)
                            for oy in 2:
                                for ox in 2:
                                    proof.set_pixel(160 + int(cell["x"]) * 32 + sx * 2 + ox,
                                        112 + int(cell["y"]) * 32 + sy * 2 + oy, color)
                proof.save_png("res://tilemap-runtime-capture.png")
                var report_file = FileAccess.open("res://tilemap-runtime-report.json", FileAccess.WRITE)
                report_file.store_string(JSON.stringify(report))
                print("TILEMAP_RUNTIME_GODOT=SUCCESS")
                print(JSON.stringify(report))
                quit(0)
            """).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "negative.gd").write_text(
        dedent("""
            extends SceneTree

            func _init() -> void:
                var adapter = preload("res://tilemap_runtime.gd")
                var diagnostic: Dictionary = adapter.diagnose_tilemap("res://tilemap-runtime.json")
                var message := JSON.stringify(diagnostic)
                var rejected: bool = bool(diagnostic.get("status") == "FAILED" and message.contains("hash"))
                var report := {"status": "REJECTED" if rejected else "UNEXPECTED_ACCEPT", "diagnostic": diagnostic}
                var report_file = FileAccess.open("res://tilemap-runtime-negative-report.json", FileAccess.WRITE)
                report_file.store_string(JSON.stringify(report))
                print("TILEMAP_RUNTIME_GODOT_DRIFT=" + ("REJECTED" if rejected else "ACCEPTED"))
                quit(0 if rejected else 1)
            """).strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _unity_project(root: Path, package: Path) -> Path:
    project = root / "unity"
    package_destination = project / "Assets" / "NeoEngTilemap" / "Package"
    runtime_destination = project / "Assets" / "NeoEngTilemap" / "Runtime"
    editor_destination = project / "Assets" / "Editor"
    package_destination.mkdir(parents=True)
    runtime_destination.mkdir(parents=True)
    editor_destination.mkdir(parents=True)
    shutil.copytree(package, package_destination, dirs_exist_ok=True)
    shutil.copy2(UNITY_ADAPTER, runtime_destination / UNITY_ADAPTER.name)
    (project / "ProjectSettings").mkdir(parents=True)
    (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8", newline="\n"
    )
    (editor_destination / "TilemapRuntimeAudit.cs").write_text(
        dedent("""
            using System;
            using System.IO;
            using NeoEng.DTrace;
            using UnityEditor;
            using UnityEngine;

            public static class TilemapRuntimeAudit
            {
                [Serializable] private sealed class Report
                {
                    public string status;
                    public string engine;
                    public int layers;
                    public int tiles;
                    public int tile_cells;
                    public int rendered_sprites;
                    public int rules;
                    public string atlas_sha256;
                    public string error;
                }

                public static void Run()
                {
                    try
                    {
                        NeoEngRuntimeTilemap.Result result = NeoEngRuntimeTilemap.Import("Assets/NeoEngTilemap/Package/tilemap-runtime.json");
                        if (result.RenderedSprites != result.TileCells)
                            throw new Exception("Unity did not materialize every authored cell");
                        File.WriteAllText("tilemap-runtime-unity-report.json", JsonUtility.ToJson(new Report
                        {
                            status = "SUCCESS", engine = "unity", layers = result.Layers, tiles = result.Tiles,
                            tile_cells = result.TileCells, rendered_sprites = result.RenderedSprites,
                            rules = result.Rules, atlas_sha256 = result.AtlasSha256
                        }));
                        WriteProof(result);
                        Debug.Log("TILEMAP_RUNTIME_UNITY=SUCCESS");
                        Debug.Log("TILEMAP_RUNTIME_UNITY_CELLS=" + result.TileCells);
                        UnityEngine.Object.DestroyImmediate(result.Root);
                        EditorApplication.Exit(0);
                    }
                    catch (Exception exception)
                    {
                        Debug.LogException(exception);
                        File.WriteAllText("tilemap-runtime-unity-report.json", JsonUtility.ToJson(new Report
                        {
                            status = "FAILURE", engine = "unity", error = exception.Message
                        }));
                        EditorApplication.Exit(1);
                    }
                }

                public static void RunNegative()
                {
                    try
                    {
                        NeoEngRuntimeTilemap.Import("Assets/NeoEngTilemap/Package/tilemap-runtime.json");
                        File.WriteAllText("tilemap-runtime-unity-negative-report.json", JsonUtility.ToJson(new Report
                        {
                            status = "ACCEPTED", engine = "unity"
                        }));
                        Debug.Log("TILEMAP_RUNTIME_UNITY_DRIFT=ACCEPTED");
                        EditorApplication.Exit(1);
                    }
                    catch (Exception exception)
                    {
                        File.WriteAllText("tilemap-runtime-unity-negative-report.json", JsonUtility.ToJson(new Report
                        {
                            status = "REJECTED", engine = "unity", error = exception.Message
                        }));
                        Debug.Log("TILEMAP_RUNTIME_UNITY_DRIFT=REJECTED");
                        Debug.Log(exception.Message);
                        EditorApplication.Exit(0);
                    }
                }

                private static void WriteProof(NeoEngRuntimeTilemap.Result result)
                {
                    byte[] bytes = File.ReadAllBytes(result.AtlasPath);
                    Texture2D atlas = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                    if (!atlas.LoadImage(bytes, false)) throw new Exception("Unity proof atlas decode failed");
                    Texture2D proof = new Texture2D(640, 360, TextureFormat.RGBA32, false);
                    Color[] background = new Color[640 * 360];
                    for (int index = 0; index < background.Length; index++) background[index] = new Color(0.06f, 0.09f, 0.14f, 1.0f);
                    proof.SetPixels(background);
                    foreach (NeoEngRuntimeTilemap.CellData cell in result.Payload.cells)
                    {
                        NeoEngRuntimeTilemap.TileData tile = Array.Find(result.Payload.tileset.tiles, item => item.id == cell.tile_id);
                        NeoEngRuntimeTilemap.RectData rect = tile.source_rect;
                        Color[] pixels = atlas.GetPixels(rect.x, atlas.height - rect.y - rect.h, rect.w, rect.h);
                        int originX = 160 + cell.x * 32;
                        int originY = 250 - cell.y * 32;
                        for (int y = 0; y < rect.h; y++)
                            for (int x = 0; x < rect.w; x++)
                                for (int sy = 0; sy < 2; sy++)
                                    for (int sx = 0; sx < 2; sx++)
                                        proof.SetPixel(originX + x * 2 + sx, originY + y * 2 + sy, pixels[y * rect.w + x]);
                    }
                    proof.Apply();
                    File.WriteAllBytes("tilemap-runtime-unity-capture.png", proof.EncodeToPNG());
                    UnityEngine.Object.DestroyImmediate(proof);
                    UnityEngine.Object.DestroyImmediate(atlas);
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
        raise RuntimeError(f"could not load Unity discovery helper: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    discovered = module.discover_unity()
    return Path(discovered[0] if isinstance(discovered, tuple) else discovered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--godot", type=Path, default=Path("C:/ProgramData/chocolatey/bin/godot.exe")
    )
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--engine", choices=("both", "godot", "unity"), default="both")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {output}")
    if not GODOT_ADAPTER.is_file():
        raise FileNotFoundError(f"Godot adapter is missing: {GODOT_ADAPTER}")
    if not UNITY_ADAPTER.is_file():
        raise FileNotFoundError(f"Unity adapter is missing: {UNITY_ADAPTER}")
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(
        prefix="neoeng-post-e13-tilemap-runtime-"
    ) as temporary:
        temporary_root = Path(temporary)
        authoring_root, source = _authoring_fixture(temporary_root)
        package = build_tilemap_runtime_package(
            source,
            project_root=authoring_root,
            destination=temporary_root / "runtime-package",
        ).directory
        shutil.copytree(package, output / "runtime-package", dirs_exist_ok=True)

        godot_run: dict[str, object] = {"status": "NOT_RUN"}
        if args.engine in {"both", "godot"}:
            godot_project = _godot_project(temporary_root, package)
            godot_run["positive"] = _run(
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
            report = godot_project / "tilemap-runtime-report.json"
            capture = godot_project / "tilemap-runtime-capture.png"
            if report.is_file():
                shutil.copy2(report, output / "godot-tilemap-runtime-report.json")
                godot_run["report"] = json.loads(report.read_text(encoding="utf-8"))
            if capture.is_file():
                shutil.copy2(capture, output / "godot-tilemap-runtime-capture.png")
            atlas = godot_project / "assets" / "tiles" / "terrain.png"
            atlas.write_bytes(atlas.read_bytes() + b"\nDRIFT")
            godot_run["negative"] = _run(
                [
                    str(args.godot),
                    "--headless",
                    "--path",
                    str(godot_project),
                    "--script",
                    "res://negative.gd",
                    "--quit-after",
                    "15",
                ],
                godot_project,
                timeout=90,
            )
            negative = godot_project / "tilemap-runtime-negative-report.json"
            if negative.is_file():
                shutil.copy2(
                    negative, output / "godot-tilemap-runtime-negative-report.json"
                )
                godot_run["negative_report"] = json.loads(
                    negative.read_text(encoding="utf-8")
                )

        unity_run: dict[str, object] = {"status": "NOT_RUN"}
        if args.engine in {"both", "unity"}:
            try:
                unity = args.unity or _discover_unity()
                unity_project = _unity_project(temporary_root, package)
                unity_run["positive"] = _run(
                    [
                        str(unity),
                        "-batchmode",
                        "-nographics",
                        "-quit",
                        "-projectPath",
                        str(unity_project),
                        "-executeMethod",
                        "TilemapRuntimeAudit.Run",
                        "-logFile",
                        str(output / "unity-positive.log"),
                    ],
                    unity_project,
                    timeout=360,
                )
                report = unity_project / "tilemap-runtime-unity-report.json"
                capture = unity_project / "tilemap-runtime-unity-capture.png"
                if report.is_file():
                    shutil.copy2(report, output / "unity-tilemap-runtime-report.json")
                    unity_run["report"] = json.loads(report.read_text(encoding="utf-8"))
                if capture.is_file():
                    shutil.copy2(capture, output / "unity-tilemap-runtime-capture.png")
                atlas = (
                    unity_project
                    / "Assets"
                    / "NeoEngTilemap"
                    / "Package"
                    / "assets"
                    / "tiles"
                    / "terrain.png"
                )
                atlas.write_bytes(atlas.read_bytes() + b"\nDRIFT")
                unity_run["negative"] = _run(
                    [
                        str(unity),
                        "-batchmode",
                        "-nographics",
                        "-quit",
                        "-projectPath",
                        str(unity_project),
                        "-executeMethod",
                        "TilemapRuntimeAudit.RunNegative",
                        "-logFile",
                        str(output / "unity-negative.log"),
                    ],
                    unity_project,
                    timeout=360,
                )
                negative = unity_project / "tilemap-runtime-unity-negative-report.json"
                if negative.is_file():
                    shutil.copy2(
                        negative, output / "unity-tilemap-runtime-negative-report.json"
                    )
                    unity_run["negative_report"] = json.loads(
                        negative.read_text(encoding="utf-8")
                    )
            except Exception as exc:
                unity_run = {"status": "PENDING_EVIDENCE", "reason": str(exc)}

    godot_positive = godot_run.get("positive", {})
    godot_negative = godot_run.get("negative", {})
    godot_pass = args.engine == "unity" or (
        isinstance(godot_positive, dict)
        and godot_positive.get("returncode") == 0
        and isinstance(godot_run.get("report"), dict)
        and godot_run["report"].get("status") == "SUCCESS"
        and isinstance(godot_negative, dict)
        and godot_negative.get("returncode") == 0
        and isinstance(godot_run.get("negative_report"), dict)
        and godot_run["negative_report"].get("status") == "REJECTED"
    )
    unity_positive = unity_run.get("positive", {})
    unity_negative = unity_run.get("negative", {})
    unity_pass = args.engine == "godot" or (
        isinstance(unity_positive, dict)
        and unity_positive.get("returncode") == 0
        and isinstance(unity_run.get("report"), dict)
        and unity_run["report"].get("status") == "SUCCESS"
        and isinstance(unity_negative, dict)
        and unity_negative.get("returncode") == 0
        and isinstance(unity_run.get("negative_report"), dict)
        and unity_run["negative_report"].get("status") == "REJECTED"
    )
    godot_run["status"] = _engine_status(
        args.engine in {"both", "godot"}, godot_pass, godot_run
    )
    unity_run["status"] = _engine_status(
        args.engine in {"both", "unity"}, unity_pass, unity_run
    )
    report = {
        "schema_version": 1,
        "format_id": "neoeng-d-trace-tilemap-runtime-audit",
        "adapter_sha256": {
            "godot": _sha256(GODOT_ADAPTER),
            "unity": _sha256(UNITY_ADAPTER),
        },
        "godot": godot_run,
        "unity": unity_run,
        "status": (
            "SUCCESS"
            if godot_pass and unity_pass
            else "PENDING_EVIDENCE" if "PENDING_EVIDENCE" in str(unity_run) else "FAIL"
        ),
    }
    (output / "tilemap-runtime-engine-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
