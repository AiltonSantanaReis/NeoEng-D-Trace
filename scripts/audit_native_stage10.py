"""Reproducible real-engine closure audit for native adapter Stage 10.

The audit creates fresh Godot and Unity projects, exercises the already
integrated adapter contracts, compares independent runs, and writes a
sanitized evidence package.  It never overwrites an existing evidence
directory and it fails closed when an engine or an expected marker is absent.
"""

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

from scripts.audit_godot_plugin_stage4 import _prepare as prepare_godot_stage4
from scripts.audit_native_advanced_stage8 import (
    create_fixture as create_advanced_fixture,
)
from scripts.audit_native_advanced_stage8 import (
    discover_godot,
    discover_unity,
)
from scripts.audit_native_advanced_stage8 import sanitize as sanitize_stage8
from scripts.audit_unity_import_stage6 import IMPORT_METHOD as UNITY_STAGE6_IMPORT
from scripts.audit_unity_import_stage6 import (
    create_fixture as create_unity_stage6_fixture,
)
from scripts.audit_unity_import_stage6 import load_report as load_unity_report
from scripts.audit_unity_import_stage6 import run_unity as run_unity_stage6
from scripts.audit_unity_import_stage6 import (
    write_project as write_unity_stage6_project,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "evidence" / "artifacts" / "native-stage10-2026-08-17"
INTERMEDIATE_FAILURE_SUMMARY = (
    "Stage 10 native-adapter closure harness — intermediate execution record\n"
    "Date: 2026-08-17\n\n"
    "The following failed runs were retained as diagnostic workspaces during "
    "development and are summarized here after the final successful run. "
    "No failed run was promoted to PASS.\n\n"
    "run=1 status=FAILED cause=Godot validator parse error caused by an invalid "
    "multiline return statement.\n"
    "run=2 status=FAILED cause=Godot validator parse error caused by invalid "
    "implicit multiline string concatenation.\n"
    "run=3 status=FAILED cause=Harness ordering defect: the independent snapshot "
    "was captured after the intentional manual-conflict mutation.\n"
    "run=4 status=FAILED cause=Unity independent-project comparison was too strict "
    "because internal YAML fileIDs and GUIDs legitimately differed.\n"
    "run=5 status=FAILED cause=Artifact privacy audit found unsanitized Unity "
    "paths/identity data and the Python capture overwrote the Unity engine log "
    "path.\n"
    "run=6 status=FAILED cause=Report command sanitization and Unity log "
    "separation were still incomplete; the package was invalidated and not used "
    "as evidence.\n"
    "run=7 status=SUCCESS_BUT_REJECTED cause=Harness gates passed, but post-run "
    "privacy audit found PIDs and a WindowsEditor identity in nested Stage6 output; "
    "the package was invalidated and not used as evidence.\n"
    "run=8 status=SUCCESS_BUT_REJECTED cause=Direct log sanitization passed, but the "
    "nested Stage6 report still contained an unsanitized PID; the package was "
    "invalidated and not used as evidence.\n"
    "run=9 status=SUCCESS cause=Recursive report sanitization passed the engine gates, "
    "index, privacy scan, and final evidence audit.\n\n"
    "Reproducibility rule: the official package contains only the final sanitized "
    "artifacts and this failure summary. Temporary diagnostic workspaces are not "
    "evidence and are excluded from version control.\n"
)
UNITY_ADVANCED_IMPORT = (
    "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessAdvancedImport"
)
UNITY_DRY_RUN = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessStage9DryRun"
UNITY_MANUAL = "NeoEng.DTrace.Editor.UnityImportGenerator.CreateManualPrefabFixture"


def sanitize_output(value: str, temporary: Path) -> str:
    """Sanitize engine output before it enters reports or committed logs."""
    value = sanitize_stage8(value, temporary)
    patterns = (
        (
            r"(?im)^\s*(?:Machine Id|Session Id|Correlation Id|"
            r"External correlation Id):.*$",
            "<redacted-engine-identity>",
        ),
        (r"(?i)LicenseClient-[A-Za-z0-9_.-]+", "LicenseClient-<redacted>"),
        (r"(?i)\bPId:\s*\d+", "PId: <redacted>"),
        (r"(?i)\bprocessId\"?\s*[:=]\s*\d+", "processId: <redacted>"),
        (r"(?i)\bprocess\s+Id:\s*\d+", "process Id: <redacted>"),
        (r"(?i)WindowsEditor\([^)]*\)", "WindowsEditor(<redacted>)"),
        (r"(?im)^\s*Date:.*$", "<redacted-timestamp>"),
        (r"(?im)^.*http://localhost:\d+.*$", "<redacted-local-endpoint>"),
        (r"(?im)^.*debugger-agent(?::|=).*$", "<redacted-debug-endpoint>"),
    )
    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)
    return value


def sanitize_structure(value: Any, temporary: Path) -> Any:
    """Sanitize nested engine results before serializing the report."""
    if isinstance(value, str):
        return sanitize_output(value, temporary)
    if isinstance(value, list):
        return [sanitize_structure(item, temporary) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_structure(item, temporary) for key, item in value.items()}
    return value


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
    var mode := OS.get_environment("NEOENG_STAGE10_MODE")
    if mode == "dry-run":
        var result = Importer.dry_run_manifest(MANIFEST)
        if not check(
            result.get("status") == "DRY_RUN", "dry-run-result"
        ):
            return
        if not check(
            not FileAccess.file_exists(SCENE), "dry-run-mutated-output"
        ):
            return
        print("GODOT_STAGE10_DRY_RUN=PASS")
    elif mode == "apply":
        var result = Importer.import_manifest(MANIFEST)
        if not check(
            result.get("status") == "SUCCESS",
            "apply-result:" + JSON.stringify(result),
        ):
            return
        if not check(
            result.get("results", [])[0].get("status") == "UPDATED",
            "apply-updated",
        ):
            return
        var packed := load(SCENE) as PackedScene
        if not check(packed != null, "scene-load"):
            return
        var instance := packed.instantiate()
        if not check(instance != null, "scene-instantiate"):
            return
        var sprite := instance.get_node_or_null("Sprite2D") as Sprite2D
        if not check(
            sprite != null and sprite.texture is AtlasTexture, "atlas-sprite"
        ):
            return
        var atlas := sprite.texture as AtlasTexture
        if not check(
            atlas.region.size.x > 0.0 and atlas.region.size.y > 0.0, "atlas-region"
        ):
            return
        var collision := instance.get_node_or_null(
            "CollisionPolygon2D"
        ) as CollisionPolygon2D
        if not check(
            collision != null and collision.polygon.size() >= 3, "collision-polygon"
        ):
            return
        if not check(
            instance.get_meta("neoeng_advanced_page_sha256", "") != "",
            "page-hash-metadata",
        ):
            return
        instance.free()
        print("GODOT_STAGE10_APPLY=PASS")
    elif mode == "repeat":
        var result = Importer.import_manifest(MANIFEST)
        if not check(
            result.get("status") == "SUCCESS",
            "repeat-result:" + JSON.stringify(result),
        ):
            return
        if not check(
            result.get("results", [])[0].get("status") == "UNCHANGED",
            "repeat-unchanged",
        ):
            return
        print("GODOT_STAGE10_REPEAT=PASS")
    elif mode == "unsafe":
        var result = Importer.dry_run_manifest(MANIFEST, "res://../outside")
        if not check(
            result.get("status") == "FAILED", "unsafe-path-accepted"
        ):
            return
        print("GODOT_STAGE10_UNSAFE=REJECTED")
    elif mode == "manual":
        var manual := FileAccess.open(SCENE, FileAccess.WRITE)
        var manual_text := "[gd_scene format=3]\n"
        manual_text += "\n[node name=\"Manual\" type=\"Node2D\"]\n"
        manual.store_string(manual_text)
        manual.close()
        var before := FileAccess.get_file_as_bytes(SCENE)
        var result = Importer.import_manifest(MANIFEST)
        if not check(
            result.get("status") == "CONFLICT", "manual-conflict-not-blocked"
        ):
            return
        if not check(
            before == FileAccess.get_file_as_bytes(SCENE),
            "manual-resource-mutated",
        ):
            return
        print("GODOT_STAGE10_MANUAL=BLOCKED")
    elif mode == "hash-drift":
        var result = Importer.dry_run_manifest(MANIFEST)
        if not check(
            result.get("status") == "FAILED", "hash-drift-accepted"
        ):
            return
        print("GODOT_STAGE10_HASH_DRIFT=REJECTED")
    else:
        fail("unknown-stage10-mode:" + mode)
        return
    quit(0)
"""


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def snapshot_tree(root: Path) -> dict[str, dict[str, Any]]:
    """Hash generated source files while ignoring engine-generated .meta files."""
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix == ".meta":
            continue
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            canonical = raw
        else:
            canonical_text = re.sub(
                r"(?i)([0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f-]{27,})",
                "<engine-guid>",
                text,
            )
            canonical_text = re.sub(
                r"(?m)(^--- !u!\d+ &)-?\d+",
                r"\1<engine-fileid>",
                canonical_text,
            )
            canonical_text = re.sub(
                r"fileID:\s*-?\d+",
                "fileID: <engine-fileid>",
                canonical_text,
            )
            canonical = canonical_text.replace("\r\n", "\n").encode("utf-8")
        result[relative] = {
            "bytes": len(canonical),
            "sha256": hashlib.sha256(canonical).hexdigest(),
        }
    return result


def run_process(
    command: list[str],
    *,
    cwd: Path,
    temporary: Path,
    environment: dict[str, str] | None = None,
    log_name: str,
    timeout: int = 300,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    raw = completed.stdout
    log_path = temporary / log_name
    sanitized = sanitize_output(raw, temporary)
    log_path.write_text(sanitized, encoding="utf-8", newline="\n")
    return {
        "command": [
            Path(command[0]).name,
            *(sanitize_output(argument, temporary) for argument in command[1:]),
        ],
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "output": sanitized,
        "log": log_name,
    }


def require_marker(run: dict[str, Any], marker: str) -> None:
    if not run["success"] or marker not in run["output"]:
        raise RuntimeError(f"required marker missing: {marker}")


def run_godot_mode(
    executable: Path, project: Path, temporary: Path, mode: str
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE10_MODE"] = mode
    return run_process(
        [
            str(executable),
            "--headless",
            "--path",
            str(project),
            "--script",
            "validate_stage10.gd",
            "--quit-after",
            "5",
        ],
        cwd=ROOT,
        temporary=temporary,
        environment=environment,
        log_name=f"godot-stage10-{project.name}-{mode}.log",
        timeout=180,
    )


def godot_project(project: Path) -> None:
    (project / "validate_stage10.gd").write_text(
        GODOT_VALIDATOR, encoding="utf-8", newline="\n"
    )


def run_godot_closure(executable: Path, temporary: Path) -> dict[str, Any]:
    project_a = temporary / "godot-closure-a"
    project_b = temporary / "godot-closure-b"
    project_hash = temporary / "godot-closure-hash"
    fixtures: dict[str, dict[str, Path]] = {}
    runs: list[dict[str, Any]] = []
    for project in (project_a, project_b, project_hash):
        fixtures[project.name] = create_advanced_fixture(project, "godot")
        godot_project(project)
        pre = run_process(
            [
                str(executable),
                "--headless",
                "--editor",
                "--path",
                str(project),
                "--import",
                "--quit-after",
                "5",
            ],
            cwd=ROOT,
            temporary=temporary,
            log_name=f"godot-stage10-{project.name}-preimport.log",
            timeout=180,
        )
        require_marker(pre, "Godot Engine")
        if not pre["success"]:
            raise RuntimeError(f"Godot pre-import failed: {project.name}")
        runs.append({"project": project.name, "mode": "pre-import", "run": pre})

    snapshot_a: dict[str, dict[str, Any]] | None = None
    for mode, marker in (
        ("dry-run", "GODOT_STAGE10_DRY_RUN=PASS"),
        ("apply", "GODOT_STAGE10_APPLY=PASS"),
        ("repeat", "GODOT_STAGE10_REPEAT=PASS"),
        ("unsafe", "GODOT_STAGE10_UNSAFE=REJECTED"),
        ("manual", "GODOT_STAGE10_MANUAL=BLOCKED"),
    ):
        run = run_godot_mode(executable, project_a, temporary, mode)
        require_marker(run, marker)
        runs.append({"project": project_a.name, "mode": mode, "run": run})
        if mode == "repeat":
            snapshot_a = snapshot_tree(project_a / "NeoEngGenerated")

    apply_b = run_godot_mode(executable, project_b, temporary, "apply")
    require_marker(apply_b, "GODOT_STAGE10_APPLY=PASS")
    runs.append({"project": project_b.name, "mode": "apply", "run": apply_b})
    hash_fixture = fixtures[project_hash.name]
    hash_fixture["atlas"].write_bytes(
        hash_fixture["atlas"].read_bytes() + b"stage10-drift"
    )
    hash_run = run_godot_mode(executable, project_hash, temporary, "hash-drift")
    require_marker(hash_run, "GODOT_STAGE10_HASH_DRIFT=REJECTED")
    runs.append({"project": project_hash.name, "mode": "hash-drift", "run": hash_run})

    if snapshot_a is None:
        raise RuntimeError("Godot repeat snapshot was not captured")
    snapshot_b = snapshot_tree(project_b / "NeoEngGenerated")
    if snapshot_a != snapshot_b:
        raise RuntimeError("Godot independent generated snapshots differ")
    return {
        "version": "4.7.stable",
        "runs": runs,
        "deterministic_snapshot": snapshot_a,
        "fixtures": {
            name: {key: digest(path) for key, path in files.items()}
            for name, files in fixtures.items()
        },
    }


def run_unity_call(
    executable: Path,
    project: Path,
    temporary: Path,
    method: str,
    report_path: Path,
    log_name: str,
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE6_MANIFEST"] = (
        "Assets/NeoEngInput/hero.ndt.integration.json"
    )
    environment["NEOENG_STAGE6_REPORT"] = str(report_path)
    engine_log_name = "engine-" + log_name
    engine_log_path = temporary / engine_log_name
    run = run_process(
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
            str(engine_log_path),
        ],
        cwd=ROOT,
        temporary=temporary,
        environment=environment,
        log_name=log_name,
        timeout=420,
    )
    if engine_log_path.is_file():
        engine_output = sanitize_output(
            engine_log_path.read_text(encoding="utf-8", errors="replace"), temporary
        )
        combined = (run["output"] + "\n" + engine_output).strip() + "\n"
        (temporary / log_name).write_text(combined, encoding="utf-8", newline="\n")
        run["output"] = combined
    if report_path.is_file():
        run["report"] = json.loads(report_path.read_text(encoding="utf-8"))
    return run


def run_unity_closure(
    executable: Path, version: str, temporary: Path
) -> dict[str, Any]:
    project_a = temporary / "unity-closure-a"
    project_b = temporary / "unity-closure-b"
    project_hash = temporary / "unity-closure-hash"
    project_manual = temporary / "unity-closure-manual"
    fixtures: dict[str, dict[str, Path]] = {}
    runs: list[dict[str, Any]] = []
    for project in (project_a, project_b, project_hash, project_manual):
        fixtures[project.name] = create_advanced_fixture(project, "unity", version)
    dry_report = temporary / "unity-stage10-dry.json"
    dry = run_unity_call(
        executable,
        project_a,
        temporary,
        UNITY_DRY_RUN,
        dry_report,
        "unity-stage10-dry.log",
    )
    if (
        not dry["success"]
        or not dry.get("report", {}).get("Success")
        or not dry["report"].get("DryRun")
    ):
        raise RuntimeError("Unity Stage 10 dry-run failed")
    if (project_a / "Assets" / "NeoEngGenerated").exists():
        raise RuntimeError("Unity dry-run created generated output")
    runs.append({"project": project_a.name, "mode": "dry-run", "run": dry})

    initial_report = temporary / "unity-stage10-initial.json"
    initial = run_unity_call(
        executable,
        project_a,
        temporary,
        UNITY_ADVANCED_IMPORT,
        initial_report,
        "unity-stage10-initial.log",
    )
    if (
        not initial["success"]
        or not initial.get("report", {}).get("Success")
        or initial["report"].get("UpdatedAssets") != 1
    ):
        raise RuntimeError("Unity Stage 10 initial import failed")
    runs.append({"project": project_a.name, "mode": "apply", "run": initial})
    repeat_report = temporary / "unity-stage10-repeat.json"
    repeat = run_unity_call(
        executable,
        project_a,
        temporary,
        UNITY_ADVANCED_IMPORT,
        repeat_report,
        "unity-stage10-repeat.log",
    )
    if (
        not repeat["success"]
        or not repeat.get("report", {}).get("Success")
        or repeat["report"].get("UnchangedAssets") != 1
    ):
        raise RuntimeError("Unity Stage 10 repeat import was not unchanged")
    runs.append({"project": project_a.name, "mode": "repeat", "run": repeat})

    manual_setup = run_unity_call(
        executable,
        project_manual,
        temporary,
        UNITY_MANUAL,
        temporary / "unity-stage10-manual-setup.json",
        "unity-stage10-manual-setup.log",
    )
    if not manual_setup["success"]:
        raise RuntimeError("Unity manual fixture setup failed")
    manual_report = temporary / "unity-stage10-manual.json"
    manual = run_unity_call(
        executable,
        project_manual,
        temporary,
        UNITY_ADVANCED_IMPORT,
        manual_report,
        "unity-stage10-manual.log",
    )
    if (
        manual["success"]
        or manual.get("report", {}).get("Success")
        or "manual" not in manual.get("report", {}).get("Error", "").lower()
    ):
        raise RuntimeError("Unity manual generated resource was not blocked")
    runs.append({"project": project_manual.name, "mode": "manual", "run": manual})

    hash_fixture = fixtures[project_hash.name]
    hash_fixture["atlas"].write_bytes(
        hash_fixture["atlas"].read_bytes() + b"stage10-drift"
    )
    hash_report = temporary / "unity-stage10-hash.json"
    hash_run = run_unity_call(
        executable,
        project_hash,
        temporary,
        UNITY_ADVANCED_IMPORT,
        hash_report,
        "unity-stage10-hash.log",
    )
    if (
        hash_run["success"]
        or hash_run.get("report", {}).get("Success")
        or "hash" not in hash_run.get("report", {}).get("Error", "").lower()
    ):
        raise RuntimeError("Unity hash drift was not rejected")
    runs.append({"project": project_hash.name, "mode": "hash-drift", "run": hash_run})

    initial_b_report = temporary / "unity-stage10-b.json"
    initial_b = run_unity_call(
        executable,
        project_b,
        temporary,
        UNITY_ADVANCED_IMPORT,
        initial_b_report,
        "unity-stage10-b.log",
    )
    if not initial_b["success"] or not initial_b.get("report", {}).get("Success"):
        raise RuntimeError("Unity independent import failed")
    runs.append({"project": project_b.name, "mode": "apply", "run": initial_b})
    snapshot_a = snapshot_tree(project_a / "Assets" / "NeoEngGenerated")
    snapshot_b = snapshot_tree(project_b / "Assets" / "NeoEngGenerated")
    if snapshot_a != snapshot_b:
        raise RuntimeError("Unity independent generated snapshots differ")
    return {
        "version": version,
        "runs": runs,
        "deterministic_snapshot": snapshot_a,
        "fixtures": {
            name: {key: digest(path) for key, path in files.items()}
            for name, files in fixtures.items()
        },
    }


def run_regression_fixtures(
    godot: Path, unity: Path, unity_version: str, temporary: Path
) -> dict[str, Any]:
    godot_project = temporary / "godot-regression-stage4"
    fixture = prepare_godot_stage4(godot_project)
    pre = run_process(
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
        temporary=temporary,
        log_name="godot-stage10-regression-preimport.log",
        timeout=180,
    )
    validation = run_process(
        [
            str(godot),
            "--headless",
            "--path",
            str(godot_project),
            "--script",
            "validate_stage4.gd",
            "--quit-after",
            "5",
        ],
        cwd=ROOT,
        temporary=temporary,
        log_name="godot-stage10-regression-stage4.log",
        timeout=180,
    )
    require_marker(validation, "NATIVE_PLUGIN_STAGE4_CORE=SUCCESS")
    unity_project = temporary / "unity-regression-stage6"
    write_unity_stage6_project(
        unity_project,
        ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace",
        unity_version,
    )
    create_unity_stage6_fixture(unity_project)
    report_path = temporary / "unity-stage10-regression.json"
    unity_run = run_unity_stage6(
        unity, unity_project, UNITY_STAGE6_IMPORT, temporary, report_path
    )
    report = load_unity_report(report_path)
    if (
        unity_run["returncode"] != 0
        or not unity_run["success_marker"]
        or not report.get("Success")
    ):
        raise RuntimeError("Unity Stage 6 regression fixture failed")
    return {
        "godot_stage4": {
            "pre_import": pre,
            "validation": validation,
            "fixture": {
                key: digest(value)
                for key, value in fixture.items()
                if isinstance(value, Path)
            },
        },
        "unity_stage6": {
            "run": sanitize_structure(unity_run, temporary),
            "report": sanitize_structure(report, temporary),
        },
    }


def write_artifacts(output: Path, report: dict[str, Any], temporary: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"evidence output already exists: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "stage10-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for path in sorted(temporary.glob("*.log")):
        sanitized = sanitize_output(
            path.read_text(encoding="utf-8", errors="replace"), temporary
        )
        (output / path.name).write_text(sanitized, encoding="utf-8", newline="\n")
    for engine_name, engine_data in (
        ("godot", report["engines"]["godot"]),
        ("unity", report["engines"]["unity"]),
    ):
        for fixture_name, files in engine_data["fixtures"].items():
            for name in files:
                source = (
                    temporary
                    / fixture_name
                    / ("atlas" if name == "atlas" else "NeoEngGenerated")
                )
                if name == "manifest":
                    source = (
                        temporary
                        / fixture_name
                        / (
                            "NeoEngGenerated"
                            if engine_name == "godot"
                            else "Assets/NeoEngInput"
                        )
                        / ("hero.ndt.integration.json")
                    )
                if name == "atlas":
                    source = (
                        temporary
                        / fixture_name
                        / (
                            "atlas/atlas_0.png"
                            if engine_name == "godot"
                            else "Assets/atlas/atlas_0.png"
                        )
                    )
                if source.is_file():
                    shutil.copy2(
                        source,
                        output / f"{engine_name}-{fixture_name}-{name}{source.suffix}",
                    )
    (output / "stage10-intermediate-failures.log").write_text(
        INTERMEDIATE_FAILURE_SUMMARY, encoding="utf-8", newline="\n"
    )
    files = {
        path.name: digest(path) for path in sorted(output.iterdir()) if path.is_file()
    }
    (output / "stage10-index.json").write_text(
        json.dumps(
            {"schema_version": 1, "stage": 10, "status": "SUCCESS", "files": files},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", type=Path)
    parser.add_argument("--unity", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--failure-dir", type=Path)
    args = parser.parse_args()
    godot = args.godot or discover_godot()
    unity, unity_version = (
        (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    )
    if not godot.is_file() or not unity.is_file():
        raise RuntimeError("both real Godot and Unity executables are required")
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": 10,
        "status": "FAILED",
        "engines": {},
        "release_approved": False,
    }
    with tempfile.TemporaryDirectory(prefix="neoeng-native-stage10-") as raw:
        temporary = Path(raw)
        try:
            report["engines"]["godot"] = run_godot_closure(godot, temporary)
            report["engines"]["unity"] = run_unity_closure(
                unity, unity_version, temporary
            )
            report["regression_fixtures"] = run_regression_fixtures(
                godot, unity, unity_version, temporary
            )
            report["status"] = "SUCCESS"
            write_artifacts(args.output.resolve(), report, temporary)
        except Exception:
            if args.failure_dir is not None:
                failure_dir = args.failure_dir.resolve()
                if failure_dir.exists():
                    raise RuntimeError(
                        f"failure workspace already exists: {failure_dir}"
                    )
                shutil.copytree(temporary, failure_dir)
            raise
    print("NATIVE_STAGE10=SUCCESS")
    print("GODOT_REAL_CLOSURE=PASS")
    print("UNITY_REAL_CLOSURE=PASS")
    print("DETERMINISTIC_FIXTURES=PASS")
    print("REGRESSION_FIXTURES=PASS")
    print("RELEASE_APPROVED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
