# src/physics/physics_manager.py
"""
Physics Manager
Manages physics objects and collision detection using
broadphase + narrow-phase.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .broadphase import AABB, UniformGridBroadPhase
from .sat2d import sat_polygon_vs_polygon


@dataclass
class Body:
    id: int
    verts_px: List[Tuple[float, float]]  # editor coords in pixels
    is_static: bool
    metadata: dict


class PhysicsObject:
    """Represents a physics object with shape and collision properties."""

    def __init__(
        self,
        obj_id: Any,
        shape: List[Tuple[float, float]],
        position: Tuple[float, float] = (0.0, 0.0),
        metadata: Optional[dict] = None,
    ):
        """
        Initialize physics object.

        Args:
            obj_id: Unique identifier
            shape: List of (x, y) vertices in local coordinates
            position: World position offset
            metadata: Additional data
        """
        self.obj_id = obj_id
        self.shape = shape
        self.position = position
        self.metadata = metadata or {}
        self.aabb = self._calculate_aabb()

    def _calculate_aabb(self) -> AABB:
        """Calculate world-space AABB for this object."""
        if not self.shape:
            return AABB(0, 0, 0, 0)

        # Transform shape to world coordinates
        world_shape = [
            (x + self.position[0], y + self.position[1]) for x, y in self.shape
        ]

        return AABB.from_polygon(world_shape)

    def update_position(self, new_position: Tuple[float, float]):
        """Update object position and recalculate AABB."""
        self.position = new_position
        self.aabb = self._calculate_aabb()

    def get_world_shape(self) -> List[Tuple[float, float]]:
        """Get shape in world coordinates."""
        return [(x + self.position[0], y + self.position[1]) for x, y in self.shape]


class CollisionResult:
    """Result of a collision test."""

    def __init__(
        self,
        obj1_id: Any,
        obj2_id: Any,
        colliding: bool,
        mtv: Optional[Tuple[float, float]] = None,
    ):
        self.obj1_id = obj1_id
        self.obj2_id = obj2_id
        self.colliding = colliding
        self.mtv = mtv  # Minimum Translation Vector

    def __repr__(self):
        return (
            f"CollisionResult({self.obj1_id} vs {self.obj2_id}: "
            f"{self.colliding}, MTV={self.mtv})"
        )


class PhysicsManager:
    """
    Physics manager that handles object registration and collision detection.
    """

    def __init__(
        self,
        grid_cell_size: int = 64,
        gravity=(0, -9.81),
        pixels_per_meter: float = 100.0,
        fixed_dt: float = 1 / 60.0,
    ):
        self.broadphase = UniformGridBroadPhase(grid_cell_size)
        self.objects: Dict[Any, PhysicsObject] = {}
        self.collision_results: List[CollisionResult] = []
        self.gravity = gravity
        self.pixels_per_meter = float(pixels_per_meter)
        self.fixed_dt = fixed_dt
        self._accumulator = 0.0
        self._callbacks: List[Callable] = []
        self._next_id = 1
        # backend placeholder (Box2D world or custom)
        self.backend = None

    def add_body(
        self,
        verts_px: List[Tuple[float, float]],
        is_static: bool = False,
        metadata: Optional[dict] = None,
    ) -> int:
        if len(verts_px) < 3:
            raise ValueError("polygon must have at least 3 points")
        # scale to meters for backend
        # verts_m = [
        #     (x / self.pixels_per_meter, y / self.pixels_per_meter)
        #     for x, y in verts_px
        # ]
        # here validate and decompose if needed (call convex_decomp)
        body_id = self._next_id if hasattr(self, "_next_id") else 1
        if not hasattr(self, "_next_id"):
            self._next_id = 1
        self._next_id += 1
        # Use existing register method
        self.register(body_id, verts_px, (0.0, 0.0))
        # Add metadata
        if metadata:
            self.objects[body_id].metadata = metadata
        return body_id

    def remove_body(self, body_id: int):
        self.unregister(body_id)

    def step(self, dt: float):
        # accumulate and step at fixed dt for deterministic behavior
        self._accumulator += dt
        steps = 0
        while self._accumulator >= self.fixed_dt:
            if self.backend:
                self.backend.step(self.fixed_dt)
            # else: perform collision detection
            self.batch_test()
            self._accumulator -= self.fixed_dt
            steps += 1
        return steps

    def register_collision_callback(self, fn: Callable):
        self._callbacks.append(fn)

    def register(
        self,
        obj_id: Any,
        shape: List[Tuple[float, float]],
        position: Tuple[float, float] = (0.0, 0.0),
        metadata: Optional[dict] = None,
    ):
        if obj_id in self.objects:
            self.unregister(obj_id)

        obj = PhysicsObject(obj_id, shape, position, metadata)
        self.objects[obj_id] = obj
        self.broadphase.insert(obj_id, obj.aabb)

    def unregister(self, obj_id: Any):
        if obj_id in self.objects:
            self.broadphase.remove(obj_id)
            del self.objects[obj_id]

    def update_position(self, obj_id: Any, new_position: Tuple[float, float]):
        if obj_id not in self.objects:
            return

        obj = self.objects[obj_id]
        obj.update_position(new_position)
        self.broadphase.update(obj_id, obj.aabb)

    def batch_test(self) -> List[CollisionResult]:
        """
        Perform batch collision testing on all registered objects.
        """
        self.collision_results.clear()

        candidate_pairs = self.broadphase.get_all_pairs()

        for obj1_id, obj2_id in candidate_pairs:
            if obj1_id not in self.objects or obj2_id not in self.objects:
                continue

            obj1 = self.objects[obj1_id]
            obj2 = self.objects[obj2_id]

            shape1 = obj1.get_world_shape()
            shape2 = obj2.get_world_shape()

            colliding, mtv = sat_polygon_vs_polygon(shape1, shape2)

            result = CollisionResult(obj1_id, obj2_id, colliding, mtv)
            self.collision_results.append(result)

        return self.collision_results.copy()

    def query_collisions(self, obj_id: Any) -> List[CollisionResult]:
        if obj_id not in self.objects:
            return []

        query_aabb = self.objects[obj_id].aabb
        candidates = self.broadphase.query(query_aabb)

        results = []
        query_shape = self.objects[obj_id].get_world_shape()

        for candidate_id in candidates:
            if candidate_id == obj_id:
                continue

            if candidate_id not in self.objects:
                continue

            candidate_shape = self.objects[candidate_id].get_world_shape()
            colliding, mtv = sat_polygon_vs_polygon(query_shape, candidate_shape)

            if colliding:
                result = CollisionResult(obj_id, candidate_id, True, mtv)
                results.append(result)

        return results

    def get_object(self, obj_id: Any) -> Optional[PhysicsObject]:
        return self.objects.get(obj_id)

    def get_all_objects(self) -> List[PhysicsObject]:
        return list(self.objects.values())

    def clear(self):
        self.objects.clear()
        self.broadphase.clear()
        self.collision_results.clear()

    def get_stats(self) -> Dict[str, Any]:
        broadphase_stats = self.broadphase.get_stats()
        total_collisions = sum(
            1 for result in self.collision_results if result.colliding
        )

        return {
            **broadphase_stats,
            "total_collision_tests": len(self.collision_results),
            "total_collisions_found": total_collisions,
            "collision_rate": (
                total_collisions / len(self.collision_results)
                if self.collision_results
                else 0.0
            ),
        }
