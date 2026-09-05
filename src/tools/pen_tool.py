# src/tools/pen_tool.py
"""Pen creation and persistent cubic Bézier handle editing."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (  # noqa: F401 - public module compatibility
    QMenu,
    QMessageBox,
)

from src.core.bezier_geometry import (
    BezierSegments,
    canonicalize_beziers,
    cubic_bezier_point,
    sample_beziers,
)
from src.core.commands import (
    CommandStatus,
    CreateBezierObjectCommand,
    HandleMoveCommand,
)
from src.core.operational_limits import MAX_POLYGON_POINTS

from .base_tool import BaseTool


def bezier_point(
    t: float,
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> Tuple[float, float]:
    """Backward-compatible wrapper around the canonical cubic evaluator."""

    return cubic_bezier_point(t, p0, p1, p2, p3)


def bezier_curve(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    segments: int = 20,
) -> List[Tuple[float, float]]:
    """Backward-compatible sampling helper for one segment."""

    return sample_beziers(
        [(p0, p1, p2, p3)],
        steps_per_segment=segments,
    )


@dataclass
class _HandleEditState:
    object_id: str
    segment_index: int
    handle_index: int
    old_pos: Tuple[float, float]
    old_beziers: BezierSegments
    old_polygon: List[Tuple[int, int]]
    preview_beziers: BezierSegments
    preview_polygon: List[Tuple[int, int]]


class BezierNode:
    def __init__(self, anchor: Tuple[float, float]):
        self.anchor = (float(anchor[0]), float(anchor[1]))
        self.handle_in = self.anchor
        self.handle_out = self.anchor


class PenTool(BaseTool):
    """Create Bézier objects and edit their handles through command history."""

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self._nodes: List[BezierNode] = []
        self._selected_node: Optional[BezierNode] = None
        self._selected_handle: Optional[str] = None
        self._is_placing_handle = False
        self._curve_segments = 20
        self._editing_object_id: Optional[str] = None
        self._closed = False
        self._close_tolerance = 12.0
        self._cursor_position: Optional[Tuple[float, float]] = None
        self._active_handle_edit: Optional[_HandleEditState] = None
        self._last_command_result = None
        self._last_error = ""

        self.current_lang = "en"
        self.translations = {
            "en": {
                "cancel_selection": "Cancel Selection",
                "undo": "Undo",
                "redo": "Redo",
            },
            "pt": {
                "cancel_selection": "Cancelar Seleção",
                "undo": "Desfazer",
                "redo": "Refazer",
            },
        }
        self._load_selected_bezier_object()

    def _model(self):
        return getattr(self.canvas_view, "model", None)

    def _nodes_beziers(self) -> Optional[BezierSegments]:
        try:
            return self._nodes_to_beziers()
        except (OverflowError, ValueError):
            return None

    def _object_bezier_state(
        self, obj
    ) -> Optional[Tuple[BezierSegments, List[Tuple[int, int]]]]:
        beziers = getattr(obj, "beziers", None) if obj is not None else None
        if beziers is None:
            return None
        try:
            model = self._model()
            if model is not None and hasattr(model, "prepare_bezier_geometry"):
                canonical, _polygon = model.prepare_bezier_geometry(
                    beziers,
                    steps_per_segment=self._curve_segments,
                )
            else:
                canonical = canonicalize_beziers(beziers)
        except (OverflowError, TypeError, ValueError):
            return None
        return canonical, copy.deepcopy(obj.polygon)

    def _active_preview_matches_model(self) -> bool:
        edit = self._active_handle_edit
        if edit is None:
            return False
        model = self._model()
        obj = model.objects.get(edit.object_id) if model is not None else None
        state = self._object_bezier_state(obj)
        if state is None:
            return False
        return state == (edit.preview_beziers, edit.preview_polygon)

    def _discard_active_handle_edit(self, *, restore_preview: bool) -> bool:
        if self._active_handle_edit is None:
            return False
        if restore_preview and self._active_preview_matches_model():
            self._restore_handle_preview()
        self._active_handle_edit = None
        self._selected_node = None
        self._selected_handle = None
        self._is_placing_handle = False
        self._closed = False
        self._cursor_position = None
        return True

    def _cancel_active_handle_edit(self) -> bool:
        if not self._discard_active_handle_edit(restore_preview=True):
            return False
        self._load_selected_bezier_object()
        self.canvas_view.update()
        return True

    def _clear_loaded_bezier_object(self, *, restore_preview: bool = True) -> None:
        self._discard_active_handle_edit(restore_preview=restore_preview)
        self._editing_object_id = None
        self._nodes = []
        self._selected_node = None
        self._selected_handle = None
        self._is_placing_handle = False

    def _load_selected_bezier_object(self) -> bool:
        model = self._model()
        object_id = getattr(model, "selected_id", None) if model is not None else None
        obj = (
            model.objects.get(object_id)
            if model is not None and object_id is not None
            else None
        )
        state = self._object_bezier_state(obj)
        if state is None:
            if self._editing_object_id is not None:
                self._clear_loaded_bezier_object()
            return False

        selected_id = str(object_id)
        if self._active_handle_edit is not None:
            self._discard_active_handle_edit(restore_preview=True)
        self._editing_object_id = selected_id
        self._load_nodes_from_beziers(state[0])
        return True

    def _synchronize_selected_bezier_object(self) -> bool:
        if self._editing_object_id is None:
            return True
        model = self._model()
        selected_id = getattr(model, "selected_id", None) if model is not None else None
        obj = (
            model.objects.get(selected_id)
            if model is not None and selected_id is not None
            else None
        )
        if str(selected_id) != self._editing_object_id or obj is None:
            return self._load_selected_bezier_object()

        model_state = self._object_bezier_state(obj)
        if model_state is None:
            self._clear_loaded_bezier_object()
            return False

        # A global Undo/Redo or another command may replace the geometry while
        # the same object remains selected. During a gesture, compare against
        # the exact last preview installed in the model. Outside a gesture,
        # only the canonical controls need to match the loaded nodes; the
        # persisted polygon may legitimately use another sampling density.
        if self._active_handle_edit is not None:
            if not self._active_preview_matches_model():
                self._discard_active_handle_edit(restore_preview=False)
                self._load_nodes_from_beziers(model_state[0])
            return True

        loaded_beziers = self._nodes_beziers()
        if loaded_beziers != model_state[0]:
            self._load_nodes_from_beziers(model_state[0])
        return True

    def _load_nodes_from_beziers(self, beziers: BezierSegments) -> None:
        canonical = canonicalize_beziers(beziers)
        nodes = [BezierNode(canonical[0][0])]
        for segment in canonical:
            nodes.append(BezierNode(segment[3]))
        for index, segment in enumerate(canonical):
            nodes[index].handle_out = segment[1]
            nodes[index + 1].handle_in = segment[2]
        self._nodes = nodes
        self._selected_node = None
        self._selected_handle = None
        self._is_placing_handle = False
        self._closed = len(canonical) >= 2 and canonical[-1][3] == canonical[0][0]
        self._cursor_position = None

    def _nodes_to_beziers(self) -> BezierSegments:
        if len(self._nodes) < 2:
            raise ValueError("At least two Bézier nodes are required.")
        return canonicalize_beziers(
            [
                (
                    node.anchor,
                    node.handle_out,
                    self._nodes[index + 1].handle_in,
                    self._nodes[index + 1].anchor,
                )
                for index, node in enumerate(self._nodes[:-1])
            ]
        )

    def _beziers_for_commit(self, *, closed: bool = False) -> BezierSegments:
        """Build the canonical open or closed path represented by the nodes."""

        beziers = self._nodes_to_beziers()
        if not closed:
            return beziers
        if len(self._nodes) < 3:
            raise ValueError(
                "At least three Bézier nodes are required to close a path."
            )

        first_node = self._nodes[0]
        last_node = self._nodes[-1]
        segments = list(beziers)
        segments.append(
            (
                last_node.anchor,
                last_node.handle_out,
                first_node.handle_in,
                first_node.anchor,
            )
        )
        return canonicalize_beziers(segments)

    def _node_index(self, node: BezierNode) -> Optional[int]:
        for index, candidate in enumerate(self._nodes):
            if candidate is node:
                return index
        return None

    def _handle_mapping(
        self,
        node: BezierNode,
        handle_name: str,
    ) -> Optional[Tuple[int, int]]:
        node_index = self._node_index(node)
        if node_index is None:
            return None
        if handle_name == "out" and node_index < len(self._nodes) - 1:
            return node_index, 1
        if handle_name == "in" and node_index > 0:
            return node_index - 1, 2
        return None

    def on_mouse_press(self, event: QMouseEvent, position: Tuple[float, float]):
        self._is_placing_handle = False
        if event.button() == Qt.MouseButton.LeftButton:
            had_loaded_object = self._editing_object_id is not None
            if had_loaded_object and not self._synchronize_selected_bezier_object():
                self.canvas_view.update()
                return
            if not self._nodes:
                self._load_selected_bezier_object()
            click_point = (float(position[0]), float(position[1]))
            self._cursor_position = click_point
            if (
                self._editing_object_id is None
                and len(self._nodes) >= 3
                and self._is_near_first_anchor(click_point)
                and self._get_handle_at_point(click_point) is None
            ):
                self.commit_selection(closed=True)
                self.canvas_view.update()
                return
            handle_hit = self._get_handle_at_point(click_point)
            if handle_hit:
                self._selected_node, self._selected_handle = handle_hit
                if self._editing_object_id is not None:
                    mapping = self._handle_mapping(*handle_hit)
                    model = self._model()
                    obj = (
                        model.objects.get(self._editing_object_id)
                        if model is not None
                        else None
                    )
                    if mapping is not None and obj is not None:
                        beziers = canonicalize_beziers(obj.beziers)
                        self._active_handle_edit = _HandleEditState(
                            object_id=self._editing_object_id,
                            segment_index=mapping[0],
                            handle_index=mapping[1],
                            old_pos=beziers[mapping[0]][mapping[1]],
                            old_beziers=copy.deepcopy(beziers),
                            old_polygon=copy.deepcopy(obj.polygon),
                            preview_beziers=copy.deepcopy(beziers),
                            preview_polygon=copy.deepcopy(obj.polygon),
                        )
                self.canvas_view.update()
                return

            anchor_hit = self._get_anchor_at_point(click_point)
            if anchor_hit:
                self._selected_node = anchor_hit
                self._selected_handle = None
                self.canvas_view.update()
                return

            if self._editing_object_id is None:
                node_count = len(self._nodes)
                self._place_anchor(click_point)
                self._is_placing_handle = len(self._nodes) > node_count

        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

        self.canvas_view.update()

    def on_mouse_move(self, event: QMouseEvent, position: Tuple[float, float]):
        self._cursor_position = (float(position[0]), float(position[1]))
        if (
            self._editing_object_id is not None
            and not self._synchronize_selected_bezier_object()
        ):
            self.canvas_view.update()
            return
        if self._is_placing_handle:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self._update_placement_handles(position)
        elif self._selected_node and self._selected_handle:
            point = (float(position[0]), float(position[1]))
            if self._selected_handle == "in":
                self._selected_node.handle_in = point
            elif self._selected_handle == "out":
                self._selected_node.handle_out = point

            edit = self._active_handle_edit
            if edit is not None:
                model = self._model()
                object_id = edit.object_id
                obj = model.objects.get(object_id) if model is not None else None
                if obj is not None:
                    try:
                        requested_beziers = self._nodes_to_beziers()
                        beziers, polygon = model.prepare_bezier_geometry(
                            requested_beziers,
                            steps_per_segment=self._curve_segments,
                        )
                    except (OverflowError, TypeError, ValueError) as exc:
                        # Invalid continuous geometry remains visual-only. The
                        # accepted model stays at the last valid preview so a
                        # release can reject without installing corrupt state.
                        self._last_error = self._safe_p2d05_message(
                            exc,
                            operation="preview",
                        )
                    else:
                        self._last_error = ""
                        edit.preview_beziers = copy.deepcopy(beziers)
                        edit.preview_polygon = copy.deepcopy(polygon)
                        obj.beziers = copy.deepcopy(beziers)
                        obj.polygon = copy.deepcopy(polygon)
                        model._notify()
        self.canvas_view.update()

    def _restore_handle_preview(self) -> None:
        if self._active_handle_edit is None:
            return
        model = self._model()
        object_id = self._active_handle_edit.object_id
        obj = model.objects.get(object_id) if model is not None else None
        if obj is None:
            return
        obj.beziers = copy.deepcopy(self._active_handle_edit.old_beziers)
        obj.polygon = copy.deepcopy(self._active_handle_edit.old_polygon)
        model._notify()

    def _finish_handle_edit(self) -> None:
        edit = self._active_handle_edit
        if edit is None:
            return
        if not self._active_preview_matches_model():
            self._discard_active_handle_edit(restore_preview=False)
            self._load_selected_bezier_object()
            self._present_p2d05_error(
                RuntimeError("The selected Bezier object changed during this edit."),
                operation="edit",
                severity="warning",
                channel="status",
            )
            self.canvas_view.update()
            return

        model = self._model()
        object_id = edit.object_id
        segment_index = edit.segment_index
        handle_index = edit.handle_index
        mapping_node = (
            self._nodes[segment_index]
            if handle_index == 1
            else self._nodes[segment_index + 1]
        )
        new_pos = (
            mapping_node.handle_out if handle_index == 1 else mapping_node.handle_in
        )
        old_pos = edit.old_pos
        self._restore_handle_preview()
        self._active_handle_edit = None

        manager = getattr(model, "cmd", None) if model is not None else None
        if manager is None:
            self._present_p2d05_error(
                RuntimeError("Undo/Redo command history is unavailable."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            self._load_selected_bezier_object()
            return

        command = HandleMoveCommand(
            object_id,
            segment_index,
            handle_index,
            old_pos,
            new_pos,
            steps_per_segment=self._curve_segments,
        )
        try:
            result = manager.execute(command, model)
        except Exception as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
            self._load_selected_bezier_object()
            return

        self._last_command_result = result
        if result.status is CommandStatus.REJECTED:
            self._present_p2d05_error(
                RuntimeError(result.message or "The handle movement was rejected."),
                operation="edit",
                severity="warning",
                channel="status",
            )
        elif result.status is CommandStatus.FAILED:
            self._present_p2d05_error(
                RuntimeError(result.message or "The handle movement failed."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
        elif result.status is CommandStatus.NO_CHANGE:
            self._last_error = self._safe_p2d05_message(
                RuntimeError(
                    result.message or "The handle movement produced no change."
                ),
                operation="edit",
            )
        else:
            self._last_error = ""
        self._load_selected_bezier_object()

    def on_mouse_release(self, event: QMouseEvent, position: Tuple[float, float]):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_placing_handle:
                self._update_placement_handles(position)
            self._synchronize_selected_bezier_object()
            self._finish_handle_edit()
            self._selected_handle = None
            self._is_placing_handle = False
            self.canvas_view.update()

    def on_double_click(self, event: QMouseEvent, position: Tuple[float, float]):
        if self._editing_object_id is None and len(self._nodes) >= 2:
            self.commit_selection()
            self.canvas_view.update()

    def on_key_press(self, event) -> bool:
        if event.key() == Qt.Key.Key_Escape:
            return self._cancel_active_handle_edit() or self._cancel_creation_preview()
        return False

    def on_undo(self) -> bool:
        return self._cancel_active_handle_edit() or self._cancel_creation_preview()

    def on_redo(self) -> bool:
        return self._cancel_active_handle_edit() or self._cancel_creation_preview()

    def _cancel_creation_preview(self) -> bool:
        if self._editing_object_id is not None or not self._nodes:
            return False
        self.cancel()
        return True

    def _update_placement_handles(self, position: Tuple[float, float]) -> None:
        node = self._selected_node
        if node is None or self._editing_object_id is not None:
            return
        dx = float(position[0]) - node.anchor[0]
        dy = float(position[1]) - node.anchor[1]
        # Ignore click jitter in logical screen pixels, independently of zoom.
        if math.hypot(dx, dy) * self.get_canvas_zoom() < 3.0:
            node.handle_in = node.anchor
            node.handle_out = node.anchor
            return
        node.handle_out = (node.anchor[0] + dx, node.anchor[1] + dy)
        node.handle_in = (node.anchor[0] - dx, node.anchor[1] - dy)

    def _place_anchor(self, point: Tuple[float, float]):
        max_nodes = ((MAX_POLYGON_POINTS - 1) // self._curve_segments) + 1
        if len(self._nodes) >= max_nodes:
            self._present_p2d05_error(
                ValueError(
                    f"Bezier geometry cannot exceed {MAX_POLYGON_POINTS} "
                    "sampled points."
                ),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return
        new_node = BezierNode(point)
        # A click creates a corner. Only an explicit drag authors handles;
        # adding a neighbour must never rewrite controls already chosen.
        self._nodes.append(new_node)
        self._selected_node = new_node

    def _get_anchor_at_point(
        self, point: Tuple[float, float], tolerance_screen: float = 8.0
    ) -> Optional[BezierNode]:
        zoom = self.get_canvas_zoom()
        tolerance = tolerance_screen / zoom if zoom > 0 else tolerance_screen

        for node in self._nodes:
            dx = point[0] - node.anchor[0]
            dy = point[1] - node.anchor[1]
            if dx * dx + dy * dy <= tolerance * tolerance:
                return node
        return None

    def _is_near_first_anchor(self, point: Tuple[float, float]) -> bool:
        """Return whether an image-space click requests closing the path."""

        if not self._nodes or self._closed:
            return False
        first_anchor = self._nodes[0].anchor
        distance = math.hypot(point[0] - first_anchor[0], point[1] - first_anchor[1])
        zoom = self.get_canvas_zoom()
        tolerance = self._close_tolerance / zoom if zoom > 0 else self._close_tolerance
        return distance <= tolerance

    def _get_handle_at_point(
        self, point: Tuple[float, float], tolerance_screen: float = 6.0
    ) -> Optional[Tuple[BezierNode, str]]:
        zoom = self.get_canvas_zoom()
        tolerance = tolerance_screen / zoom if zoom > 0 else tolerance_screen

        for node in self._nodes:
            dx = point[0] - node.handle_in[0]
            dy = point[1] - node.handle_in[1]
            if (
                node.handle_in != node.anchor
                and dx * dx + dy * dy <= tolerance * tolerance
            ):
                return (node, "in")

            dx = point[0] - node.handle_out[0]
            dy = point[1] - node.handle_out[1]
            if (
                node.handle_out != node.anchor
                and dx * dx + dy * dy <= tolerance * tolerance
            ):
                return (node, "out")

        return None

    def _generate_curve_points(self) -> List[Tuple[float, float]]:
        if len(self._nodes) < 2:
            return []
        try:
            return sample_beziers(
                self._nodes_to_beziers(),
                steps_per_segment=self._curve_segments,
            )
        except (OverflowError, ValueError):
            return []

    @staticmethod
    def _beziers_from_sampled_points(
        points: List[Tuple[float, float]],
    ) -> BezierSegments:
        """Convert a legacy sampled polyline into continuous straight cubics.

        Existing scripted callers may provide only ``_generate_curve_points``
        without constructing PenTool node state. The compatibility conversion
        still creates one real Bézier object through ``CreateBezierObjectCommand``;
        it never falls back to direct polygon mutation.
        """

        cleaned: List[Tuple[float, float]] = []
        for index, point in enumerate(points):
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ValueError(
                    f"Sampled point {index} must contain exactly two coordinates."
                )
            x, y = point
            if (
                isinstance(x, bool)
                or isinstance(y, bool)
                or not isinstance(x, (int, float))
                or not isinstance(y, (int, float))
            ):
                raise ValueError(f"Sampled point {index} coordinates must be numeric.")
            try:
                current = (float(x), float(y))
            except (OverflowError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Sampled point {index} coordinates must be finite "
                    "and representable."
                ) from exc
            if not math.isfinite(current[0]) or not math.isfinite(current[1]):
                raise ValueError(f"Sampled point {index} coordinates must be finite.")
            if not cleaned or cleaned[-1] != current:
                cleaned.append(current)

        if len(cleaned) > 1 and cleaned[-1] == cleaned[0]:
            cleaned.pop()
        if len(cleaned) < 3:
            raise ValueError(
                "At least three distinct sampled points are required "
                "for Bézier creation."
            )

        segments: BezierSegments = []
        for start, end in zip(cleaned, cleaned[1:]):
            delta_x = (end[0] - start[0]) / 3.0
            delta_y = (end[1] - start[1]) / 3.0
            segments.append(
                (
                    start,
                    (start[0] + delta_x, start[1] + delta_y),
                    (start[0] + 2.0 * delta_x, start[1] + 2.0 * delta_y),
                    end,
                )
            )
        return canonicalize_beziers(segments)

    # Package 5C supersedes the former commit_polygon_command( path because
    # Bézier controls and the sampled polygon must be created atomically.
    def commit_selection(self, *, closed: bool = False):
        if self._editing_object_id is not None:
            return self._editing_object_id
        model = self._model()
        manager = getattr(model, "cmd", None) if model is not None else None
        if manager is None:
            self._present_p2d05_error(
                RuntimeError("Undo/Redo command history is unavailable."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None
        try:
            if closed and len(self._nodes) < 3:
                raise ValueError(
                    "At least three Bézier nodes are required to close a path."
                )
            beziers = (
                self._beziers_for_commit(closed=closed)
                if len(self._nodes) >= 2
                else self._beziers_from_sampled_points(self._generate_curve_points())
            )
        except (OverflowError, TypeError, ValueError) as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="warning",
                channel="status",
            )
            return None

        command = CreateBezierObjectCommand(
            beziers,
            steps_per_segment=self._curve_segments,
        )
        try:
            result = manager.execute(command, model)
        except Exception as exc:
            self._present_p2d05_error(
                exc,
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None

        self._last_command_result = result
        if result.status is CommandStatus.REJECTED:
            self._present_p2d05_error(
                RuntimeError(
                    result.message or "The Bezier object creation was rejected."
                ),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return None
        if result.status is CommandStatus.FAILED:
            self._present_p2d05_error(
                RuntimeError(result.message or "The Bezier object creation failed."),
                operation="edit",
                severity="critical",
                channel="modal",
            )
            return None
        if not result.changed or command.object_id is None:
            self._present_p2d05_error(
                RuntimeError(result.message or "No Bezier object was created."),
                operation="edit",
                severity="warning",
                channel="status",
            )
            return None

        self._editing_object_id = str(command.object_id)
        self._load_selected_bezier_object()
        self._last_error = ""
        return self._editing_object_id

    def draw_overlay(self, painter: QPainter):
        self._synchronize_selected_bezier_object()
        if not self._nodes:
            return

        transform = self.canvas_view.get_transform()
        zoom = self.get_canvas_zoom()

        painter.save()
        painter.setTransform(transform, combine=True)

        curve_points = self._generate_curve_points()
        if curve_points:
            pen = QPen(QColor(0, 0, 255), 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            if len(curve_points) > 1:
                painter.drawPolyline(
                    QPolygonF([QPointF(float(x), float(y)) for x, y in curve_points])
                )

        handle_radius = 5.0 / zoom if zoom > 0 else 5.0
        anchor_radius = 6.0 / zoom if zoom > 0 else 6.0
        close_ready = (
            self._editing_object_id is None
            and not self._closed
            and len(self._nodes) >= 3
            and self._cursor_position is not None
            and self._is_near_first_anchor(self._cursor_position)
        )
        if close_ready:
            close_pen = QPen(QColor(255, 210, 0), 2)
            close_pen.setCosmetic(True)
            close_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(close_pen)
            painter.drawLine(
                QPointF(*self._nodes[-1].anchor), QPointF(*self._nodes[0].anchor)
            )

        handle_pen = QPen(QColor(80, 210, 255), 2)
        handle_pen.setCosmetic(True)
        painter.setPen(handle_pen)
        for node in self._nodes:
            if node.handle_in != node.anchor:
                painter.drawLine(QPointF(*node.anchor), QPointF(*node.handle_in))
            if node.handle_out != node.anchor:
                painter.drawLine(QPointF(*node.anchor), QPointF(*node.handle_out))
            painter.setBrush(QColor(200, 200, 200))
            if node.handle_in != node.anchor:
                painter.drawEllipse(
                    QPointF(*node.handle_in), handle_radius, handle_radius
                )
            if node.handle_out != node.anchor:
                painter.drawEllipse(
                    QPointF(*node.handle_out), handle_radius, handle_radius
                )

        anchor_pen = QPen(QColor(255, 72, 72), 2)
        anchor_pen.setCosmetic(True)
        painter.setPen(anchor_pen)
        painter.setBrush(QColor(255, 72, 72))
        for index, node in enumerate(self._nodes):
            if index == 0 and self._editing_object_id is None and not self._closed:
                ring_pen = QPen(QColor(255, 210, 0), 2)
                ring_pen.setCosmetic(True)
                painter.setPen(ring_pen)
                painter.setBrush(QColor(255, 210, 0))
                ring_radius = anchor_radius + (3.0 / zoom if zoom > 0 else 3.0)
                painter.drawEllipse(QPointF(*node.anchor), ring_radius, ring_radius)
                painter.setPen(anchor_pen)
                painter.setBrush(QColor(255, 72, 72))
            painter.drawEllipse(QPointF(*node.anchor), anchor_radius, anchor_radius)
        painter.restore()

    def show_context_menu(self, event: QMouseEvent):
        menu = QMenu(self.canvas_view)

        act_cancel = menu.addAction(
            self.translations[self.current_lang]["cancel_selection"]
        )
        act_cancel.triggered.connect(self.cancel)
        menu.addSeparator()
        act_undo = menu.addAction(self.translations[self.current_lang]["undo"])
        act_undo.triggered.connect(self.undo_last_action)
        act_redo = menu.addAction(self.translations[self.current_lang]["redo"])
        act_redo.triggered.connect(self.redo_last_action)
        menu.exec(event.globalPos())

    def undo_last_action(self):
        if self.on_undo():
            return
        model = self._model()
        if model is not None and getattr(model, "cmd", None):
            model.cmd.undo(model)
            self._load_selected_bezier_object()

    def redo_last_action(self):
        if self.on_redo():
            return
        model = self._model()
        if model is not None and getattr(model, "cmd", None):
            model.cmd.redo(model)
            self._load_selected_bezier_object()

    def cancel(self):
        self._discard_active_handle_edit(restore_preview=True)
        self._nodes = []
        self._selected_node = None
        self._selected_handle = None
        self._is_placing_handle = False
        self._editing_object_id = None
        self._closed = False
        self._cursor_position = None
        self.canvas_view.update()

    def on_cancel(self):
        self.cancel()

    def update_language(self, lang):
        self.current_lang = lang
