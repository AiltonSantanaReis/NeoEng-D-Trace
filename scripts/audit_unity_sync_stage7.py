from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from typing import Any
from scripts.audit_unity_import_stage6 import PACKAGE_ROOT, ROOT, create_fixture, discover_unity, sanitize, write_project

OUT = ROOT / "docs" / "evidence" / "artifacts" / "unity-sync-stage7-2026-08-16"
IMPORT_METHOD = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessImport"
MUTATE_METHOD = "NeoEng.DTrace.Editor.UnityImportGenerator.MutateGeneratedPrefabFixture"

def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def run_unity(exe: Path, project: Path, temp: Path, method: str, report: Path | None = None, confirm: bool = False) -> dict[str, Any]:
    env = os.environ.copy()
    if report is not None:
        env["NEOENG_STAGE6_REPORT"] = str(report)
        env["NEOENG_STAGE6_MANIFEST"] = "Assets/NeoEngInput/hero.ndt.integration.json"
    else:
        env.pop("NEOENG_STAGE6_REPORT", None)
        env.pop("NEOENG_STAGE6_MANIFEST", None)
    if confirm:
        env["NEOENG_STAGE7_CONFIRM_DESTRUCTIVE"] = "1"
    else:
        env.pop("NEOENG_STAGE7_CONFIRM_DESTRUCTIVE", None)
    log = temp / f"{project.name}-{method.split('.')[-1]}-{len(list(temp.glob('*.log'))):02d}.log"
    command = [str(exe), "-batchmode", "-nographics", "-quit", "-projectPath", str(project), "-executeMethod", method, "-logFile", str(log)]
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=300, check=False)
    if report is not None:
        for _ in range(60):
            if report.is_file():
                break
            time.sleep(0.5)
    for _ in range(60):
        if log.is_file():
            break
        time.sleep(0.5)
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {"method": method.split(".")[-1], "returncode": completed.returncode, "success": completed.returncode == 0, "output": sanitize(output, temp)}

def load_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Unity report missing: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))

def check_success(run: dict[str, Any], report: dict[str, Any], updated: int, unchanged: int, overrides: int) -> None:
    if not run["success"] or "UNITY_NATIVE_SYNC_STAGE7=SUCCESS" not in run["output"] or not report["Success"]:
        raise RuntimeError(f"Unity sync run failed: {run}")
    if report.get("UpdatedAssets") != updated or report.get("UnchangedAssets") != unchanged or report.get("OverridesApplied") != overrides:
        raise RuntimeError(f"Unity sync counters invalid: {report}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    args = parser.parse_args()
    executable, version = (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    if not executable.is_file():
        raise RuntimeError("Unity executable was not found")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    runs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="neoeng-unity-sync-stage7-") as raw:
        temp = Path(raw)
        project = temp / "project"
        hash_project = temp / "hash-drift"
        write_project(project, PACKAGE_ROOT, version)
        write_project(hash_project, PACKAGE_ROOT, version)
        create_fixture(project)
        create_fixture(hash_project, mutate_source=True)

        first_path = temp / "first.json"
        first = run_unity(executable, project, temp, IMPORT_METHOD, first_path)
        first_report = load_report(first_path)
        check_success(first, first_report, 1, 0, 0)
        runs.append({"name": "initial", "run": first, "report": first_report})

        repeat_path = temp / "repeat.json"
        repeat = run_unity(executable, project, temp, IMPORT_METHOD, repeat_path)
        repeat_report = load_report(repeat_path)
        check_success(repeat, repeat_report, 0, 1, 0)
        runs.append({"name": "repeat", "run": repeat, "report": repeat_report})

        override_path = project / "Assets" / "NeoEngGenerated" / "hero.ndt.override.json"
        override_path.write_text(json.dumps({"schema_version": 1, "object_id": "hero", "polygon_in_sprite": [{"x": 1, "y": 1}, {"x": 15, "y": 1}, {"x": 15, "y": 11}, {"x": 1, "y": 11}]}, indent=2) + "\n", encoding="utf-8")
        override_report_path = temp / "override.json"
        override_run = run_unity(executable, project, temp, IMPORT_METHOD, override_report_path)
        override_report = load_report(override_report_path)
        check_success(override_run, override_report, 1, 0, 1)
        runs.append({"name": "override", "run": override_run, "report": override_report})

        override_repeat_path = temp / "override-repeat.json"
        override_repeat = run_unity(executable, project, temp, IMPORT_METHOD, override_repeat_path)
        override_repeat_report = load_report(override_repeat_path)
        check_success(override_repeat, override_repeat_report, 0, 1, 1)
        runs.append({"name": "override-repeat", "run": override_repeat, "report": override_repeat_report})

        mutate = run_unity(executable, project, temp, MUTATE_METHOD)
        if not mutate["success"] or "UNITY_NATIVE_SYNC_STAGE7_MUTATION=APPLIED" not in mutate["output"]:
            raise RuntimeError(f"Unity mutation fixture failed: {mutate}")
        runs.append({"name": "manual-mutation", "run": mutate})

        conflict_path = temp / "conflict.json"
        conflict = run_unity(executable, project, temp, IMPORT_METHOD, conflict_path)
        conflict_report = load_report(conflict_path)
        if conflict["success"] or "UNITY_NATIVE_SYNC_STAGE7=FAILURE" not in conflict["output"] or conflict_report.get("ErrorCode") != "sync_conflict" or "manually" not in conflict_report.get("Error", ""):
            raise RuntimeError(f"Unity manual divergence was not blocked: {conflict_report}")
        runs.append({"name": "manual-conflict", "run": conflict, "report": conflict_report})

        confirm_path = temp / "confirmed.json"
        confirmed = run_unity(executable, project, temp, IMPORT_METHOD, confirm_path, confirm=True)
        confirmed_report = load_report(confirm_path)
        check_success(confirmed, confirmed_report, 1, 0, 1)
        runs.append({"name": "destructive-confirmed", "run": confirmed, "report": confirmed_report})

        hash_path = temp / "hash.json"
        hash_run = run_unity(executable, hash_project, temp, IMPORT_METHOD, hash_path)
        hash_report = load_report(hash_path)
        if hash_run["success"] or "UNITY_NATIVE_SYNC_STAGE7=FAILURE" not in hash_run["output"] or hash_report.get("ErrorCode") != "import_exception" or "hash" not in hash_report.get("Error", "").lower():
            raise RuntimeError(f"Unity source hash drift was not rejected: {hash_report}")
        runs.append({"name": "hash-drift", "run": hash_run, "report": hash_report})

        report = {"schema_version": 1, "stage": 7, "status": "SUCCESS", "engine": "unity", "unity_version": version, "scenarios": {"initial_update": True, "repeat_unchanged": True, "override_preserved": True, "manual_divergence_blocked": True, "destructive_confirmation_required": True, "hash_drift_rejected": True}, "runs": runs}
        (OUT / "stage7-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        for index, item in enumerate(runs, 1):
            (OUT / f"unity-stage7-{index:02d}-{item['name']}.log").write_text(item["run"]["output"], encoding="utf-8")
            if "report" in item:
                (OUT / f"unity-stage7-{index:02d}-{item['name']}.json").write_text(json.dumps(item["report"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = {path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()}
    (OUT / "stage7-index.json").write_text(json.dumps({"schema_version": 1, "stage": 7, "status": "SUCCESS", "engine": "unity", "unity_version": version, "files": files}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("NATIVE_SYNC_STAGE7_UNITY=SUCCESS")
    print("INITIAL_UPDATE=PASS")
    print("REPEAT_UNCHANGED=PASS")
    print("OVERRIDE_PRESERVED=PASS")
    print("MANUAL_DIVERGENCE_BLOCKED=PASS")
    print("DESTRUCTIVE_CONFIRMATION=PASS")
    print("HASH_DRIFT_REJECTED=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
