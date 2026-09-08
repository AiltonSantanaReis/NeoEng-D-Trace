"""Small native editor for the E01 independent empty-scene lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QPainter,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.independent_scene_gestures import IndependentScenePointEditGesture
from src.core.independent_scene_session import IndependentSceneSession
from src.persistence.independent_scene_io import (
    IndependentSceneReadError,
    IndependentSceneValidationError,
    IndependentSceneWriteError,
)
from src.persistence.independent_scene_schema import upgrade_independent_scene_document
from src.persistence.project_schema import PointRecord
from src.ui.theme_tokens import THEME_TOKENS


class IndependentSceneCanvas(QFrame):
    """Small deterministic preview of the authoring document."""

    point_pressed = Signal(int)
    point_preview = Signal(int, object)
    point_released = Signal(int, object)
    empty_clicked = Signal()
    double_clicked = Signal()
    escape_pressed = Signal()
    finalize_pressed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.document = None
        self.selected_ids: tuple[str, ...] = ()
        self.object_count = 0
        self.editing_primitive_id: str | None = None
        self.editing_points: tuple[PointRecord, ...] | None = None
        self.editing_state = "idle"
        self._dragging_index: int | None = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_document(self, document: Any, selected_ids: tuple[str, ...] = ()) -> None:
        self.document = document
        self.selected_ids = selected_ids
        self.object_count = len(getattr(document, "objects", []))
        self.update()

    def set_editing_state(
        self,
        primitive_id: str | None,
        points: tuple[PointRecord, ...] | None,
        state: str = "idle",
    ) -> None:
        self.editing_primitive_id = primitive_id
        self.editing_points = points
        self.editing_state = state
        self._dragging_index = None
        self.update()

    def _viewport(self) -> tuple[float, float, float, float, float]:
        if self.document is None:
            return 0.0, 0.0, 1.0, 0.0, 0.0
        width = float(self.document.resolution.width)
        height = float(self.document.resolution.height)
        scale = min((self.width() - 48) / width, (self.height() - 48) / height)
        scale = max(0.01, scale)
        return (
            width,
            height,
            scale,
            (self.width() - width * scale) / 2.0,
            (self.height() - height * scale) / 2.0,
        )

    def _screen_to_document(self, point: QPointF) -> PointRecord:
        _, _, scale, origin_x, origin_y = self._viewport()
        return PointRecord(
            x=(point.x() - origin_x) / scale,
            y=(point.y() - origin_y) / scale,
        )

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        if self.document is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(THEME_TOKENS.canvas))
        width, height, scale, origin_x, origin_y = self._viewport()
        canvas_width = width * scale
        canvas_height = height * scale
        painter.setPen(QPen(QColor(THEME_TOKENS.border), 1))
        painter.setBrush(QBrush(QColor(THEME_TOKENS.surface)))
        painter.drawRect(origin_x, origin_y, canvas_width, canvas_height)

        for primitive in getattr(self.document, "objects", []):
            points = primitive.geometry.points
            if (
                primitive.id == self.editing_primitive_id
                and self.editing_points is not None
            ):
                points = self.editing_points
            position = primitive.transform.position
            mapped = [
                (
                    origin_x + (float(point.x) + float(position.x)) * scale,
                    origin_y + (float(point.y) + float(position.y)) * scale,
                )
                for point in points
            ]
            selected = primitive.id in self.selected_ids
            color = QColor(THEME_TOKENS.warning if selected else THEME_TOKENS.accent)
            painter.setPen(QPen(color, 3 if selected else 2))
            painter.setBrush(
                QBrush(QColor(color.red(), color.green(), color.blue(), 70))
                if primitive.geometry.filled
                else Qt.BrushStyle.NoBrush
            )
            if primitive.geometry.kind == "rectangle":
                left, top = mapped[0]
                right, bottom = mapped[1]
                painter.drawRect(
                    min(left, right),
                    min(top, bottom),
                    abs(right - left),
                    abs(bottom - top),
                )
            elif primitive.geometry.kind == "ellipse":
                left, top = mapped[0]
                right, bottom = mapped[1]
                painter.drawEllipse(
                    min(left, right),
                    min(top, bottom),
                    abs(right - left),
                    abs(bottom - top),
                )
            else:
                polygon = QPolygonF([QPointF(x, y) for x, y in mapped])
                if primitive.geometry.closed:
                    painter.drawPolygon(polygon)
                else:
                    painter.drawPolyline(polygon)
            if primitive.id == self.editing_primitive_id:
                handle_color = QColor(
                    THEME_TOKENS.error
                    if self.editing_state == "preview_invalid"
                    else THEME_TOKENS.focus
                )
                painter.setPen(QPen(handle_color, 2))
                painter.setBrush(QBrush(QColor(THEME_TOKENS.surface)))
                for x, y in mapped:
                    painter.drawEllipse(QPointF(x, y), 7.0, 7.0)
        painter.end()

    def mousePressEvent(self, event: Any) -> None:
        if (
            self.editing_primitive_id is None
            or self.editing_points is None
            or event.button() != Qt.MouseButton.LeftButton
        ):
            self.empty_clicked.emit()
            super().mousePressEvent(event)
            return
        primitive = next(
            (
                item
                for item in getattr(self.document, "objects", [])
                if item.id == self.editing_primitive_id
            ),
            None,
        )
        if primitive is None:
            self.empty_clicked.emit()
            return
        _, _, scale, origin_x, origin_y = self._viewport()
        position = primitive.transform.position
        screen_points = [
            QPointF(
                origin_x + (float(point.x) + float(position.x)) * scale,
                origin_y + (float(point.y) + float(position.y)) * scale,
            )
            for point in self.editing_points
        ]
        cursor = event.position()
        nearest = min(
            enumerate(screen_points),
            key=lambda pair: (pair[1] - cursor).manhattanLength(),
            default=None,
        )
        if nearest is None or (nearest[1] - cursor).manhattanLength() > 18.0:
            self.empty_clicked.emit()
            return
        self._dragging_index = nearest[0]
        self.point_pressed.emit(nearest[0])
        self.setFocus(Qt.FocusReason.MouseFocusReason)

    def mouseMoveEvent(self, event: Any) -> None:
        if self._dragging_index is not None:
            self.point_preview.emit(
                self._dragging_index,
                self._screen_to_document(event.position()),
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        if self._dragging_index is not None:
            index = self._dragging_index
            self._dragging_index = None
            self.point_released.emit(index, self._screen_to_document(event.position()))
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            return
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self.finalize_pressed.emit()
            return
        super().keyPressEvent(event)


class IndependentSceneWindow(QMainWindow):
    """User-facing New/Open/Save/Save As surface without a project dependency."""

    document_changed = Signal()

    _TEXT = {
        "en": {
            "title": "Independent Scene",
            "toolbar": "Scene",
            "new": "New Scene",
            "open": "Open Scene...",
            "save": "Save",
            "save_as": "Save As...",
            "resolution": "Resolution",
            "width": "Width",
            "height": "Height",
            "camera": "Camera",
            "camera_x": "Position X",
            "camera_y": "Position Y",
            "zoom": "Zoom",
            "canvas": "Empty scene canvas",
            "objects": "Objects",
            "rectangle": "Rectangle",
            "ellipse": "Ellipse",
            "polygon": "Polygon",
            "edit_points": "Edit Points",
            "duplicate": "Duplicate",
            "remove": "Remove",
            "object_position": "Object position",
            "object_x": "Object X",
            "object_y": "Object Y",
            "undo": "Undo",
            "redo": "Redo",
            "created": "{item} created.",
            "saved": "Independent scene saved.",
            "loaded": "Independent scene loaded.",
            "new_done": "New independent scene created.",
            "open_dialog": "Open Independent Scene",
            "save_dialog": "Save Independent Scene",
            "files": "Independent Scenes (*.ndtscene)",
            "unsaved_title": "Unsaved scene",
            "unsaved": "Save changes to the independent scene?",
            "error": "Independent scene operation failed: ",
            "editing_points": (
                "Editing points — drag a handle; Enter/double-click finalizes; "
                "Esc cancels."
            ),
            "edit_finalized": "Point edit finalized.",
            "edit_cancelled": "Point edit cancelled.",
            "edit_invalid": "Invalid preview: {error}",
            "edit_no_selection": "Select one object before editing points.",
        },
        "pt": {
            "title": "Cenário Independente",
            "toolbar": "Cenário",
            "new": "Novo Cenário",
            "open": "Abrir Cenário...",
            "save": "Salvar",
            "save_as": "Salvar Como...",
            "resolution": "Resolução",
            "width": "Largura",
            "height": "Altura",
            "camera": "Câmera",
            "camera_x": "Posição X",
            "camera_y": "Posição Y",
            "zoom": "Zoom",
            "canvas": "Canvas de cenário vazio",
            "objects": "Objetos",
            "rectangle": "Retângulo",
            "ellipse": "Elipse",
            "polygon": "Polígono",
            "edit_points": "Editar pontos",
            "duplicate": "Duplicar",
            "remove": "Remover",
            "object_position": "Posição do objeto",
            "object_x": "Objeto X",
            "object_y": "Objeto Y",
            "undo": "Desfazer",
            "redo": "Refazer",
            "created": "{item} criado.",
            "saved": "Cenário independente salvo.",
            "loaded": "Cenário independente aberto.",
            "new_done": "Novo cenário independente criado.",
            "open_dialog": "Abrir Cenário Independente",
            "save_dialog": "Salvar Cenário Independente",
            "files": "Cenários Independentes (*.ndtscene)",
            "unsaved_title": "Cenário não salvo",
            "unsaved": "Salvar as alterações do cenário independente?",
            "error": "Falha na operação do cenário independente: ",
            "editing_points": (
                "Editando pontos — arraste um ponto; Enter/duplo clique finaliza; "
                "Esc cancela."
            ),
            "edit_finalized": "Edição de pontos finalizada.",
            "edit_cancelled": "Edição de pontos cancelada.",
            "edit_invalid": "Prévia inválida: {error}",
            "edit_no_selection": "Selecione um objeto antes de editar os pontos.",
        },
    }

    def __init__(
        self,
        *,
        language: str = "en",
        session: IndependentSceneSession | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session or IndependentSceneSession()
        self.current_lang = language if language in self._TEXT else "en"
        self.setObjectName("independent_scene_window")
        self.setMinimumSize(760, 520)
        self.resize(980, 680)

        self.toolbar = QToolBar(self)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.new_action = QAction(self)
        self.open_action = QAction(self)
        self.save_action = QAction(self)
        self.save_as_action = QAction(self)
        self.rectangle_action = QAction(self)
        self.ellipse_action = QAction(self)
        self.polygon_action = QAction(self)
        self.edit_action = QAction(self)
        self.duplicate_action = QAction(self)
        self.remove_action = QAction(self)
        self.undo_action = QAction(self)
        self.redo_action = QAction(self)
        self.new_action.setShortcut("Ctrl+N")
        self.open_action.setShortcut("Ctrl+O")
        self.save_action.setShortcut("Ctrl+S")
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.undo_action.setShortcut("Ctrl+Z")
        self.redo_action.setShortcut("Ctrl+Y")
        self.rectangle_action.setShortcut("Ctrl+Shift+R")
        self.ellipse_action.setShortcut("Ctrl+Shift+E")
        self.polygon_action.setShortcut("Ctrl+Shift+P")
        self.edit_action.setShortcut("Ctrl+Alt+E")
        self.edit_action.setCheckable(True)
        self.duplicate_action.setShortcut("Ctrl+D")
        self.remove_action.setShortcut("Ctrl+Shift+Delete")
        for action in (
            self.new_action,
            self.open_action,
            self.save_action,
            self.save_as_action,
            self.rectangle_action,
            self.ellipse_action,
            self.polygon_action,
            self.edit_action,
            self.duplicate_action,
            self.remove_action,
            self.undo_action,
            self.redo_action,
        ):
            self.toolbar.addAction(action)
        self.new_action.triggered.connect(self.new_scene)
        self.open_action.triggered.connect(self.open_scene)
        self.save_action.triggered.connect(self.save_scene)
        self.save_as_action.triggered.connect(self.save_scene_as)
        self.rectangle_action.triggered.connect(
            lambda: self.create_primitive("rectangle")
        )
        self.ellipse_action.triggered.connect(lambda: self.create_primitive("ellipse"))
        self.polygon_action.triggered.connect(lambda: self.create_primitive("polygon"))
        self.edit_action.triggered.connect(self.toggle_point_edit)
        self.duplicate_action.triggered.connect(self.duplicate_selected)
        self.remove_action.triggered.connect(self.remove_selected)
        self.undo_action.triggered.connect(self.undo_scene)
        self.redo_action.triggered.connect(self.redo_scene)

        root = QWidget(self)
        layout = QVBoxLayout(root)
        self.canvas = IndependentSceneCanvas(root)
        self.canvas.setObjectName("independent_scene_canvas")
        self.canvas.setFrameShape(QFrame.Shape.StyledPanel)
        canvas_layout = QVBoxLayout(self.canvas)
        self.canvas_label = QLabel(self.canvas)
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_layout.addWidget(self.canvas_label)
        self.canvas_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.canvas_label.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.canvas_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.point_gesture = IndependentScenePointEditGesture()
        self.canvas.point_preview.connect(self._preview_point)
        self.canvas.point_released.connect(self._release_point)
        self.canvas.empty_clicked.connect(self.cancel_point_edit)
        self.canvas.double_clicked.connect(self.finalize_point_edit)
        self.canvas.escape_pressed.connect(self.cancel_point_edit)
        self.canvas.finalize_pressed.connect(self.finalize_point_edit)
        layout.addWidget(self.canvas, 1)

        self.objects_label = QLabel(root)
        self.object_list = QListWidget(root)
        self.object_list.setObjectName("independent_scene_object_list")
        self.object_list.setMaximumHeight(160)
        self.object_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.object_list.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.objects_label)
        layout.addWidget(self.object_list)

        form = QFormLayout()
        self.width_spin = QSpinBox(root)
        self.width_spin.setRange(1, 32768)
        self.height_spin = QSpinBox(root)
        self.height_spin.setRange(1, 32768)
        self.camera_x_spin = self._double_spin(root)
        self.camera_y_spin = self._double_spin(root)
        self.zoom_spin = self._double_spin(root)
        self.zoom_spin.setRange(0.01, 100.0)
        self.object_x_spin = self._double_spin(root)
        self.object_y_spin = self._double_spin(root)
        self.resolution_label = QLabel(root)
        self.camera_label = QLabel(root)
        self.width_label = QLabel(root)
        self.height_label = QLabel(root)
        self.camera_x_label = QLabel(root)
        self.camera_y_label = QLabel(root)
        self.zoom_label = QLabel(root)
        self.object_position_label = QLabel(root)
        self.object_x_label = QLabel(root)
        self.object_y_label = QLabel(root)
        form.addRow(self.resolution_label, QWidget(root))
        form.addRow(self.width_label, self.width_spin)
        form.addRow(self.height_label, self.height_spin)
        form.addRow(self.camera_label, QWidget(root))
        form.addRow(self.camera_x_label, self.camera_x_spin)
        form.addRow(self.camera_y_label, self.camera_y_spin)
        form.addRow(self.zoom_label, self.zoom_spin)
        form.addRow(self.object_position_label, QWidget(root))
        form.addRow(self.object_x_label, self.object_x_spin)
        form.addRow(self.object_y_label, self.object_y_spin)
        layout.addLayout(form)
        self.setCentralWidget(root)

        for widget in (
            self.width_spin,
            self.height_spin,
            self.camera_x_spin,
            self.camera_y_spin,
            self.zoom_spin,
        ):
            widget.valueChanged.connect(self._fields_changed)
        self.object_x_spin.valueChanged.connect(self._object_transform_changed)
        self.object_y_spin.valueChanged.connect(self._object_transform_changed)
        self.update_language(self.current_lang)
        self.refresh()

    @staticmethod
    def _double_spin(parent: QWidget) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(parent)
        spin.setRange(-1_000_000.0, 1_000_000.0)
        spin.setDecimals(3)
        return spin

    def _t(self, key: str) -> str:
        return self._TEXT[self.current_lang][key]

    def _fields_changed(self) -> None:
        self._apply_fields()
        self.refresh()
        self.document_changed.emit()

    def _apply_fields(self) -> None:
        self.session.set_resolution(self.width_spin.value(), self.height_spin.value())
        self.session.set_camera(
            x=self.camera_x_spin.value(),
            y=self.camera_y_spin.value(),
            zoom=self.zoom_spin.value(),
        )

    def _selection_changed(self) -> None:
        ids = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.object_list.selectedItems()
        ]
        try:
            self.session.set_selection([item for item in ids if item])
        except KeyError as exc:
            self._show_error(exc)
            return
        self.refresh()

    def _object_transform_changed(self) -> None:
        if not self.session_selection:
            return
        primitive_id = self.session_selection[0]
        document = upgrade_independent_scene_document(self.session.document)
        primitive = next(item for item in document.objects if item.id == primitive_id)
        transform = primitive.transform.model_copy(
            update={
                "position": PointRecord(
                    x=self.object_x_spin.value(),
                    y=self.object_y_spin.value(),
                )
            }
        )
        try:
            self.session.update_primitive_transform(primitive_id, transform)
        except (KeyError, PermissionError, ValueError) as exc:
            self._show_error(exc)
            return
        self.refresh()
        self.document_changed.emit()

    def refresh(self) -> None:
        document = upgrade_independent_scene_document(self.session.document)
        widgets = (
            (self.width_spin, document.resolution.width),
            (self.height_spin, document.resolution.height),
            (self.camera_x_spin, float(document.camera.position.x)),
            (self.camera_y_spin, float(document.camera.position.y)),
            (self.zoom_spin, float(document.camera.zoom)),
        )
        for widget, value in widgets:
            blocked = widget.blockSignals(True)
            if isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            else:
                widget.setValue(float(value))
            widget.blockSignals(blocked)
        dirty = " *" if self.session.is_modified else ""
        self.setWindowTitle(f"{self._t('title')} — {self.session.document_name}{dirty}")
        self.canvas_label.setText(
            f"{self._t('canvas') if self.object_count == 0 else self._t('objects')}\n"
            f"{document.resolution.width} × {document.resolution.height}\n"
            f"{document.coordinates.origin}, {document.coordinates.unit}\n"
            f"{self.object_count} {self._t('objects').lower()}"
        )
        edit_points = (
            self.point_gesture.working_points
            if self.point_gesture.primitive_id is not None
            and self.point_gesture.state in {"creating", "editing", "preview_invalid"}
            else None
        )
        edit_id = self.point_gesture.primitive_id if edit_points is not None else None
        self.canvas.set_document(document, self.session_selection)
        self.canvas.set_editing_state(edit_id, edit_points, self.point_gesture.state)
        list_signals_blocked = self.object_list.blockSignals(True)
        self.object_list.clear()
        for primitive in getattr(document, "objects", []):
            item = QListWidgetItem(
                f"{primitive.name} · {primitive.geometry.kind} · {primitive.id}"
            )
            item.setData(Qt.ItemDataRole.UserRole, primitive.id)
            self.object_list.addItem(item)
            if primitive.id in self.session_selection:
                item.setSelected(True)
        self.object_list.blockSignals(list_signals_blocked)
        selected = self.session_selection[0] if self.session_selection else None
        selected_primitive = next(
            (item for item in getattr(document, "objects", []) if item.id == selected),
            None,
        )
        for widget, value in (
            (
                self.object_x_spin,
                (
                    float(selected_primitive.transform.position.x)
                    if selected_primitive
                    else 0.0
                ),
            ),
            (
                self.object_y_spin,
                (
                    float(selected_primitive.transform.position.y)
                    if selected_primitive
                    else 0.0
                ),
            ),
        ):
            blocked = widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(blocked)
        self.undo_action.setEnabled(self.session.can_undo)
        self.redo_action.setEnabled(self.session.can_redo)
        self.duplicate_action.setEnabled(bool(self.session_selection))
        self.remove_action.setEnabled(bool(self.session_selection))
        self.edit_action.setEnabled(len(self.session_selection) == 1)
        self.edit_action.setChecked(edit_points is not None)

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in self._TEXT else "en"
        self.new_action.setText(self._t("new"))
        self.open_action.setText(self._t("open"))
        self.save_action.setText(self._t("save"))
        self.save_as_action.setText(self._t("save_as"))
        self.rectangle_action.setText(self._t("rectangle"))
        self.ellipse_action.setText(self._t("ellipse"))
        self.polygon_action.setText(self._t("polygon"))
        self.edit_action.setText(self._t("edit_points"))
        self.duplicate_action.setText(self._t("duplicate"))
        self.remove_action.setText(self._t("remove"))
        self.undo_action.setText(self._t("undo"))
        self.redo_action.setText(self._t("redo"))
        self.toolbar.setWindowTitle(self._t("toolbar"))
        self.resolution_label.setText(self._t("resolution"))
        self.width_label.setText(self._t("width"))
        self.height_label.setText(self._t("height"))
        self.camera_label.setText(self._t("camera"))
        self.camera_x_label.setText(self._t("camera_x"))
        self.camera_y_label.setText(self._t("camera_y"))
        self.zoom_label.setText(self._t("zoom"))
        self.object_position_label.setText(self._t("object_position"))
        self.object_x_label.setText(self._t("object_x"))
        self.object_y_label.setText(self._t("object_y"))
        self.objects_label.setText(self._t("objects"))
        self.refresh()

    @property
    def object_count(self) -> int:
        return self.session.object_count

    @property
    def session_selection(self) -> tuple[str, ...]:
        return tuple(
            getattr(self.session, "selection", ())
            if hasattr(self.session, "selection")
            else ()
        )

    def create_primitive(self, kind: str) -> bool:
        width = float(self.session.document.resolution.width)
        height = float(self.session.document.resolution.height)
        if kind == "rectangle":
            points = [
                PointRecord(x=width * 0.2, y=height * 0.2),
                PointRecord(x=width * 0.45, y=height * 0.4),
            ]
        elif kind == "ellipse":
            points = [
                PointRecord(x=width * 0.5, y=height * 0.2),
                PointRecord(x=width * 0.75, y=height * 0.4),
            ]
        elif kind == "polygon":
            points = [
                PointRecord(x=width * 0.2, y=height * 0.6),
                PointRecord(x=width * 0.45, y=height * 0.6),
                PointRecord(x=width * 0.325, y=height * 0.85),
            ]
        else:
            raise ValueError(f"unsupported independent primitive kind: {kind}")
        try:
            self.session.add_primitive(
                kind=kind,
                points=points,
                name=self._t(kind),
            )
        except (ValueError, PermissionError) as exc:
            self._show_error(exc)
            return False
        self.refresh()
        self.statusBar().showMessage(
            self._t("created").format(item=self._t(kind)),
            5000,
        )
        self.document_changed.emit()
        return True

    @property
    def point_edit_active(self) -> bool:
        return self.point_gesture.state in {
            "creating",
            "editing",
            "preview_invalid",
        }

    def toggle_point_edit(self) -> bool:
        if self.point_edit_active:
            return self.finalize_point_edit()
        if len(self.session_selection) != 1:
            self.edit_action.setChecked(False)
            self.statusBar().showMessage(self._t("edit_no_selection"), 5000)
            return False
        primitive_id = self.session_selection[0]
        document = upgrade_independent_scene_document(self.session.document)
        primitive = next(item for item in document.objects if item.id == primitive_id)
        try:
            self.point_gesture.begin(
                primitive_id,
                primitive.geometry,
                locked=primitive.locked,
            )
        except (KeyError, PermissionError, ValueError) as exc:
            self.edit_action.setChecked(False)
            self._show_error(exc)
            return False
        self.canvas.set_editing_state(
            primitive_id,
            self.point_gesture.working_points,
            self.point_gesture.state,
        )
        self.canvas.setFocus(Qt.FocusReason.OtherFocusReason)
        self.edit_action.setChecked(True)
        self.statusBar().showMessage(self._t("editing_points"), 5000)
        return True

    def _preview_point(self, point_index: int, point: PointRecord) -> None:
        if not self.point_edit_active:
            return
        valid = self.point_gesture.preview_point(point_index, point)
        self.canvas.set_editing_state(
            self.point_gesture.primitive_id,
            self.point_gesture.working_points,
            self.point_gesture.state,
        )
        if not valid:
            self.statusBar().showMessage(
                self._t("edit_invalid").format(
                    error=self.point_gesture.last_error or "invalid geometry",
                ),
                5000,
            )

    def _release_point(self, point_index: int, point: PointRecord) -> None:
        if not self.point_edit_active:
            return
        self._preview_point(point_index, point)
        if self.point_gesture.state == "editing":
            self.finalize_point_edit()

    def finalize_point_edit(self) -> bool:
        if not self.point_edit_active:
            return False
        try:
            points = self.point_gesture.commit()
            self.session.update_primitive_geometry(
                self.point_gesture.primitive_id or "",
                points=points,
            )
        except (KeyError, PermissionError, ValueError) as exc:
            self.point_gesture.state = "preview_invalid"
            self._show_error(exc)
            return False
        self.canvas.set_editing_state(None, None, "idle")
        self.edit_action.setChecked(False)
        self.statusBar().showMessage(self._t("edit_finalized"), 5000)
        self.refresh()
        self.document_changed.emit()
        return True

    def cancel_point_edit(self) -> bool:
        if not self.point_edit_active:
            return False
        self.point_gesture.cancel()
        self.canvas.set_editing_state(None, None, "idle")
        self.edit_action.setChecked(False)
        self.statusBar().showMessage(self._t("edit_cancelled"), 5000)
        self.refresh()
        return True

    def duplicate_selected(self) -> bool:
        if not self.session_selection:
            return False
        try:
            self.session.duplicate_selection()
        except (KeyError, PermissionError, ValueError) as exc:
            self._show_error(exc)
            return False
        self.refresh()
        self.statusBar().showMessage(self._t("duplicate"), 5000)
        self.document_changed.emit()
        return True

    def remove_selected(self) -> bool:
        if not self.session_selection:
            return False
        try:
            self.session.remove_selection()
        except (KeyError, PermissionError, ValueError) as exc:
            self._show_error(exc)
            return False
        self.refresh()
        self.statusBar().showMessage(self._t("remove"), 5000)
        self.document_changed.emit()
        return True

    def undo_scene(self) -> bool:
        changed = self.session.undo()
        if changed:
            self.refresh()
            self.document_changed.emit()
        return changed

    def redo_scene(self) -> bool:
        changed = self.session.redo()
        if changed:
            self.refresh()
            self.document_changed.emit()
        return changed

    def new_scene(self) -> bool:
        if not self._confirm_discard_or_save():
            return False
        self.session.new()
        self.refresh()
        self.statusBar().showMessage(self._t("new_done"), 5000)
        self.document_changed.emit()
        return True

    def open_scene(self) -> bool:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("open_dialog"),
            self.session.dialog_start(),
            self._t("files"),
        )
        if not path:
            return False
        try:
            self.session.load(path)
        except (IndependentSceneReadError, IndependentSceneValidationError) as exc:
            self._show_error(exc)
            return False
        self.refresh()
        self.statusBar().showMessage(self._t("loaded"), 5000)
        self.document_changed.emit()
        return True

    def save_scene(self) -> bool:
        if self.session.path is None:
            return self.save_scene_as()
        return self._save_to(self.session.path)

    def save_scene_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("save_dialog"),
            self.session.dialog_start(),
            self._t("files"),
        )
        if not path:
            return False
        return self._save_to(path)

    def _save_to(self, path: str | Path) -> bool:
        try:
            self._apply_fields()
            self.session.save(path)
        except (IndependentSceneWriteError, IndependentSceneValidationError) as exc:
            self._show_error(exc)
            return False
        self.refresh()
        self.statusBar().showMessage(self._t("saved"), 5000)
        self.document_changed.emit()
        return True

    def _confirm_discard_or_save(self) -> bool:
        if not self.session.is_modified:
            return True
        choice = QMessageBox.warning(
            self,
            self._t("unsaved_title"),
            self._t("unsaved"),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self.save_scene()
        return choice == QMessageBox.StandardButton.Discard

    def _show_error(self, exc: BaseException) -> None:
        QMessageBox.critical(self, self._t("title"), self._t("error") + str(exc))

    def closeEvent(self, event: Any) -> None:
        if self._confirm_discard_or_save():
            event.accept()
        else:
            event.ignore()


__all__ = ["IndependentSceneWindow"]
