import unittest
import numpy as np
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt, QPointF

# Try to import and create QApplication for GUI tests
try:
    from PySide6.QtWidgets import QApplication
    import sys

    # Create QApplication if not exists
    if not QApplication.instance():
        app = QApplication(sys.argv)
    HAS_QT = True
except ImportError:
    HAS_QT = False

from src.ui.mask_viewer import MaskViewer


class TestMaskViewer(unittest.TestCase):
    """Test cases for MaskViewer pan/zoom functionality."""

    def setUp(self):
        """Set up test fixtures."""
        if not HAS_QT:
            self.skipTest("PySide6 not available")
        self.viewer = MaskViewer()

    def test_import_and_api(self):
        """Test basic import and API availability."""
        # Test instance creation
        self.assertIsInstance(self.viewer, MaskViewer)

        # Test initial state
        self.assertEqual(self.viewer.get_zoom(), 1.0)
        self.assertEqual(self.viewer.get_pan(), (0.0, 0.0))
        self.assertIsNone(self.viewer.get_numpy_image())

        # Test setting/getting zoom
        self.viewer.set_zoom(2.0)
        self.assertEqual(self.viewer.get_zoom(), 2.0)

        # Test setting/getting pan
        self.viewer.set_pan(10.0, 20.0)
        self.assertEqual(self.viewer.get_pan(), (10.0, 20.0))

        # Test view transform
        self.viewer.set_view_transform(1.5, 5.0, 15.0)
        zoom, pan_x, pan_y = self.viewer.get_view_transform()
        self.assertEqual(zoom, 1.5)
        self.assertEqual(pan_x, 5.0)
        self.assertEqual(pan_y, 15.0)

    def test_numpy_image_handling(self):
        """Test setting and getting numpy images."""
        # Create test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Set image
        self.viewer.set_numpy_image(test_image)

        # Get image back
        retrieved = self.viewer.get_numpy_image()
        self.assertIsNotNone(retrieved)
        np.testing.assert_array_equal(retrieved, test_image)

        # Test None handling
        self.viewer.set_numpy_image(None)
        self.assertIsNone(self.viewer.get_numpy_image())

    def test_zoom_limits(self):
        """Test zoom limits are enforced."""
        # Test minimum zoom
        self.viewer.set_zoom(0.05)  # Below min
        self.assertEqual(self.viewer.get_zoom(), 0.1)

        # Test maximum zoom
        self.viewer.set_zoom(10.0)  # Above max
        self.assertEqual(self.viewer.get_zoom(), 8.0)

        # Test valid zoom
        self.viewer.set_zoom(2.0)
        self.assertEqual(self.viewer.get_zoom(), 2.0)

    def test_zoom_by(self):
        """Test zoom_by method."""
        initial_zoom = self.viewer.get_zoom()

        # Zoom in
        self.viewer.zoom_by(2.0)
        self.assertEqual(self.viewer.get_zoom(), initial_zoom * 2.0)

        # Zoom out
        self.viewer.zoom_by(0.5)
        self.assertEqual(self.viewer.get_zoom(), initial_zoom)

    def test_coordinate_transforms(self):
        """Test view_to_image and image_to_view transforms."""
        # Set up a simple transform
        self.viewer.set_zoom(2.0)
        self.viewer.set_pan(10.0, 20.0)

        # Test round-trip transform
        image_point = (50.0, 75.0)
        view_point = self.viewer.image_to_view(image_point)
        back_to_image = self.viewer.view_to_image(view_point)

        # Should be very close (within floating point precision)
        self.assertAlmostEqual(back_to_image[0], image_point[0], places=5)
        self.assertAlmostEqual(back_to_image[1], image_point[1], places=5)

        # Test inverse
        test_view = QPointF(100.0, 150.0)
        image_from_view = self.viewer.view_to_image(test_view)
        view_from_image = self.viewer.image_to_view(image_from_view)

        self.assertAlmostEqual(view_from_image.x(), test_view.x(), places=5)
        self.assertAlmostEqual(view_from_image.y(), test_view.y(), places=5)

    def test_pan_transform(self):
        """Test pan transform simulation."""
        # Set initial pan
        self.viewer.set_pan(0.0, 0.0)

        # Simulate pan by directly setting internal state (since we can't easily simulate mouse events)
        self.viewer._pan_x = 50.0
        self.viewer._pan_y = 75.0

        # Check pan changed
        pan_x, pan_y = self.viewer.get_pan()
        self.assertEqual(pan_x, 50.0)
        self.assertEqual(pan_y, 75.0)

    def test_reset_view(self):
        """Test reset view functionality."""
        # Set some transform
        self.viewer.set_zoom(3.0)
        self.viewer.set_pan(100.0, 200.0)

        # Reset without image
        self.viewer.reset_view()
        self.assertEqual(self.viewer.get_zoom(), 1.0)
        self.assertEqual(self.viewer.get_pan(), (0.0, 0.0))

        # Reset with image
        test_image = np.zeros((200, 300, 3), dtype=np.uint8)
        self.viewer.set_numpy_image(test_image)

        # Mock widget size
        with patch.object(self.viewer, 'width', return_value=400), \
             patch.object(self.viewer, 'height', return_value=300):
            self.viewer.reset_view()

            # Should fit image to widget
            zoom, pan_x, pan_y = self.viewer.get_view_transform()
            # Image is 200x300, widget is 400x300
            # zoom_x = 400/300 ≈ 1.333, zoom_y = 300/200 = 1.5
            # zoom = min(1.333, 1.5, 1.0) = 1.0 (don't zoom in beyond 1:1)
            self.assertEqual(zoom, 1.0)  # Should be 1.0 since we don't zoom in
            # Pan should center the image
            # image_width_at_zoom = 300 * 1.0 = 300
            # pan_x = (400 - 300) / 2 = 50
            expected_pan_x = (400 - 300 * zoom) / 2
            expected_pan_y = (300 - 200 * zoom) / 2
            self.assertAlmostEqual(pan_x, expected_pan_x, places=2)
            self.assertAlmostEqual(pan_y, expected_pan_y, places=2)

    def test_signals(self):
        """Test signal emissions."""
        # Mock signal receivers
        view_changed_called = False
        image_clicked_called = False
        clicked_pos = None

        def on_view_changed():
            nonlocal view_changed_called
            view_changed_called = True

        def on_image_clicked(pos):
            nonlocal image_clicked_called, clicked_pos
            image_clicked_called = True
            clicked_pos = pos

        self.viewer.viewChanged.connect(on_view_changed)
        self.viewer.imageClicked.connect(on_image_clicked)

        # Test viewChanged signal
        self.viewer.set_zoom(2.0)
        self.assertTrue(view_changed_called)

        # Reset flag
        view_changed_called = False
        self.viewer.set_pan(10.0, 20.0)
        self.assertTrue(view_changed_called)

        # Test imageClicked signal (would be emitted on mouse click without tool handler)
        # This is harder to test without mocking mouse events, so we'll skip for now

    def test_tool_handler_integration(self):
        """Test tool handler delegation."""
        # Mock tool handler
        handler_called = False
        handler_result = True  # Handler accepts the event

        def mock_handler(event):
            nonlocal handler_called, handler_result
            handler_called = True
            return handler_result

        self.viewer.tool_handler = mock_handler

        # Create mock mouse event
        mock_event = Mock()
        mock_event.button.return_value = Qt.LeftButton  # Left button
        mock_event.modifiers.return_value = Qt.NoModifier  # No modifiers
        mock_event.position.return_value = QPointF(100.0, 100.0)
        mock_event.accept = Mock()

        # Test handler called and returns True (event accepted)
        with patch.object(self.viewer, '_image', np.zeros((200, 200, 3), dtype=np.uint8)):
            self.viewer.mousePressEvent(mock_event)
            self.assertTrue(handler_called)
            mock_event.accept.assert_called()


if __name__ == '__main__':
    unittest.main()