"""Native tileset authoring surface for the integrated scenario studio."""

from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path
from typing import Any

from PIL import Image
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.exporters.tileset_exporter import (
    FORMAT_ID,
    SCHEMA_VERSION,
    prepare_tileset,
    save_tileset,
)


class TilesetAtlasPreview(QWidget):
    """Render an atlas and its slice boundaries with a selectable tile."""

    tile_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tileset_atlas_preview")
        self.setMinimumHeight(170)
        self.setMouseTracking(True)
        self._image = QImage()
        self._entries: list[dict[str, Any]] = []
        self._display_rect = QRect()
        self._scale = 1.0
        self._selected_index = -1

    def set_atlas(self, path: str | Path, entries: list[dict[str, Any]]) -> None:
        image = QImage(str(path))
        self._image = image if not image.isNull() else QImage()
        self._entries = list(entries)
        self._selected_index = -1
        self.update()

    def clear_preview(self) -> None:
        self._image = QImage()
        self._entries = []
        self._selected_index = -1
        self.update()

    def set_selected_index(self, index: int) -> None:
        self._selected_index = index
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101820"))
        if self._image.isNull():
            painter.setPen(QColor("#9aa9b5"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                (
                    "Selecione um atlas para visualizar"
                    if self._entries == []
                    else "Prévia do atlas indisponível"
                ),
            )
            return
        available = self.rect().adjusted(12, 12, -12, -12)
        self._scale = min(
            available.width() / max(1, self._image.width()),
            available.height() / max(1, self._image.height()),
        )
        self._scale = max(0.05, min(self._scale, 4.0))
        width = max(1, int(self._image.width() * self._scale))
        height = max(1, int(self._image.height() * self._scale))
        self._display_rect = QRect(
            available.center().x() - width // 2,
            available.center().y() - height // 2,
            width,
            height,
        )
        painter.drawImage(self._display_rect, self._image)
        for index, entry in enumerate(self._entries):
            rect = entry.get("source_rect", {})
            source = QRect(
                int(rect.get("x", 0)),
                int(rect.get("y", 0)),
                int(rect.get("w", 0)),
                int(rect.get("h", 0)),
            )
            target = QRect(
                self._display_rect.x() + int(source.x() * self._scale),
                self._display_rect.y() + int(source.y() * self._scale),
                max(1, int(source.width() * self._scale)),
                max(1, int(source.height() * self._scale)),
            )
            if index == self._selected_index:
                painter.fillRect(target, QColor(78, 196, 255, 75))
                painter.setPen(QPen(QColor("#76d7ff"), 2))
            else:
                painter.setPen(QPen(QColor(230, 242, 255, 130), 1))
            painter.drawRect(target)

    def mousePressEvent(self, event: Any) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._display_rect.isNull():
            return
        point = event.position().toPoint()
        if not self._display_rect.contains(point):
            return
        image_x = (point.x() - self._display_rect.x()) / self._scale
        image_y = (point.y() - self._display_rect.y()) / self._scale
        for index, entry in enumerate(self._entries):
            rect = entry.get("source_rect", {})
            if (
                float(rect.get("x", 0)) <= image_x
                < float(rect.get("x", 0)) + float(rect.get("w", 0))
                and float(rect.get("y", 0)) <= image_y
                < float(rect.get("y", 0)) + float(rect.get("h", 0))
            ):
                self._selected_index = index
                self.tile_selected.emit(index)
                self.update()
                return


class TilesetAuthoringPanel(QWidget):
    """Create, persist and reopen a tileset through the user-facing studio UI."""

    status_message = Signal(str)

    def __init__(self, project_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_root = Path(project_root)
        self.current_lang = "en"
        self.prepared: dict[str, Any] | None = None

        self.setObjectName("tileset_authoring_panel")
        self.title_label = QLabel(self)
        self.summary_label = QLabel(self)
        self.atlas_path_edit = QLineEdit(self)
        self.atlas_path_edit.setObjectName("tileset_atlas_path")
        self.atlas_path_edit.setPlaceholderText("Atlas PNG")
        self.browse_button = QPushButton(self)
        self.width_spin = self._size_spin(16)
        self.height_spin = self._size_spin(16)
        self.spacing_spin = self._size_spin(0)
        self.margin_spin = self._size_spin(0)
        self.tiles_list = QListWidget(self)
        self.tiles_list.setObjectName("tileset_tiles_list")
        self.new_button = QPushButton(self)
        self.generate_button = QPushButton(self)
        self.save_button = QPushButton(self)
        self.open_button = QPushButton(self)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        self.atlas_preview = TilesetAtlasPreview(self)
        self.atlas_preview.setToolTip(
            "Clique em uma célula para selecionar o tile e conferir sua área no atlas."
        )
        self.selected_tile_label = QLabel(self)
        self._entries: list[dict[str, Any]] = []
        self.atlas_label = QLabel(self)
        self.tile_width_label = QLabel(self)
        self.tile_height_label = QLabel(self)
        self.spacing_label = QLabel(self)
        self.margin_label = QLabel(self)

        self.browse_button.clicked.connect(self._browse)
        self.new_button.clicked.connect(self.new_tileset)
        self.generate_button.clicked.connect(self.generate_tileset)
        self.save_button.clicked.connect(self.save_current)
        self.open_button.clicked.connect(self.open_tileset)
        self.atlas_preview.tile_selected.connect(self._select_tile)
        self.tiles_list.currentRowChanged.connect(self._select_preview_tile)

        path_row = QHBoxLayout()
        path_row.addWidget(self.atlas_path_edit, 1)
        path_row.addWidget(self.browse_button)
        form = QFormLayout()
        form.addRow(self.atlas_label, path_row)
        form.addRow(self.tile_width_label, self.width_spin)
        form.addRow(self.tile_height_label, self.height_spin)
        form.addRow(self.spacing_label, self.spacing_spin)
        form.addRow(self.margin_label, self.margin_spin)

        actions = QHBoxLayout()
        for button in (
            self.new_button,
            self.generate_button,
            self.save_button,
            self.open_button,
        ):
            button.setAutoDefault(False)
            actions.addWidget(button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.summary_label)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.atlas_preview)
        layout.addWidget(self.selected_tile_label)
        layout.addWidget(self.tiles_list, 1)
        layout.addWidget(self.status_label)
        self.tiles_list.setIconSize(QSize(52, 52))
        self.tiles_list.setUniformItemSizes(True)
        self.update_language("pt")
        self.new_tileset()

    @staticmethod
    def _size_spin(value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, 4096)
        spin.setValue(value)
        return spin

    @property
    def tileset_dir(self) -> Path:
        return self.project_root / "assets" / "tilesets" / "scenario"

    @property
    def manifest_path(self) -> Path:
        return self.tileset_dir / "tileset.json"

    def _browse(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar atlas",
            str(self.project_root),
            "Imagens (*.png *.jpg *.jpeg *.bmp)",
        )
        if selected:
            self.atlas_path_edit.setText(selected)

    def _render_tiles(self, entries: list[dict[str, Any]]) -> None:
        self._entries = list(entries)
        self.tiles_list.clear()
        for index, entry in enumerate(entries):
            rect = entry.get("source_rect", {})
            collision = "com colisão" if entry.get("collision") else "sem colisão"
            item = QListWidgetItem(
                f"{entry.get('id', 'tile')} · "
                f"({rect.get('x', 0)}, {rect.get('y', 0)}) "
                f"{rect.get('w', 0)}×{rect.get('h', 0)} · {collision}"
            )
            image = entry.get("image")
            if isinstance(image, Image.Image):
                rgba = image.convert("RGBA")
                qimage = QImage(
                    rgba.tobytes("raw", "RGBA"),
                    rgba.width,
                    rgba.height,
                    QImage.Format.Format_RGBA8888,
                ).copy()
                item.setIcon(QIcon(QPixmap.fromImage(qimage)))
            self.tiles_list.addItem(item)
        self.summary_label.setText(
            f"{len(entries)} tiles · {FORMAT_ID} v{SCHEMA_VERSION}"
        )

    def _select_tile(self, index: int) -> None:
        if 0 <= index < self.tiles_list.count():
            self.tiles_list.setCurrentRow(index)

    def _select_preview_tile(self, index: int) -> None:
        if 0 <= index < len(self._entries):
            entry = self._entries[index]
            rect = entry.get("source_rect", {})
            self.selected_tile_label.setText(
                f"Tile selecionado: {entry.get('id', 'tile')} · "
                f"{rect.get('w', 0)}×{rect.get('h', 0)} px"
            )
            self.atlas_preview.set_selected_index(index)
        else:
            self.selected_tile_label.setText("Nenhum tile selecionado")

    def new_tileset(self) -> None:
        self.prepared = None
        self._entries = []
        self.tiles_list.clear()
        self.atlas_preview.clear_preview()
        self.selected_tile_label.setText("Nenhum tile selecionado")
        self.summary_label.setText("Nenhum tileset carregado")
        self.status_label.setText("Novo tileset pronto para configuração")

    def generate_tileset(self) -> None:
        source = Path(self.atlas_path_edit.text().strip())
        if not source.is_file():
            self.status_label.setText(
                "Atlas não encontrado; selecione uma imagem válida"
            )
            self.status_message.emit("Falha ao criar tileset: atlas não encontrado")
            return
        try:
            with Image.open(source) as image:
                prepared = prepare_tileset(
                    image.convert("RGBA"),
                    tile_size=(self.width_spin.value(), self.height_spin.value()),
                    spacing=self.spacing_spin.value(),
                    margin=self.margin_spin.value(),
                )
            if not prepared["tiles"]:
                raise ValueError("o atlas não contém uma célula completa")
        except (OSError, ValueError) as exc:
            self.status_label.setText(f"Falha ao preparar tileset: {exc}")
            self.status_message.emit(f"Falha ao criar tileset: {exc}")
            return
        self.prepared = prepared
        self.prepared["_source_atlas_path"] = str(source)
        self._render_tiles(prepared["tiles"])
        self.atlas_preview.set_atlas(source, prepared["tiles"])
        self.status_label.setText("Tileset preparado; clique em Salvar")
        self.status_message.emit("Tileset preparado")

    def save_current(self) -> None:
        if self.prepared is None:
            self.status_label.setText("Gere um tileset antes de salvar")
            self.status_message.emit(
                "Falha ao salvar tileset: nenhum tileset preparado"
            )
            return
        try:
            source = Path(str(self.prepared.get("_source_atlas_path", "")))
            if not source.is_file():
                raise ValueError("atlas de origem não está disponível")
            self.tileset_dir.mkdir(parents=True, exist_ok=True)
            source_name = f"source_atlas{source.suffix.lower() or '.png'}"
            bundled_atlas = self.tileset_dir / source_name
            shutil.copy2(source, bundled_atlas)
            prepared = dict(self.prepared)
            prepared.pop("_source_atlas_path", None)
            prepared["atlas_path"] = source_name
            prepared["atlas_sha256"] = hashlib.sha256(
                bundled_atlas.read_bytes()
            ).hexdigest()
            result = save_tileset(prepared, self.tileset_dir)
        except (OSError, ValueError) as exc:
            self.status_label.setText(f"Falha ao salvar tileset: {exc}")
            self.status_message.emit(f"Falha ao salvar tileset: {exc}")
            return
        self.status_label.setText(
            f"Tileset salvo: {Path(result['manifest_path']).name}"
        )
        self.status_message.emit(f"Tileset salvo: {self.manifest_path.name}")

    def open_tileset(self) -> None:
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if payload.get("format_id") != FORMAT_ID:
                raise ValueError("formato de tileset incompatível")
            if payload.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("versão de tileset incompatível")
            entries = payload.get("tiles")
            if not isinstance(entries, list) or not entries:
                raise ValueError("tileset sem tiles")
            loaded_entries: list[dict[str, Any]] = []
            atlas_reference = payload.get("atlas_path")
            if isinstance(atlas_reference, str):
                atlas_path = self.manifest_path.parent / atlas_reference
                if atlas_path.is_file():
                    self.atlas_path_edit.setText(str(atlas_path))
            for entry in entries:
                current = dict(entry)
                texture = current.get("texture")
                if isinstance(texture, str):
                    texture_path = self.manifest_path.parent / texture
                    if texture_path.is_file():
                        with Image.open(texture_path) as image:
                            current["image"] = image.convert("RGBA").copy()
                loaded_entries.append(current)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            self.status_label.setText(f"Falha ao reabrir tileset: {exc}")
            self.status_message.emit(f"Falha ao reabrir tileset: {exc}")
            return
        self.prepared = None
        self._render_tiles(loaded_entries)
        atlas_path = Path(self.atlas_path_edit.text().strip())
        if atlas_path.is_file():
            self.atlas_preview.set_atlas(atlas_path, loaded_entries)
        else:
            self.atlas_preview.clear_preview()
        self.status_label.setText("Tileset reaberto")
        self.status_message.emit("Tileset reaberto")

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.title_label.setText("Tileset / Atlas")
            self.browse_button.setText("Procurar")
            self.new_button.setText("Novo")
            self.generate_button.setText("Gerar")
            self.save_button.setText("Salvar")
            self.open_button.setText("Reabrir")
            self.atlas_label.setText("Atlas")
            self.tile_width_label.setText("Largura do tile")
            self.tile_height_label.setText("Altura do tile")
            self.spacing_label.setText("Espaçamento")
            self.margin_label.setText("Margem")
        else:
            self.title_label.setText("Tileset / Atlas")
            self.browse_button.setText("Browse")
            self.new_button.setText("New")
            self.generate_button.setText("Generate")
            self.save_button.setText("Save")
            self.open_button.setText("Reopen")
            self.atlas_label.setText("Atlas")
            self.tile_width_label.setText("Tile width")
            self.tile_height_label.setText("Tile height")
            self.spacing_label.setText("Spacing")
            self.margin_label.setText("Margin")


__all__ = ["TilesetAtlasPreview", "TilesetAuthoringPanel"]
