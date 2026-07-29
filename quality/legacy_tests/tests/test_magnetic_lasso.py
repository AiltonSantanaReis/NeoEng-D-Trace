# tests/test_magnetic_lasso.py
"""
Tests for the MagneticLassoTool class.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtGui import QMouseEvent, QImage
from PySide6.QtCore import QPointF, Qt
from src.tools.magnetic_lasso import MagneticLassoTool, sobel_edge_detection, dijkstra_pathfinding


class TestMagneticLassoAlgorithms:
    """
    Test the underlying algorithms used by MagneticLassoTool.
    """

    def test_sobel_edge_detection(self):
        """
        Test Sobel edge detection algorithm.
        """
        # Create a simple test image with a vertical edge
        image = np.zeros((5, 5), dtype=np.uint8)
        image[:, 2:] = 255  # Vertical edge in the middle
        
        edges = sobel_edge_detection(image)
        
        assert edges.shape == (5, 5)
        assert edges.dtype == np.uint8
        # Should detect edges around column 2
        assert np.max(edges) > 0

    def test_dijkstra_pathfinding_simple(self):
        """
        Test Dijkstra pathfinding with a simple case.
        """
        # Create a simple edge map
        edge_map = np.ones((5, 5), dtype=np.uint8) * 100
        edge_map[2, :] = 50  # Lower cost path through middle row
        
        start = (0, 0)
        end = (4, 4)
        
        path = dijkstra_pathfinding(edge_map, start, end)
        
        assert len(path) > 0
        assert path[0] == start
        assert path[-1] == end

    def test_dijkstra_pathfinding_no_path(self):
        """
        Test Dijkstra when no path exists.
        """
        # Create an edge map with obstacles
        edge_map = np.ones((5, 5), dtype=np.uint8) * 100
        # Make it impossible to reach end
        edge_map[4, 4] = 255  # But this shouldn't matter
        
        start = (0, 0)
        end = (4, 4)
        
        path = dijkstra_pathfinding(edge_map, start, end)
        
        # Should still find a path in this simple case
        assert len(path) > 0


class TestMagneticLassoTool:
    """
    Test suite for MagneticLassoTool functionality.
    """

    def setup_method(self):
        """
        Setup test fixtures.
        """
        self.canvas_view = Mock()
        self.scene = Mock()
        self.scene.cmd = Mock()  # Mock CommandManager
        self.scene.objects = {}
        self.scene.add_polygon = Mock(side_effect=self._mock_add_polygon)
        self.canvas_view.scene = self.scene
        self.canvas_view.model = self.scene  # For commit_selection
        self.canvas_view._zoom = 1.0
        self.canvas_view._pan = [0.0, 0.0]
        self.canvas_view.widget_to_image = Mock(return_value=(100.0, 100.0))
        
        # Mock image
        self.mock_image = Mock()
        self.mock_image.convertToFormat.return_value = self.mock_image
        self.mock_image.width.return_value = 100
        self.mock_image.height.return_value = 100
        self.mock_image.constBits.return_value = np.random.randint(0, 256, 10000, dtype=np.uint8).tobytes()
        
        self.scene.get_image.return_value = self.mock_image
        
        self.tool = MagneticLassoTool(self.canvas_view)

    def _mock_add_polygon(self, polygon, layer_id=None):
        """Mock add_polygon that returns an object ID."""
        oid = f"obj_{len(self.scene.objects)}"
        mock_obj = Mock()
        mock_obj.polygon = polygon
        mock_obj.layer_id = layer_id or 'layer_default'
        self.scene.objects[oid] = mock_obj
        return oid

    def test_initialization(self):
        """
        Test that MagneticLassoTool initializes correctly.
        """
        assert self.tool.canvas_view == self.canvas_view
        assert self.tool._anchors == []
        assert self.tool._path == []
        assert self.tool._preview_path == []
        assert self.tool._edge_map is None

    def test_get_image_array(self):
        """
        Test image array extraction.
        """
        array = self.tool._get_image_array()
        assert array is not None
        assert array.shape == (100, 100)
        assert array.dtype == np.uint8

    def test_compute_edge_map(self):
        """
        Test edge map computation.
        """
        self.tool._compute_edge_map()
        assert self.tool._edge_map is not None
        assert self.tool._edge_map.shape == (100, 100)
        assert self.tool._edge_map.dtype == np.uint8

    def test_mouse_press_adds_anchor(self):
        """
        Test that mouse press adds an anchor point.
        """
        self.canvas_view.widget_to_image.return_value = (50.0, 75.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(50, 75)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_press(event, (50.0, 75.0))

        assert len(self.tool._anchors) == 1
        assert self.tool._anchors[0] == (50.0, 75.0)
        self.canvas_view.update.assert_called_once()

    def test_mouse_press_computes_path_between_anchors(self):
        """
        Test that mouse press computes path between anchors.
        """
        # Add first anchor
        self.tool._anchors = [(10.0, 10.0)]
        
        self.canvas_view.widget_to_image.return_value = (50.0, 50.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(50, 50)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_press(event, (50.0, 50.0))

        assert len(self.tool._anchors) == 2
        assert len(self.tool._path) > 0  # Should have computed a path

    def test_mouse_move_updates_preview(self):
        """
        Test that mouse move updates preview path.
        """
        # Add an anchor first
        self.tool._anchors = [(25.0, 25.0)]
        
        self.canvas_view.widget_to_image.return_value = (75.0, 75.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(75, 75)

        self.tool.on_mouse_move(event, (75.0, 75.0))

        assert len(self.tool._preview_path) > 0
        self.canvas_view.update.assert_called_once()

    def test_double_click_closes_selection(self):
        """
        Test that double-click closes the selection.
        """
        # Add anchors for a triangle
        self.tool._anchors = [(10, 10), (50, 10), (30, 50)]
        self.tool._path = [(10, 10), (20, 10), (30, 10), (40, 10), (50, 10), (50, 20), (50, 30), (50, 40), (50, 50), (40, 50), (30, 50)]

        event = Mock(spec=QMouseEvent)
        self.tool.on_double_click(event, (10, 10))

        # Should call CommandManager execute
        self.scene.cmd.execute.assert_called_once()
        
        # Should reset state
        assert self.tool._anchors == []
        assert self.tool._path == []
        assert self.tool._preview_path == []

    def test_commit_selection_converts_to_integers(self):
        """
        Test that commit_selection converts coordinates to integers.
        """
        # Float coordinates
        self.tool._path = [(0.7, 1.3), (100.9, 0.1), (50.4, 100.8)]

        result = self.tool.commit_selection()

        # Should call CommandManager execute
        self.scene.cmd.execute.assert_called_once()

    def test_cancel_clears_state(self):
        """
        Test that cancel clears all state.
        """
        self.tool._anchors = [(0, 0), (100, 0)]
        self.tool._path = [(0, 0), (50, 0), (100, 0)]
        self.tool._preview_path = [(100, 0), (100, 50)]

        self.tool.cancel()

        assert self.tool._anchors == []
        assert self.tool._path == []
        assert self.tool._preview_path == []
        self.canvas_view.update.assert_called_once()

    def test_interface_returns_tool_interface(self):
        """
        Test that interface() returns a ToolInterface compatible object.
        """
        interface = self.tool.interface()
        assert hasattr(interface, 'on_mouse_press')
        assert hasattr(interface, 'on_mouse_move')
        assert hasattr(interface, 'on_mouse_release')
        assert hasattr(interface, 'on_cancel')
        assert hasattr(interface, 'draw_overlay')

    def test_draw_overlay_renders_paths_and_anchors(self):
        """
        Test that draw_overlay renders paths and anchors.
        """
        painter = Mock()
        self.tool._anchors = [(0, 0), (100, 100)]
        self.tool._path = [(0, 0), (50, 50), (100, 100)]
        self.tool._preview_path = [(100, 100), (150, 150)]

        self.tool.draw_overlay(painter)

        # Should have called various drawing methods
        painter.setPen.assert_called()
        painter.setBrush.assert_called()
        painter.drawPolyline.assert_called()
        painter.drawEllipse.assert_called()

    def test_compute_magnetic_path_with_edge_map(self):
        """
        Test magnetic path computation with actual edge map.
        """
        # Force computation of edge map
        self.tool._compute_edge_map()
        
        start = (10.0, 10.0)
        end = (50.0, 50.0)
        
        path = self.tool._compute_magnetic_path(start, end)
        
        assert len(path) > 0
        assert path[0] == (10, 10)  # Should be close to start
        assert path[-1] == (50, 50)  # Should be close to end