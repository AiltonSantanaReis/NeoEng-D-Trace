from __future__ import annotations

import argparse
import hashlib
import json
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
from src.exporters.integration_manifest import (
    build_integration_manifest,
    save_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene

OUT = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / "native-compound-colliders-stage2-2026-08-17"
)

RUNNER = r"""using System;
using System.IO;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;
using NeoEng.DTrace.Editor;

[InitializeOnLoad]
internal static class NeoEngStage2Runner
{
    private const string Source = "Assets/source.png";
    private const string Manifest = "Assets/NeoEngInput/hero.ndt.integration.json";
    private const string Prefab = "Assets/NeoEngGenerated/hero.prefab";
    private const string Metadata = "Assets/NeoEngGenerated/hero.metadata.asset";
    private static int phase = -1;
    private static double nextAction;
    private static string secondPathHash;
    private static string secondSourceHash;

    static NeoEngStage2Runner() { EditorApplication.delayCall += Begin; }

    private static void Begin()
    {
        UnityImportGenerator.ImportResult baseline =
            UnityImportGenerator.ImportManifest(Manifest);
        if (!baseline.Success)
        {
            Fail("baseline:" + baseline.ErrorSummary());
            return;
        }
        GameObject root = PrefabUtility.LoadPrefabContents(Prefab);
        PolygonCollider2D collider = root == null
            ? null
            : root.GetComponent<PolygonCollider2D>();
        bool generated = collider != null && collider.pathCount == 2 &&
            collider.GetPath(0).Length == 4 && collider.GetPath(1).Length == 4;
        if (root != null) PrefabUtility.UnloadPrefabContents(root);
        if (!generated) {
            Fail("compound collider did not generate two four-point paths");
            return;
        }
        Debug.Log("UNITY_COMPOUND_STAGE2=GENERATED");
        Debug.Log("UNITY_COMPOUND_STAGE2_PATHS=2");
        root = PrefabUtility.LoadPrefabContents(Prefab);
        collider = root.GetComponent<PolygonCollider2D>();
        Vector2[] second = collider.GetPath(1);
        second[0] += new Vector2(0.25f, 0.0f);
        secondPathHash = HashPath(second);
        collider.SetPath(1, second);
        PrefabUtility.SaveAsPrefabAsset(root, Prefab);
        PrefabUtility.UnloadPrefabContents(root);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
        secondSourceHash = MutateInput(71);
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
        phase = 1;
        Schedule(4.0);
    }

    private static void Schedule(double seconds)
    {
        nextAction = EditorApplication.timeSinceStartup + seconds;
        EditorApplication.update -= Tick;
        EditorApplication.update += Tick;
    }

    private static void Tick()
    {
        if (EditorApplication.timeSinceStartup < nextAction) return;
        EditorApplication.update -= Tick;
        if (phase != 1)
        {
            Fail("unexpected runner phase");
            return;
        }
        NeoEngImportedSpriteMetadata metadata =
            AssetDatabase.LoadAssetAtPath<NeoEngImportedSpriteMetadata>(Metadata);
        GameObject root = PrefabUtility.LoadPrefabContents(Prefab);
        PolygonCollider2D collider = root == null
            ? null
            : root.GetComponent<PolygonCollider2D>();
        bool preserved = false;
        if (collider != null && collider.pathCount == 2 &&
            collider.GetPath(1).Length == 4)
        {
            preserved = HashPath(collider.GetPath(1)) == secondPathHash;
        }
        if (root != null) PrefabUtility.UnloadPrefabContents(root);
        if (!preserved) {
            Fail("automatic sync overwrote the manually changed secondary path");
            return;
        }
        if (metadata == null || metadata.sourceImageHash == secondSourceHash)
        {
            Fail("conflicted metadata was updated unexpectedly");
            return;
        }
        Debug.Log("UNITY_COMPOUND_STAGE2=CONFLICT_BLOCKED");
        Debug.Log("UNITY_COMPOUND_STAGE2=PASS");
        EditorApplication.Exit(0);
    }

    private static string HashPath(Vector2[] points)
    {
        string value = string.Join(";",
            Array.ConvertAll(points, point =>
                point.x.ToString("R") + "," + point.y.ToString("R")));
        using (SHA256 sha = SHA256.Create())
        {
            return BitConverter.ToString(
                sha.ComputeHash(System.Text.Encoding.UTF8.GetBytes(value)))
                .Replace("-", "").ToLowerInvariant();
        }
    }

    private static string MutateInput(byte extra)
    {
        byte[] original = File.ReadAllBytes(Source);
        byte[] changed = new byte[original.Length + 1];
        Buffer.BlockCopy(original, 0, changed, 0, original.Length);
        changed[changed.Length - 1] = extra;
        File.WriteAllBytes(Source, changed);
        string hash;
        using (SHA256 sha = SHA256.Create())
        {
            hash = BitConverter.ToString(sha.ComputeHash(changed))
                .Replace("-", "").ToLowerInvariant();
        }
        string manifest = File.ReadAllText(Manifest);
        Match match = Regex.Match(
            manifest, "\\\"sha256\\\"\\s*:\\s*\\\"([0-9a-fA-F]{64})\\\"");
        if (!match.Success)
        {
            Fail("source image hash field was not found");
            return "";
        }
        manifest = manifest.Replace(match.Groups[1].Value, hash);
        File.WriteAllText(Manifest, manifest);
        return hash;
    }

    private static void Fail(string message)
    {
        Debug.LogError("UNITY_COMPOUND_STAGE2=FAIL " + message);
        EditorApplication.Exit(1);
    }
}"""


def create_compound_fixture(project: Path) -> None:
    source = project / "Assets" / "source.png"
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((4, 6, 20, 22), fill=(40, 180, 240, 255))
    image.save(source)
    scene = Scene()
    scene.load_image(image, "source.png")
    scene.image_path = "source.png"
    scene.image_path_kind = "relative"
    scene.add_object("hero", [(4, 6), (20, 6), (20, 22), (4, 22)], select=False)
    scene.objects["hero"].set_pivot(0.5, 0.5)
    scene.collision_shapes["hero"] = [(4, 6), (20, 6), (20, 22), (4, 22)]
    scene.collision_parts["hero"] = [
        [(4, 6), (12, 6), (12, 22), (4, 22)],
        [(12, 6), (20, 6), (20, 22), (12, 22)],
    ]
    metadata = export_scene_metadata(scene)
    manifest = build_integration_manifest(
        metadata,
        engine="unity",
        image_path=source,
        image_reference="source.png",
    )
    save_integration_manifest(
        manifest, project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
    )


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run(executable: Path, project: Path, temporary: Path) -> dict[str, Any]:
    log = temporary / "unity-stage2-compound.log"
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
        command, cwd=ROOT, capture_output=True, text=True, timeout=300, check=False
    )
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "output": sanitize(output, temporary),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    executable, version = (
        (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    )
    if not executable.is_file():
        raise RuntimeError("Unity executable was not found")
    output_dir = args.output or OUT
    output_dir.mkdir(parents=True, exist_ok=True)
    final_names = {
        "unity-stage2-compound.log",
        "stage2-unity-report.json",
        "stage2-unity-index.json",
    }
    if any(path.name in final_names for path in output_dir.iterdir()):
        raise RuntimeError(
            "Unity Stage 2 evidence already has final artifacts; refusing to overwrite"
        )
    with tempfile.TemporaryDirectory(prefix="neoeng-unity-compound-stage2-") as raw:
        temporary = Path(raw)
        project = temporary / "project"
        write_project(project, PACKAGE_ROOT, version)
        create_compound_fixture(project)
        runner_dir = project / "Assets" / "Editor"
        runner_dir.mkdir(parents=True)
        (runner_dir / "NeoEngStage2Runner.cs").write_text(
            RUNNER, encoding="utf-8", newline="\n"
        )
        result = run(executable, project, temporary)
        output = result["output"]
        markers = {
            "compound_paths_generated": "UNITY_COMPOUND_STAGE2=GENERATED" in output,
            "two_paths_reported": "UNITY_COMPOUND_STAGE2_PATHS=2" in output,
            "manual_secondary_path_preserved": "UNITY_COMPOUND_STAGE2=CONFLICT_BLOCKED"
            in output,
            "final_pass": "UNITY_COMPOUND_STAGE2=PASS" in output,
        }
        success = result["success"] and all(markers.values())
        if not success:
            (output_dir / "attempt-unity-stage2-failure.log").write_text(
                output, encoding="utf-8", newline="\n"
            )
            (output_dir / "attempt-unity-stage2-failure.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "stage": 2,
                        "status": "FAIL",
                        "engine": "unity",
                        "unity_version": version,
                        "markers": markers,
                        "run": result,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            raise RuntimeError("Unity compound-collider validation failed")
        report = {
            "schema_version": 1,
            "stage": 2,
            "status": "SUCCESS",
            "engine": "unity",
            "unity_version": version,
            "scenarios": markers,
            "contract": {
                "shape_type": "compound",
                "generated_path_count": 2,
                "generated_point_counts": [4, 4],
                "manual_secondary_path_conflict": "blocked",
            },
            "run": result,
            "fixture": {
                "source.png": digest(project / "Assets" / "source.png"),
                "manifest": digest(
                    project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
                ),
            },
        }
        (output_dir / "stage2-unity-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (output_dir / "unity-stage2-compound.log").write_text(
            output, encoding="utf-8", newline="\n"
        )
    files = {
        path.name: digest(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file()
    }
    (output_dir / "stage2-unity-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": 2,
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
    print("NATIVE_COMPOUND_COLLIDERS_STAGE2_UNITY=SUCCESS")
    print("COMPOUND_PATHS_GENERATED=PASS")
    print("SECONDARY_PATH_CONFLICT_BLOCKED=PASS")
    print("EVIDENCE_HASH_INDEX=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
