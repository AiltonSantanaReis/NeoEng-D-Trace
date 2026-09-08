"""Compact professional TileMap surface backed by the E04 core contract."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.tilemap_grids import GridKind, GridSpec
from src.core.tilemap_model import (
    TileDefinition,
    TileLayer,
    TileMapBounds,
    TileMapDocument,
    TileSet,
)
from src.core.tilemap_tools import TileEditTransaction, TileTool, erase_line, paint_line
from src.persistence.tilemap_io import load_tilemap, save_tilemap


def _default_tileset() -> TileSet:
    digest = hashlib.sha256(b"neoeng-e04-preview-atlas").hexdigest()
    return TileSet(
        id="default-terrain",
        atlas_asset_id="default-terrain-atlas",
        atlas_sha256=digest,
        tiles=(
            TileDefinition("grass", "default-terrain-atlas", (0, 0, 32, 32)),
            TileDefinition("water", "default-terrain-atlas", (32, 0, 32, 32)),
        ),
    )


def _default_document() -> TileMapDocument:
    return TileMapDocument(
        id="scenario-terrain",
        name="Scenario Terrain",
        tileset=_default_tileset(),
        grid=GridKind.ORTHOGONAL,
        layers=(TileLayer("ground", "Ground", 0),),
        chunk_size=64,
        bounds=TileMapBounds(-64, -64, 63, 63),
    )


class TileMapCanvas(QFrame):
    """Small interactive canvas that uses the same grid transform as picking."""

    cell_painted = Signal(tuple, tuple)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tilemap_authoring_canvas")
        self.setMinimumHeight(260)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.document: TileMapDocument | None = None
        self.grid_kind = GridKind.ORTHOGONAL
        self._last_cell: tuple[int, int] | None = None

    def set_document(self, document: TileMapDocument | None) -> None:
        self.document = document
        self.update()

    def set_grid_kind(self, kind: GridKind) -> None:
        self.grid_kind = kind
        self.update()

    def _spec(self) -> GridSpec:
        return GridSpec(
            self.grid_kind,
            32.0,
            32.0 if self.grid_kind != GridKind.ISOMETRIC else 24.0,
            -self.width() / 2.0,
            -self.height() / 2.0,
        )

    def _cell_at(self, point: QPoint) -> tuple[int, int]:
        return self._spec().world_to_cell((float(point.x()), float(point.y())))

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cell = self._cell_at(event.position().toPoint())
            self._last_cell = cell
            self.cell_painted.emit(cell, cell)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            cell = self._cell_at(event.position().toPoint())
            if cell != self._last_cell:
                start = self._last_cell or cell
                self._last_cell = cell
                self.cell_painted.emit(start, cell)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        self._last_cell = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101820"))
        spec = self._spec()
        painter.setPen(QPen(QColor("#253747"), 1))
        for x in range(0, self.width() + 1, 32):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + 1, 32):
            painter.drawLine(0, y, self.width(), y)
        if self.document is None:
            painter.setPen(QColor("#9aa9b5"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Crie um tilemap para começar",
            )
            return
        for _layer_id, coordinate, cell in self.document.iter_cells():
            center = spec.cell_to_world(coordinate)
            x = int(center[0] - 16)
            y = int(center[1] - 16)
            color = QColor("#3aa675") if cell.tile_id == "grass" else QColor("#2989b8")
            painter.fillRect(x, y, 31, 31, color)
            painter.setPen(QPen(QColor("#9bd7eb"), 1))
            painter.drawRect(x, y, 31, 31)


class TileMapAuthoringPanel(QWidget):
    """UI for the user-flow acceptance path of E04."""

    status_message = Signal(str)

    def __init__(
        self,
        project_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.project_root = project_root
        self.document: TileMapDocument | None = None
        self._undo: list[TileEditTransaction] = []
        self._redo: list[TileEditTransaction] = []
        self.current_lang = "en"
        self.title_label = QLabel(self)
        self.summary_label = QLabel(self)
        self.grid_combo = QComboBox(self)
        self.grid_combo.setObjectName("tilemap_grid_combo")
        for kind, label in (
            (GridKind.ORTHOGONAL, "Orthogonal"),
            (GridKind.ISOMETRIC, "Isometric"),
            (GridKind.HEXAGONAL, "Hexagonal"),
        ):
            self.grid_combo.addItem(label, kind.value)
        self.tile_combo = QComboBox(self)
        self.tile_combo.setObjectName("tilemap_tile_palette")
        self.tool_combo = QComboBox(self)
        self.tool_combo.setObjectName("tilemap_tool_combo")
        for tool, label in (
            (TileTool.PENCIL, "Pincel"),
            (TileTool.ERASER, "Borracha"),
        ):
            self.tool_combo.addItem(label, tool.value)
        self.new_button = QPushButton(self)
        self.open_button = QPushButton(self)
        self.save_button = QPushButton(self)
        self.undo_button = QPushButton(self)
        self.redo_button = QPushButton(self)
        self.canvas = TileMapCanvas(self)
        self.canvas.cell_painted.connect(self._paint_cells)
        self.grid_combo.currentIndexChanged.connect(self._grid_changed)
        self.new_button.clicked.connect(self.new_map)
        self.open_button.clicked.connect(self.open_map)
        self.save_button.clicked.connect(self.save_map)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self._build_layout()
        self.update_language("pt")

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.summary_label)
        layout.addLayout(header)
        controls = QHBoxLayout()
        controls.addWidget(self.grid_combo)
        controls.addWidget(self.tile_combo)
        controls.addWidget(self.tool_combo)
        layout.addLayout(controls)
        actions = QHBoxLayout()
        for button in (
            self.new_button,
            self.open_button,
            self.save_button,
            self.undo_button,
            self.redo_button,
        ):
            actions.addWidget(button)
        layout.addLayout(actions)
        layout.addWidget(self.canvas, 1)

    @property
    def map_path(self) -> Path:
        return self.project_root / "assets" / "tilemaps" / "scenario.tilemap.json"

    def _refresh_palette(self) -> None:
        self.tile_combo.clear()
        if self.document is not None:
            for tile in self.document.tileset.tiles:
                self.tile_combo.addItem(tile.id, tile.id)

    def _refresh_summary(self) -> None:
        if self.document is None:
            self.summary_label.setText(
                "Sem mapa" if self.current_lang == "pt" else "No map"
            )
        else:
            self.summary_label.setText(
                f"{self.document.grid} · "
                f"{self.document.populated_cell_count} células · "
                f"{self.document.populated_chunk_count} chunks"
            )
        self.undo_button.setEnabled(bool(self._undo))
        self.redo_button.setEnabled(bool(self._redo))

    def _grid_changed(self) -> None:
        value = self.grid_combo.currentData()
        if value is None:
            return
        kind = GridKind(value)
        if self.document is not None:
            self.document.grid = kind.value
        self.canvas.set_grid_kind(kind)
        self._refresh_summary()

    def _paint_cells(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        if self.document is None or not self.tile_combo.currentData():
            return
        layer_id = self.document.layers[0].id
        if self.tool_combo.currentData() == TileTool.ERASER.value:
            transaction = erase_line(self.document, layer_id, start, end)
        else:
            transaction = paint_line(
                self.document,
                layer_id,
                start,
                end,
                str(self.tile_combo.currentData()),
            )
        if transaction.deltas:
            self._undo.append(transaction)
            self._redo.clear()
            self._refresh_summary()
            self.canvas.update()
            self.status_message.emit("Tilemap edit applied")

    def new_map(self) -> None:
        self.document = _default_document()
        self._undo.clear()
        self._redo.clear()
        self.canvas.set_document(self.document)
        self._refresh_palette()
        self._refresh_summary()
        self.status_message.emit("Novo tilemap criado")

    def open_map(self) -> None:
        try:
            self.document = load_tilemap(self.map_path)
        except Exception as exc:
            self.status_message.emit(f"Tilemap open failed: {exc}")
            return
        self._undo.clear()
        self._redo.clear()
        self.grid_combo.setCurrentIndex(self.grid_combo.findData(self.document.grid))
        self.canvas.set_grid_kind(GridKind(self.document.grid))
        self.canvas.set_document(self.document)
        self._refresh_palette()
        self._refresh_summary()
        self.status_message.emit("Tilemap reaberto")

    def save_map(self) -> None:
        if self.document is None:
            self.status_message.emit("Crie um tilemap antes de salvar")
            return
        try:
            save_tilemap(self.document, self.map_path)
        except Exception as exc:
            self.status_message.emit(f"Tilemap save failed: {exc}")
            return
        self.status_message.emit(f"Tilemap salvo: {self.map_path.name}")

    def undo(self) -> None:
        if self._undo:
            transaction = self._undo.pop()
            transaction.undo()
            self._redo.append(transaction)
            self._refresh_summary()
            self.canvas.update()

    def redo(self) -> None:
        if self._redo:
            transaction = self._redo.pop()
            transaction.redo()
            self._undo.append(transaction)
            self._refresh_summary()
            self.canvas.update()

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.title_label.setText("Tilemap / Terreno")
            grid_labels = ("Ortogonal", "Isométrico", "Hexagonal")
            tool_labels = ("Pincel", "Borracha")
            self.new_button.setText("Novo")
            self.open_button.setText("Reabrir")
            self.save_button.setText("Salvar")
            self.undo_button.setText("Desfazer")
            self.redo_button.setText("Refazer")
        else:
            self.title_label.setText("Tilemap / Terrain")
            grid_labels = ("Orthogonal", "Isometric", "Hexagonal")
            tool_labels = ("Pencil", "Eraser")
            self.new_button.setText("New")
            self.open_button.setText("Reopen")
            self.save_button.setText("Save")
            self.undo_button.setText("Undo")
            self.redo_button.setText("Redo")
        for index, label in enumerate(grid_labels):
            self.grid_combo.setItemText(index, label)
        for index, label in enumerate(tool_labels):
            self.tool_combo.setItemText(index, label)
        self._refresh_summary()


__all__ = ["TileMapAuthoringPanel", "TileMapCanvas"]
