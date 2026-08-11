"""Static polygon collision service used by the editor UI."""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .broadphase import AABB, UniformGridBroadPhase
from .sat2d import polygons_overlap, validate_polygon

Point = Tuple[float, float]


@dataclass
class CollisionObject:
    """Validated immutable polygon registered for static overlap queries."""

    obj_id: Any
    shape: tuple[Point, ...]
    position: Point = (0.0, 0.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    aabb: AABB = field(init=False)

    def __post_init__(self) -> None:
        self.position = _validate_position(self.position)
        self.aabb = AABB.from_polygon(self.get_world_shape())

    def update_position(self, new_position: Point) -> None:
        self.position = _validate_position(new_position)
        self.aabb = AABB.from_polygon(self.get_world_shape())

    def get_world_shape(self) -> List[Point]:
        return [(x + self.position[0], y + self.position[1]) for x, y in self.shape]


@dataclass(frozen=True)
class CollisionResult:
    """Observable result of one static polygon overlap test."""

    obj1_id: Any
    obj2_id: Any
    colliding: bool
    mtv: Optional[Point] = None


def _validate_identifier(obj_id: Any) -> None:
    try:
        hash(obj_id)
    except TypeError as exc:
        raise ValueError("Object identifier must be hashable") from exc


def _validate_position(position: Sequence[float]) -> Point:
    if len(position) != 2:
        raise ValueError("Position must contain two coordinates")
    try:
        canonical = (float(position[0]), float(position[1]))
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("Position coordinates must be numeric") from exc
    if not math.isfinite(canonical[0]) or not math.isfinite(canonical[1]):
        raise ValueError("Position coordinates must be finite")
    return canonical


class StaticCollisionManager:
    """Register polygons and perform deterministic static overlap queries."""

    def __init__(self, grid_cell_size: int = 64):
        if (
            isinstance(grid_cell_size, bool)
            or not isinstance(grid_cell_size, int)
            or grid_cell_size <= 0
        ):
            raise ValueError("grid_cell_size must be a positive integer")
        self.broadphase = UniformGridBroadPhase(grid_cell_size)
        self.objects: Dict[Any, CollisionObject] = {}
        self.collision_results: List[CollisionResult] = []
        self._registration_order: Dict[Any, int] = {}
        self._next_order = 0
        self._next_id = 1

    def add_shape(
        self,
        vertices: Sequence[Sequence[float]],
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> int:
        shape_id = self._next_id
        self._next_id += 1
        self.register(shape_id, vertices, metadata=metadata)
        return shape_id

    def add_body(
        self,
        verts_px: Sequence[Sequence[float]],
        is_static: bool = False,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> int:
        """Compatibility adapter; dynamic bodies are outside the product scope."""
        if not isinstance(is_static, bool):
            raise ValueError("is_static must be a boolean")
        return self.add_shape(verts_px, metadata)

    def remove_body(self, body_id: int) -> None:
        """Compatibility adapter for historical callers."""
        self.unregister(body_id)

    def register(
        self,
        obj_id: Any,
        shape: Sequence[Sequence[float]],
        position: Sequence[float] = (0.0, 0.0),
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        _validate_identifier(obj_id)
        canonical_shape = validate_polygon(shape)
        canonical_position = _validate_position(position)
        collision_object = CollisionObject(
            obj_id,
            canonical_shape,
            canonical_position,
            dict(metadata or {}),
        )
        if obj_id not in self._registration_order:
            self._registration_order[obj_id] = self._next_order
            self._next_order += 1
        if obj_id in self.objects:
            self.broadphase.remove(obj_id)
        self.objects[obj_id] = collision_object
        self.broadphase.insert(obj_id, collision_object.aabb)

    def unregister(self, obj_id: Any) -> None:
        if obj_id in self.objects:
            self.broadphase.remove(obj_id)
            del self.objects[obj_id]
            del self._registration_order[obj_id]

    def update_position(self, obj_id: Any, new_position: Sequence[float]) -> bool:
        if obj_id not in self.objects:
            return False
        collision_object = self.objects[obj_id]
        collision_object.update_position(_validate_position(new_position))
        self.broadphase.update(obj_id, collision_object.aabb)
        return True

    def _ordered_pairs(self) -> List[Tuple[Any, Any]]:
        ordered = []
        for first_id, second_id in self.broadphase.get_all_pairs():
            if self._registration_order[first_id] > self._registration_order[second_id]:
                first_id, second_id = second_id, first_id
            ordered.append((first_id, second_id))
        return sorted(
            ordered,
            key=lambda pair: (
                self._registration_order[pair[0]],
                self._registration_order[pair[1]],
            ),
        )

    def batch_test(self) -> List[CollisionResult]:
        self.collision_results = []
        for first_id, second_id in self._ordered_pairs():
            first = self.objects.get(first_id)
            second = self.objects.get(second_id)
            if first is None or second is None:
                continue
            colliding, mtv = polygons_overlap(
                first.get_world_shape(), second.get_world_shape()
            )
            self.collision_results.append(
                CollisionResult(first_id, second_id, colliding, mtv)
            )
        return self.collision_results.copy()

    def query_collisions(self, obj_id: Any) -> List[CollisionResult]:
        collision_object = self.objects.get(obj_id)
        if collision_object is None:
            return []
        candidate_ids = sorted(
            self.broadphase.query(collision_object.aabb) - {obj_id},
            key=self._registration_order.__getitem__,
        )
        results = []
        for candidate_id in candidate_ids:
            candidate = self.objects.get(candidate_id)
            if candidate is None:
                continue
            colliding, mtv = polygons_overlap(
                collision_object.get_world_shape(), candidate.get_world_shape()
            )
            if colliding:
                results.append(CollisionResult(obj_id, candidate_id, True, mtv))
        return results

    def get_object(self, obj_id: Any) -> Optional[CollisionObject]:
        return self.objects.get(obj_id)

    def get_all_objects(self) -> List[CollisionObject]:
        return list(self.objects.values())

    def clear(self) -> None:
        self.objects.clear()
        self.broadphase.clear()
        self.collision_results.clear()
        self._registration_order.clear()
        self._next_order = 0

    def get_stats(self) -> Dict[str, Any]:
        broadphase_stats = self.broadphase.get_stats()
        total_collisions = sum(result.colliding for result in self.collision_results)
        total_tests = len(self.collision_results)
        return {
            **broadphase_stats,
            "total_collision_tests": total_tests,
            "total_collisions_found": total_collisions,
            "collision_rate": total_collisions / total_tests if total_tests else 0.0,
        }
