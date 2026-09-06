"""Shared pytest bootstrap for deterministic headless Qt tests."""

import os

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def isolate_residual_qt_modal():
    """Keep modal dialogs from one Qt test from affecting the next test."""

    app = QApplication.instance()
    if app is not None:
        modal = app.activeModalWidget()
        if modal is not None:
            modal.close()
            modal.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
        assert app.activeModalWidget() is None
    yield
