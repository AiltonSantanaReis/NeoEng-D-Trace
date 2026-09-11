from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.tilemap_model import TileMapBounds
from src.core.tilemap_tools import TileTool, rectangle_cells
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


def test_tilemap_panel_exposes_advanced_tools_and_real_gestures(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    panel.canvas.resize(320, 240)
    panel.canvas.show()
    qt_app.processEvents()

    assert [
        panel.tool_combo.itemData(index) for index in range(panel.tool_combo.count())
    ] == [tool.value for tool in TileTool]
    assert [
        panel.tool_combo.itemText(index) for index in range(panel.tool_combo.count())
    ] == ["Pincel", "Borracha", "Retângulo", "Balde", "Conta-gotas"]

    panel.tool_combo.setCurrentIndex(
        panel.tool_combo.findData(TileTool.RECTANGLE.value)
    )
    panel.tile_combo.setCurrentIndex(1)
    start_point = QPoint(150, 100)
    end_point = QPoint(190, 140)
    start_cell = panel.canvas._cell_at(start_point)
    end_cell = panel.canvas._cell_at(end_point)
    QTest.mousePress(panel.canvas, Qt.MouseButton.LeftButton, pos=start_point)
    QTest.mouseMove(panel.canvas, end_point, 20)
    QTest.mouseRelease(panel.canvas, Qt.MouseButton.LeftButton, pos=end_point)

    assert panel.document is not None
    assert panel.document.populated_cell_count == len(
        rectangle_cells(start_cell, end_cell)
    )
    assert panel.document.get_cell("ground", start_cell) is not None

    panel.update_language("en")
    assert [
        panel.tool_combo.itemText(index) for index in range(panel.tool_combo.count())
    ] == ["Pencil", "Eraser", "Rectangle", "Bucket", "Picker"]


def test_tilemap_advanced_tools_are_transactional_and_picker_selects_tile(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    assert panel.document is not None
    panel.document.bounds = TileMapBounds(-1, -1, 1, 1)

    panel.tile_combo.setCurrentIndex(1)
    panel.tool_combo.setCurrentIndex(
        panel.tool_combo.findData(TileTool.RECTANGLE.value)
    )
    panel._finish_gesture((0, 0), (1, 1))
    assert panel.document.populated_cell_count == 4
    assert panel.document.get_cell("ground", (1, 1)).tile_id == "water"

    panel.undo()
    assert panel.document.populated_cell_count == 0
    panel.redo()
    assert panel.document.populated_cell_count == 4

    panel.tile_combo.setCurrentIndex(0)
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(TileTool.PICKER.value))
    panel._finish_gesture((1, 1), (1, 1))
    assert panel.tile_combo.currentData() == "water"

    panel.tile_combo.setCurrentIndex(0)
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(TileTool.BUCKET.value))
    panel._finish_gesture((-1, -1), (-1, -1))
    assert panel.document.populated_cell_count == 9
    assert panel.document.get_cell("ground", (-1, -1)).tile_id == "grass"


def test_tilemap_advanced_tools_preserve_locked_layer_failure(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    assert panel.document is not None
    panel.document.set_layer_lock("ground", True)
    messages: list[str] = []
    panel.status_message.connect(messages.append)
    panel.tool_combo.setCurrentIndex(
        panel.tool_combo.findData(TileTool.RECTANGLE.value)
    )
    panel._finish_gesture((0, 0), (1, 1))
    assert panel.document.populated_cell_count == 0
    assert messages[-1].startswith("Edição não aplicada: layer is locked")


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
