"""Qt adapter for the P2D-05 user-facing error contract."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QStatusBar, QWidget

from src.core.logger import logger
from src.persistence.p2d05_presentation import (
    P2D05Presentation,
    build_p2d05_presentation,
)
from src.ui.p2d05_status_notice import P2D05StatusNotice

_STATUS_PERSISTENT_TIMEOUT_MS = 0
_TITLES = {
    "en": {
        "INFO": "Information",
        "WARNING": "Action needs attention",
        "ERROR": "Operation failed",
        "CRITICAL": "Operation failed",
    },
    "pt": {
        "INFO": "Informação",
        "WARNING": "Atenção necessária",
        "ERROR": "Falha na operação",
        "CRITICAL": "Falha na operação",
    },
}


def _status_bar_for(parent: QWidget | None) -> QStatusBar | None:
    if not isinstance(parent, QWidget):
        return None
    candidates = [parent]
    try:
        candidates.append(parent.window())
    except RuntimeError:
        pass
    for candidate in candidates:
        getter = getattr(candidate, "statusBar", None)
        if not callable(getter):
            continue
        try:
            status_bar = getter()
        except RuntimeError:
            continue
        if isinstance(status_bar, QStatusBar):
            return status_bar
    return None


def _log_p2d05_presentation(
    presentation: P2D05Presentation,
    exc: BaseException,
) -> None:
    level = (
        logging.ERROR
        if presentation.severity in {"ERROR", "CRITICAL"}
        else logging.WARNING
    )
    traceback_info = (
        (type(exc), exc, exc.__traceback__) if exc.__traceback__ is not None else None
    )
    logger.log(
        level,
        "P2D05 %s operation=%s detail=%s",
        presentation.code,
        presentation.operation,
        presentation.safe_detail or "details unavailable",
        exc_info=traceback_info,
    )


def show_p2d05_error(
    parent: QWidget | None,
    exc: BaseException,
    *,
    operation: str,
    language: str = "en",
    severity: str = "warning",
    channel: str = "modal",
) -> P2D05Presentation:
    """Render one safe P2D-05 failure through the requested Qt channel."""

    presentation = build_p2d05_presentation(
        exc,
        operation=operation,
        language=language,
        severity=severity,
        channel=channel,
    )
    _log_p2d05_presentation(presentation, exc)

    if presentation.channel == "STATUS":
        status_bar = _status_bar_for(parent)
        if status_bar is not None:
            notice = status_bar.findChild(P2D05StatusNotice, "p2d05_status_notice")
            if notice is None:
                notice = P2D05StatusNotice(status_bar)
                status_bar.insertPermanentWidget(0, notice, 1)
            notice.present(presentation, parent)
            status_bar.showMessage(
                presentation.message,
                _STATUS_PERSISTENT_TIMEOUT_MS,
            )
        else:
            logger.log(
                (
                    logging.ERROR
                    if presentation.severity in {"ERROR", "CRITICAL"}
                    else logging.WARNING
                ),
                "P2D05 %s status channel is unavailable because no QStatusBar exists",
                presentation.code,
            )
        return presentation

    if not isinstance(parent, QWidget):
        logger.log(
            (
                logging.ERROR
                if presentation.severity in {"ERROR", "CRITICAL"}
                else logging.WARNING
            ),
            "P2D05 %s could not be displayed because no QWidget parent exists",
            presentation.code,
        )
        return presentation

    box = QMessageBox(parent)
    if presentation.severity in {"ERROR", "CRITICAL"}:
        icon = QMessageBox.Icon.Critical
    elif presentation.severity == "WARNING":
        icon = QMessageBox.Icon.Warning
    else:
        icon = QMessageBox.Icon.Information
    box.setIcon(icon)
    box.setWindowTitle(_TITLES[presentation.language][presentation.severity])
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setText(presentation.message)
    box.setDetailedText(presentation.detailed_text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.setDefaultButton(QMessageBox.StandardButton.Ok)
    box.setAccessibleName(presentation.code)
    box.exec()
    return presentation


__all__ = [
    "P2D05Presentation",
    "build_p2d05_presentation",
    "show_p2d05_error",
]
