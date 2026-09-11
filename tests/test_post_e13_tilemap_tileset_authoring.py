from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from src.ui.tilemap_authoring_panel import TileMapAuthoringPanel
from src.ui.tileset_authoring_panel import TilesetAuthoringPanel


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _atlas(path: Path) -> Path:
    image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    image.paste((222, 76, 76, 255), (0, 0, 32, 32))
    image.paste((76, 180, 112, 255), (32, 0, 64, 32))
    image.save(path)
    return path


def test_tileset_panel_exposes_visual_atlas_selection_and_localized_labels(
    tmp_path: Path,
) -> None:
    _app()
    panel = TilesetAuthoringPanel(tmp_path)
    panel.atlas_path_edit.setText(str(_atlas(tmp_path / "terreno.png")))
    panel.width_spin.setValue(32)
    panel.height_spin.setValue(32)
    panel.generate_tileset()

    assert not panel.atlas_preview._image.isNull()
    assert panel.tiles_list.count() == 2
    assert panel.tiles_list.item(0).icon().isNull() is False
    assert panel.atlas_label.text() == "Atlas"
    assert panel.tile_width_label.text() == "Largura do tile"
    assert panel.spacing_label.text() == "Espaçamento"

    panel.atlas_preview.tile_selected.emit(1)
    assert panel.tiles_list.currentRow() == 1
    assert "tile_0001" in panel.selected_tile_label.text()


def test_tilemap_uses_saved_tileset_textures_and_supports_layers(
    tmp_path: Path,
) -> None:
    _app()
    atlas = _atlas(tmp_path / "terreno.png")
    tileset = TilesetAuthoringPanel(tmp_path)
    tileset.atlas_path_edit.setText(str(atlas))
    tileset.width_spin.setValue(32)
    tileset.height_spin.setValue(32)
    tileset.generate_tileset()
    tileset.save_current()

    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    assert panel.document is not None
    assert panel.document.tileset.id == "scenario-tileset"
    assert set(panel._tile_images) == {"tile_0000", "tile_0001"}
    assert panel.tile_palette.count() == 2
    assert panel.tile_palette.item(1).icon().isNull() is False

    panel.add_layer()
    assert panel.document.layers[-1].id == "layer_1"
    panel.layer_combo.setCurrentIndex(1)
    panel._paint_cells((12, 5), (13, 5))
    assert panel.document.populated_cell_count == 2
    panel.save_map()

    reopened = TileMapAuthoringPanel(tmp_path)
    reopened.open_map()
    assert reopened.document is not None
    assert [layer.id for layer in reopened.document.layers] == ["ground", "layer_1"]
    assert reopened.document.populated_cell_count == 2
    assert set(reopened._tile_images) == {"tile_0000", "tile_0001"}


def test_tilemap_canvas_renders_loaded_texture_instead_of_only_placeholder_color(
    tmp_path: Path,
) -> None:
    _app()
    atlas = _atlas(tmp_path / "terreno.png")
    tileset = TilesetAuthoringPanel(tmp_path)
    tileset.atlas_path_edit.setText(str(atlas))
    tileset.width_spin.setValue(32)
    tileset.height_spin.setValue(32)
    tileset.generate_tileset()
    tileset.save_current()

    panel = TileMapAuthoringPanel(tmp_path)
    panel.new_map()
    panel.canvas.resize(640, 320)
    panel._paint_cells((12, 5), (12, 5))
    panel.canvas.show()
    _app().processEvents()
    image = panel.canvas.grab().toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    matching = 0
    for x in range(image.width()):
        for y in range(image.height()):
            pixel = image.pixelColor(x, y)
            if pixel.red() > 180 and pixel.green() < 120 and pixel.blue() < 120:
                matching += 1
    assert matching > 100
