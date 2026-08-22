"""Viewport status-bar adapter for the main editor window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


def configure_viewport_status(window) -> QLabel:
    """Install the live viewport state indicator without growing MainWindow."""

    status = QLabel(window)
    status.setObjectName("viewport_status")
    status.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status.setMinimumWidth(210)
    status.setAccessibleName("Viewport status")
    status.setToolTip("Current viewport mode and zoom")
    window.statusBar().addPermanentWidget(status)

    def update(text: str | None = None) -> None:
        status.setText(text or window.canvas.viewport_state_text())

    window.viewport_status = status
    window.canvas.viewport_state_changed.connect(update)
    update()
    return status
