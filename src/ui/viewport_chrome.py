"""Viewport chrome matching the reference editor composition."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QStackedLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.viewport_state import ViewportState


class _Ruler(QWidget):
    def __init__(self, canvas, *, horizontal: bool, parent=None) -> None:
        super().__init__(parent)
        self.canvas = canvas
        self.horizontal = horizontal
        self.setObjectName(
            "viewport_horizontal_ruler" if horizontal else "viewport_vertical_ruler"
        )
        if horizontal:
            self.setMinimumHeight(28)
            self.setMaximumHeight(28)
        else:
            self.setMinimumWidth(28)
            self.setMaximumWidth(28)
        canvas.viewport_state_model_changed.connect(lambda _state: self.update())

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#18222d"))
        painter.setPen(QPen(QColor("#718396"), 1))
        painter.setFont(QFont("Segoe UI", 8))
        zoom = max(0.01, float(self.canvas.get_zoom()))
        pan = self.canvas._pan
        if self.horizontal:
            origin = float(pan.x())
            length = self.width()
            for image_x in range(-2000, 4001, 100):
                screen_x = origin + image_x * zoom
                if screen_x < 0 or screen_x >= length:
                    continue
                tick = 10 if image_x % 500 else 18
                painter.drawLine(
                    int(screen_x), self.height() - tick, int(screen_x), self.height()
                )
                if image_x % 500 == 0:
                    painter.drawText(int(screen_x) + 3, 12, str(image_x))
        else:
            origin = float(pan.y())
            length = self.height()
            for image_y in range(-2000, 4001, 100):
                screen_y = origin + image_y * zoom
                if screen_y < 0 or screen_y >= length:
                    continue
                tick = 10 if image_y % 500 else 18
                painter.drawLine(
                    self.width() - tick, int(screen_y), self.width(), int(screen_y)
                )
                if image_y % 500 == 0:
                    painter.save()
                    painter.translate(12, int(screen_y) + 3)
                    painter.rotate(-90)
                    painter.drawText(0, 0, str(image_y))
                    painter.restore()


class ViewportOverlayBar(QWidget):
    """Clickable view/zoom/snap controls over the lower viewport edge."""

    def __init__(self, window, canvas, parent=None) -> None:
        super().__init__(parent)
        self.host_window = window
        self.canvas = canvas
        self._compact = False
        self.setObjectName("viewport_overlay_bar")
        self.setFixedHeight(38)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.view_button = QToolButton(self)
        self.view_button.setObjectName("viewport_view_button")
        self.view_button.setText('View: Lit')
        self.view_button.setAccessibleName('Viewport view menu')
        self.view_button.setAccessibleDescription('Choose Lit or X-Ray viewport rendering')
        self.view_button.setToolTip('Choose viewport rendering mode')
        self.view_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        view_menu = QMenu(self.view_button)
        for action in (
            window.act_lit,
            window.act_xray1,
            window.act_xray2,
            window.act_xray3,
        ):
            view_menu.addAction(action)
        self.view_button.setMenu(view_menu)

        self.zoom_button = QToolButton(self)
        self.zoom_button.setObjectName("viewport_zoom_button")
        self.zoom_button.setText('Zoom: 1.00x')
        self.zoom_button.setAccessibleName('Viewport zoom menu')
        self.zoom_button.setAccessibleDescription('Choose fit-to-window or one-to-one viewport zoom')
        self.zoom_button.setToolTip('Choose viewport zoom')
        self.zoom_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.zoom_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        zoom_menu = QMenu(self.zoom_button)
        zoom_menu.addAction(window.act_fit)
        zoom_menu.addAction(window.act_100)
        self.zoom_button.setMenu(zoom_menu)

        self.snap_button = QToolButton(self)
        self.snap_button.setObjectName("viewport_snap_button")
        self.snap_button.setCheckable(True)
        self.snap_button.setAccessibleName('Toggle vertex snapping')
        self.snap_button.setAccessibleDescription('Enable or disable snapping edited vertices to the active grid')
        self.snap_button.setToolTip('Toggle real vertex snapping')
        self.snap_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.snap_button.toggled.connect(self._set_snap)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(8)
        layout.addWidget(self.view_button)
        layout.addWidget(self.zoom_button)
        layout.addWidget(self.snap_button)
        layout.addStretch(1)
        canvas.viewport_state_model_changed.connect(self._sync)
        self._sync(canvas.viewport_state())

    def set_compact(self, compact: bool) -> None:
        self._compact = bool(compact)
        self._sync(self.canvas.viewport_state())

    def _set_snap(self, enabled: bool) -> None:
        self.canvas.set_vertex_snapping(enabled, grid_size=16)

    def _sync(self, state: ViewportState) -> None:
        mode = state.view_mode.title()
        if self._compact:
            self.view_button.setText(mode)
            self.zoom_button.setText(f"{state.zoom:.2f}x")
        else:
            self.view_button.setText(f"View: {mode}")
            self.zoom_button.setText(f"Zoom: {state.zoom:.2f}x")
        self.snap_button.blockSignals(True)
        self.snap_button.setChecked(state.snap_enabled)
        self.snap_button.blockSignals(False)
        snap_state = f"{'On' if state.snap_enabled else 'Off'} ({state.snap_grid_size})"
        self.snap_button.setText(
            f'Snap {snap_state}' if self._compact else f'Snap: {snap_state}'
        )
        self.view_button.setAccessibleDescription(
            f'Choose viewport rendering mode; current mode: {mode}'
        )
        self.zoom_button.setAccessibleDescription(
            f'Choose viewport zoom; current zoom: {state.zoom:.2f}x'
        )
        self.snap_button.setAccessibleDescription(
            'Enable or disable snapping edited vertices to the active grid; '
            f'current state: {snap_state}'
        )


class ViewportChrome(QWidget):
    """Add rulers and the reference HUD without replacing CanvasView."""

    def __init__(self, window, canvas, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("viewport_chrome")
        self.canvas = canvas
        self.horizontal_ruler = _Ruler(canvas, horizontal=True, parent=self)
        self.vertical_ruler = _Ruler(canvas, horizontal=False, parent=self)
        self.canvas_stack = QWidget(self)
        stack = QStackedLayout(self.canvas_stack)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.addWidget(canvas)
        # Keep the HUD out of the layout-managed stack. Text/state changes in
        # View, Zoom or Snap must not trigger a layout pass that repositions
        # the overlay by a few pixels.
        self.overlay = ViewportOverlayBar(window, canvas, self.canvas_stack)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.vertical_ruler)
        body.addWidget(self.canvas_stack, 1)
        layout.addWidget(self.horizontal_ruler)
        layout.addLayout(body, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.overlay.set_compact(self.canvas_stack.width() < 900)
        self.overlay.setGeometry(
            8,
            10,
            max(1, self.canvas_stack.width() - 16),
            self.overlay.height(),
        )
        self.overlay.raise_()


__all__ = ["ViewportChrome", "ViewportOverlayBar"]
