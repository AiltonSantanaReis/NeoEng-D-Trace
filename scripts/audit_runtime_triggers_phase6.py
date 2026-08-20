"""Run the fail-closed reproducibility audit for runtime triggers."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from src.persistence.project_schema import Point3Record
from src.runtime.scene_runtime import RuntimeCancellationToken, RuntimeHost
from src.runtime.triggers import (
    TriggerCancellationError,
    TriggerConditionRecord,
    TriggerDocumentV1,
    TriggerEventRecord,
    TriggerExecutionError,
    TriggerObservation,
    TriggerRuntime,
    TriggerSourceBindingRecord,
    TriggerValidationError,
    TriggerZoneRecord,
    build_trigger_runtime_export,
    load_trigger_runtime_export,
    load_trigger_runtime_export_bytes,
    save_trigger_runtime_export,
    serialize_trigger_replay,
    serialize_trigger_runtime_export,
    verify_trigger_source_binding,
)
from tools.evidence_integrity import digest_path, write_json_lf

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_BYTES = 2_000_000
HOST_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|home)[\\/]|/(?:Users|home)/|\\\\[^\\/]+[\\/])"
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


def _point(x: float, y: float = 0.0, z: float = 0.0) -> Point3Record:
    return Point3Record(x=x, y=y, z=z)


def _document() -> TriggerDocumentV1:
    return TriggerDocumentV1(
        source=TriggerSourceBindingRecord(sha256="a" * 64),
        fixed_dt=1.0 / 60.0,
        max_substeps=4,
        events=[
            TriggerEventRecord(id="enter", payload={"kind": "entered"}),
            TriggerEventRecord(id="stay", payload={"kind": "stayed"}),
            TriggerEventRecord(id="exit", payload={"kind": "exited"}),
            TriggerEventRecord(id="disabled", enabled=False),
        ],
        zones=[
            TriggerZoneRecord(
                id="high",
                priority=20,
                center=_point(0.0),
                size=_point(10.0, 10.0, 10.0),
                conditions=[
                    TriggerConditionRecord(key="mode", operator="eq", value="active")
                ],
                enter_event_id="enter",
                stay_event_id="stay",
                exit_event_id="exit",
            ),
            TriggerZoneRecord(
                id="low",
                priority=10,
                center=_point(0.0),
                size=_point(20.0, 20.0, 20.0),
                enter_event_id="enter",
            ),
            TriggerZoneRecord(
                id="disabled-zone",
                enabled=False,
                center=_point(0.0),
                size=_point(30.0, 30.0, 30.0),
                enter_event_id="disabled",
            ),
        ],
    )


def _observation(x: float, mode: str = "active") -> TriggerObservation:
    return TriggerObservation("actor", _point(x), {"mode": mode})


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
        "source_binding_is_hash_bound": False,
        "priority_order_and_transitions_are_deterministic": False,
        "conditions_and_disabled_events_are_explicit": False,
        "missing_observation_emits_exit": False,
        "cancellation_preserves_state": False,
        "fixed_step_limits_preserve_state": False,
        "pause_resume_is_explicit": False,
        "replay_is_deterministic_and_bound": False,
        "atomic_persistence_preserves_previous_bytes": False,
        "runtime_host_advertises_capability": False,
        "privacy": False,
    }

    with tempfile.TemporaryDirectory(prefix="neoeng-stage6-triggers-") as temp:
        staging = Path(temp)
        document = _document()
        raw = serialize_trigger_runtime_export(document)
        checks["canonical_sidecar_roundtrip"] = load_trigger_runtime_export_bytes(
            raw
        ) == document and build_trigger_runtime_export(document) == json.loads(
            raw.decode("utf-8")
        )

        bound = document.model_copy(
            update={
                "source": TriggerSourceBindingRecord(
                    sha256=hashlib.sha256(b"source").hexdigest()
                )
            }
        )
        try:
            verify_trigger_source_binding(bound, b"source")
            verify_trigger_source_binding(bound, b"different-source")
        except TriggerValidationError:
            checks["source_binding_is_hash_bound"] = True

        runtime = TriggerRuntime(document)
        runtime.start()
        first = runtime.advance(1.0 / 60.0, [_observation(0.0)])
        second = runtime.advance(1.0 / 60.0, [_observation(0.0)])
        checks["priority_order_and_transitions_are_deterministic"] = [
            (event.zone_id, event.transition) for event in first.events
        ] == [("high", "enter"), ("low", "enter")] and [
            (event.zone_id, event.transition) for event in second.events
        ] == [
            ("high", "stay")
        ]

        inactive = TriggerRuntime(document)
        inactive.start()
        inactive_result = inactive.advance(
            1.0 / 60.0, [_observation(0.0, mode="inactive")]
        )
        checks["conditions_and_disabled_events_are_explicit"] = [
            (event.zone_id, event.event_id) for event in inactive_result.events
        ] == [("low", "enter")]

        missing_result = runtime.advance(1.0 / 60.0, [])
        checks["missing_observation_emits_exit"] = [
            (event.zone_id, event.transition) for event in missing_result.events
        ] == [("high", "exit")] and runtime.snapshot.active_pairs == ()

        cancellation_runtime = TriggerRuntime(document)
        cancellation_runtime.start()
        cancellation_runtime.advance(1.0 / 60.0, [_observation(0.0)])
        before = cancellation_runtime.snapshot
        token = RuntimeCancellationToken()
        token.cancel()
        try:
            cancellation_runtime.advance(1.0 / 60.0, [_observation(20.0)], token)
        except TriggerCancellationError:
            checks["cancellation_preserves_state"] = (
                cancellation_runtime.snapshot == before
            )

        limit_runtime = TriggerRuntime(document)
        limit_runtime.start()
        before = limit_runtime.snapshot
        try:
            limit_runtime.advance(5.0 / 60.0, [_observation(0.0)])
        except TriggerExecutionError:
            checks["fixed_step_limits_preserve_state"] = (
                limit_runtime.snapshot == before
            )

        paused = TriggerRuntime(document)
        paused.start()
        paused_snapshot = paused.pause()
        try:
            paused.advance(1.0 / 60.0, [_observation(0.0)])
        except TriggerExecutionError:
            paused.resume()
            checks["pause_resume_is_explicit"] = (
                paused.snapshot.phase == "running" and paused_snapshot.phase == "paused"
            )

        replay_runtime = TriggerRuntime(document)
        replay_runtime.start()
        replay_runtime.start_recording()
        first_replay_step = replay_runtime.advance(1.0 / 60.0, [_observation(0.0)])
        second_replay_step = replay_runtime.advance(1.0 / 60.0, [_observation(20.0)])
        expected_replay_events = first_replay_step.events + second_replay_step.events
        tape = replay_runtime.stop_recording()
        replayed = TriggerRuntime.replay(document, tape)
        try:
            TriggerRuntime.replay(document, replace(tape, document_sha256="b" * 64))
        except TriggerExecutionError:
            checks["replay_is_deterministic_and_bound"] = (
                replayed == expected_replay_events
            )
        replay_path = staging / "trigger-replay.json"
        replay_path.write_bytes(serialize_trigger_replay(tape))

        destination = staging / "triggers.json"
        save_trigger_runtime_export(document, destination)
        previous_bytes = destination.read_bytes()
        invalid_payload = document.model_dump(mode="json")
        invalid_payload["zones"][0]["enter_event_id"] = "missing"
        try:
            save_trigger_runtime_export(invalid_payload, destination)
        except TriggerValidationError:
            checks["atomic_persistence_preserves_previous_bytes"] = (
                load_trigger_runtime_export(destination) == document
                and destination.read_bytes() == previous_bytes
            )

        checks["runtime_host_advertises_capability"] = (
            "runtime.triggers" in RuntimeHost().supported_capabilities
        )
        write_json_lf(staging / "trigger-sidecar.json", json.loads(raw))
        checks["privacy"] = not _privacy_leaks(staging)
        report = {
            "schema_version": 1,
            "stage": "runtime-triggers-phase6",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "source": source,
            "environment": {"platform": platform.platform(), "python": sys.version},
            "backend": {
                "native": "deterministic-fixed-step-cpu",
                "engine_adapters": [],
            },
            "commands": [
                (
                    "python scripts/audit_runtime_triggers_phase6.py "
                    "--output <new-directory>"
                ),
                "python -m pytest -q tests/test_stage6_runtime_triggers.py",
                "python -m pytest --cov=src --cov-branch --cov-fail-under=90",
            ],
            "checks": checks,
            "contract": {
                "format_id": document.format_id,
                "schema_version": document.schema_version,
                "algorithm_version": document.algorithm_version,
                "document_sha256": hashlib.sha256(raw).hexdigest(),
                "serialized_bytes": len(raw),
                "zone_count": len(document.zones),
                "event_count": len(document.events),
                "fixed_dt": document.fixed_dt,
                "max_substeps": document.max_substeps,
            },
            "privacy_leaks": _privacy_leaks(staging),
            "limitations": [
                (
                    "The implemented runtime is a deterministic CPU trigger "
                    "dispatcher, "
                    "not a graphical engine or physics engine."
                ),
                "Godot and Unity trigger adapters are not implemented in this phase.",
                (
                    "Network delivery, streaming and engine-specific frame scheduling "
                    "remain outside this phase."
                ),
                (
                    "The phase is not approved until full repository gates, "
                    "tracked-byte "
                    "validation, CI and post-merge validation pass."
                ),
            ],
        }
        report_path = staging / "stage6-runtime-triggers-report.json"
        write_json_lf(report_path, report)
        if report_path.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError("trigger audit report exceeds the report size limit")
        output.mkdir(parents=True)
        for path in staging.iterdir():
            (output / path.name).write_bytes(path.read_bytes())

    write_json_lf(
        output / "artifact-index.json",
        {
            "schema_version": 1,
            "stage": "runtime-triggers-phase6",
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
        print(f"RUNTIME_TRIGGERS_PHASE6=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]}, sort_keys=True
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
