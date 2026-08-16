"""Reference-inspired contextual 2D transform gizmo.

The supplied reference is a 3D editor gizmo. The NeoEng-D-Trace canvas is
2D, so this implementation exposes only operations with an unambiguous 2D
meaning: translation on X/Y or XY, rotation around Z, and uniform/axis scale.
Z remains explicit metadata and is not represented by a fake perspective drag.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF


class TransformGizmo:
    """Screen-space handles with stable size across canvas zoom levels."""

    NONE = 0
    AXIS_X = 1
    AXIS_Y = 2
    CENTER = 3  # compatibility alias retained for the central scale handle
    TRANSLATE_XY = 8
    ROTATE_Z = 4
    SCALE_UNIFORM = 3
    SCALE_X = 6
    SCALE_Y = 7

    def __init__(self):
        self.active_axis = self.NONE
        self.hover_axis = self.NONE
        self.screen_pos = QPointF(0, 0)
        self.arm_length = 76.0
        self.arrow_size = 14.0
        self.handle_thickness = 10.0
        self.rotation_radius = 51.0
        self.rotation_tolerance = 10.0
        self.plane_size = 18.0
        self.scale_handle_size = 11.0
        self.center_radius = 13.0
        self.color_x = QColor(255, 74, 74)
        self.color_y = QColor(86, 236, 124)
        self.color_z = QColor(72, 220, 255)
        self.color_anchor = QColor(62, 236, 255)
        self.color_center = QColor(205, 235, 242)
        self.color_hover = QColor(255, 231, 91)
        self.color_dimmed = QColor(100, 100, 100, 150)

    def set_screen_position(self, pos: QPointF):
        self.screen_pos = QPointF(pos)

    @staticmethod
    def _distance_to_segment(point: QPointF, start: QPointF, end: QPointF) -> float:
        vx = end.x() - start.x()
        vy = end.y() - start.y()
        wx = point.x() - start.x()
        wy = point.y() - start.y()
        length_sq = vx * vx + vy * vy
        if length_sq <= 1e-9:
            return math.hypot(wx, wy)
        t = max(0.0, min(1.0, (wx * vx + wy * vy) / length_sq))
        return math.hypot(
            point.x() - (start.x() + t * vx), point.y() - (start.y() + t * vy)
        )

    def _hit_scale_handle(self, dx: float, dy: float) -> int:
        half = self.scale_handle_size / 2.0 + 5.0
        if abs(dx - self.arm_length) <= half and abs(dy) <= half:
            return self.SCALE_X
        if abs(dx) <= half and abs(dy + self.arm_length) <= half:
            return self.SCALE_Y
        return self.NONE

    def hit_test(self, mouse_pos: QPointF) -> int:
        """Return the nearest semantic handle under a screen-space point."""
        dx = mouse_pos.x() - self.screen_pos.x()
        dy = mouse_pos.y() - self.screen_pos.y()
        distance = math.hypot(dx, dy)
        # The anchor ring translates freely; the inner square is uniform scale.
        if distance <= 5.0:
            return self.CENTER
        if distance <= self.center_radius:
            return self.SCALE_UNIFORM
        scale_hit = self._hit_scale_handle(dx, dy)
        if scale_hit != self.NONE:
            return scale_hit

        if abs(dx) <= self.plane_size and -self.plane_size * 1.5 <= dy <= -2:
            return self.TRANSLATE_XY

        x_end = QPointF(self.screen_pos.x() + self.arm_length, self.screen_pos.y())
        if (
            self._distance_to_segment(mouse_pos, self.screen_pos, x_end)
            <= self.handle_thickness
        ):
            return self.AXIS_X

        y_end = QPointF(self.screen_pos.x(), self.screen_pos.y() - self.arm_length)
        if (
            self._distance_to_segment(mouse_pos, self.screen_pos, y_end)
            <= self.handle_thickness
        ):
            return self.AXIS_Y

        # Keep the old downward Y hit area for existing integrations while
        # rendering the reference orientation upward.
        y_legacy_end = QPointF(
            self.screen_pos.x(), self.screen_pos.y() + self.arm_length
        )
        if (
            self._distance_to_segment(mouse_pos, self.screen_pos, y_legacy_end)
            <= self.handle_thickness
        ):
            return self.AXIS_Y

        if abs(distance - self.rotation_radius) <= self.rotation_tolerance:
            return self.ROTATE_Z
        return self.NONE

    def update_hover(self, mouse_pos: QPointF):
        previous = self.hover_axis
        self.hover_axis = self.hit_test(mouse_pos)
        return previous != self.hover_axis

    def _color(self, operation: int, base: QColor) -> QColor:
        color = QColor(
            self.color_hover
            if operation == self.hover_axis or operation == self.active_axis
            else base
        )
        if self.active_axis != self.NONE and operation != self.active_axis:
            color.setAlpha(70)
        return color

    @staticmethod
    def _draw_arrow(painter: QPainter, end: QPointF, direction: QPointF, size: float):
        perpendicular = QPointF(-direction.y(), direction.x())
        base = end - direction * size
        painter.drawPolygon(
            QPolygonF(
                [
                    end,
                    base + perpendicular * (size / 2.6),
                    base - perpendicular * (size / 2.6),
                ]
            )
        )

    def draw(self, painter: QPainter):
        """Draw the complete 2D contextual gizmo in screen coordinates."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.translate(self.screen_pos)

        ring_color = self._color(self.ROTATE_Z, self.color_z)
        painter.setPen(QPen(ring_color, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            -self.rotation_radius,
            -self.rotation_radius,
            self.rotation_radius * 2,
            self.rotation_radius * 2,
        )

        plane_color = self._color(self.TRANSLATE_XY, self.color_anchor)
        painter.setPen(QPen(plane_color, 1.5))
        painter.setBrush(QBrush(QColor(62, 236, 255, 45)))
        painter.drawRect(
            -self.plane_size, -self.plane_size, self.plane_size, self.plane_size
        )

        x_color = self._color(self.AXIS_X, self.color_x)
        painter.setPen(
            QPen(x_color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(QPointF(0, 0), QPointF(self.arm_length, 0))
        self._draw_arrow(
            painter,
            QPointF(self.arm_length + self.arrow_size, 0),
            QPointF(1, 0),
            self.arrow_size,
        )
        painter.setPen(QPen(self._color(self.SCALE_X, self.color_x), 2.0))
        painter.setBrush(QBrush(QColor(20, 20, 20, 220)))
        painter.drawRect(
            self.arm_length - self.scale_handle_size / 2,
            -self.scale_handle_size / 2,
            self.scale_handle_size,
            self.scale_handle_size,
        )

        y_color = self._color(self.AXIS_Y, self.color_y)
        painter.setPen(
            QPen(y_color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(QPointF(0, 0), QPointF(0, -self.arm_length))
        self._draw_arrow(
            painter,
            QPointF(0, -self.arm_length - self.arrow_size),
            QPointF(0, -1),
            self.arrow_size,
        )
        painter.setPen(QPen(self._color(self.SCALE_Y, self.color_y), 2.0))
        painter.setBrush(QBrush(QColor(20, 20, 20, 220)))
        painter.drawRect(
            -self.scale_handle_size / 2,
            -self.arm_length - self.scale_handle_size / 2,
            self.scale_handle_size,
            self.scale_handle_size,
        )

        anchor_color = self._color(self.SCALE_UNIFORM, self.color_anchor)
        painter.setPen(QPen(anchor_color, 2.0))
        painter.setBrush(QBrush(QColor(10, 48, 55, 230)))
        painter.drawEllipse(
            -self.center_radius,
            -self.center_radius,
            self.center_radius * 2,
            self.center_radius * 2,
        )
        painter.setPen(QPen(self.color_center, 1.2))
        painter.drawLine(-6, 0, 6, 0)
        painter.drawLine(0, -6, 0, 6)

        painter.setPen(self.color_anchor)
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        painter.drawText(self.arm_length + 19, 4, "X")
        painter.drawText(-4, -self.arm_length - self.arrow_size - 7, "Y")
        painter.drawText(self.rotation_radius + 7, -self.rotation_radius + 2, "Rz")
        painter.restore()
