"""Small native editor for the E01 independent empty-scene lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.independent_scene_session import IndependentSceneSession
from src.persistence.independent_scene_io import (
    IndependentSceneReadError,
    IndependentSceneValidationError,
    IndependentSceneWriteError,
)
from src.persistence.project_schema import PointRecord


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
        for action in (
            self.new_action,
            self.open_action,
            self.save_action,
            self.save_as_action,
            self.rectangle_action,
            self.ellipse_action,
            self.polygon_action,
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
        self.undo_action.triggered.connect(self.undo_scene)
        self.redo_action.triggered.connect(self.redo_scene)

        root = QWidget(self)
        layout = QVBoxLayout(root)
        self.canvas = QFrame(root)
        self.canvas.setObjectName("independent_scene_canvas")
        self.canvas.setFrameShape(QFrame.Shape.StyledPanel)
        canvas_layout = QVBoxLayout(self.canvas)
        self.canvas_label = QLabel(self.canvas)
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_layout.addStretch(1)
        canvas_layout.addWidget(self.canvas_label)
        canvas_layout.addStretch(1)
        layout.addWidget(self.canvas, 1)

        self.objects_label = QLabel(root)
        self.object_list = QListWidget(root)
        self.object_list.setObjectName("independent_scene_object_list")
        self.object_list.setMaximumHeight(120)
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
        self.resolution_label = QLabel(root)
        self.camera_label = QLabel(root)
        self.width_label = QLabel(root)
        self.height_label = QLabel(root)
        self.camera_x_label = QLabel(root)
        self.camera_y_label = QLabel(root)
        self.zoom_label = QLabel(root)
        form.addRow(self.resolution_label, QWidget(root))
        form.addRow(self.width_label, self.width_spin)
        form.addRow(self.height_label, self.height_spin)
        form.addRow(self.camera_label, QWidget(root))
        form.addRow(self.camera_x_label, self.camera_x_spin)
        form.addRow(self.camera_y_label, self.camera_y_spin)
        form.addRow(self.zoom_label, self.zoom_spin)
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

    def refresh(self) -> None:
        document = self.session.document
        widgets = (
            (self.width_spin, document.resolution.width),
            (self.height_spin, document.resolution.height),
            (self.camera_x_spin, float(document.camera.position.x)),
            (self.camera_y_spin, float(document.camera.position.y)),
            (self.zoom_spin, float(document.camera.zoom)),
        )
        for widget, value in widgets:
            blocked = widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(blocked)
        dirty = " *" if self.session.is_modified else ""
        self.setWindowTitle(f"{self._t('title')} — {self.session.document_name}{dirty}")
        self.canvas_label.setText(
            f"{self._t('canvas')}\n"
            f"{document.resolution.width} × {document.resolution.height}\n"
            f"{document.coordinates.origin}, {document.coordinates.unit}\n"
            f"{self.object_count} {self._t('objects').lower()}"
        )
        self.object_list.clear()
        for primitive in getattr(document, "objects", []):
            self.object_list.addItem(
                f"{primitive.name} · {primitive.geometry.kind} · {primitive.id}"
            )
        self.undo_action.setEnabled(self.session.can_undo)
        self.redo_action.setEnabled(self.session.can_redo)

    def update_language(self, language: str) -> None:
        self.current_lang = language if language in self._TEXT else "en"
        self.new_action.setText(self._t("new"))
        self.open_action.setText(self._t("open"))
        self.save_action.setText(self._t("save"))
        self.save_as_action.setText(self._t("save_as"))
        self.rectangle_action.setText(self._t("rectangle"))
        self.ellipse_action.setText(self._t("ellipse"))
        self.polygon_action.setText(self._t("polygon"))
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
        self.objects_label.setText(self._t("objects"))
        self.refresh()

    @property
    def object_count(self) -> int:
        return self.session.object_count

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
