"""Professional numeric inspector for scene object transforms."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import SceneSnapRecord, SceneTransformRecord


class SceneAuthoringInspector(QWidget):
    """Inspector with explicit numeric edits and history controls."""

    status_message = Signal(str)
    request_fit = Signal()

    def __init__(self, session: SceneAuthoringSession, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("professional_scene_inspector")
        self.setMinimumWidth(300)
        self._refreshing = False

        self.title = QLabel("Scene Inspector")
        self.selection_label = QLabel("No object selected")
        self.selection_label.setObjectName("scene_selection_summary")

        self.position_x = self._spin(-1_000_000.0, 1_000_000.0)
        self.position_y = self._spin(-1_000_000.0, 1_000_000.0)
        self.position_z = self._spin(-1_000_000.0, 1_000_000.0)
        self.rotation_x = self._spin(-360.0, 360.0)
        self.rotation_y = self._spin(-360.0, 360.0)
        self.rotation_z = self._spin(-360.0, 360.0)
        self.scale_x = self._spin(0.001, 1000.0, step=0.1)
        self.scale_y = self._spin(0.001, 1000.0, step=0.1)
        self.scale_z = self._spin(0.001, 1000.0, step=0.1)
        self.pivot_x = self._spin(0.0, 1.0, step=0.05)
        self.pivot_y = self._spin(0.0, 1.0, step=0.05)
        self.flip_x = QCheckBox("Flip X")
        self.flip_y = QCheckBox("Flip Y")
        self.snap_enabled = QCheckBox("Snap enabled")
        self.snap_spacing_x = self._spin(0.001, 100000.0, step=1.0)
        self.snap_spacing_y = self._spin(0.001, 100000.0, step=1.0)
        self.snap_spacing_x.setValue(1.0)
        self.snap_spacing_y.setValue(1.0)

        self.apply_button = QPushButton("Apply Transform")
        self.undo_button = QPushButton("Undo")
        self.redo_button = QPushButton("Redo")
        self.delete_button = QPushButton("Delete Selected")
        self.fit_button = QPushButton("Fit Selection")
        for button in (
            self.apply_button,
            self.undo_button,
            self.redo_button,
            self.delete_button,
            self.fit_button,
        ):
            button.setAutoDefault(False)

        form = QFormLayout()
        form.addRow("Selection", self.selection_label)
        form.addRow("Position X", self.position_x)
        form.addRow("Position Y", self.position_y)
        form.addRow("Depth Z", self.position_z)
        form.addRow("Rotation X", self.rotation_x)
        form.addRow("Rotation Y", self.rotation_y)
        form.addRow("Rotation Z", self.rotation_z)
        form.addRow("Scale X", self.scale_x)
        form.addRow("Scale Y", self.scale_y)
        form.addRow("Scale Z", self.scale_z)
        form.addRow("Pivot X", self.pivot_x)
        form.addRow("Pivot Y", self.pivot_y)
        form.addRow(self.flip_x)
        form.addRow(self.flip_y)
        form.addRow(self.snap_enabled)
        form.addRow("Grid X", self.snap_spacing_x)
        form.addRow("Grid Y", self.snap_spacing_y)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(form)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.fit_button)
        layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_transform)
        self.undo_button.clicked.connect(self._undo)
        self.redo_button.clicked.connect(self._redo)
        self.delete_button.clicked.connect(self._delete)
        self.fit_button.clicked.connect(self.request_fit)
        self.snap_enabled.toggled.connect(self._apply_snap)
        self.snap_spacing_x.editingFinished.connect(self._apply_snap)
        self.snap_spacing_y.editingFinished.connect(self._apply_snap)
        self.session.subscribe(self.refresh)
        self.refresh()

    @staticmethod
    def _spin(
        minimum: float,
        maximum: float,
        step: float = 1.0,
    ) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setSingleStep(step)
        widget.setDecimals(4)
        widget.setKeyboardTracking(False)
        return widget

    def _primary(self):
        primary = self.session.selection.primary
        if primary is None:
            return None
        return next(
            (item for item in self.session.document.objects if item.id == primary),
            None,
        )

    def _transform_widgets(self):
        return (
            self.position_x,
            self.position_y,
            self.position_z,
            self.rotation_x,
            self.rotation_y,
            self.rotation_z,
            self.scale_x,
            self.scale_y,
            self.scale_z,
            self.pivot_x,
            self.pivot_y,
            self.flip_x,
            self.flip_y,
        )

    def refresh(self) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            primary = self._primary()
            enabled = primary is not None
            self.selection_label.setText(
                ", ".join(self.session.selection.ids)
                if self.session.selection.ids
                else "No object selected"
            )
            for widget in self._transform_widgets():
                widget.setEnabled(enabled)
            self.apply_button.setEnabled(enabled)
            self.delete_button.setEnabled(enabled)
            self.undo_button.setEnabled(self.session.can_undo)
            self.redo_button.setEnabled(self.session.can_redo)
            if primary is None:
                return
            transform = primary.transform
            values = (
                transform.position.x,
                transform.position.y,
                transform.position.z,
                transform.rotation.x,
                transform.rotation.y,
                transform.rotation.z,
                transform.scale.x,
                transform.scale.y,
                transform.scale.z,
                transform.pivot.x,
                transform.pivot.y,
            )
            for widget, value in zip(
                (
                    self.position_x,
                    self.position_y,
                    self.position_z,
                    self.rotation_x,
                    self.rotation_y,
                    self.rotation_z,
                    self.scale_x,
                    self.scale_y,
                    self.scale_z,
                    self.pivot_x,
                    self.pivot_y,
                ),
                values,
            ):
                with QSignalBlocker(widget):
                    widget.setValue(float(value))
            with QSignalBlocker(self.flip_x):
                self.flip_x.setChecked(transform.flip_x)
            with QSignalBlocker(self.flip_y):
                self.flip_y.setChecked(transform.flip_y)
            snap = self.session.document.snap
            with QSignalBlocker(self.snap_enabled):
                self.snap_enabled.setChecked(snap.enabled)
            with QSignalBlocker(self.snap_spacing_x):
                self.snap_spacing_x.setValue(float(snap.spacing.x))
            with QSignalBlocker(self.snap_spacing_y):
                self.snap_spacing_y.setValue(float(snap.spacing.y))
        finally:
            self._refreshing = False

    def apply_transform(self) -> None:
        primary = self._primary()
        if primary is None:
            self.status_message.emit("Select an object before editing its transform")
            return
        transform = SceneTransformRecord(
            position=Point3Record(
                x=self.position_x.value(),
                y=self.position_y.value(),
                z=self.position_z.value(),
            ),
            rotation=Point3Record(
                x=self.rotation_x.value(),
                y=self.rotation_y.value(),
                z=self.rotation_z.value(),
            ),
            scale=Point3Record(
                x=self.scale_x.value(),
                y=self.scale_y.value(),
                z=self.scale_z.value(),
            ),
            pivot=PointRecord(x=self.pivot_x.value(), y=self.pivot_y.value()),
            flip_x=self.flip_x.isChecked(),
            flip_y=self.flip_y.isChecked(),
        )
        try:
            if self.session.update_transform(primary.id, transform):
                self.status_message.emit("Transform updated")
            else:
                self.status_message.emit("No transform changes")
        except (KeyError, PermissionError, ValueError) as exc:
            self.status_message.emit(str(exc))

    def _apply_snap(self) -> None:
        try:
            self.session.set_snap(
                SceneSnapRecord(
                    enabled=self.snap_enabled.isChecked(),
                    spacing=PointRecord(
                        x=self.snap_spacing_x.value(),
                        y=self.snap_spacing_y.value(),
                    ),
                )
            )
        except ValueError as exc:
            self.status_message.emit(str(exc))

    def _undo(self) -> None:
        if self.session.undo():
            self.status_message.emit("Undo applied")

    def _redo(self) -> None:
        if self.session.redo():
            self.status_message.emit("Redo applied")

    def _delete(self) -> None:
        primary = self._primary()
        if primary is not None and self.session.remove_object(primary.id):
            self.status_message.emit("Object removed")
