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

from scripts.audit_unity_import_stage6 import PACKAGE_ROOT, ROOT, create_fixture, discover_unity, sanitize, write_project
from src.exporters.integration_manifest import build_advanced_integration_manifest, save_integration_manifest

OUT = ROOT / "docs" / "evidence" / "artifacts" / "native-auto-sync-stage1-2026-08-17"
RUNNER = r'''using System;
using System.IO;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace;
using NeoEng.DTrace.Editor;

[InitializeOnLoad]
internal static class NeoEngStage1Runner
{
    private const string Source = "Assets/atlas.png";
    private const string Manifest = "Assets/NeoEngInput/hero.ndt.integration.json";
    private const string Prefab = "Assets/NeoEngGenerated/hero.prefab";
    private const string Metadata = "Assets/NeoEngGenerated/hero.metadata.asset";
    private static int phase = -1;
    private static double nextAction;
    private static string firstHash;
    private static string secondHash;
    private static float manualPointX;

    static NeoEngStage1Runner() { EditorApplication.delayCall += Begin; }

    private static void Begin()
    {
        UnityImportGenerator.ImportResult baseline = UnityImportGenerator.ImportManifest(Manifest);
        if (!baseline.Success) { Fail("baseline:" + baseline.ErrorSummary()); return; }
        phase = 0;
        Schedule(2.0);
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
        if (phase == 0)
        {
            firstHash = MutateInput(17);
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
            phase = 1;
            Schedule(4.0);
            return;
        }
        if (phase == 1)
        {
            NeoEngImportedSpriteMetadata metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedSpriteMetadata>(Metadata);
            if (metadata == null || metadata.sourceImageHash != firstHash) { Fail("automatic update was not applied"); return; }
            Debug.Log("UNITY_AUTO_SYNC_STAGE1=UPDATED");
            GameObject root = PrefabUtility.LoadPrefabContents(Prefab);
            PolygonCollider2D collider = root == null ? null : root.GetComponent<PolygonCollider2D>();
            if (collider == null || collider.pathCount != 1)
            {
                if (root != null) PrefabUtility.UnloadPrefabContents(root);
                Fail("generated collider fixture is invalid");
                return;
            }
            Vector2[] points = collider.GetPath(0);
            points[0] += new Vector2(0.25f, 0.0f);
            manualPointX = points[0].x;
            collider.SetPath(0, points);
            PrefabUtility.SaveAsPrefabAsset(root, Prefab);
            PrefabUtility.UnloadPrefabContents(root);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
            secondHash = MutateInput(29);
            AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
            phase = 2;
            Schedule(4.0);
            return;
        }
        if (phase == 2)
        {
            NeoEngImportedSpriteMetadata metadata = AssetDatabase.LoadAssetAtPath<NeoEngImportedSpriteMetadata>(Metadata);
            GameObject root = PrefabUtility.LoadPrefabContents(Prefab);
            PolygonCollider2D collider = root == null ? null : root.GetComponent<PolygonCollider2D>();
            bool preserved = collider != null && collider.pathCount == 1 && Mathf.Abs(collider.GetPath(0)[0].x - manualPointX) < 0.0001f;
            if (root != null) PrefabUtility.UnloadPrefabContents(root);
            if (metadata == null || !preserved) { Fail("automatic sync overwrote manual divergence"); return; }
            if (metadata.sourceImageHash == secondHash) { Fail("automatic sync changed conflicted metadata"); return; }
            Debug.Log("UNITY_AUTO_SYNC_STAGE1=CONFLICT_BLOCKED");
            Debug.Log("UNITY_AUTO_SYNC_STAGE1=PASS");
            EditorApplication.Exit(0);
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
        using (SHA256 sha = SHA256.Create()) hash = BitConverter.ToString(sha.ComputeHash(changed)).Replace("-", "").ToLowerInvariant();
        string manifest = File.ReadAllText(Manifest);
        Match match = Regex.Match(manifest, "\\\"sha256\\\"\\s*:\\s*\\\"([0-9a-fA-F]{64})\\\"");
        if (!match.Success) { Fail("source image hash field was not found"); return ""; }
        manifest = manifest.Replace(match.Groups[1].Value, hash);
        File.WriteAllText(Manifest, manifest);
        return hash;
    }

    private static void Fail(string message)
    {
        Debug.LogError("UNITY_AUTO_SYNC_STAGE1=FAIL " + message);
        EditorApplication.Exit(1);
    }
}'''

def create_advanced_fixture(project: Path) -> None:
    create_fixture(project)
    source = project / "Assets" / "source.png"
    atlas = project / "Assets" / "atlas.png"
    shutil.copy2(source, atlas)
    manifest_path = project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    advanced = build_advanced_integration_manifest(
        payload["metadata"],
        engine="unity",
        image_path=atlas,
        image_reference="atlas.png",
        atlas_pages=[
            {
                "id": "atlas_0",
                "file_path": atlas,
                "path": "atlas.png",
                "entries": [
                    {
                        "id": "hero",
                        "rect": {"x": 4, "y": 6, "w": 17, "h": 17},
                        "packed_rect": {"x": 3, "y": 5, "w": 19, "h": 19},
                        "extrusion": 1,
                        "rotated": False,
                    }
                ],
            }
        ],
    )
    save_integration_manifest(advanced, manifest_path)

def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run(executable: Path, project: Path, temporary: Path) -> dict[str, Any]:
    log = temporary / "unity-stage1-auto-sync.log"
    command = [str(executable), "-batchmode", "-nographics", "-projectPath", str(project), "-logFile", str(log)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "arguments": [re.sub(r"[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", item) for item in command[1:]],
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "output": sanitize(output, temporary),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output_dir = args.output or OUT
    executable, version = (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    if not executable.is_file():
        raise RuntimeError("Unity executable was not found")
    output_dir.mkdir(parents=True, exist_ok=True)
    final_names = {"unity-stage1-auto-sync.log", "stage1-unity-report.json", "stage1-unity-index.json"}
    if any(path.name in final_names for path in output_dir.iterdir()):
        raise RuntimeError("Unity Stage 1 evidence already has final artifacts; refusing to overwrite")
    with tempfile.TemporaryDirectory(prefix="neoeng-unity-auto-sync-stage1-") as raw:
        temporary = Path(raw)
        project = temporary / "project"
        write_project(project, PACKAGE_ROOT, version)
        create_advanced_fixture(project)
        runner_dir = project / "Assets" / "Editor"
        runner_dir.mkdir(parents=True)
        (runner_dir / "NeoEngStage1Runner.cs").write_text(RUNNER, encoding="utf-8", newline="\n")
        run_result = run(executable, project, temporary)
        if not run_result["success"] or "UNITY_AUTO_SYNC_STAGE1=UPDATED" not in run_result["output"] or "UNITY_AUTO_SYNC_STAGE1=CONFLICT_BLOCKED" not in run_result["output"] or "UNITY_AUTO_SYNC_STAGE1=PASS" not in run_result["output"]:
            (output_dir / "attempt-unity-stage1-failure.log").write_text(run_result["output"], encoding="utf-8", newline="\n")
            (output_dir / "attempt-unity-stage1-failure.json").write_text(json.dumps({"schema_version": 1, "stage": 1, "status": "FAIL", "engine": "unity", "unity_version": version, "run": run_result}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            raise RuntimeError("Unity automatic synchronization validation failed")
        report = {
            "schema_version": 1,
            "stage": 1,
            "status": "SUCCESS",
            "engine": "unity",
            "unity_version": version,
            "scenarios": {"asset_postprocessor_updated_generated_output": True, "manual_divergence_blocked": True, "destructive_delete_not_performed": True},
            "run": run_result,
            "fixture": {"atlas.png": digest(project / "Assets" / "atlas.png"), "manifest": digest(project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json")},
        }
        (output_dir / "stage1-unity-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        (output_dir / "unity-stage1-auto-sync.log").write_text(run_result["output"], encoding="utf-8", newline="\n")
    files = {path.name: digest(path) for path in sorted(output_dir.iterdir()) if path.is_file()}
    (output_dir / "stage1-unity-index.json").write_text(json.dumps({"schema_version": 1, "stage": 1, "status": "SUCCESS", "engine": "unity", "unity_version": version, "files": files}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("NATIVE_AUTO_SYNC_STAGE1_UNITY=SUCCESS")
    print("ASSET_POSTPROCESSOR_UPDATE=PASS")
    print("MANUAL_DIVERGENCE_BLOCKED=PASS")
    print("EVIDENCE_HASH_INDEX=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())