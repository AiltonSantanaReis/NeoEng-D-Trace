"""Thin Qt timer adapter for autosave callbacks."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer


class AutosaveController:
    def __init__(
        self,
        parent,
        callback: Callable[[], bool],
        *,
        interval_seconds: int,
    ) -> None:
        bounded_seconds = min(max(int(interval_seconds), 15), 3_600)
        self.timer = QTimer(parent)
        self.timer.setInterval(bounded_seconds * 1_000)
        self.timer.timeout.connect(callback)
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()
