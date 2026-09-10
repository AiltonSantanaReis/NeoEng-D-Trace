from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.tilemap_authoring_panel import TileMapAuthoringPanel


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_tilemap_panel_exposes_ptbr_flow_and_persists_user_edits(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    panel._paint_cells((0, 0), (2, 0))
    assert panel.title_label.text() == "Tilemap / Terreno"
    assert panel.document is not None
    assert panel.document.populated_cell_count == 3
    panel.save_map()
    assert panel.map_path.is_file()
    panel.document = None
    panel.open_map()
    assert panel.document is not None
    assert panel.document.populated_cell_count == 3
    assert panel.canvas.objectName() == "tilemap_authoring_canvas"


def test_tilemap_panel_undo_redo_and_grid_switch_are_observable(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    panel._paint_cells((0, 0), (0, 0))
    panel.undo()
    assert panel.document is not None
    assert panel.document.populated_cell_count == 0
    panel.redo()
    assert panel.document.populated_cell_count == 1
    panel.grid_combo.setCurrentIndex(1)
    assert panel.document.grid == "isometric"


def test_tilemap_panel_localizes_status_messages(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    messages: list[str] = []
    panel.status_message.connect(messages.append)

    panel.new_map()
    panel._paint_cells((0, 0), (0, 0))
    panel.save_map()
    panel.document = None
    panel.open_map()

    assert messages == [
        "Novo tilemap criado",
        "Edição do tilemap aplicada",
        "Tilemap salvo: scenario.tilemap.json",
        "Tilemap reaberto",
    ]

    panel.update_language("en")
    panel.new_map()
    panel._paint_cells((0, 0), (0, 0))
    panel.save_map()

    assert messages[-3:] == [
        "New tilemap created",
        "Tilemap edit applied",
        "Tilemap saved: scenario.tilemap.json",
    ]
