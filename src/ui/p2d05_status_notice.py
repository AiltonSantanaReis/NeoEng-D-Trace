"""Readable, non-interrupting status errors with explicitly requested details."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.persistence.p2d05_presentation import P2D05Presentation

_LABELS = {
    "pt": {
        "details": "Detalhes",
        "dismiss": "Dispensar",
        "title": "Detalhes seguros do erro",
        "copy": "Copiar diagnóstico",
        "close": "Fechar",
    },
    "en": {
        "details": "Details",
        "dismiss": "Dismiss",
        "title": "Safe error details",
        "copy": "Copy diagnostic",
        "close": "Close",
    },
}


class P2D05StatusNotice(QWidget):
    """One bounded notice per status bar; no document or history references."""

    def __init__(self, status_bar: QStatusBar) -> None:
        super().__init__(status_bar)
        self.setObjectName("p2d05_status_notice")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._status_bar = status_bar
        self._presentation: P2D05Presentation | None = None
        self._origin: QWidget | None = None
        self._dialog: QDialog | None = None
        self._diagnostic: QPlainTextEdit | None = None
        self._copy_button: QPushButton | None = None
        self._close_button: QPushButton | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.message = QLabel(self)
        self.message.setObjectName("p2d05_status_message")
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        self.message.setMinimumWidth(0)
        self.message.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.message.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.message, 1)
        buttons = QHBoxLayout()
        self.details = QPushButton(self)
        self.details.setObjectName("p2d05_status_details")
        self.details.clicked.connect(self._show_details)
        self.dismiss = QPushButton(self)
        self.dismiss.setObjectName("p2d05_status_dismiss")
        self.dismiss.clicked.connect(self._dismiss)
        buttons.addWidget(self.details)
        buttons.addWidget(self.dismiss)
        layout.addLayout(buttons)
        status_bar.messageChanged.connect(self._message_changed)
        self.hide()

    def present(self, presentation: P2D05Presentation, origin: QWidget | None) -> None:
        self._presentation = presentation
        if self._origin is not origin:
            if self._origin is not None:
                self._origin.destroyed.disconnect(self._origin_destroyed)
            self._origin = origin
            if origin is not None:
                origin.destroyed.connect(self._origin_destroyed)
        labels = _LABELS[presentation.language]
        self.message.setText(
            f"{presentation.headline} [{presentation.code}]. "
            f"{presentation.action}. {presentation.preserved_state}."
        )
        self.message.setAccessibleName(self.message.text())
        self.setAccessibleName(presentation.code)
        for button, key in ((self.details, "details"), (self.dismiss, "dismiss")):
            button.setText(labels[key])
            button.setAccessibleName(f"{labels[key]} — {presentation.code}")
        self._update_details()
        self.show()
        self._fit_text_height()
        self.updateGeometry()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._fit_text_height()

    def _fit_text_height(self) -> None:
        layout = self.layout()
        if layout is None or self.width() < self.minimumSizeHint().width():
            return
        layout.activate()
        margins = layout.contentsMargins()
        height = (
            max(
                self.message.heightForWidth(self.message.width()),
                self.details.sizeHint().height(),
                self.dismiss.sizeHint().height(),
            )
            + margins.top()
            + margins.bottom()
        )
        # QStatusBar otherwise uses the label's unconstrained size hint,
        # reserving many lines even when the actual width needs only two.
        if self.minimumHeight() != height or self.maximumHeight() != height:
            self.setFixedHeight(height)

    def _message_changed(self, message: str) -> None:
        if self._presentation is not None and message != self._presentation.message:
            self.hide()
            if self._dialog is not None:
                self._dialog.close()

    def _origin_destroyed(self) -> None:
        self._origin = None

    def _dismiss(self) -> None:
        self.hide()
        if self._dialog is not None:
            self._dialog.close()
        if (
            self._presentation is not None
            and self._status_bar.currentMessage() == self._presentation.message
        ):
            self._status_bar.clearMessage()
        if self._origin is not None and self._origin.isVisible():
            self._origin.setFocus(Qt.FocusReason.OtherFocusReason)

    def _show_details(self) -> None:
        if self._presentation is None:
            return
        if self._dialog is None:
            self._dialog = QDialog(self)
            self._dialog.setObjectName("p2d05_status_details_dialog")
            self._dialog.setModal(False)
            self._dialog.resize(640, 400)
            layout = QVBoxLayout(self._dialog)
            self._diagnostic = QPlainTextEdit(self._dialog)
            self._diagnostic.setObjectName("p2d05_safe_diagnostic")
            self._diagnostic.setReadOnly(True)
            layout.addWidget(self._diagnostic)
            buttons = QHBoxLayout()
            self._copy_button = QPushButton(self._dialog)
            self._copy_button.setObjectName("p2d05_copy_diagnostic")
            self._copy_button.clicked.connect(self._copy_diagnostic)
            buttons.addWidget(self._copy_button)
            self._close_button = QPushButton(self._dialog)
            self._close_button.setObjectName("p2d05_close_details")
            self._close_button.setDefault(True)
            self._close_button.clicked.connect(self._dialog.accept)
            buttons.addWidget(self._close_button)
            layout.addLayout(buttons)
            self._dialog.finished.connect(self._restore_details_focus)
        self._update_details()
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()
        if self._close_button is not None:
            self._close_button.setFocus()

    def _update_details(self) -> None:
        if self._dialog is None or self._presentation is None:
            return
        presentation = self._presentation
        labels = _LABELS[presentation.language]
        self._dialog.setWindowTitle(labels["title"])
        self._dialog.setAccessibleName(f"{labels['title']} — {presentation.code}")
        if self._diagnostic is not None:
            self._diagnostic.setPlainText(
                f"{presentation.message}\n\n{presentation.detailed_text}"
            )
            self._diagnostic.setAccessibleName(labels["title"])
        for button, key in ((self._copy_button, "copy"), (self._close_button, "close")):
            if button is not None:
                button.setText(labels[key])
                button.setAccessibleName(labels[key])

    def _copy_diagnostic(self) -> None:
        if self._diagnostic is not None:
            QApplication.clipboard().setText(self._diagnostic.toPlainText())

    def _restore_details_focus(self) -> None:
        if self.isVisible():
            self.window().activateWindow()
            self.details.setFocus(Qt.FocusReason.OtherFocusReason)
