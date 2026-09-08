"""Versioned persistence for the E06 NavMesh source and derived bake metadata."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from src.core.navmesh_2d import NavLink, NavMeshSource, NavObstacle, NavRegion

FORMAT_ID = "neoeng-d-trace-navmesh-2d"


def save_navmesh(source: NavMeshSource, path: str | os.PathLike[str]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"format_id": FORMAT_ID, "schema_version": 1, **source.canonical_dict()}
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


def load_navmesh(path: str | os.PathLike[str]) -> NavMeshSource:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("format_id") != FORMAT_ID or payload.get("schema_version") != 1:
        raise ValueError("[unsupported_navmesh_format] unsupported NavMesh document")
    return NavMeshSource(
        regions=[
            NavRegion(item["id"], tuple(item["bounds"])) for item in payload["regions"]
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


__all__ = ["FORMAT_ID", "load_navmesh", "save_navmesh"]
