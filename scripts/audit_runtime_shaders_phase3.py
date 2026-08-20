"""Run the fail-closed real audit for runtime shader phase 3.

The audit uses the real Qt Shader Tools executable resolved from the current
Python environment. It validates the canonical sidecar, compiles both stages,
reproduces a rejected shader without replacing the previous binaries, and
writes only relative, hashable evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from src.runtime.shaders import (
    ShaderCompilationError,
    ShaderDocumentV1,
    ShaderMaterialRecord,
    ShaderProgramRecord,
    ShaderSourceBindingRecord,
    ShaderStageRecord,
    ShaderUniformRecord,
    compile_shader_program,
    load_shader_runtime_export_bytes,
    resolve_qt_qsb,
    save_shader_runtime_export,
    serialize_shader_runtime_export,
)
from tools.evidence_integrity import digest_path, write_json_lf

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_BYTES = 2_000_000
HOST_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|home)[\\/]|/(?:Users|home)/|\\\\[^\\/]+[\\/])"
)
VERTEX_SOURCE = """#version 440
layout(location = 0) in vec4 vertex;
void main() { gl_Position = vertex; }
"""
FRAGMENT_SOURCE = """#version 440
layout(location = 0) out vec4 fragColor;
void main() { fragColor = vec4(1.0); }
"""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _document(fragment: str = FRAGMENT_SOURCE) -> ShaderDocumentV1:
    return ShaderDocumentV1(
        source=ShaderSourceBindingRecord(sha256="a" * 64),
        programs=[
            ShaderProgramRecord(
                id="basic",
                stages=[
                    ShaderStageRecord(stage="vertex", source=VERTEX_SOURCE),
                    ShaderStageRecord(stage="fragment", source=fragment),
                ],
            )
        ],
        materials=[
            ShaderMaterialRecord(
                id="material-basic",
                program_id="basic",
                uniforms=[
                    ShaderUniformRecord(
                        name="tint",
                        kind="vec4",
                        default=[1.0, 1.0, 1.0, 1.0],
                    )
                ],
            )
        ],
    )


def _files_index(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): digest_path(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "artifact-index.json"
    }


def _privacy_leaks(root: Path) -> list[str]:
    leaks: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if HOST_PATH_RE.search(text) or str(ROOT).replace("\\", "/") in text:
            leaks.append(path.relative_to(root).as_posix())
    return leaks


def _write_report(output: Path, report: dict[str, Any]) -> None:
    write_json_lf(output / "stage3-runtime-shaders-report.json", report)
    if (
        output / "stage3-runtime-shaders-report.json"
    ).stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("shader audit report exceeds the report size limit")


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(
            f"output must be a new directory; refusing to overwrite: {output.name}"
        )
    source = _source_state()
    checks: dict[str, bool] = {
        "source_tree_clean": source["worktree_clean"],
        "canonical_sidecar_roundtrip": False,
        "real_qt_qsb_resolved": False,
        "both_stages_compiled": False,
        "invalid_stage_rejected_without_replacement": False,
        "privacy": False,
    }
    compiler_name = ""
    compilation: dict[str, Any] = {}
    failure_reproduction: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="neoeng-stage3-shader-") as temporary:
        staging = Path(temporary)
        compiled = staging / "compiled"
        document = _document()
        raw = serialize_shader_runtime_export(document)
        loaded = load_shader_runtime_export_bytes(raw)
        checks["canonical_sidecar_roundtrip"] = loaded == document
        compiler = resolve_qt_qsb()
        compiler_name = compiler.name
        checks["real_qt_qsb_resolved"] = compiler.is_file()
        report = compile_shader_program(document, "basic", compiled)
        checks["both_stages_compiled"] = report.status == "PASS" and {
            item.stage for item in report.stages
        } == {"vertex", "fragment"}
        compilation = {
            "status": report.status,
            "backend": report.backend,
            "program_id": report.program_id,
            "compiler": compiler.name,
            "stages": [
                {
                    "stage": item.stage,
                    "bytes": item.bytes,
                    "sha256": item.sha256,
                    "file": f"compiled/basic.{item.stage}.qsb",
                }
                for item in report.stages
            ],
        }
        previous = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(compiled.glob("*.qsb"))
        }
        try:
            compile_shader_program(
                _document("#version 440\nvoid main( {"), "basic", compiled
            )
        except ShaderCompilationError as exc:
            failure_reproduction = {
                "status": "EXPECTED_REJECTION",
                "error_type": type(exc).__name__,
                "message": str(exc)[:2000],
            }
        checks["invalid_stage_rejected_without_replacement"] = bool(
            failure_reproduction
        ) and previous == {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(compiled.glob("*.qsb"))
        }
        write_json_lf(staging / "shader-sidecar.json", json.loads(raw.decode("utf-8")))
        save_shader_runtime_export(document, staging / "shader-sidecar-copy.json")
        shutil.copytree(staging, output)

    leaks = _privacy_leaks(output)
    checks["privacy"] = not leaks
    final_report: dict[str, Any] = {
        "schema_version": 1,
        "stage": "3",
        "scope": "runtime-shaders",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "source": source,
        "environment": {"platform": platform.platform(), "python": sys.version},
        "backend": {"id": "qt-qsb", "compiler": compiler_name},
        "commands": [
            "python scripts/audit_runtime_shaders_phase3.py --output <output>",
            "python -m pytest --cov=src --cov-branch --cov-fail-under=90",
            "python tools/check_coverage_policy.py coverage.xml",
        ],
        "checks": checks,
        "compilation": compilation,
        "failure_reproduction": failure_reproduction,
        "limitations": [
            "The native backend in this phase is Qt Shader Tools (qsb).",
            (
                "Unsupported backends are rejected explicitly; no silent fallback "
                "is claimed."
            ),
            (
                "Particles, post-processing, triggers, streaming and engine runtime "
                "adapters remain future phases."
            ),
        ],
        "privacy_leaks": leaks,
    }
    _write_report(output, final_report)
    write_json_lf(
        output / "artifact-index.json",
        {"schema_version": 1, "stage": "3", "files": _files_index(output)},
    )
    if _privacy_leaks(output):
        final_report["status"] = "FAIL"
        final_report["checks"]["privacy"] = False
        final_report["privacy_leaks"] = _privacy_leaks(output)
        _write_report(output, final_report)
    return final_report


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = run(args.output)
    except Exception as exc:
        print(f"STAGE3_RUNTIME_SHADERS=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]}, sort_keys=True
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
