"""Execute smoke tests against a portable Windows release bundle."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

from src.core.app_identity import APP_VERSION


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
            "gui-open-close",
            "user-state-directory",
        ],
        "outputs": {
            path.name: {"size": path.stat().st_size}
            for path in sorted(output.iterdir())
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
