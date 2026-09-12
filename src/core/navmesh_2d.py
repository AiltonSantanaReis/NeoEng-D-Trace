"""Deterministic, surface-only 2D navigation source and bake."""

from __future__ import annotations

import hashlib
import heapq
import json
import math
from dataclasses import dataclass, field


class NavMeshError(ValueError):
    """Raised when navigation input or a derived bake is not usable."""


def _finite(value: float, code: str) -> float:
    if not math.isfinite(value):
        raise NavMeshError(f"[{code}] value must be finite")
    return float(value)


def _rect(rect: tuple[float, float, float, float], code: str) -> tuple[float, ...]:
    if len(rect) != 4:
        raise NavMeshError(f"[{code}] rectangle requires four values")
    x, y, width, height = (_finite(item, code) for item in rect)
    if width <= 0 or height <= 0:
        raise NavMeshError(f"[{code}] rectangle must be positive")
    return x, y, width, height


@dataclass(frozen=True)
class NavRegion:
    id: str
    bounds: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if not self.id or len(self.id) > 64:
            raise NavMeshError("[invalid_region_id] region id is required")
        object.__setattr__(self, "bounds", _rect(self.bounds, "invalid_region"))


@dataclass(frozen=True)
class NavObstacle:
    id: str
    bounds: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if not self.id or len(self.id) > 64:
            raise NavMeshError("[invalid_obstacle_id] obstacle id is required")
        object.__setattr__(self, "bounds", _rect(self.bounds, "invalid_obstacle"))


@dataclass(frozen=True)
class NavLink:
    id: str
    start: tuple[float, float]
    end: tuple[float, float]

    def __post_init__(self) -> None:
        if not self.id:
            raise NavMeshError("[invalid_link_id] link id is required")
        for point in (self.start, self.end):
            if len(point) != 2 or not all(math.isfinite(value) for value in point):
                raise NavMeshError("[invalid_link] link points must be finite")


@dataclass
class NavMeshSource:
    regions: list[NavRegion] = field(default_factory=list)
    obstacles: list[NavObstacle] = field(default_factory=list)
    links: list[NavLink] = field(default_factory=list)
    agent_radius: float = 8.0
    cell_size: float = 16.0
    revision: int = 0

    def __post_init__(self) -> None:
        if self.agent_radius <= 0 or not math.isfinite(self.agent_radius):
            raise NavMeshError("[invalid_agent_radius] agent radius must be positive")
        if self.cell_size <= 0 or not math.isfinite(self.cell_size):
            raise NavMeshError("[invalid_cell_size] cell size must be positive")
        self.agent_radius = float(self.agent_radius)
        self.cell_size = float(self.cell_size)
        self._assert_unique_ids()

    def _assert_unique_ids(self) -> None:
        ids = [item.id for item in self.regions]
        ids.extend(item.id for item in self.obstacles)
        ids.extend(item.id for item in self.links)
        if len(ids) != len(set(ids)):
            raise NavMeshError("[duplicate_navigation_id] ids must be unique")

    def touch(self) -> None:
        self.revision += 1

    def canonical_dict(self) -> dict[str, object]:
        self._assert_unique_ids()
        return {
            "regions": [
                {"id": item.id, "bounds": list(item.bounds)}
                for item in sorted(self.regions, key=lambda value: value.id)
            ],
            "obstacles": [
                {"id": item.id, "bounds": list(item.bounds)}
                for item in sorted(self.obstacles, key=lambda value: value.id)
            ],
            "links": [
                {"id": item.id, "start": list(item.start), "end": list(item.end)}
                for item in sorted(self.links, key=lambda value: value.id)
            ],
            "agent_radius": self.agent_radius,
            "cell_size": self.cell_size,
            "revision": self.revision,
        }

    def source_hash(self) -> str:
        payload = json.dumps(
            self.canonical_dict(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NavMeshBake:
    algorithm_version: str
    source_hash: str
    source_revision: int
    nodes: tuple[tuple[int, int], ...]
    cell_size: float

    def is_obsolete(self, source: NavMeshSource) -> bool:
        return (
            source.revision != self.source_revision
            or source.source_hash() != self.source_hash
        )


@dataclass(frozen=True)
class NavPath:
    points: tuple[tuple[float, float], ...]
    bake_hash: str


def _inside(
    point: tuple[float, float], bounds: tuple[float, float, float, float]
) -> bool:
    x, y = point
    left, top, width, height = bounds
    return left <= x <= left + width and top <= y <= top + height


def _expanded_hit(
    point: tuple[float, float], obstacle: NavObstacle, margin: float
) -> bool:
    x, y, width, height = obstacle.bounds
    return (
        x - margin <= point[0] <= x + width + margin
        and y - margin <= point[1] <= y + height + margin
    )


def bake_navmesh(source: NavMeshSource) -> NavMeshBake:
    if not source.regions:
        raise NavMeshError("[no_walkable_region] at least one region is required")
    region = source.regions[0]
    x, y, width, height = region.bounds
    cols = max(1, math.ceil(width / source.cell_size))
    rows = max(1, math.ceil(height / source.cell_size))
    nodes: list[tuple[int, int]] = []
    for row in range(rows):
        for col in range(cols):
            center = (
                x + (col + 0.5) * source.cell_size,
                y + (row + 0.5) * source.cell_size,
            )
            if not any(
                _expanded_hit(center, obstacle, source.agent_radius)
                for obstacle in source.obstacles
            ):
                nodes.append((col, row))
    if not nodes:
        raise NavMeshError("[no_walkable_nodes] agent cannot fit in the region")
    return NavMeshBake(
        "grid-surface-v1",
        source.source_hash(),
        source.revision,
        tuple(nodes),
        source.cell_size,
    )


def _nearest_node(point: tuple[float, float], bake: NavMeshBake) -> tuple[int, int]:
    return min(
        bake.nodes,
        key=lambda node: (
            (node[0] * bake.cell_size - point[0]) ** 2
            + (node[1] * bake.cell_size - point[1]) ** 2,
            node,
        ),
    )


def find_path(
    source: NavMeshSource,
    bake: NavMeshBake,
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> NavPath:
    if bake.is_obsolete(source):
        raise NavMeshError("[obsolete_bake] bake must be rebuilt after source changes")
    region = source.regions[0]
    if not _inside(origin, region.bounds) or not _inside(destination, region.bounds):
        raise NavMeshError(
            "[point_outside_region] origin and destination must be walkable"
        )
    start = _nearest_node(origin, bake)
    goal = _nearest_node(destination, bake)
    node_set = set(bake.nodes)
    if start not in node_set or goal not in node_set:
        raise NavMeshError("[no_path] no walkable node is available")
    frontier: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost: dict[tuple[int, int], float] = {start: 0.0}
    while frontier:
        _, node = heapq.heappop(frontier)
        if node == goal:
            break
        for neighbor in sorted(
            (
                candidate
                for candidate in (
                    (node[0] + 1, node[1]),
                    (node[0] - 1, node[1]),
                    (node[0], node[1] + 1),
                    (node[0], node[1] - 1),
                )
                if candidate in node_set
            )
        ):
            next_cost = cost[node] + 1
            if next_cost < cost.get(neighbor, math.inf):
                cost[neighbor] = next_cost
                priority = (
                    next_cost + abs(goal[0] - neighbor[0]) + abs(goal[1] - neighbor[1])
                )
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = node
    if goal not in came_from:
        raise NavMeshError("[no_path] no connected path exists")
    cells: list[tuple[int, int]] = []
    cursor: tuple[int, int] | None = goal
    while cursor is not None:
        cells.append(cursor)
        cursor = came_from[cursor]
    cells.reverse()
    points = tuple(
        ((col + 0.5) * bake.cell_size, (row + 0.5) * bake.cell_size)
        for col, row in cells
    )
    return NavPath(points, bake.source_hash)


__all__ = [
    "NavLink",
    "NavMeshBake",
    "NavMeshError",
    "NavMeshSource",
    "NavObstacle",
    "NavPath",
    "NavRegion",
    "bake_navmesh",
    "find_path",
]
