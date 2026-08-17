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

from src.exporters.integration_manifest import (
    build_integration_manifest,
    save_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace"
OUT = ROOT / "docs" / "evidence" / "artifacts" / "unity-import-stage6-2026-08-16"
IMPORT_METHOD = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessImport"
MANUAL_METHOD = "NeoEng.DTrace.Editor.UnityImportGenerator.CreateManualPrefabFixture"


def discover_unity() -> tuple[Path, str]:
    roots = []
    for variable in ("ProgramFiles", "ProgramW6464", "ProgramFiles(x86)"):
        value = os.environ.get(variable)
        if value:
            roots.append(Path(value) / "Unity" / "Hub" / "Editor")
    roots.extend(
        [
            Path("C:/Program Files/Unity/Hub/Editor"),
            Path("C:/Program Files (x86)/Unity/Hub/Editor"),
        ]
    )
    candidates = []
    for root in roots:
        if not root.is_dir():
            continue
        for version in root.iterdir():
            executable = version / "Editor" / "Unity.exe"
            if executable.is_file():
                candidates.append((executable, version.name))
    if not candidates:
        raise RuntimeError("Unity Editor executable was not found")
    preferred = [item for item in candidates if item[1] == "6000.5.7f1"]
    return sorted(preferred or candidates, key=lambda item: item[1], reverse=True)[0]


def sanitize(text: str, temporary_root: Path) -> str:
    value = text.replace(str(temporary_root), "<local-path>")
    value = value.replace(str(ROOT), "<repo>")
    value = value.replace(str(PACKAGE_ROOT), "<package>")
    value = re.sub(r"[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", value)
    value = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<network-address>", value)
    value = re.sub(
        r"(?im)^(\s*(?:Machine Id|Session Id|Correlation Id|External correlation Id):).*$",
        r"\1<redacted>",
        value,
    )
    value = re.sub(r"(?i)LicenseClient-[A-Za-z0-9_.-]+", "LicenseClient-<redacted>", value)
    value = re.sub(r"(?i)\bPId:\s*\d+", "PId: <redacted>", value)
    value = re.sub(r"(?i)\bprocessId\"?\s*[:=]\s*\d+", "processId: <redacted>", value)
    value = re.sub(r"(?i)\bprocess\s+Id:\s*\d+", "process Id: <redacted>", value)
    value = re.sub(r"(?i)\bPort\s+\d+", "Port <redacted>", value)
    value = re.sub(r"WindowsEditor\([^)]*\)", "WindowsEditor(<redacted>)", value)
    value = re.sub(r"(?im)Player connection\s*\[\d+\][^\\\r\n\"]*(?=\\+n|\r?\n|\\\"|\"|$)", "<redacted-player-connection>", value)
    return value

def write_project(project: Path, package_path: Path, unity_version: str) -> None:
    (project / "ProjectSettings").mkdir(parents=True)
    (project / "Packages").mkdir(parents=True)
    (project / "Assets" / "NeoEngInput").mkdir(parents=True)
    relative_package = os.path.relpath(package_path, project / "Packages").replace(
        "\\", "/"
    )
    (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
        f"m_EditorVersion: {unity_version}\n", encoding="utf-8", newline="\n"
    )
    (project / "Packages" / "manifest.json").write_text(
        json.dumps(
            {"dependencies": {"com.neoeng.dtrace": f"file:{relative_package}"}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def create_fixture(project: Path, mutate_source: bool = False) -> None:
    source = project / "Assets" / "source.png"
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((4, 6, 20, 22), fill=(40, 180, 240, 255))
    image.save(source)
    scene = Scene()
    scene.load_image(image, "source.png")
    scene.image_path = "source.png"
    scene.image_path_kind = "relative"
    scene.add_object("hero", [(4, 6), (20, 6), (20, 22), (4, 22)], select=False)
    scene.objects["hero"].set_pivot(0.5, 0.5)
    metadata = export_scene_metadata(scene)
    manifest = build_integration_manifest(
        metadata,
        engine="unity",
        image_path=source,
        image_reference="source.png",
    )
    save_integration_manifest(
        manifest, project / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
    )
    if mutate_source:
        image.putpixel((0, 0), (255, 0, 0, 255))
        image.save(source)


def run_unity(
    executable: Path,
    project: Path,
    method: str,
    temporary_root: Path,
    report: Path | None = None,
) -> dict[str, Any]:
    environment = os.environ.copy()
    if report is not None:
        environment["NEOENG_STAGE6_REPORT"] = str(report)
        environment["NEOENG_STAGE6_MANIFEST"] = (
            "Assets/NeoEngInput/hero.ndt.integration.json"
        )
    log = temporary_root / f"{project.name}-{method.split('.')[-1]}.log"
    command = [
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
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "returncode": completed.returncode,
        "success_marker": "UNITY_NATIVE_IMPORT_STAGE6=SUCCESS" in output,
        "failure_marker": "UNITY_NATIVE_IMPORT_STAGE6=FAILURE" in output,
        "output": sanitize(output, temporary_root),
    }


def load_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Unity did not produce {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_positive(run: dict[str, Any], report: dict[str, Any]) -> None:
    if run["returncode"] != 0 or not run["success_marker"] or not report["Success"]:
        raise RuntimeError("Unity import positive case failed")
    if report["ImportedSprites"] != 1 or report["ImportedPrefabs"] != 1:
        raise RuntimeError("Unity import positive counts are invalid")
    asset = report["Assets"][0]
    if asset["ColliderPointCount"] != 4 or not asset["PrefabPath"].startswith(
        "Assets/NeoEngGenerated/"
    ):
        raise RuntimeError("Unity import generated asset contract is invalid")


def digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    args = parser.parse_args()
    executable, unity_version = (
        (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    )
    if not executable.is_file() or not PACKAGE_ROOT.is_dir():
        raise RuntimeError("Unity executable or package directory is missing")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    with tempfile.TemporaryDirectory(
        prefix="neoeng-dtrace-stage6-", ignore_cleanup_errors=True
    ) as temporary:
        temporary_root = Path(temporary)
        positive_one = temporary_root / "positive-one"
        positive_two = temporary_root / "positive-two"
        negative_hash = temporary_root / "negative-hash"
        negative_manual = temporary_root / "negative-manual"
        for project in (positive_one, positive_two, negative_hash, negative_manual):
            write_project(project, PACKAGE_ROOT, unity_version)
        create_fixture(positive_one)
        create_fixture(positive_two)
        create_fixture(negative_hash, mutate_source=True)
        create_fixture(negative_manual)

        positive_one_path = temporary_root / "positive-one-report.json"
        positive_two_path = temporary_root / "positive-two-report.json"
        negative_hash_path = temporary_root / "negative-hash-report.json"
        negative_manual_path = temporary_root / "negative-manual-report.json"
        positive_one_run = run_unity(
            executable, positive_one, IMPORT_METHOD, temporary_root, positive_one_path
        )
        positive_one_report = load_report(positive_one_path)
        assert_positive(positive_one_run, positive_one_report)

        positive_two_run = run_unity(
            executable, positive_two, IMPORT_METHOD, temporary_root, positive_two_path
        )
        positive_two_report = load_report(positive_two_path)
        assert_positive(positive_two_run, positive_two_report)
        if json.dumps(positive_one_report, sort_keys=True) != json.dumps(
            positive_two_report, sort_keys=True
        ):
            raise RuntimeError("Unity import reports are not deterministic")

        negative_hash_run = run_unity(
            executable, negative_hash, IMPORT_METHOD, temporary_root, negative_hash_path
        )
        negative_hash_report = load_report(negative_hash_path)
        if (
            negative_hash_run["returncode"] == 0
            or not negative_hash_run["failure_marker"]
            or negative_hash_report["Success"]
            or "hash" not in negative_hash_report["Error"].lower()
        ):
            raise RuntimeError("Unity import did not reject image hash drift")

        manual_setup = run_unity(
            executable, negative_manual, MANUAL_METHOD, temporary_root
        )
        if manual_setup["returncode"] != 0:
            raise RuntimeError("Unity manual prefab fixture could not be created")
        negative_manual_run = run_unity(
            executable,
            negative_manual,
            IMPORT_METHOD,
            temporary_root,
            negative_manual_path,
        )
        negative_manual_report = load_report(negative_manual_path)
        if (
            negative_manual_run["returncode"] == 0
            or not negative_manual_run["failure_marker"]
            or negative_manual_report["Success"]
            or "manual" not in negative_manual_report["Error"].lower()
        ):
            raise RuntimeError("Unity import did not block a manual generated root")

        final = {
            "schema_version": 1,
            "stage": 6,
            "status": "SUCCESS",
            "engine": "unity",
            "unity_version": unity_version,
            "positive": {
                "returncode": positive_one_run["returncode"],
                "marker": "UNITY_NATIVE_IMPORT_STAGE6=SUCCESS",
                "report": positive_one_report,
            },
            "repeat": {
                "returncode": positive_two_run["returncode"],
                "marker": "UNITY_NATIVE_IMPORT_STAGE6=SUCCESS",
                "report_identical": True,
            },
            "negative_hash": {
                "returncode": negative_hash_run["returncode"],
                "marker": "UNITY_NATIVE_IMPORT_STAGE6=FAILURE",
                "hash_drift_rejected": True,
                "report": negative_hash_report,
            },
            "negative_manual": {
                "returncode": negative_manual_run["returncode"],
                "marker": "UNITY_NATIVE_IMPORT_STAGE6=FAILURE",
                "manual_content_rejected": True,
                "report": negative_manual_report,
            },
        }
        (OUT / "stage6-report.json").write_text(
            json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        (OUT / "stage6-report-repeat.json").write_bytes(positive_two_path.read_bytes())
        (OUT / "stage6-report-negative-hash.json").write_bytes(
            negative_hash_path.read_bytes()
        )
        (OUT / "stage6-report-negative-manual.json").write_bytes(
            negative_manual_path.read_bytes()
        )
        (OUT / "fixture-manifest.json").write_bytes(
            (
                positive_one / "Assets" / "NeoEngInput" / "hero.ndt.integration.json"
            ).read_bytes()
        )
        for name, run in (
            ("unity-import-positive.log", positive_one_run),
            ("unity-import-repeat.log", positive_two_run),
            ("unity-import-negative-hash.log", negative_hash_run),
            ("unity-import-negative-manual.log", negative_manual_run),
            ("unity-manual-fixture.log", manual_setup),
        ):
            (OUT / name).write_text(run["output"], encoding="utf-8", newline="\n")

    files = {
        path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()
    }
    (OUT / "stage6-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": 6,
                "status": "SUCCESS",
                "engine": "unity",
                "unity_version": unity_version,
                "files": files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("NATIVE_IMPORT_STAGE6=SUCCESS")
    print(f"UNITY_VERSION={unity_version}")
    print("SPRITE_ASSET=LOADED")
    print("SCRIPTABLE_OBJECT=LOADED")
    print("POLYGON_COLLIDER2D=VALIDATED")
    print("PREFAB=VALIDATED")
    print("HASH_DRIFT=REJECTED")
    print("MANUAL_CONTENT=REJECTED")
    print("REPEAT_IMPORT=DETERMINISTIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
