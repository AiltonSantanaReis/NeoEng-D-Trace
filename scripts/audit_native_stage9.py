"""Reproducible real-engine audit for Stage 9 dry-run and rollback contracts."""

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

from scripts.audit_native_advanced_stage8 import (
    create_fixture,
    discover_godot,
    discover_unity,
    load_report,
)
from scripts.audit_native_advanced_stage8 import sanitize as sanitize_stage8

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "artifacts" / "native-stage9-2026-08-17"


def sanitize(value: str, temporary: Path) -> str:
    value = sanitize_stage8(value, temporary)
    patterns = (
        (
            r"(?im)Player connection\s*\[\d+\][^\\\r\n\"]*(?=\\+n|\r?\n|\\\"|\"|$)",
            "<redacted-player-connection>",
        ),
        (
            r"(?im)(?:OS:|Physical Memory:)[^\\\r\n\"]*(?=\\+n|\r?\n|\\\"|\"|$)",
            "<redacted-host-profile>",
        ),
        (
            r"(?im)Date:[^\\\r\n\"]*(?=\\+n|\r?\n|\\\"|\"|$)",
            "Date: <redacted-timestamp>",
        ),
        (
            r'(?im)^.*(?:PId|process Id|processId)"?\s*[:=]\s*\d+.*$',
            "<redacted-process-info>",
        ),
        (r"(?im)^\s*Id:.*$", "<redacted-engine-id>"),
        (r"(?im)^\s*(?:Product|Type|Expiration):.*$", "<redacted-license-info>"),
        (
            r"(?im)^\s*\[Licensing::Module\] License group:.*$",
            "<redacted-license-group>",
        ),
        (r"(?im)http://localhost:\d+", "<redacted-local-endpoint>"),
        (
            r"(?im)debugger-agent(?::|=)[^\\\r\n\"]*(?=\\+n|\r?\n|\\\"|\"|$)",
            "<redacted-debug-endpoint>",
        ),
    )
    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)
    return value


UNITY_IMPORT = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessAdvancedImport"
UNITY_DRY_RUN = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessStage9DryRun"

GODOT_VALIDATOR = r"""extends SceneTree

const Importer = preload("res://addons/neoeng_d_trace/import_generator.gd")
const MANIFEST := "res://NeoEngGenerated/hero.ndt.integration.json"
const SCENE := "res://NeoEngGenerated/hero.tscn"

func fail(message: String) -> void:
    push_error(message)
    quit(1)

func check(condition: bool, message: String) -> bool:
    if not condition:
        fail(message)
        return false
    return true

func _init() -> void:
    var mode := OS.get_environment("NEOENG_STAGE9_MODE")
    if mode == "dry-run":
        var result = Importer.dry_run_manifest(MANIFEST)
        if not check(
            result.get("status") == "DRY_RUN",
            "dry-run:" + JSON.stringify(result),
        ): return
        if not check(
            not FileAccess.file_exists(SCENE),
            "dry-run-mutated-output",
        ): return
        print("GODOT_STAGE9_DRY_RUN=PASS")
    elif mode == "initial":
        var result = Importer.import_manifest(MANIFEST)
        if not check(
            result.get("status") == "SUCCESS",
            "initial:" + JSON.stringify(result),
        ): return
        if not check(
            result.get("results", [])[0].get("status") == "UPDATED",
            "initial-result:" + JSON.stringify(result),
        ): return
        print("GODOT_STAGE9_APPLY=PASS")
    elif mode == "repeat":
        var result = Importer.import_manifest(MANIFEST)
        if not check(
            result.get("status") == "SUCCESS",
            "repeat:" + JSON.stringify(result),
        ): return
        if not check(
            result.get("results", [])[0].get("status") == "UNCHANGED",
            "repeat-result:" + JSON.stringify(result),
        ): return
        print("GODOT_STAGE9_REPEAT=PASS")
    elif mode == "unsafe":
        var result = Importer.dry_run_manifest(MANIFEST, "res://../outside")
        if not check(
            result.get("status") == "FAILED",
            "unsafe:" + JSON.stringify(result),
        ): return
        print("GODOT_STAGE9_UNSAFE_PATH=REJECTED")
    elif mode == "hash-drift":
        var result = Importer.dry_run_manifest(MANIFEST)
        if not check(
            result.get("status") == "FAILED",
            "hash-drift:" + JSON.stringify(result),
        ): return
        print("GODOT_STAGE9_HASH_DRIFT=REJECTED")
    else:
        fail("unknown-mode:" + mode)
        return
    quit(0)
"""


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_godot(
    executable: Path, project: Path, temporary: Path, mode: str
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE9_MODE"] = mode
    completed = subprocess.run(
        [
            str(executable),
            "--headless",
            "--path",
            str(project),
            "--script",
            "validate_stage9.gd",
            "--quit-after",
            "5",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    return {
        "mode": mode,
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "marker": next(
            (line for line in completed.stdout.splitlines() if "GODOT_STAGE9_" in line),
            "",
        ),
        "output": sanitize(completed.stdout, temporary),
    }


def run_unity(
    executable: Path, project: Path, temporary: Path, method: str, report: Path
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE6_MANIFEST"] = (
        "Assets/NeoEngInput/hero.ndt.integration.json"
    )
    environment["NEOENG_STAGE6_REPORT"] = str(report)
    log = temporary / f"{project.name}-{method.rsplit('.', 1)[-1]}.log"
    completed = subprocess.run(
        [
            str(executable),
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            method,
            "-logFile",
            str(log),
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    output = completed.stdout
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "method": method.rsplit(".", 1)[-1],
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "marker": next(
            (
                line
                for line in output.splitlines()
                if "UNITY_NATIVE_STAGE9_DRY_RUN=SUCCESS" in line
            ),
            next(
                (
                    line
                    for line in output.splitlines()
                    if "UNITY_NATIVE_" in line and "SUCCESS" in line
                ),
                "",
            ),
        ),
        "output": sanitize(output, temporary),
    }


def project_source_files(project: Path) -> list[str]:
    roots = ("Assets", "Packages", "ProjectSettings")
    return sorted(
        path.relative_to(project).as_posix()
        for root in roots
        for path in (project / root).rglob("*")
        if path.is_file()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path)
    parser.add_argument("--unity", type=Path)
    args = parser.parse_args()
    godot = args.godot or discover_godot()
    unity, unity_version = (
        (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    )
    if not godot.is_file() or not unity.is_file():
        raise RuntimeError("both real Godot and Unity executables are required")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": 9,
        "status": "FAILED",
        "engines": {},
    }
    with tempfile.TemporaryDirectory(prefix="neoeng-native-stage9-") as raw:
        temporary = Path(raw)
        godot_project = temporary / "godot-project"
        godot_fixture = create_fixture(godot_project, "godot")
        (godot_project / "validate_stage9.gd").write_text(
            GODOT_VALIDATOR, encoding="utf-8", newline="\n"
        )
        godot_pre = subprocess.run(
            [
                str(godot),
                "--headless",
                "--editor",
                "--path",
                str(godot_project),
                "--import",
                "--quit-after",
                "5",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        if godot_pre.returncode != 0:
            raise RuntimeError(
                "Godot Stage 9 fixture pre-import failed: "
                + sanitize(godot_pre.stdout, temporary)
            )
        godot_runs = [
            run_godot(godot, godot_project, temporary, mode)
            for mode in ("dry-run", "initial", "repeat", "unsafe")
        ]
        godot_fixture["atlas"].write_bytes(
            godot_fixture["atlas"].read_bytes() + b"stage9-drift"
        )
        godot_runs.append(run_godot(godot, godot_project, temporary, "hash-drift"))
        expected_godot = [
            "GODOT_STAGE9_DRY_RUN=PASS",
            "GODOT_STAGE9_APPLY=PASS",
            "GODOT_STAGE9_REPEAT=PASS",
            "GODOT_STAGE9_UNSAFE_PATH=REJECTED",
            "GODOT_STAGE9_HASH_DRIFT=REJECTED",
        ]
        if (
            any(not item["success"] for item in godot_runs)
            or [item["marker"] for item in godot_runs] != expected_godot
        ):
            raise RuntimeError(f"Godot Stage 9 validation failed: {godot_runs}")

        unity_project = temporary / "unity-project"
        unity_fixture = create_fixture(unity_project, "unity", unity_version)
        generated_root = unity_project / "Assets" / "NeoEngGenerated"
        warm_report_path = temporary / "unity-dry-run-warm.json"
        unity_warm = run_unity(
            unity, unity_project, temporary, UNITY_DRY_RUN, warm_report_path
        )
        warm_report = load_report(warm_report_path)
        before = project_source_files(unity_project)
        dry_report_path = temporary / "unity-dry-run.json"
        unity_dry = run_unity(
            unity, unity_project, temporary, UNITY_DRY_RUN, dry_report_path
        )
        dry_report = load_report(dry_report_path)
        after = project_source_files(unity_project)
        if (
            not unity_warm["success"]
            or not warm_report.get("Success")
            or not unity_dry["success"]
            or unity_dry["marker"] != "UNITY_NATIVE_STAGE9_DRY_RUN=SUCCESS"
            or not dry_report.get("Success")
            or not dry_report.get("DryRun")
            or before != after
            or generated_root.exists()
        ):
            raise RuntimeError(
                f"Unity Stage 9 dry-run validation failed: {unity_dry}, {dry_report}"
            )
        initial_report_path = temporary / "unity-initial.json"
        unity_initial = run_unity(
            unity, unity_project, temporary, UNITY_IMPORT, initial_report_path
        )
        initial_report = load_report(initial_report_path)
        repeat_report_path = temporary / "unity-repeat.json"
        unity_repeat = run_unity(
            unity, unity_project, temporary, UNITY_IMPORT, repeat_report_path
        )
        repeat_report = load_report(repeat_report_path)
        if (
            not unity_initial["success"]
            or not initial_report.get("Success")
            or initial_report.get("UpdatedAssets") != 1
        ):
            raise RuntimeError(
                f"Unity Stage 9 initial validation failed: {initial_report}"
            )
        if (
            not unity_repeat["success"]
            or not repeat_report.get("Success")
            or repeat_report.get("UnchangedAssets") != 1
        ):
            raise RuntimeError(
                f"Unity Stage 9 repeat validation failed: {repeat_report}"
            )
        rollback_project = temporary / "unity-rollback-project"
        rollback_fixture = create_fixture(rollback_project, "unity", unity_version)
        rollback_manifest_path = rollback_fixture["manifest"]
        rollback_manifest = json.loads(
            rollback_manifest_path.read_text(encoding="utf-8")
        )
        rollback_manifest["schema_version"] = 1
        rollback_manifest.pop("advanced", None)
        broken_sprite = json.loads(
            json.dumps(rollback_manifest["metadata"]["sprites"][0])
        )
        broken_sprite["id"] = "broken"
        broken_sprite["polygon_in_sprite"] = [[0.0, 0.0], [1.0, 1.0]]
        rollback_manifest["metadata"]["sprites"].append(broken_sprite)
        rollback_manifest["source"]["metadata"]["sha256"] = canonical_hash(
            rollback_manifest["metadata"]
        )
        rollback_manifest_path.write_text(
            json.dumps(rollback_manifest, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        rollback_report_path = temporary / "unity-rollback.json"
        unity_rollback = run_unity(
            unity, rollback_project, temporary, UNITY_IMPORT, rollback_report_path
        )
        rollback_report = load_report(rollback_report_path)
        rollback_root = rollback_project / "Assets" / "NeoEngGenerated"
        rollback_files = (
            sorted(path.name for path in rollback_root.rglob("*") if path.is_file())
            if rollback_root.exists()
            else []
        )
        if (
            unity_rollback["success"]
            or rollback_report.get("Success")
            or rollback_files
        ):
            raise RuntimeError(
                f"Unity Stage 9 rollback validation failed: "
                f"{unity_rollback}, {rollback_report}, {rollback_files}"
            )

        report["engines"] = {
            "godot": {
                "version": "4.7.stable",
                "runs": godot_runs,
                "fixture": {name: digest(path) for name, path in godot_fixture.items()},
            },
            "unity": {
                "version": unity_version,
                "dry_run": {
                    "warmup": {"run": unity_warm, "report": warm_report},
                    "run": unity_dry,
                    "report": dry_report,
                    "project_unchanged": True,
                },
                "initial": {"run": unity_initial, "report": initial_report},
                "repeat": {"run": unity_repeat, "report": repeat_report},
                "rollback": {
                    "run": unity_rollback,
                    "report": rollback_report,
                    "partial_outputs_after_failure": rollback_files,
                },
                "fixture": {name: digest(path) for name, path in unity_fixture.items()},
            },
        }
        report["status"] = "SUCCESS"
        (OUT / "stage9-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        for item in godot_runs:
            (OUT / f"godot-stage9-{item['mode']}.log").write_text(
                item["output"], encoding="utf-8", newline="\n"
            )
        (OUT / "unity-stage9-dry-run.log").write_text(
            unity_dry["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "unity-stage9-initial.log").write_text(
            unity_initial["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "unity-stage9-repeat.log").write_text(
            unity_repeat["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "unity-stage9-rollback.log").write_text(
            unity_rollback["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "godot-manifest.ndt.integration.json").write_bytes(
            godot_fixture["manifest"].read_bytes()
        )
        (OUT / "unity-manifest.ndt.integration.json").write_bytes(
            unity_fixture["manifest"].read_bytes()
        )
    files = {
        path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()
    }
    (OUT / "stage9-index.json").write_text(
        json.dumps(
            {"schema_version": 1, "stage": 9, "status": "SUCCESS", "files": files},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("NATIVE_STAGE9=SUCCESS")
    print("GODOT_REAL_DRY_RUN=PASS")
    print("UNITY_REAL_DRY_RUN=PASS")
    print("HASH_DRIFT_REJECTED=PASS")
    print("REPEAT_IMPORT_DETERMINISTIC=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
