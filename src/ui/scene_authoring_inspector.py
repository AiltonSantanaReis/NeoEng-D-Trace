"""Professional numeric inspector for scene object transforms."""

from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
    SceneLightSocketRecord,
    SceneParallaxLayerRecord,
    SceneSnapRecord,
    SceneSocketRecord,
    SceneTransformRecord,
    SceneTriggerSocketRecord,
    SceneVfxSocketRecord,
)


class SceneAuthoringInspector(QWidget):
    """Inspector with explicit numeric edits and history controls."""

    status_message = Signal(str)
    request_fit = Signal()
    request_fit_all = Signal()

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
        self.fit_all_button = QPushButton("Fit All")
        self.fit_button.setObjectName("scene_fit_selection_button")
        self.fit_all_button.setObjectName("scene_fit_all_button")
        self.fit_button.setToolTip("Frame the visible selected objects in the viewport")
        self.fit_all_button.setToolTip("Frame all visible objects in the viewport")
        self.camera_x = self._spin(-1_000_000.0, 1_000_000.0)
        self.camera_y = self._spin(-1_000_000.0, 1_000_000.0)
        self.camera_zoom = self._spin(0.001, 1000.0, step=0.1)
        self.camera_apply_button = QPushButton("Apply Camera")
        self.layer_combo = QComboBox()
        self.parallax_depth = self._spin(0.0, 1.0, step=0.05)
        self.parallax_translation = self._spin(0.0, 1.0, step=0.05)
        self.parallax_zoom = self._spin(0.0, 1.0, step=0.05)
        self.parallax_apply_button = QPushButton("Apply Layer Parallax")
        self.socket_combo = QComboBox()
        self.socket_type = QComboBox()
        self.socket_type.addItems(["light", "vfx", "trigger"])
        self.socket_id = QLineEdit()
        self.socket_x = self._spin(-1_000_000.0, 1_000_000.0)
        self.socket_y = self._spin(-1_000_000.0, 1_000_000.0)
        self.socket_z = self._spin(-1_000_000.0, 1_000_000.0)
        self.add_socket_button = QPushButton("Add Socket")
        self.update_socket_button = QPushButton("Update Socket Position")
        self.remove_socket_button = QPushButton("Remove Socket")
        self.stage4_group = QGroupBox("Camera, Parallax & Sockets")
        stage4_form = QFormLayout(self.stage4_group)
        stage4_form.addRow("Camera X", self.camera_x)
        stage4_form.addRow("Camera Y", self.camera_y)
        stage4_form.addRow("Camera Zoom", self.camera_zoom)
        stage4_form.addRow(self.camera_apply_button)
        stage4_form.addRow("Layer", self.layer_combo)
        stage4_form.addRow("Depth", self.parallax_depth)
        stage4_form.addRow("Translation", self.parallax_translation)
        stage4_form.addRow("Zoom", self.parallax_zoom)
        stage4_form.addRow(self.parallax_apply_button)
        stage4_form.addRow("Socket", self.socket_combo)
        stage4_form.addRow("Type", self.socket_type)
        stage4_form.addRow("ID", self.socket_id)
        stage4_form.addRow("Socket X", self.socket_x)
        stage4_form.addRow("Socket Y", self.socket_y)
        stage4_form.addRow("Socket Z", self.socket_z)
        stage4_form.addRow(self.add_socket_button)
        stage4_form.addRow(self.update_socket_button)
        stage4_form.addRow(self.remove_socket_button)
        for button in (
            self.apply_button,
            self.undo_button,
            self.redo_button,
            self.delete_button,
            self.fit_button,
            self.fit_all_button,
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
        layout.addWidget(self.fit_all_button)
        layout.addWidget(self.stage4_group)
        layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_transform)
        self.undo_button.clicked.connect(self._undo)
        self.redo_button.clicked.connect(self._redo)
        self.delete_button.clicked.connect(self._delete)
        self.fit_button.clicked.connect(self.request_fit)
        self.fit_all_button.clicked.connect(self.request_fit_all)
        self.camera_apply_button.clicked.connect(self._apply_camera)
        self.parallax_apply_button.clicked.connect(self._apply_parallax)
        self.layer_combo.currentIndexChanged.connect(self._refresh_parallax_fields)
        self.socket_combo.currentIndexChanged.connect(self._refresh_socket_fields)
        self.add_socket_button.clicked.connect(self._add_socket)
        self.update_socket_button.clicked.connect(self._update_socket)
        self.remove_socket_button.clicked.connect(self._remove_socket)
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
            self._refresh_stage4_controls()
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

    def _refresh_stage4_controls(self) -> None:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            self.stage4_group.setEnabled(False)
            return
        self.stage4_group.setEnabled(True)
        with QSignalBlocker(self.camera_x):
            self.camera_x.setValue(float(document.camera.position.x))
        with QSignalBlocker(self.camera_y):
            self.camera_y.setValue(float(document.camera.position.y))
        with QSignalBlocker(self.camera_zoom):
            self.camera_zoom.setValue(float(document.camera.zoom))
        selected_layer = self.layer_combo.currentData()
        with QSignalBlocker(self.layer_combo):
            self.layer_combo.clear()
            for layer in document.layers:
                self.layer_combo.addItem(layer.name, layer.id)
            index = self.layer_combo.findData(selected_layer)
            self.layer_combo.setCurrentIndex(max(0, index))
        self._refresh_parallax_fields()
        selected_socket = self.socket_combo.currentData()
        with QSignalBlocker(self.socket_combo):
            self.socket_combo.clear()
            for socket in document.sockets:
                self.socket_combo.addItem(f"{socket.id} ({socket.type})", socket.id)
            index = self.socket_combo.findData(selected_socket)
            if index < 0 and document.sockets:
                index = len(document.sockets) - 1
            self.socket_combo.setCurrentIndex(index)
        self._refresh_socket_fields()

    def _refresh_parallax_fields(self) -> None:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            return
        layer_id = self.layer_combo.currentData()
        record = next(
            (item for item in document.parallax_layers if item.layer_id == layer_id),
            None,
        )
        values = record or SceneParallaxLayerRecord(layer_id=layer_id or "default")
        for widget, value in (
            (self.parallax_depth, values.depth),
            (self.parallax_translation, values.translation_strength),
            (self.parallax_zoom, values.zoom_strength),
        ):
            with QSignalBlocker(widget):
                widget.setValue(float(value))

    def _refresh_socket_fields(self) -> None:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            return
        socket_id = self.socket_combo.currentData()
        socket = next((item for item in document.sockets if item.id == socket_id), None)
        if socket is None:
            self.socket_id.clear()
            for widget in (self.socket_x, self.socket_y, self.socket_z):
                with QSignalBlocker(widget):
                    widget.setValue(0.0)
            return
        self.socket_id.setText(socket.id)
        with QSignalBlocker(self.socket_type):
            self.socket_type.setCurrentText(socket.type)
        for widget, value in (
            (self.socket_x, socket.position.x),
            (self.socket_y, socket.position.y),
            (self.socket_z, socket.position.z),
        ):
            with QSignalBlocker(widget):
                widget.setValue(float(value))

    def _apply_camera(self) -> None:
        try:
            changed = self.session.set_camera(
                SceneCameraAuthoringRecord(
                    position=PointRecord(
                        x=self.camera_x.value(), y=self.camera_y.value()
                    ),
                    zoom=self.camera_zoom.value(),
                )
            )
            self.status_message.emit(
                "Camera updated" if changed else "No camera changes"
            )
        except (ValueError, KeyError) as exc:
            self.status_message.emit(str(exc))

    def _apply_parallax(self) -> None:
        layer_id = self.layer_combo.currentData()
        if not layer_id:
            self.status_message.emit("Select a layer before editing parallax")
            return
        try:
            changed = self.session.set_parallax_layer(
                SceneParallaxLayerRecord(
                    layer_id=layer_id,
                    depth=self.parallax_depth.value(),
                    translation_strength=self.parallax_translation.value(),
                    zoom_strength=self.parallax_zoom.value(),
                )
            )
            self.status_message.emit(
                "Parallax updated" if changed else "No parallax changes"
            )
        except (ValueError, KeyError) as exc:
            self.status_message.emit(str(exc))

    def _add_socket(self) -> None:
        layer_id = self.layer_combo.currentData()
        socket_id = self.socket_id.text().strip()
        if not layer_id or not socket_id:
            self.status_message.emit("Socket ID and layer are required")
            return
        position = Point3Record(
            x=self.socket_x.value(), y=self.socket_y.value(), z=self.socket_z.value()
        )
        socket_type = self.socket_type.currentText()
        object_id = self.session.selection.primary
        try:
            socket: SceneSocketRecord
            if socket_type == "light":
                socket = SceneLightSocketRecord(
                    id=socket_id,
                    layer_id=layer_id,
                    object_id=object_id,
                    position=position,
                    color="#ffffff",
                )
            elif socket_type == "vfx":
                socket = SceneVfxSocketRecord(
                    id=socket_id,
                    layer_id=layer_id,
                    object_id=object_id,
                    position=position,
                    effect_id="default",
                )
            else:
                socket = SceneTriggerSocketRecord(
                    id=socket_id,
                    layer_id=layer_id,
                    object_id=object_id,
                    position=position,
                    event_id="default",
                    size=Point3Record(x=32.0, y=32.0, z=1.0),
                )
            self.session.add_socket(socket)
            self.status_message.emit("Socket added")
        except (ValueError, KeyError) as exc:
            self.status_message.emit(str(exc))

    def _update_socket(self) -> None:
        socket_id = self.socket_combo.currentData()
        if not socket_id:
            self.status_message.emit("Select a socket before editing")
            return
        try:
            self.session.update_socket_position(
                socket_id,
                Point3Record(
                    x=self.socket_x.value(),
                    y=self.socket_y.value(),
                    z=self.socket_z.value(),
                ),
            )
            self.status_message.emit("Socket updated")
        except (ValueError, KeyError) as exc:
            self.status_message.emit(str(exc))

    def _remove_socket(self) -> None:
        socket_id = self.socket_combo.currentData()
        if not socket_id:
            self.status_message.emit("Select a socket before removing")
            return
        try:
            self.session.remove_socket(socket_id)
            self.status_message.emit("Socket removed")
        except (ValueError, KeyError) as exc:
            self.status_message.emit(str(exc))

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
        count = len(self.session.selection.ids)
        try:
            changed = self.session.delete_selected()
        except (KeyError, PermissionError, ValueError) as exc:
            self.status_message.emit(str(exc))
            return
        if changed:
            self.status_message.emit(f"Deleted {count} object(s)")
        else:
            self.status_message.emit("No objects selected")
