"""Deterministic base runtime for the versioned scenario export contract.

The existing scenario exporter remains the authoring-to-manifest boundary.  It
does not execute a scene.  This module is the separate, deliberately small
execution host required by the runtime ADR.  It validates the existing
``neoeng-d-trace-scenario-runtime`` manifest without changing its schema and
provides only the base guarantees: transactional activation, lifecycle,
explicit capabilities, cancellation and fixed-step time.

Lighting, particles, shaders, post-processing, triggers and streaming are not
registered as supported capabilities here.  A later phase must add each one
with its own contract and evidence instead of silently treating this host as a
complete engine.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.exporters.scenario_exporter import validate_scenario_runtime_export

RUNTIME_HOST_FORMAT_ID = "neoeng-d-trace-runtime-host"
RUNTIME_HOST_API_VERSION = 1
_DEFAULT_FIXED_DT = 1.0 / 60.0
_DEFAULT_MAX_SUBSTEPS = 8
_SUPPORTED_CAPABILITIES = frozenset(
    {
        "runtime.scene_loading",
        "runtime.lifecycle",
        "runtime.fixed_update",
        "runtime.cancellation",
        "runtime.rollback",
    }
)


class RuntimeHostError(Exception):
    """Base class for controlled runtime-host failures."""


class RuntimeManifestFormatError(RuntimeHostError):
    """Raised when manifest bytes are not strict canonical UTF-8 JSON."""


class RuntimeManifestValidationError(RuntimeHostError):
    """Raised when a manifest does not satisfy the existing runtime schema."""


class RuntimeCapabilityError(RuntimeHostError):
    """Raised when requested capabilities cannot be fulfilled safely."""

    def __init__(self, message: str, report: "RuntimeCapabilityReport") -> None:
        super().__init__(message)
        self.report = report


class RuntimeLifecycleError(RuntimeHostError):
    """Raised when an operation is invalid for the current lifecycle state."""


class RuntimeClockError(RuntimeHostError):
    """Raised when fixed-step input would be unsafe or nondeterministic."""


class RuntimeCancelledError(RuntimeHostError):
    """Raised when a cancellable runtime operation is cancelled."""


class RuntimeExecutionError(RuntimeHostError):
    """Reserved base-runtime error for a failed deterministic execution step."""


class RuntimePhase(str, Enum):
    """Lifecycle states exposed by the base runtime host."""

    EMPTY = "empty"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class Compatibility(str, Enum):
    """Compatibility result for one explicitly requested capability."""

    NATIVE = "native"
    DEGRADED = "degraded"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True)
class CapabilityRequest:
    """A capability request with an explicit safe fallback declaration."""

    required_capability: str
    required: bool = True
    fallback_mode: str | None = None
    fallback_reason: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.required_capability, str)
            or not self.required_capability
        ):
            raise ValueError("required_capability must be a non-empty string")
        if not isinstance(self.required, bool):
            raise ValueError("required must be boolean")
        if (self.fallback_mode is None) != (self.fallback_reason is None):
            raise ValueError(
                "fallback_mode and fallback_reason must be provided together"
            )
        for name, value in (
            ("fallback_mode", self.fallback_mode),
            ("fallback_reason", self.fallback_reason),
        ):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class CapabilityDecision:
    """Auditable decision for one capability request."""

    required_capability: str
    compatibility: Compatibility
    mode: str
    reason: str
    adapter_id: str
    adapter_version: int


@dataclass(frozen=True)
class RuntimeCapabilityReport:
    """Immutable capability negotiation result."""

    decisions: tuple[CapabilityDecision, ...]

    @property
    def accepted(self) -> bool:
        return all(
            decision.compatibility is not Compatibility.INCOMPATIBLE
            for decision in self.decisions
        )

    @property
    def incompatible(self) -> tuple[CapabilityDecision, ...]:
        return tuple(
            decision
            for decision in self.decisions
            if decision.compatibility is Compatibility.INCOMPATIBLE
        )


@dataclass(frozen=True)
class RuntimeHostSnapshot:
    """Deterministic observable host state; no wall-clock data is included."""

    phase: RuntimePhase
    manifest_sha256: str | None
    fixed_dt: float
    tick_index: int
    simulation_time: float
    accumulator: float


@dataclass(frozen=True)
class RuntimeTickResult:
    """Result of one fixed-step advancement request."""

    elapsed: float
    steps: int
    tick_index: int
    simulation_time: float
    accumulator: float


class RuntimeCancellationToken:
    """Thread-safe cooperative cancellation token for runtime operations."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeManifestValidationError(
            f"runtime manifest cannot be canonicalized: {exc}"
        ) from exc
    return (text + "\n").encode("utf-8")


def _validated_manifest(payload: object) -> tuple[dict[str, Any], bytes, str]:
    if not isinstance(payload, Mapping):
        raise RuntimeManifestValidationError("runtime manifest root must be an object")
    copied = copy.deepcopy(dict(payload))
    try:
        validate_scenario_runtime_export(copied)
    except (TypeError, ValueError, KeyError) as exc:
        raise RuntimeManifestValidationError(str(exc)) from exc
    canonical = _canonical_json_bytes(copied)
    digest = hashlib.sha256(canonical).hexdigest()
    return copied, canonical, digest


def _read_manifest_file(path: Path) -> tuple[dict[str, Any], bytes, str]:
    if not path.exists():
        raise RuntimeManifestFormatError(f"runtime manifest not found: {path}")
    if not path.is_file():
        raise RuntimeManifestFormatError(f"runtime manifest is not a file: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise RuntimeManifestFormatError(
            f"runtime manifest cannot be inspected: {exc}"
        ) from exc
    if size > MAX_PROJECT_FILE_BYTES:
        raise RuntimeManifestFormatError(
            f"runtime manifest exceeds {MAX_PROJECT_FILE_BYTES} bytes"
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeManifestFormatError(
            f"runtime manifest cannot be read: {exc}"
        ) from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeManifestFormatError("UTF-8 BOM is not allowed")
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as exc:
        raise RuntimeManifestFormatError(
            f"invalid runtime manifest JSON: {exc}"
        ) from exc
    copied, canonical, digest = _validated_manifest(payload)
    if raw != canonical:
        raise RuntimeManifestFormatError(
            "runtime manifest bytes are not canonical; regenerate the export"
        )
    return copied, canonical, digest


class RuntimeHost:
    """Transactional deterministic host for the existing runtime manifest."""

    def __init__(
        self,
        *,
        fixed_dt: float = _DEFAULT_FIXED_DT,
        max_substeps: int = _DEFAULT_MAX_SUBSTEPS,
    ) -> None:
        if isinstance(fixed_dt, bool) or not isinstance(fixed_dt, (int, float)):
            raise ValueError("fixed_dt must be a finite positive number")
        if not math.isfinite(float(fixed_dt)) or float(fixed_dt) <= 0:
            raise ValueError("fixed_dt must be a finite positive number")
        if isinstance(max_substeps, bool) or not isinstance(max_substeps, int):
            raise ValueError("max_substeps must be a positive integer")
        if max_substeps <= 0:
            raise ValueError("max_substeps must be a positive integer")
        self._fixed_dt = float(fixed_dt)
        self._max_substeps = max_substeps
        self._phase = RuntimePhase.EMPTY
        self._manifest: dict[str, Any] | None = None
        self._manifest_sha256: str | None = None
        self._tick_index = 0
        self._simulation_time = 0.0
        self._accumulator = 0.0

    @property
    def snapshot(self) -> RuntimeHostSnapshot:
        return RuntimeHostSnapshot(
            phase=self._phase,
            manifest_sha256=self._manifest_sha256,
            fixed_dt=self._fixed_dt,
            tick_index=self._tick_index,
            simulation_time=self._simulation_time,
            accumulator=self._accumulator,
        )

    @property
    def supported_capabilities(self) -> frozenset[str]:
        return _SUPPORTED_CAPABILITIES

    def manifest_copy(self) -> dict[str, Any] | None:
        """Return a defensive copy of the active manifest, if one is loaded."""

        return copy.deepcopy(self._manifest) if self._manifest is not None else None

    def negotiate(
        self,
        requests: tuple[CapabilityRequest, ...] | list[CapabilityRequest],
    ) -> RuntimeCapabilityReport:
        decisions: list[CapabilityDecision] = []
        for request in requests:
            if not isinstance(request, CapabilityRequest):
                raise ValueError("capability requests must use CapabilityRequest")
            if request.required_capability in _SUPPORTED_CAPABILITIES:
                decisions.append(
                    CapabilityDecision(
                        required_capability=request.required_capability,
                        compatibility=Compatibility.NATIVE,
                        mode="native",
                        reason="supported by the base runtime host",
                        adapter_id=RUNTIME_HOST_FORMAT_ID,
                        adapter_version=RUNTIME_HOST_API_VERSION,
                    )
                )
                continue
            if request.fallback_mode is not None:
                decisions.append(
                    CapabilityDecision(
                        required_capability=request.required_capability,
                        compatibility=Compatibility.DEGRADED,
                        mode=request.fallback_mode,
                        reason=request.fallback_reason or "explicit safe fallback",
                        adapter_id=RUNTIME_HOST_FORMAT_ID,
                        adapter_version=RUNTIME_HOST_API_VERSION,
                    )
                )
                continue
            decisions.append(
                CapabilityDecision(
                    required_capability=request.required_capability,
                    compatibility=Compatibility.INCOMPATIBLE,
                    mode="rejected",
                    reason="no native support and no explicit safe fallback",
                    adapter_id=RUNTIME_HOST_FORMAT_ID,
                    adapter_version=RUNTIME_HOST_API_VERSION,
                )
            )
        return RuntimeCapabilityReport(tuple(decisions))

    def _require_capabilities(
        self,
        requests: tuple[CapabilityRequest, ...] | list[CapabilityRequest],
    ) -> RuntimeCapabilityReport:
        report = self.negotiate(requests)
        if report.incompatible:
            raise RuntimeCapabilityError(
                "runtime manifest requires incompatible capabilities",
                report,
            )
        return report

    def load_manifest(
        self,
        payload: Mapping[str, Any],
        *,
        requirements: tuple[CapabilityRequest, ...] | list[CapabilityRequest] = (),
    ) -> RuntimeHostSnapshot:
        """Validate and atomically activate a manifest without partial state."""

        if self._phase is RuntimePhase.RUNNING:
            raise RuntimeLifecycleError(
                "stop the runtime before replacing its manifest"
            )
        candidate, _canonical, digest = _validated_manifest(payload)
        self._require_capabilities(requirements)
        self._manifest = candidate
        self._manifest_sha256 = digest
        self._phase = RuntimePhase.READY
        self._tick_index = 0
        self._simulation_time = 0.0
        self._accumulator = 0.0
        return self.snapshot

    def load_file(
        self,
        path: str | os.PathLike[str],
        *,
        requirements: tuple[CapabilityRequest, ...] | list[CapabilityRequest] = (),
    ) -> RuntimeHostSnapshot:
        """Load and atomically activate canonical bytes from a real file."""

        if self._phase is RuntimePhase.RUNNING:
            raise RuntimeLifecycleError(
                "stop the runtime before replacing its manifest"
            )
        candidate, _canonical, digest = _read_manifest_file(Path(path))
        self._require_capabilities(requirements)
        self._manifest = candidate
        self._manifest_sha256 = digest
        self._phase = RuntimePhase.READY
        self._tick_index = 0
        self._simulation_time = 0.0
        self._accumulator = 0.0
        return self.snapshot

    def start(self) -> RuntimeHostSnapshot:
        if self._manifest is None:
            raise RuntimeLifecycleError("a validated runtime manifest is required")
        if self._phase not in {
            RuntimePhase.READY,
            RuntimePhase.PAUSED,
            RuntimePhase.STOPPED,
        }:
            raise RuntimeLifecycleError(f"cannot start from phase {self._phase.value}")
        self._phase = RuntimePhase.RUNNING
        return self.snapshot

    def pause(self) -> RuntimeHostSnapshot:
        if self._phase is not RuntimePhase.RUNNING:
            raise RuntimeLifecycleError("pause requires a running runtime")
        self._phase = RuntimePhase.PAUSED
        return self.snapshot

    def resume(self) -> RuntimeHostSnapshot:
        if self._phase is not RuntimePhase.PAUSED:
            raise RuntimeLifecycleError("resume requires a paused runtime")
        self._phase = RuntimePhase.RUNNING
        return self.snapshot

    def stop(self) -> RuntimeHostSnapshot:
        if self._phase not in {
            RuntimePhase.READY,
            RuntimePhase.RUNNING,
            RuntimePhase.PAUSED,
            RuntimePhase.STOPPED,
        }:
            raise RuntimeLifecycleError("stop requires an activated runtime")
        self._phase = RuntimePhase.STOPPED
        return self.snapshot

    def tick(
        self,
        elapsed: float,
        cancellation: RuntimeCancellationToken | None = None,
    ) -> RuntimeTickResult:
        """Advance deterministic fixed steps, or leave state untouched on cancel."""

        if self._phase is not RuntimePhase.RUNNING:
            raise RuntimeLifecycleError("tick requires a running runtime")
        if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)):
            raise RuntimeClockError("elapsed must be a finite non-negative number")
        elapsed_value = float(elapsed)
        if not math.isfinite(elapsed_value) or elapsed_value < 0:
            raise RuntimeClockError("elapsed must be a finite non-negative number")
        if elapsed_value > self._fixed_dt * self._max_substeps:
            raise RuntimeClockError("elapsed exceeds the fixed-step catch-up limit")
        if cancellation is not None and cancellation.cancelled:
            raise RuntimeCancelledError("runtime tick was cancelled")

        candidate_accumulator = self._accumulator + elapsed_value
        steps = int(math.floor(candidate_accumulator / self._fixed_dt + 1e-12))
        if steps > self._max_substeps:
            raise RuntimeClockError("fixed-step catch-up limit would be exceeded")
        for _ in range(steps):
            if cancellation is not None and cancellation.cancelled:
                raise RuntimeCancelledError("runtime tick was cancelled")
        candidate_accumulator -= steps * self._fixed_dt
        candidate_tick = self._tick_index + steps
        candidate_time = self._simulation_time + steps * self._fixed_dt
        self._accumulator = candidate_accumulator
        self._tick_index = candidate_tick
        self._simulation_time = candidate_time
        return RuntimeTickResult(
            elapsed=elapsed_value,
            steps=steps,
            tick_index=candidate_tick,
            simulation_time=candidate_time,
            accumulator=candidate_accumulator,
        )
