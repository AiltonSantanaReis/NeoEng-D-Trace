"""Compact professional TileMap surface backed by the E04 core contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
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
from src.core.tilemap_tools import (
    TileEditTransaction,
    TileTool,
    bucket_fill,
    erase_line,
    paint_line,
    paint_rectangle,
)
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


def _default_document(tileset: TileSet | None = None) -> TileMapDocument:
    return TileMapDocument(
        id="scenario-terrain",
        name="Scenario Terrain",
        tileset=tileset or _default_tileset(),
        grid=GridKind.ORTHOGONAL,
        layers=(TileLayer("ground", "Ground", 0),),
        chunk_size=64,
        bounds=TileMapBounds(-64, -64, 63, 63),
    )


class TileMapCanvas(QFrame):
    """Small interactive canvas that uses the same grid transform as picking."""

    gesture_started = Signal(tuple)
    cell_painted = Signal(tuple, tuple)
    gesture_finished = Signal(tuple, tuple)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tilemap_authoring_canvas")
        self.setMinimumHeight(260)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.document: TileMapDocument | None = None
        self.grid_kind = GridKind.ORTHOGONAL
        self._last_cell: tuple[int, int] | None = None
        self._drag_start: tuple[int, int] | None = None
        self._tile_images: dict[str, QImage] = {}
        self.active_layer_id: str | None = None

    def set_document(self, document: TileMapDocument | None) -> None:
        self.document = document
        self.update()

    def set_grid_kind(self, kind: GridKind) -> None:
        self.grid_kind = kind
        self.update()

    def set_tile_images(self, images: dict[str, QImage]) -> None:
        self._tile_images = dict(images)
        self.update()

    def set_active_layer(self, layer_id: str | None) -> None:
        self.active_layer_id = layer_id
        self.update()

    def _spec(self) -> GridSpec:
        return GridSpec(
            self.grid_kind,
            32.0,
            32.0 if self.grid_kind != GridKind.ISOMETRIC else 24.0,
            -self.width() / 2.0,
            -self.height() / 2.0,
        )

    def grid_spec(self) -> GridSpec:
        """Return the exact grid transform used by pointer picking."""

        return self._spec()

    def _cell_at(self, point: QPoint) -> tuple[int, int]:
        return self._spec().world_to_cell((float(point.x()), float(point.y())))

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cell = self._cell_at(event.position().toPoint())
            self._drag_start = cell
            self._last_cell = cell
            self.gesture_started.emit(cell)
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
        if event.button() == Qt.MouseButton.LeftButton:
            cell = self._cell_at(event.position().toPoint())
            start = self._drag_start or cell
            self.gesture_finished.emit(start, cell)
            self._drag_start = None
        self._last_cell = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101820"))
        spec = self._spec()
        self._draw_grid(painter, spec)
        if self.document is None:
            painter.setPen(QColor("#9aa9b5"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Crie um tilemap para começar",
            )
            return
        for layer_id, coordinate, cell in self.document.iter_cells():
            if not self.document.layer(layer_id).visible:
                continue
            center = spec.cell_to_world(coordinate)
            shape = self._cell_shape(spec, center)
            image = self._tile_images.get(cell.tile_id)
            if image is not None and not image.isNull():
                bounds = shape.boundingRect()
                painter.drawImage(bounds, image)
            else:
                color = (
                    QColor("#3aa675")
                    if cell.tile_id in {"grass", "default"}
                    else QColor("#2989b8")
                )
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(shape)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#9bd7eb"), 1))
            painter.drawPolygon(shape)

    def _cell_shape(self, spec: GridSpec, center: tuple[float, float]) -> QPolygonF:
        cx, cy = center
        if spec.kind == GridKind.ISOMETRIC:
            half_w = spec.cell_width / 2.0
            half_h = spec.cell_height / 2.0
            return QPolygonF(
                [
                    QPoint(int(cx), int(cy - half_h)),
                    QPoint(int(cx + half_w), int(cy)),
                    QPoint(int(cx), int(cy + half_h)),
                    QPoint(int(cx - half_w), int(cy)),
                ]
            )
        if spec.kind == GridKind.HEXAGONAL:
            radius_x = spec.cell_width / 2.0
            radius_y = spec.cell_height / 2.0
            return QPolygonF(
                [
                    QPoint(int(cx - radius_x * 0.5), int(cy - radius_y)),
                    QPoint(int(cx + radius_x * 0.5), int(cy - radius_y)),
                    QPoint(int(cx + radius_x), int(cy)),
                    QPoint(int(cx + radius_x * 0.5), int(cy + radius_y)),
                    QPoint(int(cx - radius_x * 0.5), int(cy + radius_y)),
                    QPoint(int(cx - radius_x), int(cy)),
                ]
            )
        return QPolygonF(
            [
                QPoint(int(cx - spec.cell_width / 2), int(cy - spec.cell_height / 2)),
                QPoint(int(cx + spec.cell_width / 2), int(cy - spec.cell_height / 2)),
                QPoint(int(cx + spec.cell_width / 2), int(cy + spec.cell_height / 2)),
                QPoint(int(cx - spec.cell_width / 2), int(cy + spec.cell_height / 2)),
            ]
        )

    def _draw_grid(self, painter: QPainter, spec: GridSpec) -> None:
        painter.setPen(QPen(QColor("#253747"), 1))
        if spec.kind == GridKind.ORTHOGONAL:
            for x in range(0, self.width() + 1, int(spec.cell_width)):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height() + 1, int(spec.cell_height)):
                painter.drawLine(0, y, self.width(), y)
            return
        for row in range(-40, 41):
            for column in range(-40, 41):
                center = spec.cell_to_world((column, row))
                shape = self._cell_shape(spec, center)
                if shape.boundingRect().intersects(QRectF(self.rect())):
                    painter.drawPolygon(shape)


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
        self._active_gesture_transactions: list[TileEditTransaction] | None = None
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
        self.tile_palette = QListWidget(self)
        self.tile_palette.setObjectName("tilemap_tile_palette_preview")
        self.tile_palette.setViewMode(QListWidget.ViewMode.IconMode)
        self.tile_palette.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.tile_palette.setMovement(QListWidget.Movement.Static)
        self.tile_palette.setWrapping(True)
        self.tile_palette.setIconSize(self._palette_icon_size())
        self.tile_palette.setMinimumHeight(82)
        self.tile_palette.setMaximumHeight(128)
        self.tile_palette.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tool_combo = QComboBox(self)
        self.tool_combo.setObjectName("tilemap_tool_combo")
        for tool, label in (
            (TileTool.PENCIL, "Pincel"),
            (TileTool.ERASER, "Borracha"),
            (TileTool.RECTANGLE, "Retângulo"),
            (TileTool.BUCKET, "Balde"),
            (TileTool.PICKER, "Conta-gotas"),
        ):
            self.tool_combo.addItem(label, tool.value)
        self.new_button = QPushButton(self)
        self.open_button = QPushButton(self)
        self.save_button = QPushButton(self)
        self.reload_tileset_button = QPushButton(self)
        self.add_layer_button = QPushButton(self)
        self.layer_combo = QComboBox(self)
        self.layer_combo.setObjectName("tilemap_layer_combo")
        self.undo_button = QPushButton(self)
        self.redo_button = QPushButton(self)
        self.canvas = TileMapCanvas(self)
        self._tile_images: dict[str, QImage] = {}
        self.canvas.gesture_started.connect(self._begin_gesture)
        self.canvas.cell_painted.connect(self._paint_cells)
        self.canvas.gesture_finished.connect(self._finish_gesture)
        self.grid_combo.currentIndexChanged.connect(self._grid_changed)
        self.tile_combo.currentIndexChanged.connect(self._tile_combo_changed)
        self.tile_palette.currentRowChanged.connect(self._tile_palette_changed)
        self.layer_combo.currentIndexChanged.connect(self._layer_changed)
        self.new_button.clicked.connect(self.new_map)
        self.open_button.clicked.connect(self.open_map)
        self.save_button.clicked.connect(self.save_map)
        self.reload_tileset_button.clicked.connect(self.reload_tileset)
        self.add_layer_button.clicked.connect(self.add_layer)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self._build_layout()
        self.update_language("pt")

    def _status(self, pt: str, en: str) -> str:
        return pt if self.current_lang == "pt" else en

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
        palette_label = QLabel(self)
        palette_label.setObjectName("tilemap_palette_label")
        self.palette_label = palette_label
        layout.addWidget(palette_label)
        layout.addWidget(self.tile_palette)
        layer_row = QGridLayout()
        layer_label = QLabel(self)
        layer_label.setObjectName("tilemap_layer_label")
        self.layer_label = layer_label
        layer_row.addWidget(layer_label, 0, 0)
        layer_row.addWidget(self.layer_combo, 0, 1)
        layer_row.addWidget(self.add_layer_button, 1, 0, 1, 2)
        layer_row.setColumnStretch(1, 1)
        layout.addLayout(layer_row)
        actions = QGridLayout()
        action_buttons = (
            self.new_button,
            self.open_button,
            self.save_button,
            self.reload_tileset_button,
            self.undo_button,
            self.redo_button,
        )
        for index, button in enumerate(action_buttons):
            actions.addWidget(button, index // 3, index % 3)
        layout.addLayout(actions)
        layout.addWidget(self.canvas, 1)

    @property
    def map_path(self) -> Path:
        return self.project_root / "assets" / "tilemaps" / "scenario.tilemap.json"

    def _refresh_palette(self) -> None:
        self.tile_combo.clear()
        self.tile_palette.clear()
        if self.document is not None:
            for tile in self.document.tileset.tiles:
                self.tile_combo.addItem(tile.id, tile.id)
                item = QListWidgetItem(tile.id)
                image = self._tile_images.get(tile.id)
                if image is not None and not image.isNull():
                    item.setIcon(QIcon(QPixmap.fromImage(image)))
                self.tile_palette.addItem(item)
        if self.tile_combo.count():
            self.tile_combo.setCurrentIndex(0)
            self.tile_palette.setCurrentRow(0)

    @staticmethod
    def _palette_icon_size():
        from PySide6.QtCore import QSize

        return QSize(48, 48)

    @property
    def tileset_manifest_path(self) -> Path:
        return self.project_root / "assets" / "tilesets" / "scenario" / "tileset.json"

    def _load_saved_tileset(self) -> tuple[TileSet | None, dict[str, QImage]]:
        path = self.tileset_manifest_path
        if not path.is_file():
            return None, {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("format_id") != "neoeng-d-trace-tileset":
                return None, {}
            entries = payload.get("tiles")
            if not isinstance(entries, list) or not entries:
                return None, {}
            tiles: list[TileDefinition] = []
            images: dict[str, QImage] = {}
            manifest_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            for entry in entries:
                if not isinstance(entry, dict):
                    return None, {}
                rect = entry.get("source_rect")
                if not isinstance(rect, dict):
                    return None, {}
                tile_id = str(entry.get("id", ""))
                texture = entry.get("texture")
                tiles.append(
                    TileDefinition(
                        tile_id,
                        "scenario-tileset",
                        (
                            int(rect.get("x", 0)),
                            int(rect.get("y", 0)),
                            int(rect.get("w", 0)),
                            int(rect.get("h", 0)),
                        ),
                    )
                )
                if isinstance(texture, str):
                    image = QImage(str(path.parent / texture))
                    if not image.isNull():
                        images[tile_id] = image
            tileset = TileSet(
                id="scenario-tileset",
                atlas_asset_id="scenario-tileset",
                atlas_sha256=manifest_hash,
                tiles=tuple(tiles),
            )
            return tileset, images
        except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
            return None, {}

    def _sync_canvas(self) -> None:
        self.canvas.set_document(self.document)
        self.canvas.set_tile_images(self._tile_images)
        self.canvas.set_active_layer(self.layer_combo.currentData())

    def _refresh_layers(self) -> None:
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        if self.document is not None:
            for layer in self.document.layers:
                self.layer_combo.addItem(
                    f"{layer.name} · {'bloqueada' if layer.locked else 'editável'}",
                    layer.id,
                )
        self.layer_combo.blockSignals(False)
        if self.layer_combo.count():
            self.layer_combo.setCurrentIndex(0)

    def _tile_combo_changed(self, index: int) -> None:
        if 0 <= index < self.tile_palette.count():
            self.tile_palette.blockSignals(True)
            self.tile_palette.setCurrentRow(index)
            self.tile_palette.blockSignals(False)

    def _tile_palette_changed(self, index: int) -> None:
        if 0 <= index < self.tile_combo.count():
            self.tile_combo.blockSignals(True)
            self.tile_combo.setCurrentIndex(index)
            self.tile_combo.blockSignals(False)

    def _layer_changed(self) -> None:
        self.canvas.set_active_layer(self.layer_combo.currentData())

    def reload_tileset(self) -> None:
        tileset, images = self._load_saved_tileset()
        if tileset is None:
            self.status_message.emit(
                self._status(
                    "Nenhum tileset salvo encontrado; mantendo o tileset atual",
                    "No saved tileset found; keeping the current tileset",
                )
            )
            return
        if self.document is not None:
            current_cells = tuple(self.document.iter_cells())
            if any(
                not tileset.has_tile(cell.tile_id)
                for _layer, _coord, cell in current_cells
            ):
                self.status_message.emit(
                    self._status(
                        "Tileset não aplicado: há células incompatíveis",
                        "Tileset not applied: incompatible cells exist",
                    )
                )
                return
            self.document.tileset = tileset
        self._tile_images = images
        self._refresh_palette()
        self._sync_canvas()
        self.status_message.emit(
            self._status("Tileset atualizado", "Tileset updated")
        )

    def add_layer(self) -> None:
        if self.document is None:
            self.status_message.emit(
                self._status(
                    "Crie um tilemap antes de adicionar uma camada",
                    "Create a tilemap before adding a layer",
                )
            )
            return
        existing = {layer.id for layer in self.document.layers}
        index = 1
        while f"layer_{index}" in existing:
            index += 1
        self.document.add_layer(
            TileLayer(f"layer_{index}", f"Camada {index}", len(self.document.layers))
        )
        self._refresh_layers()
        self.layer_combo.setCurrentIndex(self.layer_combo.count() - 1)
        self._sync_canvas()
        self.status_message.emit(
            self._status("Camada adicionada", "Layer added")
        )

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

    def _select_tile(self, tile_id: str) -> bool:
        index = self.tile_combo.findData(tile_id)
        if index < 0:
            return False
        self.tile_combo.setCurrentIndex(index)
        self.tile_palette.setCurrentRow(index)
        return True

    def _record_transaction(
        self,
        transaction: TileEditTransaction,
        *,
        pt_message: str = "Edição do tilemap aplicada",
        en_message: str = "Tilemap edit applied",
    ) -> None:
        if not transaction.deltas:
            self.status_message.emit(
                self._status("Nenhuma célula alterada", "No cells changed")
            )
            return
        self._undo.append(transaction)
        self._redo.clear()
        self._refresh_summary()
        self.canvas.update()
        self.status_message.emit(self._status(pt_message, en_message))

    def _begin_gesture(self, _start: tuple[int, int]) -> None:
        """Start collecting the incremental segments of one pointer gesture."""

        self._active_gesture_transactions = []

    def _paint_cells(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        if self.document is None:
            return
        tool = self.tool_combo.currentData()
        if tool not in {TileTool.PENCIL.value, TileTool.ERASER.value}:
            return
        if tool == TileTool.PENCIL.value and not self.tile_combo.currentData():
            return
        layer_id = self.layer_combo.currentData() or self.document.layers[0].id
        try:
            if tool == TileTool.ERASER.value:
                transaction = erase_line(self.document, layer_id, start, end)
            else:
                transaction = paint_line(
                    self.document,
                    layer_id,
                    start,
                    end,
                    str(self.tile_combo.currentData()),
                )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Edição não aplicada: {exc}", f"Edit not applied: {exc}")
            )
            return
        if self._active_gesture_transactions is not None:
            if transaction.deltas:
                self._active_gesture_transactions.append(transaction)
                self._refresh_summary()
                self.canvas.update()
            return
        self._record_transaction(transaction)

    def _finish_gesture(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        pending = self._active_gesture_transactions
        self._active_gesture_transactions = None
        if self.document is None:
            return
        tool = self.tool_combo.currentData()
        if tool in {TileTool.PENCIL.value, TileTool.ERASER.value}:
            if pending:
                self._record_transaction(
                    TileEditTransaction.group_applied(pending),
                )
            else:
                self.status_message.emit(
                    self._status("Nenhuma célula alterada", "No cells changed")
                )
            return
        if tool not in {
            TileTool.RECTANGLE.value,
            TileTool.BUCKET.value,
            TileTool.PICKER.value,
        }:
            return
        layer_id = self.layer_combo.currentData() or self.document.layers[0].id
        try:
            if tool == TileTool.PICKER.value:
                cell = self.document.get_cell(layer_id, start)
                if cell is None:
                    self.status_message.emit(
                        self._status(
                            "Conta-gotas: nenhuma célula ocupada",
                            "Picker: no occupied cell",
                        )
                    )
                    return
                if not self._select_tile(cell.tile_id):
                    self.status_message.emit(
                        self._status(
                            f"Conta-gotas: tile incompatível ({cell.tile_id})",
                            f"Picker: incompatible tile ({cell.tile_id})",
                        )
                    )
                    return
                self.status_message.emit(
                    self._status(
                        f"Tile selecionado: {cell.tile_id}",
                        f"Tile selected: {cell.tile_id}",
                    )
                )
                return

            tile_id = self.tile_combo.currentData()
            if not tile_id:
                return
            if tool == TileTool.RECTANGLE.value:
                transaction = paint_rectangle(
                    self.document, layer_id, start, end, str(tile_id)
                )
                self._record_transaction(
                    transaction,
                    pt_message="Retângulo aplicado",
                    en_message="Rectangle applied",
                )
                return

            transaction = bucket_fill(
                self.document,
                layer_id,
                start,
                str(tile_id),
                grid=self.canvas.grid_spec(),
            )
            self._record_transaction(
                transaction,
                pt_message="Preenchimento aplicado",
                en_message="Bucket fill applied",
            )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Edição não aplicada: {exc}", f"Edit not applied: {exc}")
            )

    def new_map(self) -> None:
        tileset, images = self._load_saved_tileset()
        self._tile_images = images
        self.document = _default_document(tileset)
        self._undo.clear()
        self._redo.clear()
        self._active_gesture_transactions = None
        self._refresh_layers()
        self._refresh_palette()
        self._sync_canvas()
        self._refresh_summary()
        self.status_message.emit(
            self._status("Novo tilemap criado", "New tilemap created")
        )

    def open_map(self) -> None:
        try:
            self.document = load_tilemap(self.map_path)
        except Exception as exc:
            self.status_message.emit(
                self._status(
                    f"Falha ao abrir o tilemap: {exc}",
                    f"Tilemap open failed: {exc}",
                )
            )
            return
        self._undo.clear()
        self._redo.clear()
        self._active_gesture_transactions = None
        self.grid_combo.setCurrentIndex(self.grid_combo.findData(self.document.grid))
        self.canvas.set_grid_kind(GridKind(self.document.grid))
        _tileset, images = self._load_saved_tileset()
        self._tile_images = images
        self._refresh_layers()
        self._refresh_palette()
        self._sync_canvas()
        self._refresh_summary()
        self.status_message.emit(self._status("Tilemap reaberto", "Tilemap reopened"))

    def save_map(self) -> None:
        if self.document is None:
            self.status_message.emit(
                self._status(
                    "Crie um tilemap antes de salvar",
                    "Create a tilemap before saving",
                )
            )
            return
        try:
            save_tilemap(self.document, self.map_path)
        except Exception as exc:
            self.status_message.emit(
                self._status(
                    f"Falha ao salvar o tilemap: {exc}",
                    f"Tilemap save failed: {exc}",
                )
            )
            return
        self.status_message.emit(
            self._status(
                f"Tilemap salvo: {self.map_path.name}",
                f"Tilemap saved: {self.map_path.name}",
            )
        )

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
            tool_labels = (
                "Pincel",
                "Borracha",
                "Retângulo",
                "Balde",
                "Conta-gotas",
            )
            self.palette_label.setText("Paleta de tiles")
            self.layer_label.setText("Camada")
            self.new_button.setText("Novo")
            self.open_button.setText("Reabrir")
            self.save_button.setText("Salvar")
            self.reload_tileset_button.setText("Atualizar tileset")
            self.add_layer_button.setText("Adicionar camada")
            self.undo_button.setText("Desfazer")
            self.redo_button.setText("Refazer")
        else:
            self.title_label.setText("Tilemap / Terrain")
            grid_labels = ("Orthogonal", "Isometric", "Hexagonal")
            tool_labels = ("Pencil", "Eraser", "Rectangle", "Bucket", "Picker")
            self.palette_label.setText("Tile palette")
            self.layer_label.setText("Layer")
            self.new_button.setText("New")
            self.open_button.setText("Reopen")
            self.save_button.setText("Save")
            self.reload_tileset_button.setText("Reload tileset")
            self.add_layer_button.setText("Add layer")
            self.undo_button.setText("Undo")
            self.redo_button.setText("Redo")
        for index, label in enumerate(grid_labels):
            self.grid_combo.setItemText(index, label)
        for index, label in enumerate(tool_labels):
            self.tool_combo.setItemText(index, label)
        self.tool_combo.setToolTip(
            "Escolha a ferramenta e arraste no canvas"
            if self.current_lang == "pt"
            else "Choose a tool and drag on the canvas"
        )
        self._refresh_summary()


__all__ = ["TileMapAuthoringPanel", "TileMapCanvas"]
