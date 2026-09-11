"""Shared pytest bootstrap for deterministic headless Qt tests."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def _destroy_orphaned_qt_windows():
    """Keep native top-level windows isolated between behavioral tests.

    Closing a ``QMainWindow`` only hides it when its close handler ignores the
    event (the scenario editor intentionally does this so the product can
    reopen the same editor).  Tests that construct those windows standalone
    must still release them before the next test; otherwise Qt keeps their
    native popup/window resources and a later event dispatch can abort the
    process instead of raising a Python exception.

    Only widgets without a QWidget parent are collected.  Menus, frames and
    controls owned by a live window are left to their real QObject owner.
    """

    yield

    app = QApplication.instance()
    if app is None:
        return

    for widget in tuple(app.topLevelWidgets()):
        if widget.parentWidget() is not None:
            continue
        widget.hide()
        widget.deleteLater()

    # DeferredDelete can enqueue child cleanup while a root window is being
    # destroyed.  Drain two bounded passes without turning the fixture into a
    # blocking wait or changing the behavior under test.
    for _ in range(2):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
