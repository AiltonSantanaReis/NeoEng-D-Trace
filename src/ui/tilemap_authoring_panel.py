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
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
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
    TileClipboard,
    TileEditTransaction,
    TileTool,
    bucket_fill,
    copy_cells,
    erase_line,
    paint_line,
    paint_rectangle,
    paint_variation,
    paste_cells,
    rectangle_cells,
)
from src.core.tilemap_rules import NeighborCondition, TerrainRule, TileRuleSet
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
    selection_changed = Signal(tuple, tuple)

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
        self.selection: tuple[tuple[int, int], tuple[int, int]] | None = None

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

    def set_selection(
        self,
        selection: tuple[tuple[int, int], tuple[int, int]] | None,
    ) -> None:
        self.selection = selection
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
        if self.selection is not None:
            start, end = self.selection
            min_x, max_x = sorted((start[0], end[0]))
            min_y, max_y = sorted((start[1], end[1]))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#ffd166"), 2, Qt.PenStyle.DashLine))
            for row in range(min_y, max_y + 1):
                for column in range(min_x, max_x + 1):
                    painter.drawPolygon(
                        self._cell_shape(spec, spec.cell_to_world((column, row)))
                    )

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
        self._selection: tuple[tuple[int, int], tuple[int, int]] | None = None
        self._clipboard: TileClipboard | None = None
        self._rules: list[TerrainRule] = []
        self._rule_fallback_tile_id: str | None = None
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
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.tool_combo = QComboBox(self)
        self.tool_combo.setObjectName("tilemap_tool_combo")
        for tool, label in (
            (TileTool.PENCIL, "Pincel"),
            (TileTool.ERASER, "Borracha"),
            (TileTool.RECTANGLE, "Retângulo"),
            (TileTool.BUCKET, "Balde"),
            (TileTool.PICKER, "Conta-gotas"),
            (TileTool.SELECT, "Seleção"),
        ):
            self.tool_combo.addItem(label, tool.value)
        self.variation_seed_label = QLabel(self)
        self.variation_seed_spin = QSpinBox(self)
        self.variation_seed_spin.setRange(0, 2_147_483_647)
        self.variation_seed_spin.setValue(7)
        self.new_button = QPushButton(self)
        self.open_button = QPushButton(self)
        self.save_button = QPushButton(self)
        self.reload_tileset_button = QPushButton(self)
        self.add_layer_button = QPushButton(self)
        self.layer_combo = QComboBox(self)
        self.layer_combo.setObjectName("tilemap_layer_combo")
        self.undo_button = QPushButton(self)
        self.redo_button = QPushButton(self)
        self.copy_button = QPushButton(self)
        self.paste_button = QPushButton(self)
        self.variation_button = QPushButton(self)
        self.rules_group = QGroupBox(self)
        self.rule_target_label = QLabel(self)
        self.rule_target_combo = QComboBox(self)
        self.rule_neighbor_label = QLabel(self)
        self.rule_neighbor_combo = QComboBox(self)
        self.rule_offset_label = QLabel(self)
        self.rule_offset_combo = QComboBox(self)
        self.rule_fallback_label = QLabel(self)
        self.rule_fallback_combo = QComboBox(self)
        self.add_rule_button = QPushButton(self)
        self.apply_rules_button = QPushButton(self)
        self.rules_list = QListWidget(self)
        self.rules_list.setMaximumHeight(30)
        self.rules_group.setMaximumHeight(135)
        for label, offset in (
            ("Direita", (1, 0)),
            ("Esquerda", (-1, 0)),
            ("Abaixo", (0, 1)),
            ("Acima", (0, -1)),
        ):
            self.rule_offset_combo.addItem(label, offset)
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
        self.copy_button.clicked.connect(self.copy_selection)
        self.paste_button.clicked.connect(self.paste_selection)
        self.variation_button.clicked.connect(self.apply_variation)
        self.add_rule_button.clicked.connect(self.add_rule)
        self.apply_rules_button.clicked.connect(self.apply_rules)
        self.paste_button.setEnabled(False)
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
        controls.addWidget(self.variation_seed_label)
        controls.addWidget(self.variation_seed_spin)
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
        extra_buttons = (
            self.copy_button,
            self.paste_button,
            self.variation_button,
        )
        for offset, button in enumerate(extra_buttons, start=len(action_buttons)):
            actions.addWidget(button, offset // 3, offset % 3)
        layout.addLayout(actions)
        rules_form = QGridLayout(self.rules_group)
        rules_form.addWidget(self.rule_target_label, 0, 0)
        rules_form.addWidget(self.rule_target_combo, 0, 1)
        rules_form.addWidget(self.rule_neighbor_label, 0, 2)
        rules_form.addWidget(self.rule_neighbor_combo, 0, 3)
        rules_form.addWidget(self.rule_offset_label, 1, 0)
        rules_form.addWidget(self.rule_offset_combo, 1, 1)
        rules_form.addWidget(self.rule_fallback_label, 1, 2)
        rules_form.addWidget(self.rule_fallback_combo, 1, 3)
        rule_actions = QHBoxLayout()
        rule_actions.addWidget(self.add_rule_button)
        rule_actions.addWidget(self.apply_rules_button)
        rules_form.addLayout(rule_actions, 2, 0, 1, 4)
        rules_form.addWidget(self.rules_list, 3, 0, 1, 4)
        layout.addWidget(self.rules_group)
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
                item.setData(Qt.ItemDataRole.UserRole, tile.id)
                image = self._tile_images.get(tile.id)
                if image is not None and not image.isNull():
                    item.setIcon(QIcon(QPixmap.fromImage(image)))
                self.tile_palette.addItem(item)
        if self.tile_combo.count():
            self.tile_combo.setCurrentIndex(0)
            self.tile_palette.setCurrentRow(0)
            self.tile_palette.item(0).setSelected(True)
        self._refresh_rule_controls()

    def _refresh_rule_controls(self) -> None:
        values = [] if self.document is None else [
            tile.id for tile in self.document.tileset.tiles
        ]
        for combo in (
            self.rule_target_combo,
            self.rule_neighbor_combo,
            self.rule_fallback_combo,
        ):
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            if combo is self.rule_neighbor_combo:
                combo.addItem("<vazio>", None)
            for tile_id in values:
                combo.addItem(tile_id, tile_id)
            if current in values or (combo is self.rule_neighbor_combo and current is None):
                combo.setCurrentIndex(combo.findData(current))
            elif combo.count():
                combo.setCurrentIndex(0)
            combo.blockSignals(False)
        if values and self._rule_fallback_tile_id not in values:
            self._rule_fallback_tile_id = values[0]
        if self._rule_fallback_tile_id is not None:
            self.rule_fallback_combo.setCurrentIndex(
                self.rule_fallback_combo.findData(self._rule_fallback_tile_id)
            )
        self._refresh_rules_list()

    def _refresh_empty_neighbor_label(self) -> None:
        if self.rule_neighbor_combo.count() and self.rule_neighbor_combo.currentData() is None:
            self.rule_neighbor_combo.setItemText(
                0,
                "<vazio>" if self.current_lang == "pt" else "<empty>",
            )

    def _refresh_rules_list(self) -> None:
        self.rules_list.clear()
        for rule in self._rules:
            self.rules_list.addItem(
                f"{rule.id} → {rule.target_tile_id} ({len(rule.conditions)} vizinhos)"
            )

    def _load_rule_state(self) -> None:
        """Restore the optional rule authoring state from the open document."""

        self._rules = []
        self._rule_fallback_tile_id = None
        if self.document is not None and self.document.rule_set_payload is not None:
            rule_set = TileRuleSet.from_dict(self.document.rule_set_payload)
            self._rules = list(rule_set.rules)
            self._rule_fallback_tile_id = rule_set.fallback_tile_id
        self._refresh_rule_controls()

    def _selected_tile_ids(self) -> tuple[str, ...]:
        values = tuple(
            str(item.data(Qt.ItemDataRole.UserRole))
            for item in self.tile_palette.selectedItems()
            if item.data(Qt.ItemDataRole.UserRole)
        )
        if values:
            return values
        current = self.tile_combo.currentData()
        return () if current is None else (str(current),)

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
            atlas_hash = payload.get("atlas_sha256", manifest_hash)
            if not isinstance(atlas_hash, str):
                atlas_hash = manifest_hash
            atlas_path = payload.get("atlas_path")
            if not isinstance(atlas_path, str):
                atlas_path = None
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
                atlas_sha256=atlas_hash,
                tiles=tuple(tiles),
                atlas_path=atlas_path,
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
        self.tile_palette.clearSelection()
        self.tile_palette.setCurrentRow(index)
        if self.tile_palette.item(index) is not None:
            self.tile_palette.item(index).setSelected(True)
        return True

    def _set_selection(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        *,
        announce: bool = True,
    ) -> None:
        self._selection = (start, end)
        self.canvas.set_selection(self._selection)
        if announce:
            min_x, max_x = sorted((start[0], end[0]))
            min_y, max_y = sorted((start[1], end[1]))
            count = (max_x - min_x + 1) * (max_y - min_y + 1)
            self.status_message.emit(
                self._status(
                    f"Seleção criada: {count} células",
                    f"Selection created: {count} cells",
                )
            )

    def _selected_coordinates(self) -> tuple[tuple[int, int], ...]:
        if self._selection is None:
            return ()
        return rectangle_cells(*self._selection)

    def copy_selection(self) -> None:
        if self.document is None or self._selection is None:
            self.status_message.emit(
                self._status("Selecione uma área antes de copiar", "Select an area before copying")
            )
            return
        layer_id = self.layer_combo.currentData() or self.document.layers[0].id
        try:
            self._clipboard = copy_cells(
                self.document, layer_id, self._selected_coordinates()
            )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Cópia não aplicada: {exc}", f"Copy not applied: {exc}")
            )
            return
        self.paste_button.setEnabled(True)
        self.status_message.emit(
            self._status(
                f"Área copiada: {len(self._clipboard.cells)} células",
                f"Area copied: {len(self._clipboard.cells)} cells",
            )
        )

    def paste_selection(self) -> None:
        if self.document is None or self._selection is None:
            self.status_message.emit(
                self._status("Selecione um destino antes de colar", "Select a destination before pasting")
            )
            return
        if self._clipboard is None:
            self.status_message.emit(
                self._status("Nenhuma área copiada", "No copied area")
            )
            return
        layer_id = self.layer_combo.currentData() or self.document.layers[0].id
        anchor = min(self._selection[0][0], self._selection[1][0]), min(
            self._selection[0][1], self._selection[1][1]
        )
        try:
            transaction = paste_cells(
                self.document, layer_id, anchor, self._clipboard
            )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Colagem não aplicada: {exc}", f"Paste not applied: {exc}")
            )
            return
        self._record_transaction(
            transaction,
            pt_message="Área colada",
            en_message="Area pasted",
        )

    def apply_variation(self) -> None:
        if self.document is None or self._selection is None:
            self.status_message.emit(
                self._status("Selecione uma área para variar", "Select an area to vary")
            )
            return
        tile_ids = self._selected_tile_ids()
        if len(tile_ids) < 2:
            self.status_message.emit(
                self._status(
                    "Selecione pelo menos dois tiles na paleta",
                    "Select at least two tiles in the palette",
                )
            )
            return
        layer_id = self.layer_combo.currentData() or self.document.layers[0].id
        try:
            transaction = paint_variation(
                self.document,
                layer_id,
                self._selection[0],
                self._selection[1],
                tile_ids,
                seed=self.variation_seed_spin.value(),
            )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Variação não aplicada: {exc}", f"Variation not applied: {exc}")
            )
            return
        self._record_transaction(
            transaction,
            pt_message="Variação aplicada",
            en_message="Variation applied",
        )

    def add_rule(self) -> None:
        target = self.rule_target_combo.currentData()
        offset = self.rule_offset_combo.currentData()
        neighbour = self.rule_neighbor_combo.currentData()
        if (
            not target
            or not isinstance(offset, (tuple, list))
            or len(offset) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in offset)
        ):
            self.status_message.emit(
                self._status("Configure a regra antes de adicionar", "Configure the rule before adding")
            )
            return
        rule_id = f"rule_{len(self._rules) + 1}"
        while rule_id in {rule.id for rule in self._rules}:
            rule_id = f"rule_{len(self._rules) + 2}"
        condition = NeighborCondition(
            tuple(offset),
            () if neighbour is None else (str(neighbour),),
            allow_empty=neighbour is None,
        )
        try:
            self._rules.append(
                TerrainRule(str(rule_id), str(target), conditions=(condition,))
            )
            self._refresh_rules_list()
            self.status_message.emit(
                self._status("Regra de autotiling adicionada", "Autotile rule added")
            )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Regra não adicionada: {exc}", f"Rule not added: {exc}")
            )

    def apply_rules(self) -> None:
        if self.document is None or not self._rules:
            self.status_message.emit(
                self._status("Adicione uma regra antes de aplicar", "Add a rule before applying")
            )
            return
        fallback = self.rule_fallback_combo.currentData()
        if not fallback:
            self.status_message.emit(
                self._status("Selecione o tile de fallback", "Select the fallback tile")
            )
            return
        layer_id = self.layer_combo.currentData() or self.document.layers[0].id
        coordinates = self._selected_coordinates()
        if not coordinates:
            coordinates = tuple(
                coordinate
                for current_layer, coordinate, _cell in self.document.iter_cells(layer_id)
                if current_layer == layer_id
            )
        if not coordinates:
            self.status_message.emit(
                self._status("Não há células para autotiling", "There are no cells to autotile")
            )
            return
        try:
            rule_set = TileRuleSet(tuple(self._rules), fallback_tile_id=str(fallback))
            _resolutions, transaction = rule_set.apply(
                self.document,
                layer_id,
                coordinates,
                grid=self.canvas.grid_spec(),
                seed=self.variation_seed_spin.value(),
            )
        except ValueError as exc:
            self.status_message.emit(
                self._status(f"Autotiling não aplicado: {exc}", f"Autotiling not applied: {exc}")
            )
            return
        self.document.rule_set_payload = rule_set.to_dict()
        self._rule_fallback_tile_id = str(fallback)
        self._record_transaction(
            transaction,
            pt_message="Autotiling aplicado",
            en_message="Autotiling applied",
        )

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
        if tool == TileTool.SELECT.value:
            self._set_selection(start, end)
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
        self.grid_combo.setCurrentIndex(self.grid_combo.findData(self.document.grid))
        self.canvas.set_grid_kind(GridKind(self.document.grid))
        self._undo.clear()
        self._redo.clear()
        self._active_gesture_transactions = None
        self._selection = None
        self._clipboard = None
        self.paste_button.setEnabled(False)
        self._rules = []
        self._rule_fallback_tile_id = None
        self._refresh_layers()
        self._refresh_palette()
        self._load_rule_state()
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
        self._selection = None
        self._clipboard = None
        self.paste_button.setEnabled(False)
        self.grid_combo.setCurrentIndex(self.grid_combo.findData(self.document.grid))
        self.canvas.set_grid_kind(GridKind(self.document.grid))
        _tileset, images = self._load_saved_tileset()
        self._tile_images = images
        self._refresh_layers()
        self._refresh_palette()
        self._load_rule_state()
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
            if self._rules:
                fallback = self.rule_fallback_combo.currentData()
                if not fallback:
                    raise ValueError("selecione o tile de fallback")
                self._rule_fallback_tile_id = str(fallback)
                self.document.rule_set_payload = TileRuleSet(
                    tuple(self._rules),
                    fallback_tile_id=self._rule_fallback_tile_id,
                ).to_dict()
            else:
                self.document.rule_set_payload = None
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
                "Seleção",
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
            self.variation_seed_label.setText("Semente da variação")
            self.copy_button.setText("Copiar")
            self.paste_button.setText("Colar")
            self.variation_button.setText("Variação")
            self.rules_group.setTitle("Autotiling / Rule Tiles")
            self.rule_target_label.setText("Tile alvo")
            self.rule_neighbor_label.setText("Vizinho")
            self.rule_offset_label.setText("Direção")
            self.rule_fallback_label.setText("Fallback")
            self.add_rule_button.setText("Adicionar regra")
            self.apply_rules_button.setText("Aplicar regras")
        else:
            self.title_label.setText("Tilemap / Terrain")
            grid_labels = ("Orthogonal", "Isometric", "Hexagonal")
            tool_labels = (
                "Pencil",
                "Eraser",
                "Rectangle",
                "Bucket",
                "Picker",
                "Select",
            )
            self.palette_label.setText("Tile palette")
            self.layer_label.setText("Layer")
            self.new_button.setText("New")
            self.open_button.setText("Reopen")
            self.save_button.setText("Save")
            self.reload_tileset_button.setText("Reload tileset")
            self.add_layer_button.setText("Add layer")
            self.undo_button.setText("Undo")
            self.redo_button.setText("Redo")
            self.variation_seed_label.setText("Variation seed")
            self.copy_button.setText("Copy")
            self.paste_button.setText("Paste")
            self.variation_button.setText("Variation")
            self.rules_group.setTitle("Autotiling / Rule Tiles")
            self.rule_target_label.setText("Target tile")
            self.rule_neighbor_label.setText("Neighbor")
            self.rule_offset_label.setText("Direction")
            self.rule_fallback_label.setText("Fallback")
            self.add_rule_button.setText("Add rule")
            self.apply_rules_button.setText("Apply rules")
        self._refresh_empty_neighbor_label()
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
