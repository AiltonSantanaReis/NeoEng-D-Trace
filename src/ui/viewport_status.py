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
    language = {"value": "en"}

    def localized_details(state: ViewportState) -> str:
        if language["value"] == "pt":
            snap = "LIGADO" if state.snap_enabled else "DESLIGADO"
            grid = "LIGADA" if state.grid_visible else "DESLIGADA"
            gizmo = "LIGADO" if state.gizmo_enabled else "DESLIGADO"
            selection = (
                ",".join(state.selection_ids) if state.selection_ids else "NENHUM"
            )
            return (
                f"VISUALIZAÇÃO: {state.view_mode} | ZOOM: {state.zoom:.2f}x | "
                f"ENCAIXE: {snap} | GRADE: {grid} | EIXO: {gizmo} | "
                f"PAN: {state.pan_x:.0f},{state.pan_y:.0f} | "
                f"SELEÇÃO: {selection} | CURSOR: {state.cursor_x},{state.cursor_y}"
            )
        return format_viewport_details(state)

    status.setToolTip(localized_details(window.canvas.viewport_state()))
    window.statusBar().addPermanentWidget(status)

    def update(state: ViewportState) -> None:
        status.setText(format_compact_viewport_details(state))
        status.setToolTip(localized_details(state))

    def update_language(language_name: str) -> None:
        language["value"] = language_name if language_name in {"en", "pt"} else "en"
        canvas = getattr(window, "canvas", None)
        if canvas is not None and hasattr(canvas, "viewport_state"):
            update(canvas.viewport_state())

    setattr(status, "update_language", update_language)

    window.viewport_status = status
    window.canvas.viewport_state_model_changed.connect(update)
    update(window.canvas.viewport_state())
    return status
