"""Compatibility imports for the historical physics manager module."""

from src.collision.manager import (
    CollisionObject,
    CollisionResult,
    StaticCollisionManager,
)

PhysicsObject = CollisionObject
PhysicsManager = StaticCollisionManager

__all__ = [
    "CollisionObject",
    "CollisionResult",
    "PhysicsManager",
    "PhysicsObject",
    "StaticCollisionManager",
]
