"""Regression gates for Portuguese hover and accessibility metadata."""

from __future__ import annotations

import sys

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget

from scripts.audit_ui_capture import AuditConfig
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.scenario_editor_window import ScenarioEditorWindow


ENGLISH_LEAK_MARKERS = (
    "Open an image",
    "Select objects",
    "Rectangle selection",
    "Ellipse selection",
    "Lasso tool",
    "Polygonal lasso",
    "Magnetic lasso",
    "Pen tool",
    "Edit polygon vertices",
    "Paint collision geometry",
    "Validate collision geometry",
    "Move viewport",
    "Zoom viewport",
    "Fit viewport",
    "Focus selected object",
    "Choose viewport rendering mode",
    "Choose viewport zoom",
    "Toggle real vertex snapping",
    "Run collision detection",
    "Export collision results",
    "Choose the collider",
    "Generate collision shapes",
    "Filter layers by name",
    "Activate ",
    "Select an object to inspect",
    "Filter scene objects",
    "Open the scenario editor",
    "Preview Parallax",
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication(sys.argv)


def _visible_feedback(root: QWidget) -> list[str]:
    values: list[str] = []
    for widget in [root, *root.findChildren(QWidget)]:
        if widget is not root and not widget.isVisibleTo(root):
            continue
        values.extend(value for value in (widget.toolTip(), widget.accessibleDescription()) if value)
    for action in root.findChildren(QAction):
        if action.isVisible():
            values.extend(value for value in (action.toolTip(), action.statusTip()) if value)
    return values


def _assert_no_english_leaks(values: list[str]) -> None:
    leaks = [
        value
        for value in values
        if any(marker.casefold() in value.casefold() for marker in ENGLISH_LEAK_MARKERS)
    ]
    assert not leaks, "Portuguese hover metadata still contains English: " + repr(leaks)


def test_main_window_portuguese_hover_metadata(qt_app):
    window = MainWindow(Scene(), AuditConfig())
    window.show()
    qt_app.processEvents()
    try:
        window.set_language("pt")
        qt_app.processEvents()
        _assert_no_english_leaks(_visible_feedback(window))
        assert "Laço magnético" in window.tool_palette.btn_magnetic_lasso.toolTip()
        assert "colisão" in window.collision_panel.batch_test_btn.toolTip()
    finally:
        window.close()


def test_scenario_editor_portuguese_hover_metadata(qt_app):
    scene = Scene()
    window = ScenarioEditorWindow(ScenarioAuthoringState(scene), scene, language="en")
    window.show()
    qt_app.processEvents()
    try:
        assert window._new_professional()
        window.update_language("pt")
        qt_app.processEvents()
        _assert_no_english_leaks(_visible_feedback(window))
        assert "Aplicar" in window.professional_inspector.apply_button.text()
        assert "Posição" in window.professional_inspector._field_labels["position_x"].text()
        assert window.vector_contour_panel.source_label.text().startswith("Selecione")
        assert window.vector_contour_panel.undo_button.text() == "Desfazer"
        assert "Autoria" in window.status_label.text()
    finally:
        window.close()
