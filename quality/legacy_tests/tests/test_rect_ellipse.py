# tests/test_rect_ellipse.py
"""
Tests for the RectSelectionTool and EllipseSelectionTool classes.
"""

import pytest
import math
from unittest.mock import Mock, MagicMock
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt
from src.tools.rect_selection import RectSelectionTool
from src.tools.ellipse_selection import EllipseSelectionTool


class TestRectSelectionTool:
    """
    Test suite for RectSelectionTool functionality.
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
        self.mock_image.constBits.return_value = b'\x00' * 10000
        
        self.scene.get_image.return_value = self.mock_image
        
        self.tool = RectSelectionTool(self.canvas_view)

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
        Test that RectSelectionTool initializes correctly.
        """
        assert self.tool.canvas_view == self.canvas_view
        assert self.tool._start_point is None
        assert self.tool._end_point is None
        assert self.tool._is_selecting is False

    def test_mouse_press_starts_selection(self):
        """
        Test that mouse press starts rectangle selection.
        """
        self.canvas_view.widget_to_image.return_value = (50.0, 75.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(50, 75)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_press(event, (50.0, 75.0))

        assert self.tool._is_selecting is True
        assert self.tool._start_point == (50.0, 75.0)
        assert self.tool._end_point == (50.0, 75.0)
        self.canvas_view.update.assert_called_once()

    def test_mouse_move_updates_bounds(self):
        """
        Test that mouse move updates rectangle bounds.
        """
        # Start selection
        self.tool._is_selecting = True
        self.tool._start_point = (50.0, 50.0)
        
        self.canvas_view.widget_to_image.return_value = (100.0, 80.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(100, 80)
        event.modifiers.return_value = Qt.NoModifier

        self.tool.on_mouse_move(event, (100.0, 80.0))

        assert self.tool._end_point == (100.0, 80.0)
        self.canvas_view.update.assert_called_once()

    def test_mouse_move_with_shift_constrains_to_square(self):
        """
        Test that Shift modifier constrains rectangle to square.
        """
        # Start selection
        self.tool._is_selecting = True
        self.tool._start_point = (50.0, 50.0)
        
        self.canvas_view.widget_to_image.return_value = (80.0, 60.0)  # dx=30, dy=10
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(80, 60)
        event.modifiers.return_value = Qt.ShiftModifier

        self.tool.on_mouse_move(event, (80.0, 60.0))

        # Should create square with size 30 (larger dimension)
        expected_end = (50.0 + 30, 50.0 + 30)  # (80, 80)
        assert self.tool._end_point == expected_end

    def test_mouse_release_commits_selection(self):
        """
        Test that mouse release commits the rectangle selection.
        """
        # Setup rectangle
        self.tool._start_point = (10, 10)
        self.tool._end_point = (50, 30)
        self.tool._is_selecting = True

        event = Mock(spec=QMouseEvent)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_release(event, (50, 30))

        # Should call CommandManager execute
        self.scene.cmd.execute.assert_called_once()
        
        # Should reset state
        assert self.tool._start_point is None
        assert self.tool._end_point is None
        assert self.tool._is_selecting is False

    def test_cancel_clears_state(self):
        """
        Test that cancel clears all state.
        """
        self.tool._start_point = (10, 10)
        self.tool._end_point = (50, 30)
        self.tool._is_selecting = True

        self.tool.cancel()

        assert self.tool._start_point is None
        assert self.tool._end_point is None
        assert self.tool._is_selecting is False
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


class TestEllipseSelectionTool:
    """
    Test suite for EllipseSelectionTool functionality.
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
        self.mock_image.constBits.return_value = b'\x00' * 10000
        
        self.scene.get_image.return_value = self.mock_image
        
        self.tool = EllipseSelectionTool(self.canvas_view)

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
        Test that EllipseSelectionTool initializes correctly.
        """
        assert self.tool.canvas_view == self.canvas_view
        assert self.tool._center is None
        assert self.tool._radius_x == 0
        assert self.tool._radius_y == 0
        assert self.tool._is_selecting is False
        assert self.tool._segments == 64

    def test_mouse_press_starts_selection(self):
        """
        Test that mouse press starts ellipse selection.
        """
        self.canvas_view.widget_to_image.return_value = (50.0, 75.0)
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(50, 75)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_press(event, (50.0, 75.0))

        assert self.tool._is_selecting is True
        assert self.tool._center == (50.0, 75.0)
        assert self.tool._radius_x == 0
        assert self.tool._radius_y == 0
        self.canvas_view.update.assert_called_once()

    def test_mouse_move_updates_radii(self):
        """
        Test that mouse move updates ellipse radii.
        """
        # Start selection
        self.tool._is_selecting = True
        self.tool._center = (50.0, 50.0)
        
        self.canvas_view.widget_to_image.return_value = (80.0, 70.0)  # dx=30, dy=20
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(80, 70)
        event.modifiers.return_value = Qt.NoModifier

        self.tool.on_mouse_move(event, (80.0, 70.0))

        assert self.tool._radius_x == 30
        assert self.tool._radius_y == 20
        self.canvas_view.update.assert_called_once()

    def test_mouse_move_with_shift_constrains_to_circle(self):
        """
        Test that Shift modifier constrains ellipse to circle.
        """
        # Start selection
        self.tool._is_selecting = True
        self.tool._center = (50.0, 50.0)
        
        self.canvas_view.widget_to_image.return_value = (80.0, 60.0)  # dx=30, dy=10
        event = Mock(spec=QMouseEvent)
        event.position.return_value = QPointF(80, 60)
        event.modifiers.return_value = Qt.ShiftModifier

        self.tool.on_mouse_move(event, (80.0, 60.0))

        # Should create circle with radius 30 (larger dimension)
        assert self.tool._radius_x == 30
        assert self.tool._radius_y == 30

    def test_mouse_release_commits_selection(self):
        """
        Test that mouse release commits the ellipse selection.
        """
        # Setup ellipse
        self.tool._center = (50, 50)
        self.tool._radius_x = 20
        self.tool._radius_y = 15
        self.tool._is_selecting = True

        event = Mock(spec=QMouseEvent)
        event.button.return_value = Qt.LeftButton
        event.LeftButton = Qt.LeftButton

        self.tool.on_mouse_release(event, (70, 65))

        # Should call CommandManager execute
        self.scene.cmd.execute.assert_called_once()
        
        # Should reset state
        assert self.tool._center is None
        assert self.tool._radius_x == 0
        assert self.tool._radius_y == 0
        assert self.tool._is_selecting is False

    def test_cancel_clears_state(self):
        """
        Test that cancel clears all state.
        """
        self.tool._center = (50, 50)
        self.tool._radius_x = 20
        self.tool._radius_y = 15
        self.tool._is_selecting = True

        self.tool.cancel()

        assert self.tool._center is None
        assert self.tool._radius_x == 0
        assert self.tool._radius_y == 0
        assert self.tool._is_selecting is False
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