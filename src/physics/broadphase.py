"""Implementation of :mod:`src.physics.broadphase`.

Implementation preserved in the single ``src`` source tree.
"""

"""
Broadphase Collision Detection
Implements uniform grid broadphase for efficient collision candidate finding.
"""

from typing import Any, Dict, List, Set, Tuple


class AABB:
    """Axis-Aligned Bounding Box for collision detection."""

    def __init__(self, min_x: float, min_y: float, max_x: float, max_y: float):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center_x(self) -> float:
        return (self.min_x + self.max_x) / 2.0

    @property
    def center_y(self) -> float:
        return (self.min_y + self.max_y) / 2.0

    def overlaps(self, other: "AABB") -> bool:
        """Check if this AABB overlaps with another."""
        return (
            self.min_x < other.max_x
            and self.max_x > other.min_x
            and self.min_y < other.max_y
            and self.max_y > other.min_y
        )

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside this AABB."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    @staticmethod
    def from_polygon(polygon: List[Tuple[float, float]]) -> "AABB":
        """Create AABB from polygon vertices."""
        if not polygon:
            return AABB(0, 0, 0, 0)

        min_x = min(p[0] for p in polygon)
        max_x = max(p[0] for p in polygon)
        min_y = min(p[1] for p in polygon)
        max_y = max(p[1] for p in polygon)

        return AABB(min_x, min_y, max_x, max_y)


class BroadPhaseSAP:
    """
    Sweep and Prune broadphase collision detection.
    Efficient for axis-aligned scenarios.
    """

    def __init__(self):
        # store intervals (min_x, max_x, id)
        self._intervals: Dict[int, Tuple[float, float]] = {}

    def insert(self, body_id: int, aabb: AABB):
        self._intervals[body_id] = (aabb.min_x, aabb.max_x)

    def update(self, body_id: int, aabb: AABB):
        self._intervals[body_id] = (aabb.min_x, aabb.max_x)

    def remove(self, body_id: int):
        self._intervals.pop(body_id, None)

    def potential_pairs(self):
        # naive O(n log n) approach: sort by min_x and sweep
        items = sorted(self._intervals.items(), key=lambda kv: kv[1][0])
        active = []
        pairs = []
        for id_i, (minx, maxx) in items:
            # remove inactive
            active = [(j, jmax) for j, jmax in active if jmax >= minx]
            for j, jmax in active:
                pairs.append((j, id_i))
            active.append((id_i, maxx))
        return pairs


class UniformGridBroadPhase:
    """
    Uniform grid broadphase collision detection.
    """

    def __init__(self, grid_cell_size: int = 64):
        """
        Initialize the broadphase with given cell size.
        """
        self.grid_cell_size = grid_cell_size
        # (grid_x, grid_y) -> set of object_ids
        self.grid: Dict[Tuple[int, int], Set[Any]] = {}
        self.objects: Dict[Any, AABB] = {}  # object_id -> AABB

    def _get_grid_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        return (int(x // self.grid_cell_size), int(y // self.grid_cell_size))

    def _get_cells_for_aabb(self, aabb: AABB) -> List[Tuple[int, int]]:
        """Get all grid cells that this AABB overlaps."""
        cells = []

        # Find min and max grid coordinates
        min_grid_x = int(aabb.min_x // self.grid_cell_size)
        max_grid_x = int(aabb.max_x // self.grid_cell_size)
        min_grid_y = int(aabb.min_y // self.grid_cell_size)
        max_grid_y = int(aabb.max_y // self.grid_cell_size)

        # Handle edge case where AABB is smaller than one cell
        if max_grid_x < min_grid_x:
            max_grid_x = min_grid_x
        if max_grid_y < min_grid_y:
            max_grid_y = min_grid_y

        # Collect all cells this AABB touches
        for grid_x in range(min_grid_x, max_grid_x + 1):
            for grid_y in range(min_grid_y, max_grid_y + 1):
                cells.append((grid_x, grid_y))

        return cells

    def insert(self, obj_id: Any, aabb: AABB):
        """
        Insert an object into the broadphase.
        """
        # Remove from old position if it exists
        if obj_id in self.objects:
            self.remove(obj_id)

        # Store the AABB
        self.objects[obj_id] = aabb

        # Add to all relevant grid cells
        cells = self._get_cells_for_aabb(aabb)
        for cell in cells:
            if cell not in self.grid:
                self.grid[cell] = set()
            self.grid[cell].add(obj_id)

    def update(self, obj_id: Any, new_aabb: AABB):
        """
        Update an object's position in the broadphase.
        """
        self.insert(obj_id, new_aabb)  # insert handles removal of old position

    def remove(self, obj_id: Any):
        """
        Remove an object from the broadphase.
        """
        if obj_id not in self.objects:
            return

        # Remove from all grid cells
        old_aabb = self.objects[obj_id]
        cells = self._get_cells_for_aabb(old_aabb)

        for cell in cells:
            if cell in self.grid and obj_id in self.grid[cell]:
                self.grid[cell].remove(obj_id)
                # Clean up empty cells
                if not self.grid[cell]:
                    del self.grid[cell]

        # Remove from objects dict
        del self.objects[obj_id]

    def query(self, aabb: AABB) -> Set[Any]:
        """
        Query for all objects whose AABBs overlap with the given AABB.
        """
        candidates = set()
        cells = self._get_cells_for_aabb(aabb)

        # Collect all objects from the relevant cells
        for cell in cells:
            if cell in self.grid:
                candidates.update(self.grid[cell])

        return candidates

    def get_all_pairs(self) -> List[Tuple[Any, Any]]:
        """
        Get all potential collision pairs.
        Optimized version: Handles IDs directly without attribute
        access overhead.
        """
        pairs = []
        processed = set()

        # For each cell, check all pairs within that cell
        for cell_objects in self.grid.values():
            obj_list = list(cell_objects)
            count = len(obj_list)

            for i in range(count):
                id1 = obj_list[i]
                for j in range(i + 1, count):
                    id2 = obj_list[j]

                    # CORREÇÃO: id1 e id2 já são os IDs (strings), não objetos.
                    # Comparação direta de strings é rápida em Python.
                    if id1 < id2:
                        pair_key = (id1, id2)
                    else:
                        pair_key = (id2, id1)

                    if pair_key not in processed:
                        pairs.append((id1, id2))
                        processed.add(pair_key)

        return pairs

    def clear(self):
        """Clear all objects from the broadphase."""
        self.grid.clear()
        self.objects.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the broadphase."""
        total_objects = len(self.objects)
        occupied_cells = len(self.grid)
        avg_objects_per_cell = (
            total_objects / occupied_cells if occupied_cells > 0 else 0
        )

        return {
            "total_objects": total_objects,
            "occupied_cells": occupied_cells,
            "avg_objects_per_cell": avg_objects_per_cell,
            "grid_cell_size": self.grid_cell_size,
        }
