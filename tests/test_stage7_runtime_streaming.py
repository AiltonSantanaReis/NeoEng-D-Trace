"""Real-file, deterministic and negative coverage for runtime streaming."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from src.runtime.scene_runtime import CapabilityRequest, RuntimeHost
from src.runtime.streaming import (
    StreamingAssetRecord,
    StreamingDocumentV1,
    StreamingExecutionError,
    StreamingFormatError,
    StreamingLifecycleError,
    StreamingLimitsRecord,
    StreamingRuntime,
    StreamingSourceBindingRecord,
    StreamingState,
    StreamingValidationError,
    load_streaming_runtime_export,
    load_streaming_runtime_export_bytes,
    save_streaming_runtime_export,
    serialize_streaming_runtime_export,
    streaming_runtime_export_sha256,
    verify_streaming_source_binding,
)


def _source() -> StreamingSourceBindingRecord:
    return StreamingSourceBindingRecord(
        sha256=hashlib.sha256(b"scenario-runtime").hexdigest()
    )


def _asset(asset_id: str, path: str, payload: bytes, priority: int = 0) -> dict:
    return {
        "id": asset_id,
        "path": path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "priority": priority,
    }


def _document(*assets: dict, max_cache_bytes: int = 64) -> StreamingDocumentV1:
    return StreamingDocumentV1.model_validate(
        {
            "source": _source().model_dump(mode="json"),
            "limits": {
                "max_cache_bytes": max_cache_bytes,
                "max_asset_bytes": min(64, max_cache_bytes),
                "max_pending": 4,
                "max_events_per_poll": 32,
            },
            "assets": list(assets),
        },
        strict=True,
    )


def _wait(
    runtime: StreamingRuntime,
    expected: str,
    state: StreamingState | None = None,
    timeout: float = 3.0,
):
    deadline = time.monotonic() + timeout
    events = []
    while time.monotonic() < deadline:
        events.extend(runtime.poll())
        if any(
            event.asset_id == expected and (state is None or event.state is state)
            for event in events
        ):
            return events
        time.sleep(0.005)
    return events


def test_streaming_contract_is_canonical_hash_bound_and_round_trips(tmp_path: Path):
    payload = b"asset-bytes"
    document = _document(_asset("hero", "hero.bin", payload))
    raw = serialize_streaming_runtime_export(document)
    assert raw.endswith(b"\n")
    assert load_streaming_runtime_export_bytes(raw) == document
    assert streaming_runtime_export_sha256(document) == hashlib.sha256(raw).hexdigest()

    destination = tmp_path / "streaming.json"
    save_streaming_runtime_export(document, destination)
    assert destination.read_bytes() == raw
    verify_streaming_source_binding(document, b"scenario-runtime")


def test_streaming_reads_real_files_and_reports_ready(tmp_path: Path):
    payload = b"real-file-content"
    (tmp_path / "hero.bin").write_bytes(payload)
    document = _document(_asset("hero", "hero.bin", payload))
    with StreamingRuntime() as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)
        request = runtime.request("hero")
        events = _wait(runtime, "hero")
        assert any(event.request_id == request.request_id for event in events)
        assert any(event.state is StreamingState.READY for event in events)
        assert runtime.get("hero") == payload


def test_streaming_priority_is_stable_even_when_workers_complete_differently(
    tmp_path: Path,
):
    low = b"low"
    high = b"high"
    (tmp_path / "low.bin").write_bytes(low)
    (tmp_path / "high.bin").write_bytes(high)
    document = _document(
        _asset("low", "low.bin", low, priority=1),
        _asset("high", "high.bin", high, priority=20),
    )
    with StreamingRuntime(workers=2) as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)
        runtime.request("low")
        runtime.request("high")
        events = []
        deadline = time.monotonic() + 3.0
        while (
            len([event for event in events if event.state is StreamingState.READY]) < 2
        ):
            events.extend(runtime.poll())
            if time.monotonic() >= deadline:
                break
            time.sleep(0.005)
        ready = [
            event.asset_id for event in events if event.state is StreamingState.READY
        ]
        assert ready == ["high", "low"]


def test_streaming_cache_evicts_old_unreferenced_asset_deterministically(
    tmp_path: Path,
):
    first, second, third = b"111", b"222", b"333"
    for name, payload in (("a.bin", first), ("b.bin", second), ("c.bin", third)):
        (tmp_path / name).write_bytes(payload)
    document = _document(
        _asset("a", "a.bin", first),
        _asset("b", "b.bin", second),
        _asset("c", "c.bin", third),
        max_cache_bytes=6,
    )
    with StreamingRuntime() as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)
        first_request = runtime.request("a")
        _wait(runtime, "a")
        runtime.release(first_request)
        second_request = runtime.request("b")
        _wait(runtime, "b")
        runtime.release(second_request)
        runtime.request("c")
        events = _wait(runtime, "c")
        assert any(
            event.state is StreamingState.EVICTED and event.asset_id == "a"
            for event in events
        )
        assert runtime.snapshot.cache_bytes == 6
        assert runtime.get("b") == second


def test_streaming_hash_mismatch_is_failure_and_retry_is_explicit(tmp_path: Path):
    expected = b"expected"
    path = tmp_path / "asset.bin"
    path.write_bytes(b"wrong!__")
    document = _document(_asset("asset", "asset.bin", expected))
    with StreamingRuntime() as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)
        runtime.request("asset")
        events = _wait(runtime, "asset")
        failure = [event for event in events if event.state is StreamingState.FAILED]
        assert failure and "hash mismatch" in (failure[0].error or "")
        with pytest.raises(StreamingExecutionError):
            runtime.request("asset")
        path.write_bytes(expected)
        runtime.retry("asset")
        runtime.request("asset")
        events = _wait(runtime, "asset", StreamingState.READY)
        assert any(event.state is StreamingState.READY for event in events)


def test_streaming_cancel_preserves_cache_and_does_not_create_ready_data(
    tmp_path: Path,
):
    payload = b"cancel-me"
    (tmp_path / "asset.bin").write_bytes(payload)
    document = _document(_asset("asset", "asset.bin", payload))
    with StreamingRuntime() as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)
        request = runtime.request("asset")
        runtime.cancel(request)
        events = runtime.poll()
        assert runtime.snapshot.ready_assets == ()
        assert runtime.snapshot.cache_bytes == 0
        assert not any(event.state is StreamingState.READY for event in events)


def test_streaming_reactivates_cancelled_and_evicted_assets(tmp_path: Path):
    payload = b"reusable"
    (tmp_path / "asset.bin").write_bytes(payload)
    document = _document(_asset("asset", "asset.bin", payload))
    with StreamingRuntime() as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)

        cancelled = runtime.request("asset")
        runtime.cancel(cancelled)
        events = runtime.poll()
        assert any(
            event.asset_id == "asset" and event.state is StreamingState.CANCELLED
            for event in events
        )

        retry_request = runtime.request("asset")
        events = _wait(runtime, "asset", StreamingState.READY)
        assert any(event.request_id == retry_request.request_id for event in events)
        runtime.release(retry_request)
        runtime.evict("asset")

        reloaded = runtime.request("asset")
        events = _wait(runtime, "asset", StreamingState.READY)
        assert any(event.request_id == reloaded.request_id for event in events)


def test_streaming_cache_limit_is_failure_until_reference_is_released(
    tmp_path: Path,
):
    first, second = b"1111", b"2222"
    (tmp_path / "a.bin").write_bytes(first)
    (tmp_path / "b.bin").write_bytes(second)
    document = _document(
        _asset("a", "a.bin", first),
        _asset("b", "b.bin", second),
        max_cache_bytes=4,
    )
    with StreamingRuntime() as runtime:
        runtime.load_manifest(document.model_dump(mode="json"))
        runtime.start(tmp_path)
        first_request = runtime.request("a")
        _wait(runtime, "a", StreamingState.READY)
        second_request = runtime.request("b")
        failure_events = _wait(runtime, "b", StreamingState.FAILED)
        assert any("cache budget" in (event.error or "") for event in failure_events)
        runtime.release(first_request)
        runtime.release(second_request)
        runtime.retry("b")
        reloaded = runtime.request("b")
        ready_events = _wait(runtime, "b", StreamingState.READY)
        assert any(event.request_id == reloaded.request_id for event in ready_events)


def test_streaming_strict_limits_and_asset_fields_fail_closed():
    with pytest.raises(ValueError):
        StreamingLimitsRecord.model_validate({"max_cache_bytes": True}, strict=True)
    with pytest.raises(ValueError):
        StreamingLimitsRecord(max_cache_bytes=0)
    with pytest.raises(ValueError):
        StreamingLimitsRecord(max_cache_bytes=2, max_asset_bytes=3)
    for unsafe_path in ("", "a\\b", "/absolute.bin", "a\x00b"):
        with pytest.raises(ValueError):
            StreamingAssetRecord(
                id="asset",
                path=unsafe_path,
                sha256="a" * 64,
                size_bytes=1,
            )
    with pytest.raises(ValueError):
        StreamingAssetRecord(
            id="asset",
            path="asset.bin",
            sha256="a" * 64,
            size_bytes=1,
            priority=True,
        )


def test_streaming_format_and_persistence_boundaries_are_fail_closed(tmp_path: Path):
    payload = b"payload"
    document = _document(_asset("asset", "asset.bin", payload))
    raw = serialize_streaming_runtime_export(document)
    with pytest.raises(StreamingFormatError):
        load_streaming_runtime_export_bytes(raw.decode("utf-8"))
    with pytest.raises(StreamingFormatError):
        load_streaming_runtime_export_bytes(b"\xef\xbb\xbf" + raw)
    with pytest.raises(StreamingFormatError):
        load_streaming_runtime_export_bytes(b'{"duplicate": 1, "duplicate": 2}')
    with pytest.raises(StreamingFormatError):
        load_streaming_runtime_export_bytes(b"{")
    with pytest.raises(StreamingFormatError):
        load_streaming_runtime_export(tmp_path / "missing.json")
    with pytest.raises(StreamingValidationError):
        save_streaming_runtime_export(document, tmp_path)
    with pytest.raises(StreamingValidationError):
        save_streaming_runtime_export(document, tmp_path / "missing" / "streaming.json")
    with pytest.raises(StreamingValidationError):
        verify_streaming_source_binding(document, "not-bytes")


def test_streaming_lifecycle_and_request_errors_are_explicit(tmp_path: Path):
    payload = b"payload"
    document = _document(_asset("asset", "asset.bin", payload))
    runtime = StreamingRuntime()
    with pytest.raises(StreamingLifecycleError):
        runtime.request("asset")
    with pytest.raises(StreamingLifecycleError):
        runtime.start(tmp_path)
    runtime.load_manifest(document.model_dump(mode="json"))
    with pytest.raises(StreamingLifecycleError):
        runtime.start(tmp_path / "missing")
    runtime.start(tmp_path)
    with pytest.raises(StreamingLifecycleError):
        runtime.start(tmp_path)
    with pytest.raises(StreamingLifecycleError):
        runtime.load_manifest(document.model_dump(mode="json"))
    with pytest.raises(StreamingExecutionError):
        runtime.request("unknown")
    with pytest.raises(ValueError):
        runtime.request("asset", priority=True)
    with pytest.raises(ValueError):
        runtime.poll(max_events=0)
    with pytest.raises(StreamingExecutionError):
        runtime.get("asset")
    with pytest.raises(StreamingExecutionError):
        runtime.retry("asset")
    request = runtime.request("asset")
    runtime.cancel(request)
    runtime.release(request)
    with pytest.raises(StreamingExecutionError):
        runtime.release(request)
    with pytest.raises(StreamingExecutionError):
        runtime.cancel(request)
    runtime.shutdown()
    with pytest.raises(StreamingLifecycleError):
        runtime.poll()


def test_streaming_load_file_and_eviction_guards(tmp_path: Path):
    payload = b"payload"
    (tmp_path / "asset.bin").write_bytes(payload)
    document = _document(_asset("asset", "asset.bin", payload))
    manifest = tmp_path / "streaming.json"
    save_streaming_runtime_export(document, manifest)
    with StreamingRuntime() as runtime:
        runtime.load_file(manifest)
        runtime.start(tmp_path)
        request = runtime.request("asset")
        _wait(runtime, "asset", StreamingState.READY)
        with pytest.raises(StreamingExecutionError):
            runtime.evict("asset")
        runtime.release(request)
        runtime.evict("asset")
        assert any(event.state is StreamingState.EVICTED for event in runtime.poll())

    pinned_document = _document(
        {**_asset("pinned", "asset.bin", payload), "pinned": True}
    )
    with StreamingRuntime() as runtime:
        runtime.load_manifest(pinned_document.model_dump(mode="json"))
        runtime.start(tmp_path)
        request = runtime.request("pinned")
        _wait(runtime, "pinned", StreamingState.READY)
        runtime.release(request)
        with pytest.raises(StreamingExecutionError):
            runtime.evict("pinned")


def test_streaming_rejects_unsafe_paths_duplicates_and_noncanonical_bytes():
    with pytest.raises(ValueError):
        _document(_asset("bad", "../bad.bin", b"bad"))
    with pytest.raises(ValueError):
        _document(_asset("bad", "C:/bad.bin", b"bad"))
    duplicate = _asset("same", "one.bin", b"1")
    with pytest.raises(ValueError):
        _document(duplicate, {**duplicate, "path": "two.bin"})
    document = _document(_asset("asset", "asset.bin", b"x"))
    with pytest.raises(StreamingFormatError):
        load_streaming_runtime_export_bytes(
            json.dumps(document.model_dump(mode="json")).encode("utf-8")
        )


def test_streaming_limits_and_source_binding_fail_closed():
    with pytest.raises(ValueError):
        _document(_asset("large", "large.bin", b"1234"), max_cache_bytes=3)
    document = _document(_asset("asset", "asset.bin", b"x"))
    with pytest.raises(StreamingValidationError):
        verify_streaming_source_binding(document, b"different-scenario")


def test_runtime_host_advertises_streaming_as_native_capability():
    host = RuntimeHost()
    assert "runtime.streaming" in host.supported_capabilities
    report = host.negotiate([CapabilityRequest("runtime.streaming")])
    assert report.accepted
