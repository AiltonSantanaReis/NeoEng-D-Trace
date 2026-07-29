# tests/test_pen_tool.py
"""
Tests for the PenTool class.
"""

import pytest
from unittest.mock import Mock, MagicMock
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt
from src.tools.pen_tool import PenTool, BezierNode, bezier_point, bezier_curve


class TestBezierMath:
    """Test Bézier curve mathematics."""

    def test_bezier_point(self):
        """Test cubic Bézier point calculation."""
        p0 = (0, 0)
        p1 = (1, 1)
        p2 = (2, 1)
        p3 = (3, 0)
        
        # At t=0, should return p0
        result = bezier_point(0, p0, p1, p2, p3)
        assert result == (0, 0)
        
        # At t=1, should return p3
        result = bezier_point(1, p0, p1, p2, p3)
        assert result == (3, 0)
        
        # At t=0.5, should be at midpoint-ish
        result = bezier_point(0.5, p0, p1, p2, p3)
        assert result[0] > 1.4 and result[0] < 1.6  # Approximate midpoint
        assert result[1] > 0.7 and result[1] < 0.8  # Correct y value

    def test_bezier_curve(self):
        """Test Bézier curve generation."""
        p0 = (0, 0)
        p1 = (1, 1)
        p2 = (2, 1)
        p3 = (3, 0)
        
        points = bezier_curve(p0, p1, p2, p3, segments=10)
        
        assert len(points) == 11  # segments + 1
        assert points[0] == (0, 0)
        assert points[-1] == (3, 0)
        
        # Points should be monotonically increasing in x
        for i in range(1, len(points)):
            assert points[i][0] >= points[i-1][0]


class TestBezierNode:
    """Test BezierNode class."""

    def test_initialization(self):
        """Test node initialization."""
        anchor = (10, 20)
        node = BezierNode(anchor)
        
        assert node.anchor == anchor
        assert node.handle_in == anchor
        assert node.handle_out == anchor


class TestPenTool:
    """Test PenTool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_canvas = Mock()
        self.mock_canvas.model = Mock()
        self.tool = PenTool(self.mock_canvas)

    def test_initialization(self):
        """Test tool initialization."""
        assert self.tool._nodes == []
        assert self.tool._selected_node is None
        assert self.tool._selected_handle is None
        assert not self.tool._is_placing_handle

    def test_place_anchor_first(self):
        """Test placing the first anchor."""
        point = (100, 200)
        self.tool._place_anchor(point)
        
        assert len(self.tool._nodes) == 1
        assert self.tool._nodes[0].anchor == point
        assert self.tool._selected_node == self.tool._nodes[0]

    def test_place_anchor_second(self):
        """Test placing a second anchor with auto-handle placement."""
        point1 = (100, 200)
        point2 = (150, 250)
        
        self.tool._place_anchor(point1)
        self.tool._place_anchor(point2)
        
        assert len(self.tool._nodes) == 2
        assert self.tool._nodes[1].anchor == point2
        
        # Check that handles are set
        node1 = self.tool._nodes[0]
        node2 = self.tool._nodes[1]
        
        # With only 2 nodes, handles should be at anchor positions initially
        # (auto-placement requires at least 3 nodes for direction calculation)
        assert node2.handle_in == point2

    def test_get_anchor_at_point(self):
        """Test anchor point detection."""
        self.tool._place_anchor((100, 200))
        
        # Should find anchor
        found = self.tool._get_anchor_at_point((100, 200))
        assert found is not None
        assert found.anchor == (100, 200)
        
        # Should not find far away point
        found = self.tool._get_anchor_at_point((200, 300))
        assert found is None

    def test_get_handle_at_point(self):
        """Test handle point detection."""
        node = BezierNode((100, 200))
        node.handle_out = (120, 220)
        self.tool._nodes = [node]
        
        # Should find handle
        found = self.tool._get_handle_at_point((120, 220))
        assert found is not None
        assert found[0] == node
        assert found[1] == 'out'
        
        # Should not find far away point
        found = self.tool._get_handle_at_point((200, 300))
        assert found is None

    def test_generate_curve_points_single_node(self):
        """Test curve generation with single node."""
        self.tool._place_anchor((100, 200))
        points = self.tool._generate_curve_points()
        assert points == []

    def test_generate_curve_points_two_nodes(self):
        """Test curve generation with two nodes."""
        self.tool._place_anchor((100, 200))
        self.tool._place_anchor((150, 250))
        
        points = self.tool._generate_curve_points()
        assert len(points) > 0
        assert points[0] == (100, 200)  # Start at first anchor
        assert points[-1] == (150, 250)  # End at second anchor

    def test_commit_selection_valid(self):
        """Test committing a valid selection."""
        # Create a simple curve
        self.tool._place_anchor((100, 200))
        self.tool._place_anchor((150, 250))
        self.tool._place_anchor((200, 220))
        
        # Mock the model - ensure cmd is None to use fallback
        self.mock_canvas.model.cmd = None
        self.mock_canvas.model.add_polygon.return_value = "oid123"
        
        result = self.tool.commit_selection()
        assert result == "oid123"  # Should return object ID
        
        # Verify model was called
        self.mock_canvas.model.add_polygon.assert_called_once()

    def test_commit_selection_invalid(self):
        """Test committing an invalid selection."""
        # Only one point
        self.tool._place_anchor((100, 200))
        
        result = self.tool.commit_selection()
        assert result is None
        
        # Model should not be called
        self.mock_canvas.model.add_polygon.assert_not_called()

    def test_mouse_press_place_anchor(self):
        """Test mouse press to place anchor."""
        event = Mock(spec=QMouseEvent)
        event.button.return_value = Qt.LeftButton
        event.position.return_value = QPointF(150, 250)
        
        # Mock screen_to_image
        self.tool.screen_to_image = Mock(return_value=(100, 200))
        
        self.tool.on_mouse_press(event, (100, 200))
        
        assert len(self.tool._nodes) == 1
        assert self.tool._nodes[0].anchor == (100, 200)

    def test_mouse_press_select_handle(self):
        """Test mouse press to select handle."""
        # Create node with handle
        node = BezierNode((100, 200))
        node.handle_out = (120, 220)
        self.tool._nodes = [node]
        
        event = Mock(spec=QMouseEvent)
        event.button.return_value = Qt.LeftButton
        event.position.return_value = QPointF(170, 270)  # Screen coords
        
        # Mock screen_to_image to return handle position
        self.tool.screen_to_image = Mock(return_value=(120, 220))
        
        self.tool.on_mouse_press(event, (120, 220))
        
        assert self.tool._selected_node == node
        assert self.tool._selected_handle == 'out'

    def test_mouse_move_drag_handle(self):
        """Test dragging a handle."""
        node = BezierNode((100, 200))
        node.handle_out = (120, 220)
        self.tool._nodes = [node]
        self.tool._selected_node = node
        self.tool._selected_handle = 'out'
        
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(180, 280)
        
        self.tool.screen_to_image = Mock(return_value=(130, 230))
        
        self.tool.on_mouse_move(event, (130, 230))
        
        assert node.handle_out == (130, 230)

    def test_double_click_commit(self):
        """Test double-click to commit selection."""
        self.tool._place_anchor((100, 200))
        self.tool._place_anchor((150, 250))
        
        self.mock_canvas.model.cmd = None
        self.mock_canvas.model.add_polygon.return_value = "oid123"
        
        event = Mock(spec=QMouseEvent)
        self.tool.on_double_click(event, (100, 200))
        
        # Should have committed and cleared
        assert self.tool._nodes == []
        assert self.tool._selected_node is None
        
        self.mock_canvas.model.add_polygon.assert_called_once()

    def test_cancel(self):
        """Test canceling the tool."""
        self.tool._place_anchor((100, 200))
        self.tool._selected_node = self.tool._nodes[0]
        self.tool._selected_handle = 'out'
        
        self.tool.cancel()
        
        assert self.tool._nodes == []
        assert self.tool._selected_node is None
        assert self.tool._selected_handle is None
        assert not self.tool._is_placing_handle

    def test_draw_overlay_no_nodes(self):
        """Test drawing overlay with no nodes."""
        painter = Mock()
        self.tool.draw_overlay(painter)
        # Should not crash, no assertions needed

    def test_draw_overlay_with_nodes(self):
        """Test drawing overlay with nodes."""
        self.tool._place_anchor((100, 200))
        self.tool._place_anchor((150, 250))
        
        painter = Mock()
        self.tool.image_to_screen = Mock(side_effect=lambda x, y: (x*2, y*2))
        
        self.tool.draw_overlay(painter)
        
        # Verify drawing calls were made
        painter.setPen.assert_called()
        painter.drawPolyline.assert_called()