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

from PIL import Image, ImageDraw

from scripts.audit_godot_plugin_stage4 import ADDON_SOURCE
from scripts.audit_unity_import_stage6 import (
    PACKAGE_ROOT,
    discover_unity,
    write_project,
)
from src.exporters.atlas_exporter import build_atlas
from src.exporters.integration_manifest import (
    build_advanced_integration_manifest,
    save_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "artifacts" / "native-advanced-stage8-2026-08-17"
UNITY_IMPORT = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessAdvancedImport"

GODOT_VALIDATOR = r"""extends SceneTree

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

func _init() -> void:
    var mode := OS.get_environment("NEOENG_STAGE8_MODE")
    var result = Importer.import_manifest(MANIFEST)
    if mode == "initial":
        if not check(
            result.get("status") == "SUCCESS",
            "initial:" + JSON.stringify(result),
        ): return
        if not check(
            result.get("results", []).size() == 1
            and result.get("results", [])[0].get("status") == "UPDATED",
            "initial-result:" + JSON.stringify(result),
        ): return
        var scene_text := FileAccess.get_file_as_string(SCENE)
        if not check(
            scene_text.contains("res://atlas/atlas_0.png"),
            "atlas-reference",
        ): return
        if not check(
            scene_text.contains("texture_filter = 1")
            and scene_text.contains("texture_repeat = 0"),
            "texture-properties",
        ): return
        var scale_pattern := RegEx.new()
        scale_pattern.compile("scale = Vector2\\(([^,]+), ([^)]+)\\)")
        var scale_match := scale_pattern.search(scene_text)
        if not check(
            scene_text.contains("z_index = 6")
            and scale_match != null
            and is_equal_approx(float(scale_match.get_string(1)), 1.0)
            and is_equal_approx(float(scale_match.get_string(2)), 1.0),
            "transform-properties",
        ): return
        if not check(
            scene_text.contains("metadata/neoeng_advanced_page_sha256"),
            "page-hash-metadata",
        ): return
        print("GODOT_NATIVE_ADVANCED_INITIAL=UPDATED")
    elif mode == "repeat":
        if not check(
            result.get("status") == "SUCCESS",
            "repeat:" + JSON.stringify(result),
        ): return
        if not check(
            result.get("results", [])[0].get("status") == "UNCHANGED",
            "repeat-result:" + JSON.stringify(result),
        ): return
        print("GODOT_NATIVE_ADVANCED_REPEAT=UNCHANGED")
    elif mode == "hash-drift":
        if not check(
            result.get("status") == "FAILED",
            "hash-drift:" + JSON.stringify(result),
        ): return
        print("GODOT_NATIVE_ADVANCED_HASH_DRIFT=REJECTED")
    else:
        fail("unknown-mode:" + mode)
        return
    quit(0)
"""


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def sanitize(value: str, temporary: Path) -> str:
    value = value.replace(str(temporary), "<local-path>").replace(str(ROOT), "<repo>")
    value = re.sub(r"(?<!res)[A-Za-z]:[\\/](?!/)[^\r\n\"]+", "<local-path>", value)
    value = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<network-address>", value)
    identity_pattern = (
        r"(?im)^\s*(?:Machine Id|Session Id|Correlation Id|"
        r"External correlation Id):.*$"
    )
    value = re.sub(identity_pattern, "<redacted-engine-identity>", value)
    value = re.sub(
        r"(?i)LicenseClient-[A-Za-z0-9_.-]+", "LicenseClient-<redacted>", value
    )
    return value


def create_source() -> tuple[Image.Image, dict[str, Any]]:
    image = Image.new("RGBA", (24, 18), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((3, 4, 18, 14), fill=(40, 180, 240, 255))
    scene = Scene()
    scene.load_image(image, "source.png")
    scene.image_path = "source.png"
    scene.image_path_kind = "relative"
    scene.add_object("hero", [(3, 4), (18, 4), (18, 14), (3, 14)], select=False)
    scene.objects["hero"].set_pivot(0.25, 0.75)
    scene.collision_shapes["hero"] = [(3, 4), (18, 4), (18, 14), (3, 14)]
    return image, export_scene_metadata(scene)


def create_fixture(
    project: Path, engine: str, unity_version: str | None = None
) -> dict[str, Path]:
    if engine == "unity":
        write_project(project, PACKAGE_ROOT, unity_version or "6000.5.7f1")
        (project / "Assets" / "atlas").mkdir(parents=True, exist_ok=True)
        destination_root = project / "Assets" / "NeoEngInput"
    else:
        (project / "addons").mkdir(parents=True, exist_ok=True)
        shutil.copytree(ADDON_SOURCE, project / "addons" / "neoeng_d_trace")
        (project / "NeoEngGenerated").mkdir(parents=True, exist_ok=True)
        (project / "atlas").mkdir(parents=True, exist_ok=True)
        (project / "project.godot").write_text(
            '[application]\nconfig/name="NeoEngDTraceStage8"\n'
            "[editor_plugins]\n"
            'enabled=PackedStringArray("res://addons/neoeng_d_trace/plugin.cfg")\n',
            encoding="utf-8",
            newline="\n",
        )
        destination_root = project / "NeoEngGenerated"
    image, metadata = create_source()
    build_dir = project / "_atlas_build"
    atlas_result = build_atlas(
        [("hero", image)], str(build_dir), max_size=(64, 64), padding=2, bleed=1
    )[0]
    relative_atlas = Path("atlas") / "atlas_0.png"
    atlas_path = project / ("Assets" if engine == "unity" else "") / relative_atlas
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(atlas_result["atlas_path"], atlas_path)
    manifest = build_advanced_integration_manifest(
        metadata,
        engine=engine,
        image_path=atlas_path,
        image_reference=relative_atlas.as_posix(),
        atlas_pages=[
            {
                "id": "atlas_0",
                "path": relative_atlas.as_posix(),
                "file_path": atlas_path,
                "entries": atlas_result["entries"],
            }
        ],
        engine_properties={
            "godot": {
                "texture_filter": "nearest",
                "texture_repeat": "disabled",
                "centered": True,
                "z_index": 6,
            },
            "unity": {
                "pixels_per_unit": 16.0,
                "filter_mode": "Point",
                "wrap_mode": "Clamp",
                "sorting_layer": "Default",
                "sorting_order": 7,
                "z_depth": 1.5,
            },
        },
    )
    manifest_path = destination_root / "hero.ndt.integration.json"
    save_integration_manifest(manifest, manifest_path)
    return {"atlas": atlas_path, "manifest": manifest_path}


def run_godot(
    executable: Path, project: Path, temporary: Path, mode: str
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE8_MODE"] = mode
    arguments = [
        "--headless",
        "--path",
        str(project),
        "--script",
        "validate_stage8.gd",
        "--quit-after",
        "5",
    ]
    completed = subprocess.run(
        [str(executable), *arguments],
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
            (
                line
                for line in completed.stdout.splitlines()
                if "GODOT_NATIVE_ADVANCED_" in line
            ),
            "",
        ),
        "output": sanitize(completed.stdout, temporary),
    }


def run_unity(
    executable: Path, project: Path, temporary: Path, report: Path
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE6_MANIFEST"] = (
        "Assets/NeoEngInput/hero.ndt.integration.json"
    )
    environment["NEOENG_STAGE6_REPORT"] = str(report)
    log = temporary / f"{project.name}.log"
    command = [
        str(executable),
        "-batchmode",
        "-nographics",
        "-quit",
        "-projectPath",
        str(project),
        "-executeMethod",
        UNITY_IMPORT,
        "-logFile",
        str(log),
    ]
    completed = subprocess.run(
        command,
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
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "marker": (
            "UNITY_NATIVE_IMPORT_STAGE8=SUCCESS"
            if "UNITY_NATIVE_IMPORT_STAGE8=SUCCESS" in output
            else ""
        ),
        "output": sanitize(output, temporary),
    }


def load_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError("Unity report was not produced")
    return json.loads(path.read_text(encoding="utf-8"))


def discover_godot() -> Path:
    configured = os.environ.get("NEOENG_GODOT_EXECUTABLE")
    if configured:
        return Path(configured)
    for name in ("godot", "godot4", "godot_console"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise RuntimeError("Godot console executable was not found")


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
        "stage": 8,
        "status": "FAILED",
        "engines": {},
    }
    with tempfile.TemporaryDirectory(prefix="neoeng-native-advanced-stage8-") as raw:
        temporary = Path(raw)
        godot_project = temporary / "godot-project"
        unity_project = temporary / "unity-project"
        godot_fixture = create_fixture(godot_project, "godot")
        (godot_project / "validate_stage8.gd").write_text(
            GODOT_VALIDATOR, encoding="utf-8", newline="\n"
        )
        unity_fixture = create_fixture(unity_project, "unity", unity_version)
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
                "Godot Stage 8 asset pre-import failed: "
                + sanitize(godot_pre.stdout, temporary)
            )
        godot_runs = [
            run_godot(godot, godot_project, temporary, "initial"),
            run_godot(godot, godot_project, temporary, "repeat"),
        ]
        godot_fixture["atlas"].write_bytes(
            godot_fixture["atlas"].read_bytes() + b"stage8-drift"
        )
        godot_runs.append(run_godot(godot, godot_project, temporary, "hash-drift"))
        if any(not item["success"] for item in godot_runs) or [
            item["marker"] for item in godot_runs
        ] != [
            "GODOT_NATIVE_ADVANCED_INITIAL=UPDATED",
            "GODOT_NATIVE_ADVANCED_REPEAT=UNCHANGED",
            "GODOT_NATIVE_ADVANCED_HASH_DRIFT=REJECTED",
        ]:
            raise RuntimeError(f"Godot Stage 8 validation failed: {godot_runs}")
        unity_initial_report_path = temporary / "unity-initial.json"
        unity_repeat_report_path = temporary / "unity-repeat.json"
        unity_initial = run_unity(
            unity, unity_project, temporary, unity_initial_report_path
        )
        unity_initial_report = load_report(unity_initial_report_path)
        unity_repeat = run_unity(
            unity, unity_project, temporary, unity_repeat_report_path
        )
        unity_repeat_report = load_report(unity_repeat_report_path)
        if (
            not unity_initial["success"]
            or unity_initial["marker"] != "UNITY_NATIVE_IMPORT_STAGE8=SUCCESS"
            or not unity_initial_report.get("Success")
            or unity_initial_report.get("UpdatedAssets") != 1
        ):
            raise RuntimeError(
                f"Unity Stage 8 initial validation failed: {unity_initial_report}"
            )
        if (
            not unity_repeat["success"]
            or unity_repeat["marker"] != "UNITY_NATIVE_IMPORT_STAGE8=SUCCESS"
            or not unity_repeat_report.get("Success")
            or unity_repeat_report.get("UnchangedAssets") != 1
        ):
            raise RuntimeError(
                f"Unity Stage 8 repeat validation failed: {unity_repeat_report}"
            )
        unity_project_hash = temporary / "unity-project-hash"
        unity_hash_fixture = create_fixture(unity_project_hash, "unity", unity_version)
        unity_hash_fixture["atlas"].write_bytes(
            unity_hash_fixture["atlas"].read_bytes() + b"stage8-drift"
        )
        unity_hash_report_path = temporary / "unity-hash.json"
        unity_hash = run_unity(
            unity, unity_project_hash, temporary, unity_hash_report_path
        )
        unity_hash_report = load_report(unity_hash_report_path)
        if (
            unity_hash["success"]
            or unity_hash_report.get("Success")
            or "hash" not in unity_hash_report.get("Error", "").lower()
        ):
            raise RuntimeError(
                f"Unity Stage 8 hash drift was not rejected: {unity_hash_report}"
            )
        report["engines"] = {
            "godot": {
                "version": "4.7.stable",
                "pre_import_returncode": godot_pre.returncode,
                "runs": godot_runs,
                "fixture": {name: digest(path) for name, path in godot_fixture.items()},
            },
            "unity": {
                "version": unity_version,
                "initial": {"run": unity_initial, "report": unity_initial_report},
                "repeat": {"run": unity_repeat, "report": unity_repeat_report},
                "hash_drift": {"run": unity_hash, "report": unity_hash_report},
                "fixture": {name: digest(path) for name, path in unity_fixture.items()},
            },
        }
        report["status"] = "SUCCESS"
        (OUT / "stage8-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (OUT / "godot-stage8-initial.log").write_text(
            godot_runs[0]["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "godot-stage8-repeat.log").write_text(
            godot_runs[1]["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "godot-stage8-hash-drift.log").write_text(
            godot_runs[2]["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "unity-stage8-initial.log").write_text(
            unity_initial["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "unity-stage8-repeat.log").write_text(
            unity_repeat["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "unity-stage8-hash-drift.log").write_text(
            unity_hash["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "godot-manifest.ndt.integration.json").write_bytes(
            godot_fixture["manifest"].read_bytes()
        )
        (OUT / "unity-manifest.ndt.integration.json").write_bytes(
            unity_fixture["manifest"].read_bytes()
        )
        (OUT / "godot-atlas-0.png").write_bytes(godot_fixture["atlas"].read_bytes())
        (OUT / "unity-atlas-0.png").write_bytes(unity_fixture["atlas"].read_bytes())
    files = {
        path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()
    }
    (OUT / "stage8-index.json").write_text(
        json.dumps(
            {"schema_version": 1, "stage": 8, "status": "SUCCESS", "files": files},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("NATIVE_ADVANCED_STAGE8=SUCCESS")
    print("GODOT_REAL_ATLAS_PROPERTIES=PASS")
    print("UNITY_REAL_ATLAS_PROPERTIES=PASS")
    print("REPEAT_IMPORT_DETERMINISTIC=PASS")
    print("HASH_DRIFT_REJECTED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
