"""Viewport settings dialog adapter for the MainWindow."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout


def open_view_settings(window: Any) -> None:
    """Open and commit the live Grid/Snap settings for the window."""

    dialog = QDialog(window)
    dialog.setObjectName("view_settings_dialog")
    dialog.setWindowTitle(window.translations[window.current_lang]["view_settings"])
    dialog.setModal(True)
    layout = QVBoxLayout(dialog)

    text = window.translations[window.current_lang]
    grid = QCheckBox(text["grid"], dialog)
    grid.setObjectName("view_settings_grid")
    grid.setChecked(window.canvas.is_grid_visible())
    grid.setAccessibleName(text["grid"])
    layout.addWidget(grid)

    snap = QCheckBox(text["snap"], dialog)
    snap.setObjectName("view_settings_snap")
    snap.setChecked(window.canvas._vertex_snap_settings.enabled)
    snap.setAccessibleName(text["snap"])
    layout.addWidget(snap)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        parent=dialog,
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    window.view_settings_dialog = dialog
    if dialog.exec() == QDialog.DialogCode.Accepted:
        window.canvas.set_grid_visible(grid.isChecked())
        window.act_grid.setChecked(grid.isChecked())
        window.canvas.set_vertex_snapping(snap.isChecked(), grid_size=16)
        window.act_snap.setChecked(snap.isChecked())
