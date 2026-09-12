# src/tools/polygon_edit_tool.py
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (  # noqa: F401 - public module compatibility
    QMenu,
    QMessageBox,
)

from src.core.commands import (
    CommandResult,
    CommandStatus,
    CompositeCommand,
    DeleteObjectCommand,
    UpdatePolygonCommand,
)
from src.core.polygon_gesture import PolygonGestureTransaction
from src.tools.base_tool import BaseTool
from src.ui.context_menu_utils import fit_context_menu


class PolygonEditTool(BaseTool):
    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self.current_lang = "en"
        self.translations = {
            "en": {
                "move_vertex": "Move Vertex",
                "delete_vertex": "Delete Vertex",
                "delete_vertices": "Delete {count} Vertices",
                "add_vertex_here": "Add Vertex Here",
                "delete_polygon": "Delete Polygon",
                "delete_polygons": "Delete {count} Polygons",
                "select_all_vertices": "Select All Vertices",
                "clear_selection": "Clear Selection",
                "add_new_polygon": "Add New Polygon",
                "undo": "Undo",
                "redo": "Redo",
            },
            "pt": {
                "move_vertex": "Mover vértice",
                "delete_vertex": "Excluir vértice",
                "delete_vertices": "Excluir {count} vértices",
                "add_vertex_here": "Adicionar vértice aqui",
                "delete_polygon": "Excluir polígono",
                "delete_polygons": "Excluir {count} polígonos",
                "select_all_vertices": "Selecionar todos os vértices",
                "clear_selection": "Limpar seleção",
                "add_new_polygon": "Adicionar novo polígono",
                "undo": "Desfazer",
                "redo": "Refazer",
            },
        }
        self.selected_polygon_id: Optional[str] = None
        self.selected_vertex: Optional[int] = None
        # Each entry is (object_id, vertex_index). ``selected_vertex`` remains
        # the primary vertex for the existing gizmo contract.
        self.selected_vertices: set[Tuple[str, int]] = set()
        self.drag_start_pos: Optional[QPointF] = None
        self.adding_new = False
        self.multi_select = False
        self.selected_polygon_ids = set()
        self.mode = "select"  # Default mode
        self._vertex_transaction: Optional[PolygonGestureTransaction] = None
        self._vertex_origin_index: Optional[int] = None
        self._vertex_preview_position: Optional[Tuple[int, int]] = None
        self._hovered_vertex: Optional[Tuple[str, int]] = None
        self._context_image_pos: Optional[Tuple[int, int]] = None
        self._context_target: Optional[Tuple[str, str, Optional[int]]] = None
        self._last_error = ""

    def update_language(self, lang: str) -> None:
        """Update labels used by the polygon editor context menu."""

        self.current_lang = lang if lang in self.translations else "en"

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
            self._present_p2d05_error(
                RuntimeError(result.message or "The vertex edit was rejected."),
                operation="edit",
                severity="warning",
                channel="status",
            )
        elif result.status is CommandStatus.FAILED:
            self._present_p2d05_error(
                RuntimeError(result.message or "The vertex edit failed."),
                operation="edit",
                severity="critical",
                channel="modal",
            )

    def _execute_polygon_update(
        self,
        object_id: str,
        old_polygon: List[Tuple[int, int]],
        new_polygon: List[Tuple[int, int]],
        operation: str,
    ) -> Optional[CommandResult]:
        model = getattr(self.canvas_view, "model", None)
        manager = getattr(model, "cmd", None)
        if manager is None:
            self._present_p2d05_error(
                RuntimeError("Undo/Redo command history is unavailable."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None

        try:
            result = manager.execute(
                UpdatePolygonCommand(
                    object_id,
                    old_polygon,
                    new_polygon,
                ),
                model,
            )
        except Exception as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None

        self._report_vertex_result(result, operation)
        if result.changed:
            self.canvas_view.update()
            self._last_error = ""
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
            self._present_p2d05_error(
                RuntimeError("Select a vertex before moving it."),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return False

        model = getattr(self.canvas_view, "model", None)
        manager = getattr(model, "cmd", None)
        if model is None or manager is None:
            self._present_p2d05_error(
                RuntimeError("Undo/Redo command history is unavailable."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return False

        obj = model.objects.get(object_id)
        if (
            obj is None
            or not obj.polygon
            or not isinstance(vertex_index, int)
            or isinstance(vertex_index, bool)
            or vertex_index < 0
            or vertex_index >= len(obj.polygon)
        ):
            self._present_p2d05_error(
                KeyError("selected vertex"),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return False

        try:
            self._vertex_transaction = PolygonGestureTransaction(
                model,
                object_id,
            )
        except Exception as exc:
            self._vertex_transaction = None
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return False

        self._vertex_origin_index = vertex_index
        self._vertex_preview_position = tuple(obj.polygon[vertex_index])
        return True

    def begin_vertex_gizmo_gesture(self) -> bool:
        """Start a vertex transaction for the canvas gizmo."""

        if self._vertex_transaction is not None:
            return False
        return self._begin_vertex_gesture()

    def preview_vertex_gizmo_position(self, position: Tuple[int, int]) -> None:
        """Preview a gizmo-constrained vertex position."""

        self._preview_vertex_position((int(position[0]), int(position[1])))

    def finish_vertex_gizmo_gesture(self) -> Optional[CommandResult]:
        """Commit the active vertex transaction as one history entry."""

        return self._finish_vertex_gesture()

    def cancel_vertex_gizmo_gesture(self) -> bool:
        """Cancel the active vertex transaction without adding history."""

        return self._cancel_vertex_gesture()

    def selected_vertex_position(self) -> Optional[Tuple[int, int]]:
        """Return the selected vertex, including an active preview."""

        if self.selected_polygon_id is None or self.selected_vertex is None:
            return None
        if self._vertex_preview_position is not None:
            return (
                int(self._vertex_preview_position[0]),
                int(self._vertex_preview_position[1]),
            )
        obj = self.canvas_view.model.objects.get(self.selected_polygon_id)
        if obj is None or not obj.polygon:
            return None
        if self.selected_vertex < 0 or self.selected_vertex >= len(obj.polygon):
            return None
        return tuple(obj.polygon[self.selected_vertex])

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
            self._present_p2d05_error(
                KeyError("selected vertex"),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return

        try:
            snapper = getattr(self.canvas_view, "snap_vertex_position", None)
            if callable(snapper):
                target = tuple(snapper(position))
            else:
                target = (int(position[0]), int(position[1]))
            candidate = list(origin)
            candidate[vertex_index] = target
            preview = transaction.preview(candidate)
        except Exception as exc:
            try:
                if transaction.active:
                    transaction.cancel()
            except Exception as cleanup_exc:
                self._present_p2d05_error(
                    cleanup_exc,
                    operation="edit",
                    severity="critical",
                    channel="modal",
                )
            self._reset_vertex_gesture_state()
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
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
                try:
                    result = transaction.commit(
                        getattr(self.canvas_view.model, "cmd", None)
                    )
                except Exception as exc:
                    self._present_p2d05_error(
                        exc,
                        operation="edit",
                        severity="critical",
                        channel="modal",
                    )
                else:
                    self._report_vertex_result(
                        result,
                        "Vertex Movement",
                    )
                    if result.changed and object_id is not None:
                        self.selected_vertex = self._find_current_vertex_index(
                            object_id,
                            target,
                        )
                    if result.changed:
                        self._last_error = ""
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
        except Exception as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
        finally:
            self._reset_vertex_gesture_state()
            self.canvas_view.update()
        return restored

    def on_mouse_press(self, event: QMouseEvent, pos: Tuple[int, int]):
        if event.button() == Qt.MouseButton.RightButton:
            self._context_image_pos = (int(pos[0]), int(pos[1]))
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
                self.selected_vertices.clear()
                self._hovered_vertex = None
                self.canvas_view.update()
            return

        try:
            additive = bool(
                event.modifiers()
                & (
                    Qt.KeyboardModifier.ControlModifier
                    | Qt.KeyboardModifier.ShiftModifier
                )
            )
        except (AttributeError, TypeError):
            additive = False

        clicked_polygon_id, clicked_vertex = self._find_vertex_for_interaction(pos)
        if clicked_polygon_id is not None and clicked_vertex is not None:
            if not additive:
                self.selected_vertices = {(clicked_polygon_id, clicked_vertex)}
                self.selected_polygon_ids = {clicked_polygon_id}
            elif (clicked_polygon_id, clicked_vertex) in self.selected_vertices:
                self.selected_vertices.remove((clicked_polygon_id, clicked_vertex))
                remaining = sorted(self.selected_vertices)
                if remaining:
                    self.selected_polygon_id, self.selected_vertex = remaining[0]
                else:
                    self.selected_vertex = None
            else:
                self.selected_vertices.add((clicked_polygon_id, clicked_vertex))
                self.selected_polygon_ids.add(clicked_polygon_id)

            if (clicked_polygon_id, clicked_vertex) in self.selected_vertices:
                self.selected_polygon_id = clicked_polygon_id
                self.selected_vertex = clicked_vertex
            # A drag edits one vertex at a time. Multi-selection is still
            # retained for batch operations and is not accidentally collapsed.
            if not additive and len(self.selected_vertices) == 1:
                if self._begin_vertex_gesture():
                    self.drag_start_pos = QPointF(pos[0], pos[1])
                else:
                    self.drag_start_pos = None
            else:
                self.drag_start_pos = None
        else:
            clicked_polygon_id = self.find_polygon_at(pos)
            self.selected_vertex = None
            self.selected_vertices.clear()
            if additive:
                if clicked_polygon_id in self.selected_polygon_ids:
                    self.selected_polygon_ids.remove(clicked_polygon_id)
                elif clicked_polygon_id is not None:
                    self.selected_polygon_ids.add(clicked_polygon_id)
            else:
                self.selected_polygon_ids = (
                    {clicked_polygon_id} if clicked_polygon_id else set()
                )
            self.selected_polygon_id = (
                clicked_polygon_id
                if clicked_polygon_id is not None
                else next(iter(self.selected_polygon_ids), None)
            )
            self.drag_start_pos = None
        self._hovered_vertex = (
            (clicked_polygon_id, clicked_vertex)
            if clicked_polygon_id is not None and clicked_vertex is not None
            else None
        )
        self.canvas_view.update()

    def on_mouse_move(self, event: QMouseEvent, pos: Tuple[int, int]):
        if self.drag_start_pos is not None and self._vertex_transaction is not None:
            self._preview_vertex_position(pos)
        else:
            oid, vertex_index = self._find_vertex_for_interaction(pos)
            self._hovered_vertex = (
                (oid, vertex_index)
                if oid is not None and vertex_index is not None
                else None
            )
            if hasattr(self.canvas_view, "setCursor"):
                self.canvas_view.setCursor(
                    Qt.CursorShape.PointingHandCursor
                    if self._hovered_vertex is not None
                    else Qt.CursorShape.ArrowCursor
                )
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

    def _resolve_context_target(
        self, pos: Optional[Tuple[int, int]]
    ) -> Optional[Tuple[str, str, Optional[int]]]:
        """Bind the context menu to the geometry under the pointer.

        The previous implementation reused the last left-click selection. That
        made a right-click on a vertex open the polygon/object deletion path.
        Context actions must be based on the right-click hit test itself.
        """

        if pos is None:
            if (
                self.selected_polygon_id is not None
                and self.selected_vertex is not None
            ):
                self._context_target = (
                    "vertex",
                    self.selected_polygon_id,
                    self.selected_vertex,
                )
            elif self.selected_polygon_id is not None:
                self._context_target = (
                    "polygon",
                    self.selected_polygon_id,
                    None,
                )
            return self._context_target

        oid, vertex_index = self._find_vertex_for_interaction(pos)
        if oid is not None and vertex_index is not None:
            if (oid, vertex_index) not in self.selected_vertices:
                self.selected_polygon_id = oid
                self.selected_polygon_ids = {oid}
                self.selected_vertices = {(oid, vertex_index)}
            else:
                self.selected_polygon_id = oid
                self.selected_polygon_ids.add(oid)
            self.selected_vertex = vertex_index
            self._hovered_vertex = (oid, vertex_index)
            self._context_target = ("vertex", oid, vertex_index)
            self.canvas_view.update()
            return self._context_target

        oid = self.find_polygon_at(pos)
        if oid is not None:
            if oid not in self.selected_polygon_ids:
                self.selected_polygon_id = oid
                self.selected_polygon_ids = {oid}
            else:
                self.selected_polygon_id = oid
            self.selected_vertex = None
            self.selected_vertices.clear()
            self._hovered_vertex = None
            self._context_target = ("polygon", oid, None)
            self.canvas_view.update()
            return self._context_target

        self._context_target = None
        self._hovered_vertex = None
        return None

    def _find_vertex_for_interaction(
        self, pos: Tuple[int, int]
    ) -> Tuple[Optional[str], Optional[int]]:
        """Hit-test with preference for the active polygon.

        The compatibility fallback keeps lightweight tool doubles that expose
        the original one-argument ``find_vertex_at`` contract working.
        """

        try:
            return self.find_vertex_at(
                pos,
                preferred_polygon_id=self.selected_polygon_id,
            )
        except TypeError as exc:
            if "preferred_polygon_id" not in str(exc):
                raise
            return self.find_vertex_at(pos)

    def show_context_menu(self, event: QMouseEvent):
        target = self._resolve_context_target(self._context_image_pos)
        menu = QMenu(self.canvas_view)
        text = self.translations[self.current_lang]

        # The target is captured at menu-open time; actions cannot fall back to
        # a stale selection after the menu is displayed.
        has_selection = target is not None
        has_vertex = target is not None and target[0] == "vertex"
        vertex_count = len(self.selected_vertices)
        multiple_selected = len(self.selected_polygon_ids) > 1 and target is not None

        if has_selection and not multiple_selected:
            target_object_id = target[1]
            target_vertex_index = target[2]
            obj = self.canvas_view.model.objects.get(target_object_id)
            poly_len = len(obj.polygon) if obj and obj.polygon else 0

            if has_vertex:
                # Vertex-specific actions
                act_move_vertex = menu.addAction(text["move_vertex"])
                act_move_vertex.triggered.connect(lambda: self.set_mode("move_vertex"))

                if vertex_count > 1:
                    act_del_vertex = menu.addAction(
                        text["delete_vertices"].format(count=vertex_count)
                    )
                    act_del_vertex.triggered.connect(
                        lambda _checked=False: self.delete_selected_vertices()
                    )
                elif poly_len > 3:  # Can't delete if it would make polygon invalid
                    act_del_vertex = menu.addAction(text["delete_vertex"])

                    def delete_vertex_action(
                        _checked=False,
                        oid=target_object_id,
                        index=target_vertex_index,
                    ):
                        self.delete_selected_vertex(oid, index)

                    act_del_vertex.triggered.connect(delete_vertex_action)

                # Do not put object/polygon deletion next to a vertex target.
                # This prevents the destructive fallback that caused the
                # reported regression.
            else:
                menu.addSeparator()

                # Polygon actions
                act_add_vertex = menu.addAction(text["add_vertex_here"])
                act_add_vertex.triggered.connect(
                    lambda _checked=False: self.add_vertex_at_cursor(event)
                )

                act_del_polygon = menu.addAction(text["delete_polygon"])

                def delete_polygon_action(_checked=False, oid=target_object_id):
                    self.delete_selected_polygon([oid])

                act_del_polygon.triggered.connect(delete_polygon_action)

            menu.addSeparator()

        elif multiple_selected:
            # Multiple polygons selected
            act_del_polygons = menu.addAction(
                text["delete_polygons"].format(count=len(self.selected_polygon_ids))
            )
            act_del_polygons.triggered.connect(self.delete_selected_polygon)

            menu.addSeparator()

        # Global actions
        act_select_all = menu.addAction(text["select_all_vertices"])
        act_select_all.triggered.connect(self.select_all_vertices)

        act_clear_selection = menu.addAction(text["clear_selection"])
        act_clear_selection.triggered.connect(self.clear_selection)

        menu.addSeparator()

        act_add_new = menu.addAction(text["add_new_polygon"])
        act_add_new.triggered.connect(self.start_adding_new)

        menu.addSeparator()

        act_undo = menu.addAction(text["undo"])
        act_undo.triggered.connect(self.undo_last_action)

        act_redo = menu.addAction(text["redo"])
        act_redo.triggered.connect(self.redo_last_action)

        fit_context_menu(menu).exec(event.globalPos())

    def draw_overlay(self, painter: QPainter):
        """Draws selected polygons and handles directly in Image Space."""
        if not self.selected_polygon_ids:
            return

        transform = self.canvas_view.get_transform()
        zoom = self.canvas_view.get_zoom()

        painter.save()
        painter.setTransform(transform, combine=True)

        # Scale handle size inversely to zoom to keep constant screen size.
        # Handles use an outer contrast ring so they remain discoverable on
        # both the light image and the dark canvas.
        safe_zoom = zoom if zoom > 0 else 1.0
        handle_size = 10.0 / safe_zoom
        selected_handle_size = 16.0 / safe_zoom
        hovered_handle_size = 14.0 / safe_zoom

        for oid in self.selected_polygon_ids:
            obj = self.canvas_view.model.objects.get(oid)
            if obj and obj.polygon:
                # Draw selected polygon outline
                pen = QPen(QColor(255, 235, 80), 3)
                pen.setCosmetic(True)  # Width stays constant (2px)
                painter.setPen(pen)
                painter.setBrush(QColor(255, 235, 80, 28))

                points = [QPointF(float(x), float(y)) for x, y in obj.polygon]
                painter.drawPolygon(QPolygonF(points))

                # Draw vertices (Control Points)
                for i, (x, y) in enumerate(obj.polygon):
                    pt = QPointF(float(x), float(y))

                    is_selected = (oid, i) in self.selected_vertices or (
                        oid == self.selected_polygon_id and i == self.selected_vertex
                    )
                    is_hovered = self._hovered_vertex == (oid, i)
                    if is_selected:
                        size = selected_handle_size
                        painter.setPen(QPen(QColor(255, 255, 255), 2))
                        painter.setBrush(QColor(0, 220, 255, 235))
                        painter.drawEllipse(
                            QRectF(
                                pt.x() - size / 2 - 2.0 / safe_zoom,
                                pt.y() - size / 2 - 2.0 / safe_zoom,
                                size + 4.0 / safe_zoom,
                                size + 4.0 / safe_zoom,
                            )
                        )
                    elif is_hovered:
                        size = hovered_handle_size
                        painter.setPen(QPen(QColor(255, 255, 255), 2))
                        painter.setBrush(QColor(0, 220, 255, 210))
                    else:
                        size = handle_size
                        pen_handle = QPen(QColor(255, 255, 255), 2)
                        pen_handle.setCosmetic(True)
                        painter.setPen(pen_handle)
                        painter.setBrush(QColor(20, 130, 210, 230))

                    # Draw a circular target: it is easier to acquire than a
                    # small square and remains legible at high zoom levels.
                    painter.drawEllipse(
                        QRectF(pt.x() - size / 2, pt.y() - size / 2, size, size)
                    )

        painter.restore()

    def find_vertex_at(
        self,
        pos: Tuple[int, int],
        preferred_polygon_id: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[int]]:
        # Keep the hit target aligned with the visible 16px selected handle and
        # absorb small DPI/rounding differences from native mouse events.
        tolerance_screen = 14  # pixels on screen
        # Adjust tolerance to Image Space
        zoom = self.canvas_view.get_zoom()
        tolerance_image = tolerance_screen / zoom if zoom > 0 else tolerance_screen

        object_items = list(self.canvas_view.model.objects.items())
        if preferred_polygon_id is not None:
            object_items.sort(key=lambda item: item[0] != preferred_polygon_id)
        else:
            object_items.reverse()

        best: Optional[Tuple[float, str, int]] = None
        for oid, obj in object_items:
            if obj.polygon:
                for i, (x, y) in enumerate(obj.polygon):
                    distance = ((x - pos[0]) ** 2 + (y - pos[1]) ** 2) ** 0.5
                    if distance <= tolerance_image and (
                        best is None or distance < best[0]
                    ):
                        best = (distance, oid, i)
        return (best[1], best[2]) if best is not None else (None, None)

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
            self._present_p2d05_error(
                RuntimeError("Select a polygon before adding vertices."),
                operation="edit",
                severity="warning",
                channel="status",
            )

    def delete_selected_vertex(
        self,
        object_id: Optional[str] = None,
        vertex_index: Optional[int] = None,
    ):
        # Context-menu actions pass an immutable target captured at menu-open
        # time. Keyboard/toolbar callers continue to use the current selection.
        object_id = self.selected_polygon_id if object_id is None else object_id
        vertex_index = self.selected_vertex if vertex_index is None else vertex_index
        if object_id is None or vertex_index is None:
            self._present_p2d05_error(
                RuntimeError("Select a vertex before deleting it."),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return

        model = getattr(self.canvas_view, "model", None)
        obj = model.objects.get(object_id) if model is not None else None
        if (
            obj is None
            or not obj.polygon
            or not isinstance(vertex_index, int)
            or isinstance(vertex_index, bool)
            or vertex_index < 0
            or vertex_index >= len(obj.polygon)
        ):
            self._present_p2d05_error(
                KeyError("selected vertex"),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return
        if len(obj.polygon) <= 3:
            self._present_p2d05_error(
                ValueError("A polygon must keep at least three vertices."),
                operation="edit",
                severity="warning",
                channel="status",
            )
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
            self.selected_vertices.discard((object_id, vertex_index))
            self.selected_vertex = None
            self.canvas_view.update()

    def delete_selected_vertices(self):
        """Delete all selected vertices as one undoable operation."""

        selections = sorted(self.selected_vertices)
        if not selections:
            if (
                self.selected_polygon_id is not None
                and self.selected_vertex is not None
            ):
                selections = [(self.selected_polygon_id, self.selected_vertex)]
            else:
                self._present_p2d05_error(
                    RuntimeError("Select one or more vertices before deleting them."),
                    operation="edit",
                    severity="warning",
                    channel="status",
                )
                return

        grouped: dict[str, list[int]] = {}
        for object_id, vertex_index in selections:
            grouped.setdefault(object_id, []).append(vertex_index)

        commands = []
        model = getattr(self.canvas_view, "model", None)
        manager = getattr(model, "cmd", None)
        if model is None or manager is None:
            self._present_p2d05_error(
                RuntimeError("Undo/Redo command history is unavailable."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return

        for object_id, indices in grouped.items():
            obj = model.objects.get(object_id)
            if obj is None or not obj.polygon:
                self._present_p2d05_error(
                    KeyError(object_id),
                    operation="edit",
                    severity="warning",
                    channel="status",
                )
                return
            unique_indices = sorted(set(indices), reverse=True)
            if len(obj.polygon) - len(unique_indices) < 3:
                self._present_p2d05_error(
                    ValueError("A polygon must keep at least three vertices."),
                    operation="edit",
                    severity="warning",
                    channel="status",
                )
                return
            old_polygon = [tuple(point) for point in obj.polygon]
            new_polygon = list(old_polygon)
            for index in unique_indices:
                if index < 0 or index >= len(new_polygon):
                    self._present_p2d05_error(
                        KeyError("selected vertex"),
                        operation="edit",
                        severity="warning",
                        channel="status",
                    )
                    return
                new_polygon.pop(index)
            commands.append(UpdatePolygonCommand(object_id, old_polygon, new_polygon))

        try:
            result = manager.execute(CompositeCommand(commands), model)
        except Exception as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return
        self._report_vertex_result(result, "Delete Vertices")
        if result.changed:
            self.selected_vertices.clear()
            self.selected_vertex = None
            self.canvas_view.update()

    def add_vertex_at_pos(self, pos: Tuple[int, int]):
        object_id = self.selected_polygon_id
        model = getattr(self.canvas_view, "model", None)
        if object_id is None:
            self._present_p2d05_error(
                RuntimeError("Select a polygon before adding a vertex."),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return

        obj = model.objects.get(object_id) if model is not None else None
        if obj is None or not obj.polygon:
            self._present_p2d05_error(
                KeyError("selected polygon"),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return

        old_polygon = [tuple(point) for point in obj.polygon]
        try:
            target = (int(pos[0]), int(pos[1]))
        except (OverflowError, TypeError, ValueError) as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="warning",
                channel="status",
            )
            return

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
        model = getattr(self.canvas_view, "model", None)
        manager = getattr(model, "cmd", None)
        if model is None or manager is None:
            self._present_p2d05_error(
                RuntimeError("Undo/Redo command history is unavailable."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None

        requested = set(object_ids)
        missing = requested.difference(model.objects)
        if missing:
            self._present_p2d05_error(
                KeyError("selected object"),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return None

        targets = [object_id for object_id in model.objects if object_id in requested]
        if not targets:
            self._present_p2d05_error(
                KeyError("selected object"),
                operation="edit",
                severity="warning",
                channel="status",
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
                model,
            )
        except Exception as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None

        if result.status is CommandStatus.REJECTED:
            self._present_p2d05_error(
                RuntimeError(result.message or "The deletion was rejected."),
                operation="edit",
                severity="warning",
                channel="status",
            )
        elif result.status is CommandStatus.FAILED:
            self._present_p2d05_error(
                RuntimeError(result.message or "The deletion failed."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
        elif result.changed:
            self._last_error = ""
        return result

    def delete_selected_polygon(self, object_ids: Optional[List[str]] = None):
        if object_ids is not None:
            object_ids = list(object_ids)
            operation = "Delete Polygon"
        elif self.multi_select and self.selected_polygon_ids:
            object_ids = list(self.selected_polygon_ids)
            operation = "Delete Polygons"
        elif self.selected_polygon_id:
            object_ids = [self.selected_polygon_id]
            operation = "Delete Polygon"
        else:
            self._present_p2d05_error(
                RuntimeError("Select a polygon before deleting it."),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return

        result = self._execute_object_deletion(
            object_ids,
            operation,
        )
        if result is not None and result.changed:
            self.selected_polygon_ids.clear()
            self.selected_polygon_id = None
            self.selected_vertex = None
            self._last_error = ""
            self.canvas_view.update()

    def select_all_vertices(self):
        self.selected_vertices.clear()
        polygon_ids = set(self.selected_polygon_ids)
        if self.selected_polygon_id is not None:
            polygon_ids.add(self.selected_polygon_id)
        for object_id in polygon_ids:
            obj = self.canvas_view.model.objects.get(object_id)
            if obj is not None:
                self.selected_vertices.update(
                    (object_id, index) for index in range(len(obj.polygon))
                )
        if self.selected_vertices:
            self.selected_polygon_id, self.selected_vertex = sorted(
                self.selected_vertices
            )[0]
            self.canvas_view.update()

    def clear_selection(self):
        self.selected_polygon_id = None
        self.selected_vertex = None
        self.selected_vertices.clear()
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
