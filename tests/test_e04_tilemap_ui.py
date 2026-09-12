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
    assert panel.rule_neighbor_combo.itemText(0) == "<vazio>"
    assert panel.document is not None
    assert panel.document.populated_cell_count == 3
    assert len(panel._undo) == 1

    panel.undo()
    assert panel.document.populated_cell_count == 0
    assert len(panel._redo) == 1

    panel.redo()
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
    ] == ["Pincel", "Borracha", "Retângulo", "Balde", "Conta-gotas", "Seleção"]

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
    assert panel.rule_neighbor_combo.itemText(0) == "<empty>"
    assert [
        panel.tool_combo.itemText(index) for index in range(panel.tool_combo.count())
    ] == ["Pencil", "Eraser", "Rectangle", "Bucket", "Picker", "Select"]


def test_tilemap_selection_copy_paste_variation_rules_and_persistence(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    assert panel.document is not None

    panel.tile_combo.setCurrentIndex(0)
    panel.tool_combo.setCurrentIndex(
        panel.tool_combo.findData(TileTool.RECTANGLE.value)
    )
    panel._finish_gesture((0, 0), (1, 1))
    panel.tool_combo.setCurrentIndex(panel.tool_combo.findData(TileTool.SELECT.value))
    panel._finish_gesture((0, 0), (1, 1))
    assert panel._selection == ((0, 0), (1, 1))
    panel.copy_selection()
    assert panel._clipboard is not None
    assert panel.paste_button.isEnabled()

    panel._finish_gesture((3, 3), (4, 4))
    panel.paste_selection()
    assert panel.document.get_cell("ground", (3, 3)).tile_id == "grass"
    assert panel.document.get_cell("ground", (4, 4)).tile_id == "grass"

    panel.tile_palette.item(0).setSelected(True)
    panel.tile_palette.item(1).setSelected(True)
    panel.variation_seed_spin.setValue(7)
    panel._finish_gesture((6, 6), (7, 7))
    panel.apply_variation()
    assert all(
        panel.document.get_cell("ground", coordinate) is not None
        for coordinate in ((6, 6), (6, 7), (7, 6), (7, 7))
    )

    panel.rule_target_combo.setCurrentIndex(panel.rule_target_combo.findData("water"))
    panel.rule_neighbor_combo.setCurrentIndex(0)
    panel.add_rule()
    assert panel._rules
    panel.rule_fallback_combo.setCurrentIndex(panel.rule_fallback_combo.findData("grass"))
    panel.apply_rules()
    assert panel.document.rule_set_payload is not None
    panel.save_map()

    reopened = TileMapAuthoringPanel(tmp_path)
    reopened.open_map()
    assert reopened.document is not None
    assert reopened.document.rule_set_payload == panel.document.rule_set_payload
    assert len(reopened._rules) == 1
    assert reopened.rules_list.count() == 1
    assert reopened.rules_group.title() == "Autotiling / Rule Tiles"
    reopened.update_language("en")
    assert reopened.copy_button.text() == "Copy"
    assert reopened.rules_group.title() == "Autotiling / Rule Tiles"


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


def test_tilemap_drag_is_one_undoable_gesture(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    panel.canvas.resize(320, 240)
    panel.canvas.show()
    qt_app.processEvents()

    start_point = QPoint(120, 100)
    end_point = QPoint(184, 100)
    QTest.mousePress(panel.canvas, Qt.MouseButton.LeftButton, pos=start_point)
    QTest.mouseMove(panel.canvas, end_point, 20)
    QTest.mouseRelease(panel.canvas, Qt.MouseButton.LeftButton, pos=end_point)

    assert panel.document is not None
    assert panel.document.populated_cell_count == 3


def test_tilemap_actions_fit_narrow_professional_inspector(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TileMapAuthoringPanel(tmp_path)
    panel.resize(520, 900)
    panel.show()
    qt_app.processEvents()

    for widget in (
        panel.new_button,
        panel.open_button,
        panel.save_button,
        panel.reload_tileset_button,
        panel.undo_button,
        panel.redo_button,
        panel.add_layer_button,
    ):
        assert widget.isVisible()
        assert widget.geometry().right() <= panel.width()


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
