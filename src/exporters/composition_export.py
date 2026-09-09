"""Deterministic package export for a complete 2D/2.5D authored scene.

The authoring panels persist independent documents by design.  E11 needs one
portable handoff that proves those documents belong to the same composition,
without pretending that a loose collection of JSON files is an engine scene.
This module validates every required document, copies it into one package and
binds each component by size and SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.exporters.scene_authoring_export import (
    SceneAuthoringExportError,
    build_scene_authoring_export,
)
from src.persistence.navmesh_io import load_navmesh
from src.persistence.scene_authoring_io import load_scene_authoring_v2
from src.persistence.scenario_collider_io import load_colliders
from src.persistence.tilemap_io import load_tilemap

COMPOSITION_FORMAT_ID = "neoeng-d-trace-composition-package"
COMPOSITION_SCHEMA_VERSION = 1


class CompositionExportError(ValueError):
    """Raised when a composition cannot be exported safely."""


@dataclass(frozen=True)
class CompositionInputs:
    """Project-relative sources required for the E11 composition package."""

    scene: Path
    tilemap: Path
    colliders: Path
    navmesh: Path
    runtime_bundle: Path | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _copy_bound(source: Path, destination: Path, kind: str) -> dict[str, Any]:
    if not source.is_file():
        raise CompositionExportError(f"missing composition component: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "kind": kind,
        "path": destination.name,
        "bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
        "required": True,
    }


def _safe_asset_path(value: str) -> Path:
    relative = Path(value)
    if (
        relative.is_absolute()
        or not value
        or "\\" in value
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise CompositionExportError("scene asset path is unsafe")
    return relative


def _validate_json_file(path: Path, kind: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CompositionExportError(f"invalid {kind} document: {path}") from exc


def _validate_inputs(inputs: CompositionInputs) -> dict[str, Any]:
    try:
        scene = load_scene_authoring_v2(inputs.scene)
        tilemap = load_tilemap(inputs.tilemap)
        colliders = load_colliders(inputs.colliders)
        navmesh = load_navmesh(inputs.navmesh)
    except Exception as exc:
        raise CompositionExportError(
            f"composition input validation failed: {exc}"
        ) from exc

    scene_exports: dict[str, Any] = {}
    for target in ("godot", "unity"):
        try:
            scene_exports[target] = build_scene_authoring_export(scene, target=target)
        except SceneAuthoringExportError as exc:
            raise CompositionExportError(
                f"scene export validation failed for {target}: {exc}"
            ) from exc

    runtime_payload = None
    if inputs.runtime_bundle is not None:
        runtime_payload = _validate_json_file(inputs.runtime_bundle, "runtime bundle")
        if not isinstance(runtime_payload, dict):
            raise CompositionExportError("runtime bundle must be a JSON object")

    return {
        "scene": scene,
        "scene_exports": scene_exports,
        "tilemap": tilemap,
        "colliders": colliders,
        "navmesh": navmesh,
        "runtime_payload": runtime_payload,
    }


def build_composition_package(
    inputs: CompositionInputs,
    destination: str | os.PathLike[str],
) -> dict[str, Any]:
    """Validate and write one non-overwriting composition package."""

    target = Path(destination)
    if target.exists():
        raise CompositionExportError(
            f"composition destination already exists: {target}"
        )
    target.mkdir(parents=True)
    validated = _validate_inputs(inputs)
    components: list[dict[str, Any]] = []

    for target_name, payload in validated["scene_exports"].items():
        path = target / f"scene-{target_name}.runtime.json"
        path.write_bytes(_canonical_json(payload))
        components.append(
            {
                "kind": f"scene-export-{target_name}",
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "required": True,
            }
        )

    for source, name, kind in (
        (inputs.tilemap, "tilemap.json", "tilemap"),
        (inputs.colliders, "colliders.json", "colliders"),
        (inputs.navmesh, "navmesh.json", "navmesh"),
    ):
        components.append(_copy_bound(source, target / name, kind))

    scene_root = inputs.scene.parent
    for asset in validated["scene"].assets:
        relative = _safe_asset_path(asset.path)
        source = scene_root / relative
        asset_component = _copy_bound(source, target / relative, "asset")
        asset_component["path"] = relative.as_posix()
        components.append(asset_component)

    if inputs.runtime_bundle is not None:
        components.append(
            _copy_bound(
                inputs.runtime_bundle,
                target / "runtime-adapters.json",
                "runtime-adapters",
            )
        )

    manifest: dict[str, Any] = {
        "format_id": COMPOSITION_FORMAT_ID,
        "schema_version": COMPOSITION_SCHEMA_VERSION,
        "generator": {"id": "neoeng_d_trace", "version": "0.3.0"},
        "components": sorted(components, key=lambda item: item["path"]),
        "capabilities": {
            "scene": "native-scene-export",
            "tilemap": "validated-authored-document",
            "colliders": "validated-authored-document",
            "navmesh": "validated-authored-document",
            "runtime-adapters": "optional-runtime-bundle",
        },
    }
    (target / "composition.json").write_bytes(_canonical_json(manifest))
    return manifest


def validate_composition_package(package: str | os.PathLike[str]) -> dict[str, Any]:
    """Verify manifest bindings and re-validate every required component."""

    root = Path(package)
    manifest_path = root / "composition.json"
    if not manifest_path.is_file():
        raise CompositionExportError("composition manifest is missing")
    payload = _validate_json_file(manifest_path, "composition manifest")
    if (
        not isinstance(payload, dict)
        or payload.get("format_id") != COMPOSITION_FORMAT_ID
        or payload.get("schema_version") != COMPOSITION_SCHEMA_VERSION
        or not isinstance(payload.get("components"), list)
    ):
        raise CompositionExportError("composition manifest schema is invalid")
    for component in payload["components"]:
        if not isinstance(component, dict) or not component.get("required"):
            raise CompositionExportError("composition component record is invalid")
        path = root / Path(str(component.get("path", "")))
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise CompositionExportError(
                "composition component path is unsafe or missing"
            ) from exc
        if not path.is_file() or path.is_symlink():
            raise CompositionExportError(
                "composition component path is unsafe or missing"
            )
        if path.stat().st_size != component.get("bytes") or _sha256(
            path
        ) != component.get("sha256"):
            raise CompositionExportError(
                f"composition component hash mismatch: {path.name}"
            )
        kind = component.get("kind")
        if kind == "tilemap":
            load_tilemap(path)
        elif kind == "colliders":
            load_colliders(path)
        elif kind == "navmesh":
            load_navmesh(path)
        elif kind.startswith("scene-export-"):
            _validate_json_file(path, kind)
        elif kind == "runtime-adapters":
            _validate_json_file(path, kind)
        elif kind == "asset":
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bin"}:
                raise CompositionExportError("unsupported composition asset type")
        else:
            raise CompositionExportError(f"unknown composition component: {kind}")
    return payload


__all__ = [
    "COMPOSITION_FORMAT_ID",
    "COMPOSITION_SCHEMA_VERSION",
    "CompositionExportError",
    "CompositionInputs",
    "build_composition_package",
    "validate_composition_package",
]
