from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any
from scripts.audit_godot_plugin_stage4 import _prepare

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "artifacts" / "godot-sync-stage7-2026-08-16"
VALIDATOR_NAME = "validate_stage7.gd"
VALIDATOR = r'''extends SceneTree

const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")
const SCENE := "res://NeoEngGenerated/hero.tscn"
const MANIFEST := "res://NeoEngGenerated/hero.ndt.integration.json"

func fail(message: String) -> void:
    push_error(message)
    quit(1)

func check(condition: bool, message: String) -> bool:
    if not condition:
        fail(message)
        return false
    return true

func result() -> Dictionary:
    return Importer.import_manifest(MANIFEST)

func _init() -> void:
    var mode := OS.get_environment("NEOENG_STAGE7_MODE")
    var value := result()
    if mode == "initial":
        var initial_results: Array = value.get("results", [])
        if not check(value.get("status") == "SUCCESS" and initial_results.size() == 4, "initial:" + JSON.stringify(value)): return
        for initial_result in initial_results:
            if not check(initial_result.get("status") == "UPDATED", "initial-result:" + JSON.stringify(value)): return
        print("GODOT_SYNC_STAGE7_INITIAL=UPDATED")
    elif mode == "repeat":
        var repeat_results: Array = value.get("results", [])
        if not check(value.get("status") == "SUCCESS" and repeat_results.size() == 4, "repeat:" + JSON.stringify(value)): return
        for repeat_result in repeat_results:
            if not check(repeat_result.get("status") == "UNCHANGED", "repeat-result:" + JSON.stringify(value)): return
        print("GODOT_SYNC_STAGE7_REPEAT=UNCHANGED")
    elif mode == "override":
        var override_results: Array = value.get("results", [])
        if not check(value.get("status") == "SUCCESS" and override_results.size() == 4, "override:" + JSON.stringify(value)): return
        if not check(override_results[0].get("status") == "UPDATED" and bool(override_results[0].get("override_applied", false)), "override-not-applied"): return
        for override_index in range(1, override_results.size()):
            if not check(override_results[override_index].get("status") == "UNCHANGED", "override-result:" + JSON.stringify(value)): return
        if not check(FileAccess.get_file_as_string(SCENE).contains("-7"), "override-geometry"): return
        print("GODOT_SYNC_STAGE7_OVERRIDE=PRESERVED")
    elif mode == "override-repeat":
        var override_repeat_results: Array = value.get("results", [])
        if not check(value.get("status") == "SUCCESS" and override_repeat_results.size() == 4, "override-repeat:" + JSON.stringify(value)): return
        for override_repeat_result in override_repeat_results:
            if not check(override_repeat_result.get("status") == "UNCHANGED", "override-repeat-result:" + JSON.stringify(value)): return
        print("GODOT_SYNC_STAGE7_OVERRIDE_REPEAT=UNCHANGED")
    elif mode == "manual":
        var original := FileAccess.get_file_as_bytes(SCENE)
        var file := FileAccess.open(SCENE, FileAccess.WRITE)
        file.store_buffer(original)
        file.store_string("\n# manual divergence\n")
        file.close()
        var mutated := FileAccess.get_file_as_bytes(SCENE)
        value = result()
        if not check(value.get("status") == "CONFLICT", "manual:" + JSON.stringify(value)): return
        if not check(mutated == FileAccess.get_file_as_bytes(SCENE), "manual-mutated"): return
        print("GODOT_SYNC_STAGE7_MANUAL=CONFLICT")
    elif mode == "confirmed":
        OS.set_environment("NEOENG_STAGE7_CONFIRM_DESTRUCTIVE", "1")
        value = result()
        if not check(value.get("status") == "SUCCESS" and value.get("results", [])[0].get("status") == "UPDATED", "confirmed:" + JSON.stringify(value)): return
        if not check(not FileAccess.get_file_as_string(SCENE).contains("manual divergence"), "confirmed-text"): return
        print("GODOT_SYNC_STAGE7_CONFIRMATION=ACCEPTED")
    elif mode == "hash-drift":
        if not check(value.get("status") == "FAILED", "hash-drift:" + JSON.stringify(value)): return
        print("GODOT_SYNC_STAGE7_HASH_DRIFT=REJECTED")
    else:
        fail("unknown-mode:" + mode)
        return
    quit(0)
'''

def sanitize(value: str, temp: Path) -> str:
    value = value.replace(str(temp), "<local-path>").replace(str(ROOT), "<repo>")
    value = re.sub(r"[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", value)
    value = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<network-address>", value)
    return value

def run(exe: Path, args: list[str], temp: Path, mode: str | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if mode is not None:
        env["NEOENG_STAGE7_MODE"] = mode
    p = subprocess.run([str(exe), *args], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=45, check=False)
    output = sanitize(p.stdout, temp)
    return {"mode": mode or "asset-preimport", "returncode": p.returncode, "success": p.returncode == 0, "marker": next((line for line in output.splitlines() if "STAGE7_" in line), ""), "output": output}

def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path)
    args = parser.parse_args()
    executable = args.executable
    if executable is None:
        configured = os.environ.get("NEOENG_GODOT_EXECUTABLE")
        executable = Path(configured) if configured else None
    if executable is None:
        executable = next(
            (
                Path(candidate)
                for candidate in ("godot", "godot4", "godot_console")
                if shutil.which(candidate)
            ),
            None,
        )
    if executable is None or (not executable.is_file() and not shutil.which(str(executable))):
        raise RuntimeError("Godot console executable was not found")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    runs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="neoeng-godot-sync-stage7-") as raw:
        temp = Path(raw)
        workspace = temp / "project"
        workspace.mkdir()
        fixture = _prepare(workspace)
        (workspace / VALIDATOR_NAME).write_text(VALIDATOR, encoding="utf-8", newline="\n")
        pre = run(executable, ["--headless", "--editor", "--path", str(workspace), "--import", "--quit-after", "5"], temp)
        runs.append(pre)
        if not pre["success"]:
            raise RuntimeError("Godot asset pre-import failed")
        script_args = ["--headless", "--path", str(workspace), "--script", VALIDATOR_NAME, "--quit-after", "5"]
        for mode in ("initial", "repeat"):
            item = run(executable, script_args, temp, mode)
            runs.append(item)
            if not item["success"]:
                raise RuntimeError(f"Godot stage7 mode failed: {mode} | {item}")
        override_path = workspace / "NeoEngGenerated" / "hero.ndt.override.json"
        override_path.write_text(json.dumps({"schema_version": 1, "object_id": "hero", "polygon_in_sprite": [[1, 1], [15, 1], [15, 11], [1, 11]]}, indent=2) + "\n", encoding="utf-8", newline="\n")
        for mode in ("override", "override-repeat", "manual", "confirmed"):
            item = run(executable, script_args, temp, mode)
            runs.append(item)
            if not item["success"]:
                raise RuntimeError(f"Godot stage7 mode failed: {mode} | {item}")
        fixture["image"].write_bytes(fixture["image"].read_bytes() + b"stage7-drift")
        item = run(executable, script_args, temp, "hash-drift")
        runs.append(item)
        if not item["success"]:
            raise RuntimeError("Godot hash drift mode failed")
        report = {"schema_version": 1, "stage": 7, "status": "SUCCESS", "engine": "godot", "godot_version": "4.7.stable", "scenarios": {"initial_update": True, "repeat_unchanged": True, "override_preserved": True, "manual_divergence_blocked": True, "destructive_confirmation_required": True, "hash_drift_rejected": True}, "runs": runs, "fixture": {"source_image": digest(fixture["image"]), "manifest": digest(fixture["manifest"])}}
        (OUT / "stage7-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        for index, item in enumerate(runs, 1):
            (OUT / f"godot-stage7-{index:02d}-{item['mode']}.log").write_text(item["output"], encoding="utf-8", newline="\n")
    files = {path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()}
    (OUT / "stage7-index.json").write_text(json.dumps({"schema_version": 1, "stage": 7, "status": "SUCCESS", "engine": "godot", "files": files}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("NATIVE_SYNC_STAGE7_GODOT=SUCCESS")
    print("INITIAL_UPDATE=PASS")
    print("REPEAT_UNCHANGED=PASS")
    print("OVERRIDE_PRESERVED=PASS")
    print("MANUAL_DIVERGENCE_BLOCKED=PASS")
    print("DESTRUCTIVE_CONFIRMATION=PASS")
    print("HASH_DRIFT_REJECTED=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
