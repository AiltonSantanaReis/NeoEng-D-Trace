"""
Tests for Broadphase and Physics Manager.
"""

import pytest
from src.physics.broadphase import UniformGridBroadPhase, AABB
from src.physics.physics_manager import PhysicsManager, PhysicsObject, CollisionResult


class TestBroadPhase:
    """Test cases for broadphase collision detection."""

    def test_aabb_creation(self):
        """Test AABB creation from polygon."""
        polygon = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
        aabb = AABB.from_polygon(polygon)

        assert aabb.min_x == 0.0
        assert aabb.max_x == 2.0
        assert aabb.min_y == 0.0
        assert aabb.max_y == 1.0
        assert aabb.width == 2.0
        assert aabb.height == 1.0

    def test_aabb_overlap(self):
        """Test AABB overlap detection."""
        aabb1 = AABB(0.0, 0.0, 2.0, 2.0)
        aabb2 = AABB(1.0, 1.0, 3.0, 3.0)
        aabb3 = AABB(3.0, 3.0, 4.0, 4.0)

        assert aabb1.overlaps(aabb2) is True
        assert aabb1.overlaps(aabb3) is False
        assert aabb2.overlaps(aabb3) is False

    def test_uniform_grid_insert(self):
        """Test inserting objects into uniform grid."""
        broadphase = UniformGridBroadPhase(grid_cell_size=64)

        # Insert a rectangle
        rect_aabb = AABB(0.0, 0.0, 100.0, 100.0)
        broadphase.insert("rect1", rect_aabb)

        assert "rect1" in broadphase.objects
        assert broadphase.objects["rect1"] == rect_aabb

        # Check grid cells (100x100 rectangle with 64x64 cells should cover multiple cells)
        # Should cover cells (0,0), (1,0), (0,1), (1,1)
        expected_cells = [(0, 0), (1, 0), (0, 1), (1, 1)]
        for cell in expected_cells:
            assert cell in broadphase.grid
            assert "rect1" in broadphase.grid[cell]

    def test_uniform_grid_query(self):
        """Test querying objects in broadphase."""
        broadphase = UniformGridBroadPhase(grid_cell_size=64)

        # Insert several rectangles
        broadphase.insert("rect1", AABB(0.0, 0.0, 50.0, 50.0))
        broadphase.insert("rect2", AABB(30.0, 30.0, 80.0, 80.0))
        broadphase.insert("rect3", AABB(200.0, 200.0, 250.0, 250.0))

        # Query overlapping area
        query_aabb = AABB(25.0, 25.0, 75.0, 75.0)
        candidates = broadphase.query(query_aabb)

        # Should find rect1 and rect2, but not rect3
        assert "rect1" in candidates
        assert "rect2" in candidates
        assert "rect3" not in candidates

    def test_uniform_grid_update(self):
        """Test updating object position in broadphase."""
        broadphase = UniformGridBroadPhase(grid_cell_size=64)

        # Insert and then update
        broadphase.insert("obj1", AABB(0.0, 0.0, 50.0, 50.0))
        broadphase.update("obj1", AABB(200.0, 200.0, 250.0, 250.0))

        # Old position should be empty
        old_query = broadphase.query(AABB(0.0, 0.0, 50.0, 50.0))
        assert "obj1" not in old_query

        # New position should contain object
        new_query = broadphase.query(AABB(200.0, 200.0, 250.0, 250.0))
        assert "obj1" in new_query

    def test_uniform_grid_remove(self):
        """Test removing objects from broadphase."""
        broadphase = UniformGridBroadPhase(grid_cell_size=64)

        broadphase.insert("obj1", AABB(0.0, 0.0, 50.0, 50.0))
        assert "obj1" in broadphase.objects

        broadphase.remove("obj1")
        assert "obj1" not in broadphase.objects

        # Query should not find removed object
        query = broadphase.query(AABB(0.0, 0.0, 50.0, 50.0))
        assert "obj1" not in query

    def test_uniform_grid_get_all_pairs(self):
        """Test getting all candidate pairs."""
        broadphase = UniformGridBroadPhase(grid_cell_size=64)

        # Insert objects that will be in the same cell
        broadphase.insert("obj1", AABB(0.0, 0.0, 30.0, 30.0))
        broadphase.insert("obj2", AABB(10.0, 10.0, 40.0, 40.0))
        broadphase.insert("obj3", AABB(200.0, 200.0, 230.0, 230.0))  # Different cell

        pairs = broadphase.get_all_pairs()

        # Should find pair (obj1, obj2) but not involving obj3
        pair_found = False
        for pair in pairs:
            if set(pair) == {"obj1", "obj2"}:
                pair_found = True
                break

        assert pair_found, f"Expected pair (obj1, obj2) not found in {pairs}"

        # obj3 should not be in any pairs
        for pair in pairs:
            assert "obj3" not in pair


class TestPhysicsManager:
    """Test cases for physics manager."""

    def test_register_object(self):
        """Test registering physics objects."""
        manager = PhysicsManager(grid_cell_size=64)

        # Register a rectangle
        rect_shape = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        manager.register("rect1", rect_shape, (10.0, 10.0))

        assert "rect1" in manager.objects
        obj = manager.objects["rect1"]
        assert obj.position == (10.0, 10.0)
        assert len(obj.shape) == 4

    def test_batch_test_no_collisions(self):
        """Test batch collision testing with no collisions."""
        manager = PhysicsManager(grid_cell_size=64)

        # Register two separate rectangles
        rect1 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        rect2 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

        manager.register("obj1", rect1, (0.0, 0.0))
        manager.register("obj2", rect2, (10.0, 10.0))  # Far apart

        results = manager.batch_test()

        # Should have one test result (no collision)
        assert len(results) == 1
        assert results[0].colliding is False
        assert results[0].mtv is None

    def test_batch_test_with_collisions(self):
        """Test batch collision testing with overlapping rectangles."""
        manager = PhysicsManager(grid_cell_size=64)

        # Register two overlapping rectangles
        rect1 = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
        rect2 = [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]

        manager.register("obj1", rect1, (0.0, 0.0))
        manager.register("obj2", rect2, (0.0, 0.0))  # Overlapping

        results = manager.batch_test()

        # Should have one test result (collision detected)
        assert len(results) == 1
        assert results[0].colliding is True
        assert results[0].mtv is not None
        assert len(results[0].mtv) == 2

    def test_update_position(self):
        """Test updating object positions."""
        manager = PhysicsManager(grid_cell_size=64)

        rect_shape = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        manager.register("obj1", rect_shape, (0.0, 0.0))

        # Update position
        manager.update_position("obj1", (100.0, 100.0))

        obj = manager.objects["obj1"]
        assert obj.position == (100.0, 100.0)
        assert obj.aabb.min_x == 100.0
        assert obj.aabb.min_y == 100.0

    def test_query_collisions(self):
        """Test querying collisions for specific object."""
        manager = PhysicsManager(grid_cell_size=64)

        rect1 = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
        rect2 = [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]
        rect3 = [(10.0, 10.0), (11.0, 10.0), (11.0, 11.0), (10.0, 11.0)]

        manager.register("obj1", rect1, (0.0, 0.0))
        manager.register("obj2", rect2, (0.0, 0.0))  # Collides with obj1
        manager.register("obj3", rect3, (0.0, 0.0))  # Far from others

        # Query collisions for obj1
        collisions = manager.query_collisions("obj1")

        # Should find collision with obj2
        assert len(collisions) == 1
        assert collisions[0].obj1_id == "obj1"
        assert collisions[0].obj2_id == "obj2"
        assert collisions[0].colliding is True

    def test_unregister_object(self):
        """Test unregistering physics objects."""
        manager = PhysicsManager(grid_cell_size=64)

        rect_shape = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        manager.register("obj1", rect_shape)

        assert "obj1" in manager.objects

        manager.unregister("obj1")
        assert "obj1" not in manager.objects

    def test_get_stats(self):
        """Test getting physics manager statistics."""
        manager = PhysicsManager(grid_cell_size=32)  # Smaller cells

        # Register some objects
        rect1 = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        rect2 = [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]

        manager.register("obj1", rect1)
        manager.register("obj2", rect2)

        # Run collision test
        manager.batch_test()

        stats = manager.get_stats()

        assert stats['total_objects'] == 2
        assert stats['grid_cell_size'] == 32
        assert stats['total_collision_tests'] == 1  # One pair tested
        assert 'occupied_cells' in stats
        assert 'avg_objects_per_cell' in stats
        assert 'collision_rate' in stats