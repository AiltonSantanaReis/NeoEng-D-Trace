"""Reproduce the real Godot/Unity consumer checks for scenario runtime JSON."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from scripts.audit_native_stage10 import sanitize_output
from src.exporters.scenario_exporter import serialize_scenario_runtime_export
from src.persistence.project_schema import PointRecord
from src.persistence.scenario_schema import (
    ProjectReferenceRecord,
    ScenarioCameraRecord,
    ScenarioDocumentV1,
    ScenarioLayerRecord,
    ScenarioParallaxRecord,
    default_scenario_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/evidence/artifacts/stage4b4-engine-validation-2026-08-18"


def _document() -> ScenarioDocumentV1:
    return ScenarioDocumentV1(
        metadata=default_scenario_metadata("Runtime Engine Fixture"),
        project=ProjectReferenceRecord(sha256="a" * 64),
        camera=ScenarioCameraRecord(
            position=PointRecord(x=12.0, y=-4.0),
            zoom=1.5,
        ),
        layers=[
            ScenarioLayerRecord(
                id="layer_foreground",
                name="Foreground",
                visible=True,
                object_ids=["object_a"],
                parallax=ScenarioParallaxRecord(
                    depth=0.25,
                    translation_strength=0.75,
                    zoom_strength=0.8,
                ),
            ),
            ScenarioLayerRecord(
                id="layer_background",
                name="Background",
                visible=False,
                object_ids=[],
                parallax=ScenarioParallaxRecord(
                    depth=1.0,
                    translation_strength=0.5,
                    zoom_strength=0.4,
                ),
            ),
        ],
    )


def _sanitize(text: str, temporary_root: Path) -> str:
    value = sanitize_output(text, temporary_root).replace(
        "<redacted-engine-identity>", "<redacted>"
    )
    labels = (
        "Machine Id:",
        "Session Id:",
        "Correlation Id:",
        "External correlation Id:",
    )
    sanitized_lines = [
        "<redacted-engine-identity>" if line.strip().startswith(labels) else line
        for line in value.splitlines()
    ]
    result = "\n".join(sanitized_lines)
    return result + ("\n" if value.endswith("\n") else "")


def _run(command: list[str], *, env: dict[str, str], cwd: Path) -> tuple[int, str]:
    process = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return process.returncode, process.stdout + process.stderr


def _find_godot() -> str:
    candidate = shutil.which("godot") or shutil.which("godot4")
    if candidate:
        return candidate
    raise RuntimeError("Godot executable was not found on PATH")


def _find_unity() -> str:
    candidate = shutil.which("Unity.exe") or shutil.which("Unity")
    if candidate:
        return candidate
    roots = [Path("C:/Program Files/Unity/Hub/Editor")]
    candidates = sorted(
        (root.glob("*/Editor/Unity.exe") for root in roots if root.is_dir()),
        key=lambda path: str(path),
    )
    flattened = [path for group in candidates for path in group]
    if not flattened:
        raise RuntimeError("Unity executable was not found")
    return str(flattened[-1])


def _write_fixture(root: Path) -> tuple[Path, Path, bytes]:
    payload = serialize_scenario_runtime_export(_document())
    godot_project = root / "godot"
    unity_project = root / "unity"
    (godot_project / "NeoEngGenerated").mkdir(parents=True)
    (unity_project / "Assets/NeoEngGenerated").mkdir(parents=True)
    shutil.copytree(
        ROOT / "integrations/godot/addons/neoeng_d_trace",
        godot_project / "addons/neoeng_d_trace",
    )
    (godot_project / "tools").mkdir()
    shutil.copy2(
        ROOT / "tools/godot_scenario_stage4b4_validator.gd",
        godot_project / "tools/godot_scenario_stage4b4_validator.gd",
    )
    (godot_project / "project.godot").write_text(
        (
            "[application]\n"
            'config/name="NeoEngStage4B4"\n'
            "[rendering]\n"
            'renderer/rendering_method="gl_compatibility"\n'
            "[editor_plugins]\n"
            'enabled=PackedStringArray("res://addons/neoeng_d_trace/plugin.cfg")\n'
        ),
        encoding="utf-8",
    )
    export_path = godot_project / "NeoEngGenerated/scenario.ndtscenario.runtime.json"
    export_path.write_bytes(payload)
    (unity_project / "Packages/com.neoeng.dtrace").parent.mkdir(exist_ok=True)
    shutil.copytree(
        ROOT / "integrations/unity/package/com.neoeng.dtrace",
        unity_project / "Packages/com.neoeng.dtrace",
    )
    (unity_project / "ProjectSettings").mkdir()
    (unity_project / "ProjectSettings/ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8"
    )
    (unity_project / "Packages/manifest.json").write_text(
        (
            '{\n  "dependencies": {\n'
            '    "com.neoeng.dtrace": "file:com.neoeng.dtrace"\n'
            "  }\n}\n"
        ),
        encoding="utf-8",
    )
    unity_export = (
        unity_project / "Assets/NeoEngGenerated/scenario.ndtscenario.runtime.json"
    )
    unity_export.write_bytes(payload)
    return godot_project, unity_project, payload


def _negative_payloads(payload: bytes) -> dict[str, bytes]:
    """Return independent malformed payloads for real consumer rejection tests."""

    cases: dict[str, dict] = {}
    cases["wrong_format"] = {"format_id": "wrong", "schema_version": 1}
    generator = json.loads(payload)
    generator["generator"]["id"] = "wrong_generator"
    cases["generator_identity"] = generator
    binding = json.loads(payload)
    binding["source"]["sha256"] = "A" * 64
    cases["lowercase_binding_hash"] = binding
    camera = json.loads(payload)
    camera["camera"]["zoom"] = 0
    cases["camera_zoom"] = camera
    parallax = json.loads(payload)
    parallax["layers"][0]["parallax"]["depth"] = 2
    cases["parallax_range"] = parallax
    return {
        name: (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        for name, value in cases.items()
    }


def _write_report(name: str, content: str) -> str:
    path = OUTPUT / name
    path.write_text(content, encoding="utf-8")
    return name


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    godot = _find_godot()
    unity = _find_unity()
    with tempfile.TemporaryDirectory(prefix="neoeng-stage4b4-") as temporary:
        fixture_root = Path(temporary)
        godot_project, unity_project, payload = _write_fixture(fixture_root)
        base_env = os.environ.copy()
        godot_command = [
            godot,
            "--headless",
            "--path",
            str(godot_project),
            "--script",
            "res://tools/godot_scenario_stage4b4_validator.gd",
            "--quit-after",
            "2",
        ]
        env = {
            **base_env,
            "NEOENG_SCENARIO_EXPORT": (
                "res://NeoEngGenerated/scenario.ndtscenario.runtime.json"
            ),
        }
        godot_plugin_command = [
            godot,
            "--headless",
            "--editor",
            "--path",
            str(godot_project),
            "--quit-after",
            "2",
        ]
        godot_plugin_code, godot_plugin_output = _run(
            godot_plugin_command, env=base_env, cwd=ROOT
        )
        godot_code, godot_output = _run(godot_command, env=env, cwd=ROOT)
        unity_command = [
            unity,
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(unity_project),
            "-executeMethod",
            "NeoEng.DTrace.Editor.ScenarioImportGenerator.RunHeadlessScenarioImport",
            "-logFile",
            "-",
        ]
        unity_env = {
            **base_env,
            "NEOENG_SCENARIO_EXPORT": (
                "Assets/NeoEngGenerated/scenario.ndtscenario.runtime.json"
            ),
        }
        unity_code, unity_output = _run(unity_command, env=unity_env, cwd=ROOT)
        negative_payloads = _negative_payloads(payload)
        godot_negative_results: dict[str, dict[str, object]] = {}
        unity_negative_results: dict[str, dict[str, object]] = {}
        for case_name, invalid_payload in negative_payloads.items():
            godot_name = f"scenario.invalid.{case_name}.json"
            unity_name = f"scenario.invalid.{case_name}.json"
            (godot_project / "NeoEngGenerated" / godot_name).write_bytes(
                invalid_payload
            )
            (unity_project / "Assets/NeoEngGenerated" / unity_name).write_bytes(
                invalid_payload
            )
            godot_negative_code, godot_negative_output = _run(
                godot_command,
                env={
                    **base_env,
                    "NEOENG_SCENARIO_EXPORT": f"res://NeoEngGenerated/{godot_name}",
                },
                cwd=ROOT,
            )
            unity_negative_code, unity_negative_output = _run(
                unity_command,
                env={
                    **base_env,
                    "NEOENG_SCENARIO_EXPORT": f"Assets/NeoEngGenerated/{unity_name}",
                },
                cwd=ROOT,
            )
            godot_negative_results[case_name] = {
                "exit": godot_negative_code,
                "log": _sanitize(godot_negative_output, fixture_root),
            }
            unity_negative_results[case_name] = {
                "exit": unity_negative_code,
                "log": _sanitize(unity_negative_output, fixture_root),
            }

    godot_negative_code = max(
        int(item["exit"]) for item in godot_negative_results.values()
    )
    unity_negative_code = max(
        int(item["exit"]) for item in unity_negative_results.values()
    )
    godot_negative_output = "\n".join(
        f"CASE={name}\n{item['log']}" for name, item in godot_negative_results.items()
    )
    unity_negative_output = "\n".join(
        f"CASE={name}\n{item['log']}" for name, item in unity_negative_results.items()
    )
    logs = {
        "godot-plugin.log": _sanitize(godot_plugin_output, fixture_root),
        "godot-positive.log": _sanitize(godot_output, fixture_root),
        "godot-negative.log": godot_negative_output + "\n",
        "unity-positive.log": _sanitize(unity_output, fixture_root),
        "unity-negative.log": unity_negative_output + "\n",
    }
    for name, content in logs.items():
        _write_report(name, content)
    (OUTPUT / "scenario.ndtscenario.runtime.json").write_bytes(payload)
    results = {
        "godot": {
            "positive_exit": godot_code,
            "negative_exit": godot_negative_code,
            "plugin_exit": godot_plugin_code,
            "negative_cases": {
                name: {"exit": int(item["exit"])}
                for name, item in godot_negative_results.items()
            },
        },
        "unity": {
            "positive_exit": unity_code,
            "negative_exit": unity_negative_code,
            "negative_cases": {
                name: {"exit": int(item["exit"])}
                for name, item in unity_negative_results.items()
            },
        },
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "expected": {
            "godot_plugin_exit": 0,
            "godot_positive_exit": 0,
            "godot_negative_exit": 1,
            "unity_positive_exit": 0,
            "unity_negative_exit": 1,
        },
    }
    results["status"] = (
        "PASS"
        if (
            godot_code == 0
            and godot_plugin_code == 0
            and all(item["exit"] != 0 for item in godot_negative_results.values())
            and unity_code == 0
            and all(item["exit"] != 0 for item in unity_negative_results.values())
            and "SCRIPT ERROR" not in logs["godot-plugin.log"]
            and "Parse Error" not in logs["godot-plugin.log"]
            and "SCENARIO_ENGINE_STAGE4B4=SUCCESS" in logs["godot-positive.log"]
            and "SCENARIO_ENGINE_STAGE4B4=SUCCESS" in logs["unity-positive.log"]
            and all(
                "CASE=" + name in logs["godot-negative.log"]
                for name in negative_payloads
            )
            and all(
                "CASE=" + name in logs["unity-negative.log"]
                for name in negative_payloads
            )
            and "C:\\" not in logs["godot-negative.log"]
            and "C:/" not in logs["godot-negative.log"]
            and "C:\\" not in logs["unity-negative.log"]
            and "C:/" not in logs["unity-negative.log"]
        )
        else "FAIL"
    )
    _write_report(
        "engine-report.json", json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    index = {}
    for path in sorted(OUTPUT.iterdir()):
        if path.is_file() and path.name != "artifact-index.json":
            index[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    _write_report(
        "artifact-index.json", json.dumps(index, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(results, sort_keys=True))
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
