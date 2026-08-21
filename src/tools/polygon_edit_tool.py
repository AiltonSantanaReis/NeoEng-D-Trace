# src/tools/polygon_edit_tool.py
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QMenu, QMessageBox

from src.core.commands import (
    CommandResult,
    CommandStatus,
    CompositeCommand,
    DeleteObjectCommand,
    UpdatePolygonCommand,
)
from src.core.polygon_gesture import PolygonGestureTransaction
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
        self._vertex_transaction: Optional[PolygonGestureTransaction] = None
        self._vertex_origin_index: Optional[int] = None
        self._vertex_preview_position: Optional[Tuple[int, int]] = None

    def set_mode(self, mode: str):
        """Set the current tool mode."""
        if mode != self.mode and self._vertex_transaction is not None:
            self._cancel_vertex_gesture()
        self.mode = mode

    def _report_vertex_result(
        self,
        result: CommandResult,
        operation: str,
    ) -> None:
        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self.canvas_view,
                f"{operation} Rejected",
                result.message or "The vertex edit was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                result.message or "The vertex edit failed.",
            )

    def _execute_polygon_update(
        self,
        object_id: str,
        old_polygon: List[Tuple[int, int]],
        new_polygon: List[Tuple[int, int]],
        operation: str,
    ) -> Optional[CommandResult]:
        manager = getattr(self.canvas_view.model, "cmd", None)
        if manager is None:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return None

        try:
            result = manager.execute(
                UpdatePolygonCommand(
                    object_id,
                    old_polygon,
                    new_polygon,
                ),
                self.canvas_view.model,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                str(exc),
            )
            return None

        self._report_vertex_result(result, operation)
        if result.changed:
            self.canvas_view.update()
        return result

    @staticmethod
    def _find_vertex_index_in_polygon(
        polygon: List[Tuple[int, int]],
        position: Tuple[int, int],
    ) -> Optional[int]:
        target = tuple(position)
        for index, point in enumerate(polygon):
            if tuple(point) == target:
                return index
        return None

    def _find_current_vertex_index(
        self,
        object_id: str,
        position: Optional[Tuple[int, int]],
    ) -> Optional[int]:
        if position is None:
            return None
        obj = self.canvas_view.model.objects.get(object_id)
        if obj is None or not obj.polygon:
            return None
        return self._find_vertex_index_in_polygon(
            [tuple(point) for point in obj.polygon],
            position,
        )

    def _reset_vertex_gesture_state(self) -> None:
        self._vertex_transaction = None
        self._vertex_origin_index = None
        self._vertex_preview_position = None
        self.drag_start_pos = None

    def _begin_vertex_gesture(self) -> bool:
        object_id = self.selected_polygon_id
        vertex_index = self.selected_vertex
        if object_id is None or vertex_index is None:
            return False

        manager = getattr(self.canvas_view.model, "cmd", None)
        if manager is None:
            QMessageBox.critical(
                self.canvas_view,
                "Vertex Movement Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return False

        obj = self.canvas_view.model.objects.get(object_id)
        if (
            obj is None
            or not obj.polygon
            or vertex_index < 0
            or vertex_index >= len(obj.polygon)
        ):
            QMessageBox.warning(
                self.canvas_view,
                "Vertex Movement Rejected",
                "The selected vertex is no longer available.",
            )
            return False

        try:
            self._vertex_transaction = PolygonGestureTransaction(
                self.canvas_view.model,
                object_id,
            )
        except Exception as exc:
            self._vertex_transaction = None
            QMessageBox.critical(
                self.canvas_view,
                "Vertex Movement Failed",
                str(exc),
            )
            return False

        self._vertex_origin_index = vertex_index
        self._vertex_preview_position = tuple(obj.polygon[vertex_index])
        return True

    def _preview_vertex_position(
        self,
        position: Tuple[int, int],
    ) -> None:
        transaction = self._vertex_transaction
        vertex_index = self._vertex_origin_index
        if transaction is None or not transaction.active or vertex_index is None:
            return

        origin = transaction.origin_polygon
        if vertex_index < 0 or vertex_index >= len(origin):
            self._cancel_vertex_gesture()
            QMessageBox.warning(
                self.canvas_view,
                "Vertex Movement Rejected",
                "The selected vertex is no longer available.",
            )
            return

        snapper = getattr(self.canvas_view, "snap_vertex_position", None)
        if callable(snapper):
            target = tuple(snapper(position))
        else:
            target = (int(position[0]), int(position[1]))
        candidate = list(origin)
        candidate[vertex_index] = target

        try:
            preview = transaction.preview(candidate)
        except Exception as exc:
            try:
                if transaction.active:
                    transaction.cancel()
            except Exception:
                pass
            self._reset_vertex_gesture_state()
            QMessageBox.critical(
                self.canvas_view,
                "Vertex Movement Failed",
                str(exc),
            )
            self.canvas_view.update()
            return

        self._vertex_preview_position = target
        preview_index = self._find_vertex_index_in_polygon(
            preview,
            target,
        )
        if preview_index is not None:
            self.selected_vertex = preview_index
        self.canvas_view.update()

    def _finish_vertex_gesture(self) -> Optional[CommandResult]:
        transaction = self._vertex_transaction
        object_id = self.selected_polygon_id
        target = self._vertex_preview_position
        result: Optional[CommandResult] = None

        try:
            if transaction is not None and transaction.active:
                result = transaction.commit(
                    getattr(self.canvas_view.model, "cmd", None)
                )
                self._report_vertex_result(
                    result,
                    "Vertex Movement",
                )
                if result.changed and object_id is not None:
                    self.selected_vertex = self._find_current_vertex_index(
                        object_id,
                        target,
                    )
        finally:
            self._reset_vertex_gesture_state()
            self.canvas_view.update()

        return result

    def _cancel_vertex_gesture(self) -> bool:
        transaction = self._vertex_transaction
        restored = False
        try:
            if transaction is not None and transaction.active:
                restored = transaction.cancel()
        finally:
            self._reset_vertex_gesture_state()
            self.canvas_view.update()
        return restored

    def on_mouse_press(self, event: QMouseEvent, pos: Tuple[int, int]):
        if event.button() == Qt.MouseButton.RightButton:
            if self._vertex_transaction is not None:
                self._cancel_vertex_gesture()
                return
            if self.adding_new:
                self.adding_new = False
                self.canvas_view.update()
            else:
                self.show_context_menu(event)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

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
            return

        self.selected_polygon_id, self.selected_vertex = self.find_vertex_at(pos)
        if self.selected_polygon_id is None:
            self.selected_polygon_id = self.find_polygon_at(pos)
            self.selected_vertex = None
            self.selected_polygon_ids = (
                {self.selected_polygon_id} if self.selected_polygon_id else set()
            )
            self.drag_start_pos = None
        else:
            self.selected_polygon_ids = {self.selected_polygon_id}
            if self._begin_vertex_gesture():
                self.drag_start_pos = QPointF(pos[0], pos[1])
            else:
                self.drag_start_pos = None
        self.canvas_view.update()

    def on_mouse_move(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self.drag_start_pos is not None and self._vertex_transaction is not None:
            self._preview_vertex_position(pos)
        self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self._vertex_transaction is not None:
            self._finish_vertex_gesture()
        else:
            self.drag_start_pos = None
            self.canvas_view.update()

    def on_cancel(self):
        if self._vertex_transaction is not None:
            self._cancel_vertex_gesture()
        self.adding_new = False
        self.drag_start_pos = None
        self.canvas_view.update()

    def on_key_press(self, event) -> bool:
        if event.key() == Qt.Key.Key_Escape and self._vertex_transaction is not None:
            self._cancel_vertex_gesture()
            return True
        if event.key() == Qt.Key.Key_Escape and self.adding_new:
            self.adding_new = False
            self.canvas_view.update()
            return True
        return False

    def on_undo(self) -> bool:
        if self._vertex_transaction is not None:
            self._cancel_vertex_gesture()
            return True
        return False

    def on_redo(self) -> bool:
        if self._vertex_transaction is not None:
            self._cancel_vertex_gesture()
            return True
        return False

    def show_context_menu(self, event: QMouseEvent):
        menu = QMenu(self.canvas_view)

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
                act_move_vertex.triggered.connect(lambda: self.set_mode("move_vertex"))

                if poly_len > 3:  # Can't delete if it would make polygon invalid
                    act_del_vertex = menu.addAction("Delete Vertex")
                    act_del_vertex.triggered.connect(self.delete_selected_vertex)

            menu.addSeparator()

            # Polygon actions
            act_add_vertex = menu.addAction("Add Vertex Here")
            act_add_vertex.triggered.connect(lambda: self.add_vertex_at_cursor(event))

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
                pen.setCosmetic(True)  # Width stays constant (2px)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

                points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                painter.drawPolygon(QPolygonF(points))

                # Draw vertices (Control Points)
                for i, (x, y) in enumerate(obj.polygon):
                    pt = QPointF(float(x), float(y))

                    if oid == self.selected_polygon_id and i == self.selected_vertex:
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
                    painter.drawRect(
                        QRectF(pt.x() - size / 2, pt.y() - size / 2, size, size)
                    )

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

    def point_in_polygon(self, pos: Tuple[int, int], points: List[QPointF]) -> bool:
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
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
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
        object_id = self.selected_polygon_id
        vertex_index = self.selected_vertex
        if object_id is None or vertex_index is None:
            return

        obj = self.canvas_view.model.objects.get(object_id)
        if (
            obj is None
            or not obj.polygon
            or len(obj.polygon) <= 3
            or vertex_index < 0
            or vertex_index >= len(obj.polygon)
        ):
            return

        old_polygon = [tuple(point) for point in obj.polygon]
        new_polygon = list(old_polygon)
        new_polygon.pop(vertex_index)

        result = self._execute_polygon_update(
            object_id,
            old_polygon,
            new_polygon,
            "Delete Vertex",
        )
        if result is not None and result.changed:
            self.selected_vertex = None
            self.canvas_view.update()

    def add_vertex_at_pos(self, pos: Tuple[int, int]):
        object_id = self.selected_polygon_id
        if object_id is None:
            return

        obj = self.canvas_view.model.objects.get(object_id)
        if obj is None or not obj.polygon:
            return

        old_polygon = [tuple(point) for point in obj.polygon]
        target = (int(pos[0]), int(pos[1]))

        min_dist = float("inf")
        insert_idx = len(old_polygon)
        for index in range(len(old_polygon)):
            point_a = old_polygon[index]
            point_b = old_polygon[(index + 1) % len(old_polygon)]
            distance = self.point_to_line_distance(
                target,
                point_a,
                point_b,
            )
            if distance < min_dist:
                min_dist = distance
                insert_idx = (index + 1) % len(old_polygon)

        new_polygon = list(old_polygon)
        new_polygon.insert(insert_idx, target)

        result = self._execute_polygon_update(
            object_id,
            old_polygon,
            new_polygon,
            "Add Vertex",
        )
        if result is not None and result.changed:
            self.selected_vertex = self._find_current_vertex_index(
                object_id,
                target,
            )
            self.canvas_view.update()

    def _execute_object_deletion(
        self,
        object_ids: List[str],
        operation: str,
    ) -> Optional[CommandResult]:
        manager = getattr(self.canvas_view.model, "cmd", None)
        if manager is None:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Unavailable",
                "Undo/Redo command history is unavailable.",
            )
            return None

        requested = set(object_ids)
        missing = requested.difference(self.canvas_view.model.objects)
        if missing:
            QMessageBox.warning(
                self.canvas_view,
                f"{operation} Rejected",
                "The selection changed before deletion; " "no objects were removed.",
            )
            return None

        targets = [
            object_id
            for object_id in self.canvas_view.model.objects
            if object_id in requested
        ]
        if not targets:
            QMessageBox.warning(
                self.canvas_view,
                f"{operation} Rejected",
                "No selected object is available for deletion.",
            )
            return None

        command = (
            DeleteObjectCommand(targets[0])
            if len(targets) == 1
            else CompositeCommand(
                [DeleteObjectCommand(object_id) for object_id in targets]
            )
        )

        try:
            result = manager.execute(
                command,
                self.canvas_view.model,
            )
        except Exception as exc:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                str(exc),
            )
            return None

        if result.status is CommandStatus.REJECTED:
            QMessageBox.warning(
                self.canvas_view,
                f"{operation} Rejected",
                result.message or "The deletion was rejected.",
            )
        elif result.status is CommandStatus.FAILED:
            QMessageBox.critical(
                self.canvas_view,
                f"{operation} Failed",
                result.message or "The deletion failed.",
            )
        return result

    def delete_selected_polygon(self):
        if self.multi_select and self.selected_polygon_ids:
            object_ids = list(self.selected_polygon_ids)
            operation = "Delete Polygons"
        elif self.selected_polygon_id:
            object_ids = [self.selected_polygon_id]
            operation = "Delete Polygon"
        else:
            return

        result = self._execute_object_deletion(
            object_ids,
            operation,
        )
        if result is not None and result.changed:
            self.selected_polygon_ids.clear()
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
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.undo(self.canvas_view.model)

    def redo_last_action(self):
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
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

        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
