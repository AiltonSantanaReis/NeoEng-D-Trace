# src/tools/pen_tool.py
"""
Pen tool for drawing curves using Bézier splines.
"""

import math
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QMenu

from .base_tool import BaseTool


def bezier_point(
    t: float,
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
) -> Tuple[float, float]:
    u = 1 - t
    tt = t * t
    uu = u * u
    uuu = uu * u
    ttt = tt * t

    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]

    return (x, y)


def bezier_curve(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    segments: int = 20,
) -> List[Tuple[float, float]]:
    points = []
    for i in range(segments + 1):
        t = i / segments
        point = bezier_point(t, p0, p1, p2, p3)
        points.append(point)
    return points


class BezierNode:
    def __init__(self, anchor: Tuple[float, float]):
        self.anchor = anchor
        self.handle_in = anchor
        self.handle_out = anchor


class PenTool(BaseTool):
    """
    Pen tool for creating Bézier curves.
    """

    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self._nodes: List[BezierNode] = []
        self._selected_node: Optional[BezierNode] = None
        self._selected_handle: Optional[str] = None
        self._is_placing_handle = False
        self._curve_segments = 20

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

    def on_mouse_press(self, event: QMouseEvent, position: Tuple[float, float]):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = position
            click_point = (x, y)

            handle_hit = self._get_handle_at_point(click_point)
            if handle_hit:
                self._selected_node = handle_hit[0]
                self._selected_handle = handle_hit[1]
                return

            anchor_hit = self._get_anchor_at_point(click_point)
            if anchor_hit:
                self._selected_node = anchor_hit
                self._selected_handle = None
                return

            self._place_anchor(click_point)

        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event)

        self.canvas_view.update()

    def on_mouse_move(self, event: QMouseEvent, position: Tuple[float, float]):
        if self._selected_node and self._selected_handle:
            x, y = position
            if self._selected_handle == "in":
                self._selected_node.handle_in = (x, y)
            elif self._selected_handle == "out":
                self._selected_node.handle_out = (x, y)
        elif self._nodes and not self._is_placing_handle:
            pass

        self.canvas_view.update()

    def on_mouse_release(self, event: QMouseEvent, position: Tuple[float, float]):
        if event.button() == Qt.MouseButton.LeftButton:
            self._selected_handle = None
            self._is_placing_handle = False

    def on_double_click(self, event: QMouseEvent, position: Tuple[float, float]):
        if len(self._nodes) >= 2:
            self.commit_selection()
            self._nodes = []
            self._selected_node = None
            self._selected_handle = None
            self.canvas_view.update()

    def _place_anchor(self, point: Tuple[float, float]):
        new_node = BezierNode(point)

        if self._nodes:
            last_node = self._nodes[-1]
            if len(self._nodes) >= 2:
                prev_node = self._nodes[-2]
                dx = last_node.anchor[0] - prev_node.anchor[0]
                dy = last_node.anchor[1] - prev_node.anchor[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    handle_dist = min(dist * 0.3, 50)
                    new_node.handle_in = (
                        point[0] + dx / dist * handle_dist,
                        point[1] + dy / dist * handle_dist,
                    )

            last_node.handle_out = (
                last_node.anchor[0] - (new_node.handle_in[0] - point[0]),
                last_node.anchor[1] - (new_node.handle_in[1] - point[1]),
            )

        self._nodes.append(new_node)
        self._selected_node = new_node

    def _get_anchor_at_point(
        self, point: Tuple[float, float], tolerance_screen: float = 8.0
    ) -> Optional[BezierNode]:
        # Convert screen tolerance to image tolerance based on zoom
        zoom = self.get_canvas_zoom()
        tolerance = tolerance_screen / zoom if zoom > 0 else tolerance_screen

        for node in self._nodes:
            dx = point[0] - node.anchor[0]
            dy = point[1] - node.anchor[1]
            if dx * dx + dy * dy <= tolerance * tolerance:
                return node
        return None

    def _get_handle_at_point(
        self, point: Tuple[float, float], tolerance_screen: float = 6.0
    ) -> Optional[Tuple[BezierNode, str]]:
        zoom = self.get_canvas_zoom()
        tolerance = tolerance_screen / zoom if zoom > 0 else tolerance_screen

        for node in self._nodes:
            dx = point[0] - node.handle_in[0]
            dy = point[1] - node.handle_in[1]
            if dx * dx + dy * dy <= tolerance * tolerance:
                return (node, "in")

            dx = point[0] - node.handle_out[0]
            dy = point[1] - node.handle_out[1]
            if dx * dx + dy * dy <= tolerance * tolerance:
                return (node, "out")

        return None

    def _generate_curve_points(self) -> List[Tuple[float, float]]:
        if len(self._nodes) < 2:
            return []

        all_points = []

        for i in range(len(self._nodes) - 1):
            node1 = self._nodes[i]
            node2 = self._nodes[i + 1]

            curve_points = bezier_curve(
                node1.anchor,
                node1.handle_out,
                node2.handle_in,
                node2.anchor,
                self._curve_segments,
            )

            if i > 0:
                curve_points = curve_points[1:]

            all_points.extend(curve_points)

        return all_points

    def commit_selection(self):
        curve_points = self._generate_curve_points()
        if len(curve_points) < 3:
            return None

        polygon = [(int(round(x)), int(round(y))) for x, y in curve_points]

        cleaned_polygon = []
        for point in polygon:
            if not cleaned_polygon or point != cleaned_polygon[-1]:
                cleaned_polygon.append(point)

        if len(cleaned_polygon) < 3:
            return None

        try:
            if (
                hasattr(self.canvas_view.model, "cmd")
                and self.canvas_view.model.cmd is not None
            ):
                from src.core.commands import AddPolygonCommand

                cmd = AddPolygonCommand(cleaned_polygon)
                self.canvas_view.model.cmd.execute(cmd, self.canvas_view.model)
                return cmd.object_id
            else:
                oid = self.canvas_view.model.add_polygon(cleaned_polygon)
                return oid
        except Exception as e:
            print(f"Error adding Bézier curve: {e}")
            return None

    def draw_overlay(self, painter: QPainter):
        if not self._nodes:
            return

        # Setup transform to draw in Image Space
        transform = self.canvas_view.get_transform()
        zoom = self.get_canvas_zoom()

        painter.save()
        painter.setTransform(transform, combine=True)

        # 1. Draw the Curve (Blue)
        curve_points = self._generate_curve_points()
        if curve_points:
            pen = QPen(QColor(0, 0, 255), 2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            if len(curve_points) > 1:
                qpoints = [QPointF(float(p[0]), float(p[1])) for p in curve_points]
                painter.drawPolyline(QPolygonF(qpoints))

        # 2. Draw Handles (In/Out) lines
        handle_pen = QPen(QColor(128, 128, 128), 1)
        handle_pen.setCosmetic(True)
        painter.setPen(handle_pen)

        # Constant screen size for handles
        handle_radius = 3.0 / zoom if zoom > 0 else 3.0
        anchor_radius = 4.0 / zoom if zoom > 0 else 4.0

        for node in self._nodes:
            # Handles lines
            if node.handle_in != node.anchor:
                painter.drawLine(QPointF(*node.anchor), QPointF(*node.handle_in))
            if node.handle_out != node.anchor:
                painter.drawLine(QPointF(*node.anchor), QPointF(*node.handle_out))

            painter.setBrush(QColor(200, 200, 200))

            # Handle Dots (In/Out)
            if node.handle_in != node.anchor:
                pt = QPointF(*node.handle_in)
                painter.drawEllipse(pt, handle_radius, handle_radius)

            if node.handle_out != node.anchor:
                pt = QPointF(*node.handle_out)
                painter.drawEllipse(pt, handle_radius, handle_radius)

        # 3. Draw Anchors (Red)
        anchor_pen = QPen(QColor(255, 0, 0), 1)
        anchor_pen.setCosmetic(True)
        painter.setPen(anchor_pen)
        painter.setBrush(QColor(255, 0, 0))

        for node in self._nodes:
            pt = QPointF(*node.anchor)
            painter.drawEllipse(pt, anchor_radius, anchor_radius)

        painter.restore()

    def show_context_menu(self, event: QMouseEvent):
        menu = QMenu(self.canvas_view)
        menu.setStyleSheet("""
            QMenu { background-color: #2d2d30; color: #e6e6e6;
            border: 1px solid #3f3f46; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #2a6f97; }
            QMenu::separator { height: 1px; background: #3f3f46;
            margin: 5px 0; }
        """)

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
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.undo(self.canvas_view.model)

    def redo_last_action(self):
        if hasattr(self.canvas_view.model, "cmd") and self.canvas_view.model.cmd:
            self.canvas_view.model.cmd.redo(self.canvas_view.model)

    def cancel(self):
        self._nodes = []
        self._selected_node = None
        self._selected_handle = None
        self._is_placing_handle = False
        self.canvas_view.update()

    def update_language(self, lang):
        self.current_lang = lang
