"""Audit authored particle scene export through real Godot and Unity importers.

The audit creates a fresh V2 scene with one VFX socket and one deterministic
particle system, exports the same authoring document for both engines, runs
the native importers, captures Godot's real renderer, and preserves deliberate
unbound-socket failures.  It is an evidence harness, not a replacement for
the official test suite.
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
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_unity_import_stage6 import discover_unity  # noqa: E402
from src.exporters.scene_authoring_export import (
    SceneAuthoringExportError,
    save_scene_authoring_export,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneParticleSystemRecord,
    SceneTransformRecord,
    SceneVfxSocketRecord,
)
from src.runtime.particles import ParticleEmitterRecord

GODOT_ADDON = ROOT / "integrations/godot/addons/neoeng_d_trace"
UNITY_PACKAGE = ROOT / "integrations/unity/package/com.neoeng.dtrace"
UNITY_METHOD = (
    "NeoEng.DTrace.Editor.ProfessionalSceneImportGenerator."
    "RunHeadlessProfessionalSceneImport"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize(value: str, temporary_root: Path) -> str:
    result = value.replace(str(temporary_root), "<temporary-project>")
    result = result.replace(str(ROOT), "<repo>")
    return re.sub(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", result)


def _discover_godot() -> Path:
    found = shutil.which("godot")
    if found:
        return Path(found)
    fallback = Path("C:/ProgramData/chocolatey/bin/godot.exe")
    if fallback.is_file():
        return fallback
    raise RuntimeError("Godot executable was not found")


def _document(asset: Path) -> SceneAuthoringDocumentV2:
    digest = _sha256(asset)
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="Post E13 particle scene export",
            generator="NeoEng-D-Trace",
            app_version="0.3.0",
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[
            AssetReferenceRecord(id="hero_asset", path="assets/hero.png", sha256=digest)
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero",
                asset_id="hero_asset",
                layer_id="foreground",
                transform=SceneTransformRecord(
                    position=Point3Record(x=0.0, y=0.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )
        ],
        groups=[],
        camera=SceneCameraAuthoringRecord(position=PointRecord(x=0.0, y=0.0), zoom=1.0),
        sockets=[
            SceneVfxSocketRecord(
                id="fountain-socket",
                layer_id="foreground",
                position=Point3Record(x=0.0, y=0.0, z=0.0),
                rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                effect_id="fountain",
                scale=1.0,
                enabled=True,
            )
        ],
        particle_systems=[
            SceneParticleSystemRecord(
                id="fountain",
                fixed_dt=0.1,
                max_substeps=8,
                loop=True,
                duration=1.0,
                emitters=[
                    ParticleEmitterRecord(
                        id="main",
                        seed=17,
                        origin=Point3Record(x=-48.0, y=20.0, z=0.0),
                        initial_velocity=Point3Record(x=100.0, y=-35.0, z=0.0),
                        velocity_spread=Point3Record(x=35.0, y=20.0, z=0.0),
                        acceleration=Point3Record(x=0.0, y=12.0, z=0.0),
                        emission_rate=10.0,
                        lifetime=1.0,
                        max_particles=8,
                        burst_count=4,
                    )
                ],
            )
        ],
    )


def _write_godot_project(project: Path, export: dict[str, object], asset: Path) -> None:
    (project / "addons").mkdir(parents=True)
    (project / "NeoEngGenerated").mkdir(parents=True)
    (project / "assets").mkdir(parents=True)
    shutil.copytree(GODOT_ADDON, project / "addons/neoeng_d_trace", dirs_exist_ok=True)
    shutil.copy2(asset, project / "assets/hero.png")
    (project / "NeoEngGenerated/scene-authoring.godot.json").write_text(
        json.dumps(export, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "project.godot").write_text(
        "[application]\n"
        'config/name="NeoEng Post E13 Particle Scene Export"\n'
        "[display]\n"
        "window/size/viewport_width=480\n"
        "window/size/viewport_height=270\n"
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
        '    var importer = preload("res://addons/neoeng_d_trace/professional_scene_importer.gd")\n'
        '    var diagnosis = importer.diagnose_export("res://NeoEngGenerated/scene-authoring.godot.json")\n'
        '    if diagnosis.get("status") != "SUCCESS":\n'
        '        print("GODOT_PROFESSIONAL_SCENE_PARTICLE_EXPORT=FAILURE")\n'
        "        print(JSON.stringify(diagnosis)); quit(1); return\n"
        '    var imported = importer.import_scene("res://NeoEngGenerated/scene-authoring.godot.json")\n'
        '    if imported.get("status") != "SUCCESS":\n'
        '        print("GODOT_PROFESSIONAL_SCENE_PARTICLE_EXPORT=FAILURE")\n'
        "        print(JSON.stringify(imported)); quit(1); return\n"
        '    var root = imported["root"]\n'
        '    var particles = root.get_node_or_null("Layer_foreground/Particles_fountain")\n'
        '    if particles == null:\n'
        '        print("GODOT_PROFESSIONAL_SCENE_PARTICLE_EXPORT=FAILURE")\n'
        '        print("particle component was not materialized"); quit(1); return\n'
        '    particles.set_auto_process(false)\n'
        '    var scene_camera = root.get_node_or_null("SceneCamera")\n'
        '    if scene_camera != null:\n'
        '        print("GODOT_PROFESSIONAL_SCENE_CAMERA_IMPORTED=SUCCESS")\n'
        '        scene_camera.enabled = false\n'
        '        scene_camera.get_parent().remove_child(scene_camera)\n'
        '        scene_camera.free()\n'
        '    root.position = Vector2(240.0, 135.0)\n'
        '    var subviewport := SubViewport.new()\n'
        '    subviewport.size = Vector2i(480, 270)\n'
        '    subviewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS\n'
        '    subviewport.transparent_bg = false\n'
        '    get_root().add_child(subviewport)\n'
        '    subviewport.add_child(root)\n'
        '    if int(particles.get_particle_count()) != 0:\n'
        '        print("particle system did not start empty"); quit(1); return\n'
        '    if not particles.advance_fixed_ticks(3):\n'
        '        print("particle system did not advance"); quit(1); return\n'
        '    var particle_count := int(particles.get_particle_count())\n'
        '    if particle_count != 7:\n'
        '        print("unexpected particle count: " + str(particle_count)); quit(1); return\n'
        '    print("GODOT_NATIVE_PROFESSIONAL_SCENE_PARTICLE_EXPORT=SUCCESS")\n'
        '    print("GODOT_PROFESSIONAL_SCENE_PARTICLES=1")\n'
        '    print("GODOT_PROFESSIONAL_SCENE_PARTICLE_EMITTERS=" + str(particles.get_emitter_count()))\n'
        '    print("GODOT_PROFESSIONAL_SCENE_PARTICLE_COUNT=" + str(particle_count))\n'
        '    print("GODOT_PROFESSIONAL_SCENE_PARTICLE_STATE_SHA256=" + str(particles.get_meta("neoeng_particle_state_sha256", "")))\n'
        '    if DisplayServer.get_name() == "headless" or DisplayServer.get_name() == "dummy":\n'
        '        print("GODOT_PROFESSIONAL_SCENE_PARTICLE_CAPTURE=NOT_AVAILABLE_HEADLESS")\n'
        '        print("GODOT_PROFESSIONAL_SCENE_PARTICLE_CAPTURE_LIMITATION=renderer backend does not expose pixels in headless mode")\n'
        '        root.queue_free(); subviewport.queue_free()\n'
        '        quit(0); return\n'
        '    await process_frame\n'
        '    await process_frame\n'
        '    var capture_timer := Timer.new()\n'
        '    capture_timer.wait_time = 0.25\n'
        '    capture_timer.one_shot = true\n'
        '    get_root().add_child(capture_timer)\n'
        '    capture_timer.start()\n'
        '    await capture_timer.timeout\n'
        '    await process_frame\n'
        '    await process_frame\n'
        '    var texture = subviewport.get_texture()\n'
        '    if texture == null:\n'
        '        print("scene particle capture texture is unavailable"); quit(1); return\n'
        '    var image = texture.get_image()\n'
        '    if image == null:\n'
        '        print("scene particle capture image is unavailable"); quit(1); return\n'
        '    var capture_path = ProjectSettings.globalize_path("res://scene-particles.png")\n'
        '    if image.save_png(capture_path) != OK:\n'
        '        print("scene particle capture failed"); quit(1); return\n'
        '    print("GODOT_PROFESSIONAL_SCENE_PARTICLE_CAPTURE=SUCCESS")\n'
        '    root.queue_free(); subviewport.queue_free()\n'
        '    await process_frame\n'
        '    quit(0)\n',
        encoding="utf-8",
        newline="\n",
    )
    (project / "failure.gd").write_text(
        "extends SceneTree\n"
        "func _init():\n"
        '    var importer = preload("res://addons/neoeng_d_trace/professional_scene_importer.gd")\n'
        '    var result = importer.diagnose_export("res://NeoEngGenerated/scene-authoring.godot.json")\n'
        '    if result.get("status") == "SUCCESS":\n'
        '        print("GODOT_PROFESSIONAL_SCENE_PARTICLE_FAILURE_GUARD=FAILURE"); quit(1); return\n'
        '    print("GODOT_PROFESSIONAL_SCENE_PARTICLE_FAILURE_GUARD=PASS")\n'
        '    print(JSON.stringify(result)); quit(0)\n',
        encoding="utf-8",
        newline="\n",
    )
    (project / "window.gd").write_text(
        "extends SceneTree\n"
        "\n"
        "func _init():\n"
        '    call_deferred("_run")\n'
        "\n"
        "func _result(status: String, particle_count: int, message: String = \"\") -> void:\n"
        '    var handle = FileAccess.open("res://window-result.json", FileAccess.WRITE)\n'
        '    handle.store_string(JSON.stringify({"status": status, "particle_count": particle_count, "message": message, "display_server": DisplayServer.get_name()}))\n'
        "\n"
        "func _run():\n"
        '    var importer = preload("res://addons/neoeng_d_trace/professional_scene_importer.gd")\n'
        '    var imported = importer.import_scene("res://NeoEngGenerated/scene-authoring.godot.json")\n'
        '    if imported.get("status") != "SUCCESS":\n'
        '        _result("FAILED", 0, JSON.stringify(imported)); quit(1); return\n'
        '    var root = imported["root"]\n'
        '    var particles = root.get_node_or_null("Layer_foreground/Particles_fountain")\n'
        '    if particles == null:\n'
        '        _result("FAILED", 0, "particle component was not materialized"); quit(1); return\n'
        '    particles.set_auto_process(false)\n'
        '    root.position = Vector2(240.0, 135.0)\n'
        '    get_root().add_child(root)\n'
        '    if int(particles.get_particle_count()) != 0:\n'
        '        _result("FAILED", int(particles.get_particle_count()), "particle system did not start empty"); quit(1); return\n'
        '    if not particles.advance_fixed_ticks(3):\n'
        '        _result("FAILED", 0, "particle system did not advance"); quit(1); return\n'
        '    var particle_count := int(particles.get_particle_count())\n'
        '    if particle_count != 7:\n'
        '        _result("FAILED", particle_count, "unexpected particle count"); quit(1); return\n'
        '    await process_frame\n'
        '    await process_frame\n'
        '    var texture = get_root().get_texture()\n'
        '    if texture == null:\n'
        '        _result("FAILED", particle_count, "native window texture is unavailable"); quit(1); return\n'
        '    var image = texture.get_image()\n'
        '    if image == null:\n'
        '        _result("FAILED", particle_count, "native window image is unavailable"); quit(1); return\n'
        '    var capture_path = ProjectSettings.globalize_path("res://scene-particles-window.png")\n'
        '    if image.save_png(capture_path) != OK:\n'
        '        _result("FAILED", particle_count, "native window capture failed"); quit(1); return\n'
        '    _result("SUCCESS", particle_count)\n'
        '    print("GODOT_NATIVE_WINDOW_SCENE_PARTICLE_CAPTURE=SUCCESS")\n'
        '    print("GODOT_NATIVE_WINDOW_SCENE_PARTICLE_COUNT=" + str(particle_count))\n'
        '    await process_frame\n'
        '    root.queue_free()\n'
        '    quit(0)\n',
        encoding="utf-8",
        newline="\n",
    )


def _run_godot(
    godot: Path, project: Path, temporary_root: Path, label: str
) -> dict[str, object]:
    preimport = subprocess.run(
        [
            str(godot),
            "--headless",
            "--editor",
            "--path",
            str(project),
            "--import",
            "--quit-after",
            "5",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    preimport_output = _sanitize(preimport.stdout + preimport.stderr, temporary_root)
    try:
        completed = subprocess.run(
            [
                str(godot),
                "--headless",
                "--path",
                str(project),
                "--script",
                "res://main.gd",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        output = "PREIMPORT\n" + preimport_output + "\nRUNTIME\n" + _sanitize(
            completed.stdout + completed.stderr, temporary_root
        )
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        output = (
            "PREIMPORT\n"
            + preimport_output
            + "\nRUNTIME\n"
            + _sanitize(
                str(stdout) + str(stderr) + "\nGODOT_AUDIT_TIMEOUT=FAILURE\n",
                temporary_root,
            )
        )
        returncode = 124
    log = project / f"{label}.log"
    log.write_text(output, encoding="utf-8", newline="\n")
    count = re.search(r"GODOT_PROFESSIONAL_SCENE_PARTICLE_COUNT=(\d+)", output)
    emitters = re.search(r"GODOT_PROFESSIONAL_SCENE_PARTICLE_EMITTERS=(\d+)", output)
    return {
        "returncode": returncode,
        "success_marker": "GODOT_NATIVE_PROFESSIONAL_SCENE_PARTICLE_EXPORT=SUCCESS" in output,
        "capture_marker": "GODOT_PROFESSIONAL_SCENE_PARTICLE_CAPTURE=SUCCESS" in output,
        "headless_capture_mode": "GODOT_PROFESSIONAL_SCENE_PARTICLE_CAPTURE=NOT_AVAILABLE_HEADLESS" in output,
        "particle_count": int(count.group(1)) if count else None,
        "emitters": int(emitters.group(1)) if emitters else None,
        "diagnostics": [
            line.strip()
            for line in output.splitlines()
            if "ERROR" in line or "SCRIPT ERROR" in line or "FAILURE" in line
        ][:30],
        "log_sha256": _sha256(log),
    }


def _run_godot_window(
    godot: Path, project: Path, temporary_root: Path, label: str
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [str(godot), "--path", str(project), "--script", "res://window.gd"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        output = _sanitize(completed.stdout + completed.stderr, temporary_root)
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        output = _sanitize(
            str(stdout) + str(stderr) + "\nGODOT_NATIVE_WINDOW_AUDIT_TIMEOUT=FAILURE\n",
            temporary_root,
        )
        returncode = 124
    result_path = project / "window-result.json"
    result: dict[str, object] = {}
    if result_path.is_file():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result = {"status": "FAILED", "message": "window result was invalid JSON"}
    capture = project / "scene-particles-window.png"
    log = project / f"{label}.log"
    log.write_text(
        output + ("\nWINDOW_RESULT\n" + json.dumps(result, ensure_ascii=False) if result else ""),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "returncode": returncode,
        "capture_marker": result.get("status") == "SUCCESS" and capture.is_file(),
        "particle_count": result.get("particle_count"),
        "display_server": result.get("display_server"),
        "result": result,
        "capture_sha256": _sha256(capture) if capture.is_file() else None,
        "diagnostics": [
            line.strip()
            for line in output.splitlines()
            if "ERROR" in line or "FAILURE" in line or "SCRIPT ERROR" in line
        ][:30],
        "log_sha256": _sha256(log),
    }


def _run_godot_failure(
    godot: Path, project: Path, temporary_root: Path, label: str
) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [str(godot), "--headless", "--path", str(project), "--script", "res://failure.gd"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        output = _sanitize(completed.stdout + completed.stderr, temporary_root)
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        output = _sanitize(str(stdout) + str(stderr) + "\nGODOT_AUDIT_TIMEOUT=FAILURE\n", temporary_root)
        returncode = 124
    log = project / f"{label}.log"
    log.write_text(output, encoding="utf-8", newline="\n")
    return {
        "returncode": returncode,
        "guard_marker": "GODOT_PROFESSIONAL_SCENE_PARTICLE_FAILURE_GUARD=PASS" in output,
        "diagnostics": [line.strip() for line in output.splitlines() if "particle" in line.lower() or "ERROR" in line][:30],
        "log_sha256": _sha256(log),
    }


def _write_unity_project(project: Path, unity_version: str) -> None:
    (project / "ProjectSettings").mkdir(parents=True)
    (project / "Packages").mkdir(parents=True)
    (project / "Assets/NeoEngGenerated").mkdir(parents=True)
    (project / "Assets/assets").mkdir(parents=True)
    (project / "ProjectSettings/ProjectVersion.txt").write_text(
        f"m_EditorVersion: {unity_version}\n", encoding="utf-8", newline="\n"
    )
    package_reference = os.path.relpath(UNITY_PACKAGE, project / "Packages").replace("\\", "/")
    (project / "Packages/manifest.json").write_text(
        json.dumps(
            {
                "dependencies": {
                    "com.unity.modules.particlesystem": "1.0.0",
                    "com.unity.modules.jsonserialize": "1.0.0",
                    "com.neoeng.dtrace": f"file:{package_reference}",
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sprite_meta() -> str:
    return (
        "\n".join(
            [
                "fileFormatVersion: 2",
                "guid: 1c5a84e2a98a42bf9fe8910d5c25ec67",
                "TextureImporter:",
                "  internalIDToNameTable: []",
                "  externalObjects: {}",
                "  serializedVersion: 12",
                "  mipmaps:",
                "    mipMapMode: 0",
                "    enableMipMap: 0",
                "    sRGBTexture: 1",
                "  textureType: 8",
                "  spriteMode: 1",
                "  spritePixelsToUnits: 100",
                "  alphaIsTransparency: 1",
            ]
        )
        + "\n"
    )


def _run_unity(
    unity: Path, project: Path, temporary_root: Path, label: str
) -> dict[str, object]:
    log = project / f"{label}.log"
    environment = os.environ.copy()
    environment["NEOENG_PROFESSIONAL_SCENE_EXPORT"] = "Assets/NeoEngGenerated/scene-authoring.unity.json"
    completed = subprocess.run(
        [
            str(unity),
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            UNITY_METHOD,
            "-logFile",
            str(log),
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    output = _sanitize(output, temporary_root)
    log.write_text(output, encoding="utf-8", newline="\n")
    count = re.search(r"UNITY_PROFESSIONAL_SCENE_PARTICLE_COUNT=(\d+)", output)
    emitters = re.search(r"UNITY_PROFESSIONAL_SCENE_PARTICLES=(\d+)", output)
    return {
        "returncode": completed.returncode,
        "success_marker": "UNITY_NATIVE_PROFESSIONAL_SCENE_PARTICLE_EXPORT=SUCCESS" in output,
        "particle_component_count": int(emitters.group(1)) if emitters else None,
        "particle_count": int(count.group(1)) if count else None,
        "diagnostics": [
            line.strip()
            for line in output.splitlines()
            if (
                "Error:" in line
                or "Exception" in line
                or "Curl error" in line
                or "error CS" in line
                or "COMPIL" in line.upper()
            )
        ][:30],
        "log_sha256": _sha256(log),
    }


def _write_export(document: SceneAuthoringDocumentV2, destination: Path, target: str) -> None:
    save_scene_authoring_export(document, destination, target=target)


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    godot = _discover_godot()
    unity, unity_version = discover_unity()
    with tempfile.TemporaryDirectory(prefix="neoeng-dtrace-post-e13-particle-scene-") as temp:
        temporary_root = Path(temp)
        asset = temporary_root / "hero.png"
        Image.new("RGBA", (24, 24), (30, 80, 120, 255)).save(asset)
        document = _document(asset)

        godot_project = temporary_root / "godot-positive"
        godot_export = godot_project / "NeoEngGenerated/scene-authoring.godot.json"
        godot_project.mkdir()
        godot_payload = json.loads(
            json.dumps(
                document.model_dump(mode="json"), ensure_ascii=False, sort_keys=True
            )
        )
        _write_godot_project(godot_project, godot_payload, asset)
        _write_export(document, godot_export, "godot")
        godot_positive = _run_godot(godot, godot_project, temporary_root, "positive")
        godot_window = _run_godot_window(godot, godot_project, temporary_root, "native-window")

        godot_negative = temporary_root / "godot-negative"
        shutil.copytree(godot_project, godot_negative)
        negative_payload = json.loads(
            (godot_negative / "NeoEngGenerated/scene-authoring.godot.json").read_text(
                encoding="utf-8"
            )
        )
        negative_payload["scene"]["sockets"] = []
        (godot_negative / "NeoEngGenerated/scene-authoring.godot.json").write_text(
            json.dumps(negative_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        shutil.copy2(godot_project / "failure.gd", godot_negative / "failure.gd")
        godot_failure = _run_godot_failure(godot, godot_negative, temporary_root, "negative-unbound")

        unity_project = temporary_root / "unity-positive"
        unity_negative = temporary_root / "unity-negative"
        for project in (unity_project, unity_negative):
            _write_unity_project(project, unity_version)
            unity_asset = project / "Assets/assets/hero.png"
            Image.new("RGBA", (24, 24), (30, 80, 120, 255)).save(unity_asset)
            (unity_asset.with_suffix(".png.meta")).write_text(
                _sprite_meta(), encoding="utf-8", newline="\n"
            )
            _write_export(
                document,
                project / "Assets/NeoEngGenerated/scene-authoring.unity.json",
                "unity",
            )
        unity_positive = _run_unity(unity, unity_project, temporary_root, "positive")
        unity_negative_payload = json.loads(
            (unity_negative / "Assets/NeoEngGenerated/scene-authoring.unity.json").read_text(
                encoding="utf-8"
            )
        )
        unity_negative_payload["scene"]["sockets"] = []
        (unity_negative / "Assets/NeoEngGenerated/scene-authoring.unity.json").write_text(
            json.dumps(unity_negative_payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        unity_failure = _run_unity(unity, unity_negative, temporary_root, "negative-unbound")

        for project, label in (
            (godot_project, "godot-positive"),
            (godot_negative, "godot-negative-unbound"),
            (unity_project, "unity-positive"),
            (unity_negative, "unity-negative-unbound"),
        ):
            log_path = project / ("positive.log" if "positive" in label else "negative-unbound.log")
            if log_path.is_file():
                shutil.copy2(log_path, output / f"{label}.log")
        if (godot_project / "native-window.log").is_file():
            shutil.copy2(godot_project / "native-window.log", output / "godot-native-window.log")
        if (godot_project / "window-result.json").is_file():
            shutil.copy2(godot_project / "window-result.json", output / "godot-window-result.json")

        shutil.copy2(
            godot_export, output / "scene-authoring.godot.json"
        )
        shutil.copy2(
            godot_project / "assets/hero.png", output / "hero-godot.png"
        )
        godot_capture = godot_project / "scene-particles.png"
        if godot_capture.is_file():
            shutil.copy2(godot_capture, output / "scene-particles.png")
        godot_window_capture = godot_project / "scene-particles-window.png"
        if godot_window_capture.is_file():
            shutil.copy2(godot_window_capture, output / "scene-particles-window.png")
        shutil.copy2(
            unity_project / "Assets/NeoEngGenerated/scene-authoring.unity.json",
            output / "scene-authoring.unity.json",
        )
        shutil.copy2(
            unity_project / "Assets/assets/hero.png", output / "hero-unity.png"
        )
        python_failure = "PASS"
        try:
            _write_export(
                document.model_copy(update={"sockets": []}),
                temporary_root / "should-not-export.json",
                "unity",
            )
        except SceneAuthoringExportError:
            python_failure = "PASS"
        else:
            python_failure = "FAIL"

    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    report: dict[str, object] = {
        "schema_version": 1,
        "stage": "post-e13-particle-scene-export-native",
        "status": "PASS",
        "source": {
            "branch": subprocess.run(
                ["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, check=True
            ).stdout.strip(),
            "commit": source_commit,
            "worktree_clean": not bool(
                subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
            ),
        },
        "engines": {
            "godot": {
                "version": subprocess.run([str(godot), "--version"], capture_output=True, text=True, check=True).stdout.strip(),
                "positive": godot_positive,
                "native_window": godot_window,
                "negative_unbound": godot_failure,
            },
            "unity": {
                "version": unity_version,
                "positive": unity_positive,
                "negative_unbound": unity_failure,
            },
        },
        "python_failure_guard": python_failure,
        "artifacts": {},
        "limitations": [
            "Unity foi executado em batchmode/nographics; a captura visual nativa deste checkpoint é do Godot.",
            "A execução headless Godot comprova importação, materialização e contagem, mas o backend dummy não expõe pixels; a captura visual é feita em uma segunda execução nativa com janela real e é mantida separada no relatório.",
            "A imagem comprova o renderer Godot do componente importado; não substitui a revisão humana final.",
            "A ponte cobre os campos v1 do emissor; textura, cor e tamanho autorais continuam fora do schema de partículas.",
        ],
    }
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "post-e13-particle-scene-export-report.json":
            report["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    checks = [
        godot_positive["returncode"] == 0,
        godot_positive["success_marker"],
        godot_positive["headless_capture_mode"],
        godot_positive["particle_count"] == 7,
        godot_positive["emitters"] == 1,
        godot_window["returncode"] == 0,
        godot_window["capture_marker"],
        godot_window["particle_count"] == 7,
        godot_failure["returncode"] == 0,
        godot_failure["guard_marker"],
        unity_positive["returncode"] == 0,
        unity_positive["success_marker"],
        unity_positive["particle_component_count"] == 1,
        unity_positive["particle_count"] == 7,
        unity_failure["returncode"] != 0,
        unity_failure["success_marker"] is False,
        python_failure == "PASS",
    ]
    report["checks"] = {"passed": sum(bool(item) for item in checks), "total": len(checks)}
    report["status"] = "PASS" if all(checks) else "FAIL"
    report_path = output / "post-e13-particle-scene-export-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    index = {
        "schema_version": 1,
        "stage": report["stage"],
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in sorted(output.iterdir())
            if path.is_file()
        },
    }
    (output / "artifact-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({"status": report["status"], "output": "<audit-output>"}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
