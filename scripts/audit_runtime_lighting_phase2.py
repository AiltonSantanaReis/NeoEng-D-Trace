"""Generate reproducible evidence for runtime lighting/materials phase 2.

The auditor is fail-closed and records the clean source commit before writing
an output directory outside the repository. It does not change thresholds,
ignore failed commands or claim GPU/engine rendering support.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
FOCUSED_TESTS = (
    "tests/test_stage1_runtime_base.py",
    "tests/test_stage2_runtime_lighting.py",
    "tests/test_stage2_runtime_lighting_hardening.py",
    "tests/test_stage4b4_scenario_export.py",
    "tests/test_scenario_schema_io.py",
)


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _run(label: str, args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    command = " ".join(args[1:]) if args and args[0] == sys.executable else label
    sanitized_root = str(ROOT)
    return {
        "label": label,
        "command": command,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout.replace(sanitized_root, "<repo>"),
        "stderr": result.stderr.replace(sanitized_root, "<repo>"),
    }


def _files_index(output: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "artifact-index.json"
    }


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {output}")
    source = _source_state()
    output.mkdir(parents=True)
    commands = [
        (
            "focused_pytest",
            [sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS, "--tb=short"],
        ),
        ("full_pytest", [sys.executable, "-m", "pytest", "-q", "--tb=short"]),
        (
            "black_check",
            [
                sys.executable,
                "-m",
                "black",
                "--check",
                "src/runtime",
                *FOCUSED_TESTS,
                "scripts/audit_runtime_lighting_phase2.py",
            ],
        ),
        (
            "flake8",
            [
                sys.executable,
                "-m",
                "flake8",
                "src/runtime",
                *FOCUSED_TESTS,
                "scripts/audit_runtime_lighting_phase2.py",
            ],
        ),
        ("mypy", [sys.executable, "-m", "mypy", "src/runtime"]),
        (
            "py_compile",
            [
                sys.executable,
                "-m",
                "py_compile",
                "src/runtime/lighting.py",
                "src/runtime/scene_runtime.py",
                "src/runtime/__init__.py",
                *FOCUSED_TESTS,
                "scripts/audit_runtime_lighting_phase2.py",
            ],
        ),
        (
            "baseline_integrity",
            [sys.executable, "tools/baseline_integrity.py", "--verify", "--git-blob"],
        ),
        (
            "evidence_integrity",
            [
                sys.executable,
                "tools/evidence_integrity.py",
                "--require-tracked",
                "--git-blob",
            ],
        ),
        ("git_diff_check", ["git", "diff", "--check"]),
    ]
    results: list[dict[str, Any]] = []
    for label, args in commands:
        result = _run(label, args)
        results.append(result)
        (output / f"{label}.log").write_text(
            result["stdout"] + result["stderr"],
            encoding="utf-8",
            newline="\n",
        )
    checks = {result["label"]: result["passed"] for result in results}
    report = {
        "schema_version": 1,
        "stage": "runtime-lighting-materials-phase2",
        "status": (
            "PASS" if source["worktree_clean"] and all(checks.values()) else "FAIL"
        ),
        "source": source,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "checks": checks,
        "results": [
            {
                "label": result["label"],
                "command": result["command"],
                "returncode": result["returncode"],
                "passed": result["passed"],
            }
            for result in results
        ],
        "contract": {
            "lighting_format_id": "neoeng-d-trace-runtime-lighting",
            "lighting_schema_version": 1,
            "lighting_api_version": 1,
            "source_format_id": "neoeng-d-trace-scenario-runtime",
            "source_schema_version": 1,
            "supported_kinds": ["point", "directional", "spot"],
            "material_modes": ["lit", "unlit"],
            "fallback": "unlit material or explicit incompatible capability decision",
        },
        "limitations": [
            (
                "Preview is a deterministic structural colour evaluation, "
                "not GPU rasterization."
            ),
            (
                "This phase does not implement shaders, particles, post-processing, "
                "triggers or streaming."
            ),
            (
                "Hardware-specific GPU, VRAM, driver and FPS behaviour remains "
                "outside this portable gate."
            ),
            "Godot and Unity runtime reproduction belongs to the later adapter phase.",
        ],
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    _write_json(output / "runtime-lighting-report.json", report)
    _write_json(
        output / "artifact-index.json",
        {"schema_version": 1, "files": _files_index(output)},
    )
    return report


def main(argv: Iterable[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if len(values) != 2 or values[0] != "--output":
        print("usage: audit_runtime_lighting_phase2.py --output <new-directory>")
        return 2
    try:
        report = run(Path(values[1]))
    except Exception as exc:
        print(f"RUNTIME_LIGHTING_PHASE2=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]}, sort_keys=True
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
