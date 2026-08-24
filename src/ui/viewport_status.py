"""Viewport status-bar adapter for the main editor window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


def configure_viewport_status(window) -> QLabel:
    """Install the live viewport state indicator without growing MainWindow."""

    status = QLabel(window)
    status.setObjectName("viewport_status")
    status.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status.setMinimumWidth(160)
    status.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
    status.setAccessibleName("Viewport status")
    status.setToolTip("Viewport, zoom, snap, grid, gizmo, selection and cursor state")
    window.statusBar().addPermanentWidget(status)

    def update(text: str | None = None) -> None:
        full = text or window.canvas.viewport_details_text()
        status.setText(window.canvas.viewport_compact_details_text())
        status.setToolTip(full)

    window.viewport_status = status
    window.canvas.viewport_details_changed.connect(update)
    update(window.canvas.viewport_details_text())
    return status
