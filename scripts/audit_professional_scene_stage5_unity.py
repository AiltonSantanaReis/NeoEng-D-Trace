"""Run the real Unity Stage 5 professional-scene adapter audit."""

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

from PIL import Image

from scripts.audit_professional_scene_stage5 import _document
from scripts.audit_unity_package_stage5 import (
    _discover_unity,
)
from scripts.audit_unity_package_stage5 import _sanitize as _sanitize_unity
from src.exporters.scene_authoring_export import save_scene_authoring_export

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations/unity/package/com.neoeng.dtrace"
OUT = ROOT / "docs/evidence/artifacts/stage5-professional-scene-2026-08-19"
METHOD = (
    "NeoEng.DTrace.Editor.ProfessionalSceneImportGenerator."
    "RunHeadlessProfessionalSceneImport"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_project(project: Path, unity_version: str) -> None:
    (project / "ProjectSettings").mkdir(parents=True)
    (project / "Packages").mkdir(parents=True)
    (project / "Assets/NeoEngGenerated").mkdir(parents=True)
    (project / "Assets/assets").mkdir(parents=True)
    (project / "ProjectSettings/ProjectVersion.txt").write_text(
        f"m_EditorVersion: {unity_version}\n", encoding="utf-8", newline="\n"
    )
    package_reference = os.path.relpath(PACKAGE_ROOT, project / "Packages").replace(
        "\\", "/"
    )
    (project / "Packages/manifest.json").write_text(
        json.dumps(
            {"dependencies": {"com.neoeng.dtrace": f"file:{package_reference}"}},
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
                "guid: 9f2e7f0c4c714f24a8d91a1b5a5e18d7",
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
    log = temporary_root / f"{label}.log"
    environment = os.environ.copy()
    environment["NEOENG_PROFESSIONAL_SCENE_EXPORT"] = (
        "Assets/NeoEngGenerated/scene-authoring.unity.json"
    )
    completed = subprocess.run(
        [
            str(unity),
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath",
            str(project),
            "-executeMethod",
            METHOD,
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
    sanitized = _sanitize_unity(output, temporary_root)
    diagnostic_lines = [
        line.strip()
        for line in sanitized.splitlines()
        if "Error:" in line or "Curl error" in line or "timeout" in line.lower()
    ][:20]
    destination = OUT / f"unity-{label}.log"
    destination.write_text(sanitized, encoding="utf-8", newline="\n")
    layer_match = re.search(r"UNITY_PROFESSIONAL_SCENE_LAYERS=(\d+)", sanitized)
    object_match = re.search(r"UNITY_PROFESSIONAL_SCENE_OBJECTS=(\d+)", sanitized)
    return {
        "returncode": completed.returncode,
        "success_marker": "UNITY_NATIVE_PROFESSIONAL_SCENE_STAGE5=SUCCESS" in sanitized,
        "failure_marker": "UNITY_NATIVE_PROFESSIONAL_SCENE_STAGE5=FAILURE" in sanitized,
        "layers": int(layer_match.group(1)) if layer_match else None,
        "objects": int(object_match.group(1)) if object_match else None,
        "diagnostic_lines": diagnostic_lines,
        "log_sha256": _sha256(destination),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    args = parser.parse_args()
    unity, unity_version = (
        (args.unity, args.unity.parents[1].name) if args.unity else _discover_unity()
    )
    if not unity.is_file() or not PACKAGE_ROOT.is_dir():
        raise RuntimeError("Unity executable or package directory is missing")
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-dtrace-stage5-unity-") as temp:
        temporary_root = Path(temp)
        positive = temporary_root / "positive"
        negative = temporary_root / "negative"
        for project in (positive, negative):
            _write_project(project, unity_version)
            image = Image.new("RGBA", (8, 8), (30, 80, 120, 255))
            image.save(project / "Assets/assets/hero.png")
            (project / "Assets/assets/hero.png.meta").write_text(
                _sprite_meta(), encoding="utf-8", newline="\n"
            )
        document = _document(positive / "Assets/assets/hero.png")
        save_scene_authoring_export(
            document,
            positive / "Assets/NeoEngGenerated/scene-authoring.unity.json",
            target="unity",
        )
        save_scene_authoring_export(
            document,
            negative / "Assets/NeoEngGenerated/scene-authoring.unity.json",
            target="unity",
        )
        (negative / "Assets/assets/hero.png").write_bytes(b"tampered after export")
        positive_run = _run_unity(unity, positive, temporary_root, "positive")
        negative_run = _run_unity(unity, negative, temporary_root, "negative-hash")
        negative_log = (OUT / "unity-negative-hash.log").read_text(encoding="utf-8")
        negative_run["expected_hash_rejection"] = (
            "asset hash does not match" in negative_log
        )
        shutil.copy2(
            positive / "Assets/NeoEngGenerated/scene-authoring.unity.json",
            OUT / "scene-authoring.unity.json",
        )
        shutil.copy2(positive / "Assets/assets/hero.png", OUT / "hero-unity.png")
    report = {
        "schema_version": 1,
        "engine": "unity",
        "engine_version": unity_version,
        "positive": positive_run,
        "negative_hash": negative_run,
        "artifacts": {
            "asset": {
                "bytes": (OUT / "hero-unity.png").stat().st_size,
                "sha256": _sha256(OUT / "hero-unity.png"),
            },
            "export": {
                "bytes": (OUT / "scene-authoring.unity.json").stat().st_size,
                "sha256": _sha256(OUT / "scene-authoring.unity.json"),
            },
        },
    }
    (OUT / "unity-stage5-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if (
        positive_run["returncode"] != 0
        or not positive_run["success_marker"]
        or positive_run["layers"] != 1
        or positive_run["objects"] != 1
        or negative_run["returncode"] == 0
        or not negative_run["failure_marker"]
        or not negative_run["expected_hash_rejection"]
    ):
        raise RuntimeError(f"Unity Stage 5 adapter audit failed: {report}")
    print("UNITY_REAL_PROFESSIONAL_SCENE_STAGE5=PASS")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
