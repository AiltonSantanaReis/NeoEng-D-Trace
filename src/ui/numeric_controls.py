"""Safe numeric controls used by the scene inspectors.

Numeric fields in an editor must not change because the pointer happened to
pass over them while the user was navigating.  The label is also a useful,
discoverable place for scrubbing, so the control pair exposes that behavior
without adding another button to the inspector.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QDoubleSpinBox, QLabel


class ProtectedDoubleSpinBox(QDoubleSpinBox):
    """A numeric editor whose value cannot be changed by accidental scrolling."""

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        # Scrolling over an inspector field should scroll the inspector, not
        # silently mutate the scene.  Keyboard arrows, typing and scrubbing
        # remain explicit editing gestures.
        event.ignore()


class ScrubbableLabel(QLabel):
    """Label that changes its associated numeric field while being dragged."""

    PIXELS_PER_STEP = 4.0

    def __init__(self, text: str, target: QDoubleSpinBox, parent=None) -> None:
        super().__init__(text, parent)
        self.target = target
        self._scrub_origin_x: float | None = None
        self._scrub_origin_value = 0.0
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        self.setToolTip("Arraste horizontalmente para ajustar; wheel protegido")
        self.setAccessibleDescription(
            "Arraste horizontalmente para ajustar este valor; "
            "rolagem não altera o valor"
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._scrub_origin_x = float(event.position().x())
            self._scrub_origin_value = float(self.target.value())
            self.target.setFocus(Qt.FocusReason.MouseFocusReason)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._scrub_origin_x is not None:
            delta = float(event.position().x()) - self._scrub_origin_x
            steps = delta / self.PIXELS_PER_STEP
            value = self._scrub_origin_value + steps * float(self.target.singleStep())
            self.target.setValue(value)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._scrub_origin_x is not None
        ):
            self._scrub_origin_x = None
            event.accept()
            return
        super().mouseReleaseEvent(event)


__all__ = ["ProtectedDoubleSpinBox", "ScrubbableLabel"]
