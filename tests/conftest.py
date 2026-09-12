"""Shared pytest bootstrap for deterministic headless Qt tests."""

import os

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def isolate_qt_windows_and_modals():
    """Keep modal dialogs and native top-level windows isolated between tests."""

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

    app = QApplication.instance()
    if app is None:
        return

    # Closing a QMainWindow can only hide it when its close handler ignores the
    # event. The scenario editor intentionally does that so the product can
    # reopen the same editor. Standalone tests still need deterministic native
    # window cleanup before the next event dispatch.
    for widget in tuple(app.topLevelWidgets()):
        if widget.parentWidget() is not None:
            continue
        widget.hide()
        widget.deleteLater()

    # DeferredDelete can enqueue child cleanup while a root window is being
    # destroyed. Drain two bounded passes without blocking or changing the
    # behavior under test.
    for _ in range(2):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
