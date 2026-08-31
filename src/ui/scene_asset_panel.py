"""Asset library and lifecycle controls for the professional scene editor."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
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


class SceneAssetLibrary(QWidget):
    """Inspectable asset list with transactional relink and replace actions."""

    status_message = Signal(str)

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
        self.asset_list = QListWidget()
        self.asset_list.setObjectName("scene_asset_library_list")
        self.asset_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.asset_list.setMinimumHeight(140)
        self.asset_list.setAlternatingRowColors(True)
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
        for button in (
            self.import_button,
            self.relink_button,
            self.replace_button,
            self.refresh_button,
        ):
            button.setAutoDefault(False)

        actions = QHBoxLayout()
        actions.addWidget(self.import_button)
        actions.addWidget(self.relink_button)
        actions.addWidget(self.replace_button)
        actions.addWidget(self.refresh_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.asset_list)
        layout.addWidget(self.diagnostics_label)
        layout.addLayout(actions)

        self.asset_list.currentRowChanged.connect(self._selection_changed)
        self.import_button.clicked.connect(self._choose_import)
        self.relink_button.clicked.connect(self._choose_relink)
        self.replace_button.clicked.connect(self._choose_replace)
        self.refresh_button.clicked.connect(self.refresh)
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
                for asset in self.session.document.assets:
                    inspection, size = self._inspection_for(asset)
                    inspections[asset.id] = inspection
                    if size is not None:
                        dimensions[asset.id] = size
                    uses = sum(
                        item.asset_id == asset.id
                        for item in self.session.document.objects
                    )
                    state = _state_label(inspection.state)
                    size_text = f" · {size[0]}×{size[1]}" if size else ""
                    item = QListWidgetItem(
                        f"{state}  {asset.id} — {asset.path}"
                        f" · {uses} object(s){size_text}"
                    )
                    item.setData(Qt.ItemDataRole.UserRole, asset.id)
                    item.setForeground(QBrush(QColor(_STATE_COLORS[inspection.state])))
                    issue = inspection.issue or "No issue detected"
                    item.setToolTip(
                        f"ID: {asset.id}\n"
                        f"Path: {asset.path}\n"
                        f"SHA-256: {asset.sha256}\n"
                        f"State: {state}\n"
                        f"Objects: {uses}\n"
                        f"Diagnostic: {issue}"
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
            self.summary_label.setText(
                f"Assets: {len(inspections)} · Issues: {issues} · Used: {used}"
            )
            messages = [
                f"{asset.id}: {inspection.issue}"
                for asset in self.session.document.assets
                if (inspection := inspections[asset.id]).issue
            ]
            self.diagnostics_label.setText(
                "No asset issues detected." if not messages else " | ".join(messages)
            )
            self._refresh_actions()
        finally:
            self._refreshing = False

    def _selection_changed(self, _row: int) -> None:
        self._refresh_actions()

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

    def _choose_file(self, title: str) -> str:
        path, _filter = QFileDialog.getOpenFileName(self, title, "", _ASSET_FILTER)
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
                f"Asset imported into library: {asset.id}"
                if changed
                else "Asset import made no changes"
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
            self.import_button.setText("Importar")
            self.relink_button.setText("Relink")
            self.replace_button.setText("Substituir")
            self.refresh_button.setText("Atualizar")
        else:
            self.title.setText("Scene Assets")
            self.import_button.setText("Import")
            self.relink_button.setText("Relink")
            self.replace_button.setText("Replace")
            self.refresh_button.setText("Refresh")
        self.refresh()


def _state_label(state: SceneAssetState) -> str:
    return _STATE_LABELS[state]


__all__ = ["SceneAssetLibrary"]
