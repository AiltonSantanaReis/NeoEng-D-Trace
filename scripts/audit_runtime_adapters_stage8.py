"""Run the real Stage 8 Godot/Unity adapter audit.

The audit creates a fresh, sanitized fixture from the current contracts, writes
the exact bundle and sidecars, validates both engine decisions, then invokes
the installed engines in headless mode when they are discoverable.  Missing
engine executables are reported as NOT_TESTED and never converted to PASS.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from scripts.audit_runtime_particles_phase4 import _document as particle_document
from scripts.audit_runtime_post_processing_phase5 import _document as post_document
from scripts.audit_runtime_shaders_phase3 import _document as shader_document
from scripts.audit_runtime_streaming_phase7 import (
    _asset,
)
from scripts.audit_runtime_streaming_phase7 import _document as streaming_document
from scripts.audit_runtime_triggers_phase6 import _document as trigger_document
from src.exporters.scenario_exporter import serialize_scenario_runtime_export
from src.runtime.engine_adapters import (
    CAPABILITIES,
    AdapterBundleError,
    build_adapter_bundle,
    load_adapter_bundle,
    serialize_adapter_bundle,
)
from src.runtime.lighting import (
    LightingSourceBindingRecord,
    serialize_lighting_runtime_export,
)
from src.runtime.particles import (
    ParticleSourceBindingRecord,
    serialize_particle_runtime_export,
)
from src.runtime.post_processing import (
    PostProcessingSourceBindingRecord,
    serialize_post_processing_runtime_export,
)
from src.runtime.shaders import (
    ShaderSourceBindingRecord,
    serialize_shader_runtime_export,
)
from src.runtime.streaming import (
    StreamingSourceBindingRecord,
    serialize_streaming_runtime_export,
)
from src.runtime.triggers import (
    TriggerSourceBindingRecord,
    serialize_trigger_runtime_export,
)
from tests.test_stage2_runtime_lighting import _document as lighting_document
from tests.test_stage4b4_scenario_export import _document as scenario_document

ROOT = Path(__file__).resolve().parents[1]
HOST_MARKERS = (str(ROOT), str(ROOT).replace("\\", "/"))
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\r\n\"']+")


def _canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _matrix() -> dict[str, dict[str, object]]:
    support = [
        {
            "id": capability,
            "compatibility": (
                "native"
                if capability
                in {
                    "runtime.scene_loading",
                    "runtime.lifecycle",
                    "runtime.fixed_update",
                }
                else "degraded"
            ),
            "mode": (
                "scene-tree-fixed-tick"
                if capability
                in {
                    "runtime.scene_loading",
                    "runtime.lifecycle",
                    "runtime.fixed_update",
                }
                else "validated-sidecar-metadata"
            ),
            "reason": "The adapter executes the declared contract in this scope.",
        }
        for capability in CAPABILITIES
    ]
    return {
        engine: {
            "adapter_id": f"neoeng.dtrace.{engine}.runtime",
            "adapter_version": 1,
            "support": copy.deepcopy(support),
        }
        for engine in ("godot", "unity")
    }


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _tracked_artifacts(output: Path) -> list[Path]:
    return sorted([*output.glob("runtime/*.json"), output / "stage8-report.json"])


def _privacy_leaks(paths: list[Path]) -> list[str]:
    leaks: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if LOCAL_PATH_RE.search(text) or any(
            marker in text
            for marker in (
                "LicenseClient-",
                "Machine Id:",
                "Correlation Id:",
            )
        ):
            leaks.append(path.name)
    return leaks


def _fixture() -> tuple[dict[str, Any], dict[str, bytes], bytes]:
    scenario = serialize_scenario_runtime_export(scenario_document())
    scenario_hash = _sha256(scenario)
    lighting = lighting_document().model_copy(
        update={"source": LightingSourceBindingRecord(sha256=scenario_hash)}
    )
    lighting_bytes = serialize_lighting_runtime_export(lighting)
    shader = shader_document().model_copy(
        update={"source": ShaderSourceBindingRecord(sha256=_sha256(lighting_bytes))}
    )
    particle = particle_document().model_copy(
        update={"source": ParticleSourceBindingRecord(sha256=scenario_hash)}
    )
    post = post_document().model_copy(
        update={"source": PostProcessingSourceBindingRecord(sha256=scenario_hash)}
    )
    trigger = trigger_document().model_copy(
        update={"source": TriggerSourceBindingRecord(sha256=scenario_hash)}
    )
    streaming = streaming_document(
        _asset("smoke", "textures/smoke.bin", b"smoke")
    ).model_copy(update={"source": StreamingSourceBindingRecord(sha256=scenario_hash)})
    sidecars = {
        "runtime.lighting": lighting_bytes,
        "runtime.shaders": serialize_shader_runtime_export(shader),
        "runtime.particles": serialize_particle_runtime_export(particle),
        "runtime.post_processing": serialize_post_processing_runtime_export(post),
        "runtime.triggers": serialize_trigger_runtime_export(trigger),
        "runtime.streaming": serialize_streaming_runtime_export(streaming),
    }
    payload = build_adapter_bundle(
        source_path="runtime/scenario.ndtscenario.runtime.json",
        source_bytes=scenario,
        sidecars={
            capability: (f"runtime/{capability.split('.', 1)[1]}.json", raw)
            for capability, raw in sidecars.items()
        },
        capabilities=_matrix(),
    )
    return payload, sidecars, scenario


def _write_fixture(
    root: Path, payload: dict[str, Any], sidecars: dict[str, bytes], scenario: bytes
) -> Path:
    runtime = root / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "scenario.ndtscenario.runtime.json").write_bytes(scenario)
    for capability, raw in sidecars.items():
        (runtime / f"{capability.split('.', 1)[1]}.json").write_bytes(raw)
    bundle = runtime / "adapters.json"
    bundle.write_bytes(serialize_adapter_bundle(payload))
    return bundle


def _sanitize(text: str) -> str:
    for marker in HOST_MARKERS:
        text = text.replace(marker, "<redacted>")
    return re.sub(
        r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\\r\\n\"']*", "<redacted-path>", text
    )


def _log_markers(text: str) -> str:
    lines = []
    for line in text.splitlines():
        lowered = line.lower()
        if (
            "runtime_adapter_" in lowered
            or "godot engine v" in lowered
            or "initialize engine version" in lowered
            or "error" in lowered
            or "failed" in lowered
        ):
            lines.append(_sanitize(line))
    return "\\n".join(lines)


def _run(
    label: str, command: list[str], cwd: Path, env: dict[str, str] | None = None
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "label": label,
        "command": [_sanitize(str(argument)) for argument in command],
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "stdout_markers": _log_markers(result.stdout),
        "stderr_markers": _log_markers(result.stderr),
    }


def _discover_godot() -> str | None:
    return shutil.which("godot") or shutil.which("godot4")


def _discover_unity() -> str | None:
    try:
        from scripts.audit_unity_import_stage6 import discover_unity

        discovered = discover_unity()
        if isinstance(discovered, tuple):
            discovered = discovered[0]
        return str(discovered) if discovered else None
    except Exception:
        return None


def _prepare_godot(root: Path, bundle: Path) -> Path:
    project = root / "godot"
    project.mkdir()
    (project / "runtime").mkdir()
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
    (project / "project.godot").write_text(
        "[application]\n"
        'config/name="NeoEngStage8"\n'
        "[display]\n"
        "window/size/viewport_width=320\n"
        "window/size/viewport_height=180\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "main.gd").write_text(
        "extends SceneTree\nfunc _init():\n"
        '    var adapter = preload("res://runtime_adapter.gd")\n'
        '    var diagnosis = adapter.diagnose_bundle("res://runtime/adapters.json")\n'
        '    if diagnosis.get("status") != "SUCCESS":\n'
        "        print(JSON.stringify(diagnosis)); quit(1); return\n"
        '    var imported = adapter.import_bundle("res://runtime/adapters.json")\n'
        '    if imported.get("status") != "SUCCESS": quit(1); return\n'
        '    var root = imported["root"]\n'
        "    get_root().add_child(root)\n"
        "    if not adapter.advance_fixed_ticks(root, 3): quit(1); return\n"
        '    print("RUNTIME_ADAPTER_GODOT=SUCCESS")\n'
        '    print("RUNTIME_ADAPTER_LAYERS=" + str(root.get_child_count()))\n'
        '    print("RUNTIME_ADAPTER_FIXED_TICK=" + str('
        'root.get_meta("neoeng_fixed_tick")))\n'
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
        ROOT
        / "integrations/unity/package/com.neoeng.dtrace"
        / "Editor/RuntimeAdapterGenerator.cs",
        editor / "RuntimeAdapterGenerator.cs",
    )
    for name in ("NeoEngRuntimeAdapterMetadata.cs", "NeoEngScenarioMetadata.cs"):
        shutil.copy2(
            ROOT / f"integrations/unity/package/com.neoeng.dtrace/Runtime/{name}",
            runtime / name,
        )
    (project / "ProjectSettings").mkdir()
    (project / "ProjectSettings/ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.5.7f1\n", encoding="utf-8", newline="\n"
    )
    return project


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {output}")
    source = _source_state()
    output.mkdir(parents=True)
    payload, sidecars, scenario = _fixture()
    bundle = _write_fixture(output, payload, sidecars, scenario)
    reports: dict[str, Any] = {"source": source, "python": {}, "engines": {}}
    for engine in ("godot", "unity"):
        try:
            _, report = load_adapter_bundle(output, bundle, engine=engine)
            reports["python"][engine] = {
                "status": "PASS",
                "bundle_sha256": report.bundle_sha256,
                "scenario_sha256": report.scenario_sha256,
                "sidecars": list(report.sidecar_capabilities),
                "capabilities": dict(report.decisions),
            }
        except AdapterBundleError as exc:
            reports["python"][engine] = {"status": "FAIL", "error": str(exc)}

    godot = _discover_godot()
    if godot:
        project = _prepare_godot(output, bundle)
        reports["engines"]["godot"] = _run(
            "godot_headless",
            [godot, "--headless", "--path", str(project), "--script", "res://main.gd"],
            project,
        )
    else:
        reports["engines"]["godot"] = {
            "status": "NOT_TESTED",
            "reason": "Godot executable was not discoverable",
        }

    unity = _discover_unity()
    if unity:
        project = _prepare_unity(output, bundle)
        env = os.environ.copy()
        env["NEOENG_RUNTIME_ADAPTER_BUNDLE"] = "runtime/adapters.json"
        reports["engines"]["unity"] = _run(
            "unity_batchmode",
            [
                unity,
                "-batchmode",
                "-nographics",
                "-quit",
                "-projectPath",
                str(project),
                "-executeMethod",
                "NeoEng.DTrace.Editor.RuntimeAdapterGenerator."
                "RunHeadlessRuntimeAdapter",
                "-logFile",
                "-",
            ],
            project,
            env,
        )
    else:
        reports["engines"]["unity"] = {
            "status": "NOT_TESTED",
            "reason": "Unity executable was not discoverable",
        }

    reports["platform"] = platform.platform()
    tracked = _tracked_artifacts(output)
    reports["privacy_leaks"] = _privacy_leaks(tracked)
    reports["artifacts"] = {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path.read_bytes()),
        }
        for path in tracked
        if path.name != "stage8-report.json"
    }
    functional_ok = all(
        item.get("status") == "PASS" for item in reports["python"].values()
    ) and all(item.get("status") == "PASS" for item in reports["engines"].values())
    reports["functional_status"] = "PASS" if functional_ok else "FAIL"
    reports["status"] = (
        "PASS"
        if functional_ok and source["worktree_clean"] and not reports["privacy_leaks"]
        else "FAIL"
    )
    report_path = output / "stage8-report.json"
    report_path.write_bytes(_canonical_json(reports))
    index_payload = {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path.read_bytes()),
        }
        for path in [*tracked, report_path]
    }
    (output / "artifact-index.json").write_bytes(_canonical_json(index_payload))
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(
        json.dumps(
            {"status": report["status"], "output": "<audit-output>"},
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
