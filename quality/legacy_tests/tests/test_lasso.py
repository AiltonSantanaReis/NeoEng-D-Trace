# tests/test_lasso.py
"""
Tests for the LassoTool class.
"""

import pytest
from unittest.mock import Mock, MagicMock
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt
from src.tools.lasso_tool import LassoTool, rdp_simplify


class TestLassoTool:
    """
    Test suite for LassoTool functionality.
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
        self.canvas_view.widget_to_image = Mock(return_value=(100.0, 100.0))  # Mock coordinate conversion
        self.tool = LassoTool(self.canvas_view)

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
        Test that LassoTool initializes correctly.
        """
        assert self.tool.canvas_view == self.canvas_view
        assert self.tool._points == []
        assert self.tool._sample_dist == 3
        assert self.tool._is_drawing is False

    def test_rdp_simplify(self):
        """
        Test RDP simplification algorithm.
        """
        # Simple line
        points = [(0, 0), (1, 1), (2, 2), (3, 3)]
        simplified = rdp_simplify(points, epsilon=0.1)
        assert len(simplified) == 2  # Should reduce to endpoints

        # More complex shape
        points = [(0, 0), (1, 0.1), (2, 0), (3, 0.1), (4, 0)]
        simplified = rdp_simplify(points, epsilon=0.5)
        assert len(simplified) >= 2

    def test_mouse_press_starts_drawing(self):
        """
        Test that mouse press starts drawing.
        """
        self.canvas_view.widget_to_image.return_value = (100.0, 100.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(100, 100)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_press(event, (100.0, 100.0))

        assert self.tool._is_drawing is True
        assert len(self.tool._points) == 1
        assert self.tool._points[0] == (100.0, 100.0)

    def test_mouse_move_adds_points_with_distance_threshold(self):
        """
        Test that mouse move adds points only when distance threshold is met.
        """
        # Start drawing
        self.canvas_view.widget_to_image.return_value = (0.0, 0.0)
        press_event = Mock(spec=QMouseEvent)
        press_event.position.return_value = QPointF(0, 0)
        press_event.button.return_value = Qt.LeftButton
        press_event.LeftButton = Qt.LeftButton
        self.tool.on_mouse_press(press_event, (0.0, 0.0))

        # Move close - should not add point
        self.canvas_view.widget_to_image.return_value = (1.0, 1.0)
        move_event = Mock(spec=QMouseEvent)
        move_event.position.return_value = QPointF(1, 1)  # Distance < 3
        self.tool.on_mouse_move(move_event, (1.0, 1.0))
        assert len(self.tool._points) == 1

        # Move far enough - should add point
        self.canvas_view.widget_to_image.return_value = (5.0, 5.0)
        move_event.position.return_value = QPointF(5, 5)  # Distance > 3
        self.tool.on_mouse_move(move_event, (5.0, 5.0))
        assert len(self.tool._points) == 2

    def test_mouse_release_commits_selection(self):
        """
        Test that mouse release commits the selection to the scene.
        """
        # Simulate drawing a triangle
        self.canvas_view.widget_to_image.return_value = (0.0, 0.0)
        press_event = Mock(spec=QMouseEvent)
        press_event.position.return_value = QPointF(0, 0)
        press_event.button.return_value = Qt.LeftButton
        press_event.LeftButton = Qt.LeftButton
        self.tool.on_mouse_press(press_event, (0.0, 0.0))

        # Add more points
        self.tool._points.extend([(100, 0), (50, 100)])

        # Release
        release_event = Mock(spec=QMouseEvent)
        release_event.position.return_value = QPointF(0, 0)
        release_event.button.return_value = Qt.LeftButton
        release_event.LeftButton = Qt.LeftButton
        self.tool.on_mouse_release(release_event, (0.0, 0.0))

        # Should have called CommandManager execute
        self.scene.cmd.execute.assert_called_once()
        assert self.tool._is_drawing is False
        assert self.tool._points == []  # Reset after commit

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

    def test_draw_overlay_renders_points(self):
        """
        Test that draw_overlay renders the lasso points.
        """
        painter = Mock()
        self.tool._points = [(0, 0), (100, 100), (200, 0)]
        self.tool._is_drawing = True

        self.tool.draw_overlay(painter)

        # Should draw polyline
        painter.setPen.assert_called()
        painter.drawPolyline.assert_called_once()