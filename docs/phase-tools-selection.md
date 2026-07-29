# Phase: Tools - Selection Infrastructure

## Overview

This phase implements the foundational infrastructure for selection tools in PolygonTool v2. The goal is to establish a consistent architecture for various selection methods while keeping implementations lightweight and extensible.

## Architecture

### BaseTool Class

Located in `src/tools/base_tool.py`, this abstract base class provides:

- **Coordinate Transformations**: `screen_to_image()` and `image_to_screen()` for handling zoom/pan
- **Snapping Utilities**: `snap_to_grid()` and `snap_to_angle()` for precise positioning
- **Selection Modes**: Support for add, subtract, and intersect operations
- **Event Interface**: Standardized mouse event handlers
- **Overlay Drawing**: Consistent drawing hooks for visual feedback

### Tool Interface

All selection tools implement:

```python
class MyTool(BaseTool):
    def on_mouse_press(self, event): pass
    def on_mouse_move(self, event): pass
    def on_mouse_release(self, event): pass
    def draw_overlay(self, painter): pass
    def cancel(self): pass
```

## Implemented Tools

### 1. LassoTool (`src/tools/lasso_tool.py`)
- Free-form selection by mouse dragging
- Stores path points during drawing
- TODO: Implement selection mask creation

### 2. PolygonalLassoTool (`src/tools/polygonal_lasso.py`)
- Straight-edged selection via vertex placement
- Double-click to complete polygon
- TODO: Implement polygon validation and selection

### 3. MagneticLassoTool (`src/tools/magnetic_lasso.py`)
- Edge-guided selection using image analysis
- Places anchor points, computes optimal paths
- TODO: Integrate with existing magnetic lasso algorithms

### 4. RectSelectionTool (`src/tools/rect_selection.py`)
- Rectangular selection by drag
- Simple bounding box selection
- TODO: Implement rectangle mask creation

### 5. EllipseSelectionTool (`src/tools/ellipse_selection.py`)
- Elliptical selection by drag
- Center and radius-based selection
- TODO: Implement ellipse mask creation

### 6. PenTool (`src/tools/pen_tool.py`)
- Free-form drawing tool
- Can be used for custom selections
- TODO: Implement smoothing and selection modes

## Integration Points

### Canvas View
- Tools register with `CanvasView` for event handling
- Overlay drawing integrated into paint cycle
- Coordinate transformations provided by canvas

### Scene Model
- Selection results stored in scene objects
- Support for multiple selection modes
- TODO: Implement selection mask storage

### UI Integration
- Tool selection via toolbar/menu
- Visual feedback during selection
- TODO: Implement tool property panels

## Testing

Basic import test confirms all modules load without errors:

```bash
python -c "import src.tools.base_tool, src.tools.lasso_tool, src.tools.pen_tool; print('IMPORTS_OK')"
```

## Next Steps

1. **Complete Tool Implementations**: Fill in TODOs for each tool's core functionality
2. **Selection Mask System**: Implement mask creation and storage
3. **UI Integration**: Connect tools to canvas and toolbar
4. **Advanced Features**: Add tool-specific options (brush size, smoothing, etc.)
5. **Performance Optimization**: Optimize drawing and mask operations

## Dependencies

- PySide6 for Qt GUI events and painting
- NumPy for coordinate calculations
- Existing PolygonTool scene and canvas infrastructure