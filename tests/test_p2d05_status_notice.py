"""Real Qt regressions for P2D-05 language, readable errors and safe details."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from src.core.commands import CommandManager
from src.core.config import ConfigManager
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView, ToolInterface
from src.ui.error_presentation import show_p2d05_error
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS


@pytest.fixture
def window(tmp_path):
    app = QApplication.instance() or QApplication([])
    original_font, original_style = app.font(), app.styleSheet()
    # Windows offscreen can start without a font database. Load a real system
    # font explicitly for layout assertions, not a product/font-discovery fix.
    if not QFontDatabase.families():
        for name in ("arial.ttf", "arialbd.ttf", "segoeui.ttf", "segoeuib.ttf"):
            font = Path(os.environ["WINDIR"]) / "Fonts" / name
            assert QFontDatabase.addApplicationFont(str(font)) >= 0
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    app.setStyleSheet(QSS)
    scene = Scene()
    scene.cmd = CommandManager()
    result = MainWindow(scene, ConfigManager(str(tmp_path / "config.json")))
    result.resize(1280, 720)
    result.show()
    scene.load_image(np.zeros((480, 640, 3), dtype=np.uint8), "test-input.png")
    result._refresh_document_views(project_loaded=False)
    app.processEvents()
    try:
        yield result
    finally:
        result._mark_document_clean()
        result.close()
        result.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        app.setStyleSheet(original_style)
        app.setFont(original_font)


def _click(window, x, y):
    QTest.mouseClick(
        window.canvas,
        Qt.MouseButton.LeftButton,
        pos=window.canvas.image_to_widget(x, y).toPoint(),
    )
    QApplication.processEvents()


def _tool(window):
    return window.canvas._tool.on_mouse_press.__self__


@pytest.mark.parametrize("language", ["pt", "en"])
def test_new_pen_inherits_active_language_and_preserves_rejected_path(window, language):
    getattr(window, "act_portuguese" if language == "pt" else "act_english").trigger()
    QTest.mouseClick(window.tool_palette.btn_pen, Qt.MouseButton.LeftButton)
    tool = _tool(window)
    assert tool.current_lang == language
    for point in ((100, 100), (200, 100), (300, 100)):
        _click(window, *point)
    before = [(node.anchor, node.handle_in, node.handle_out) for node in tool._nodes]
    _click(window, 100, 100)
    assert [(n.anchor, n.handle_in, n.handle_out) for n in tool._nodes] == before
    assert window.canvas.model.objects == {}
    assert window.canvas.model.cmd.undo_count == 0
    assert "P2D05-OPERATION" in window.statusBar().currentMessage()
    expected = (
        "A operação foi rejeitada" if language == "pt" else "The operation was rejected"
    )
    assert expected in window.statusBar().currentMessage()
    assert QApplication.activeModalWidget() is None


def test_canvas_language_callback_and_adapter_without_callback(window):
    canvas = CanvasView(Scene())
    calls = []
    canvas.update_language("pt")
    canvas.set_tool(ToolInterface(update_language=calls.append))
    assert calls == ["pt"]
    canvas.set_tool(ToolInterface())
    canvas.set_tool(None)
    canvas.deleteLater()


def test_visible_notice_reflows_on_resize_without_clipping_or_losing_details(window):
    show_p2d05_error(
        window,
        ValueError("geometry rejected"),
        operation="edit",
        language="pt",
        channel="status",
    )
    notice = window.statusBar().findChild(QWidget, "p2d05_status_notice")
    label = notice.findChild(QLabel, "p2d05_status_message")
    for size in ((1920, 1080), (1280, 720), (1366, 768), (1280, 720)):
        window.resize(*size)
        QApplication.processEvents()
        assert (window.width(), window.height()) == size
        assert notice.isVisible()
        assert label.height() >= label.heightForWidth(label.width())
        assert window.statusBar().height() <= 96
        for name in ("p2d05_status_details", "p2d05_status_dismiss"):
            button = notice.findChild(QPushButton, name)
            assert button.isVisible() and notice.rect().contains(button.geometry())


@pytest.mark.parametrize("size", [(1280, 720), (1366, 768), (1920, 1080)])
@pytest.mark.parametrize("language", ["pt", "en"])
def test_status_text_wraps_and_details_are_explicit_safe_and_keyboard_accessible(
    window, size, language
):
    window.resize(*size)
    presentation = show_p2d05_error(
        window.canvas,
        ValueError(r"Invalid geometry at C:\Private\user\secret.json token=top-secret"),
        operation="edit",
        language=language,
        channel="status",
    )
    QApplication.processEvents()
    notice = window.statusBar().findChild(QWidget, "p2d05_status_notice")
    assert notice is not None and notice.isVisible()
    label = notice.findChild(QLabel, "p2d05_status_message")
    assert label.wordWrap()
    assert label.textFormat() == Qt.TextFormat.PlainText
    assert presentation.action in label.text()
    assert presentation.preserved_state in label.text()
    assert presentation.safe_detail not in label.text()
    assert label.height() >= label.heightForWidth(label.width())
    # Readability must not consume the canvas through a pathological size hint.
    assert window.statusBar().height() <= 96
    assert (window.width(), window.height()) == size
    assert QApplication.activeModalWidget() is None
    assert not notice.findChildren(QDialog)
    details = notice.findChild(QPushButton, "p2d05_status_details")
    assert details.isVisible() and details.accessibleName()
    details.setFocus()
    QTest.keyClick(details, Qt.Key.Key_Space)
    QApplication.processEvents()
    dialog = notice.findChild(QDialog, "p2d05_status_details_dialog")
    assert dialog is not None and dialog.isVisible()
    assert not dialog.isModal()
    text = dialog.findChild(QPlainTextEdit, "p2d05_safe_diagnostic")
    assert text.isReadOnly()
    assert presentation.message in text.toPlainText()
    assert presentation.detailed_text in text.toPlainText()
    assert "top-secret" not in text.toPlainText()
    assert r"C:\Private" not in text.toPlainText()
    copy = dialog.findChild(QPushButton, "p2d05_copy_diagnostic")
    QTest.mouseClick(copy, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == text.toPlainText()
    QTest.keyClick(dialog, Qt.Key.Key_Escape)
    QApplication.processEvents()
    assert not dialog.isVisible()
    assert notice.isVisible()
    assert details.hasFocus()
    assert window.canvas.model.objects == {}
    assert window.canvas.model.cmd.undo_count == 0


def test_status_reuses_notice_replaces_details_and_dismisses_explicitly(window):
    first = show_p2d05_error(
        window, ValueError("first"), operation="edit", channel="status"
    )
    notice = window.statusBar().findChild(QWidget, "p2d05_status_notice")
    assert notice is not None
    second = show_p2d05_error(
        window, ValueError("second"), operation="edit", channel="status"
    )
    QApplication.processEvents()
    assert len(window.statusBar().findChildren(QWidget, "p2d05_status_notice")) == 1
    assert window.statusBar().currentMessage() == second.message != first.message
    details = notice.findChild(QPushButton, "p2d05_status_details")
    QTest.mouseClick(details, Qt.MouseButton.LeftButton)
    dialog = notice.findChild(QDialog, "p2d05_status_details_dialog")
    text = dialog.findChild(QPlainTextEdit, "p2d05_safe_diagnostic").toPlainText()
    assert "second" in text and "first" not in text
    dialog.close()
    dismiss = notice.findChild(QPushButton, "p2d05_status_dismiss")
    dismiss.setFocus()
    QTest.keyClick(dismiss, Qt.Key.Key_Space)
    QApplication.processEvents()
    assert not notice.isVisible()
    assert window.statusBar().currentMessage() == ""


def test_pen_returns_to_valid_drawing_and_keyboard_history_after_error(window):
    window.act_portuguese.trigger()
    QTest.mouseClick(window.tool_palette.btn_pen, Qt.MouseButton.LeftButton)
    for point in ((100, 100), (200, 100), (300, 100), (100, 100)):
        _click(window, *point)
    notice = window.statusBar().findChild(QWidget, "p2d05_status_notice")
    assert notice is not None and notice.isVisible()
    QTest.mouseClick(
        notice.findChild(QPushButton, "p2d05_status_dismiss"),
        Qt.MouseButton.LeftButton,
    )
    assert window.canvas.hasFocus()
    # Switching tools explicitly cancels the uncommitted path; no node edits.
    QTest.mouseClick(window.tool_palette.btn_rect, Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.tool_palette.btn_pen, Qt.MouseButton.LeftButton)
    assert _tool(window).current_lang == "pt"
    for point in ((100, 100), (300, 100), (300, 250), (100, 100)):
        _click(window, *point)
    scene = window.canvas.model
    assert len(scene.objects) == 1 and scene.cmd.undo_count == 1
    original = next(iter(scene.objects.values()))
    polygon, beziers = list(original.polygon), list(original.beziers)
    QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    assert not scene.objects and scene.cmd.redo_count == 1
    QTest.keyClick(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    QApplication.processEvents()
    restored = next(iter(scene.objects.values()))
    assert restored.polygon == polygon and restored.beziers == beziers
    assert scene.cmd.undo_count == 1 and scene.cmd.redo_count == 0


def test_open_details_updates_without_duplicates_and_closes_on_replacement(window):
    show_p2d05_error(window, ValueError("first"), operation="edit", channel="status")
    notice = window.statusBar().findChild(QWidget, "p2d05_status_notice")
    details = notice.findChild(QPushButton, "p2d05_status_details")
    QTest.mouseClick(details, Qt.MouseButton.LeftButton)
    dialog = notice.findChild(QDialog, "p2d05_status_details_dialog")
    assert dialog.isVisible()
    show_p2d05_error(
        window, ValueError("second"), operation="edit", language="pt", channel="status"
    )
    assert dialog.windowTitle() == "Detalhes seguros do erro"
    assert "second" in dialog.findChild(QPlainTextEdit).toPlainText()
    QTest.mouseClick(details, Qt.MouseButton.LeftButton)
    assert len(notice.findChildren(QDialog)) == 1
    QTest.keyClick(dialog, Qt.Key.Key_Return)
    assert not dialog.isVisible()
    QTest.mouseClick(details, Qt.MouseButton.LeftButton)
    window.statusBar().clearMessage()
    assert not dialog.isVisible() and not notice.isVisible()
    assert window.statusBar().currentMessage() == ""
    show_p2d05_error(window, ValueError("third"), operation="edit", channel="status")
    assert notice.isVisible()
    window.statusBar().showMessage("Confirmed subsequent state")
    assert not notice.isVisible()


def test_notice_does_not_retain_a_destroyed_error_origin(window):
    origin = QWidget(window)
    origin.show()
    show_p2d05_error(origin, ValueError("first"), operation="edit", channel="status")
    notice = window.statusBar().findChild(QWidget, "p2d05_status_notice")
    assert notice is not None
    # Replacing the origin must disconnect the old destruction callback.
    show_p2d05_error(
        window.canvas, ValueError("second"), operation="edit", channel="status"
    )
    origin.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert notice._origin is window.canvas
    replacement = QWidget(window)
    replacement.show()
    show_p2d05_error(
        replacement, ValueError("third"), operation="edit", channel="status"
    )
    replacement.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert notice._origin is None
    QTest.mouseClick(
        notice.findChild(QPushButton, "p2d05_status_dismiss"), Qt.MouseButton.LeftButton
    )
    assert not notice.isVisible()
