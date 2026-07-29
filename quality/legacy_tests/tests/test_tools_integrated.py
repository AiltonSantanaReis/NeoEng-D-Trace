# tests/test_tools_integrated.py
"""
Integrated tests for all selection tools with CommandManager integration.
"""

import pytest
from unittest.mock import Mock
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QPointF, Qt
from src.tools.lasso_tool import LassoTool
from src.tools.polygonal_lasso import PolygonalLassoTool
from src.tools.magnetic_lasso import MagneticLassoTool
from src.tools.pen_tool import PenTool, BezierNode
from src.tools.rect_selection import RectSelectionTool
from src.tools.ellipse_selection import EllipseSelectionTool
from src.core.commands import CommandManager


class TestToolsIntegrated:
    """Test all tools with CommandManager integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_canvas = Mock()
        self.scene = Mock()
        self.scene.cmd = CommandManager()
        self.scene.objects = {}
        self.scene.layers = [Mock(id='layer_default', name='Default', visible=True, locked=False)]
        self.scene.add_polygon = Mock(side_effect=self._mock_add_polygon)
        self.scene.remove_object = Mock(side_effect=self._mock_remove_object)
        self.mock_canvas.model = self.scene

    def _mock_add_polygon(self, polygon, layer_id=None):
        """Mock add_polygon that returns an object ID."""
        oid = f"obj_{len(self.scene.objects)}"
        mock_obj = Mock()
        mock_obj.polygon = polygon
        mock_obj.layer_id = layer_id or 'layer_default'
        self.scene.objects[oid] = mock_obj
        return oid

    def _mock_remove_object(self, oid):
        """Mock remove_object."""
        if oid in self.scene.objects:
            del self.scene.objects[oid]

    def test_lasso_tool_with_commands(self):
        """Test lasso tool creates undoable commands."""
        tool = LassoTool(self.mock_canvas)
        
        # Simulate lasso drawing
        event_press = Mock(spec=QMouseEvent)
        event_press.button.return_value = Qt.LeftButton
        event_press.position.return_value = QPointF(100, 100)
        
        event_move1 = Mock(spec=QMouseEvent)
        event_move1.position.return_value = QPointF(150, 120)
        
        event_move2 = Mock(spec=QMouseEvent)
        event_move2.position.return_value = QPointF(200, 150)
        
        event_release = Mock(spec=QMouseEvent)
        event_release.button.return_value = Qt.LeftButton
        
        # Mock coordinate conversion
        tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        # Draw lasso
        tool.on_mouse_press(event_press, (100, 100))
        tool.on_mouse_move(event_move1, (150, 120))
        tool.on_mouse_move(event_move2, (200, 150))
        tool.on_mouse_release(event_release, (200, 150))
        
        # Should have created a polygon
        assert len(self.scene.objects) == 1
        
        # Test undo
        initial_count = len(self.scene.objects)
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == initial_count - 1

    def test_polygonal_lasso_with_commands(self):
        """Test polygonal lasso tool creates undoable commands."""
        tool = PolygonalLassoTool(self.mock_canvas)
        
        # Simulate polygonal lasso
        events = [
            (Qt.LeftButton, QPointF(100, 100)),
            (Qt.LeftButton, QPointF(150, 120)),
            (Qt.LeftButton, QPointF(200, 150)),
            (Qt.LeftButton, QPointF(100, 100)),  # Close the polygon
        ]
        
        tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        # Place points
        for button, pos in events[:-1]:  # All except the last
            event = Mock(spec=QMouseEvent)
            event.button.return_value = button
            event.position.return_value = pos
            tool.on_mouse_press(event, (pos.x(), pos.y()))
        
        # Double-click to complete
        event_double = Mock(spec=QMouseEvent)
        tool.on_double_click(event_double, (100, 100))
        
        # Should have created a polygon
        assert len(self.scene.objects) == 1
        
        # Test undo
        initial_count = len(self.scene.objects)
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == initial_count - 1

    def test_pen_tool_with_commands(self):
        """Test pen tool creates undoable commands."""
        tool = PenTool(self.mock_canvas)
        
        # Simulate Bézier curve creation
        tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        # Place anchors
        points = [(100, 100), (150, 120), (200, 150)]
        for point in points:
            tool._place_anchor(point)
        
        # Commit selection
        result = tool.commit_selection()
        
        # Should have created a polygon
        assert result is not None
        assert len(self.scene.objects) == 1
        
        # Test undo
        initial_count = len(self.scene.objects)
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == initial_count - 1

    def test_rect_tool_with_commands(self):
        """Test rectangle tool creates undoable commands."""
        tool = RectSelectionTool(self.mock_canvas)
        
        # Simulate rectangle creation
        event_press = Mock(spec=QMouseEvent)
        event_press.button.return_value = Qt.LeftButton
        event_press.position.return_value = QPointF(100, 100)
        
        event_release = Mock(spec=QMouseEvent)
        event_release.button.return_value = Qt.LeftButton
        event_release.position.return_value = QPointF(200, 150)
        
        tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        # Create rectangle
        tool.on_mouse_press(event_press, (100, 100))
        tool.on_mouse_release(event_release, (200, 150))
        
        # Should have created a polygon
        assert len(self.scene.objects) == 1
        
        # Test undo
        initial_count = len(self.scene.objects)
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == initial_count - 1

    def test_ellipse_tool_with_commands(self):
        """Test ellipse tool creates undoable commands."""
        tool = EllipseSelectionTool(self.mock_canvas)
        
        # Simulate ellipse creation
        event_press = Mock(spec=QMouseEvent)
        event_press.button.return_value = Qt.LeftButton
        event_press.position.return_value = QPointF(150, 125)  # Center
        
        event_move = Mock(spec=QMouseEvent)
        event_move.position.return_value = QPointF(200, 150)  # Corner
        event_move.modifiers.return_value = Qt.NoModifier
        
        event_release = Mock(spec=QMouseEvent)
        event_release.button.return_value = Qt.LeftButton
        event_release.position.return_value = QPointF(200, 150)  # Corner
        
        tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        # Create ellipse
        tool.on_mouse_press(event_press, (150, 125))
        tool.on_mouse_move(event_move, (200, 150))
        tool.on_mouse_release(event_release, (200, 150))
        
        # Should have created a polygon
        assert len(self.scene.objects) == 1
        
        # Test undo
        initial_count = len(self.scene.objects)
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == initial_count - 1

    def test_multiple_operations_undo_redo(self):
        """Test multiple operations with undo/redo sequence."""
        # Create a polygonal lasso
        polygonal_tool = PolygonalLassoTool(self.mock_canvas)
        polygonal_tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        events = [
            (Qt.LeftButton, QPointF(100, 100)),
            (Qt.LeftButton, QPointF(150, 120)),
            (Qt.LeftButton, QPointF(200, 150)),
            (Qt.LeftButton, QPointF(100, 100)),  # Close the polygon
        ]
        
        # Place points
        for button, pos in events[:-1]:  # All except the last
            event = Mock(spec=QMouseEvent)
            event.button.return_value = button
            event.position.return_value = pos
            polygonal_tool.on_mouse_press(event, (pos.x(), pos.y()))
        
        # Double-click to complete
        event_double = Mock(spec=QMouseEvent)
        polygonal_tool.on_double_click(event_double, (100, 100))
        
        # Create a rectangle
        rect_tool = RectSelectionTool(self.mock_canvas)
        rect_tool.screen_to_image = Mock(side_effect=lambda x, y: (x, y))
        
        event_press = Mock(spec=QMouseEvent)
        event_press.button.return_value = Qt.LeftButton
        event_press.position.return_value = QPointF(100, 100)
        
        event_release = Mock(spec=QMouseEvent)
        event_release.button.return_value = Qt.LeftButton
        event_release.position.return_value = QPointF(150, 150)
        
        rect_tool.on_mouse_press(event_press, (100, 100))
        rect_tool.on_mouse_release(event_release, (150, 150))
        
        # Should have 2 objects
        assert len(self.scene.objects) == 2
        
        # Undo rectangle
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == 1
        
        # Undo polygonal lasso
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == 0
        
        # Redo polygonal lasso
        self.scene.cmd.redo(self.scene)
        assert len(self.scene.objects) == 1
        
        # Redo rectangle
        self.scene.cmd.redo(self.scene)
        assert len(self.scene.objects) == 2

    def test_magnetic_lasso_with_commands(self):
        """Test magnetic lasso tool creates undoable commands."""
        # This is a simplified test since magnetic lasso requires image processing
        tool = MagneticLassoTool(self.mock_canvas)
        
        # Mock the required methods
        tool.screen_to_image = Mock(return_value=(100, 100))
        tool._compute_magnetic_path = Mock(return_value=[(100, 100), (150, 120), (200, 150)])
        
        # Simulate magnetic lasso - place anchors and double-click to complete
        event_click1 = Mock(spec=QMouseEvent)
        event_click1.button.return_value = Qt.LeftButton
        event_click1.position.return_value = QPointF(100, 100)
        
        event_click2 = Mock(spec=QMouseEvent)
        event_click2.button.return_value = Qt.LeftButton
        event_click2.position.return_value = QPointF(150, 120)
        
        event_click3 = Mock(spec=QMouseEvent)
        event_click3.button.return_value = Qt.LeftButton
        event_click3.position.return_value = QPointF(200, 150)
        
        event_double = Mock(spec=QMouseEvent)
        
        # Place anchors
        tool.on_mouse_press(event_click1, (100, 100))
        tool.on_mouse_press(event_click2, (150, 120))
        tool.on_mouse_press(event_click3, (200, 150))
        
        # Double-click to complete
        tool.on_double_click(event_double, (200, 150))
        
        # Should have created a polygon
        assert len(self.scene.objects) == 1
        
        # Test undo
        initial_count = len(self.scene.objects)
        self.scene.cmd.undo(self.scene)
        assert len(self.scene.objects) == initial_count - 1