"""Run the fail-closed reproducibility audit for runtime particle phase 4."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Iterable

from src.persistence.project_schema import Point3Record
from src.runtime.particles import (
    PARTICLE_ALGORITHM_VERSION,
    PARTICLES_FORMAT_ID,
    ParticleDocumentV1,
    ParticleEmitterRecord,
    ParticleFormatError,
    ParticleRuntimeError,
    ParticleSimulation,
    ParticleSimulationError,
    ParticleSourceBindingRecord,
    load_particle_runtime_export,
    load_particle_runtime_export_bytes,
    particle_runtime_export_sha256,
    replay_particle_simulation,
    save_particle_runtime_export,
    serialize_particle_runtime_export,
    validate_particle_runtime_export,
)
from tools.evidence_integrity import digest_path, write_json_lf

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_BYTES = 2_000_000
HOST_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|home)[\\/]|/(?:Users|home)/|\\\\[^\\/]+[\\/])"
)
TRANSIENT_KEYS = {
    "particles",
    "simulation_time",
    "rng_state",
    "accumulator",
    "tick_index",
    "phase",
}


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


def _document(
    *,
    seed: int = 7,
    emission_rate: float = 10.0,
    burst_count: int = 1,
) -> ParticleDocumentV1:
    return ParticleDocumentV1(
        source=ParticleSourceBindingRecord(sha256="a" * 64),
        fixed_dt=0.1,
        max_substeps=4,
        emitters=[
            ParticleEmitterRecord(
                id="smoke",
                seed=seed,
                initial_velocity=Point3Record(x=1.0, y=2.0, z=0.0),
                velocity_spread=Point3Record(x=0.25, y=0.5, z=0.0),
                acceleration=Point3Record(x=0.0, y=-1.0, z=0.0),
                emission_rate=emission_rate,
                lifetime=0.5,
                max_particles=4,
                burst_count=burst_count,
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


def _rejected(
    action: Callable[[], Any],
    expected: tuple[type[BaseException], ...],
) -> bool:
    try:
        action()
    except expected:
        return True
    return False


def _write_report(output: Path, report: dict[str, Any]) -> None:
    path = output / "stage4-runtime-particles-report.json"
    write_json_lf(path, report)
    if path.stat().st_size > MAX_REPORT_BYTES:
        raise ValueError("particle audit report exceeds the report size limit")


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
        "authorial_state_excludes_transient_state": False,
        "fixed_update_is_deterministic": False,
        "seed_zero_is_preserved": False,
        "pause_preserves_state": False,
        "limits_are_enforced": False,
        "replay_is_hash_bound_and_reproducible": False,
        "atomic_persistence_preserves_previous_bytes": False,
        "privacy": False,
    }

    with tempfile.TemporaryDirectory(prefix="neoeng-stage4-particles-") as temp:
        staging = Path(temp)
        document = _document()
        raw = serialize_particle_runtime_export(document)
        checks["canonical_sidecar_roundtrip"] = (
            load_particle_runtime_export_bytes(raw) == document
        )
        checks["authorial_state_excludes_transient_state"] = not (
            set(json.loads(raw)) & TRANSIENT_KEYS
        )

        first = ParticleSimulation(document)
        second = ParticleSimulation(document)
        first.start()
        second.start()
        first.advance(0.05)
        second.advance(0.05)
        half_step = first.snapshot.tick_index == 0
        first.advance(0.05)
        second.advance(0.05)
        checks["fixed_update_is_deterministic"] = (
            half_step
            and first.snapshot.tick_index == 1
            and first.snapshot == second.snapshot
            and first.states() == second.states()
        )

        zero_seed = ParticleSimulation(_document(seed=0))
        one_seed = ParticleSimulation(_document(seed=1))
        zero_seed.start()
        one_seed.start()
        zero_seed.advance(0.1)
        one_seed.advance(0.1)
        checks["seed_zero_is_preserved"] = (
            zero_seed.snapshot.state_sha256 != one_seed.snapshot.state_sha256
        )

        paused = ParticleSimulation(_document(emission_rate=0.0))
        paused.start()
        paused.advance(0.1)
        before_pause = paused.snapshot
        paused.pause()
        paused_snapshot = paused.snapshot
        checks["pause_preserves_state"] = (
            paused_snapshot.phase == "paused"
            and paused_snapshot.tick_index == before_pause.tick_index
            and paused_snapshot.simulation_time == before_pause.simulation_time
            and paused_snapshot.state_sha256 == before_pause.state_sha256
            and _rejected(
                lambda: paused.advance(0.1),
                (ParticleSimulationError,),
            )
        )

        limited = ParticleSimulation(document)
        limited.start()
        limited.advance(0.4)
        payload = document.model_dump(mode="json")
        payload["emitters"][0]["max_particles"] = 100_001
        checks["limits_are_enforced"] = (
            limited.snapshot.particle_count <= 4
            and _rejected(
                lambda: limited.advance(0.5),
                (ParticleSimulationError,),
            )
            and _rejected(
                lambda: validate_particle_runtime_export(payload),
                (ParticleRuntimeError,),
            )
        )

        replay_source = ParticleSimulation(document)
        replay_source.start()
        replay_source.begin_replay_recording()
        replay_source.advance(0.1)
        replay_source.advance(0.2)
        tape = replay_source.finish_replay_recording()
        replayed = replay_particle_simulation(document, tape)
        checks["replay_is_hash_bound_and_reproducible"] = (
            replayed == replay_source.snapshot
            and tape.algorithm_version == PARTICLE_ALGORITHM_VERSION
            and tape.format_id == PARTICLES_FORMAT_ID
            and _rejected(
                lambda: replay_particle_simulation(_document(seed=99), tape),
                (ParticleSimulationError,),
            )
            and _rejected(
                lambda: replay_particle_simulation(
                    document, replace(tape, fixed_dt=0.2)
                ),
                (ParticleSimulationError,),
            )
        )

        destination = staging / "particles.json"
        save_particle_runtime_export(document, destination)
        previous_bytes = destination.read_bytes()
        invalid_payload = document.model_dump(mode="json")
        invalid_payload["emitters"][0]["unexpected"] = True
        checks["atomic_persistence_preserves_previous_bytes"] = (
            load_particle_runtime_export(destination) == document
            and _rejected(
                lambda: save_particle_runtime_export(invalid_payload, destination),
                (ParticleRuntimeError,),
            )
            and destination.read_bytes() == previous_bytes
            and _rejected(
                lambda: load_particle_runtime_export_bytes(
                    b'{"format_id":"x","format_id":"y"}'
                ),
                (ParticleFormatError,),
            )
        )

        write_json_lf(
            staging / "particle-sidecar.json",
            json.loads(raw.decode("utf-8")),
        )
        leaks = _privacy_leaks(staging)
        checks["privacy"] = not leaks
        report = {
            "schema_version": 1,
            "stage": "runtime-particles-phase4",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "source": source,
            "environment": {
                "platform": platform.platform(),
                "python": sys.version,
            },
            "commands": [
                (
                    "python scripts/audit_runtime_particles_phase4.py "
                    "--output <new-directory>"
                ),
                "python -m pytest -q tests/test_stage4_runtime_particles.py",
                (
                    "python -m pytest -q tests/test_stage1_runtime_base.py "
                    "tests/test_stage2_runtime_lighting.py "
                    "tests/test_stage3_runtime_shaders.py"
                ),
            ],
            "checks": checks,
            "contract": {
                "format_id": document.format_id,
                "schema_version": document.schema_version,
                "algorithm_version": document.algorithm_version,
                "document_sha256": particle_runtime_export_sha256(document),
                "serialized_bytes": len(raw),
                "fixed_dt": document.fixed_dt,
                "emitter_count": len(document.emitters),
                "max_particles": sum(
                    emitter.max_particles for emitter in document.emitters
                ),
                "replay_elapsed_requests": list(tape.elapsed_requests),
                "snapshot_state_sha256": replay_source.snapshot.state_sha256,
            },
            "privacy_leaks": leaks,
            "limitations": [
                (
                    "This is a deterministic structural/runtime audit, not GPU "
                    "rasterization."
                ),
                "Godot and Unity runtime execution is outside this phase.",
                (
                    "VRAM, driver-specific FPS and backend-specific rendering "
                    "remain untested."
                ),
                (
                    "The phase is not approved until full repository gates, "
                    "tracked-byte validation, CI and post-merge validation pass."
                ),
            ],
        }
        _write_report(staging, report)
        output.mkdir(parents=True)
        for path in staging.iterdir():
            (output / path.name).write_bytes(path.read_bytes())

    write_json_lf(
        output / "artifact-index.json",
        {
            "schema_version": 1,
            "stage": "runtime-particles-phase4",
            "files": _files_index(output),
        },
    )
    return report


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = run(args.output)
    except Exception as exc:
        print(f"RUNTIME_PARTICLES_PHASE4=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]}, sort_keys=True
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
