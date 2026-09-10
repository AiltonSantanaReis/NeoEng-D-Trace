"""Asset library and lifecycle controls for the professional scene editor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QByteArray, QMimeData, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scene_asset_library import (
    PreparedSceneAsset,
    SceneAssetInspection,
    SceneAssetState,
    inspect_scene_asset,
    prepare_scene_asset,
    validate_scene_asset_source,
)
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.p2d05_errors import user_error_message
from src.persistence.scene_authoring_schema import AssetReferenceRecord
from src.ui.context_menu_utils import fit_context_menu
from src.ui.scene_authoring_viewport import SceneAuthoringViewport
from src.ui.theme_tokens import THEME_TOKENS

_ASSET_FILTER = (
    "Scene assets (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.svg);;" "All files (*)"
)
_STATE_COLORS = {
    "ready": THEME_TOKENS.success,
    "missing": THEME_TOKENS.warning,
    "modified": THEME_TOKENS.warning,
    "invalid": THEME_TOKENS.error,
    "unavailable": THEME_TOKENS.error,
}
_STATE_LABELS = {
    "ready": "READY",
    "missing": "MISSING",
    "modified": "MODIFIED",
    "invalid": "INVALID",
    "unavailable": "UNAVAILABLE",
}


def _asset_category(asset: AssetReferenceRecord) -> str:
    return "Vector" if asset.path.lower().endswith(".svg") else "Raster"


class _AssetListWidget(QListWidget):
    """Asset list with an explicit, inspectable MIME contract for drops."""

    ASSET_MIME = "application/x-neoeng-scene-asset"

    @classmethod
    def mime_for_asset(cls, asset_id: str) -> QMimeData:
        mime = QMimeData()
        mime.setData(cls.ASSET_MIME, QByteArray(asset_id.encode("utf-8")))
        mime.setText(f"asset://{asset_id}")
        return mime

    def startDrag(self, supported_actions: Any) -> None:
        item = self.currentItem()
        if item is None:
            return
        asset_id = item.data(Qt.ItemDataRole.UserRole)
        if not asset_id:
            return
        drag = QDrag(self)
        drag.setMimeData(self.mime_for_asset(str(asset_id)))
        drag.exec(Qt.DropAction.CopyAction)


class SceneAssetLibrary(QWidget):
    """Inspectable asset list with transactional relink and replace actions."""

    status_message = Signal(str)
    asset_selected = Signal(object)
    asset_place_requested = Signal(str)

    def __init__(
        self,
        session: SceneAuthoringSession,
        project_root: Path | None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.project_root = project_root.resolve() if project_root else None
        self.current_lang = "en"
        self._refreshing = False
        self._inspections: dict[str, SceneAssetInspection] = {}
        self._dimensions: dict[str, tuple[int, int]] = {}
        self.setObjectName("professional_scene_asset_library")

        self.title = QLabel("Scene Assets")
        self.title.setObjectName("scene_asset_library_title")
        self.summary_label = QLabel()
        self.summary_label.setObjectName("scene_asset_library_summary")
        self.summary_label.setWordWrap(True)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("scene_asset_search")
        self.category_combo = QComboBox()
        self.category_combo.setObjectName("scene_asset_category")
        self.category_combo.addItem("All categories", "all")
        self.category_combo.addItem("Raster", "raster")
        self.category_combo.addItem("Vector", "vector")
        self.asset_list = _AssetListWidget()
        self.asset_list.setDragEnabled(True)
        self.asset_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.asset_list.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.asset_list.setObjectName("scene_asset_library_list")
        self.asset_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.asset_list.setMinimumHeight(140)
        self.asset_list.setAlternatingRowColors(True)
        self.asset_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self._show_context_menu)
        self.diagnostics_label = QLabel()
        self.diagnostics_label.setObjectName("scene_asset_library_diagnostics")
        self.diagnostics_label.setWordWrap(True)

        self.import_button = QPushButton("Import")
        self.import_button.setObjectName("scene_asset_import_button")
        self.relink_button = QPushButton("Relink")
        self.relink_button.setObjectName("scene_asset_relink_button")
        self.replace_button = QPushButton("Replace")
        self.replace_button.setObjectName("scene_asset_replace_button")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("scene_asset_refresh_button")
        self.place_button = QPushButton("Place in scene")
        self.place_button.setObjectName("scene_asset_place_button")
        self.place_button.setAutoDefault(False)
        self.place_button.setMinimumWidth(128)
        self.packs_button = QPushButton("NeoEng Packs")
        self.packs_button.setObjectName("scene_asset_packs_button")
        self.packs_button.setAutoDefault(False)
        self.packs_button.clicked.connect(self._open_packs)
        for button, minimum_width in (
            (self.import_button, 98),
            (self.relink_button, 98),
            (self.replace_button, 110),
            (self.refresh_button, 110),
        ):
            button.setAutoDefault(False)
            button.setMinimumWidth(minimum_width)

        actions = QHBoxLayout()
        actions.addWidget(self.import_button)
        actions.addWidget(self.relink_button)
        actions.addWidget(self.replace_button)
        actions.addWidget(self.refresh_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.packs_button)
        filters = QHBoxLayout()
        filters.addWidget(self.search_edit, 1)
        filters.addWidget(self.category_combo)
        layout.addLayout(filters)
        layout.addWidget(self.asset_list)
        layout.addWidget(self.diagnostics_label)
        layout.addWidget(self.place_button)
        layout.addLayout(actions)

        self.asset_list.currentRowChanged.connect(self._selection_changed)
        self.search_edit.textChanged.connect(self.refresh)
        self.category_combo.currentIndexChanged.connect(self.refresh)
        self.import_button.clicked.connect(self._choose_import)
        self.relink_button.clicked.connect(self._choose_relink)
        self.replace_button.clicked.connect(self._choose_replace)
        self.refresh_button.clicked.connect(self.refresh)
        self.place_button.clicked.connect(self._place_selected_asset)
        self.session.subscribe(self.refresh)
        self.update_language("en")
        self.refresh()

    @property
    def selected_asset_id(self) -> str | None:
        item = self.asset_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value else None

    def _open_packs(self) -> None:
        from src.ui.asset_pack_dialog import AssetPackDialog

        dialog = AssetPackDialog(self)
        dialog.exec()
        dialog.deleteLater()

    def _build_context_menu(self) -> QMenu:
        menu = QMenu(self.asset_list)
        if self.current_lang == "pt":
            place_text = "Inserir na cena"
            place_tip = "Inserir o asset selecionado no centro da moldura ativa"
            refresh_text = "Atualizar"
            refresh_tip = "Atualizar a biblioteca e os diagnósticos"
        else:
            place_text = "Place in scene"
            place_tip = "Place the selected asset at the active frame center"
            refresh_text = "Refresh"
            refresh_tip = "Refresh the library and diagnostics"
        place = menu.addAction(place_text)
        place.setToolTip(place_tip)
        place.setEnabled(self.place_button.isEnabled())
        place.triggered.connect(self._place_selected_asset)
        refresh = menu.addAction(refresh_text)
        refresh.setToolTip(refresh_tip)
        refresh.triggered.connect(self.refresh)
        return menu

    def _show_context_menu(self, position) -> None:
        item = self.asset_list.itemAt(position)
        if item is None:
            return
        self.asset_list.setCurrentItem(item)
        fit_context_menu(self._build_context_menu()).exec(
            self.asset_list.mapToGlobal(position)
        )

    @property
    def selected_asset(self) -> AssetReferenceRecord | None:
        asset_id = self.selected_asset_id
        if asset_id is None:
            return None
        return next(
            (asset for asset in self.session.document.assets if asset.id == asset_id),
            None,
        )

    @property
    def inspections(self) -> dict[str, SceneAssetInspection]:
        return dict(self._inspections)

    def _inspection_for(
        self, asset: AssetReferenceRecord
    ) -> tuple[SceneAssetInspection, tuple[int, int] | None]:
        inspection = inspect_scene_asset(asset, self.project_root)
        if inspection.state != "ready" or inspection.resolved_path is None:
            return inspection, None
        if inspection.resolved_path.suffix.lower() in {".wav", ".mp3", ".ogg", ".flac"}:
            return inspection, None
        try:
            pixmap = SceneAuthoringViewport._load_asset_pixmap(inspection.resolved_path)
            if pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
                raise ValueError("asset has no positive render dimensions")
        except (OSError, ValueError) as exc:
            return (
                SceneAssetInspection(
                    asset,
                    "invalid",
                    None,
                    "Asset cannot be decoded for rendering: "
                    + user_error_message(
                        exc, operation="asset", language=self.current_lang
                    ),
                ),
                None,
            )
        return inspection, (pixmap.width(), pixmap.height())

    def refresh(self) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        selected_id = self.selected_asset_id
        try:
            inspections: dict[str, SceneAssetInspection] = {}
            dimensions: dict[str, tuple[int, int]] = {}
            with QSignalBlocker(self.asset_list):
                self.asset_list.clear()
                query = self.search_edit.text().strip().lower()
                category = str(self.category_combo.currentData() or "all")
                visible_count = 0
                for asset in self.session.document.assets:
                    asset_category = _asset_category(asset)
                    searchable = (f"{asset.id} {asset.path} {asset_category}").lower()
                    if query and query not in searchable:
                        continue
                    if category != "all" and asset_category.lower() != category:
                        continue
                    visible_count += 1
                    inspection, size = self._inspection_for(asset)
                    inspections[asset.id] = inspection
                    if size is not None:
                        dimensions[asset.id] = size
                    uses = sum(
                        item.asset_id == asset.id
                        for item in self.session.document.objects
                    )
                    state = (
                        {
                            "ready": "PRONTO",
                            "missing": "AUSENTE",
                            "modified": "MODIFICADO",
                            "invalid": "INVÁLIDO",
                            "unavailable": "INDISPONÍVEL",
                        }.get(inspection.state, inspection.state.upper())
                        if self.current_lang == "pt"
                        else _state_label(inspection.state)
                    )
                    size_text = f" · {size[0]}×{size[1]}" if size else ""
                    object_count_text = (
                        f"{uses} {'objeto' if uses == 1 else 'objetos'}"
                        if self.current_lang == "pt"
                        else f"{uses} object(s)"
                    )
                    item = QListWidgetItem(
                        f"{state}  {asset.id} — {asset.path}"
                        f" · {object_count_text}{size_text}"
                    )
                    item.setData(Qt.ItemDataRole.UserRole, asset.id)
                    item.setForeground(QBrush(QColor(_STATE_COLORS[inspection.state])))
                    if inspection.resolved_path is not None:
                        try:
                            thumbnail = SceneAuthoringViewport._load_asset_pixmap(
                                inspection.resolved_path
                            ).scaled(
                                40,
                                40,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                            item.setIcon(QIcon(thumbnail))
                        except (OSError, ValueError):
                            pass
                    issue = inspection.issue or (
                        "Nenhum problema detectado"
                        if self.current_lang == "pt"
                        else "No issue detected"
                    )
                    tooltip_labels = (
                        ("ID", "Caminho", "Estado", "Objetos", "Diagnóstico")
                        if self.current_lang == "pt"
                        else ("ID", "Path", "State", "Objects", "Diagnostic")
                    )
                    item.setToolTip(
                        f"{tooltip_labels[0]}: {asset.id}\n"
                        f"{tooltip_labels[1]}: {asset.path}\n"
                        f"SHA-256: {asset.sha256}\n"
                        f"{tooltip_labels[2]}: {state}\n"
                        f"{tooltip_labels[3]}: {uses}\n"
                        f"{tooltip_labels[4]}: {issue}"
                    )
                    self.asset_list.addItem(item)
                if selected_id:
                    for row in range(self.asset_list.count()):
                        if (
                            self.asset_list.item(row).data(Qt.ItemDataRole.UserRole)
                            == selected_id
                        ):
                            self.asset_list.setCurrentRow(row)
                            break
            self._inspections = inspections
            self._dimensions = dimensions
            issues = sum(item.state != "ready" for item in inspections.values())
            used = sum(
                item.asset_id in inspections for item in self.session.document.objects
            )
            if self.current_lang == "pt":
                self.summary_label.setText(
                    f"Assets: {len(self.session.document.assets)} · "
                    f"Exibindo: {visible_count} · Problemas: {issues} · "
                    f"Em uso: {used}"
                )
            else:
                self.summary_label.setText(
                    f"Assets: {len(self.session.document.assets)} · "
                    f"Showing: {visible_count} · Issues: {issues} · Used: {used}"
                )
            messages = [
                f"{asset.id}: {inspection.issue}"
                for asset in self.session.document.assets
                if asset.id in inspections
                and (inspection := inspections[asset.id]).issue
            ]
            self.diagnostics_label.setText(
                (
                    "Nenhum problema de asset detectado."
                    if self.current_lang == "pt"
                    else "No asset issues detected."
                )
                if not messages
                else " | ".join(messages)
            )
            self._refresh_actions()
        finally:
            self._refreshing = False

    def _selection_changed(self, _row: int) -> None:
        self._refresh_actions()
        self.asset_selected.emit(self.selected_asset_id)

    def _refresh_actions(self) -> None:
        selected = self.selected_asset
        has_project = self.project_root is not None
        self.import_button.setEnabled(has_project)
        self.replace_button.setEnabled(has_project and selected is not None)
        inspection = self._inspections.get(selected.id) if selected else None
        state = inspection.state if inspection is not None else None
        self.relink_button.setEnabled(
            has_project and selected is not None and state != "ready"
        )
        self.place_button.setEnabled(
            has_project and selected is not None and state == "ready"
        )

    def _place_selected_asset(self) -> None:
        selected = self.selected_asset
        if selected is None:
            self.status_message.emit(
                "Selecione um asset antes de inserir na cena"
                if self.current_lang == "pt"
                else "Select an asset before placing it in the scene"
            )
            return
        inspection = self._inspections.get(selected.id)
        if inspection is None or inspection.state != "ready":
            self.status_message.emit(
                "O asset selecionado não está pronto para inserção"
                if self.current_lang == "pt"
                else "The selected asset is not ready to place"
            )
            return
        self.asset_place_requested.emit(selected.id)

    def _choose_file(self, title: str) -> str:
        audio_selected = self.selected_asset is not None and Path(self.selected_asset.path).suffix.lower() in {".wav", ".mp3", ".ogg", ".flac"}
        path, _filter = QFileDialog.getOpenFileName(self, title, "", "Audio (*.wav *.mp3 *.ogg *.flac)" if audio_selected else _ASSET_FILTER)
        return path

    def _choose_import(self) -> None:
        path = self._choose_file("Import scene asset")
        if path:
            self.import_asset_from_path(path)

    def _choose_relink(self) -> None:
        path = self._choose_file("Relink scene asset")
        if path:
            self.relink_asset_from_path(path)

    def _choose_replace(self) -> None:
        path = self._choose_file("Replace scene asset")
        if path:
            self.replace_asset_from_path(path)

    def _prepare(self, path: str | Path) -> PreparedSceneAsset:
        if self.project_root is None:
            raise ValueError("Save the project before managing scene assets")
        if self.selected_asset is not None and Path(self.selected_asset.path).suffix.lower() in {".wav", ".mp3", ".ogg", ".flac"}:
            return prepare_scene_asset(path, self.project_root, allow_audio=True)
        source = validate_scene_asset_source(Path(path))
        SceneAuthoringViewport._load_asset_pixmap(source)
        prepared = prepare_scene_asset(source, self.project_root)
        SceneAuthoringViewport._load_asset_pixmap(prepared.resolved_path)
        return prepared

    def _new_asset_id(self, digest: str) -> str:
        base = "asset_" + digest[:16]
        existing = {asset.id for asset in self.session.document.assets}
        candidate = base
        suffix = 1
        while candidate in existing:
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate

    def _select_id(self, asset_id: str) -> None:
        for row in range(self.asset_list.count()):
            if self.asset_list.item(row).data(Qt.ItemDataRole.UserRole) == asset_id:
                self.asset_list.setCurrentRow(row)
                return

    def import_asset_from_path(self, path: str | Path) -> bool:
        try:
            prepared = self._prepare(path)
            existing = next(
                (
                    asset
                    for asset in self.session.document.assets
                    if asset.sha256 == prepared.sha256
                ),
                None,
            )
            if existing is not None:
                self._select_id(existing.id)
                self.status_message.emit(
                    f"Asset already in library: {existing.id}; no changes"
                )
                return False
            asset = AssetReferenceRecord(
                id=self._new_asset_id(prepared.sha256),
                path=prepared.path,
                sha256=prepared.sha256,
                source_path=prepared.source_path,
            )
            changed = self.session.add_asset(asset)
            self._select_id(asset.id)
            self.status_message.emit(
                (
                    f"Asset importado para a biblioteca: {asset.id}"
                    if self.current_lang == "pt"
                    else f"Asset imported into library: {asset.id}"
                )
                if changed
                else (
                    "A importação do asset não alterou a biblioteca"
                    if self.current_lang == "pt"
                    else "Asset import made no changes"
                )
            )
            return changed
        except (OSError, ValueError) as exc:
            self.status_message.emit(
                "Asset import rejected: "
                + user_error_message(exc, operation="asset", language=self.current_lang)
            )
            return False

    def _update_selected_from_path(
        self,
        path: str | Path,
        *,
        operation: str,
    ) -> bool:
        selected = self.selected_asset
        if selected is None:
            self.status_message.emit(f"Select an asset before {operation.lower()}")
            return False
        try:
            prepared = self._prepare(path)
            replacement = selected.model_copy(
                update={
                    "path": prepared.path,
                    "sha256": prepared.sha256,
                    "source_path": prepared.source_path,
                }
            )
            if replacement == selected:
                self.status_message.emit(f"{operation} made no changes")
                return False
            changed = self.session.update_asset(replacement)
            self._select_id(selected.id)
            self.status_message.emit(
                f"{operation} applied to {selected.id}; object links preserved"
                if changed
                else f"{operation} made no changes"
            )
            return changed
        except (OSError, ValueError) as exc:
            self.status_message.emit(
                f"{operation} rejected: "
                + user_error_message(exc, operation="asset", language=self.current_lang)
            )
            return False

    def relink_asset_from_path(self, path: str | Path) -> bool:
        selected = self.selected_asset
        if selected is None:
            self.status_message.emit("Select an asset before relinking")
            return False
        inspection = self._inspections.get(selected.id)
        if inspection is not None and inspection.state == "ready":
            self.status_message.emit(
                "Relink is available only for missing or modified assets"
            )
            return False
        return self._update_selected_from_path(path, operation="Relink")

    def replace_asset_from_path(self, path: str | Path) -> bool:
        return self._update_selected_from_path(path, operation="Replace")

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.title.setText("Assets da Cena")
            self.packs_button.setText("Pacotes NeoEng")
            self.packs_button.setToolTip("Explorar pacotes e adicionar assets ao projeto")
            self.import_button.setText("Importar")
            self.relink_button.setText("Vincular novamente")
            self.replace_button.setText("Substituir")
            self.refresh_button.setText("Atualizar")
            self.place_button.setText("Inserir na cena")
            self.search_edit.setPlaceholderText("Pesquisar assets por ID ou caminho")
            self.category_combo.setItemText(0, "Todas as categorias")
            self.category_combo.setItemText(1, "Raster")
            self.category_combo.setItemText(2, "Vetorial")
            self.import_button.setToolTip("Importar um asset para a biblioteca da cena")
            self.relink_button.setToolTip("Vincular novamente um asset ausente ou modificado")
            self.replace_button.setToolTip("Substituir o arquivo do asset selecionado")
            self.refresh_button.setToolTip("Atualizar a biblioteca e os diagnósticos")
            self.place_button.setToolTip(
                "Inserir o asset selecionado no centro da moldura ativa; o arraste continua disponível"
            )
        else:
            self.title.setText("Scene Assets")
            self.packs_button.setText("NeoEng Packs")
            self.packs_button.setToolTip("Browse packs and add assets to the project")
            self.import_button.setText("Import")
            self.relink_button.setText("Relink")
            self.replace_button.setText("Replace")
            self.refresh_button.setText("Refresh")
            self.place_button.setText("Place in scene")
            self.search_edit.setPlaceholderText("Search assets by ID or path")
            self.category_combo.setItemText(0, "All categories")
            self.category_combo.setItemText(1, "Raster")
            self.category_combo.setItemText(2, "Vector")
            self.import_button.setToolTip("Import an asset into the scene library")
            self.relink_button.setToolTip("Relink a missing or modified asset")
            self.replace_button.setToolTip("Replace the selected asset file")
            self.refresh_button.setToolTip("Refresh the library and diagnostics")
            self.place_button.setToolTip(
                "Place the selected asset at the active frame center; drag-and-drop remains available"
            )
        self.refresh()


def _state_label(state: SceneAssetState) -> str:
    return _STATE_LABELS[state]


__all__ = ["SceneAssetLibrary"]
