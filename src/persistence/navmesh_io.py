"""Versioned persistence for the E06 NavMesh source and derived bake metadata."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from src.core.navmesh_2d import (
    NavLink,
    NavMeshBake,
    NavMeshSource,
    NavObstacle,
    NavRegion,
)

FORMAT_ID = "neoeng-d-trace-navmesh-2d"


def _bake_payload(bake: NavMeshBake | None, source: NavMeshSource) -> dict[str, object] | None:
    if bake is None or bake.is_obsolete(source):
        return None
    return {
        "algorithm_version": bake.algorithm_version,
        "source_hash": bake.source_hash,
        "source_revision": bake.source_revision,
        "nodes": [list(node) for node in bake.nodes],
        "cell_size": bake.cell_size,
    }


def save_navmesh(
    source: NavMeshSource,
    path: str | os.PathLike[str],
    *,
    bake: NavMeshBake | None = None,
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"format_id": FORMAT_ID, "schema_version": 1, **source.canonical_dict()}
    persisted_bake = _bake_payload(bake, source)
    if persisted_bake is not None:
        payload["bake"] = persisted_bake
    descriptor, temporary = tempfile.mkstemp(
        prefix=".navmesh-", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    return destination


def _load_source(payload: dict[str, object]) -> NavMeshSource:
    return NavMeshSource(
        regions=[
            NavRegion(item["id"], tuple(item["bounds"]))
            for item in payload["regions"]
        ],
        obstacles=[
            NavObstacle(item["id"], tuple(item["bounds"]))
            for item in payload["obstacles"]
        ],
        links=[
            NavLink(item["id"], tuple(item["start"]), tuple(item["end"]))
            for item in payload.get("links", [])
        ],
        agent_radius=float(payload["agent_radius"]),
        cell_size=float(payload["cell_size"]),
        revision=int(payload.get("revision", 0)),
    )


def _load_bake(payload: object, source: NavMeshSource) -> NavMeshBake | None:
    if not isinstance(payload, dict):
        return None
    try:
        nodes = tuple(tuple(int(value) for value in node) for node in payload["nodes"])
        bake = NavMeshBake(
            str(payload["algorithm_version"]),
            str(payload["source_hash"]),
            int(payload["source_revision"]),
            nodes,
            float(payload["cell_size"]),
        )
    except (KeyError, TypeError, ValueError):
        return None
    return bake if not bake.is_obsolete(source) else None


def load_navmesh(path: str | os.PathLike[str]) -> NavMeshSource:
    source, _bake = load_navmesh_with_bake(path)
    return source


def load_navmesh_with_bake(
    path: str | os.PathLike[str],
) -> tuple[NavMeshSource, NavMeshBake | None]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("format_id") != FORMAT_ID or payload.get("schema_version") != 1:
        raise ValueError("[unsupported_navmesh_format] unsupported NavMesh document")
    source = _load_source(payload)
    return source, _load_bake(payload.get("bake"), source)


__all__ = ["FORMAT_ID", "load_navmesh", "load_navmesh_with_bake", "save_navmesh"]
