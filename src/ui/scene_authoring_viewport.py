"""Professional 2D scene authoring viewport with real-time transforms."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QMimeData, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QTransform,
    QWheelEvent,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
)

from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scenario_preview import build_overlay_geometry
from src.core.scene_asset_library import (
    SceneAssetError,
    prepare_scene_asset,
    resolve_scene_asset,
    validate_scene_asset_source,
)
from src.core.scene_authoring_clipboard import SCENE_CLIPBOARD_MIME
from src.core.scene_authoring_groups import (
    locked_group_for_object,
    object_is_effectively_visible,
)
from src.core.scene_authoring_order import (
    layer_index_by_id,
    layer_visual_priority,
    ordered_scene_objects,
)
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_view_navigation import (
    anchored_navigation_center,
    clamp_navigation_zoom,
    fit_navigation_zoom,
    panned_navigation_center,
    wheel_navigation_zoom,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)


class SceneObjectGraphicsItem(QGraphicsObject):
    """Selectable, draggable visual representation of one authored object."""

    pressed = Signal(str, QPointF, object)
    moved = Signal(str, QPointF)
    released = Signal(str, QPointF)

    def __init__(
        self,
        object_id: str,
        polygon: QPolygonF,
        pixmap: QPixmap | None = None,
        parent=None,
        *,
        z_value: float = 10.0,
    ) -> None:
        super().__init__(parent)
        self.object_id = object_id
        self._polygon = polygon
        self._pixmap = pixmap
        self._selected = False
        self._hovered = False
        self._pressed = False
        self._enabled = True
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self._brush = QBrush(QColor("#2387b8"))
        self._pen = QPen(QColor("#65d7ff"), 2.0)
        self.setZValue(float(z_value))

    def _refresh_style(self) -> None:
        if not self._enabled:
            self._brush = QBrush(QColor("#27313a"))
            self._pen = QPen(QColor("#65727f"), 2.0)
        elif self._pressed:
            self._brush = QBrush(QColor("#4ec9e8"))
            self._pen = QPen(QColor("#ffffff"), 3.0)
        elif self._selected:
            self._brush = QBrush(QColor("#2aa8d8"))
            self._pen = QPen(QColor("#e8fbff"), 3.0)
        elif self._hovered:
            self._brush = QBrush(QColor("#2c9fc8"))
            self._pen = QPen(QColor("#b9f3ff"), 2.5)
        else:
            self._brush = QBrush(QColor("#2387b8"))
            self._pen = QPen(QColor("#65d7ff"), 2.0)
        self.update()

    def set_selected_style(self, selected: bool) -> None:
        self._selected = bool(selected)
        self._refresh_style()

    def set_interaction_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self._refresh_style()

    def boundingRect(self) -> QRectF:
        return self._polygon.boundingRect().adjusted(-3.0, -3.0, 3.0, 3.0)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        del option, widget
        if self._pixmap is not None:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawPixmap(
                self._polygon.boundingRect(),
                self._pixmap,
                QRectF(self._pixmap.rect()),
            )
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        else:
            painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawPolygon(self._polygon)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self._refresh_style()
        event.accept()

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self._refresh_style()
        event.accept()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._refresh_style()
            self.pressed.emit(self.object_id, event.scenePos(), event.modifiers())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.moved.emit(self.object_id, event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self._refresh_style()
            self.released.emit(self.object_id, event.scenePos())
            event.accept()
            return
        super().mouseReleaseEvent(event)


class SceneTransformGizmo(QGraphicsObject):
    """Interactive translate, rotate and uniform-scale gizmo.

    The scenario editor keeps its string-based signal contract, while the
    hit-test is fail-closed outside a real handle and hover state is exposed
    for consistent visual feedback.
    """

    gesture_started = Signal(str, QPointF)
    gesture_changed = Signal(str, QPointF)
    gesture_finished = Signal(str, QPointF)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setAcceptHoverEvents(True)
        self.setZValue(100.0)
        self._mode: str | None = None
        self._hover_mode: str | None = None

    def boundingRect(self) -> QRectF:
        return QRectF(-58.0, -58.0, 116.0, 116.0)

    def _mode_for(self, point: QPointF) -> str | None:
        if not self.boundingRect().contains(point):
            return None
        if 27.0 <= point.x() <= 48.0 and 27.0 <= point.y() <= 48.0:
            return "scale"
        radius = math.hypot(point.x(), point.y())
        if 38.0 <= radius <= 56.0:
            return "rotate"
        if point.x() >= 26.0 and abs(point.y()) <= 9.0:
            return "translate_x"
        if point.y() <= -26.0 and abs(point.x()) <= 9.0:
            return "translate_y"
        if radius <= 14.0:
            return "translate"
        return None

    @staticmethod
    def _color(mode: str, hover_mode: str | None, base: str) -> QColor:
        return QColor("#ffe36e" if mode == hover_mode else base)

    def paint(self, painter, option, widget=None) -> None:
        del option, widget
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)
        painter.setPen(
            QPen(self._color("translate_x", self._hover_mode, "#ff5d63"), 3.0)
        )
        painter.drawLine(QPointF(0.0, 0.0), QPointF(42.0, 0.0))
        painter.setPen(
            QPen(self._color("translate_y", self._hover_mode, "#59dc89"), 3.0)
        )
        painter.drawLine(QPointF(0.0, 0.0), QPointF(0.0, -42.0))
        painter.setPen(
            QPen(
                self._color("rotate", self._hover_mode, "#b8c6d6"),
                2.0,
                Qt.PenStyle.DashLine,
            )
        )
        painter.drawEllipse(QRectF(-48.0, -48.0, 96.0, 96.0))
        painter.setBrush(QBrush(self._color("translate", self._hover_mode, "#dceeff")))
        painter.setPen(QPen(QColor("#113044"), 1.5))
        painter.drawRect(QRectF(-7.0, -7.0, 14.0, 14.0))
        painter.setBrush(QBrush(self._color("scale", self._hover_mode, "#ffcf65")))
        painter.drawRect(QRectF(33.0, 33.0, 12.0, 12.0))
        painter.drawPolygon(
            QPolygonF([QPointF(42.0, 0.0), QPointF(32.0, -6.0), QPointF(32.0, 6.0)])
        )
        painter.setBrush(QBrush(QColor("#59dc89")))
        painter.drawPolygon(
            QPolygonF([QPointF(0.0, -42.0), QPointF(-6.0, -32.0), QPointF(6.0, -32.0)])
        )

    def hoverMoveEvent(self, event) -> None:
        mode = self._mode_for(event.pos())
        if mode != self._hover_mode:
            self._hover_mode = mode
            self.update()
        event.accept()

    def hoverLeaveEvent(self, event) -> None:
        self._hover_mode = None
        self.update()
        event.accept()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._mode = self._mode_for(event.pos())
        if self._mode is None:
            event.ignore()
            return
        self.gesture_started.emit(self._mode, event.scenePos())
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._mode is not None:
            self.gesture_changed.emit(self._mode, event.scenePos())
            event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._mode is not None:
            self.gesture_finished.emit(self._mode, event.scenePos())
            self._mode = None
            event.accept()


class SceneSocketGraphicsItem(QGraphicsObject):
    """Non-destructive visual marker for a declarative scene socket."""

    pressed = Signal(str)

    def __init__(
        self, socket_id: str, socket_type: str, color: str, parent=None
    ) -> None:
        super().__init__(parent)
        self.socket_id = socket_id
        self.socket_type = socket_type
        self._color = QColor(color)
        self.setZValue(80.0)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def boundingRect(self) -> QRectF:
        return QRectF(-9.0, -9.0, 18.0, 18.0)

    def paint(self, painter, option, widget=None) -> None:
        del option, widget
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)
        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(QColor("#f4fbff"), 2.0))
        painter.drawEllipse(QRectF(-7.0, -7.0, 14.0, 14.0))
        painter.setPen(QPen(QColor("#10202b"), 1.0))
        painter.drawText(
            QRectF(-6.0, -6.0, 12.0, 12.0),
            Qt.AlignmentFlag.AlignCenter,
            self.socket_type[:1].upper(),
        )

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed.emit(self.socket_id)
            event.accept()
            return
        super().mousePressEvent(event)


class SceneAuthoringViewport(QGraphicsView):
    """Canvas for selecting and transforming authored scene objects."""

    status_message = Signal(str)
    selection_changed = Signal()

    def __init__(
        self,
        session: SceneAuthoringSession,
        *,
        project_root: Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.project_root = project_root.resolve() if project_root else None
        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)
        self.setObjectName("professional_scene_viewport")
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor("#111820")))
        self._geometry: dict[str, tuple[tuple[float, float], ...]] = {}
        self._items: dict[str, SceneObjectGraphicsItem] = {}
        self._socket_items: dict[str, SceneSocketGraphicsItem] = {}
        self._preview_enabled = False
        self._authoring_enabled = True
        self._overlay_visible = False
        self._navigation_zoom = 1.0
        self._navigation_center: QPointF | None = None
        self._pan_origin: QPointF | None = None
        self._pan_center_start: QPointF | None = None
        self._gizmo: SceneTransformGizmo | None = None
        self._gesture_start: QPointF | None = None
        self._item_gesture_id: str | None = None
        self._gesture_layer_id: str | None = None
        self._gesture_mode: str | None = None
        self._gizmo_start: QPointF | None = None
        self._marquee_origin: QPointF | None = None
        self._marquee_current: QPointF | None = None
        self._marquee_selection_before: tuple[str, ...] | None = None
        self._marquee_primary_before: str | None = None
        self._marquee_selection_modifiers = Qt.KeyboardModifier.NoModifier
        self._asset_diagnostics: tuple[str, ...] = ()
        self._last_asset_diagnostics: tuple[str, ...] = ()
        self._asset_state_snapshot: tuple[tuple[str, str, str, str | None], ...] = ()
        self._layer_order_snapshot: tuple[str, ...] = ()
        self.sync()
        self.session.subscribe(self._on_session_change)

    def set_geometry(
        self,
        object_id: str,
        points: Iterable[tuple[float, float]],
    ) -> None:
        self._geometry[object_id] = tuple((float(x), float(y)) for x, y in points)
        self.sync()

    def set_preview_enabled(self, enabled: bool) -> None:
        """Enable camera/parallax projection without changing authored data."""
        if not isinstance(enabled, bool):
            raise TypeError("preview enabled must be boolean")
        if enabled != self._preview_enabled:
            self._navigation_center = None
        self._preview_enabled = enabled
        self.sync()

    def is_preview_enabled(self) -> bool:
        return self._preview_enabled

    def set_authoring_enabled(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("authoring enabled must be boolean")
        if not enabled and (
            self._gesture_start is not None or self._gizmo_start is not None
        ):
            self.session.cancel_gesture()
            self._gesture_start = None
            self._item_gesture_id = None
            self._gesture_layer_id = None
            self._gesture_mode = None
            self._gizmo_start = None
        self._authoring_enabled = enabled
        self._refresh_gizmo()
        self.viewport().update()

    def is_authoring_enabled(self) -> bool:
        return self._authoring_enabled

    def set_overlay_visible(self, visible: bool) -> None:
        if not isinstance(visible, bool):
            raise TypeError("overlay visible must be boolean")
        self._overlay_visible = visible
        self.viewport().update()

    def is_overlay_visible(self) -> bool:
        return self._overlay_visible

    @property
    def navigation_zoom(self) -> float:
        """Return transient presentation zoom; it is never persisted."""

        return self._navigation_zoom

    @property
    def navigation_center(self) -> QPointF:
        """Return the transient presentation center in current scene space."""

        if self._navigation_center is None:
            return self._natural_navigation_center()
        return QPointF(self._navigation_center)

    def _viewport_center(self) -> QPointF:
        rect = self.viewport().rect()
        return QPointF(rect.center())

    def _content_bounds(self, object_ids: Iterable[str] | None = None) -> QRectF | None:
        ids = tuple(object_ids) if object_ids is not None else tuple(self._items)
        bounds: QRectF | None = None
        for object_id in ids:
            visual = self._items.get(object_id)
            if visual is None or not visual.isVisible():
                continue
            candidate = visual.sceneBoundingRect()
            bounds = candidate if bounds is None else bounds.united(candidate)
        return bounds

    def _natural_navigation_center(self) -> QPointF:
        if self._preview_enabled:
            return self._viewport_center()
        bounds = self._content_bounds()
        return bounds.center() if bounds is not None else QPointF(0.0, 0.0)

    def _refresh_navigation_scene_rect(self) -> None:
        width = max(1.0, float(self.viewport().width()))
        height = max(1.0, float(self.viewport().height()))
        bounds = self._content_bounds()
        if bounds is None:
            bounds = (
                QRectF(0.0, 0.0, width, height)
                if self._preview_enabled
                else QRectF(-width / 2.0, -height / 2.0, width, height)
            )
        if self._preview_enabled:
            bounds = bounds.united(QRectF(0.0, 0.0, width, height))
        padding_x = max(512.0, width * 4.0 / self._navigation_zoom)
        padding_y = max(512.0, height * 4.0 / self._navigation_zoom)
        self.graphics_scene.setSceneRect(
            bounds.adjusted(-padding_x, -padding_y, padding_x, padding_y)
        )

    def _apply_navigation_transform(self) -> None:
        self._navigation_zoom = clamp_navigation_zoom(self._navigation_zoom)
        if self._navigation_center is None:
            self._navigation_center = self._natural_navigation_center()
        self._refresh_navigation_scene_rect()
        self.setTransform(
            QTransform.fromScale(self._navigation_zoom, self._navigation_zoom)
        )
        self.centerOn(self._navigation_center)
        self._navigation_center = self.mapToScene(self.viewport().rect().center())
        self.viewport().update()

    def _set_navigation_state(self, zoom: float, center: QPointF) -> None:
        if not math.isfinite(center.x()) or not math.isfinite(center.y()):
            raise ValueError("navigation center must be finite")
        self._navigation_zoom = clamp_navigation_zoom(zoom)
        self._navigation_center = QPointF(center)
        self._apply_navigation_transform()

    def _zoom_at(self, view_pos: QPointF, angle_delta_y: float) -> bool:
        new_zoom = wheel_navigation_zoom(self._navigation_zoom, angle_delta_y)
        if new_zoom == self._navigation_zoom:
            return False
        anchor = self.mapToScene(view_pos.toPoint())
        center = anchored_navigation_center(
            (anchor.x(), anchor.y()),
            (view_pos.x(), view_pos.y()),
            (self._viewport_center().x(), self._viewport_center().y()),
            new_zoom,
        )
        requested_center = QPointF(*center)
        self._set_navigation_state(new_zoom, requested_center)
        for _ in range(3):
            actual_anchor = self.mapToScene(view_pos.toPoint())
            correction = anchor - actual_anchor
            if max(abs(correction.x()), abs(correction.y())) <= 0.25:
                break
            requested_center += correction
            self._set_navigation_state(new_zoom, requested_center)
        self.status_message.emit(f"Viewport zoom: {new_zoom:.2f}x")
        return True

    def _fit_object_ids(self, object_ids: Iterable[str], label: str) -> bool:
        ids = tuple(object_id for object_id in object_ids if object_id in self._items)
        bounds = self._content_bounds(ids)
        if bounds is None:
            self.status_message.emit(f"{label}: no visible objects to frame")
            return False
        width = max(1.0, bounds.width())
        height = max(1.0, bounds.height())
        zoom = fit_navigation_zoom(
            (float(self.viewport().width()), float(self.viewport().height())),
            (width, height),
        )
        self._set_navigation_state(zoom, bounds.center())
        self.status_message.emit(f"{label}: framed {len(ids)} object(s) at {zoom:.2f}x")
        return True

    def fit_selection(self) -> bool:
        """Frame visible selected objects without changing authoring state."""

        return self._fit_object_ids(self.session.selection.ids, "Fit Selection")

    def fit_all(self) -> bool:
        """Frame all visible rendered objects, excluding sockets and overlays."""

        return self._fit_object_ids(self._items.keys(), "Fit All")

    def _paint_navigation_state(self) -> None:
        if not self.hasFocus() and self._pan_origin is None:
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        color = QColor("#ffe36e") if self._pan_origin is not None else QColor("#65d7ff")
        painter.setPen(QPen(color, 2.0))
        rect = self.viewport().rect().adjusted(1, 1, -2, -2)
        painter.drawRect(QRectF(rect))
        painter.end()

    def _camera(self) -> OrthographicCamera:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            return OrthographicCamera(
                (
                    max(1.0, float(self.viewport().width())),
                    max(1.0, float(self.viewport().height())),
                )
            )
        return OrthographicCamera(
            (
                max(1.0, float(self.viewport().width())),
                max(1.0, float(self.viewport().height())),
            ),
            (float(document.camera.position.x), float(document.camera.position.y)),
            float(document.camera.zoom),
        )

    def _layer_parallax(self, layer_id: str) -> ParallaxLayer:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            return ParallaxLayer()
        record = next(
            (item for item in document.parallax_layers if item.layer_id == layer_id),
            None,
        )
        if record is None:
            return ParallaxLayer()
        return ParallaxLayer(
            depth=float(record.depth),
            translation_strength=float(record.translation_strength),
            zoom_strength=float(record.zoom_strength),
        )

    def _project_position(self, position: Point3Record, layer_id: str) -> QPointF:
        if not self._preview_enabled:
            return QPointF(float(position.x), float(position.y))
        x, y = self._camera().project(
            (float(position.x), float(position.y)), self._layer_parallax(layer_id)
        )
        return QPointF(x, y)

    def _world_position(self, scene_pos: QPointF, layer_id: str) -> QPointF:
        if not self._preview_enabled:
            return scene_pos
        x, y = self._camera().unproject(
            (scene_pos.x(), scene_pos.y()), self._layer_parallax(layer_id)
        )
        return QPointF(x, y)

    def _default_geometry(self, object_id: str) -> tuple[tuple[float, float], ...]:
        del object_id
        return ((-32.0, -32.0), (32.0, -32.0), (32.0, 32.0), (-32.0, 32.0))

    def _polygon_for(self, object_id: str) -> QPolygonF:
        return QPolygonF(
            [
                QPointF(x, y)
                for x, y in self._geometry.get(
                    object_id, self._default_geometry(object_id)
                )
            ]
        )

    def _overlay_z(self, offset: float) -> float:
        return max(
            (visual.zValue() for visual in self._items.values()),
            default=0.0,
        ) + float(offset)

    def sync(self) -> None:
        self.graphics_scene.clear()
        self._items.clear()
        self._socket_items.clear()
        self._gizmo = None
        diagnostics: list[str] = []
        assets_by_id = {asset.id: asset for asset in self.session.document.assets}
        pixmap_cache: dict[str, QPixmap | None] = {}
        ordered_objects = ordered_scene_objects(self.session.document)
        layer_order = layer_index_by_id(self.session.document)
        objects_in_layer: dict[str, int] = {}
        object_count = len(ordered_objects)
        for item in ordered_objects:
            if not object_is_effectively_visible(
                self.session.document,
                item.id,
                isolated_group_id=self.session.isolated_group_id,
            ):
                continue
            pixmap: QPixmap | None = None
            asset = assets_by_id.get(item.asset_id)
            if asset is None:
                diagnostics.append(f"{item.id}: asset record is missing")
            elif asset.id not in pixmap_cache:
                asset_path, issue = resolve_scene_asset(asset, self.project_root)
                if issue is not None:
                    diagnostics.append(f"{item.id}: {issue}")
                else:
                    assert asset_path is not None
                    try:
                        pixmap_cache[asset.id] = self._load_asset_pixmap(asset_path)
                    except (OSError, ValueError) as exc:
                        diagnostics.append(f"{item.id}: {exc}")
                        pixmap_cache[asset.id] = None
            pixmap = pixmap_cache.get(asset.id) if asset is not None else None
            visual = SceneObjectGraphicsItem(
                item.id,
                self._polygon_for(item.id),
                pixmap,
                z_value=layer_visual_priority(
                    layer_order[item.layer_id],
                    objects_in_layer.get(item.layer_id, 0),
                    object_count,
                ),
            )
            objects_in_layer[item.layer_id] = objects_in_layer.get(item.layer_id, 0) + 1
            visual.pressed.connect(self._object_pressed)
            visual.moved.connect(self._object_moved)
            visual.released.connect(self._object_released)
            self.graphics_scene.addItem(visual)
            self._items[item.id] = visual
        document = self.session.document
        if isinstance(document, SceneAuthoringDocumentV2):
            visible_layers = {item.id for item in document.layers if item.visible}
            for socket in document.sockets:
                if socket.layer_id not in visible_layers:
                    continue
                color = (
                    socket.color
                    if socket.type == "light"
                    else ("#c78cff" if socket.type == "vfx" else "#ffcf65")
                )
                marker = SceneSocketGraphicsItem(socket.id, socket.type, color)
                marker.setZValue(self._overlay_z(100.0))
                marker.pressed.connect(
                    lambda socket_id: self.status_message.emit(
                        f"Socket selected: {socket_id}"
                    )
                )
                self.graphics_scene.addItem(marker)
                self._socket_items[socket.id] = marker
        self._refresh_transforms()
        self._refresh_selection()
        self._refresh_gizmo()
        self._apply_navigation_transform()
        self._asset_state_snapshot = tuple(
            (asset.id, asset.path, asset.sha256, asset.source_path)
            for asset in self.session.document.assets
        )
        self._layer_order_snapshot = tuple(
            layer.id for layer in self.session.document.layers
        )
        self._asset_diagnostics = tuple(dict.fromkeys(diagnostics))
        if self._asset_diagnostics != self._last_asset_diagnostics:
            self._last_asset_diagnostics = self._asset_diagnostics
            if self._asset_diagnostics:
                self.status_message.emit(
                    "Scene asset diagnostics: " + " | ".join(self._asset_diagnostics)
                )

    def _refresh_transforms(self) -> None:
        by_id = {item.id: item for item in self.session.document.objects}
        for object_id, visual in self._items.items():
            item = by_id[object_id]
            record = item.transform
            parallax = self._layer_parallax(item.layer_id)
            zoom = (
                self._camera().effective_zoom(parallax)
                if self._preview_enabled
                else 1.0
            )
            position = self._project_position(record.position, item.layer_id)
            visual.setPos(position)
            visual.setRotation(record.rotation.z)
            visual.setTransform(
                QTransform.fromScale(
                    record.scale.x * zoom * (-1.0 if record.flip_x else 1.0),
                    record.scale.y * zoom * (-1.0 if record.flip_y else 1.0),
                )
            )
            visual.set_selected_style(object_id in self.session.selection.ids)
        document = self.session.document
        if isinstance(document, SceneAuthoringDocumentV2):
            by_socket = {item.id: item for item in document.sockets}
            for socket_id, marker in self._socket_items.items():
                socket = by_socket[socket_id]
                marker.setPos(self._project_position(socket.position, socket.layer_id))

    def _refresh_selection(self) -> None:
        for object_id, visual in self._items.items():
            visual.set_selected_style(object_id in self.session.selection.ids)

    def _refresh_gizmo(self) -> None:
        if self._gizmo is not None:
            self.graphics_scene.removeItem(self._gizmo)
            self._gizmo = None
        primary = self.session.selection.primary
        if primary is None:
            return
        record = next(
            (item for item in self.session.document.objects if item.id == primary),
            None,
        )
        if record is None or primary not in self._items:
            return
        self._gizmo = SceneTransformGizmo()
        self._gizmo.setZValue(self._overlay_z(200.0))
        self._gizmo.setPos(
            self._project_position(record.transform.position, record.layer_id)
        )
        self._gizmo.gesture_started.connect(self._gizmo_started)
        self._gizmo.gesture_changed.connect(self._gizmo_changed)
        self._gizmo.gesture_finished.connect(self._gizmo_finished)
        self.graphics_scene.addItem(self._gizmo)

    def _refresh_after_model_change(self) -> None:
        self._refresh_transforms()
        self._refresh_gizmo()
        self.viewport().update()

    def _on_session_change(self) -> None:
        visible_ids = {
            item.id
            for item in self.session.document.objects
            if object_is_effectively_visible(
                self.session.document,
                item.id,
                isolated_group_id=self.session.isolated_group_id,
            )
        }
        visible_socket_ids = set()
        if isinstance(self.session.document, SceneAuthoringDocumentV2):
            visible_socket_ids = {
                socket.id
                for socket in self.session.document.sockets
                if any(
                    layer.id == socket.layer_id and layer.visible
                    for layer in self.session.document.layers
                )
            }
        current_asset_snapshot = tuple(
            (asset.id, asset.path, asset.sha256, asset.source_path)
            for asset in self.session.document.assets
        )
        if (
            visible_ids != set(self._items)
            or visible_socket_ids != set(self._socket_items)
            or current_asset_snapshot != self._asset_state_snapshot
            or tuple(layer.id for layer in self.session.document.layers)
            != self._layer_order_snapshot
        ):
            self.sync()
        else:
            self._refresh_after_model_change()

    def _set_selection(
        self, object_ids: Iterable[str], primary: str | None = None
    ) -> None:
        """Refresh selection affordances after a canonical selection update."""
        self.session.set_selection(object_ids, primary)
        self.selection_changed.emit()
        self._refresh_selection()
        self._refresh_gizmo()

    def _visible_object_ids(self) -> tuple[str, ...]:
        """Return selectable objects in the deterministic visual order."""
        visible_ids = set(self._items)
        return tuple(
            item.id
            for item in ordered_scene_objects(self.session.document)
            if item.id in visible_ids
        )

    def _select_all_visible(self) -> tuple[str, ...]:
        object_ids = self._visible_object_ids()
        self._set_selection(object_ids, object_ids[-1] if object_ids else None)
        return object_ids

    def _apply_marquee_selection(
        self,
        origin: QPointF,
        current: QPointF,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ) -> tuple[str, ...]:
        """Select visible objects using containment or intersection semantics."""
        selection_rect = QRectF(origin, current).normalized()
        left_to_right = current.x() >= origin.x()
        candidates: list[str] = []
        for object_id in self._visible_object_ids():
            bounds = self._items[object_id].sceneBoundingRect()
            if (
                selection_rect.contains(bounds)
                if left_to_right
                else selection_rect.intersects(bounds)
            ):
                candidates.append(object_id)

        visible_ids = set(self._visible_object_ids())
        existing = [
            item
            for item in (
                self._marquee_selection_before
                if self._marquee_selection_before is not None
                else self.session.selection.ids
            )
            if item in visible_ids
        ]
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            selected = existing
            selected.extend(item for item in candidates if item not in selected)
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            selected = [item for item in existing if item not in candidates]
            selected.extend(item for item in candidates if item not in existing)
        else:
            selected = candidates

        primary = candidates[-1] if candidates else None
        if primary is None and selected:
            primary = self._marquee_primary_before
            if primary not in selected:
                primary = selected[-1]
        self._set_selection(selected, primary)
        return tuple(selected)

    def _clear_marquee(self) -> None:
        self._marquee_origin = None
        self._marquee_current = None
        self._marquee_selection_before = None
        self._marquee_primary_before = None
        self._marquee_selection_modifiers = Qt.KeyboardModifier.NoModifier
        self.viewport().update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self._pan_origin = QPointF(event.position())
            self._pan_center_start = QPointF(self.navigation_center)
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            self.viewport().update()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self.itemAt(event.position().toPoint()) is not None:
                super().mousePressEvent(event)
                return
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            scene_pos = self.mapToScene(event.position().toPoint())
            self._marquee_origin = scene_pos
            self._marquee_current = scene_pos
            self._marquee_selection_before = tuple(self.session.selection.ids)
            self._marquee_primary_before = self.session.selection.primary
            self._marquee_selection_modifiers = event.modifiers()
            if not (
                event.modifiers() & Qt.KeyboardModifier.ControlModifier
                or event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            ):
                self._set_selection((), None)
            event.accept()
            self.viewport().update()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pan_origin is not None and self._pan_center_start is not None:
            current = QPointF(event.position())
            center = panned_navigation_center(
                (self._pan_center_start.x(), self._pan_center_start.y()),
                (self._pan_origin.x(), self._pan_origin.y()),
                (current.x(), current.y()),
                self._navigation_zoom,
            )
            self._set_navigation_state(self._navigation_zoom, QPointF(*center))
            event.accept()
            return
        if self._marquee_origin is not None:
            self._marquee_current = self.mapToScene(event.position().toPoint())
            event.accept()
            self.viewport().update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.MiddleButton
            and self._pan_origin is not None
        ):
            self._pan_origin = None
            self._pan_center_start = None
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            self.viewport().update()
            event.accept()
            return
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._marquee_origin is not None
            and self._marquee_current is not None
        ):
            self._apply_marquee_selection(
                self._marquee_origin,
                self._marquee_current,
                self._marquee_selection_modifiers,
            )
            self._clear_marquee()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _edit_status_error(self, exc: Exception) -> None:
        self.status_message.emit(str(exc))

    def _block_if_preview(self) -> bool:
        if self._authoring_enabled:
            return False
        self.status_message.emit("Preview mode is read-only")
        return True

    def _handle_nudge_key(self, key: int, modifiers: Qt.KeyboardModifier) -> bool:
        if self._block_if_preview():
            return True
        step = 10.0 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1.0
        deltas: dict[int, tuple[float, float]] = {
            int(Qt.Key.Key_Left): (-step, 0.0),
            int(Qt.Key.Key_Right): (step, 0.0),
            int(Qt.Key.Key_Up): (0.0, -step),
            int(Qt.Key.Key_Down): (0.0, step),
        }
        dx, dy = deltas[key]
        try:
            changed = self.session.nudge_selected(Point3Record(x=dx, y=dy, z=0.0))
        except (KeyError, PermissionError, ValueError) as exc:
            self._edit_status_error(exc)
        else:
            self.status_message.emit(
                "Moved selected object(s)" if changed else "No movement after snap"
            )
        return True

    def _handle_duplicate_key(self) -> bool:
        if self._block_if_preview():
            return True
        try:
            created = self.session.duplicate_selected()
        except (KeyError, PermissionError, ValueError) as exc:
            self._edit_status_error(exc)
        else:
            self.status_message.emit(
                f"Duplicated {len(created)} object(s)"
                if created
                else "No objects selected"
            )
        return True

    def _handle_delete_key(self) -> bool:
        if self._block_if_preview():
            return True
        try:
            count = len(self.session.selection.ids)
            changed = self.session.delete_selected()
        except (KeyError, PermissionError, ValueError) as exc:
            self._edit_status_error(exc)
        else:
            self.status_message.emit(
                f"Deleted {count} object(s)" if changed else "No objects selected"
            )
        return True

    def _handle_copy_key(self) -> bool:
        try:
            payload = self.session.copy_selected_payload()
        except (KeyError, PermissionError, ValueError) as exc:
            self._edit_status_error(exc)
            return True
        if payload is None:
            self.status_message.emit("No objects selected")
            return True
        mime = QMimeData()
        mime.setData(SCENE_CLIPBOARD_MIME, payload)
        clipboard = QApplication.clipboard()
        if clipboard is None:
            self.status_message.emit("Scene clipboard is unavailable")
            return True
        clipboard.setMimeData(mime)
        self.status_message.emit(f"Copied {len(self.session.selection.ids)} object(s)")
        return True

    def _handle_paste_key(self) -> bool:
        if self._block_if_preview():
            return True
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData() if clipboard is not None else None
        if mime is None or not mime.hasFormat(SCENE_CLIPBOARD_MIME):
            self.status_message.emit("No compatible scene clipboard payload")
            return True
        try:
            created = self.session.paste_payload(
                bytes(mime.data(SCENE_CLIPBOARD_MIME).data())
            )
        except (KeyError, PermissionError, ValueError) as exc:
            self._edit_status_error(exc)
        else:
            self.status_message.emit(
                f"Pasted {len(created)} object(s)" if created else "No objects pasted"
            )
        return True

    def _handle_history_key(self, *, redo: bool) -> bool:
        if self._block_if_preview():
            return True
        changed = self.redo() if redo else self.undo()
        self.status_message.emit(
            ("Redo applied" if redo else "Undo applied")
            if changed
            else ("Nothing to redo" if redo else "Nothing to undo")
        )
        return True

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta_y = event.angleDelta().y()
        if delta_y == 0:
            event.accept()
            return
        self._zoom_at(QPointF(event.position()), float(delta_y))
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        if key in {
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        } and not (
            modifiers
            & (
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.AltModifier
                | Qt.KeyboardModifier.MetaModifier
            )
        ):
            self._handle_nudge_key(key, modifiers)
            event.accept()
            return
        if key == Qt.Key.Key_D and modifiers == Qt.KeyboardModifier.ControlModifier:
            self._handle_duplicate_key()
            event.accept()
            return
        if key == Qt.Key.Key_Delete and modifiers == Qt.KeyboardModifier.NoModifier:
            self._handle_delete_key()
            event.accept()
            return
        if key == Qt.Key.Key_C and modifiers == Qt.KeyboardModifier.ControlModifier:
            self._handle_copy_key()
            event.accept()
            return
        if key == Qt.Key.Key_V and modifiers == Qt.KeyboardModifier.ControlModifier:
            self._handle_paste_key()
            event.accept()
            return
        if key == Qt.Key.Key_Z and modifiers == Qt.KeyboardModifier.ControlModifier:
            self._handle_history_key(redo=False)
            event.accept()
            return
        if key == Qt.Key.Key_Y and modifiers == Qt.KeyboardModifier.ControlModifier:
            self._handle_history_key(redo=True)
            event.accept()
            return
        if key == Qt.Key.Key_A and modifiers & Qt.KeyboardModifier.ControlModifier:
            self._select_all_visible()
            event.accept()
            return
        if key == Qt.Key.Key_Escape:
            if self._marquee_origin is not None:
                selected = self._marquee_selection_before or ()
                primary = self._marquee_primary_before
                if primary not in selected:
                    primary = selected[-1] if selected else None
                self._set_selection(selected, primary)
                self._clear_marquee()
            else:
                self._set_selection((), None)
            event.accept()
            return
        super().keyPressEvent(event)

    def _edit_block_reason(self, object_id: str) -> str | None:
        item = next(
            (value for value in self.session.document.objects if value.id == object_id),
            None,
        )
        if item is None:
            return None
        if item.locked:
            return f"Cannot edit '{object_id}': the object is locked."
        layer = next(
            (
                value
                for value in self.session.document.layers
                if value.id == item.layer_id
            ),
            None,
        )
        if layer is not None and layer.locked:
            return f"Cannot edit '{object_id}': its layer is locked."
        locked_group = locked_group_for_object(self.session.document, object_id)
        if locked_group is not None:
            return f"Cannot edit '{object_id}': group '{locked_group.name}' is locked."
        return None

    def _selection_edit_block_reason(self) -> str | None:
        for object_id in self.session.selection.ids:
            reason = self._edit_block_reason(object_id)
            if reason is not None:
                return reason
        return None

    def _object_pressed(self, object_id: str, scene_pos: QPointF, modifiers) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        visible_ids = set(self._visible_object_ids())
        current = [item for item in self.session.selection.ids if item in visible_ids]
        if modifiers & Qt.KeyboardModifier.ShiftModifier and not (
            modifiers & Qt.KeyboardModifier.ControlModifier
        ):
            ordered = self._visible_object_ids()
            anchor = self.session.selection.primary
            if anchor in ordered and object_id in ordered:
                start = ordered.index(anchor)
                end = ordered.index(object_id)
                current = list(ordered[min(start, end) : max(start, end) + 1])
            else:
                current = [object_id]
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            if object_id in current:
                current.remove(object_id)
            else:
                current.append(object_id)
        else:
            current = [object_id]
        self._set_selection(current, object_id if object_id in current else None)
        if object_id not in self.session.selection.ids:
            return
        if not self._authoring_enabled:
            self.status_message.emit("Preview mode is read-only")
            return
        item = next(
            (value for value in self.session.document.objects if value.id == object_id),
            None,
        )
        if item is None:
            return
        reason = self._edit_block_reason(object_id)
        if reason is not None:
            self.status_message.emit(reason)
            return
        self._item_gesture_id = object_id
        self._gesture_layer_id = item.layer_id
        self._gesture_start = scene_pos
        self.session.begin_gesture()
        self.selection_changed.emit()
        self._refresh_selection()
        self._refresh_gizmo()

    def _object_moved(self, object_id: str, scene_pos: QPointF) -> None:
        if not self._authoring_enabled:
            return
        if self._item_gesture_id != object_id or self._gesture_start is None:
            return
        layer_id = self._gesture_layer_id or ""
        start = self._world_position(self._gesture_start, layer_id)
        current = self._world_position(scene_pos, layer_id)
        delta = current - start
        try:
            self.session.preview_transform_selected(
                translation=Point3Record(x=delta.x(), y=delta.y(), z=0.0)
            )
        except PermissionError:
            self.session.cancel_gesture()
            self._item_gesture_id = None
            self._gesture_layer_id = None
            self._gesture_start = None
            self.status_message.emit(
                self._edit_block_reason(object_id)
                or f"Cannot move '{object_id}': editing is locked."
            )
            return
        self._refresh_after_model_change()

    def _object_released(self, object_id: str, scene_pos: QPointF) -> None:
        del scene_pos
        if not self._authoring_enabled:
            return
        if self._item_gesture_id == object_id:
            self.session.finish_gesture("Move objects")
        self._item_gesture_id = None
        self._gesture_layer_id = None
        self._gesture_start = None
        self._refresh_after_model_change()
        self.status_message.emit("Objects moved")

    def _gizmo_started(self, mode: str, scene_pos: QPointF) -> None:
        if not self._authoring_enabled:
            self.status_message.emit("Preview mode is read-only")
            return
        reason = self._selection_edit_block_reason()
        if reason is not None:
            self.status_message.emit(reason)
            return
        self._gesture_mode = mode
        self._gizmo_start = scene_pos
        self.session.begin_gesture()

    def _gizmo_changed(self, mode: str, scene_pos: QPointF) -> None:
        if (
            not self._authoring_enabled
            or self._gizmo_start is None
            or self._gesture_mode != mode
        ):
            return
        primary = self.session.selection.primary
        if primary is None:
            return
        record = next(
            item for item in self.session.document.objects if item.id == primary
        )
        start_world = self._world_position(self._gizmo_start, record.layer_id)
        current_world = self._world_position(scene_pos, record.layer_id)
        delta = current_world - start_world
        if mode == "translate_x":
            delta.setY(0.0)
        elif mode == "translate_y":
            delta.setX(0.0)
        try:
            if mode in {"translate", "translate_x", "translate_y"}:
                self.session.preview_transform_selected(
                    translation=Point3Record(x=delta.x(), y=delta.y(), z=0.0)
                )
            elif mode == "scale":
                factor = max(0.05, 1.0 + (delta.x() + delta.y()) / 160.0)
                self.session.preview_transform_selected(scale_factor=factor)
            elif mode == "rotate":
                center = self._project_position(
                    record.transform.position, record.layer_id
                )
                start_angle = math.degrees(
                    math.atan2(
                        self._gizmo_start.y() - center.y(),
                        self._gizmo_start.x() - center.x(),
                    )
                )
                current_angle = math.degrees(
                    math.atan2(
                        scene_pos.y() - center.y(),
                        scene_pos.x() - center.x(),
                    )
                )
                self.session.preview_transform_selected(
                    rotation_z=current_angle - start_angle
                )
        except PermissionError:
            self.session.cancel_gesture()
            self._gesture_mode = None
            self._gizmo_start = None
            self.status_message.emit(
                self._selection_edit_block_reason()
                or "Cannot transform the selection: editing is locked."
            )
            return
        self._refresh_after_model_change()

    def _gizmo_finished(self, mode: str, scene_pos: QPointF) -> None:
        del scene_pos
        if not self._authoring_enabled:
            return
        if self._gizmo_start is None or self._gesture_mode != mode:
            return
        self.session.finish_gesture(f"Apply {mode} gizmo transform")
        self._gesture_mode = None
        self._gizmo_start = None
        self._refresh_after_model_change()
        self.status_message.emit("Transform applied")

    def undo(self) -> bool:
        changed = self.session.undo()
        if changed:
            self.sync()
        return changed

    def redo(self) -> bool:
        changed = self.session.redo()
        if changed:
            self.sync()
        return changed

    def dragEnterEvent(self, event) -> None:
        if not self._authoring_enabled:
            event.ignore()
            return
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if not self._authoring_enabled:
            self.status_message.emit("Preview mode is read-only")
            event.ignore()
            return
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if not paths and event.mimeData().hasText():
            paths = [Path(event.mimeData().text())]
        if not paths:
            self.status_message.emit("Drop an image asset onto the viewport")
            event.ignore()
            return
        path = paths[0].resolve(strict=False)
        if self.project_root is None:
            self.status_message.emit("Save the project before importing scene assets")
            event.ignore()
            return
        try:
            source = validate_scene_asset_source(path)
            # Decode before copying so invalid content never enters the project.
            self._image_size(source)
            prepared = prepare_scene_asset(source, self.project_root)
            width, height = self._image_size(prepared.resolved_path)
            asset_id = "asset_" + prepared.sha256[:16]
            layer_id = self.session.document.layers[0].id
            object_id = asset_id
            while asset_id in {asset.id for asset in self.session.document.assets}:
                asset_id += "_1"
            while object_id in {item.id for item in self.session.document.objects}:
                object_id += "_1"
            position = event.position()
            scene_pos = self.mapToScene(position.toPoint())
            asset = AssetReferenceRecord(
                id=asset_id,
                path=prepared.path,
                sha256=prepared.sha256,
                source_path=prepared.source_path,
            )
            obj = SceneObjectAuthoringRecord(
                id=object_id,
                asset_id=asset_id,
                layer_id=layer_id,
                transform=SceneTransformRecord(
                    position=Point3Record(x=scene_pos.x(), y=scene_pos.y(), z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )

            def operation() -> None:
                self.session.model.add_asset(asset)
                self.session.model.add_object(obj, select=True)

            self.session.apply(operation, "Import scene asset")
            self._geometry[object_id] = (
                (-width / 2, -height / 2),
                (width / 2, -height / 2),
                (width / 2, height / 2),
                (-width / 2, height / 2),
            )
            self.sync()
            self.selection_changed.emit()
            self.status_message.emit(f"Imported {path.name}")
            event.acceptProposedAction()
        except (OSError, ValueError, SceneAssetError) as exc:
            self.status_message.emit(str(exc))
            event.ignore()

    @staticmethod
    def _load_asset_pixmap(path: Path) -> QPixmap:
        if path.suffix.lower() == ".svg":
            renderer = QSvgRenderer(str(path))
            if not renderer.isValid():
                raise ValueError("asset SVG could not be decoded")
            size = renderer.defaultSize()
            width, height = max(1, size.width()), max(1, size.height())
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return pixmap
        image = QImage(str(path))
        if image.isNull():
            raise ValueError("asset image could not be decoded")
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            raise ValueError("asset image could not be converted for rendering")
        return pixmap

    @classmethod
    def _image_size(cls, path: Path) -> tuple[float, float]:
        pixmap = cls._load_asset_pixmap(path)
        return float(max(1, pixmap.width())), float(max(1, pixmap.height()))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_navigation_scene_rect()
        self._apply_navigation_transform()
        if self._preview_enabled:
            self._refresh_after_model_change()

    def drawBackground(self, painter, rect: QRectF | QRect) -> None:
        painter.fillRect(rect, QColor("#111820"))
        pen = QPen(QColor("#1e2c39"), 1.0)
        painter.setPen(pen)
        left = math.floor(rect.left() / 32.0) * 32.0
        top = math.floor(rect.top() / 32.0) * 32.0
        x = left
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += 32.0
        y = top
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += 32.0

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._marquee_origin is not None and self._marquee_current is not None:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(QBrush(QColor(35, 135, 184, 45)))
            painter.setPen(QPen(QColor("#65d7ff"), 1.0, Qt.PenStyle.DashLine))
            start = self.mapFromScene(self._marquee_origin)
            end = self.mapFromScene(self._marquee_current)
            painter.drawRect(QRectF(start, end).normalized())
            painter.end()
        if not self._overlay_visible:
            self._paint_navigation_state()
            return
        size = self.viewport().size()
        geometry = build_overlay_geometry((float(size.width()), float(size.height())))
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for x, y, width, height in geometry.crop_regions:
            if width > 0.0 and height > 0.0:
                painter.fillRect(
                    QRectF(x, y, width, height),
                    QColor(4, 8, 12, 150),
                )
        frame = geometry.frame
        safe = geometry.safe_area
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#59d8e8"), 2.0))
        painter.drawRect(QRectF(*frame))
        painter.setPen(QPen(QColor("#a8dce7"), 1.0, Qt.PenStyle.DashLine))
        painter.drawRect(QRectF(*safe))
        painter.setPen(QPen(QColor("#e8edf2"), 1.0))
        painter.drawText(
            QPointF(frame[0] + 8.0, frame[1] + 20.0),
            "16:9  SAFE 90%",
        )
        painter.end()
        self._paint_navigation_state()
