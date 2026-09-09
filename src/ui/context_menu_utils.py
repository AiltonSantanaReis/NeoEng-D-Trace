"""Shared sizing rules for transient context menus."""

from __future__ import annotations

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QMenu


def fit_context_menu(menu: QMenu) -> QMenu:
    """Size a context menu to its localized labels without excess whitespace.

    Native popup metrics can under-report a menu width on Windows when a
    stylesheet and a high-DPI scale factor are active.  Measuring the actual
    localized labels and applying an explicit minimum keeps Portuguese labels
    readable while retaining compact menus for short actions.
    """

    # Lightweight menu probes used by the coverage suite intentionally expose
    # only the popup contract.  Keep those probes compatible while applying
    # native sizing only to real QMenu instances.
    if not hasattr(menu, "font") or not callable(getattr(menu, "actions", None)):
        if hasattr(menu, "adjustSize"):
            menu.adjustSize()
        return menu

    if hasattr(menu, "ensurePolished"):
        menu.ensurePolished()
    metrics = QFontMetrics(menu.font())
    longest = 0
    for action in menu.actions():
        text = action.text().replace("&", "")
        if text:
            longest = max(longest, metrics.horizontalAdvance(text))
        submenu = action.menu()
        if submenu is not None:
            fit_context_menu(submenu)

    # Account for the QMenu item padding, frame, and a small safety margin for
    # native font rounding without introducing a fixed global width.
    if longest:
        scale = max(1.0, float(getattr(menu, "devicePixelRatioF", lambda: 1.0)()))
        menu.setMinimumWidth(int((longest + 48) * scale))
    menu.adjustSize()
    return menu


__all__ = ["fit_context_menu"]
