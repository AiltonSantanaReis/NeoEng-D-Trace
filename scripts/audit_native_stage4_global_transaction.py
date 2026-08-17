"""Run a real Godot/Unity multi-manifest transaction audit."""

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

from scripts.audit_godot_plugin_stage4 import ADDON_SOURCE
from scripts.audit_unity_import_stage6 import (
    PACKAGE_ROOT,
    create_fixture,
    sanitize,
    write_project,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / "native-stage4-global-transaction-2026-08-17"
)
GODOT_VALIDATOR = r"""extends SceneTree

const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")
const KeepPath = "res://NeoEngGenerated/keep.txt"

func _init() -> void:
    var first := Importer.import_project("res://NeoEngGenerated")
    if (
        first.get("status") != "FAILED"
        or first.get("transaction") != "GLOBAL"
        or first.get("rollback") != "RESTORED"
    ):
        _fail("global rollback result is invalid")
        return
    if FileAccess.file_exists("res://NeoEngGenerated/hero.tscn"):
        _fail("partial Godot output survived global rollback")
        return
    if (
        not FileAccess.file_exists(KeepPath)
        or FileAccess.get_file_as_string(KeepPath) != "preserved\n"
    ):
        _fail("pre-existing Godot output was not restored")
        return
    print("GODOT_STAGE4_GLOBAL_ROLLBACK=PASS")
    if not (
        DirAccess.remove_absolute(
            "res://NeoEngGenerated/bad.ndt.integration.json"
        ) == OK
    ):
        _fail("invalid fixture manifest could not be removed")
        return
    var applied := Importer.import_project("res://NeoEngGenerated")
    if applied.get("status") != "SUCCESS" or applied.get("transaction") != "GLOBAL":
        _fail("global Godot import failed")
        return
    var first_hash := _tree_hash("res://NeoEngGenerated")
    var repeated := Importer.import_project("res://NeoEngGenerated")
    if (
        repeated.get("status") != "SUCCESS"
        or _tree_hash("res://NeoEngGenerated") != first_hash
    ):
        _fail("repeated Godot global import is not deterministic")
        return
    print("GODOT_STAGE4_GLOBAL_IMPORT=PASS")
    print("GODOT_STAGE4_GLOBAL_REPEAT=PASS")
    print("NATIVE_STAGE4_GLOBAL_GODOT=SUCCESS")
    quit(0)

func _tree_hash(root: String) -> String:
    var paths: Array[String] = []
    _collect(root, root, paths)
    paths.sort()
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    for relative in paths:
        context.update(relative.to_utf8_buffer())
        context.update(FileAccess.get_file_as_bytes(root.path_join(relative)))
    return context.finish().hex_encode()

func _collect(root: String, current: String, paths: Array[String]) -> void:
    for file_name in DirAccess.get_files_at(current):
        var path := current.path_join(file_name)
        paths.append(path.trim_prefix(root).trim_prefix("/"))
    var directories := DirAccess.get_directories_at(current)
    directories.sort()
    for directory_name in directories:
        _collect(root, current.path_join(directory_name), paths)

func _fail(message: String) -> void:
    push_error("GODOT_STAGE4_GLOBAL=FAIL " + message)
    quit(1)
"""
UNITY_RUNNER = r"""using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using NeoEng.DTrace.Editor;

[InitializeOnLoad]
internal static class NeoEngStage4GlobalRunner
{
    private const string First = "Assets/NeoEngInput/hero.ndt.integration.json";
    private const string Second = "Assets/NeoEngInput/bad.ndt.integration.json";
    private const string Generated = "Assets/NeoEngGenerated";
    private const string Keep = Generated + "/keep.txt";
    private const string KeepValue = "preserved\n";
    private const string MarkerValue = "generator=neoeng_d_trace\nversion=0.2.0\n";

    static NeoEngStage4GlobalRunner() { EditorApplication.delayCall += Begin; }

    private static void Begin()
    {
        Directory.CreateDirectory(ProjectPath(Generated));
        File.WriteAllText(ProjectPath(Generated + "/.neoeng-generated"), MarkerValue);
        File.WriteAllText(ProjectPath(Keep), KeepValue);
        UnityImportGenerator.ImportBatchResult failed =
            UnityImportGenerator.ImportManifests(new[] { First, Second });
        bool hasPartial = HasUnexpectedOutput();
        bool keepRestored = File.Exists(ProjectPath(Keep))
            && File.ReadAllText(ProjectPath(Keep)) == KeepValue;
        if (failed.Success || hasPartial || !keepRestored)
        {
            Fail("partial Unity output survived global rollback");
            return;
        }
        Debug.Log("UNITY_STAGE4_GLOBAL_ROLLBACK=PASS");
        File.Delete(ProjectPath(Second));
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
        UnityImportGenerator.ImportBatchResult applied =
            UnityImportGenerator.ImportManifests(new[] { First });
        if (!applied.Success)
        {
            Fail("global Unity import failed: " + applied.ErrorSummary());
            return;
        }
        string firstHash = TreeHash(ProjectPath(Generated));
        UnityImportGenerator.ImportBatchResult repeated =
            UnityImportGenerator.ImportManifests(new[] { First });
        if (!repeated.Success || TreeHash(ProjectPath(Generated)) != firstHash)
        {
            Fail("repeated Unity global import is not deterministic");
            return;
        }
        Debug.Log("UNITY_STAGE4_GLOBAL_IMPORT=PASS");
        Debug.Log("UNITY_STAGE4_GLOBAL_REPEAT=PASS");
        Debug.Log("NATIVE_STAGE4_GLOBAL_UNITY=SUCCESS");
        EditorApplication.Exit(0);
    }

    private static bool HasUnexpectedOutput()
    {
        if (!Directory.Exists(ProjectPath(Generated))) return false;
        string[] files = Directory.GetFiles(
            ProjectPath(Generated), "*", SearchOption.AllDirectories);
        return files.Any(path =>
        {
            string name = Path.GetFileName(path);
            if (name.EndsWith(".meta", StringComparison.OrdinalIgnoreCase))
                name = name.Substring(0, name.Length - 5);
            return name != ".neoeng-generated" && name != "keep.txt";
        });
    }

    private static string ProjectPath(string assetPath)
    {
        return Path.Combine(
            Directory.GetParent(Application.dataPath).FullName,
            assetPath.Replace('/', Path.DirectorySeparatorChar));
    }

    private static string TreeHash(string root)
    {
        using (SHA256 hash = SHA256.Create())
        using (MemoryStream stream = new MemoryStream())
        {
            foreach (string file in Directory.GetFiles(
                root, "*", SearchOption.AllDirectories
            )
                .OrderBy(path => path, StringComparer.Ordinal))
            {
                string relative = file.Substring(root.Length)
                    .TrimStart(
                        Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar
                    )
                    .Replace(Path.DirectorySeparatorChar, '/');
                byte[] name = System.Text.Encoding.UTF8.GetBytes(relative);
                stream.Write(name, 0, name.Length);
                byte[] content = File.ReadAllBytes(file);
                stream.Write(content, 0, content.Length);
            }
            return BitConverter.ToString(hash.ComputeHash(stream.ToArray()))
                .Replace("-", "").ToLowerInvariant();
        }
    }

    private static void Fail(string message)
    {
        Debug.LogError("UNITY_STAGE4_GLOBAL=FAIL " + message);
        EditorApplication.Exit(1);
    }
}
"""


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def sanitize_stage4(text: str, temporary_root: Path) -> str:
    """Apply shared sanitization plus stage-specific privacy redactions."""

    value = sanitize(text, temporary_root)
    value = re.sub(
        r"(?im)^(\s*Id:)\s+\d+-UnityPers\S*\s*$",
        r"\1 <redacted>",
        value,
    )
    return re.sub(r"(?im)^Date:.*$", "Date: <redacted>", value)


def run(
    executable: Path,
    project: Path,
    temporary: Path,
    method: str | None = None,
) -> dict[str, Any]:
    log = temporary / (project.name + ".log")
    if executable.name.lower().startswith("godot"):
        command = [str(executable), "--headless", "--path", str(project)]
        if method:
            command += ["--script", method]
        else:
            command += ["--editor", "--import", "--quit-after", "5"]
    else:
        command = [
            str(executable),
            "-batchmode",
            "-nographics",
            "-projectPath",
            str(project),
        ]
    command += ["-logFile", str(log)]
    completed = subprocess.run(
        command,
        cwd=(
            project if method and executable.name.lower().startswith("godot") else ROOT
        ),
        capture_output=True,
        text=True,
        timeout=360,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "output": sanitize_stage4(output, temporary),
    }


def summarize_run(run: dict[str, Any], markers: tuple[str, ...]) -> dict[str, Any]:
    return {
        "returncode": run["returncode"],
        "success": run["success"],
        "markers": {marker: marker in run["output"] for marker in markers},
    }


def prepare_godot(workspace: Path) -> None:
    shutil.copytree(ADDON_SOURCE, workspace / "addons" / "neoeng_d_trace")
    generated = workspace / "NeoEngGenerated"
    generated.mkdir(parents=True)
    (generated / "keep.txt").write_text("preserved\n", encoding="utf-8", newline="\n")
    source = workspace / "source.png"
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (24, 16), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((2, 2, 14, 13), fill=(30, 180, 240, 255))
    image.save(source)
    from src.exporters.integration_manifest import (
        build_integration_manifest,
        save_integration_manifest,
    )
    from src.exporters.json_exporter import export_scene_metadata
    from src.models.scene import Scene

    scene = Scene()
    scene.add_object("hero", [(2, 2), (14, 2), (14, 13), (2, 13)])
    manifest = build_integration_manifest(
        export_scene_metadata(scene),
        engine="godot",
        image_path=source,
        image_reference="source.png",
    )
    save_integration_manifest(manifest, generated / "hero.ndt.integration.json")
    invalid = json.loads(json.dumps(manifest))
    invalid["metadata"]["sprites"][0]["id"] = "bad/id"
    (generated / "bad.ndt.integration.json").write_text(
        json.dumps(invalid, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "project.godot").write_text(
        '[application]\nconfig/name="NeoEngStage4Global"\n',
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "validate_stage4_global.gd").write_text(
        GODOT_VALIDATOR, encoding="utf-8", newline="\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--unity", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if not args.godot.is_file() or not args.unity.is_file():
        raise RuntimeError("both real engine executables are required")
    output = args.output
    if output.exists():
        raise RuntimeError("refusing to overwrite existing stage4 evidence")
    output.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": 4,
        "scope": "global transaction and rollback of multiple manifests",
        "status": "FAILED",
    }

    def persist_failure(error: Exception) -> None:
        report["error_type"] = type(error).__name__
        report["error"] = str(error)
        (output / "attempt-stage4-failure.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        runs = report.get("engines", {})
        combined = (
            "\n".join(item["run"]["output"] for item in runs.values() if "run" in item)
            + "\n"
        )
        (output / "attempt-stage4-engine.log").write_text(
            combined, encoding="utf-8", newline="\n"
        )

    with tempfile.TemporaryDirectory(prefix="neoeng-stage4-global-") as raw:
        temporary = Path(raw)
        godot_project = temporary / "godot"
        godot_project.mkdir()
        prepare_godot(godot_project)
        godot_preimport = run(args.godot, godot_project, temporary)
        if godot_preimport["returncode"] != 0:
            report["engines"] = {
                "godot": {"version": "4.7.stable", "run": godot_preimport}
            }
            error = RuntimeError("real Godot pre-import failed")
            persist_failure(error)
            raise error
        godot_validation = run(
            args.godot, godot_project, temporary, "validate_stage4_global.gd"
        )
        godot_run = {
            "returncode": max(
                godot_preimport["returncode"], godot_validation["returncode"]
            ),
            "success": godot_preimport["success"] and godot_validation["success"],
            "output": godot_preimport["output"] + "\n" + godot_validation["output"],
        }
        unity_project = temporary / "unity"
        write_project(unity_project, PACKAGE_ROOT, args.unity.parents[1].name)
        create_fixture(unity_project)
        second = unity_project / "Assets" / "NeoEngInput" / "bad.ndt.integration.json"
        first_payload = json.loads(
            (
                unity_project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
            ).read_text(encoding="utf-8")
        )
        first_payload["metadata"]["sprites"][0]["id"] = "bad/id"
        second.write_text(
            json.dumps(first_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        runner = unity_project / "Assets" / "Editor" / "NeoEngStage4GlobalRunner.cs"
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_text(UNITY_RUNNER, encoding="utf-8", newline="\n")
        unity_run = run(args.unity, unity_project, temporary)
        report["engines"] = {"godot": {"version": "4.7.stable", "run": godot_run}}
        if (
            godot_run["returncode"] != 0
            or "NATIVE_STAGE4_GLOBAL_GODOT=SUCCESS" not in godot_run["output"]
        ):
            error = RuntimeError("real Godot global transaction audit failed")
            persist_failure(error)
            raise error
        report["engines"]["unity"] = {
            "version": args.unity.parents[1].name,
            "run": unity_run,
        }

        if (
            unity_run["returncode"] != 0
            or "NATIVE_STAGE4_GLOBAL_UNITY=SUCCESS" not in unity_run["output"]
        ):
            error = RuntimeError("real Unity global transaction audit failed")
            persist_failure(error)
            raise error
        report["engines"]["godot"]["run"] = summarize_run(
            godot_run,
            (
                "GODOT_STAGE4_GLOBAL_ROLLBACK=PASS",
                "GODOT_STAGE4_GLOBAL_IMPORT=PASS",
                "GODOT_STAGE4_GLOBAL_REPEAT=PASS",
                "NATIVE_STAGE4_GLOBAL_GODOT=SUCCESS",
            ),
        )
        report["engines"]["unity"]["run"] = summarize_run(
            unity_run,
            (
                "UNITY_STAGE4_GLOBAL_ROLLBACK=PASS",
                "UNITY_STAGE4_GLOBAL_IMPORT=PASS",
                "UNITY_STAGE4_GLOBAL_REPEAT=PASS",
                "NATIVE_STAGE4_GLOBAL_UNITY=SUCCESS",
            ),
        )
        report["status"] = "SUCCESS"
        report["fixtures"] = {
            "godot_source": digest(godot_project / "source.png"),
            "godot_manifest": digest(
                godot_project / "NeoEngGenerated" / "hero.ndt.integration.json"
            ),
            "unity_source": digest(unity_project / "Assets" / "source.png"),
        }
    (output / "stage4-global-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    combined = (
        "\n".join(
            (
                {"godot": godot_run, "unity": unity_run}[engine]["output"]
                for engine in ("godot", "unity")
            )
        )
        + "\n"
    )
    (output / "stage4-global-engine.log").write_text(
        combined, encoding="utf-8", newline="\n"
    )
    files = {}
    for path in sorted(output.iterdir()):
        if path.is_file():
            files[path.name] = digest(path)
    (output / "stage4-global-index.json").write_text(
        json.dumps(
            {"schema_version": 1, "stage": 4, "status": "SUCCESS", "files": files},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("NATIVE_STAGE4_GLOBAL=SUCCESS")
    print("GLOBAL_ROLLBACK_GODOT=PASS")
    print("GLOBAL_ROLLBACK_UNITY=PASS")
    print("REPEAT_IMPORT_DETERMINISTIC=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
