"""Execute smoke tests against a portable Windows release bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(REPOSITORY_ROOT))

from src.core.app_identity import APP_VERSION


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(command: list[str], environment: dict[str, str], timeout: int = 60):
    result = subprocess.run(
        command,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command[0]}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def _write_engine_input(fixture: Path, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    image_path = directory / "source.png"
    image = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 50, 139, 69), fill=(30, 180, 240, 255))
    image.save(image_path, format="PNG")

    payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload["image"] = {
        "path": image_path.name,
        "path_kind": "relative",
        "sha256": sha256_file(image_path),
    }
    points = [
        {"x": 100, "y": 50},
        {"x": 140, "y": 50},
        {"x": 140, "y": 70},
        {"x": 100, "y": 70},
    ]
    payload["objects"] = [
        {
            "id": "sprite_ação",
            "layer_id": "layer_default",
            "polygon": points,
            "collision": points,
            "beziers": None,
        }
    ]
    project = directory / "engine-input.ndtproj"
    project.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return project


def _generate_engine_fixture(
    cli: Path,
    source_fixture: Path,
    output: Path,
    profile: str,
    environment: dict[str, str],
) -> None:
    project = _write_engine_input(source_fixture, output)
    metadata = output / f"probe-{profile}.json"
    glb = output / "scene.glb"
    result = run_checked(
        [
            str(cli),
            "--project",
            str(project),
            "--export-json",
            str(metadata),
            "--export-profile",
            profile,
            "--export-scene-gltf",
            str(glb),
        ],
        environment,
    )
    if "completed successfully" not in result.stdout:
        raise AssertionError(f"{profile} engine fixture success marker is missing")
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    if payload.get("profile") != profile:
        raise AssertionError(f"{profile} metadata profile is missing")
    sprites = payload.get("sprites")
    expected_schema = f"neoeng-d-trace-{profile}-sprite"
    if not sprites or sprites[0].get("schema") != expected_schema:
        raise AssertionError(f"{profile} metadata schema is invalid")
    if glb.read_bytes()[:4] != b"glTF":
        raise AssertionError(f"{profile} GLB output has an invalid magic value")


def validate_bundle(
    bundle: Path,
    output: Path,
    fixture: Path,
) -> dict[str, object]:
    cli = bundle / "NeoEng-D-Trace-CLI.exe"
    gui = bundle / "NeoEng-D-Trace.exe"
    if not cli.is_file() or not gui.is_file():
        raise FileNotFoundError("portable bundle is missing GUI or CLI executable")
    if not fixture.is_file():
        raise FileNotFoundError(f"release smoke fixture does not exist: {fixture}")

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-release-state-") as state:
        environment = os.environ.copy()
        environment["LOCALAPPDATA"] = state
        environment["QT_QPA_PLATFORM"] = "offscreen"

        version = run_checked([str(cli), "--version"], environment)
        if APP_VERSION not in version.stdout:
            raise AssertionError(f"unexpected version output: {version.stdout!r}")

        project = output / "smoke.ndtproj"
        metadata = output / "smoke.json"
        glb = output / "smoke.glb"
        headless = run_checked(
            [
                str(cli),
                "--headless",
                "--project",
                str(fixture),
                "--save-project",
                str(project),
                "--export-json",
                str(metadata),
                "--export-scene-gltf",
                str(glb),
            ],
            environment,
        )
        if "completed successfully" not in headless.stdout:
            raise AssertionError("headless success marker is missing")
        if not project.is_file() or not metadata.is_file() or not glb.is_file():
            raise AssertionError("headless smoke outputs are incomplete")
        if glb.read_bytes()[:4] != b"glTF":
            raise AssertionError("headless GLB output has an invalid magic value")
        json.loads(project.read_text(encoding="utf-8"))
        json.loads(metadata.read_text(encoding="utf-8"))

        for profile in ("godot", "unity"):
            _generate_engine_fixture(
                cli,
                fixture,
                output / f"engine-{profile}",
                profile,
                environment,
            )

        validation_log = output / "gui-validation.jsonl"
        run_checked(
            [
                str(gui),
                "--smoke-test-gui",
                "--validation-log",
                str(validation_log),
            ],
            environment,
            timeout=90,
        )
        rows = [
            json.loads(line)
            for line in validation_log.read_text(encoding="utf-8").splitlines()
        ]
        summary = rows[-1]
        if summary["event"] != "session.summary" or summary["status"] != "SUCCESS":
            raise AssertionError(f"GUI validation did not succeed: {summary}")
        state_configs = list(Path(state).rglob("config.json"))
        if len(state_configs) != 1:
            raise AssertionError(
                f"expected one user-state config, found {len(state_configs)}"
            )
        if (bundle / "config.json").exists():
            raise AssertionError("portable runtime wrote config inside its bundle")

    report = {
        "schema_version": 1,
        "status": "SUCCESS",
        "version": APP_VERSION,
        "checks": [
            "cli-version",
            "versioned-project-input",
            "headless-project",
            "headless-json",
            "headless-glb",
            "godot-profile-json",
            "godot-release-glb",
            "unity-profile-json",
            "unity-release-glb",
            "gui-open-close",
            "user-state-directory",
        ],
        "outputs": {
            path.relative_to(output).as_posix(): {
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    report_path = output / "portable-smoke-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    validate_bundle(
        args.bundle.resolve(),
        args.output.resolve(),
        args.fixture.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
