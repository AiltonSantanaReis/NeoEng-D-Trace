"""Read-only discovery and preflight helpers for the external Unity flow.

The NeoEng-D-Trace application does not own a Unity entitlement.  Unity Hub
owns login, activation and plan validation.  This module therefore only
normalizes user-selected executable paths and inspects their presence; it
never reads license files, tokens or credentials and never starts a process.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence

from src.core.operational_limits import MAX_CONFIG_PATH_LENGTH

UNITY_HUB_DOCS_URL = "https://docs.unity.com/en-us/hub/manage-license"
UNITY_ID_URL = "https://id.unity.com/"

ExecutableKind = Literal["hub", "editor"]
ExecutableState = Literal["not_configured", "available", "missing", "invalid"]


@dataclass(frozen=True, slots=True)
class UnityIntegrationSnapshot:
    """A bounded, non-secret snapshot of the Unity tool preflight."""

    hub_path: Path | None
    editor_path: Path | None
    hub_state: ExecutableState
    editor_state: ExecutableState


def normalize_external_path(value: str | os.PathLike[str] | None) -> Path | None:
    """Normalize a user-selected external path without reading its contents."""

    if value is None:
        return None
    text = os.fspath(value).strip()
    if not text:
        return None
    if "\x00" in text:
        raise ValueError("external path contains a NUL character")
    if len(text) > MAX_CONFIG_PATH_LENGTH:
        raise ValueError("external path exceeds the configured length limit")
    return Path(text).expanduser().resolve(strict=False)


def _deduplicate(paths: Sequence[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = os.path.normcase(os.path.normpath(str(path)))
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _environment_value(environment: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = environment.get(name)
        if value:
            return value
    return None


def discover_unity_hub_executables(
    environment: Mapping[str, str] | None = None,
) -> tuple[Path, ...]:
    """Find conventional Unity Hub locations without launching anything."""

    values = os.environ if environment is None else environment
    candidates: list[Path] = []

    for name in ("PROGRAMFILES", "ProgramW6432", "PROGRAMFILES(X86)"):
        root = values.get(name)
        if root:
            candidates.append(Path(root) / "Unity Hub" / "Unity Hub.exe")

    local_app_data = _environment_value(values, "LOCALAPPDATA", "LocalAppData")
    if local_app_data:
        local_root = Path(local_app_data)
        candidates.append(local_root / "Programs" / "Unity Hub" / "Unity Hub.exe")
        candidates.append(local_root / "Unity Hub" / "Unity Hub.exe")

    for executable in ("Unity Hub.exe", "UnityHub.exe", "Unity Hub"):
        resolved = shutil.which(executable)
        if resolved:
            candidates.append(Path(resolved))

    return tuple(path for path in _deduplicate(candidates) if path.is_file())


def discover_unity_editor_executables(
    environment: Mapping[str, str] | None = None,
) -> tuple[Path, ...]:
    """Find Editors installed in the conventional Unity Hub directory."""

    values = os.environ if environment is None else environment
    roots: list[Path] = []
    for name in ("PROGRAMFILES", "ProgramW6432", "PROGRAMFILES(X86)"):
        root = values.get(name)
        if root:
            roots.append(Path(root) / "Unity" / "Hub" / "Editor")
    local_app_data = _environment_value(values, "LOCALAPPDATA", "LocalAppData")
    if local_app_data:
        roots.append(Path(local_app_data) / "UnityHub" / "Editor")

    candidates: list[Path] = []
    for root in _deduplicate(roots):
        if not root.is_dir():
            continue
        try:
            versions = sorted(root.iterdir(), key=lambda item: item.name, reverse=True)
        except OSError:
            continue
        for version in versions:
            candidates.append(version / "Editor" / "Unity.exe")

    return tuple(path for path in _deduplicate(candidates) if path.is_file())


def _expected_names(kind: ExecutableKind) -> frozenset[str]:
    if kind == "hub":
        return frozenset({"unity hub.exe", "unityhub.exe", "unity hub"})
    return frozenset({"unity.exe", "unity"})


def is_expected_executable(path: Path, kind: ExecutableKind) -> bool:
    """Return whether a selected file has a recognizable Unity executable name."""

    return path.name.casefold() in _expected_names(kind)


def inspect_executable(
    path: Path | None,
    kind: ExecutableKind,
) -> ExecutableState:
    """Classify a path using metadata only; no binary or license bytes are read."""

    if path is None:
        return "not_configured"
    try:
        if not path.exists():
            return "missing"
        if not path.is_file() or not is_expected_executable(path, kind):
            return "invalid"
    except OSError:
        return "invalid"
    return "available"


def _preferred_path(
    configured: str | os.PathLike[str] | None,
    discovered: Sequence[Path],
) -> Path | None:
    configured_path = normalize_external_path(configured)
    if configured_path is not None:
        return configured_path
    return discovered[0] if discovered else None


def build_unity_integration_snapshot(
    configured_hub: str | os.PathLike[str] | None = None,
    configured_editor: str | os.PathLike[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> UnityIntegrationSnapshot:
    """Build a deterministic preflight snapshot from config and the filesystem."""

    hub_path = _preferred_path(
        configured_hub,
        discover_unity_hub_executables(environment),
    )
    editor_path = _preferred_path(
        configured_editor,
        discover_unity_editor_executables(environment),
    )
    return UnityIntegrationSnapshot(
        hub_path=hub_path,
        editor_path=editor_path,
        hub_state=inspect_executable(hub_path, "hub"),
        editor_state=inspect_executable(editor_path, "editor"),
    )


__all__ = [
    "ExecutableState",
    "UNITY_HUB_DOCS_URL",
    "UNITY_ID_URL",
    "UnityIntegrationSnapshot",
    "build_unity_integration_snapshot",
    "discover_unity_editor_executables",
    "discover_unity_hub_executables",
    "inspect_executable",
    "is_expected_executable",
    "normalize_external_path",
]
