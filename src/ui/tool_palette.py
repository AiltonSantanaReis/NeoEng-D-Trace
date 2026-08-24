"""Public compatibility entry point for the Stage 3 tool toolbar."""

from __future__ import annotations

from PySide6.QtCore import QSize

from src.ui.tool_palette_impl import ToolPalette as _ActionToolPalette


class ToolPalette(_ActionToolPalette):
    """Action-backed vertical toolbar with a stable transition width."""

    def _refresh_button_geometry(self) -> None:
        super()._refresh_button_geometry()
        self.setMinimumWidth(56)
        self.setMaximumWidth(72)
        for button in self.tool_buttons.values():
            button.setMinimumSize(QSize(44, 40))
            button.setMaximumWidth(56)
            button.updateGeometry()
        self.updateGeometry()


__all__ = ["ToolPalette"]
