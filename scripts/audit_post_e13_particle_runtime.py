"""Audit native particle consumption in both supported engine adapters.

This is a post-E13 audit, not a replacement for the historical Stage 8 audit.
It creates a fresh fixture, marks only ``runtime.particles`` as native, runs
Godot and Unity, captures the Godot renderer output, and executes deliberate
missing-sidecar failures without touching tracked project files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_runtime_adapters_stage8 import (  # noqa: E402
    _discover_godot,
    _discover_unity,
    _fixture,
    _log_markers,
    _run,
    _sanitize,
    _source_state,
    _write_fixture,
)
from src.runtime.engine_adapters import (  # noqa: E402
    AdapterBundleError,
    build_adapter_bundle,
    load_adapter_bundle,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _marker_int(report: dict[str, Any], marker: str) -> int | None:
    match = re.search(
        re.escape(marker) + r"=([0-9]+)",
        report.get("stdout_markers", ""),
    )
    return int(match.group(1)) if match else None


def _native_payload() -> tuple[dict[str, Any], dict[str, bytes], bytes]:
    payload, sidecars, scenario = _fixture()
    payload = copy.deepcopy(payload)
    particle_payload = json.loads(sidecars["runtime.particles"].decode("utf-8"))
    particle_payload["emitters"][0].update(
        {
            "acceleration": {"x": 0.0, "y": 12.0, "z": 0.0},
            "burst_count": 4,
            "emission_rate": 10.0,
            "initial_velocity": {"x": 100.0, "y": -35.0, "z": 0.0},
            "lifetime": 1.0,
            "max_particles": 8,
            "origin": {"x": -48.0, "y": 20.0, "z": 0.0},
            "velocity_spread": {"x": 35.0, "y": 20.0, "z": 0.0},
        }
    )
    sidecars["runtime.particles"] = (
        json.dumps(
            particle_payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    for engine in ("godot", "unity"):
        for decision in payload["capabilities"][engine]["support"]:
            if decision["id"] == "runtime.particles":
                decision.update(
                    {
                        "compatibility": "native",
                        "mode": "native-deterministic-particle-system",
                        "reason": (
                            "The engine consumes the v1 sidecar, advances the "
                            "declared fixed-step algorithm and renders native particles."
                        ),
                    }
                )
    payload = build_adapter_bundle(
        source_path="runtime/scenario.ndtscenario.runtime.json",
        source_bytes=scenario,
        sidecars={
            capability: (f"runtime/{capability.split('.', 1)[1]}.json", raw)
            for capability, raw in sidecars.items()
        },
        capabilities=payload["capabilities"],
    )
    return payload, sidecars, scenario


def _prepare_godot(root: Path, bundle: Path) -> Path:
    project = root / "godot"
    project.mkdir()
    (project / "runtime").mkdir()
    addon = project / "addons" / "neoeng_d_trace"
    addon.mkdir(parents=True)
    shutil.copy2(bundle, project / "runtime" / "adapters.json")
    shutil.copy2(
        bundle.parent / "scenario.ndtscenario.runtime.json",
        project / "runtime" / "scenario.ndtscenario.runtime.json",
    )
    for path in bundle.parent.glob("*.json"):
        if path.name not in {"adapters.json", "scenario.ndtscenario.runtime.json"}:
            shutil.copy2(path, project / "runtime" / path.name)
    shutil.copy2(
        ROOT / "integrations/godot/addons/neoeng_d_trace/runtime_adapter.gd",
        project / "runtime_adapter.gd",
    )
    shutil.copy2(
        ROOT / "integrations/godot/addons/neoeng_d_trace/runtime_particles.gd",
        addon / "runtime_particles.gd",
    )
    (project / "project.godot").write_text(
        "[application]\n"
        'config/name="NeoEngPostE13ParticleRuntime"\n'
        "[display]\n"
        "window/size/viewport_width=320\n"
        "window/size/viewport_height=180\n"
        "[rendering]\n"
        'renderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n'
        'environment/defaults/default_clear_color=Color(0.03, 0.05, 0.09, 1)\n',
        encoding="utf-8",
        newline="\n",
    )
    (project / "main.gd").write_text(
        "extends SceneTree\n"
        "\n"
        "func _init():\n"
        '    call_deferred("_run")\n'
        "\n"
        "func _run():\n"
        '    var adapter = preload("res://runtime_adapter.gd")\n'
        '    var diagnosis = adapter.diagnose_bundle("res://runtime/adapters.json")\n'
        '    if diagnosis.get("status") != "SUCCESS":\n'
        "        print(JSON.stringify(diagnosis)); quit(1); return\n"
        '    var imported = adapter.import_bundle("res://runtime/adapters.json")\n'
        '    if imported.get("status") != "SUCCESS":\n'
        "        print(JSON.stringify(imported)); quit(1); return\n"
        '    var root = imported["root"]\n'
        "    root.position = Vector2(160.0, 90.0)\n"
        "    var subviewport := SubViewport.new()\n"
        "    subviewport.size = Vector2i(320, 180)\n"
        "    subviewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS\n"
        "    subviewport.transparent_bg = false\n"
        "    get_root().add_child(subviewport)\n"
        "    subviewport.add_child(root)\n"
        '    if int(root.get_meta("neoeng_particle_count", 0)) != 0:\n'
        "        print(\"particle system did not start empty\"); quit(1); return\n"
        "    if not adapter.advance_fixed_ticks(root, 3, 0.1):\n"
        "        print(\"particle system did not advance\"); quit(1); return\n"
        '    var particle_node = root.get_node("NeoEngRuntimeParticles")\n'
        '    var particle_count = int(particle_node.get_particle_count())\n'
        "    if particle_count <= 0:\n"
        "        print(\"particle system emitted no particles\"); quit(1); return\n"
        "    await process_frame\n"
        "    await process_frame\n"
        "    await RenderingServer.frame_post_draw\n"
        '    var texture = subviewport.get_texture()\n'
        "    if texture == null:\n"
        "        print(\"particle runtime viewport texture is unavailable\"); quit(1); return\n"
        '    var image = texture.get_image()\n'
        "    if image == null:\n"
        "        print(\"particle runtime image is unavailable\"); quit(1); return\n"
        '    var capture_path = ProjectSettings.globalize_path("res://particle-runtime.png")\n'
        "    if image.save_png(capture_path) != OK:\n"
        "        print(\"particle runtime capture failed\"); quit(1); return\n"
        '    print("RUNTIME_ADAPTER_GODOT=SUCCESS")\n'
        '    print("RUNTIME_ADAPTER_PARTICLES=SUCCESS")\n'
        '    print("RUNTIME_ADAPTER_PARTICLE_EMITTERS=" + str(particle_node.get_emitter_count()))\n'
        '    print("RUNTIME_ADAPTER_PARTICLE_COUNT=" + str(particle_count))\n'
        '    print("RUNTIME_ADAPTER_PARTICLE_STATE_SHA256=" + str(particle_node.get_meta("neoeng_particle_state_sha256", "")))\n'
        '    print("RUNTIME_ADAPTER_GODOT_CAPTURE=SUCCESS")\n'
        "    root.queue_free()\n"
        "    subviewport.queue_free()\n"
        "    await process_frame\n"
        "    quit(0)\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _prepare_godot_failure(root: Path, bundle: Path) -> Path:
    project = _prepare_godot(root, bundle)
    (project / "runtime" / "particles.json").unlink()
    (project / "failure.gd").write_text(
        "extends SceneTree\n"
        "func _init():\n"
        '    var adapter = preload("res://runtime_adapter.gd")\n'
        '    var result = adapter.diagnose_bundle("res://runtime/adapters.json")\n'
        '    if result.get("status") == "SUCCESS": quit(1); return\n'
        '    print("RUNTIME_ADAPTER_GODOT_FAILURE_GUARD=PASS")\n'
        "    quit(0)\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _prepare_unity(root: Path, bundle: Path) -> Path:
    project = root / "unity"
    generated = project / "runtime"
    editor = project / "Assets/NeoEngDTrace/Editor"
    runtime = project / "Assets/NeoEngDTrace/Runtime"
    generated.mkdir(parents=True)
    editor.mkdir(parents=True)
    runtime.mkdir(parents=True)
    shutil.copy2(bundle, project / "runtime/adapters.json")
    for path in bundle.parent.glob("*.json"):
        shutil.copy2(path, generated / path.name)
    shutil.copy2(
        ROOT / "integrations/unity/package/com.neoeng.dtrace/Editor/RuntimeAdapterGenerator.cs",
        editor / "RuntimeAdapterGenerator.cs",
    )
    for name in (
        "NeoEngRuntimeAdapterMetadata.cs",
        "NeoEngScenarioMetadata.cs",
        "NeoEngRuntimeParticles.cs",
    ):
        shutil.copy2(
            ROOT / f"integrations/unity/package/com.neoeng.dtrace/Runtime/{name}",
            runtime / name,
        )
    (project / "ProjectSettings").mkdir()
    (project / "ProjectSettings/ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8", newline="\n"
    )
    return project


def _run_unity(root: Path, bundle: Path) -> dict[str, Any]:
    unity = _discover_unity()
    if not unity:
        return {"status": "NOT_TESTED", "reason": "Unity executable was not discoverable"}
    project = _prepare_unity(root, bundle)
    env = dict(**__import__("os").environ)
    env["NEOENG_RUNTIME_ADAPTER_BUNDLE"] = "runtime/adapters.json"
    return _run(
        "unity_batchmode_particle_runtime",
        [
            unity,
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            "NeoEng.DTrace.Editor.RuntimeAdapterGenerator.RunHeadlessRuntimeAdapter",
            "-logFile",
            "-",
        ],
        project,
        env,
    )


def _run_unity_failure(root: Path, bundle: Path) -> dict[str, Any]:
    unity = _discover_unity()
    if not unity:
        return {"status": "NOT_TESTED", "reason": "Unity executable was not discoverable"}
    project = _prepare_unity(root, bundle)
    (project / "runtime" / "particles.json").unlink(missing_ok=True)
    env = dict(**__import__("os").environ)
    env["NEOENG_RUNTIME_ADAPTER_BUNDLE"] = "runtime/adapters.json"
    result = _run(
        "unity_batchmode_particle_runtime_failure",
        [
            unity,
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            "NeoEng.DTrace.Editor.RuntimeAdapterGenerator.RunHeadlessRuntimeAdapter",
            "-logFile",
            "-",
        ],
        project,
        env,
    )
    expected = result.get("returncode") != 0 and (
        "runtime_adapter_failure=" in result.get("stdout_markers", "").lower()
        and (
            "particles" in result.get("stdout_markers", "").lower()
            or "sidecar" in result.get("stdout_markers", "").lower()
        )
    )
    result["expected_failure_detected"] = expected
    result["status"] = "PASS" if expected else "FAIL"
    return result


def _tracked_artifacts(output: Path) -> list[Path]:
    paths = sorted(output.glob("runtime/*.json"))
    capture = output / "godot" / "particle-runtime.png"
    if capture.is_file():
        paths.append(capture)
    return paths


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {output}")
    output.mkdir(parents=True)
    source = _source_state()
    payload, sidecars, scenario = _native_payload()
    bundle = _write_fixture(output, payload, sidecars, scenario)

    python_reports: dict[str, Any] = {}
    for engine in ("godot", "unity"):
        try:
            _, report = load_adapter_bundle(output, bundle, engine=engine)
            python_reports[engine] = {
                "status": "PASS",
                "bundle_sha256": report.bundle_sha256,
                "scenario_sha256": report.scenario_sha256,
                "particles": report.decisions["runtime.particles"],
            }
        except AdapterBundleError as exc:
            python_reports[engine] = {"status": "FAIL", "error": str(exc)}

    godot = _discover_godot()
    if godot:
        godot_project = _prepare_godot(output, bundle)
        godot_report = _run(
            "godot_native_particle_runtime",
            [godot, "--path", str(godot_project), "--script", "res://main.gd"],
            godot_project,
        )
    else:
        godot_report = {"status": "NOT_TESTED", "reason": "Godot executable was not discoverable"}

    unity_report = _run_unity(output, bundle)

    failure_root = output / "failure-guards"
    failure_root.mkdir()
    def make_failure_fixture(name: str) -> tuple[Path, Path]:
        fixture_root = failure_root / name
        fixture_root.mkdir()
        fixture_payload, fixture_sidecars, fixture_scenario = _native_payload()
        fixture_bundle = _write_fixture(
            fixture_root,
            fixture_payload,
            fixture_sidecars,
            fixture_scenario,
        )
        return fixture_root, fixture_bundle

    python_failure_root, python_failure_bundle = make_failure_fixture("python")
    (python_failure_root / "runtime" / "particles.json").unlink()
    python_failure = "PASS"
    try:
        load_adapter_bundle(python_failure_root, python_failure_bundle, engine="godot")
    except (AdapterBundleError, OSError):
        python_failure = "PASS"
    else:
        python_failure = "FAIL"
    godot_failure_root, godot_failure_bundle = make_failure_fixture("godot")
    if godot:
        failure_project = _prepare_godot_failure(godot_failure_root, godot_failure_bundle)
        godot_failure = _run(
            "godot_headless_particle_runtime_failure",
            [godot, "--headless", "--path", str(failure_project), "--script", "res://failure.gd"],
            failure_project,
        )
    else:
        godot_failure = {"status": "NOT_TESTED", "reason": "Godot executable was not discoverable"}
    _, unity_failure_bundle = make_failure_fixture("unity")
    unity_failure = _run_unity_failure(failure_root / "unity-project", unity_failure_bundle)

    capture = output / "godot" / "particle-runtime.png"
    artifacts = {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in _tracked_artifacts(output)
    }
    reports: dict[str, Any] = {
        "schema_version": 1,
        "stage": "post-e13-particle-runtime",
        "status": "IN_PROGRESS",
        "source": source,
        "python": python_reports,
        "engines": {"godot": godot_report, "unity": unity_report},
        "observations": {
            "expected_particle_count_after_three_fixed_ticks": 7,
            "godot_particle_count": _marker_int(
                godot_report, "RUNTIME_ADAPTER_PARTICLE_COUNT"
            ),
            "unity_particle_count": _marker_int(
                unity_report, "RUNTIME_ADAPTER_PARTICLE_COUNT"
            ),
            "godot_particle_emitters": _marker_int(
                godot_report, "RUNTIME_ADAPTER_PARTICLE_EMITTERS"
            ),
            "unity_particle_emitters": _marker_int(
                unity_report, "RUNTIME_ADAPTER_PARTICLE_EMITTERS"
            ),
        },
        "failure_guards": {
            "python_missing_sidecar": python_failure,
            "godot": godot_failure,
            "unity": unity_failure,
        },
        "artifacts": artifacts,
        "capture": {
            "status": "PASS" if capture.is_file() else "PENDING_EVIDENCE",
            "path": "godot/particle-runtime.png" if capture.is_file() else None,
        },
        "limitations": [
            "Unity was executed in batchmode with nographics; visual PNG evidence is provided by Godot.",
            "The sidecar v1 has no authored texture, color or size fields; the native renderer uses a documented default visual material.",
            "The editor/runtime equivalence is limited to the v1 deterministic emitter fields; richer particle authoring remains outside this change.",
        ],
    }
    good_engine = all(
        reports["engines"][engine].get("status") == "PASS"
        and "RUNTIME_ADAPTER_PARTICLES=SUCCESS" in reports["engines"][engine].get("stdout_markers", "")
        and _marker_int(
            reports["engines"][engine], "RUNTIME_ADAPTER_PARTICLE_COUNT"
        )
        == 7
        and _marker_int(
            reports["engines"][engine], "RUNTIME_ADAPTER_PARTICLE_EMITTERS"
        )
        == 1
        for engine in ("godot", "unity")
    )
    good_failures = (
        python_failure == "PASS"
        and godot_failure.get("status") == "PASS"
        and unity_failure.get("status") == "PASS"
    )
    good_capture = capture.is_file() and godot_report.get("status") == "PASS"
    reports["functional_status"] = "PASS" if good_engine and good_failures and good_capture else "PENDING_EVIDENCE"
    reports["status"] = reports["functional_status"]
    report_path = output / "post-e13-particle-runtime-report.json"
    report_path.write_text(
        json.dumps(reports, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report_path.write_text(
        json.dumps(reports, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    index_paths = [*output.glob("runtime/*.json"), capture, report_path]
    (output / "artifact-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": "post-e13-particle-runtime",
                "files": {
                    path.relative_to(output).as_posix(): {
                        "bytes": path.stat().st_size,
                        "sha256": _sha256(path),
                    }
                    for path in sorted(index_paths)
                    if path.is_file()
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({"status": report["status"], "output": "<audit-output>"}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
