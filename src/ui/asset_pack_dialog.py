"""Native thumbnail catalog for bundled art, independent of scene asset records."""

from collections import OrderedDict

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImageReader, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.core.asset_packs import contained_file, discover_packs, search_key
from src.ui.theme_tokens import THEME_TOKENS


class AssetPackDialog(QDialog):
    """Browse without changing a project; import only by explicit button activation."""

    def __init__(self, library, *, pack_root=None):
        super().__init__(library)
        self.library = library
        self.pt = library.current_lang == "pt"
        self.setObjectName("asset_pack_dialog")
        self.setWindowTitle(self.tr_text("Pacotes NeoEng", "NeoEng Packs"))
        self.resize(1000, 700)
        self.packs, errors = discover_packs(pack_root)
        self._cache = OrderedDict()
        self._pending = []
        self.pack_combo = QComboBox()
        self.pack_combo.setObjectName("asset_pack_selector")
        for pack in self.packs:
            self.pack_combo.addItem(f"{pack.name} · {pack.version}")
        self.search = QLineEdit()
        self.search.setObjectName("asset_pack_search")
        self.search.setPlaceholderText(
            self.tr_text("Pesquisar por nome ou tipo…", "Search by name or type…")
        )
        self.category = QComboBox()
        self.category.setObjectName("asset_pack_category")
        self.grid = QListWidget()
        self.grid.setObjectName("asset_pack_grid")
        self.grid.setViewMode(QListView.ViewMode.IconMode)
        self.grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid.setMovement(QListView.Movement.Static)
        self.grid.setIconSize(QSize(144, 144))
        self.grid.setGridSize(QSize(174, 184))
        self.grid.setWordWrap(True)
        self.grid.setSpacing(6)
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(260, 260)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextFormat(Qt.TextFormat.PlainText)
        self.add_button = QPushButton(
            self.tr_text("Adicionar ao projeto", "Add to project")
        )
        self.add_button.setObjectName("asset_pack_import")
        self.add_button.setAutoDefault(False)
        self.add_button.setEnabled(False)
        self.add_button.setToolTip(
            self.tr_text(
                "Copia o asset para a biblioteca do projeto. Depois arraste-o para uma moldura.",
                "Copy the asset into the project library, then drag it into a frame.",
            )
        )
        self.status = QLabel("\n".join(errors))
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.TextFormat.PlainText)
        close = QPushButton(self.tr_text("Voltar à biblioteca", "Back to library"))
        close.setAutoDefault(False)
        close.clicked.connect(self.accept)
        side = QWidget()
        right = QVBoxLayout(side)
        right.addWidget(self.preview)
        right.addWidget(self.details)
        right.addStretch()
        right.addWidget(self.add_button)
        right.addWidget(close)
        splitter = QSplitter()
        splitter.addWidget(self.grid)
        splitter.addWidget(side)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        filters = QHBoxLayout()
        filters.addWidget(self.search, 1)
        filters.addWidget(self.category)
        layout = QVBoxLayout(self)
        layout.addWidget(self.pack_combo)
        layout.addWidget(self.summary)
        layout.addLayout(filters)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self._next_thumbnail)
        self.pack_combo.currentIndexChanged.connect(self._pack_changed)
        self.search.textChanged.connect(self._filter)
        self.category.currentIndexChanged.connect(self._filter)
        self.grid.currentItemChanged.connect(self._selection_changed)
        self.add_button.clicked.connect(self._import)
        self._pack_changed()
        if not self.packs and not errors:
            self.status.setText(
                self.tr_text(
                    "Nenhum pacote disponível nesta instalação.",
                    "No packs available in this installation.",
                )
            )

    def tr_text(self, pt, en):
        return pt if self.pt else en

    @property
    def pack(self):
        index = self.pack_combo.currentIndex()
        return self.packs[index] if 0 <= index < len(self.packs) else None

    def _pack_changed(self, *_):
        self.timer.stop()
        self._pending.clear()
        self.grid.clear()
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem(self.tr_text("Todos os tipos", "All types"), "")
        if self.pack:
            for category in sorted({a.category for a in self.pack.assets}):
                self.category.addItem(category, category)
            self.summary.setText(
                f"{self.pack.description}\n{len(self.pack.assets)} assets · {self.pack.provenance}"
            )
            for asset in self.pack.assets:
                item = QListWidgetItem(asset.name)
                item.setData(Qt.ItemDataRole.UserRole, asset)
                item.setToolTip(
                    f"{asset.name}\n{asset.width} × {asset.height} px\n{asset.description}"
                )
                self.grid.addItem(item)
        self.category.blockSignals(False)
        self._filter()

    def _filter(self, *_):
        query = search_key(self.search.text().strip())
        category = self.category.currentData() or ""
        self._pending.clear()
        for row in range(self.grid.count()):
            item = self.grid.item(row)
            asset = item.data(Qt.ItemDataRole.UserRole)
            visible = (
                not category or asset.category == category
            ) and query in search_key(
                " ".join((asset.name, asset.category, *asset.tags))
            )
            item.setHidden(not visible)
            if visible and item.icon().isNull():
                self._pending.append(item)
        selected = self.grid.currentItem()
        if selected and selected.isHidden():
            self.grid.setCurrentRow(-1)
        self.timer.start()

    def _image(self, asset, size):
        key = (str(self.pack.root), asset.sha256, size)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        path = contained_file(self.pack.root, asset.path)
        reader = QImageReader(str(path))
        original_size = reader.size()
        if (
            original_size.width() != asset.width
            or original_size.height() != asset.height
        ):
            raise ValueError(
                self.tr_text(
                    "Dimensões incompatíveis com o pacote",
                    "Dimensions do not match the pack",
                )
            )
        reader.setScaledSize(
            original_size.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio)
        )
        image = reader.read()
        if image.isNull():
            raise ValueError(
                self.tr_text("Não foi possível abrir a imagem", "Cannot decode image")
            )
        pixmap = QPixmap(size, size)
        painter = QPainter(pixmap)
        for y in range(0, size, 12):
            for x in range(0, size, 12):
                color = (
                    THEME_TOKENS.surface_alt
                    if (x // 12 + y // 12) % 2
                    else THEME_TOKENS.surface
                )
                painter.fillRect(x, y, 12, 12, QColor(color))
        painter.drawImage(
            (size - image.width()) // 2, (size - image.height()) // 2, image
        )
        painter.end()
        self._cache[key] = pixmap
        while len(self._cache) > 96:
            self._cache.popitem(last=False)
        return pixmap

    def _next_thumbnail(self):
        if not self._pending:
            self.timer.stop()
            return
        item = self._pending.pop(0)
        try:
            item.setIcon(QIcon(self._image(item.data(Qt.ItemDataRole.UserRole), 144)))
        except (OSError, ValueError) as exc:
            self.status.setText(str(exc))

    def _selection_changed(self, current, *_):
        self.preview.clear()
        self.details.clear()
        self.add_button.setEnabled(False)
        if current is None or self.pack is None:
            return
        asset = current.data(Qt.ItemDataRole.UserRole)
        try:
            self.preview.setPixmap(self._image(asset, 280))
            self.details.setText(
                f"{asset.name}\n{asset.category} · {asset.width} × {asset.height} px\n\n{asset.description}"
            )
            self.add_button.setEnabled(self.library.project_root is not None)
            if self.library.project_root is None:
                self.status.setText(
                    self.tr_text(
                        "Salve o projeto antes de adicionar assets.",
                        "Save the project before adding assets.",
                    )
                )
        except (OSError, ValueError) as exc:
            self.status.setText(str(exc))

    def _import(self):
        item = self.grid.currentItem()
        if item is None or self.pack is None or self.library.project_root is None:
            return
        asset = item.data(Qt.ItemDataRole.UserRole)
        try:
            path = self.pack.resolve_asset(asset)
            self.library.search_edit.clear()
            self.library.category_combo.setCurrentIndex(0)
            changed = self.library.import_asset_from_path(path)
            present = any(
                a.sha256 == asset.sha256 for a in self.library.session.document.assets
            )
            if not present:
                raise ValueError(
                    self.tr_text(
                        "A importação não foi concluída.", "Import did not complete."
                    )
                )
            self.status.setText(
                self.tr_text(
                    f"{asset.name}: {'adicionado' if changed else 'já disponível'} na biblioteca do projeto. Volte à biblioteca para arrastar até uma moldura.",
                    f"{asset.name}: {'added to' if changed else 'already in'} the project library. Return to the library to drag it into a frame.",
                )
            )
        except (OSError, ValueError) as exc:
            self.status.setText(
                self.tr_text("Falha ao importar: ", "Import failed: ") + str(exc)
            )

    def done(self, result):
        self.timer.stop()
        super().done(result)
