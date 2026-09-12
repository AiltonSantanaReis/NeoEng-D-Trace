"""Interactive hybrid 2D/2.5D/3D authoring viewport.

This is intentionally additive: the existing QGraphicsView scene editor stays
untouched and the hybrid surface writes only its versioned sidecar.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, QPointF, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.core.hybrid_scene_model import (
    HybridSceneError,
    default_hybrid_scene,
    load_hybrid_scene,
    save_hybrid_scene,
)


def _color(value: str, fallback: str = "#5b9dcc") -> QColor:
    color = QColor(value)
    return color if color.isValid() else QColor(fallback)


def _rotate(
    point: tuple[float, float, float], rotation: list[float]
) -> tuple[float, float, float]:
    x, y, z = point
    rx, ry, rz = (math.radians(float(value)) for value in rotation)
    cy, sy = math.cos(rx), math.sin(rx)
    y, z = y * cy - z * sy, y * sy + z * cy
    cy, sy = math.cos(ry), math.sin(ry)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cz, sz = math.cos(rz), math.sin(rz)
    return x * cz - y * sz, x * sz + y * cz, z


class HybridSceneCanvas(QWidget):
    """Small deterministic painter-based viewport with real mouse gestures."""

    object_selected = Signal(str)
    object_changed = Signal(str)
    gesture_finished = Signal()
    status_message = Signal(str)

    def __init__(self, owner: "HybridSceneViewport") -> None:
        super().__init__(owner)
        self.owner = owner
        self.setObjectName("hybrid_scene_canvas")
        self.setMinimumSize(520, 360)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._mode = "3d"
        self._zoom = 42.0
        self._orbit_yaw = -28.0
        self._orbit_pitch = 18.0
        self._pan = QPointF(0.0, 0.0)
        self._last_mouse = QPoint()
        self._drag_start = QPoint()
        self._drag_id: str | None = None
        self._drag_origin: list[float] | None = None
        self._orbiting = False
        self._hit_regions: list[tuple[str, QRectF]] = []
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    @property
    def document(self) -> dict[str, Any]:
        return self.owner.document

    def set_mode(self, mode: str) -> None:
        self._mode = mode if mode in {"2d", "2.5d", "3d"} else "3d"
        self.update()

    def reset_view(self) -> None:
        self._zoom = 42.0
        self._orbit_yaw = -28.0
        self._orbit_pitch = 18.0
        self._pan = QPointF()
        self.update()

    def _world_to_screen(
        self, point: tuple[float, float, float]
    ) -> tuple[QPointF, float]:
        x, y, z = point
        if self._mode == "2d":
            scale = max(8.0, self._zoom)
            return (
                QPointF(
                    self.width() / 2 + x * scale + self._pan.x(),
                    self.height() / 2 - y * scale + self._pan.y(),
                ),
                z,
            )
        if self._mode == "2.5d":
            scale = max(8.0, self._zoom * 0.82)
            iso_x = (x - z) * 0.866
            iso_y = (x + z) * 0.45 - y
            return (
                QPointF(
                    self.width() / 2 + iso_x * scale + self._pan.x(),
                    self.height() / 2 - iso_y * scale + self._pan.y(),
                ),
                z,
            )
        yaw = math.radians(self._orbit_yaw)
        pitch = math.radians(self._orbit_pitch)
        x, z = x * math.cos(yaw) - z * math.sin(yaw), x * math.sin(yaw) + z * math.cos(
            yaw
        )
        y, z = y * math.cos(pitch) - z * math.sin(pitch), y * math.sin(
            pitch
        ) + z * math.cos(pitch)
        depth = z + 12.0
        if self.document["camera"].get("projection") == "orthographic":
            factor = self._zoom
        else:
            factor = self._zoom * max(0.25, 10.0 / max(1.0, depth))
        return (
            QPointF(
                self.width() / 2 + x * factor + self._pan.x(),
                self.height() / 2 - y * factor + self._pan.y(),
            ),
            depth,
        )

    def _vertices(self, record: dict[str, Any]) -> list[tuple[float, float, float]]:
        primitive = record.get("primitive", "cube")
        if primitive == "plane":
            local = [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)]
        else:
            local = [
                (-1, -1, -1),
                (1, -1, -1),
                (1, 1, -1),
                (-1, 1, -1),
                (-1, -1, 1),
                (1, -1, 1),
                (1, 1, 1),
                (-1, 1, 1),
            ]
        scale = record.get("scale", [1, 1, 1])
        rotation = record.get("rotation", [0, 0, 0])
        position = record.get("position", [0, 0, 0])
        return [
            tuple(
                float(position[index]) + rotated[index] * float(scale[index])
                for index in range(3)
            )
            for point in local
            for rotated in (_rotate(point, rotation),)
        ]

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#203344"), 1))
        if self._mode == "2d":
            for value in range(-12, 13):
                a, _ = self._world_to_screen((value, -12, 0))
                b, _ = self._world_to_screen((value, 12, 0))
                c, _ = self._world_to_screen((-12, value, 0))
                d, _ = self._world_to_screen((12, value, 0))
                painter.drawLine(a, b)
                painter.drawLine(c, d)
            return
        for value in range(-12, 13):
            a, _ = self._world_to_screen((value, 0, -12))
            b, _ = self._world_to_screen((value, 0, 12))
            c, _ = self._world_to_screen((-12, 0, value))
            d, _ = self._world_to_screen((12, 0, value))
            painter.drawLine(a, b)
            painter.drawLine(c, d)

    def _draw_mesh(self, painter: QPainter, record: dict[str, Any]) -> None:
        vertices = self._vertices(record)
        projected = [self._world_to_screen(point) for point in vertices]
        bounds = QRectF(projected[0][0].x(), projected[0][0].y(), 1, 1)
        for point, _depth in projected[1:]:
            bounds = bounds.united(QRectF(point.x(), point.y(), 1, 1))
        self._hit_regions.append((str(record["id"]), bounds.adjusted(-18, -18, 18, 18)))
        if record.get("primitive") == "plane":
            faces = [(0, 1, 2, 3)]
        else:
            faces = [
                (0, 1, 2, 3),
                (4, 5, 6, 7),
                (0, 1, 5, 4),
                (2, 3, 7, 6),
                (1, 2, 6, 5),
                (0, 3, 7, 4),
            ]
        face_data = []
        for face in faces:
            points = [projected[index][0] for index in face]
            depth = sum(projected[index][1] for index in face) / len(face)
            face_data.append((depth, points))
        material = next(
            (
                item
                for item in self.document.get("materials", [])
                if item.get("id") == record.get("material_id")
            ),
            {},
        )
        base = _color(str(material.get("color", "#4d8fb8")))
        if str(record["id"]) == self.owner.selected_id:
            painter.setPen(QPen(QColor("#f5c451"), 2))
        else:
            painter.setPen(QPen(QColor("#79b7d8"), 1))
        for index, (_depth, points) in enumerate(
            sorted(face_data, key=lambda item: item[0], reverse=True)
        ):
            shade = max(0.55, 0.92 - index * 0.06)
            face_color = QColor(
                min(255, int(base.red() * shade)),
                min(255, int(base.green() * shade)),
                min(255, int(base.blue() * shade)),
                210,
            )
            painter.setBrush(QBrush(face_color))
            painter.drawPolygon(QPolygonF(points))
        center, _ = self._world_to_screen(
            tuple(float(value) for value in record["position"])
        )
        painter.setPen(QPen(QColor("#e5f2f8"), 1))
        painter.drawText(center + QPointF(8, -8), str(record["name"]))

    def _draw_light(self, painter: QPainter, record: dict[str, Any]) -> None:
        center, _ = self._world_to_screen(
            tuple(float(value) for value in record["position"])
        )
        radius = 12 if str(record["id"]) == self.owner.selected_id else 9
        color = _color(str(record.get("color", "#ffd58a")))
        painter.setPen(QPen(QColor("#fff1a8"), 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(center, radius, radius)
        if record.get("light_type") == "directional":
            rotation = record.get("rotation", [0, 0, 0])
            direction = _rotate((0.0, 0.0, -2.0), rotation)
            end, _ = self._world_to_screen(
                tuple(
                    float(center_value) + direction[index]
                    for index, center_value in enumerate(record["position"])
                )
            )
            painter.drawLine(center, end)
        painter.setPen(QPen(QColor("#fff1a8"), 1))
        painter.drawText(center + QPointF(14, 4), str(record["name"]))
        self._hit_regions.append(
            (str(record["id"]), QRectF(center - QPointF(20, 20), QSizeF(40, 40)))
        )

    def _draw_camera(self, painter: QPainter, record: dict[str, Any]) -> None:
        center, _ = self._world_to_screen(
            tuple(float(value) for value in record["position"])
        )
        target, _ = self._world_to_screen(
            tuple(float(value) for value in record.get("target", [0, 0, 0]))
        )
        direction = target - center
        if direction.manhattanLength() < 1:
            direction = QPointF(0, 50)
        normal = QPointF(-direction.y(), direction.x())
        length = max(1.0, math.hypot(direction.x(), direction.y()))
        normal /= length
        tip = center + direction * 0.35
        corners = [tip + normal * 22, tip - normal * 22]
        painter.setPen(QPen(QColor("#c59cff"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(center, corners[0])
        painter.drawLine(center, corners[1])
        painter.drawLine(corners[0], corners[1])
        painter.drawEllipse(center, 7, 7)
        painter.drawText(center + QPointF(12, -10), str(record["name"]))
        self._hit_regions.append(
            (str(record["id"]), QRectF(center - QPointF(24, 24), QSizeF(48, 48)))
        )

    def _draw_gizmo(self, painter: QPainter, record: dict[str, Any]) -> None:
        center, _ = self._world_to_screen(
            tuple(float(value) for value in record["position"])
        )
        length = 44
        painter.setPen(QPen(QColor("#ee6565"), 2))
        painter.drawLine(center, center + QPointF(length, 0))
        painter.setPen(QPen(QColor("#70d68b"), 2))
        painter.drawLine(center, center + QPointF(0, -length))
        painter.setPen(QPen(QColor("#6eb9f5"), 2))
        painter.drawLine(center, center + QPointF(-length * 0.55, length * 0.45))
        painter.setPen(QPen(QColor("#f4f7fb"), 1))
        painter.drawText(center + QPointF(length + 4, 4), "X")
        painter.drawText(center + QPointF(4, -length - 4), "Y")
        painter.drawText(center + QPointF(-length * 0.55 - 14, length * 0.45 + 4), "Z")

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#101820"))
        self._draw_grid(painter)
        self._hit_regions = []
        objects = list(self.document.get("objects", []))
        for record in objects:
            if record.get("kind") == "mesh":
                self._draw_mesh(painter, record)
            elif record.get("kind") == "light":
                self._draw_light(painter, record)
            elif record.get("kind") == "camera":
                self._draw_camera(painter, record)
        selected = next(
            (item for item in objects if item.get("id") == self.owner.selected_id), None
        )
        if selected is not None and selected.get("kind") != "camera":
            self._draw_gizmo(painter, selected)
        painter.setPen(QPen(QColor("#a9c4d5"), 1))
        painter.drawText(18, 26, self.owner.mode_caption())
        painter.drawText(18, 48, self.owner.projection_caption())
        painter.drawText(self.width() - 210, 26, "MMB: orbitar  •  roda: zoom")
        painter.end()

    def mousePressEvent(self, event) -> None:
        self.setFocus()
        self._last_mouse = event.position().toPoint()
        if event.button() == Qt.MouseButton.MiddleButton:
            self._orbiting = True
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = event.position()
        selected = None
        distance = float("inf")
        for object_id, rect in self._hit_regions:
            if rect.contains(point):
                delta = rect.center() - point
                value = delta.x() * delta.x() + delta.y() * delta.y()
                if value < distance:
                    selected, distance = object_id, value
        if selected is None:
            self.status_message.emit("Clique em um objeto para selecioná-lo")
            return
        self.object_selected.emit(selected)
        record = next(
            (item for item in self.document["objects"] if item["id"] == selected), None
        )
        if record is not None:
            self._drag_id = selected
            self._drag_origin = list(record["position"])
            self._drag_start = event.position().toPoint()

    def mouseMoveEvent(self, event) -> None:
        current = event.position().toPoint()
        delta = current - self._last_mouse
        self._last_mouse = current
        if self._orbiting:
            self._orbit_yaw += delta.x() * 0.7
            self._orbit_pitch = max(
                -80.0, min(80.0, self._orbit_pitch + delta.y() * 0.5)
            )
            self.update()
            return
        if self._drag_id is None:
            return
        record = next(
            (item for item in self.document["objects"] if item["id"] == self._drag_id),
            None,
        )
        if record is None or self._drag_origin is None:
            return
        scale = max(8.0, self._zoom)
        if (
            self._mode == "3d"
            and self.document["camera"].get("projection") == "perspective"
        ):
            scale *= 0.75
        position = list(self._drag_origin)
        total_delta = current - self._drag_start
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            position[1] -= total_delta.y() / scale
        else:
            position[0] += total_delta.x() / scale
            position[2] += total_delta.y() / scale
        record["position"] = [round(value, 4) for value in position]
        if record.get("kind") == "camera":
            self.document["camera"]["position"] = list(record["position"])
        self.object_changed.emit(self._drag_id)
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._orbiting = False
        if event.button() == Qt.MouseButton.LeftButton and self._drag_id is not None:
            self.gesture_finished.emit()
            self._drag_id = None
            self._drag_origin = None

    def wheelEvent(self, event) -> None:
        self._zoom = max(
            12.0, min(160.0, self._zoom + (3.0 if event.angleDelta().y() > 0 else -3.0))
        )
        self.update()


class HybridSceneViewport(QWidget):
    """Authoring surface for a versioned hybrid scene sidecar."""

    status_message = Signal(str)
    scene_changed = Signal()

    def __init__(
        self, scene_path: Path, *, language: str = "en", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("hybrid_scene_viewport")
        self.scene_path = Path(scene_path)
        self.current_lang = language if language in {"en", "pt"} else "en"
        self.document = default_hybrid_scene()
        self.selected_id = str(self.document.get("selected_id") or "")
        self.dirty = False
        if self.scene_path.is_file():
            try:
                self.document = load_hybrid_scene(self.scene_path)
                self.selected_id = str(self.document.get("selected_id") or "")
            except HybridSceneError as exc:
                self.status_message.emit(str(exc))
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self._sync_projection_combo()
        self.update_language(self.current_lang)
        self._refresh_hierarchy()
        self._refresh_inspector()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        toolbar = QHBoxLayout()
        self.mode_label = QLabel()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("2D", "2d")
        self.mode_combo.addItem("2.5D", "2.5d")
        self.mode_combo.addItem("3D", "3d")
        self.mode_combo.setCurrentIndex(2)
        self.projection_label = QLabel()
        self.projection_combo = QComboBox()
        self.projection_combo.addItem("Perspectiva", "perspective")
        self.projection_combo.addItem("Ortográfica", "orthographic")
        self.projection_combo.setCurrentIndex(0)
        toolbar.addWidget(self.mode_label)
        toolbar.addWidget(self.mode_combo)
        toolbar.addSpacing(8)
        toolbar.addWidget(self.projection_label)
        toolbar.addWidget(self.projection_combo)
        for key in (
            "new",
            "save",
            "reload",
            "cube",
            "plane",
            "light",
            "camera",
            "frame",
        ):
            button = QPushButton()
            button.setObjectName(f"hybrid_{key}_button")
            self._buttons[key] = button
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        hierarchy_box = QGroupBox()
        hierarchy_layout = QVBoxLayout(hierarchy_box)
        self.hierarchy_label = QLabel()
        self.hierarchy = QListWidget()
        self.hierarchy.setObjectName("hybrid_scene_hierarchy")
        hierarchy_layout.addWidget(self.hierarchy_label)
        hierarchy_layout.addWidget(self.hierarchy)
        splitter.addWidget(hierarchy_box)

        self.canvas = HybridSceneCanvas(self)
        splitter.addWidget(self.canvas)

        inspector_box = QGroupBox()
        inspector_layout = QVBoxLayout(inspector_box)
        self.inspector_label = QLabel()
        inspector_layout.addWidget(self.inspector_label)
        form = QFormLayout()
        self._fields: dict[str, QDoubleSpinBox] = {}
        for key in (
            "position_x",
            "position_y",
            "position_z",
            "rotation_x",
            "rotation_y",
            "rotation_z",
            "scale_x",
            "scale_y",
            "scale_z",
            "intensity",
            "fov",
        ):
            field = QDoubleSpinBox()
            field.setRange(-1_000_000.0, 1_000_000.0)
            field.setDecimals(3)
            field.setSingleStep(0.1)
            field.setObjectName(f"hybrid_{key}_field")
            self._fields[key] = field
        self._fields["scale_x"].setRange(0.001, 1_000_000.0)
        self._fields["scale_y"].setRange(0.001, 1_000_000.0)
        self._fields["scale_z"].setRange(0.001, 1_000_000.0)
        labels = {
            "position_x": "Posição X",
            "position_y": "Posição Y",
            "position_z": "Posição Z",
            "rotation_x": "Rotação X",
            "rotation_y": "Rotação Y",
            "rotation_z": "Rotação Z",
            "scale_x": "Escala X",
            "scale_y": "Escala Y",
            "scale_z": "Escala Z",
            "intensity": "Intensidade",
            "fov": "FOV",
        }
        for key, field in self._fields.items():
            form.addRow(labels[key], field)
            field.valueChanged.connect(self._apply_inspector)
        self.target_label = QLabel()
        inspector_layout.addWidget(self.target_label)
        target_form = QFormLayout()
        self._target_fields: dict[str, QDoubleSpinBox] = {}
        for axis in "xyz":
            field = QDoubleSpinBox()
            field.setRange(-1_000_000.0, 1_000_000.0)
            field.setDecimals(3)
            field.valueChanged.connect(self._apply_target)
            self._target_fields[axis] = field
            target_form.addRow(axis.upper(), field)
        inspector_layout.addLayout(form)
        inspector_layout.addLayout(target_form)
        inspector_layout.addStretch(1)
        splitter.addWidget(inspector_box)
        splitter.setSizes([210, 720, 260])
        root.addWidget(splitter, 1)

        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        self.projection_combo.currentIndexChanged.connect(self._projection_changed)
        self.hierarchy.currentItemChanged.connect(self._hierarchy_changed)
        self.canvas.object_selected.connect(self.select_object)
        self.canvas.object_changed.connect(self._canvas_changed)
        self.canvas.gesture_finished.connect(self._gesture_finished)
        self._buttons["new"].clicked.connect(self.new_scene)
        self._buttons["save"].clicked.connect(self.save_scene)
        self._buttons["reload"].clicked.connect(self.reload_scene)
        self._buttons["cube"].clicked.connect(lambda: self.add_mesh("cube"))
        self._buttons["plane"].clicked.connect(lambda: self.add_mesh("plane"))
        self._buttons["light"].clicked.connect(self.add_light)
        self._buttons["camera"].clicked.connect(self.add_camera)
        self._buttons["frame"].clicked.connect(self.frame_all)

    def mode_caption(self) -> str:
        return (
            ("Modo 2D" if self.current_lang == "pt" else "2D mode")
            if self.canvas._mode == "2d"
            else (
                ("Modo 2.5D" if self.current_lang == "pt" else "2.5D mode")
                if self.canvas._mode == "2.5d"
                else ("Modo 3D" if self.current_lang == "pt" else "3D mode")
            )
        )

    def projection_caption(self) -> str:
        projection = self.document["camera"].get("projection")
        return (
            (
                "Projeção ortográfica"
                if self.current_lang == "pt"
                else "Orthographic projection"
            )
            if projection == "orthographic"
            else (
                "Projeção perspectiva"
                if self.current_lang == "pt"
                else "Perspective projection"
            )
        )

    def _mark_dirty(self, message: str | None = None) -> None:
        self.dirty = True
        self.scene_changed.emit()
        if message:
            self.status_message.emit(message)
        self.canvas.update()

    def _refresh_hierarchy(self) -> None:
        self.hierarchy.blockSignals(True)
        self.hierarchy.clear()
        for record in self.document.get("objects", []):
            prefix = {"mesh": "◆", "light": "☀", "camera": "◉"}.get(
                record.get("kind"), "•"
            )
            item = QListWidgetItem(
                f"{prefix}  {record.get('name', record.get('id', ''))}"
            )
            item.setData(Qt.ItemDataRole.UserRole, record.get("id"))
            self.hierarchy.addItem(item)
            if record.get("id") == self.selected_id:
                self.hierarchy.setCurrentItem(item)
        self.hierarchy.blockSignals(False)

    def _selected_record(self) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in self.document.get("objects", [])
                if item.get("id") == self.selected_id
            ),
            None,
        )

    def _refresh_inspector(self) -> None:
        record = self._selected_record()
        enabled = record is not None
        for field in self._fields.values():
            field.setEnabled(enabled)
        camera_selected = (
            enabled and record is not None and record.get("kind") == "camera"
        )
        for field in self._target_fields.values():
            field.setEnabled(camera_selected)
        if record is None:
            return
        position = record.get("position", [0, 0, 0])
        rotation = record.get("rotation", [0, 0, 0])
        scale = record.get("scale", [1, 1, 1])
        values = {
            "position_x": position[0],
            "position_y": position[1],
            "position_z": position[2],
            "rotation_x": rotation[0],
            "rotation_y": rotation[1],
            "rotation_z": rotation[2],
            "scale_x": scale[0],
            "scale_y": scale[1],
            "scale_z": scale[2],
            "intensity": record.get("intensity", 1.0),
            "fov": self.document["camera"].get("fov_degrees", 55.0),
        }
        for key, value in values.items():
            field = self._fields[key]
            field.blockSignals(True)
            field.setValue(float(value))
            field.blockSignals(False)
        target = record.get("target", self.document["camera"].get("target", [0, 0, 0]))
        for axis, value in zip("xyz", target):
            field = self._target_fields[axis]
            field.blockSignals(True)
            field.setValue(float(value))
            field.blockSignals(False)

    def _hierarchy_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is not None:
            self.select_object(str(current.data(Qt.ItemDataRole.UserRole)))

    def select_object(self, object_id: str) -> None:
        if not any(
            item.get("id") == object_id for item in self.document.get("objects", [])
        ):
            return
        self.selected_id = object_id
        self.document["selected_id"] = object_id
        self._refresh_hierarchy()
        self._refresh_inspector()
        self.canvas.update()

    def _canvas_changed(self, object_id: str) -> None:
        self.select_object(object_id)
        self._mark_dirty(
            "Objeto movido — alterações não salvas"
            if self.current_lang == "pt"
            else "Object moved — unsaved changes"
        )

    def _gesture_finished(self) -> None:
        self.scene_changed.emit()

    def _apply_inspector(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        record["position"] = [
            self._fields[key].value()
            for key in ("position_x", "position_y", "position_z")
        ]
        record["rotation"] = [
            self._fields[key].value()
            for key in ("rotation_x", "rotation_y", "rotation_z")
        ]
        record["scale"] = [
            self._fields[key].value() for key in ("scale_x", "scale_y", "scale_z")
        ]
        if record.get("kind") == "light":
            record["intensity"] = self._fields["intensity"].value()
        if record.get("kind") == "camera":
            self.document["camera"]["position"] = list(record["position"])
            self.document["camera"]["fov_degrees"] = self._fields["fov"].value()
        self._mark_dirty(
            "Transformação atualizada — alterações não salvas"
            if self.current_lang == "pt"
            else "Transform updated — unsaved changes"
        )

    def _apply_target(self) -> None:
        record = self._selected_record()
        if record is None or record.get("kind") != "camera":
            return
        target = [self._target_fields[axis].value() for axis in "xyz"]
        record["target"] = target
        self.document["camera"]["target"] = list(target)
        self._mark_dirty(
            "Direção da câmera atualizada — alterações não salvas"
            if self.current_lang == "pt"
            else "Camera direction updated — unsaved changes"
        )

    def _mode_changed(self, _index: int) -> None:
        self.canvas.set_mode(str(self.mode_combo.currentData()))
        self.status_message.emit(self.mode_caption())

    def _projection_changed(self, _index: int) -> None:
        self.document["camera"]["projection"] = str(self.projection_combo.currentData())
        self._mark_dirty(
            "Projeção atualizada — alterações não salvas"
            if self.current_lang == "pt"
            else "Projection updated — unsaved changes"
        )

    def _sync_projection_combo(self) -> None:
        self.projection_combo.blockSignals(True)
        index = self.projection_combo.findData(
            self.document["camera"].get("projection")
        )
        if index >= 0:
            self.projection_combo.setCurrentIndex(index)
        self.projection_combo.blockSignals(False)

    def new_scene(self) -> None:
        self.document = default_hybrid_scene()
        self.selected_id = "mesh-cube"
        self.dirty = True
        self._refresh_hierarchy()
        self._refresh_inspector()
        self.canvas.reset_view()
        self._sync_projection_combo()
        self._mark_dirty(
            "Nova cena 3D criada — salve para persistir"
            if self.current_lang == "pt"
            else "New 3D scene created — save to persist"
        )

    def _next_id(self, prefix: str) -> str:
        existing = {str(item.get("id")) for item in self.document.get("objects", [])}
        index = 1
        while f"{prefix}-{index}" in existing:
            index += 1
        return f"{prefix}-{index}"

    def add_mesh(self, primitive: str) -> None:
        object_id = self._next_id(f"mesh-{primitive}")
        name = (
            ("Cubo" if primitive == "cube" else "Plano")
            if self.current_lang == "pt"
            else ("Cube" if primitive == "cube" else "Plane")
        )
        self.document["objects"].append(
            {
                "id": object_id,
                "name": f"{name} {len(self.document['objects'])}",
                "kind": "mesh",
                "primitive": primitive,
                "position": [len(self.document["objects"]) * 0.75 - 1.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "material_id": "default-material",
            }
        )
        self.select_object(object_id)
        self._mark_dirty(
            "Mesh adicionado — alterações não salvas"
            if self.current_lang == "pt"
            else "Mesh added — unsaved changes"
        )

    def add_light(self) -> None:
        object_id = self._next_id("light-point")
        self.document["objects"].append(
            {
                "id": object_id,
                "name": "Luz pontual" if self.current_lang == "pt" else "Point light",
                "kind": "light",
                "light_type": "point",
                "position": [2.0, 3.0, 2.0],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "intensity": 2.0,
                "color": "#9ed8ff",
            }
        )
        self.select_object(object_id)
        self._mark_dirty(
            "Luz adicionada — alterações não salvas"
            if self.current_lang == "pt"
            else "Light added — unsaved changes"
        )

    def add_camera(self) -> None:
        object_id = self._next_id("camera")
        self.document["objects"].append(
            {
                "id": object_id,
                "name": "Câmera" if self.current_lang == "pt" else "Camera",
                "kind": "camera",
                "position": [0.0, 2.0, 6.0],
                "rotation": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "target": [0.0, 0.0, 0.0],
            }
        )
        self.select_object(object_id)
        self._mark_dirty(
            "Câmera adicionada — alterações não salvas"
            if self.current_lang == "pt"
            else "Camera added — unsaved changes"
        )

    def frame_all(self) -> None:
        self.canvas.reset_view()
        self.status_message.emit(
            "Viewport enquadrado" if self.current_lang == "pt" else "Viewport framed"
        )

    def save_scene(self) -> bool:
        try:
            self.document["selected_id"] = self.selected_id
            save_hybrid_scene(self.document, self.scene_path)
        except HybridSceneError as exc:
            self.status_message.emit(str(exc))
            return False
        self.dirty = False
        self.status_message.emit(
            (
                f"Cena híbrida salva: {self.scene_path.name}"
                if self.current_lang == "pt"
                else f"Hybrid scene saved: {self.scene_path.name}"
            )
        )
        return True

    def reload_scene(self) -> bool:
        if not self.scene_path.is_file():
            self.status_message.emit(
                "Nenhuma cena híbrida salva"
                if self.current_lang == "pt"
                else "No saved hybrid scene"
            )
            return False
        try:
            self.document = load_hybrid_scene(self.scene_path)
        except HybridSceneError as exc:
            self.status_message.emit(str(exc))
            return False
        self.selected_id = str(self.document.get("selected_id") or "")
        self.dirty = False
        self._sync_projection_combo()
        self._refresh_hierarchy()
        self._refresh_inspector()
        self.canvas.update()
        self.status_message.emit(
            "Cena híbrida reaberta"
            if self.current_lang == "pt"
            else "Hybrid scene reloaded"
        )
        return True

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        pt = self.current_lang == "pt"
        self.mode_label.setText("Modo:" if pt else "Mode:")
        self.projection_label.setText("Projeção:" if pt else "Projection:")
        self.hierarchy_label.setText("Hierarquia 3D" if pt else "3D hierarchy")
        self.inspector_label.setText(
            "Inspector de transformação" if pt else "Transform inspector"
        )
        self.target_label.setText("Alvo da câmera" if pt else "Camera target")
        labels = {
            "new": "Novo 3D" if pt else "New 3D",
            "save": "Salvar 3D" if pt else "Save 3D",
            "reload": "Reabrir" if pt else "Reload",
            "cube": "Adicionar cubo" if pt else "Add cube",
            "plane": "Adicionar plano" if pt else "Add plane",
            "light": "Adicionar luz" if pt else "Add light",
            "camera": "Adicionar câmera" if pt else "Add camera",
            "frame": "Enquadrar" if pt else "Frame all",
        }
        for key, label in labels.items():
            self._buttons[key].setText(label)
            self._buttons[key].setToolTip(label)
        self.canvas.update()
        self._refresh_hierarchy()


__all__ = ["HybridSceneCanvas", "HybridSceneViewport"]
