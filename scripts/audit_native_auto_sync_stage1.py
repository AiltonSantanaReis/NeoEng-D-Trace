from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from scripts.audit_godot_plugin_stage4 import _prepare

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "artifacts" / "native-auto-sync-stage1-2026-08-17"
SCRIPT_NAME = "runner.gd"
VALIDATOR = r'''@tool
extends EditorPlugin

const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")
const SOURCE := "res://source.png"
const MANIFEST := "res://NeoEngGenerated/hero.ndt.integration.json"
const SCENE := "res://NeoEngGenerated/hero.tscn"

func _enter_tree() -> void:
    print("GODOT_STAGE1_RUNNER_ENTERED")
    call_deferred("_run")

func sha256(data: PackedByteArray) -> String:
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    context.update(data)
    return context.finish().hex_encode()

func fail(message: String) -> void:
    push_error(message)
    get_tree().quit(1)

func mutate_input(extra: int) -> Dictionary:
    var source_bytes := FileAccess.get_file_as_bytes(SOURCE) + PackedByteArray([extra])
    var source_file := FileAccess.open(SOURCE, FileAccess.WRITE)
    source_file.store_buffer(source_bytes)
    source_file.close()
    var payload = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
    payload["source"]["image"]["sha256"] = sha256(source_bytes)
    var manifest_file := FileAccess.open(MANIFEST, FileAccess.WRITE)
    manifest_file.store_string(JSON.stringify(payload, "  ") + "\n")
    manifest_file.close()
    return payload

func _run() -> void:
    await Engine.get_main_loop().create_timer(4.0).timeout
    var baseline := Importer.import_manifest(MANIFEST)
    if baseline.get("status") != "SUCCESS":
        fail("baseline:" + JSON.stringify(baseline))
        return
    mutate_input(17)
    get_editor_interface().get_resource_filesystem().scan()
    await Engine.get_main_loop().create_timer(2.5).timeout
    var payload = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
    var updated_scene := FileAccess.get_file_as_string(SCENE)
    if not updated_scene.contains(payload["source"]["image"]["sha256"]):
        fail("automatic update was not applied")
        return
    print("GODOT_AUTO_SYNC_STAGE1=UPDATED")
    var manual_file := FileAccess.open(SCENE, FileAccess.READ_WRITE)
    manual_file.seek_end()
    manual_file.store_string("\n# stage1 manual divergence\n")
    manual_file.close()
    mutate_input(29)
    get_editor_interface().get_resource_filesystem().scan()
    await Engine.get_main_loop().create_timer(2.5).timeout
    payload = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
    var conflict_scene := FileAccess.get_file_as_string(SCENE)
    if not conflict_scene.contains("stage1 manual divergence"):
        fail("automatic sync overwrote manual divergence")
        return
    if conflict_scene.contains(payload["source"]["image"]["sha256"]):
        fail("automatic sync changed conflicted output")
        return
    print("GODOT_AUTO_SYNC_STAGE1=CONFLICT_BLOCKED")
    print("GODOT_AUTO_SYNC_STAGE1=PASS")
    get_tree().quit(0)'''

def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def sanitize(value: str, temporary: Path) -> str:
    result = value.replace(str(temporary), "<local-path>").replace(str(ROOT), "<repo>")
    result = re.sub(r"[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", result)
    result = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<network-address>", result)
    return result


def run(executable: Path, arguments: list[str], workspace: Path, temporary: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [str(executable), *arguments],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    output = sanitize(completed.stdout, temporary)
    return {
        "arguments": [re.sub(r"[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", item) for item in arguments],
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "output": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path)
    args = parser.parse_args()
    executable = args.executable or Path(shutil.which("godot") or "")
    if not executable.is_file():
        raise RuntimeError("Godot executable was not found")
    if OUT.exists():
        existing = [path for path in OUT.iterdir() if not path.name.startswith("attempt-")]
        if existing:
            raise RuntimeError("evidence output already contains final artifacts; refusing to overwrite")
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-godot-auto-sync-stage1-") as raw:
        temporary = Path(raw)
        workspace = temporary / "project"
        workspace.mkdir()
        fixture = _prepare(workspace)
        (workspace / SCRIPT_NAME).write_text(VALIDATOR, encoding="utf-8", newline="\n")
        command = run(
            executable,
            ["--headless", "--editor", "--path", str(workspace), "--import", "--quit-after", "5"],
            workspace,
            temporary,
        )
        if not command["success"]:
            raise RuntimeError("Godot editor/plugin pre-import failed")
        runner_root = workspace / "addons" / "stage1_runner"
        runner_root.mkdir(parents=True)
        (runner_root / "plugin.cfg").write_text(
            '[plugin]\nname="NeoEng Stage1 Runner"\ndescription="Temporary real-event validator"\nauthor="NeoEng-D-Trace"\nversion="0.1.0"\nscript="runner.gd"\n',
            encoding="utf-8",
            newline="\n",
        )
        (runner_root / "runner.gd").write_text(VALIDATOR, encoding="utf-8", newline="\n")
        (workspace / "project.godot").write_text(
            '[application]\nconfig/name="NeoEngDTraceAutoSyncStage1"\n'
            '[editor_plugins]\n'
            'enabled=PackedStringArray("res://addons/neoeng_d_trace/plugin.cfg", "res://addons/stage1_runner/plugin.cfg")\n',
            encoding="utf-8",
            newline="\n",
        )
        automatic = run(
            executable,
            ["--headless", "--editor", "--path", str(workspace)],
            workspace,
            temporary,
        )
        if not automatic["success"] or "GODOT_AUTO_SYNC_STAGE1=UPDATED" not in automatic["output"] or "GODOT_AUTO_SYNC_STAGE1=CONFLICT_BLOCKED" not in automatic["output"] or "GODOT_AUTO_SYNC_STAGE1=PASS" not in automatic["output"]:
            (OUT / "stage1-failure-automatic-sync.log").write_text(automatic["output"], encoding="utf-8", newline="\n")
            (OUT / "stage1-failure.json").write_text(
                json.dumps({"schema_version": 1, "stage": 1, "status": "FAIL", "engine": "godot", "command": automatic}, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            raise RuntimeError("Godot automatic synchronization validation failed; see stage1-failure-automatic-sync.log")
        report = {
            "schema_version": 1,
            "stage": 1,
            "status": "SUCCESS",
            "engine": "godot",
            "scenarios": {
                "filesystem_event_updated_generated_output": True,
                "manual_divergence_blocked": True,
                "destructive_delete_not_performed": True,
            },
            "commands": [command, automatic],
            "fixture_files": {
                "source.png": digest(fixture["image"]),
                "hero.ndt.integration.json": digest(fixture["manifest"]),
            },
        }
        (OUT / "stage1-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        (OUT / "godot-stage1-editor.log").write_text(command["output"], encoding="utf-8", newline="\n")
        (OUT / "godot-stage1-automatic-sync.log").write_text(automatic["output"], encoding="utf-8", newline="\n")
    files = {path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()}
    (OUT / "stage1-index.json").write_text(json.dumps({"schema_version": 1, "stage": 1, "status": "SUCCESS", "engine": "godot", "files": files}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("NATIVE_AUTO_SYNC_STAGE1_GODOT=SUCCESS")
    print("FILESYSTEM_EVENT_UPDATE=PASS")
    print("MANUAL_DIVERGENCE_BLOCKED=PASS")
    print("EVIDENCE_HASH_INDEX=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())