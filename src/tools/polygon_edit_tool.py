# src/tools/polygon_edit_tool.py
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QMessageBox, QMenu

from src.tools.base_tool import BaseTool


class PolygonEditTool(BaseTool):
    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self.selected_polygon_id: Optional[str] = None
        self.selected_vertex: Optional[int] = None
        self.drag_start_pos: Optional[QPointF] = None
        self.adding_new = False
        self.multi_select = False
        self.selected_polygon_ids = set()
        self.mode = "select"  # Default mode

    def set_mode(self, mode: str):
        """Set the current tool mode."""
        self.mode = mode

    def on_mouse_press(self, event: QMouseEvent, pos: Tuple[int, int]):
        if event.button() == Qt.MouseButton.RightButton:
            if self.adding_new:
                self.adding_new = False
                self.canvas_view.update()
            else:
                self.show_context_menu(event)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self.adding_new:
                self.add_vertex_at_pos(pos)
                return
            if self.multi_select:
                oid = self.find_polygon_at(pos)
                if oid:
                    if oid in self.selected_polygon_ids:
                        self.selected_polygon_ids.remove(oid)
                    else:
                        self.selected_polygon_ids.add(oid)
                    self.selected_vertex = None
                    self.canvas_view.update()
            else:
                self.drag_start_pos = QPointF(pos[0], pos[1])
                # Find polygon and vertex under cursor
                self.selected_polygon_id, self.selected_vertex = (
                    self.find_vertex_at(pos)
                )
                if self.selected_polygon_id is None:
                    # Select polygon if no vertex found
                    self.selected_polygon_id = self.find_polygon_at(pos)
                    self.selected_vertex = None
                    self.selected_polygon_ids = (
                        {self.selected_polygon_id}
                        if self.selected_polygon_id
                        else set()
                    )
                else:
                    self.selected_polygon_ids = {self.selected_polygon_id}
                self.canvas_view.update()

    def on_mouse_move(self, event: QMouseEvent, pos: Tuple[int, int]):
        if (
            self.drag_start_pos
            and self.selected_vertex is not None
            and self.selected_polygon_id
        ):
            # Move vertex
            obj = self.canvas_view.model.objects.get(self.selected_polygon_id)
            if obj and obj.polygon:
                obj.polygon[self.selected_vertex] = (pos[0], pos[1])
                # Update collision if exists
                if (
                    hasattr(self.canvas_view.model, "collision_shapes")
                    and self.selected_polygon_id
                    in self.canvas_view.model.collision_shapes
                ):
                    self.canvas_view.model.collision_shapes[
                        self.selected_polygon_id
                    ][self.selected_vertex] = (float(pos[0]), float(pos[1]))
                self.canvas_view.model._notify()
        self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self.drag_start_pos:
            # Create command for undo if moved
            if self.selected_vertex is not None and self.selected_polygon_id:
                # For simplicity, we'll update directly. In full
                # implementation, use ExpandContractCommand
                pass
        self.drag_start_pos = None
        self.canvas_view.update()

    def show_context_menu(self, event: QMouseEvent):
        menu = QMenu(self.canvas_view)
        menu.setStyleSheet(
            """
            QMenu { background-color: #2d2d30; color: #e6e6e6;
            border: 1px solid #3f3f46; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #2a6f97; }
            QMenu::separator { height: 1px; background: #3f3f46;
            margin: 5px 0; }
        """
        )

        # Check what's selected
        has_selection = self.selected_polygon_id is not None or bool(
            self.selected_polygon_ids
        )
        has_vertex = self.selected_vertex is not None
        multiple_selected = len(self.selected_polygon_ids) > 1

        if has_selection and not multiple_selected:
            obj = self.canvas_view.model.objects.get(self.selected_polygon_id)
            poly_len = len(obj.polygon) if obj and obj.polygon else 0

            if has_vertex:
                # Vertex-specific actions
                act_move_vertex = menu.addAction("Move Vertex")
                act_move_vertex.triggered.connect(
                    lambda: self.set_mode("move_vertex")
                )

                if (
                    poly_len > 3
                ):  # Can't delete if it would make polygon invalid
                    act_del_vertex = menu.addAction("Delete Vertex")
                    act_del_vertex.triggered.connect(
                        self.delete_selected_vertex
                    )

            menu.addSeparator()

            # Polygon actions
            act_add_vertex = menu.addAction("Add Vertex Here")
            act_add_vertex.triggered.connect(
                lambda: self.add_vertex_at_cursor(event)
            )

            act_del_polygon = menu.addAction("Delete Polygon")
            act_del_polygon.triggered.connect(self.delete_selected_polygon)

            menu.addSeparator()

        elif multiple_selected:
            # Multiple polygons selected
            act_del_polygons = menu.addAction(
                f"Delete {len(self.selected_polygon_ids)} Polygons"
            )
            act_del_polygons.triggered.connect(self.delete_selected_polygon)

            menu.addSeparator()

        # Global actions
        act_select_all = menu.addAction("Select All Vertices")
        act_select_all.triggered.connect(self.select_all_vertices)

        act_clear_selection = menu.addAction("Clear Selection")
        act_clear_selection.triggered.connect(self.clear_selection)

        menu.addSeparator()

        act_add_new = menu.addAction("Add New Polygon")
        act_add_new.triggered.connect(self.start_adding_new)

        menu.addSeparator()

        act_undo = menu.addAction("Undo")
        act_undo.triggered.connect(self.undo_last_action)

        act_redo = menu.addAction("Redo")
        act_redo.triggered.connect(self.redo_last_action)

        menu.exec(event.globalPos())

    def draw_overlay(self, painter: QPainter):
        """Draws selected polygons and handles directly in Image Space."""
        if not self.selected_polygon_ids:
            return

        transform = self.canvas_view.get_transform()
        zoom = self.canvas_view.get_zoom()
        
        painter.save()
        painter.setTransform(transform, combine=True)

        # Scale handle size inversely to zoom to keep constant screen size
        handle_size = 8.0 / zoom if zoom > 0 else 8.0
        selected_handle_size = 12.0 / zoom if zoom > 0 else 12.0

        for oid in self.selected_polygon_ids:
            obj = self.canvas_view.model.objects.get(oid)
            if obj and obj.polygon:
                # Draw selected polygon outline
                pen = QPen(QColor(255, 255, 0), 2)
                pen.setCosmetic(True) # Width stays constant (2px)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                
                points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                painter.drawPolygon(QPolygonF(points))

                # Draw vertices (Control Points)
                for i, (x, y) in enumerate(obj.polygon):
                    pt = QPointF(float(x), float(y))
                    
                    if (
                        oid == self.selected_polygon_id
                        and i == self.selected_vertex
                    ):
                        # Selected vertex: larger red square
                        painter.setPen(QPen(QColor(255, 0, 0), 2))
                        painter.setBrush(QColor(255, 0, 0, 150))
                        size = selected_handle_size
                    else:
                        # Normal vertex: blue square
                        pen_handle = QPen(QColor(0, 150, 255), 1)
                        pen_handle.setCosmetic(True)
                        painter.setPen(pen_handle)
                        painter.setBrush(QColor(0, 150, 255, 100))
                        size = handle_size

                    # Draw rect centered on point
                    painter.drawRect(QRectF(
                        pt.x() - size / 2, 
                        pt.y() - size / 2, 
                        size, size
                    ))

        painter.restore()

    def find_vertex_at(
        self, pos: Tuple[int, int]
    ) -> Tuple[Optional[str], Optional[int]]:
        tolerance_screen = 10  # pixels on screen
        # Adjust tolerance to Image Space
        zoom = self.canvas_view.get_zoom()
        tolerance_image = tolerance_screen / zoom if zoom > 0 else tolerance_screen
        
        for oid, obj in self.canvas_view.model.objects.items():
            if obj.polygon:
                for i, (x, y) in enumerate(obj.polygon):
                    if (
                        abs(x - pos[0]) < tolerance_image
                        and abs(y - pos[1]) < tolerance_image
                    ):
                        return oid, i
        return None, None

    def find_polygon_at(self, pos: Tuple[int, int]) -> Optional[str]:
        # Simple point-in-polygon check
        for oid, obj in reversed(list(self.canvas_view.model.objects.items())):
            if obj.polygon and len(obj.polygon) >= 3:
                points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                if self.point_in_polygon(pos, points):
                    return oid
        return None

    def point_in_polygon(
        self, pos: Tuple[int, int], points: List[QPointF]
    ) -> bool:
        # Ray casting algorithm
        x, y = pos
        n = len(points)
        inside = False
        p1x, p1y = points[0].x(), points[0].y()
        for i in range(1, n + 1):
            p2x, p2y = points[i % n].x(), points[i % n].y()
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (
                                p2y - p1y
                            ) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def add_vertex_at_cursor(self, event: QMouseEvent):
        pos = self.screen_to_image(event.pos().x(), event.pos().y())
        self.add_vertex_at_pos((int(pos[0]), int(pos[1])))

    def start_adding_new(self):
        if self.selected_polygon_id:
            self.adding_new = True
        else:
            QMessageBox.information(
                self.canvas_view,
                "Info",
                "Select a polygon first to add vertices.",
            )

    def delete_selected_vertex(self):
        if self.selected_polygon_id and self.selected_vertex is not None:
            obj = self.canvas_view.model.objects.get(self.selected_polygon_id)
            if obj and obj.polygon and len(obj.polygon) > 3:
                obj.polygon.pop(self.selected_vertex)
                # Update collision if exists
                if (
                    hasattr(self.canvas_view.model, "collision_shapes")
                    and self.selected_polygon_id
                    in self.canvas_view.model.collision_shapes
                ):
                    self.canvas_view.model.collision_shapes[
                        self.selected_polygon_id
                    ].pop(self.selected_vertex)
                self.canvas_view.model._notify()
                self.selected_vertex = None
                self.canvas_view.update()

    def add_vertex_at_pos(self, pos: Tuple[int, int]):
        if self.selected_polygon_id:
            obj = self.canvas_view.model.objects.get(self.selected_polygon_id)
            if obj and obj.polygon:
                # Find closest edge and insert
                min_dist = float("inf")
                insert_idx = len(obj.polygon)
                for i in range(len(obj.polygon)):
                    p1 = obj.polygon[i]
                    p2 = obj.polygon[(i + 1) % len(obj.polygon)]
                    dist = self.point_to_line_distance(pos, p1, p2)
                    if dist < min_dist:
                        min_dist = dist
                        insert_idx = (i + 1) % len(obj.polygon)

                obj.polygon.insert(insert_idx, pos)
                # Update collision
                if (
                    hasattr(self.canvas_view.model, "collision_shapes")
                    and self.selected_polygon_id
                    in self.canvas_view.model.collision_shapes
                ):
                    self.canvas_view.model.collision_shapes[
                        self.selected_polygon_id
                    ].insert(insert_idx, (float(pos[0]), float(pos[1])))
                self.canvas_view.model._notify()
                self.selected_vertex = insert_idx
                self.canvas_view.update()

    def delete_selected_polygon(self):
        if self.multi_select and self.selected_polygon_ids:
            for oid in list(self.selected_polygon_ids):
                self.canvas_view.model.remove_object(oid)
            self.selected_polygon_ids.clear()
            self.selected_polygon_id = None
            self.selected_vertex = None
        elif self.selected_polygon_id:
            self.canvas_view.model.remove_object(self.selected_polygon_id)
            self.selected_polygon_id = None
            self.selected_vertex = None
        self.canvas_view.update()

    def select_all_vertices(self):
        # Select the first vertex of the current polygon
        if self.selected_polygon_id:
            self.selected_vertex = 0
            self.canvas_view.update()

    def clear_selection(self):
        self.selected_polygon_id = None
        self.selected_vertex = None
        self.selected_polygon_ids.clear()
        self.canvas_view.update()

    def undo_last_action(self):
        if (
            hasattr(self.canvas_view.model, "cmd")
            and self.canvas_view.model.cmd
        ):
            self.canvas_view.model.cmd.undo(self.canvas_view.model)

    def redo_last_action(self):
        if (
            hasattr(self.canvas_view.model, "cmd")
            and self.canvas_view.model.cmd
        ):
            self.canvas_view.model.cmd.redo(self.canvas_view.model)

    def point_to_line_distance(
        self,
        point: Tuple[int, int],
        line_start: Tuple[int, int],
        line_end: Tuple[int, int],
    ) -> float:
        # Distance from point to line segment
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end

        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        t = max(
            0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy))
        )
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5