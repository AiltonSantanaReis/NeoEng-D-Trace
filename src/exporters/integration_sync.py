"""Fail-closed planning and transactional application for engine outputs.

The native adapters consume the same manifest contract, but their filesystem
operations are implemented by the target engine.  This module is the Python
reference contract used by export tooling and audit harnesses: planning never
mutates the filesystem, every destination is checked before staging, and a
multi-output commit is restored when any replacement fails.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from src.core.atomic_outputs import AtomicOutputTransaction
from src.exporters.integration_manifest import (
    _canonical_json_bytes,
    _sha256_file,
    validate_integration_manifest,
)


class IntegrationSecurityError(ValueError):
    """Raised when an integration path or source violates the safety contract."""


class IntegrationPlanError(ValueError):
    """Raised when a planned output set cannot be applied safely."""


@dataclass(frozen=True)
class PlannedOutput:
    """One deterministic output in an integration plan."""

    relative_path: str
    absolute_path: Path
    action: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class IntegrationPlan:
    """Immutable plan returned before any output is written."""

    root: Path
    outputs: tuple[PlannedOutput, ...]

    @property
    def changed(self) -> tuple[PlannedOutput, ...]:
        return tuple(item for item in self.outputs if item.action != "UNCHANGED")


@dataclass(frozen=True)
class GlobalIntegrationPlan:
    """Immutable plan for one atomic commit spanning several manifests."""

    root: Path
    manifests: tuple[str, ...]
    plans: tuple[IntegrationPlan, ...]

    @property
    def outputs(self) -> tuple[PlannedOutput, ...]:
        return tuple(item for plan in self.plans for item in plan.outputs)

    @property
    def changed(self) -> tuple[PlannedOutput, ...]:
        return tuple(item for item in self.outputs if item.action != "UNCHANGED")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntegrationSecurityError("output path must be relative and safe")
    normalized = value.replace("\\", "/")
    if (
        normalized.startswith("/")
        or normalized.startswith("//")
        or (len(normalized) >= 2 and normalized[1] == ":")
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise IntegrationSecurityError("output path must be relative and safe")
    return "/".join(normalized.split("/"))


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_destination(root: Path, relative_path: str) -> Path:
    safe = _safe_relative(relative_path)
    root_resolved = root.resolve(strict=False)
    current = root_resolved
    for part in Path(safe).parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise IntegrationSecurityError("output path traverses a symlink")
    raw_candidate = root_resolved / Path(safe)
    if raw_candidate.exists() and raw_candidate.is_symlink():
        raise IntegrationSecurityError("output destination cannot be a symlink")
    candidate = raw_candidate.resolve(strict=False)
    if not _inside(root_resolved, candidate):
        raise IntegrationSecurityError("output path escapes the generated root")
    return candidate


def plan_outputs(
    root: str | Path,
    outputs: Mapping[str, bytes | bytearray | str],
) -> IntegrationPlan:
    """Validate and diff an output set without creating or modifying files."""

    root_path = Path(root)
    if root_path.exists() and not root_path.is_dir():
        raise IntegrationSecurityError("generated root must be a directory")
    normalized: list[tuple[str, Path, bytes]] = []
    seen: set[Path] = set()
    for relative_path, value in outputs.items():
        destination = _resolve_destination(root_path, relative_path)
        if destination in seen:
            raise IntegrationPlanError("duplicate output destinations")
        seen.add(destination)
        payload = value.encode("utf-8") if isinstance(value, str) else bytes(value)
        normalized.append((relative_path.replace("\\", "/"), destination, payload))
    normalized.sort(key=lambda item: item[0])
    planned: list[PlannedOutput] = []
    for relative_path, destination, payload in normalized:
        digest = _digest(payload)
        if destination.is_file() and destination.read_bytes() == payload:
            action = "UNCHANGED"
        elif destination.exists():
            action = "UPDATE"
        else:
            action = "CREATE"
        planned.append(
            PlannedOutput(
                relative_path=relative_path,
                absolute_path=destination,
                action=action,
                sha256=digest,
                bytes=len(payload),
            )
        )
    return IntegrationPlan(root=root_path.resolve(strict=False), outputs=tuple(planned))


def plan_manifest_batch(
    root: str | Path,
    manifests: Mapping[str, Mapping[str, bytes | bytearray | str]],
) -> GlobalIntegrationPlan:
    """Plan all manifest outputs before any of them is written."""

    if not isinstance(manifests, Mapping) or not manifests:
        raise IntegrationPlanError("manifest batch must not be empty")
    root_path = Path(root).resolve(strict=False)
    entries: list[tuple[str, IntegrationPlan]] = []
    destinations: set[Path] = set()
    for manifest_id, outputs in manifests.items():
        if not isinstance(manifest_id, str) or not manifest_id.strip():
            raise IntegrationPlanError("manifest identifier must be non-empty")
        _safe_relative(manifest_id)
        if not isinstance(outputs, Mapping) or not outputs:
            raise IntegrationPlanError("manifest output set must not be empty")
        entries.append((manifest_id, plan_outputs(root_path, outputs)))
    entries.sort(key=lambda item: item[0])
    for _, plan in entries:
        if plan.root != root_path:
            raise IntegrationPlanError("manifest plans must share one generated root")
        for item in plan.outputs:
            if item.absolute_path in destinations:
                raise IntegrationPlanError(
                    "manifests contain duplicate output destinations"
                )
            destinations.add(item.absolute_path)
    return GlobalIntegrationPlan(
        root=root_path,
        manifests=tuple(item[0] for item in entries),
        plans=tuple(item[1] for item in entries),
    )


def validate_manifest_sources(
    manifest: Mapping[str, object],
    *,
    image_path: str | Path,
    atlas_paths: Mapping[str, str | Path] | None = None,
) -> None:
    """Validate manifest structure and all hashes against regular local files."""

    validate_integration_manifest(manifest)
    image = manifest["source"]["image"]  # type: ignore[index]
    expected_image = image["sha256"]  # type: ignore[index]
    actual_image = _sha256_file(image_path)
    if actual_image != expected_image:
        raise IntegrationPlanError("source image hash does not match manifest")
    if manifest.get("schema_version") != 2:
        return
    pages = manifest["advanced"]["atlas"]["pages"]  # type: ignore[index]
    provided = atlas_paths or {}
    for page in pages:  # type: ignore[union-attr]
        page_id = page["id"]  # type: ignore[index]
        if page_id not in provided:
            raise IntegrationPlanError(f"atlas page path is missing: {page_id}")
        if _sha256_file(provided[page_id]) != page["sha256"]:  # type: ignore[index]
            raise IntegrationPlanError(f"atlas page hash does not match: {page_id}")


def apply_plan(
    plan: IntegrationPlan,
    outputs: Mapping[str, bytes | bytearray | str],
) -> None:
    """Apply a previously planned set atomically, with no-op unchanged files."""

    expected = {item.relative_path for item in plan.outputs}
    if set(outputs) != expected:
        raise IntegrationPlanError("output set changed after dry-run")
    _commit_output_items(plan.changed, outputs)


def apply_manifest_batch(
    plan: GlobalIntegrationPlan,
    manifests: Mapping[str, Mapping[str, bytes | bytearray | str]],
) -> None:
    """Commit every changed output from every manifest in one transaction."""

    if not isinstance(manifests, Mapping):
        raise IntegrationPlanError("manifest batch changed after dry-run")
    keys = tuple(manifests)
    if (
        any(not isinstance(key, str) for key in keys)
        or set(keys) != set(plan.manifests)
        or tuple(sorted(keys)) != plan.manifests
    ):
        raise IntegrationPlanError("manifest batch changed after dry-run")
        raise IntegrationPlanError("manifest batch changed after dry-run")
    all_outputs: dict[str, bytes | bytearray | str] = {}
    for manifest_id in plan.manifests:
        manifest_outputs = manifests[manifest_id]
        manifest_plan = plan.plans[plan.manifests.index(manifest_id)]
        if not isinstance(manifest_outputs, Mapping):
            raise IntegrationPlanError("manifest output set is invalid")
        if set(manifest_outputs) != {
            item.relative_path for item in manifest_plan.outputs
        }:
            raise IntegrationPlanError("manifest output set changed after dry-run")
        for relative_path, payload in manifest_outputs.items():
            if relative_path in all_outputs:
                raise IntegrationPlanError(
                    "manifests contain duplicate output destinations"
                )
            all_outputs[relative_path] = payload
    _commit_output_items(plan.changed, all_outputs)


def _commit_output_items(
    changed: tuple[PlannedOutput, ...],
    outputs: Mapping[str, bytes | bytearray | str],
) -> None:
    transaction = AtomicOutputTransaction()
    try:
        for item in changed:
            staged = transaction.stage_path(str(item.absolute_path))
            payload = outputs[item.relative_path]
            data = (
                payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
            )
            if _digest(data) != item.sha256:
                raise IntegrationPlanError("output payload changed after dry-run")
            with open(staged, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        transaction.commit()
    except Exception:
        transaction.abort()
        raise


def manifest_payload_hash(manifest: Mapping[str, object]) -> str:
    """Return the canonical metadata hash used by the manifest contract."""

    metadata = manifest.get("metadata")
    if not isinstance(metadata, Mapping):
        raise IntegrationPlanError("manifest metadata is invalid")
    return _digest(_canonical_json_bytes(metadata))
