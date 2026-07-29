# tests/test_auto_detect_integration.py
"""
Integration tests for auto-detection and scene integration.

Tests the complete workflow from detection to scene object creation,
including undo/redo functionality.
"""

import pytest
import numpy as np

from src.models.scene import Scene
from src.core.commands import CommandManager, CreateObjectCommand
from src.tools.auto_detect import detect_and_create_objects, detect_polygons


class TestAutoDetectIntegration:
    """Test auto-detection integration with scene management."""

    def setup_method(self):
        """Setup test scene and command manager."""
        self.scene = Scene()
        self.cmd_manager = CommandManager()
        self.scene.cmd = self.cmd_manager

        # Create a simple test image with a square
        self.test_image = np.zeros((100, 100), dtype=np.uint8)
        self.test_image[20:80, 20:80] = 255  # White square
        self.scene.image = self.test_image

    def test_detect_and_create_objects_basic(self):
        """Test basic detection and object creation."""
        # Run detection and creation
        object_ids = detect_and_create_objects(self.scene, mode='basic', apply=True)

        # Should create at least one object
        assert len(object_ids) > 0
        assert len(self.scene.objects) == len(object_ids)

        # Verify objects exist
        for obj_id in object_ids:
            assert obj_id in self.scene.objects
            obj = self.scene.objects[obj_id]
            assert len(obj.polygon) >= 3  # Valid polygon

    def test_detect_and_create_objects_preview_mode(self):
        """Test detection in preview mode (apply=False)."""
        # Run detection in preview mode
        preview_ids = detect_and_create_objects(self.scene, mode='basic', apply=False)

        # Should return preview IDs but not create objects
        assert len(preview_ids) > 0
        assert len(self.scene.objects) == 0

        # Preview IDs should be strings
        for pid in preview_ids:
            assert isinstance(pid, str)
            assert pid.startswith('preview_')

    def test_create_object_command_undo_redo(self):
        """Test CreateObjectCommand undo/redo functionality."""
        # Create a simple polygon
        test_polygon = [(10, 10), (90, 10), (90, 90), (10, 90)]

        # Execute command
        cmd = CreateObjectCommand(test_polygon)
        self.cmd_manager.execute(cmd, self.scene)

        # Should create one object
        assert len(self.scene.objects) == 1
        obj_id = cmd.object_id
        assert obj_id in self.scene.objects

        # Undo should remove the object
        self.cmd_manager.undo(self.scene)
        assert len(self.scene.objects) == 0
        assert obj_id not in self.scene.objects

        # Redo should restore the object
        self.cmd_manager.redo(self.scene)
        assert len(self.scene.objects) == 1
        assert obj_id in self.scene.objects

    def test_detect_and_create_with_custom_layer(self):
        """Test detection with custom layer assignment."""
        # Create a custom layer
        custom_layer = self.scene.create_layer("Detection Layer")

        # Run detection with custom layer
        object_ids = detect_and_create_objects(
            self.scene,
            mode='basic',
            apply=True,
            layer_id=custom_layer.id
        )

        # Verify objects are on the correct layer
        for obj_id in object_ids:
            obj = self.scene.objects[obj_id]
            assert obj.layer_id == custom_layer.id

    def test_detect_and_create_batch_operations(self):
        """Test batch creation of multiple objects."""
        # Create a more complex image with multiple shapes
        image = np.zeros((200, 200), dtype=np.uint8)

        # Add multiple squares
        image[10:40, 10:40] = 255    # Top-left
        image[10:40, 150:180] = 255  # Top-right
        image[150:180, 10:40] = 255  # Bottom-left
        image[150:180, 150:180] = 255 # Bottom-right

        self.scene.image = image

        # Run detection
        object_ids = detect_and_create_objects(self.scene, mode='basic', apply=True)

        # Should detect multiple objects
        assert len(object_ids) >= 2  # At least 2 squares detected

    def test_detect_and_create_objects_error_handling(self):
        """Test error handling in detect_and_create_objects."""
        # Remove image to cause error
        self.scene.image = None

        # Should raise ValueError
        with pytest.raises(ValueError, match="No image provided"):
            detect_and_create_objects(self.scene, mode='basic', apply=True)

    def test_integration_with_command_manager(self):
        """Test integration with scene's command manager."""
        # Ensure scene has command manager
        assert self.scene.cmd is not None

        # Run detection and creation
        initial_count = len(self.scene.objects)
        object_ids = detect_and_create_objects(self.scene, mode='basic', apply=True)

        # Should create objects
        assert len(self.scene.objects) == initial_count + len(object_ids)

        # Undo should remove all created objects
        for _ in object_ids:
            self.cmd_manager.undo(self.scene)

        assert len(self.scene.objects) == initial_count