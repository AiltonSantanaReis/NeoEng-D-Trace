"""Bounded deterministic asset streaming for the runtime ADR.

The streaming sidecar is deliberately separate from the authoring and scene
runtime manifests.  It reads real local files through a constrained root,
verifies their declared hashes, schedules requests by stable priority order,
keeps a bounded LRU cache, and exposes failures instead of silently dropping
assets.  Completion order from worker threads never determines event order.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_schema import StrictProjectModel

STREAMING_FORMAT_ID: Literal["neoeng-d-trace-runtime-streaming"] = (
    "neoeng-d-trace-runtime-streaming"
)
STREAMING_SCHEMA_VERSION: Literal[1] = 1
STREAMING_API_VERSION: Literal[1] = 1
STREAMING_ALGORITHM_VERSION: Literal[1] = 1
STREAMING_SOURCE_FORMAT_ID: Literal["neoeng-d-trace-scenario-runtime"] = (
    "neoeng-d-trace-scenario-runtime"
)
STREAMING_SOURCE_SCHEMA_VERSION: Literal[1] = 1

MAX_STREAMING_ID_LENGTH = 128
MAX_STREAMING_PATH_LENGTH = 1_024
MAX_STREAMING_ASSETS = 4_096
MAX_STREAMING_ASSET_BYTES = 256 * 1024 * 1024
MAX_STREAMING_CACHE_BYTES = 1 * 1024 * 1024 * 1024
MAX_STREAMING_PENDING = 4_096
MAX_STREAMING_EVENTS_PER_POLL = 4_096
MAX_STREAMING_PRIORITY = 1_000_000


class StreamingRuntimeError(ValueError):
    """Base class for controlled streaming failures."""


class StreamingFormatError(StreamingRuntimeError):
    """Raised when sidecar bytes are not canonical UTF-8 JSON."""


class StreamingValidationError(StreamingRuntimeError):
    """Raised when a sidecar violates the versioned contract."""


class StreamingExecutionError(StreamingRuntimeError):
    """Raised when a request cannot be loaded or verified safely."""


class StreamingLimitError(StreamingExecutionError):
    """Raised when a configured logical limit prevents a safe operation."""


class StreamingLifecycleError(StreamingExecutionError):
    """Raised when an operation is invalid for the runtime lifecycle."""


class StreamingState(str, Enum):
    """Stable state labels exposed by the runtime."""

    PENDING = "pending"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"
    EVICTED = "evicted"
    CANCELLED = "cancelled"


class StreamingSourceBindingRecord(StrictProjectModel):
    """Exact scenario-runtime bytes to which this sidecar is bound."""

    format_id: Literal["neoeng-d-trace-scenario-runtime"] = STREAMING_SOURCE_FORMAT_ID
    schema_version: Literal[1] = STREAMING_SOURCE_SCHEMA_VERSION
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def _strict_int(value: int, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be a strict integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return value


def _validate_relative_path(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_STREAMING_PATH_LENGTH
    ):
        raise ValueError("asset.path must be a non-empty bounded string")
    if "\\" in value or "\x00" in value:
        raise ValueError("asset.path must use relative POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/") or ":" in path.parts[0]:
        raise ValueError("asset.path must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("asset.path contains an unsafe component")
    return value


class StreamingLimitsRecord(StrictProjectModel):
    """Logical limits that make memory and work bounded and testable."""

    max_cache_bytes: int = MAX_STREAMING_CACHE_BYTES
    max_asset_bytes: int = MAX_STREAMING_ASSET_BYTES
    max_pending: int = MAX_STREAMING_PENDING
    max_events_per_poll: int = MAX_STREAMING_EVENTS_PER_POLL

    @field_validator(
        "max_cache_bytes",
        "max_asset_bytes",
        "max_pending",
        "max_events_per_poll",
    )
    @classmethod
    def validate_limits(cls, value: int, info) -> int:
        maximums = {
            "max_cache_bytes": MAX_STREAMING_CACHE_BYTES,
            "max_asset_bytes": MAX_STREAMING_ASSET_BYTES,
            "max_pending": MAX_STREAMING_PENDING,
            "max_events_per_poll": MAX_STREAMING_EVENTS_PER_POLL,
        }
        return _strict_int(value, info.field_name, 1, maximums[info.field_name])

    @model_validator(mode="after")
    def validate_cache_capacity(self) -> "StreamingLimitsRecord":
        if self.max_asset_bytes > self.max_cache_bytes:
            raise ValueError("max_asset_bytes cannot exceed max_cache_bytes")
        return self


class StreamingAssetRecord(StrictProjectModel):
    """One real local asset and its expected content identity."""

    id: str = Field(min_length=1, max_length=MAX_STREAMING_ID_LENGTH)
    path: str
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0, le=MAX_STREAMING_ASSET_BYTES)
    priority: int = 0
    enabled: bool = True
    pinned: bool = False

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _validate_relative_path(value)

    @field_validator("size_bytes")
    @classmethod
    def validate_size(cls, value: int) -> int:
        return _strict_int(value, "asset.size_bytes", 0, MAX_STREAMING_ASSET_BYTES)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        return _strict_int(
            value, "asset.priority", -MAX_STREAMING_PRIORITY, MAX_STREAMING_PRIORITY
        )


class StreamingDocumentV1(StrictProjectModel):
    """Complete version 1 streaming sidecar contract."""

    format_id: Literal["neoeng-d-trace-runtime-streaming"] = STREAMING_FORMAT_ID
    schema_version: Literal[1] = STREAMING_SCHEMA_VERSION
    api_version: Literal[1] = STREAMING_API_VERSION
    algorithm_version: Literal[1] = STREAMING_ALGORITHM_VERSION
    required_capability: Literal["runtime.streaming"] = "runtime.streaming"
    source: StreamingSourceBindingRecord
    limits: StreamingLimitsRecord = StreamingLimitsRecord()
    assets: list[StreamingAssetRecord] = Field(
        min_length=1, max_length=MAX_STREAMING_ASSETS
    )

    @model_validator(mode="after")
    def validate_assets(self) -> "StreamingDocumentV1":
        ids = [asset.id for asset in self.assets]
        paths = [asset.path for asset in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("streaming asset IDs must be unique")
        if len(paths) != len(set(paths)):
            raise ValueError("streaming asset paths must be unique")
        if any(asset.size_bytes > self.limits.max_asset_bytes for asset in self.assets):
            raise ValueError("asset exceeds the configured max_asset_bytes")
        return self


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StreamingValidationError(
            f"streaming document cannot be serialized: {exc}"
        ) from exc


def _validated_document(payload: object) -> StreamingDocumentV1:
    if isinstance(payload, StreamingDocumentV1):
        return payload.model_copy(deep=True)
    if not isinstance(payload, Mapping):
        raise StreamingValidationError("streaming document root must be an object")
    try:
        return StreamingDocumentV1.model_validate(payload, strict=True)
    except Exception as exc:
        raise StreamingValidationError(str(exc)) from exc


def build_streaming_runtime_export(
    document: StreamingDocumentV1,
) -> dict[str, Any]:
    """Validate and defensively copy a streaming sidecar."""

    return _validated_document(document).model_dump(mode="json")


def serialize_streaming_runtime_export(document: StreamingDocumentV1) -> bytes:
    """Serialize the streaming sidecar as canonical UTF-8 JSON."""

    encoded = _canonical_json_bytes(build_streaming_runtime_export(document))
    if len(encoded) > MAX_PROJECT_FILE_BYTES:
        raise StreamingValidationError("streaming document exceeds file limit")
    return encoded


def streaming_runtime_export_sha256(document: StreamingDocumentV1) -> str:
    """Hash the exact canonical sidecar bytes."""

    return hashlib.sha256(serialize_streaming_runtime_export(document)).hexdigest()


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_streaming_runtime_export_bytes(raw: bytes) -> StreamingDocumentV1:
    """Load canonical sidecar bytes with strict JSON checks."""

    if not isinstance(raw, bytes):
        raise StreamingFormatError("streaming manifest bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise StreamingFormatError("streaming manifest exceeds file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StreamingFormatError("UTF-8 BOM is not allowed")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise StreamingFormatError(f"invalid streaming JSON: {exc}") from exc
    document = _validated_document(payload)
    if raw != serialize_streaming_runtime_export(document):
        raise StreamingFormatError("streaming manifest bytes are not canonical")
    return document


def load_streaming_runtime_export(
    path: str | os.PathLike[str],
) -> StreamingDocumentV1:
    """Load a canonical streaming sidecar from disk."""

    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise StreamingFormatError(f"streaming manifest cannot be read: {exc}") from exc
    return load_streaming_runtime_export_bytes(raw)


def save_streaming_runtime_export(
    document: StreamingDocumentV1,
    destination: str | os.PathLike[str],
) -> None:
    """Atomically replace one streaming sidecar."""

    path = Path(destination)
    if path.exists() and path.is_dir():
        raise StreamingValidationError("streaming export destination is a directory")
    if not path.parent.exists() or not path.parent.is_dir():
        raise StreamingValidationError("streaming export parent does not exist")
    payload = serialize_streaming_runtime_export(document)
    try:
        with AtomicOutputTransaction() as transaction:
            temporary = Path(transaction.stage_path(str(path)))
            with temporary.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            transaction.commit()
    except OSError as exc:
        raise StreamingValidationError(
            f"failed to save streaming export: {exc}"
        ) from exc


def verify_streaming_source_binding(
    document: StreamingDocumentV1,
    source_bytes: bytes,
) -> None:
    """Verify that the sidecar is bound to exact scenario bytes."""

    validated = _validated_document(document)
    if not isinstance(source_bytes, bytes):
        raise StreamingValidationError("source_bytes must be bytes")
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != validated.source.sha256:
        raise StreamingValidationError("streaming source hash does not match")


@dataclass(frozen=True)
class StreamingRequest:
    """Stable handle returned for one caller request."""

    request_id: str
    asset_id: str


@dataclass(frozen=True)
class StreamingEvent:
    """Deterministic observable request transition."""

    sequence: int
    request_id: str
    asset_id: str
    state: StreamingState
    size_bytes: int = 0
    sha256: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class StreamingSnapshot:
    """Logical state that is safe to compare across platforms."""

    started: bool
    cache_bytes: int
    ready_assets: tuple[str, ...]
    pending_assets: tuple[str, ...]
    failed_assets: tuple[str, ...]
    active_requests: int


@dataclass
class _RequestState:
    request_id: str
    asset_id: str
    priority: int
    sequence: int
    released: bool = False
    cancelled: bool = False
    completed: bool = False


@dataclass
class _AssetState:
    record: StreamingAssetRecord
    state: StreamingState = StreamingState.PENDING
    payload: bytes | None = None
    future: Future[bytes] | None = None
    error: str | None = None
    last_access: int = 0


def _read_asset(root: Path, record: StreamingAssetRecord) -> bytes:
    candidate = (root / PurePosixPath(record.path)).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise StreamingExecutionError("asset path escapes the streaming root") from exc
    if not candidate.is_file():
        raise StreamingExecutionError(f"asset file not found: {record.id}")
    try:
        size = candidate.stat().st_size
        if size != record.size_bytes:
            raise StreamingExecutionError(
                f"asset size mismatch for {record.id}: "
                f"expected {record.size_bytes}, got {size}"
            )
        if size > MAX_STREAMING_ASSET_BYTES:
            raise StreamingLimitError(
                f"asset exceeds the absolute size limit: {record.id}"
            )
        payload = candidate.read_bytes()
    except OSError as exc:
        raise StreamingExecutionError(f"asset cannot be read: {record.id}") from exc
    digest = hashlib.sha256(payload).hexdigest()
    if digest != record.sha256:
        raise StreamingExecutionError(f"asset hash mismatch for {record.id}")
    return payload


class StreamingRuntime:
    """Threaded local loader with deterministic scheduling and bounded cache."""

    def __init__(self, *, workers: int = 2) -> None:
        if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
            raise ValueError("workers must be a positive integer")
        self._workers = workers
        self._document: StreamingDocumentV1 | None = None
        self._root: Path | None = None
        self._assets: dict[str, _AssetState] = {}
        self._requests: dict[str, _RequestState] = {}
        self._events: list[StreamingEvent] = []
        self._counter = 0
        self._access_counter = 0
        self._cache_bytes = 0
        self._started = False
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.RLock()

    @property
    def document(self) -> StreamingDocumentV1 | None:
        return self._document.model_copy(deep=True) if self._document else None

    @property
    def snapshot(self) -> StreamingSnapshot:
        with self._lock:
            ready = tuple(
                sorted(
                    k
                    for k, v in self._assets.items()
                    if v.state is StreamingState.READY
                )
            )
            pending = tuple(
                sorted(
                    k
                    for k, v in self._assets.items()
                    if v.state in {StreamingState.PENDING, StreamingState.LOADING}
                )
            )
            failed = tuple(
                sorted(
                    k
                    for k, v in self._assets.items()
                    if v.state is StreamingState.FAILED
                )
            )
            active = sum(
                not request.released and not request.cancelled and not request.completed
                for request in self._requests.values()
            )
            return StreamingSnapshot(
                started=self._started,
                cache_bytes=self._cache_bytes,
                ready_assets=ready,
                pending_assets=pending,
                failed_assets=failed,
                active_requests=active,
            )

    def load_manifest(self, payload: Mapping[str, Any]) -> StreamingSnapshot:
        """Validate and atomically replace the sidecar before start."""

        with self._lock:
            if self._started:
                raise StreamingLifecycleError(
                    "stop the streaming runtime before replacing its manifest"
                )
            document = _validated_document(payload)
            self._document = document
            self._assets = {
                asset.id: _AssetState(asset)
                for asset in document.assets
                if asset.enabled
            }
            self._requests.clear()
            self._events.clear()
            self._cache_bytes = 0
            return self.snapshot

    def load_file(self, path: str | os.PathLike[str]) -> StreamingSnapshot:
        """Load a canonical sidecar file before start."""

        return self.load_manifest(
            load_streaming_runtime_export(path).model_dump(mode="json")
        )

    def start(self, root: str | os.PathLike[str]) -> StreamingSnapshot:
        """Start real local loading under one existing directory root."""

        with self._lock:
            if self._started:
                raise StreamingLifecycleError("streaming runtime is already started")
            if self._document is None:
                raise StreamingLifecycleError(
                    "a validated streaming manifest is required"
                )
            candidate = Path(root)
            if not candidate.exists() or not candidate.is_dir():
                raise StreamingLifecycleError(
                    "streaming root must be an existing directory"
                )
            self._root = candidate.resolve()
            self._executor = ThreadPoolExecutor(max_workers=self._workers)
            self._started = True
            return self.snapshot

    def request(
        self, asset_id: str, *, priority: int | None = None
    ) -> StreamingRequest:
        """Queue or reuse one asset request without blocking the caller."""

        with self._lock:
            if not self._started or self._executor is None or self._document is None:
                raise StreamingLifecycleError("streaming runtime is not started")
            if not isinstance(asset_id, str) or asset_id not in self._assets:
                raise StreamingExecutionError("unknown or disabled streaming asset")
            entry = self._assets[asset_id]
            if entry.state is StreamingState.FAILED:
                raise StreamingExecutionError(
                    "asset failed; call retry before requesting it"
                )
            if entry.state in {StreamingState.CANCELLED, StreamingState.EVICTED}:
                entry.state = StreamingState.PENDING
                entry.error = None
                entry.future = None
            value = (
                entry.record.priority
                if priority is None
                else _strict_int(
                    priority,
                    "request.priority",
                    -MAX_STREAMING_PRIORITY,
                    MAX_STREAMING_PRIORITY,
                )
            )
            self._counter += 1
            request_id = f"request-{self._counter:08d}"
            request = _RequestState(request_id, asset_id, value, self._counter)
            self._requests[request_id] = request
            if entry.state is StreamingState.READY:
                self._access_counter += 1
                entry.last_access = self._access_counter
                self._events.append(
                    StreamingEvent(
                        self._counter,
                        request_id,
                        asset_id,
                        StreamingState.READY,
                        len(entry.payload or b""),
                        entry.record.sha256,
                    )
                )
            return StreamingRequest(request_id, asset_id)

    def cancel(self, request: StreamingRequest | str) -> None:
        """Cancel one request; cancellation never deletes a ready cache entry."""

        with self._lock:
            request_id = (
                request.request_id if isinstance(request, StreamingRequest) else request
            )
            state = self._requests.get(request_id)
            if state is None or state.released:
                raise StreamingExecutionError("unknown or released streaming request")
            state.cancelled = True
            entry = self._assets[state.asset_id]
            if (
                entry.state in {StreamingState.PENDING, StreamingState.LOADING}
                and self._live_requests(entry.record.id) == 0
            ):
                if entry.future is not None:
                    entry.future.cancel()
                entry.state = StreamingState.CANCELLED
                entry.error = "request cancelled"
                self._counter += 1
                self._events.append(
                    StreamingEvent(
                        self._counter,
                        request_id,
                        entry.record.id,
                        StreamingState.CANCELLED,
                        error=entry.error,
                    )
                )

    def release(self, request: StreamingRequest | str) -> None:
        """Release the caller's reference so an unpinned asset may be evicted."""

        with self._lock:
            request_id = (
                request.request_id if isinstance(request, StreamingRequest) else request
            )
            state = self._requests.get(request_id)
            if state is None or state.released:
                raise StreamingExecutionError(
                    "unknown or already released streaming request"
                )
            state.released = True

    def retry(self, asset_id: str) -> None:
        """Reset one failed/cancelled asset; retry is explicit and observable."""

        with self._lock:
            entry = self._assets.get(asset_id)
            if entry is None:
                raise StreamingExecutionError("unknown or disabled streaming asset")
            if entry.state not in {
                StreamingState.FAILED,
                StreamingState.CANCELLED,
                StreamingState.EVICTED,
            }:
                raise StreamingExecutionError("asset is not in a retryable state")
            entry.state = StreamingState.PENDING
            entry.error = None
            entry.future = None
            self._counter += 1
            self._events.append(
                StreamingEvent(self._counter, "", asset_id, StreamingState.PENDING)
            )

    def get(self, asset_id: str) -> bytes:
        """Return cached bytes only; no hidden synchronous load is allowed."""

        with self._lock:
            entry = self._assets.get(asset_id)
            if (
                entry is None
                or entry.state is not StreamingState.READY
                or entry.payload is None
            ):
                raise StreamingExecutionError(
                    "asset is not ready in the streaming cache"
                )
            self._access_counter += 1
            entry.last_access = self._access_counter
            return bytes(entry.payload)

    def evict(self, asset_id: str) -> None:
        """Evict one unpinned, unreferenced ready asset."""

        with self._lock:
            entry = self._assets.get(asset_id)
            if entry is None or entry.state is not StreamingState.READY:
                raise StreamingExecutionError("asset is not ready")
            if entry.record.pinned or self._live_requests(asset_id) > 0:
                raise StreamingExecutionError("asset is pinned or still referenced")
            self._drop_cache_entry(entry, StreamingState.EVICTED)

    def poll(self, max_events: int | None = None) -> tuple[StreamingEvent, ...]:
        """Advance workers and commit completed results in stable request order."""

        with self._lock:
            if not self._started or self._executor is None or self._document is None:
                raise StreamingLifecycleError("streaming runtime is not started")
            limit = (
                self._document.limits.max_events_per_poll
                if max_events is None
                else _strict_int(
                    max_events,
                    "max_events",
                    1,
                    self._document.limits.max_events_per_poll,
                )
            )
            self._pump()
            while len(self._events) < limit:
                candidates = sorted(
                    (
                        entry
                        for entry in self._assets.values()
                        if entry.state is StreamingState.LOADING
                        and entry.future is not None
                    ),
                    key=lambda entry: (-self._entry_priority(entry), entry.record.id),
                )
                if not candidates:
                    break
                candidate = candidates[0]
                future = candidate.future
                if future is None or not future.done():
                    break
                self._finish(candidate)
                self._pump()
            output = tuple(self._events[:limit])
            del self._events[:limit]
            return output

    def shutdown(self) -> None:
        """Cancel pending work and release worker resources deterministically."""

        with self._lock:
            for request in self._requests.values():
                if not request.released and not request.completed:
                    request.cancelled = True
            if self._executor is not None:
                self._executor.shutdown(wait=True, cancel_futures=True)
            self._executor = None
            self._started = False
            self._root = None

    def _entry_priority(self, entry: _AssetState) -> int:
        active = [
            request.priority
            for request in self._requests.values()
            if request.asset_id == entry.record.id
            and not request.released
            and not request.cancelled
            and not request.completed
        ]
        return max(active, default=entry.record.priority)

    def _live_requests(self, asset_id: str) -> int:
        return sum(
            not request.released and not request.cancelled
            for request in self._requests.values()
            if request.asset_id == asset_id
        )

    def _pump(self) -> None:
        assert self._document is not None
        assert self._executor is not None
        active_count = sum(
            entry.state is StreamingState.LOADING for entry in self._assets.values()
        )
        capacity = self._document.limits.max_pending - active_count
        if capacity <= 0:
            return
        pending = sorted(
            (
                entry
                for entry in self._assets.values()
                if entry.state is StreamingState.PENDING
            ),
            key=lambda entry: (-self._entry_priority(entry), entry.record.id),
        )
        for entry in pending[:capacity]:
            if self._live_requests(entry.record.id) == 0 and not entry.record.pinned:
                continue
            assert self._root is not None
            entry.state = StreamingState.LOADING
            entry.future = self._executor.submit(_read_asset, self._root, entry.record)

    def _finish(self, entry: _AssetState) -> None:
        assert entry.future is not None
        try:
            payload = entry.future.result()
            if self._live_requests(entry.record.id) == 0 and not entry.record.pinned:
                entry.state = StreamingState.CANCELLED
                entry.error = "all requests were cancelled"
                self._counter += 1
                self._events.append(
                    StreamingEvent(
                        self._counter,
                        self._first_request_id(entry.record.id, include_cancelled=True),
                        entry.record.id,
                        StreamingState.CANCELLED,
                        error=entry.error,
                    )
                )
                return
            self._make_room(len(payload), entry.record.id)
            entry.payload = payload
            entry.state = StreamingState.READY
            entry.error = None
            self._cache_bytes += len(payload)
            self._access_counter += 1
            entry.last_access = self._access_counter
            self._counter += 1
            self._events.append(
                StreamingEvent(
                    self._counter,
                    self._first_request_id(entry.record.id),
                    entry.record.id,
                    StreamingState.READY,
                    len(payload),
                    entry.record.sha256,
                )
            )
        except Exception as exc:
            entry.payload = None
            entry.state = StreamingState.FAILED
            entry.error = str(exc)
            self._counter += 1
            self._events.append(
                StreamingEvent(
                    self._counter,
                    self._first_request_id(entry.record.id),
                    entry.record.id,
                    StreamingState.FAILED,
                    error=str(exc),
                )
            )
        finally:
            entry.future = None
            for request in self._requests.values():
                if (
                    request.asset_id == entry.record.id
                    and not request.released
                    and not request.cancelled
                ):
                    request.completed = True

    def _first_request_id(
        self, asset_id: str, *, include_cancelled: bool = False
    ) -> str:
        requests = sorted(
            (
                request
                for request in self._requests.values()
                if request.asset_id == asset_id
                and not request.released
                and (include_cancelled or not request.cancelled)
            ),
            key=lambda request: request.sequence,
        )
        return requests[0].request_id if requests else ""

    def _make_room(self, required: int, incoming_id: str) -> None:
        assert self._document is not None
        if required > self._document.limits.max_cache_bytes:
            raise StreamingLimitError("asset does not fit in the cache budget")
        while self._cache_bytes + required > self._document.limits.max_cache_bytes:
            candidates = sorted(
                (
                    entry
                    for entry in self._assets.values()
                    if entry.record.id != incoming_id
                    and entry.state is StreamingState.READY
                    and not entry.record.pinned
                    and self._live_requests(entry.record.id) == 0
                ),
                key=lambda entry: (entry.last_access, entry.record.id),
            )
            if not candidates:
                raise StreamingLimitError("cache budget cannot fit the requested asset")
            self._drop_cache_entry(candidates[0], StreamingState.EVICTED)

    def _drop_cache_entry(self, entry: _AssetState, state: StreamingState) -> None:
        size = len(entry.payload or b"")
        self._cache_bytes -= size
        entry.payload = None
        entry.state = state
        entry.error = None
        self._counter += 1
        self._events.append(
            StreamingEvent(
                self._counter, "", entry.record.id, state, size, entry.record.sha256
            )
        )

    def __enter__(self) -> "StreamingRuntime":
        return self

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> Literal[False]:
        self.shutdown()
        return False


__all__ = [
    "MAX_STREAMING_ASSET_BYTES",
    "MAX_STREAMING_ASSETS",
    "MAX_STREAMING_CACHE_BYTES",
    "STREAMING_ALGORITHM_VERSION",
    "STREAMING_API_VERSION",
    "STREAMING_FORMAT_ID",
    "STREAMING_SCHEMA_VERSION",
    "StreamingAssetRecord",
    "StreamingDocumentV1",
    "StreamingEvent",
    "StreamingExecutionError",
    "StreamingFormatError",
    "StreamingLifecycleError",
    "StreamingLimitError",
    "StreamingRequest",
    "StreamingRuntime",
    "StreamingRuntimeError",
    "StreamingSnapshot",
    "StreamingSourceBindingRecord",
    "StreamingState",
    "StreamingValidationError",
    "build_streaming_runtime_export",
    "load_streaming_runtime_export",
    "load_streaming_runtime_export_bytes",
    "save_streaming_runtime_export",
    "serialize_streaming_runtime_export",
    "streaming_runtime_export_sha256",
    "verify_streaming_source_binding",
]
