from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.scenario_collider_panel import ScenarioColliderPanel


@pytest.fixture
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_collider_panel_creates_saves_reopens_and_undoes_in_portuguese(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = ScenarioColliderPanel(tmp_path)
    panel.create_collider()
    panel.save_document()
    assert panel.document_path.is_file()
    assert panel.document is not None
    assert len(panel.document.colliders) == 1
    panel.document = None
    panel.history = None
    panel.open_document()
    assert panel.document is not None
    assert panel.title_label.text() == "Colisores / Física"
    panel.create_collider()
    panel.undo()
    assert len(panel.document.colliders) == 1
    panel.redo()
    assert len(panel.document.colliders) == 2


def test_collider_panel_switches_language_and_removes_selection(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = ScenarioColliderPanel(tmp_path)
    panel.create_collider()
    panel.collider_list.setCurrentRow(0)
    panel.remove_selected()
    assert panel.document is not None
    assert panel.document.colliders == {}
    panel.update_language("en")
    assert panel.title_label.text() == "Colliders / Physics"
    assert panel.new_button.text() == "Create"
