"""Run the fail-closed reproducibility audit for runtime streaming."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

from src.runtime.scene_runtime import RuntimeHost
from src.runtime.streaming import (
    StreamingDocumentV1,
    StreamingRuntime,
    StreamingSourceBindingRecord,
    StreamingState,
    StreamingValidationError,
    load_streaming_runtime_export,
    load_streaming_runtime_export_bytes,
    save_streaming_runtime_export,
    serialize_streaming_runtime_export,
    verify_streaming_source_binding,
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


def _asset(
    asset_id: str, path: str, payload: bytes, priority: int = 0
) -> dict[str, Any]:
    return {
        "id": asset_id,
        "path": path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "priority": priority,
    }


def _document(
    *assets: dict[str, Any], max_cache_bytes: int = 64, max_pending: int = 4
) -> StreamingDocumentV1:
    return StreamingDocumentV1.model_validate(
        {
            "source": {"sha256": hashlib.sha256(b"scenario-runtime").hexdigest()},
            "limits": {
                "max_cache_bytes": max_cache_bytes,
                "max_asset_bytes": min(64, max_cache_bytes),
                "max_pending": max_pending,
                "max_events_per_poll": 32,
            },
            "assets": list(assets),
        },
        strict=True,
    )


def _wait_for(
    runtime: StreamingRuntime,
    asset_id: str,
    state: StreamingState,
    *,
    timeout: float = 5.0,
) -> list[Any]:
    deadline = time.monotonic() + timeout
    events: list[Any] = []
    while time.monotonic() < deadline:
        events.extend(runtime.poll())
        if any(event.asset_id == asset_id and event.state is state for event in events):
            return events
        time.sleep(0.005)
    raise AssertionError(f"timeout waiting for {asset_id}:{state.value}")


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
        "canonical_sidecar_roundtrip_and_hash": False,
        "source_binding_is_hash_bound": False,
        "real_async_load_and_payload_identity": False,
        "priority_and_pending_limit_are_deterministic": False,
        "cancellation_is_observable_and_recoverable": False,
        "cache_eviction_is_safe_and_deterministic": False,
        "hash_failure_and_explicit_retry_recover": False,
        "cache_budget_failure_is_explicit_and_recoverable": False,
        "atomic_persistence_preserves_previous_bytes": False,
        "contract_limits_are_fail_closed": False,
        "runtime_host_advertises_capability": False,
        "privacy": False,
    }

    with tempfile.TemporaryDirectory(prefix="neoeng-stage7-streaming-") as temp:
        root = Path(temp)
        raw_a = b"asset-a"
        raw_b = b"asset-b"
        raw_c = b"asset-c"
        for name, payload in (("a.bin", raw_a), ("b.bin", raw_b), ("c.bin", raw_c)):
            (root / name).write_bytes(payload)

        document = _document(
            _asset("a", "a.bin", raw_a, priority=1),
            _asset("b", "b.bin", raw_b, priority=10),
            _asset("c", "c.bin", raw_c, priority=5),
        )
        raw = serialize_streaming_runtime_export(document)
        checks["canonical_sidecar_roundtrip_and_hash"] = (
            load_streaming_runtime_export_bytes(raw) == document
            and raw.endswith(b"\n")
            and hashlib.sha256(raw).hexdigest()
            == hashlib.sha256(serialize_streaming_runtime_export(document)).hexdigest()
        )

        bound = document.model_copy(
            update={
                "source": StreamingSourceBindingRecord(
                    sha256=hashlib.sha256(b"source").hexdigest()
                )
            }
        )
        try:
            verify_streaming_source_binding(bound, b"source")
            verify_streaming_source_binding(bound, b"different-source")
        except StreamingValidationError:
            checks["source_binding_is_hash_bound"] = True

        with StreamingRuntime(workers=2) as runtime:
            runtime.load_manifest(document.model_dump(mode="json"))
            runtime.start(root)
            request_a = runtime.request("a")
            ready_a = _wait_for(runtime, "a", StreamingState.READY)
            checks["real_async_load_and_payload_identity"] = (
                any(event.request_id == request_a.request_id for event in ready_a)
                and runtime.get("a") == raw_a
            )
            runtime.release(request_a)

        priority_document = _document(
            _asset("low", "a.bin", raw_a, priority=1),
            _asset("high", "b.bin", raw_b, priority=20),
            max_pending=1,
        )
        with StreamingRuntime(workers=2) as runtime:
            runtime.load_manifest(priority_document.model_dump(mode="json"))
            runtime.start(root)
            low_request = runtime.request("low")
            high_request = runtime.request("high")
            events: list[Any] = []
            events.extend(_wait_for(runtime, "high", StreamingState.READY))
            events.extend(_wait_for(runtime, "low", StreamingState.READY))
            ready_order = [
                event.asset_id
                for event in events
                if event.state is StreamingState.READY
            ]
            checks["priority_and_pending_limit_are_deterministic"] = (
                ready_order == ["high", "low"]
                and high_request.request_id != low_request.request_id
            )
            runtime.release(low_request)
            runtime.release(high_request)

        cancel_document = _document(_asset("cancel", "a.bin", raw_a))
        with StreamingRuntime() as runtime:
            runtime.load_manifest(cancel_document.model_dump(mode="json"))
            runtime.start(root)
            cancelled = runtime.request("cancel")
            runtime.cancel(cancelled)
            cancel_events = runtime.poll()
            recovered = runtime.request("cancel")
            recovered_events = _wait_for(runtime, "cancel", StreamingState.READY)
            checks["cancellation_is_observable_and_recoverable"] = any(
                event.request_id == cancelled.request_id
                and event.state is StreamingState.CANCELLED
                for event in cancel_events
            ) and any(
                event.request_id == recovered.request_id for event in recovered_events
            )

        cache_document = _document(
            _asset("a", "a.bin", raw_a),
            _asset("b", "b.bin", raw_b),
            _asset("c", "c.bin", raw_c),
            max_cache_bytes=len(raw_a) + len(raw_b),
        )
        with StreamingRuntime() as runtime:
            runtime.load_manifest(cache_document.model_dump(mode="json"))
            runtime.start(root)
            first = runtime.request("a")
            _wait_for(runtime, "a", StreamingState.READY)
            runtime.release(first)
            second = runtime.request("b")
            _wait_for(runtime, "b", StreamingState.READY)
            runtime.release(second)
            runtime.request("c")
            cache_events = _wait_for(runtime, "c", StreamingState.READY)
            checks["cache_eviction_is_safe_and_deterministic"] = (
                any(
                    event.asset_id == "a" and event.state is StreamingState.EVICTED
                    for event in cache_events
                )
                and runtime.get("b") == raw_b
            )

        mismatch_path = root / "mismatch.bin"
        mismatch_path.write_bytes(b"wrong")
        mismatch_document = _document(_asset("mismatch", "mismatch.bin", b"right"))
        with StreamingRuntime() as runtime:
            runtime.load_manifest(mismatch_document.model_dump(mode="json"))
            runtime.start(root)
            failed_request = runtime.request("mismatch")
            failed_events = _wait_for(runtime, "mismatch", StreamingState.FAILED)
            mismatch_path.write_bytes(b"right")
            runtime.release(failed_request)
            runtime.retry("mismatch")
            recovered = runtime.request("mismatch")
            recovered_events = _wait_for(runtime, "mismatch", StreamingState.READY)
            checks["hash_failure_and_explicit_retry_recover"] = any(
                event.state is StreamingState.FAILED for event in failed_events
            ) and any(
                event.request_id == recovered.request_id for event in recovered_events
            )

        budget_document = _document(
            _asset("a", "a.bin", raw_a),
            _asset("b", "b.bin", raw_b),
            max_cache_bytes=len(raw_a),
        )
        with StreamingRuntime() as runtime:
            runtime.load_manifest(budget_document.model_dump(mode="json"))
            runtime.start(root)
            held = runtime.request("a")
            _wait_for(runtime, "a", StreamingState.READY)
            blocked = runtime.request("b")
            blocked_events = _wait_for(runtime, "b", StreamingState.FAILED)
            runtime.release(held)
            runtime.release(blocked)
            runtime.retry("b")
            recovered = runtime.request("b")
            recovered_events = _wait_for(runtime, "b", StreamingState.READY)
            checks["cache_budget_failure_is_explicit_and_recoverable"] = any(
                event.state is StreamingState.FAILED
                and "cache budget" in (event.error or "")
                for event in blocked_events
            ) and any(
                event.request_id == recovered.request_id for event in recovered_events
            )

        destination = root / "streaming.json"
        save_streaming_runtime_export(document, destination)
        previous_bytes = destination.read_bytes()
        invalid = document.model_dump(mode="json")
        invalid["assets"][0]["unexpected"] = True
        try:
            save_streaming_runtime_export(
                invalid, destination  # type: ignore[arg-type]
            )
        except StreamingValidationError:
            checks["atomic_persistence_preserves_previous_bytes"] = (
                load_streaming_runtime_export(destination) == document
                and destination.read_bytes() == previous_bytes
            )

        try:
            _document(_asset("too-large", "a.bin", raw_a), max_cache_bytes=1)
        except ValueError:
            checks["contract_limits_are_fail_closed"] = True
        checks["runtime_host_advertises_capability"] = (
            "runtime.streaming" in RuntimeHost().supported_capabilities
        )

        write_json_lf(root / "streaming-sidecar.json", json.loads(raw.decode("utf-8")))
        leaks = _privacy_leaks(root)
        checks["privacy"] = not leaks
        report = {
            "schema_version": 1,
            "stage": "runtime-streaming-phase7",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "source": source,
            "environment": {"platform": platform.platform(), "python": sys.version},
            "commands": [
                "python scripts/audit_runtime_streaming_phase7.py "
                "--output <new-directory>",
                "python -m pytest -q tests/test_stage7_runtime_streaming.py",
                "python -m pytest --cov=src --cov-branch --cov-fail-under=90",
            ],
            "checks": checks,
            "contract": {
                "format_id": document.format_id,
                "schema_version": document.schema_version,
                "algorithm_version": document.algorithm_version,
                "document_sha256": hashlib.sha256(raw).hexdigest(),
                "serialized_bytes": len(raw),
                "asset_count": len(document.assets),
                "limits": document.limits.model_dump(mode="json"),
            },
            "privacy_leaks": leaks,
            "limitations": [
                "The implementation loads real local files under a constrained root;"
                " it does not provide engine-specific GPU streaming.",
                "Memory limits are logical byte budgets; VRAM, driver-specific FPS"
                " and engine residency remain outside this phase.",
                "The phase is not approved until tracked-byte validation, full"
                " repository gates, CI and post-merge validation pass.",
            ],
        }
        if (
            len(json.dumps(report, ensure_ascii=False).encode("utf-8"))
            > MAX_REPORT_BYTES
        ):
            raise ValueError("streaming audit report exceeds the report size limit")
        output.mkdir(parents=True)
        write_json_lf(output / "stage7-runtime-streaming-report.json", report)
        write_json_lf(
            output / "streaming-sidecar.json", json.loads(raw.decode("utf-8"))
        )

    write_json_lf(
        output / "artifact-index.json",
        {
            "schema_version": 1,
            "stage": "runtime-streaming-phase7",
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
        print(f"STAGE7=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]}, sort_keys=True
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
