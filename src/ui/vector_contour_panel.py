"""Native E09 contour workflow for the professional scene inspector."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.contour_editing import ContourEditSession
from src.core.scene_asset_library import inspect_scene_asset
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.vectorization import (
    VectorizationChannel,
    VectorizationError,
    VectorizationRequest,
    VectorizationResult,
    vectorize_image_file,
)
from src.persistence.p2d05_errors import user_error_message
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import SceneTransformRecord


class VectorContourPanel(QWidget):
    """Small, explicit workflow: detect, edit, validate, cancel, create."""

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
        self._asset_id: str | None = None
        self._result: VectorizationResult | None = None
        self._editing: ContourEditSession | None = None
        self.setObjectName("professional_vector_contour_panel")

        self.title = QLabel("Vector contour")
        self.title.setObjectName("vector_contour_title")
        self.source_label = QLabel("Select a raster asset to begin")
        self.source_label.setObjectName("vector_contour_source")
        self.source_label.setWordWrap(True)
        self.state_label = QLabel("No detection")
        self.state_label.setObjectName("vector_contour_state")
        self.detect_button = QPushButton("Detect contour")
        self.detect_button.setObjectName("vector_contour_detect")
        self.simplify_button = QPushButton("Simplify")
        self.simplify_button.setObjectName("vector_contour_simplify")
        self.undo_button = QPushButton("Undo")
        self.undo_button.setObjectName("vector_contour_undo")
        self.redo_button = QPushButton("Redo")
        self.redo_button.setObjectName("vector_contour_redo")
        self.cancel_button = QPushButton("Cancel detection")
        self.cancel_button.setObjectName("vector_contour_cancel")
        self.create_button = QPushButton("Create scene object")
        self.create_button.setObjectName("vector_contour_create")
        self.vertex_index = QSpinBox()
        self.vertex_index.setObjectName("vector_contour_vertex_index")
        self.vertex_x = QDoubleSpinBox()
        self.vertex_x.setObjectName("vector_contour_vertex_x")
        self.vertex_y = QDoubleSpinBox()
        self.vertex_y.setObjectName("vector_contour_vertex_y")
        for spin in (self.vertex_x, self.vertex_y):
            spin.setRange(-1_000_000.0, 1_000_000.0)
            spin.setDecimals(2)
        self.apply_vertex_button = QPushButton("Apply vertex")
        self.apply_vertex_button.setObjectName("vector_contour_apply_vertex")
        self.diagnostics_label = QLabel(
            "Detection is hash-bound to the selected asset."
        )
        self.diagnostics_label.setObjectName("vector_contour_diagnostics")
        self.diagnostics_label.setWordWrap(True)

        actions = QGridLayout()
        actions.setHorizontalSpacing(6)
        for button in (
            self.detect_button,
            self.simplify_button,
            self.undo_button,
            self.redo_button,
            self.cancel_button,
        ):
            index = actions.count()
            actions.addWidget(button, index // 2, index % 2)
        edit = QGridLayout()
        edit.setHorizontalSpacing(6)
        self.vertex_label = QLabel("Vertex")
        edit.addWidget(self.vertex_label, 0, 0)
        edit.addWidget(self.vertex_index, 0, 1)
        edit.addWidget(QLabel("X"), 1, 0)
        edit.addWidget(self.vertex_x, 1, 1)
        edit.addWidget(QLabel("Y"), 2, 0)
        edit.addWidget(self.vertex_y, 2, 1)
        edit.addWidget(self.apply_vertex_button, 3, 0, 1, 2)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.source_label)
        layout.addWidget(self.state_label)
        layout.addLayout(actions)
        layout.addLayout(edit)
        layout.addWidget(self.create_button)
        layout.addWidget(self.diagnostics_label)

        self.detect_button.clicked.connect(self.detect_selected)
        self.simplify_button.clicked.connect(self.simplify)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.cancel_button.clicked.connect(self.cancel)
        self.apply_vertex_button.clicked.connect(self.apply_vertex)
        self.create_button.clicked.connect(self.create_object)
        self.session.subscribe(self._refresh)
        self._refresh()

    def _status(self, pt: str, en: str) -> str:
        return pt if self.current_lang == "pt" else en

    def set_selected_asset(self, asset_id: str | None) -> None:
        self._asset_id = asset_id
        self._result = None
        self._editing = None
        if asset_id is None:
            self.source_label.setText(
                "Selecione um asset raster para começar"
                if self.current_lang == "pt"
                else "Select a raster asset to begin"
            )
        else:
            self.source_label.setText(f"Asset: {asset_id}")
        self._refresh()

    def _asset(self):
        if self._asset_id is None:
            return None
        return next(
            (
                asset
                for asset in self.session.document.assets
                if asset.id == self._asset_id
            ),
            None,
        )

    def _asset_path(self) -> Path:
        asset = self._asset()
        if asset is None or self.project_root is None:
            raise VectorizationError(
                "asset_unavailable", "select a project asset first"
            )
        inspection = inspect_scene_asset(asset, self.project_root)
        if inspection.resolved_path is None:
            raise VectorizationError(
                "asset_unavailable", inspection.issue or "asset is unavailable"
            )
        return inspection.resolved_path

    def detect_selected(self) -> bool:
        try:
            path = self._asset_path()
            with Image.open(path) as image:
                channel: VectorizationChannel = (
                    "alpha" if "A" in image.getbands() else "luminance"
                )
            result = vectorize_image_file(
                path, VectorizationRequest(channel=channel, threshold=1)
            )
            self._result = result
            self._editing = ContourEditSession(result)
            self.status_message.emit(
                self._status(
                    f"Contorno detectado para {self._asset_id}: "
                    f"{len(result.polygon)} vértices",
                    f"Contour detected for {self._asset_id}: "
                    f"{len(result.polygon)} vertices",
                )
            )
            self._refresh()
            return True
        except (OSError, ValueError) as exc:
            self._result = None
            self._editing = None
            message = user_error_message(
                exc, operation="vectorization", language=self.current_lang
            )
            self.diagnostics_label.setText(message)
            self.status_message.emit(
                self._status(
                    "Detecção de contorno rejeitada: " + message,
                    "Contour detection rejected: " + message,
                )
            )
            self._refresh()
            return False

    def apply_vertex(self) -> bool:
        if self._editing is None:
            return False
        try:
            self._editing.move_vertex(
                self.vertex_index.value(),
                (self.vertex_x.value(), self.vertex_y.value()),
            )
            self.status_message.emit(
                self._status("Vértice do contorno corrigido", "Contour vertex corrected")
            )
            self._refresh()
            return True
        except VectorizationError as exc:
            self.diagnostics_label.setText(str(exc))
            self.status_message.emit(
                self._status(
                    "Correção de contorno rejeitada: " + str(exc),
                    "Contour correction rejected: " + str(exc),
                )
            )
            return False

    def simplify(self) -> bool:
        if self._editing is None:
            return False
        try:
            self._editing.simplify(1.0)
            self.status_message.emit(
                self._status(
                    "Contorno simplificado com validação geométrica",
                    "Contour simplified with geometry validation",
                )
            )
            self._refresh()
            return True
        except VectorizationError as exc:
            self.diagnostics_label.setText(str(exc))
            self.status_message.emit(
                self._status(
                    "Simplificação de contorno rejeitada: " + str(exc),
                    "Contour simplification rejected: " + str(exc),
                )
            )
            return False

    def undo(self) -> bool:
        if self._editing is None or not self._editing.can_undo:
            return False
        self._editing.undo()
        self.status_message.emit(
            self._status("Edição de contorno desfeita", "Contour edit undone")
        )
        self._refresh()
        return True

    def redo(self) -> bool:
        if self._editing is None or not self._editing.can_redo:
            return False
        self._editing.redo()
        self.status_message.emit(
            self._status("Edição de contorno refeita", "Contour edit redone")
        )
        self._refresh()
        return True

    def cancel(self) -> bool:
        if self._editing is None:
            return False
        self._editing.cancel()
        self.status_message.emit(
            self._status(
                "Detecção de contorno cancelada; origem preservada",
                "Contour detection cancelled; original source preserved",
            )
        )
        self._refresh()
        return True

    def create_object(self) -> bool:
        if self._editing is None or self._result is None or self._asset_id is None:
            return False
        if not self.session.document.layers:
            self.status_message.emit(
                self._status(
                    "Criação rejeitada: a cena não possui camada",
                    "Create object rejected: scene has no layer",
                )
            )
            return False
        base = f"vector_{self._asset_id}"
        used = {item.id for item in self.session.document.objects}
        object_id = base
        suffix = 2
        while object_id in used:
            object_id = f"{base}_{suffix}"
            suffix += 1
        try:
            changed = self.session.add_vector_object(
                self._result,
                object_id=object_id,
                asset_id=self._asset_id,
                layer_id=self.session.document.layers[0].id,
                transform=SceneTransformRecord(
                    position=Point3Record(x=0.0, y=0.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
                edited_polygon=self._editing.current_polygon,
            )
        except (OSError, ValueError) as exc:
            self.status_message.emit(
                self._status(
                    "Criação de objeto rejeitada: " + str(exc),
                    "Create object rejected: " + str(exc),
                )
            )
            return False
        self.status_message.emit(
            self._status(
                f"Objeto vetorial de cena criado: {object_id}"
                if changed
                else "Nenhum objeto criado",
                f"Vector scene object created: {object_id}"
                if changed
                else "No object created",
            )
        )
        self._refresh()
        return changed

    def _refresh(self) -> None:
        editing = self._editing is not None and not self._editing.cancelled
        self.detect_button.setEnabled(
            self._asset() is not None and self.project_root is not None
        )
        for button in (
            self.simplify_button,
            self.undo_button,
            self.redo_button,
            self.cancel_button,
            self.apply_vertex_button,
            self.create_button,
        ):
            button.setEnabled(editing)
        result = self._result
        if self._editing is not None and result is not None:
            polygon = self._editing.current_polygon
            self.state_label.setText(
                (
                    f"Detectado · {len(polygon)} vértices · "
                    f"origem {result.source_sha256[:12]}…"
                    if self.current_lang == "pt"
                    else f"Detected · {len(polygon)} vertices · "
                    f"source {result.source_sha256[:12]}…"
                )
            )
            self.vertex_index.setRange(0, max(0, len(polygon) - 1))
            point = polygon[min(self.vertex_index.value(), len(polygon) - 1)]
            self.vertex_x.setValue(float(point[0]))
            self.vertex_y.setValue(float(point[1]))
            self.undo_button.setEnabled(self._editing.can_undo)
            self.redo_button.setEnabled(self._editing.can_redo)
        else:
            self.state_label.setText(
                "Nenhuma detecção" if self.current_lang == "pt" else "No detection"
            )

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in {"en", "pt"} else "en"
        if self.current_lang == "pt":
            self.title.setText("Contorno vetorial")
            self.source_label.setText(
                "Selecione um asset raster para começar"
                if self._asset_id is None
                else f"Asset: {self._asset_id}"
            )
            self.vertex_label.setText("Vértice")
            self.detect_button.setText("Detectar contorno")
            self.simplify_button.setText("Simplificar")
            self.undo_button.setText("Desfazer")
            self.redo_button.setText("Refazer")
            self.cancel_button.setText("Cancelar detecção")
            self.create_button.setText("Criar objeto de cena")
            self.apply_vertex_button.setText("Aplicar vértice")
            self.detect_button.setToolTip("Detectar o contorno do asset selecionado")
            self.simplify_button.setToolTip(
                "Simplificar o contorno mantendo a geometria válida"
            )
            self.undo_button.setToolTip("Desfazer a última edição do contorno")
            self.redo_button.setToolTip("Refazer a última edição do contorno")
            self.cancel_button.setToolTip("Cancelar a detecção e preservar a origem")
            self.create_button.setToolTip(
                "Criar um objeto de cena a partir do contorno"
            )
            self.apply_vertex_button.setToolTip("Aplicar a posição do vértice editado")
            self.diagnostics_label.setText(
                "A detecção é vinculada por hash ao asset selecionado."
            )
        else:
            self.title.setText("Vector contour")
            self.source_label.setText(
                "Select a raster asset to begin"
                if self._asset_id is None
                else f"Asset: {self._asset_id}"
            )
            self.vertex_label.setText("Vertex")
            self.detect_button.setText("Detect contour")
            self.simplify_button.setText("Simplify")
            self.undo_button.setText("Undo")
            self.redo_button.setText("Redo")
            self.cancel_button.setText("Cancel detection")
            self.create_button.setText("Create scene object")
            self.apply_vertex_button.setText("Apply vertex")
            self.detect_button.setToolTip("Detect the contour of the selected asset")
            self.simplify_button.setToolTip(
                "Simplify the contour while preserving valid geometry"
            )
            self.undo_button.setToolTip("Undo the last contour edit")
            self.redo_button.setToolTip("Redo the last contour edit")
            self.cancel_button.setToolTip("Cancel detection and preserve the source")
            self.create_button.setToolTip("Create a scene object from the contour")
            self.apply_vertex_button.setToolTip("Apply the edited vertex position")


__all__ = ["VectorContourPanel"]
