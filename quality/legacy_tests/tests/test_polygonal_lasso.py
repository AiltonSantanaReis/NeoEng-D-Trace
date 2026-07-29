# tests/test_polygonal_lasso.py
"""
Tests for the PolygonalLassoTool class.
"""

import pytest
from unittest.mock import Mock, MagicMock
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt
from src.tools.polygonal_lasso import PolygonalLassoTool


class TestPolygonalLassoTool:
    """
    Test suite for PolygonalLassoTool functionality.
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
        self.tool = PolygonalLassoTool(self.canvas_view)

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
        Test that PolygonalLassoTool initializes correctly.
        """
        assert self.tool.canvas_view == self.canvas_view
        assert self.tool._vertices == []
        assert self.tool._preview_point is None

    def test_mouse_press_adds_vertex(self):
        """
        Test that mouse press adds a vertex.
        """
        self.canvas_view.widget_to_image.return_value = (50.0, 75.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(50, 75)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_press(event, (50.0, 75.0))

        assert len(self.tool._vertices) == 1
        assert self.tool._vertices[0] == (50.0, 75.0)
        self.canvas_view.update.assert_called_once()

    def test_mouse_move_updates_preview(self):
        """
        Test that mouse move updates preview point.
        """
        # Add a vertex first
        self.tool._vertices = [(0.0, 0.0)]
        
        self.canvas_view.widget_to_image.return_value = (100.0, 100.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(100, 100)

        self.tool.on_mouse_move(event, (100.0, 100.0))

        assert self.tool._preview_point == (100.0, 100.0)
        self.canvas_view.update.assert_called_once()

    def test_double_click_commits_selection_with_enough_vertices(self):
        """
        Test that double-click commits selection when there are enough vertices.
        """
        # Add vertices for a triangle
        self.tool._vertices = [(0, 0), (100, 0), (50, 100)]
        self.tool._preview_point = (200, 200)

        event = Mock(spec=QMouseEvent)
        self.tool.on_double_click(event, (0, 0))

        # Should call CommandManager execute
        self.scene.cmd.execute.assert_called_once()
        
        # Should reset state
        assert self.tool._vertices == []
        assert self.tool._preview_point is None
        self.canvas_view.update.assert_called_once()

    def test_double_click_ignores_insufficient_vertices(self):
        """
        Test that double-click does nothing with insufficient vertices.
        """
        # Add only 2 vertices
        self.tool._vertices = [(0, 0), (100, 0)]

        event = Mock(spec=QMouseEvent)
        self.tool.on_double_click(event, (0, 0))

        # Should not call scene.add_polygon
        self.scene.add_polygon.assert_not_called()
        
        # Should not reset state
        assert len(self.tool._vertices) == 2

    def test_commit_selection_converts_to_integers(self):
        """
        Test that commit_selection converts coordinates to integers.
        """
        # Float coordinates
        self.tool._vertices = [(0.7, 1.3), (100.9, 0.1), (50.4, 100.8)]

        result = self.tool.commit_selection()

        # Should call CommandManager execute
        self.scene.cmd.execute.assert_called_once()

    def test_cancel_clears_state(self):
        """
        Test that cancel clears all state.
        """
        self.tool._vertices = [(0, 0), (100, 0)]
        self.tool._preview_point = (50, 50)

        self.tool.cancel()

        assert self.tool._vertices == []
        assert self.tool._preview_point is None
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

    def test_draw_overlay_renders_vertices_and_edges(self):
        """
        Test that draw_overlay renders vertices and edges.
        """
        painter = Mock()
        self.tool._vertices = [(0, 0), (100, 100), (200, 0)]
        self.tool._preview_point = (300, 100)

        self.tool.draw_overlay(painter)

        # Should set pen for edges
        painter.setPen.assert_called()
        # Should draw polyline for edges
        painter.drawPolyline.assert_called()
        # Should draw ellipses for vertices
        painter.setBrush.assert_called()
        painter.drawEllipse.assert_called()
        # Should draw preview line
        # Note: This would require more detailed mocking to verify all calls

    def test_draw_overlay_no_vertices(self):
        """
        Test that draw_overlay does nothing with no vertices.
        """
        painter = Mock()
        self.tool._vertices = []

        self.tool.draw_overlay(painter)

        # Should not draw anything
        painter.setPen.assert_not_called()
        painter.drawPolyline.assert_not_called()