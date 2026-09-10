from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from src.ui.tileset_authoring_panel import TilesetAuthoringPanel


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_tileset_panel_generates_saves_and_reopens_tileset(
    qt_app: QApplication, tmp_path: Path
) -> None:
    atlas = tmp_path / "atlas.png"
    Image.new("RGBA", (32, 16), (64, 160, 96, 255)).save(atlas)
    panel = TilesetAuthoringPanel(tmp_path)
    panel.atlas_path_edit.setText(str(atlas))
    panel.width_spin.setValue(16)
    panel.height_spin.setValue(16)
    panel.generate_tileset()
    assert panel.prepared is not None
    assert len(panel.prepared["tiles"]) == 2
    panel.save_current()
    assert panel.manifest_path.is_file()
    panel.new_tileset()
    panel.open_tileset()
    assert panel.tiles_list.count() == 2
    assert "Tileset reaberto" in panel.status_label.text()


def test_tileset_panel_reports_missing_atlas_in_portuguese(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = TilesetAuthoringPanel(tmp_path)
    panel.atlas_path_edit.setText(str(tmp_path / "missing.png"))
    panel.generate_tileset()
    assert "Atlas não encontrado" in panel.status_label.text()
    assert panel.title_label.text() == "Tileset / Atlas"
