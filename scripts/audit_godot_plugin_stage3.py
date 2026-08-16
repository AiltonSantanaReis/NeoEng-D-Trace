"""Build and execute a real Godot project containing the source-only addon."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADDON_SOURCE = ROOT / "integrations" / "godot" / "addons" / "neoeng_d_trace"
MANIFEST_SOURCE = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / "integration-manifest"
    / "godot.integration.json"
)
IMAGE_SOURCE = (
    ROOT / "docs" / "evidence" / "artifacts" / "integration-manifest" / "source.png"
)
VALIDATOR_SOURCE = ROOT / "tools" / "godot_plugin_stage3_validator.gd"


def _run(executable: str, arguments: list[str], workspace: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [executable, *arguments],
        cwd=workspace,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    output = re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", completed.stdout)
    portable_arguments = [
        re.sub(r"[A-Za-z]:\\[^\r\n]+", "<local-path>", argument)
        for argument in arguments
    ]
    return {
        "executable": Path(executable).name,
        "arguments": portable_arguments,
        "returncode": completed.returncode,
        "output": output,
    }


def _prepare(workspace: Path) -> None:
    addon_destination = workspace / "addons" / "neoeng_d_trace"
    addon_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ADDON_SOURCE, addon_destination)
    generated = workspace / "NeoEngGenerated"
    generated.mkdir()
    shutil.copy2(MANIFEST_SOURCE, generated / "hero.ndt.integration.json")
    shutil.copy2(IMAGE_SOURCE, generated / "source.png")
    shutil.copy2(VALIDATOR_SOURCE, workspace / "validate_stage3.gd")
    project_text = (
        '[application]\nconfig/name="NeoEngDTracePluginStage3"\n'
        "[editor_plugins]\n"
        'enabled=PackedStringArray("res://addons/neoeng_d_trace/plugin.cfg")\n'
    )
    (workspace / "project.godot").write_text(project_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.work_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="neoeng-godot-plugin-stage3-")
        workspace = Path(temporary.name)
    else:
        workspace = args.work_dir.resolve()
        workspace.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": 3,
        "status": "FAILED",
        "plugin": "neoeng_d_trace",
        "source_only": True,
    }
    try:
        _prepare(workspace)
        commands = [
            _run(
                args.executable,
                ["--headless", "--editor", "--path", str(workspace), "--import"],
                workspace,
            ),
            _run(
                args.executable,
                [
                    "--headless",
                    "--path",
                    str(workspace),
                    "--script",
                    "validate_stage3.gd",
                ],
                workspace,
            ),
        ]
        report["commands"] = commands
        if any(command["returncode"] != 0 for command in commands):
            raise RuntimeError("Godot stage-three command failed")
        if "NATIVE_PLUGIN_STAGE3=SUCCESS" not in commands[-1]["output"]:
            raise RuntimeError("stage-three success marker missing")
        report["status"] = "SUCCESS"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return 0
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
