"""Native tileset authoring surface for the integrated scenario studio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
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

        self.browse_button.clicked.connect(self._browse)
        self.new_button.clicked.connect(self.new_tileset)
        self.generate_button.clicked.connect(self.generate_tileset)
        self.save_button.clicked.connect(self.save_current)
        self.open_button.clicked.connect(self.open_tileset)

        path_row = QHBoxLayout()
        path_row.addWidget(self.atlas_path_edit, 1)
        path_row.addWidget(self.browse_button)
        form = QFormLayout()
        form.addRow("Atlas", path_row)
        form.addRow("Tile width", self.width_spin)
        form.addRow("Tile height", self.height_spin)
        form.addRow("Spacing", self.spacing_spin)
        form.addRow("Margin", self.margin_spin)

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
        layout.addWidget(self.tiles_list, 1)
        layout.addWidget(self.status_label)
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
        self.tiles_list.clear()
        for entry in entries:
            rect = entry.get("source_rect", {})
            collision = "com colisão" if entry.get("collision") else "sem colisão"
            self.tiles_list.addItem(
                f"{entry.get('id', 'tile')} · "
                f"({rect.get('x', 0)}, {rect.get('y', 0)}) "
                f"{rect.get('w', 0)}×{rect.get('h', 0)} · {collision}"
            )
        self.summary_label.setText(
            f"{len(entries)} tiles · {FORMAT_ID} v{SCHEMA_VERSION}"
        )

    def new_tileset(self) -> None:
        self.prepared = None
        self.tiles_list.clear()
        self.summary_label.setText("Nenhum tileset carregado")
        self.status_label.setText("Novo tileset pronto para configuração")

    def generate_tileset(self) -> None:
        source = Path(self.atlas_path_edit.text().strip())
        if not source.is_file():
            self.status_label.setText("Atlas não encontrado; selecione uma imagem válida")
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
        self._render_tiles(prepared["tiles"])
        self.status_label.setText("Tileset preparado; clique em Salvar")
        self.status_message.emit("Tileset preparado")

    def save_current(self) -> None:
        if self.prepared is None:
            self.status_label.setText("Gere um tileset antes de salvar")
            self.status_message.emit("Falha ao salvar tileset: nenhum tileset preparado")
            return
        try:
            result = save_tileset(self.prepared, self.tileset_dir)
        except (OSError, ValueError) as exc:
            self.status_label.setText(f"Falha ao salvar tileset: {exc}")
            self.status_message.emit(f"Falha ao salvar tileset: {exc}")
            return
        self.status_label.setText(f"Tileset salvo: {Path(result['manifest_path']).name}")
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
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            self.status_label.setText(f"Falha ao reabrir tileset: {exc}")
            self.status_message.emit(f"Falha ao reabrir tileset: {exc}")
            return
        self.prepared = None
        self._render_tiles(entries)
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
        else:
            self.title_label.setText("Tileset / Atlas")
            self.browse_button.setText("Browse")
            self.new_button.setText("New")
            self.generate_button.setText("Generate")
            self.save_button.setText("Save")
            self.open_button.setText("Reopen")


__all__ = ["TilesetAuthoringPanel"]
