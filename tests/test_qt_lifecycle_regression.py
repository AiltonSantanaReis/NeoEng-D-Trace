"""Regression coverage for Qt callback ownership during widget teardown."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication, QToolButton, QWidget

from src.models.scene import Scene
from src.ui.canvas_view import CanvasView
from src.ui.mask_viewer import MaskViewer
from src.ui.reference_chrome import ReferenceToolPalette
from src.ui.responsive_layout import ResponsivePanelLayout


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _flush_deferred_deletes(app: QApplication) -> None:
    app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def test_reference_menu_position_timer_is_owned_by_toolbar(qt_app):
    owner = QWidget()
    palette = ReferenceToolPalette("test", owner)
    button = QToolButton(palette)
    palette.register_application_menu(button)

    assert palette._application_menu_timer.parent() is palette
    assert palette._application_menu_timer.isSingleShot()

    palette.deleteLater()
    _flush_deferred_deletes(qt_app)
    owner.deleteLater()
    _flush_deferred_deletes(qt_app)


def test_responsive_geometry_timer_is_owned_by_window(qt_app):
    owner = QWidget()
    layout = ResponsivePanelLayout(
        owner,
        main_splitter=None,
        panel_stack=None,
        compact_panel_tabs=None,
        reference_panel_tabs=None,
        reference_tool_palette=None,
        desktop_panel_splitter=None,
        right_splitter=None,
        side_panel=None,
        layers=None,
        groups=None,
        collision_panel=None,
    )

    assert layout._geometry_update_timer.parent() is owner
    assert layout._geometry_update_timer.isSingleShot()

    owner.deleteLater()
    _flush_deferred_deletes(qt_app)


def test_mask_viewer_fit_timer_is_owned_by_viewer(qt_app):
    viewer = MaskViewer()

    assert viewer._fit_timer.parent() is viewer
    assert viewer._fit_timer.isSingleShot()

    viewer.deleteLater()
    _flush_deferred_deletes(qt_app)


def test_canvas_flash_timer_is_owned_by_canvas(qt_app):
    canvas = CanvasView(Scene())

    assert canvas._flash_timer.parent() is canvas
    assert canvas._flash_timer.isSingleShot()

    canvas.deleteLater()
    _flush_deferred_deletes(qt_app)
