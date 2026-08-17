# flake8: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from scripts.audit_unity_import_stage6 import (
    PACKAGE_ROOT,
    ROOT,
    discover_unity,
    sanitize,
    write_project,
)
from src.exporters.animation_batch import export_animation_frames
from src.exporters.integration_manifest import (
    build_integration_manifest,
    save_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.exporters.tileset_exporter import prepare_tileset
from src.models.scene import Scene

OUT = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / "native-animation-tileset-stage3-2026-08-17"
)
MANIFEST = "Assets/NeoEngInput/hero.ndt.integration.json"


RUNNER = r"""using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using UnityEngine.Tilemaps;
using NeoEng.DTrace;
using NeoEng.DTrace.Editor;

[InitializeOnLoad]
internal static class NeoEngStage3Runner
{
    private const string Manifest = "Assets/NeoEngInput/hero.ndt.integration.json";
    private const string AnimationPrefab = "Assets/NeoEngGenerated/hero_animation.animation/hero_animation.prefab";
    private const string TilesetPrefab = "Assets/NeoEngGenerated/hero_tileset.tileset/hero_tileset.prefab";
    private const string AnimationMetadata = "Assets/NeoEngGenerated/hero_animation.animation/hero_animation.metadata.asset";
    private const string TilesetMetadata = "Assets/NeoEngGenerated/hero_tileset.tileset/hero_tileset.metadata.asset";

    static NeoEngStage3Runner() { EditorApplication.delayCall += Begin; }

    private static void Begin()
    {
        try
        {
            string mode = Environment.GetEnvironmentVariable("NEOENG_STAGE3_MODE") ?? "positive";
            if (mode == "positive") RunPositive();
            else if (mode == "animation-conflict") RunConflict(true);
            else if (mode == "tileset-conflict") RunConflict(false);
            else throw new InvalidOperationException("unknown Stage3 mode");
            EditorApplication.Exit(0);
        }
        catch (Exception exception)
        {
            Debug.LogError("UNITY_STAGE3_FAILURE=" + exception);
            EditorApplication.Exit(1);
        }
    }

    private static void RunPositive()
    {
        UnityImportGenerator.ImportResult first = UnityImportGenerator.ImportManifest(Manifest);
        Require(first.Success, "initial import failed: " + first.ErrorSummary());
        Require(first.ImportedAnimations == 1 && first.ImportedTilesets == 1, "optional import counts are invalid");
        Require(first.OptionalAssets.Count == 2 && first.OptionalAssets.All(asset => asset.Status == "UPDATED"), "optional update statuses are invalid");
        ValidateAnimation();
        ValidateTileset();
        Debug.Log("UNITY_STAGE3_ANIMATION_NATIVE=PASS");
        Debug.Log("UNITY_STAGE3_FRAME_COLLISION=PASS");
        Debug.Log("UNITY_STAGE3_TILESET_NATIVE=PASS");
        Debug.Log("UNITY_STAGE3_TILE_COLLISION=PASS");

        UnityImportGenerator.ImportResult second = UnityImportGenerator.ImportManifest(Manifest);
        Require(second.Success, "repeat import failed: " + second.ErrorSummary());
        Require(second.OptionalAssets.Count == 2 && second.OptionalAssets.All(asset => asset.Status == "UNCHANGED"), "repeat import was not unchanged");
        Debug.Log("UNITY_STAGE3_REPEAT=PASS");
    }

    private static void ValidateAnimation()
    {
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(AnimationPrefab);
        NeoEngImportedAnimationMetadata metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedAnimationMetadata>(AnimationMetadata);
        Require(prefab != null && metadata != null && metadata.frames != null && metadata.frames.Length == 2, "animation assets are incomplete");
        GameObject instance = UnityEngine.Object.Instantiate(prefab);
        try
        {
            SpriteRenderer renderer = instance.GetComponent<SpriteRenderer>();
            Animator animator = instance.GetComponent<Animator>();
            PolygonCollider2D collider = instance.GetComponent<PolygonCollider2D>();
            NeoEngAnimationCollisionDriver driver = instance.GetComponent<NeoEngAnimationCollisionDriver>();
            Require(renderer != null && renderer.sprite != null && animator != null && animator.runtimeAnimatorController != null, "animation prefab components are incomplete");
            Require(collider != null && collider.pathCount == 1 && collider.GetPath(0).Length == metadata.frames[0].collisionPoints.Length && collider.GetPath(0).Length >= 3, "animation collision path is invalid");
            Require(driver != null && driver.metadata == metadata, "animation collision driver metadata is not linked");
            AnimatorController controller = animator.runtimeAnimatorController as AnimatorController;
            Require(controller != null && controller.layers.Length > 0, "animation controller is invalid");
            AnimationClip clip = controller.layers[0].stateMachine.states[0].state.motion as AnimationClip;
            Require(clip != null, "animation controller clip is missing");
            EditorCurveBinding binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            ObjectReferenceKeyframe[] keys = AnimationUtility.GetObjectReferenceCurve(clip, binding);
            Require(keys != null && keys.Length == 2 && keys[0].value is Sprite && keys[1].value is Sprite, "animation sprite curve is invalid");
            renderer.sprite = metadata.frames[1].sprite;
            driver.SyncCollision();
            Vector2[] switched = collider.GetPath(0);
            Require(switched.Length == metadata.frames[1].collisionPoints.Length && SamePoints(switched, metadata.frames[1].collisionPoints), "frame collision did not follow the selected frame");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }
    private static void ValidateTileset()
    {
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(TilesetPrefab);
        NeoEngImportedTilesetMetadata metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedTilesetMetadata>(TilesetMetadata);
        Tilemap tilemap = prefab == null ? null : prefab.GetComponentInChildren<Tilemap>();
        Require(prefab != null && metadata != null && metadata.tiles != null && metadata.tiles.Length == 2 && tilemap != null, "tileset assets are incomplete");
        TileBase[] tiles = tilemap.GetTilesBlock(tilemap.cellBounds);
        Require(tiles.Count(tile => tile != null) == 2, "tileset used tile count is invalid");
        Require(metadata.tiles.All(record => record.tile is Tile && record.collisionPoints != null && record.collisionPoints.Length >= 3), "tileset metadata collision is invalid");
        Require(tiles.OfType<Tile>().Count() == 2 && tiles.OfType<Tile>().All(tile => tile.colliderType == Tile.ColliderType.None && tile.sprite != null), "tileset tile asset configuration is invalid");
        PolygonCollider2D compound = prefab.GetComponent<PolygonCollider2D>();
        Require(compound != null && compound.pathCount == metadata.tiles.Count(record => record.collisionPoints != null && record.collisionPoints.Length >= 3), "tileset compound collider path count is invalid");
        for (int index = 0; index < compound.pathCount; index++)
        {
            Vector2[] points = compound.GetPath(index);
            Require(points.Length == metadata.tiles[index].collisionPoints.Length && points.Length >= 3, "tileset compound collider path is invalid");
        }
    }

    private static void RunConflict(bool animation)
    {
        UnityImportGenerator.ImportResult baseline = UnityImportGenerator.ImportManifest(Manifest);
        Require(baseline.Success, "conflict baseline failed: " + baseline.ErrorSummary());
        string prefabPath = animation ? AnimationPrefab : TilesetPrefab;
        GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
        Require(root != null, "conflict prefab could not be loaded");
        if (animation)
        {
            PolygonCollider2D collider = root.GetComponent<PolygonCollider2D>();
            Require(collider != null, "animation collider missing for conflict fixture");
            Vector2[] points = collider.GetPath(0);
            points[0] += new Vector2(0.123f, 0.0f);
            collider.SetPath(0, points);
        }
        else
        {
            Tilemap tilemap = root.GetComponentInChildren<Tilemap>();
            Require(tilemap != null, "tileset tilemap missing for conflict fixture");
            tilemap.SetTile(new Vector3Int(0, 0, 0), null);
        }
        PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
        PrefabUtility.UnloadPrefabContents(root);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
        bool blocked = false;
        try { UnityImportGenerator.ImportManifest(Manifest); }
        catch (UnityImportGenerator.SyncConflictException exception)
        {
            blocked = exception.Message.IndexOf("manual", StringComparison.OrdinalIgnoreCase) >= 0;
        }
        Require(blocked, "manual optional output divergence was not blocked");
        Debug.Log(animation ? "UNITY_STAGE3_ANIMATION_CONFLICT_BLOCKED=PASS" : "UNITY_STAGE3_TILESET_CONFLICT_BLOCKED=PASS");
    }

    private static bool SamePoints(Vector2[] left, Vector2[] right)
    {
        return left != null && right != null && left.Length == right.Length && left.Zip(right, (a, b) => Vector2.Distance(a, b) < 0.0001f).All(value => value);
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}"""


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def create_fixture(project: Path) -> None:
    source = project / "Assets" / "source.png"
    image = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 15, 15), fill=(30, 170, 230, 255))
    draw.rectangle((16, 2, 29, 13), fill=(230, 80, 80, 255))
    image.save(source)

    scene = Scene()
    scene.load_image(image, "source.png")
    scene.image_path = "source.png"
    scene.image_path_kind = "relative"
    scene.add_object("hero", [(0, 0), (16, 0), (16, 16), (0, 16)], select=False)
    metadata = export_scene_metadata(scene)

    frame_input = project / "Assets" / "animation_input"
    frame_output = project / "Assets" / "frames"
    frame_input.mkdir(parents=True)
    for name, box, color in (
        ("frame_0.png", (2, 1, 13, 10), (50, 220, 130, 255)),
        ("frame_1.png", (4, 2, 15, 11), (220, 190, 40, 255)),
    ):
        frame = Image.new("RGBA", (16, 12), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rectangle(box, fill=color)
        frame.save(frame_input / name)
    animation = export_animation_frames(
        frame_input, frame_output, mode="basic", min_area=2
    )["manifest"]
    for frame in animation["frames"]:
        frame["texture"] = "frames/" + frame["texture"]
    animation["speed"] = 12.0
    animation["loop"] = True

    prepared = prepare_tileset(
        image, tile_size=(16, 16), spacing=0, margin=0, tolerance=0
    )
    tileset = {key: value for key, value in prepared.items() if key != "tiles"}
    tileset["tiles"] = []
    for entry in prepared["tiles"]:
        tile = {key: value for key, value in entry.items() if key != "image"}
        tile["texture"] = "source.png"
        tileset["tiles"].append(tile)

    metadata["animation"] = animation
    metadata["tileset"] = tileset
    manifest = build_integration_manifest(
        metadata, engine="unity", image_path=source, image_reference="source.png"
    )
    save_integration_manifest(
        manifest, project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
    )


def run_unity(
    executable: Path, project: Path, mode: str, temporary: Path, version: str
) -> dict[str, Any]:
    log = temporary / f"unity-stage3-{mode}.log"
    env = os.environ.copy()
    env["NEOENG_STAGE3_MODE"] = mode
    command = [
        str(executable),
        "-batchmode",
        "-nographics",
        "-projectPath",
        str(project),
        "-logFile",
        str(log),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=360,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "mode": mode,
        "returncode": completed.returncode,
        "output": sanitize(output, temporary),
        "unity_version": version,
    }


def require_markers(run: dict[str, Any], markers: list[str]) -> None:
    if run["returncode"] != 0:
        raise RuntimeError(
            f"Unity Stage3 {run['mode']} exited with {run['returncode']}"
        )
    for marker in markers:
        if marker not in run["output"]:
            raise RuntimeError(f"Unity Stage3 marker missing: {marker}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    executable, version = (
        (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    )
    output = args.output or OUT
    output.mkdir(parents=True, exist_ok=True)
    if any(
        path.name in {"stage3-report.json", "stage3-index.json"}
        for path in output.iterdir()
    ):
        raise RuntimeError(
            "Stage3 evidence already has final artifacts; refusing to overwrite"
        )
    with tempfile.TemporaryDirectory(prefix="neoeng-dtrace-stage3-") as raw:
        temporary = Path(raw)
        runs: dict[str, dict[str, Any]] = {}
        for mode in ("positive", "animation-conflict", "tileset-conflict"):
            project = temporary / mode
            write_project(project, PACKAGE_ROOT, version)
            create_fixture(project)
            runner = project / "Assets" / "Editor" / "NeoEngStage3Runner.cs"
            runner.parent.mkdir(parents=True)
            runner.write_text(RUNNER, encoding="utf-8", newline="\n")
            runs[mode] = run_unity(executable, project, mode, temporary, version)
        for mode, run in runs.items():
            (output / f"attempt-unity-stage3-{mode}.log").write_text(
                run["output"], encoding="utf-8", newline="\n"
            )
        try:
            require_markers(
                runs["positive"],
                [
                    "UNITY_STAGE3_ANIMATION_NATIVE=PASS",
                    "UNITY_STAGE3_FRAME_COLLISION=PASS",
                    "UNITY_STAGE3_TILESET_NATIVE=PASS",
                    "UNITY_STAGE3_TILE_COLLISION=PASS",
                    "UNITY_STAGE3_REPEAT=PASS",
                ],
            )
            require_markers(
                runs["animation-conflict"],
                ["UNITY_STAGE3_ANIMATION_CONFLICT_BLOCKED=PASS"],
            )
            require_markers(
                runs["tileset-conflict"], ["UNITY_STAGE3_TILESET_CONFLICT_BLOCKED=PASS"]
            )
        except Exception as exception:
            (output / "attempt-unity-stage3-failure.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "stage": 3,
                        "status": "FAIL",
                        "engine": "unity",
                        "unity_version": version,
                        "error": str(exception),
                        "runs": runs,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            raise
        for mode, run in runs.items():
            (output / f"unity-stage3-{mode}.log").write_text(
                run["output"], encoding="utf-8", newline="\n"
            )
        report = {
            "schema_version": 1,
            "stage": 3,
            "status": "SUCCESS",
            "engine": "unity",
            "unity_version": version,
            "scenarios": {
                "native_animation": True,
                "frame_collision_switch": True,
                "native_tileset": True,
                "tile_collision": True,
                "repeat_import_unchanged": True,
                "animation_manual_divergence_blocked": True,
                "tileset_manual_divergence_blocked": True,
            },
            "runs": runs,
            "fixture": {
                "source.png": digest(temporary / "positive" / "Assets" / "source.png"),
                "manifest": digest(
                    temporary
                    / "positive"
                    / "Assets"
                    / "NeoEngInput"
                    / "hero.ndt.integration.json"
                ),
            },
        }
        (output / "stage3-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    files = {
        path.name: digest(path) for path in sorted(output.iterdir()) if path.is_file()
    }
    (output / "stage3-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": 3,
                "status": "SUCCESS",
                "engine": "unity",
                "unity_version": version,
                "files": files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("NATIVE_ANIMATION_TILESET_STAGE3_UNITY=SUCCESS")
    print("ANIMATION_NATIVE=PASS")
    print("FRAME_COLLISION=PASS")
    print("TILESET_NATIVE=PASS")
    print("TILE_COLLISION=PASS")
    print("REPEAT_IMPORT=PASS")
    print("MANUAL_DIVERGENCE_BLOCKED=PASS")
    print("EVIDENCE_HASH_INDEX=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
