"""Viewport status-bar adapter for the main editor window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy

from src.ui.viewport_state import (
    ViewportState,
    format_compact_viewport_details,
    format_viewport_details,
)


def configure_viewport_status(window) -> QLabel:
    """Install the live viewport indicator from structured state."""

    status = QLabel(window)
    status.setObjectName("viewport_status")
    status.setAlignment(Qt.AlignmentFlag.AlignCenter)
    status.setMinimumWidth(160)
    status.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
    status.setAccessibleName("Viewport status")
    status.setToolTip("Viewport, zoom, snap, grid, gizmo, selection and cursor state")
    window.statusBar().addPermanentWidget(status)

    def update(state: ViewportState) -> None:
        status.setText(format_compact_viewport_details(state))
        status.setToolTip(format_viewport_details(state))

    window.viewport_status = status
    window.canvas.viewport_state_model_changed.connect(update)
    update(window.canvas.viewport_state())
    return status
