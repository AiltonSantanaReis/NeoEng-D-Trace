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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.p2d05_errors import user_error_message
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
    SceneLightSocketRecord,
    SceneMaterialAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneSnapRecord,
    SceneSocketRecord,
    SceneTransformRecord,
    SceneTriggerSocketRecord,
    SceneVfxSocketRecord,
)
from src.ui.numeric_controls import ProtectedDoubleSpinBox, ScrubbableLabel


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
        self.current_lang = "en"
        self._refreshing = False
        self._field_labels: dict[str, QLabel] = {}

        self.title = QLabel("Scene Inspector")
        self.selection_label = QLabel("No object selected")
        self.selection_label.setObjectName("scene_selection_summary")
        self.spatial_summary = QLabel("Layer/depth: —")
        self.spatial_summary.setObjectName("scene_spatial_summary")

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
        self.camera_rotation = self._spin(-36000.0, 36000.0, step=1.0)
        self.camera_apply_button = QPushButton("Apply Camera")
        self.layer_combo = QComboBox()
        self.parallax_depth = self._spin(0.0, 1.0, step=0.05)
        self.parallax_translation = self._spin(0.0, 1.0, step=0.05)
        self.parallax_zoom = self._spin(0.0, 1.0, step=0.05)
        self.parallax_scroll_x = self._spin(-4.0, 4.0, step=0.1)
        self.parallax_scroll_y = self._spin(-4.0, 4.0, step=0.1)
        self.parallax_offset_x = self._spin(-1_000_000.0, 1_000_000.0)
        self.parallax_offset_y = self._spin(-1_000_000.0, 1_000_000.0)
        self.parallax_repeat_x = QCheckBox("Repeat X")
        self.parallax_repeat_y = QCheckBox("Repeat Y")
        self.parallax_mirror_x = QCheckBox("Mirror X")
        self.parallax_mirror_y = QCheckBox("Mirror Y")
        self.parallax_apply_button = QPushButton("Apply Layer Parallax")
        self.material_albedo = QLineEdit("#ffffff")
        self.material_emission = QLineEdit("#000000")
        self.material_normal_x = self._spin(-1.0, 1.0, step=0.05)
        self.material_normal_y = self._spin(-1.0, 1.0, step=0.05)
        self.material_normal_strength = self._spin(0.0, 1.0, step=0.05)
        self.material_emission_strength = self._spin(0.0, 16.0, step=0.1)
        self.material_opacity = self._spin(0.0, 1.0, step=0.05)
        self.material_receives_shadow = QCheckBox("Receives shadows")
        self.material_casts_shadow = QCheckBox("Casts shadows")
        self.material_apply_button = QPushButton("Apply Material")
        self.socket_combo = QComboBox()
        self.socket_type = QComboBox()
        self.socket_type.addItems(["light", "vfx", "trigger"])
        for index, socket_type in enumerate(("light", "vfx", "trigger")):
            self.socket_type.setItemData(index, socket_type)
        self.socket_light_kind = QComboBox()
        self.socket_light_kind.addItems(["point", "directional"])
        for index, light_kind in enumerate(("point", "directional")):
            self.socket_light_kind.setItemData(index, light_kind)
        self.socket_id = QLineEdit()
        self.socket_x = self._spin(-1_000_000.0, 1_000_000.0)
        self.socket_y = self._spin(-1_000_000.0, 1_000_000.0)
        self.socket_z = self._spin(-1_000_000.0, 1_000_000.0)
        self.socket_rotation_z = self._spin(-36000.0, 36000.0, step=1.0)
        self.add_socket_button = QPushButton("Add Socket")
        self.update_socket_button = QPushButton("Update Socket Position")
        self.remove_socket_button = QPushButton("Remove Socket")
        self.stage4_group = QGroupBox("Camera, Parallax & Sockets")
        self.category_tabs = QTabWidget()
        self.category_tabs.setObjectName("scene_inspector_categories")
        camera_page, parallax_page, material_page, socket_page = (
            QWidget() for _ in range(4)
        )
        stage4_form = QFormLayout(camera_page)
        self._add_labeled_row(stage4_form, "camera_x", "Camera X", self.camera_x)
        self._add_labeled_row(stage4_form, "camera_y", "Camera Y", self.camera_y)
        self._add_labeled_row(
            stage4_form, "camera_zoom", "Camera Zoom", self.camera_zoom
        )
        self._add_labeled_row(
            stage4_form,
            "camera_rotation",
            "Camera Rotation",
            self.camera_rotation,
        )
        stage4_form.addRow(self.camera_apply_button)
        stage4_form = QFormLayout(parallax_page)
        self._add_labeled_row(stage4_form, "layer", "Layer", self.layer_combo)
        self._add_labeled_row(stage4_form, "depth", "Depth", self.parallax_depth)
        self._add_labeled_row(
            stage4_form, "translation", "Translation", self.parallax_translation
        )
        self._add_labeled_row(stage4_form, "zoom", "Zoom", self.parallax_zoom)
        self._add_labeled_row(
            stage4_form, "scroll_x", "Scroll X", self.parallax_scroll_x
        )
        self._add_labeled_row(
            stage4_form, "scroll_y", "Scroll Y", self.parallax_scroll_y
        )
        self._add_labeled_row(
            stage4_form, "offset_x", "Offset X", self.parallax_offset_x
        )
        self._add_labeled_row(
            stage4_form, "offset_y", "Offset Y", self.parallax_offset_y
        )
        stage4_form.addRow(self.parallax_repeat_x)
        stage4_form.addRow(self.parallax_repeat_y)
        stage4_form.addRow(self.parallax_mirror_x)
        stage4_form.addRow(self.parallax_mirror_y)
        stage4_form.addRow(self.parallax_apply_button)
        stage4_form = QFormLayout(material_page)
        self._add_labeled_row(
            stage4_form, "material_albedo", "Albedo", self.material_albedo
        )
        self._add_labeled_row(
            stage4_form, "material_emission", "Emission", self.material_emission
        )
        self._add_labeled_row(
            stage4_form, "material_normal_x", "Normal X", self.material_normal_x
        )
        self._add_labeled_row(
            stage4_form, "material_normal_y", "Normal Y", self.material_normal_y
        )
        self._add_labeled_row(
            stage4_form,
            "material_normal_strength",
            "Normal Strength",
            self.material_normal_strength,
        )
        self._add_labeled_row(
            stage4_form,
            "material_emission_strength",
            "Emission Strength",
            self.material_emission_strength,
        )
        self._add_labeled_row(
            stage4_form, "material_opacity", "Opacity", self.material_opacity
        )
        stage4_form.addRow(self.material_receives_shadow)
        stage4_form.addRow(self.material_casts_shadow)
        stage4_form.addRow(self.material_apply_button)
        stage4_form = QFormLayout(socket_page)
        self._add_labeled_row(stage4_form, "socket", "Socket", self.socket_combo)
        self._add_labeled_row(stage4_form, "socket_type", "Type", self.socket_type)
        self._add_labeled_row(
            stage4_form, "socket_light_kind", "Light Kind", self.socket_light_kind
        )
        self._add_labeled_row(stage4_form, "socket_id", "ID", self.socket_id)
        self._add_labeled_row(stage4_form, "socket_x", "Socket X", self.socket_x)
        self._add_labeled_row(stage4_form, "socket_y", "Socket Y", self.socket_y)
        self._add_labeled_row(stage4_form, "socket_z", "Socket Z", self.socket_z)
        self._add_labeled_row(
            stage4_form, "socket_rotation_z", "Socket Rotation Z", self.socket_rotation_z
        )
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
        self._add_labeled_row(form, "selection", "Selection", self.selection_label)
        self._add_labeled_row(form, "position_x", "Position X", self.position_x)
        self._add_labeled_row(form, "position_y", "Position Y", self.position_y)
        self._add_labeled_row(form, "position_z", "Depth Z", self.position_z)
        self._add_labeled_row(form, "rotation_x", "Rotation X", self.rotation_x)
        self._add_labeled_row(form, "rotation_y", "Rotation Y", self.rotation_y)
        self._add_labeled_row(form, "rotation_z", "Rotation Z", self.rotation_z)
        self._add_labeled_row(form, "scale_x", "Scale X", self.scale_x)
        self._add_labeled_row(form, "scale_y", "Scale Y", self.scale_y)
        self._add_labeled_row(form, "scale_z", "Scale Z", self.scale_z)
        self._add_labeled_row(form, "pivot_x", "Pivot X", self.pivot_x)
        self._add_labeled_row(form, "pivot_y", "Pivot Y", self.pivot_y)
        form.addRow(self.flip_x)
        form.addRow(self.flip_y)
        form.addRow(self.snap_enabled)
        self._add_labeled_row(form, "grid_x", "Grid X", self.snap_spacing_x)
        self._add_labeled_row(form, "grid_y", "Grid Y", self.snap_spacing_y)

        root_layout = QVBoxLayout(self)
        root_layout.addWidget(self.title)
        root_layout.addWidget(self.spatial_summary)
        root_layout.addWidget(self.category_tabs)
        transform_page = QWidget()
        layout = QVBoxLayout(transform_page)
        layout.addLayout(form)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.fit_button)
        layout.addWidget(self.fit_all_button)
        layout.addStretch(1)
        for page, title in (
            (transform_page, "Object"),
            (camera_page, "Camera"),
            (parallax_page, "Layer"),
            (material_page, "Material"),
            (socket_page, "Effects"),
        ):
            self.category_tabs.addTab(page, title)
        # Compatibility enable-state for callers; controls themselves live in
        # categorized pages, no longer in a single unbounded inspector column.
        self.stage4_group.setParent(self)
        self.stage4_group.hide()

        self.apply_button.clicked.connect(self.apply_transform)
        self.undo_button.clicked.connect(self._undo)
        self.redo_button.clicked.connect(self._redo)
        self.delete_button.clicked.connect(self._delete)
        self.fit_button.clicked.connect(self.request_fit)
        self.fit_all_button.clicked.connect(self.request_fit_all)
        self.camera_apply_button.clicked.connect(self._apply_camera)
        self.parallax_apply_button.clicked.connect(self._apply_parallax)
        self.material_apply_button.clicked.connect(self._apply_material)
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

    def _add_labeled_row(
        self, layout: QFormLayout, key: str, text: str, widget: QWidget
    ) -> None:
        layout.addRow(ScrubbableLabel(text, widget), widget)
        label = layout.labelForField(widget)
        if isinstance(label, QLabel):
            self._field_labels[key] = label

    @staticmethod
    def _spin(
        minimum: float,
        maximum: float,
        step: float = 1.0,
    ) -> QDoubleSpinBox:
        widget = ProtectedDoubleSpinBox()
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

    def _status(self, pt: str, en: str) -> str:
        return pt if self.current_lang == "pt" else en

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
                else (
                    "Nenhum objeto selecionado"
                    if self.current_lang == "pt"
                    else "No object selected"
                )
            )
            self.spatial_summary.setText(
                self._spatial_summary(primary)
                if primary is not None
                else (
                    "Camada/profundidade: —"
                    if self.current_lang == "pt"
                    else "Layer/depth: —"
                )
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

    def _spatial_summary(self, primary) -> str:
        """Expose layer order and Z depth beside the active object ID."""

        layer = next(
            (
                item
                for item in self.session.document.layers
                if item.id == primary.layer_id
            ),
            None,
        )
        layer_index = next(
            (
                index
                for index, item in enumerate(self.session.document.layers)
                if item.id == primary.layer_id
            ),
            0,
        )
        layer_name = layer.name if layer is not None else primary.layer_id
        z_value = float(primary.transform.position.z)
        if self.current_lang == "pt":
            return (
                f"Camada Z{layer_index:02d}: {layer_name} · Profundidade: {z_value:.2f}"
            )
        return f"Layer Z{layer_index:02d}: {layer_name} · Depth: {z_value:.2f}"

    def _refresh_stage4_controls(self) -> None:
        document = self.session.document
        for index in range(1, self.category_tabs.count()):
            self.category_tabs.setTabEnabled(
                index, isinstance(document, SceneAuthoringDocumentV2)
            )
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
        with QSignalBlocker(self.camera_rotation):
            self.camera_rotation.setValue(float(document.camera.rotation))
        selected_layer = self.layer_combo.currentData()
        with QSignalBlocker(self.layer_combo):
            self.layer_combo.clear()
            for layer in document.layers:
                self.layer_combo.addItem(layer.name, layer.id)
            index = self.layer_combo.findData(selected_layer)
            self.layer_combo.setCurrentIndex(max(0, index))
        self._refresh_parallax_fields()
        self._refresh_material_fields()
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

    def _material_widgets(self) -> tuple[QWidget, ...]:
        return (
            self.material_albedo,
            self.material_emission,
            self.material_normal_x,
            self.material_normal_y,
            self.material_normal_strength,
            self.material_emission_strength,
            self.material_opacity,
            self.material_receives_shadow,
            self.material_casts_shadow,
            self.material_apply_button,
        )

    def _refresh_material_fields(self) -> None:
        primary = self._primary()
        material = getattr(primary, "material", None)
        # A newly placed V2 object may intentionally have no material record
        # yet.  Keep the authoring controls usable and materialize the typed
        # defaults only when the user confirms Apply Material; V1 and the
        # no-selection state remain read-only/disabled.
        enabled = isinstance(self.session.document, SceneAuthoringDocumentV2) and (
            primary is not None
        )
        for widget in self._material_widgets():
            widget.setEnabled(enabled)
        if not enabled:
            return
        if not isinstance(material, SceneMaterialAuthoringRecord):
            material = SceneMaterialAuthoringRecord()
        with QSignalBlocker(self.material_albedo):
            self.material_albedo.setText(material.albedo)
        with QSignalBlocker(self.material_emission):
            self.material_emission.setText(material.emission)
        for widget, value in (
            (self.material_normal_x, material.normal_map_xy.x),
            (self.material_normal_y, material.normal_map_xy.y),
            (self.material_normal_strength, material.normal_strength),
            (self.material_emission_strength, material.emission_strength),
            (self.material_opacity, material.opacity),
        ):
            with QSignalBlocker(widget):
                widget.setValue(float(value))
        for widget, value in (
            (self.material_receives_shadow, material.receives_shadow),
            (self.material_casts_shadow, material.casts_shadow),
        ):
            with QSignalBlocker(widget):
                widget.setChecked(bool(value))

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
            (self.parallax_scroll_x, values.scroll_x),
            (self.parallax_scroll_y, values.scroll_y),
            (self.parallax_offset_x, values.offset_x),
            (self.parallax_offset_y, values.offset_y),
        ):
            with QSignalBlocker(widget):
                widget.setValue(float(value))
        for check_widget, value in (
            (self.parallax_repeat_x, values.repeat_x),
            (self.parallax_repeat_y, values.repeat_y),
            (self.parallax_mirror_x, values.mirror_x),
            (self.parallax_mirror_y, values.mirror_y),
        ):
            with QSignalBlocker(check_widget):
                check_widget.setChecked(bool(value))

    def _refresh_socket_fields(self) -> None:
        document = self.session.document
        if not isinstance(document, SceneAuthoringDocumentV2):
            return
        socket_id = self.socket_combo.currentData()
        socket = next((item for item in document.sockets if item.id == socket_id), None)
        if socket is None:
            self.socket_id.clear()
            for widget in (
                self.socket_x,
                self.socket_y,
                self.socket_z,
                self.socket_rotation_z,
            ):
                with QSignalBlocker(widget):
                    widget.setValue(0.0)
            self.socket_light_kind.setEnabled(False)
            self.socket_rotation_z.setEnabled(False)
            return
        self.socket_id.setText(socket.id)
        with QSignalBlocker(self.socket_type):
            socket_index = self.socket_type.findData(socket.type)
            if socket_index >= 0:
                self.socket_type.setCurrentIndex(socket_index)
        if socket.type == "light":
            with QSignalBlocker(self.socket_light_kind):
                light_index = self.socket_light_kind.findData(socket.kind)
                if light_index >= 0:
                    self.socket_light_kind.setCurrentIndex(light_index)
        self.socket_light_kind.setEnabled(socket.type == "light")
        self.socket_rotation_z.setEnabled(
            socket.type == "vfx"
            or (socket.type == "light" and socket.kind == "directional")
        )
        for widget, value in (
            (self.socket_x, socket.position.x),
            (self.socket_y, socket.position.y),
            (self.socket_z, socket.position.z),
            (self.socket_rotation_z, socket.rotation.z),
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
                    rotation=self.camera_rotation.value(),
                )
            )
            self.status_message.emit(
                self._status(
                    "Câmera atualizada" if changed else "Nenhuma alteração na câmera",
                    "Camera updated" if changed else "No camera changes",
                )
            )
        except (ValueError, KeyError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def _apply_parallax(self) -> None:
        layer_id = self.layer_combo.currentData()
        if not layer_id:
            self.status_message.emit(
                self._status(
                    "Selecione uma camada antes de editar a paralaxe",
                    "Select a layer before editing parallax",
                )
            )
            return
        try:
            changed = self.session.set_parallax_layer(
                SceneParallaxLayerRecord(
                    layer_id=layer_id,
                    depth=self.parallax_depth.value(),
                    translation_strength=self.parallax_translation.value(),
                    zoom_strength=self.parallax_zoom.value(),
                    scroll_x=self.parallax_scroll_x.value(),
                    scroll_y=self.parallax_scroll_y.value(),
                    offset_x=self.parallax_offset_x.value(),
                    offset_y=self.parallax_offset_y.value(),
                    repeat_x=self.parallax_repeat_x.isChecked(),
                    repeat_y=self.parallax_repeat_y.isChecked(),
                    mirror_x=self.parallax_mirror_x.isChecked(),
                    mirror_y=self.parallax_mirror_y.isChecked(),
                )
            )
            self.status_message.emit(
                self._status(
                    (
                        "Paralaxe atualizada"
                        if changed
                        else "Nenhuma alteração na paralaxe"
                    ),
                    "Parallax updated" if changed else "No parallax changes",
                )
            )
        except (ValueError, KeyError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def _apply_material(self) -> None:
        primary = self._primary()
        if primary is None:
            self.status_message.emit(
                self._status(
                    "Selecione um objeto antes de editar o material",
                    "Select an object before editing its material",
                )
            )
            return
        try:
            changed = self.session.update_material(
                primary.id,
                SceneMaterialAuthoringRecord(
                    albedo=self.material_albedo.text().strip(),
                    emission=self.material_emission.text().strip(),
                    normal_map_xy=PointRecord(
                        x=self.material_normal_x.value(),
                        y=self.material_normal_y.value(),
                    ),
                    normal_strength=self.material_normal_strength.value(),
                    emission_strength=self.material_emission_strength.value(),
                    opacity=self.material_opacity.value(),
                    receives_shadow=self.material_receives_shadow.isChecked(),
                    casts_shadow=self.material_casts_shadow.isChecked(),
                ),
            )
            self.status_message.emit(
                self._status(
                    (
                        "Material atualizado"
                        if changed
                        else "Nenhuma alteração no material"
                    ),
                    "Material updated" if changed else "No material changes",
                )
            )
        except (KeyError, PermissionError, ValueError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def _add_socket(self) -> None:
        layer_id = self.layer_combo.currentData()
        socket_id = self.socket_id.text().strip()
        if not layer_id or not socket_id:
            self.status_message.emit(
                self._status(
                    "ID do socket e camada são obrigatórios",
                    "Socket ID and layer are required",
                )
            )
            return
        position = Point3Record(
            x=self.socket_x.value(), y=self.socket_y.value(), z=self.socket_z.value()
        )
        rotation = Point3Record(
            x=0.0,
            y=0.0,
            z=self.socket_rotation_z.value(),
        )
        socket_type = self.socket_type.currentData() or self.socket_type.currentText()
        object_id = self.session.selection.primary
        try:
            socket: SceneSocketRecord
            if socket_type == "light":
                socket = SceneLightSocketRecord(
                    id=socket_id,
                    layer_id=layer_id,
                    object_id=object_id,
                    position=position,
                    rotation=rotation,
                    kind=self.socket_light_kind.currentData() or "point",
                    color="#ffffff",
                )
            elif socket_type == "vfx":
                socket = SceneVfxSocketRecord(
                    id=socket_id,
                    layer_id=layer_id,
                    object_id=object_id,
                    position=position,
                    rotation=rotation,
                    effect_id="default",
                )
            else:
                socket = SceneTriggerSocketRecord(
                    id=socket_id,
                    layer_id=layer_id,
                    object_id=object_id,
                    position=position,
                    rotation=rotation,
                    event_id="default",
                    size=Point3Record(x=32.0, y=32.0, z=1.0),
                )
            self.session.add_socket(socket)
            self.status_message.emit(self._status("Socket adicionado", "Socket added"))
        except (ValueError, KeyError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def _update_socket(self) -> None:
        socket_id = self.socket_combo.currentData()
        if not socket_id:
            self.status_message.emit(
                self._status(
                    "Selecione um socket antes de editar",
                    "Select a socket before editing",
                )
            )
            return
        try:
            socket = next(
                item
                for item in self.session.document.sockets
                if item.id == socket_id
            )
            position = Point3Record(
                x=self.socket_x.value(),
                y=self.socket_y.value(),
                z=self.socket_z.value(),
            )
            rotation = Point3Record(
                x=float(socket.rotation.x),
                y=float(socket.rotation.y),
                z=self.socket_rotation_z.value(),
            )
            light_kind = self.socket_light_kind.currentData() or "point"
            if socket.type == "light":
                self.session.update_socket_light_kind(
                    socket_id,
                    light_kind,
                )
            self.session.update_socket_transform(
                socket_id,
                position,
                rotation,
            )
            self.status_message.emit(
                self._status("Socket atualizado", "Socket updated")
            )
        except (ValueError, KeyError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def _remove_socket(self) -> None:
        socket_id = self.socket_combo.currentData()
        if not socket_id:
            self.status_message.emit(
                self._status(
                    "Selecione um socket antes de remover",
                    "Select a socket before removing",
                )
            )
            return
        try:
            self.session.remove_socket(socket_id)
            self.status_message.emit(self._status("Socket removido", "Socket removed"))
        except (ValueError, KeyError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def apply_transform(self) -> None:
        primary = self._primary()
        if primary is None:
            self.status_message.emit(
                self._status(
                    "Selecione um objeto antes de editar sua transformação",
                    "Select an object before editing its transform",
                )
            )
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
                self.status_message.emit(
                    self._status("Transformação atualizada", "Transform updated")
                )
            else:
                self.status_message.emit(
                    self._status(
                        "Nenhuma alteração na transformação", "No transform changes"
                    )
                )
        except (KeyError, PermissionError, ValueError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

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
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )

    def update_language(self, language: str) -> None:
        for index, title in enumerate(
            ("Objeto", "Câmera", "Camada", "Material", "Efeitos")
            if language == "pt"
            else ("Object", "Camera", "Layer", "Material", "Effects")
        ):
            self.category_tabs.setTabText(index, title)
        """Translate the professional inspector without changing its model."""

        self.current_lang = language
        is_pt = language == "pt"
        labels = (
            {
                "selection": "Seleção",
                "position_x": "Posição X",
                "position_y": "Posição Y",
                "position_z": "Profundidade Z",
                "rotation_x": "Rotação X",
                "rotation_y": "Rotação Y",
                "rotation_z": "Rotação Z",
                "scale_x": "Escala X",
                "scale_y": "Escala Y",
                "scale_z": "Escala Z",
                "pivot_x": "Pivô X",
                "pivot_y": "Pivô Y",
                "grid_x": "Grade X",
                "grid_y": "Grade Y",
                "camera_x": "Câmera X",
                "camera_y": "Câmera Y",
                "camera_zoom": "Zoom da Câmera",
                "camera_rotation": "Rotação da Câmera",
                "layer": "Camada",
                "depth": "Profundidade",
                "translation": "Translação",
                "zoom": "Zoom",
                "scroll_x": "Rolagem X",
                "scroll_y": "Rolagem Y",
                "offset_x": "Deslocamento X",
                "offset_y": "Deslocamento Y",
                "socket": "Socket",
                "socket_type": "Tipo",
                "socket_light_kind": "Tipo de luz",
                "socket_id": "ID",
                "socket_x": "Socket X",
                "socket_y": "Socket Y",
                "socket_z": "Socket Z",
                "socket_rotation_z": "Rotação Z do socket",
                "material_albedo": "Albedo",
                "material_emission": "Emissão",
                "material_normal_x": "Normal X",
                "material_normal_y": "Normal Y",
                "material_normal_strength": "Força da Normal",
                "material_emission_strength": "Força da Emissão",
                "material_opacity": "Opacidade",
            }
            if is_pt
            else {
                "selection": "Selection",
                "position_x": "Position X",
                "position_y": "Position Y",
                "position_z": "Depth Z",
                "rotation_x": "Rotation X",
                "rotation_y": "Rotation Y",
                "rotation_z": "Rotation Z",
                "scale_x": "Scale X",
                "scale_y": "Scale Y",
                "scale_z": "Scale Z",
                "pivot_x": "Pivot X",
                "pivot_y": "Pivot Y",
                "grid_x": "Grid X",
                "grid_y": "Grid Y",
                "camera_x": "Camera X",
                "camera_y": "Camera Y",
                "camera_zoom": "Camera Zoom",
                "camera_rotation": "Camera Rotation",
                "layer": "Layer",
                "depth": "Depth",
                "translation": "Translation",
                "zoom": "Zoom",
                "scroll_x": "Scroll X",
                "scroll_y": "Scroll Y",
                "offset_x": "Offset X",
                "offset_y": "Offset Y",
                "socket": "Socket",
                "socket_type": "Type",
                "socket_light_kind": "Light Kind",
                "socket_id": "ID",
                "socket_x": "Socket X",
                "socket_y": "Socket Y",
                "socket_z": "Socket Z",
                "socket_rotation_z": "Socket Rotation Z",
                "material_albedo": "Albedo",
                "material_emission": "Emission",
                "material_normal_x": "Normal X",
                "material_normal_y": "Normal Y",
                "material_normal_strength": "Normal Strength",
                "material_emission_strength": "Emission Strength",
                "material_opacity": "Opacity",
            }
        )
        for key, label in self._field_labels.items():
            label.setText(labels[key])
        tooltip_text = (
            {
                "position": "Posição do objeto no espaço da cena",
                "rotation": "Rotação do objeto em graus",
                "scale": "Escala do objeto por eixo",
                "pivot": "Ponto de pivô normalizado do objeto",
                "depth": "Profundidade Z usada na ordenação de renderização",
                "grid": "Espaçamento do encaixe na grade",
                "apply": "Aplicar as alterações de transformação",
                "undo": "Desfazer a última alteração do inspetor",
                "redo": "Refazer a última alteração do inspetor",
                "fit": "Enquadrar os objetos selecionados visíveis no viewport",
                "fit_all": "Enquadrar todos os objetos visíveis no viewport",
                "camera": "Aplicar posição, zoom e rotação da câmera",
                "material": "Aplicar as propriedades visuais do material",
                "parallax": "Aplicar a configuração de paralaxe da camada",
                "socket_add": "Adicionar um socket à cena",
                "socket_update": "Atualizar posição e orientação do socket selecionado",
                "socket_remove": "Remover o socket selecionado",
            }
            if is_pt
            else {
                "position": "Object position in scene space",
                "rotation": "Object rotation in degrees",
                "scale": "Object scale by axis",
                "pivot": "Normalized object pivot point",
                "depth": "Z depth used for render ordering",
                "grid": "Grid snap spacing",
                "apply": "Apply transform changes",
                "undo": "Undo the last inspector change",
                "redo": "Redo the last inspector change",
                "fit": "Frame the visible selected objects in the viewport",
                "fit_all": "Frame all visible objects in the viewport",
                "camera": "Apply the camera position, zoom and rotation",
                "material": "Apply the material visual properties",
                "parallax": "Apply the layer parallax settings",
                "socket_add": "Add a socket to the scene",
                "socket_update": "Update the selected socket position and orientation",
                "socket_remove": "Remove the selected socket",
            }
        )
        widget_tooltips = {
            self.position_x: tooltip_text["position"],
            self.position_y: tooltip_text["position"],
            self.position_z: tooltip_text["depth"],
            self.rotation_x: tooltip_text["rotation"],
            self.rotation_y: tooltip_text["rotation"],
            self.rotation_z: tooltip_text["rotation"],
            self.scale_x: tooltip_text["scale"],
            self.scale_y: tooltip_text["scale"],
            self.scale_z: tooltip_text["scale"],
            self.pivot_x: tooltip_text["pivot"],
            self.pivot_y: tooltip_text["pivot"],
            self.snap_spacing_x: tooltip_text["grid"],
            self.snap_spacing_y: tooltip_text["grid"],
            self.apply_button: tooltip_text["apply"],
            self.undo_button: tooltip_text["undo"],
            self.redo_button: tooltip_text["redo"],
            self.fit_button: tooltip_text["fit"],
            self.fit_all_button: tooltip_text["fit_all"],
            self.camera_apply_button: tooltip_text["camera"],
            self.camera_rotation: tooltip_text["camera"],
            self.material_apply_button: tooltip_text["material"],
            self.parallax_apply_button: tooltip_text["parallax"],
            self.add_socket_button: tooltip_text["socket_add"],
            self.update_socket_button: tooltip_text["socket_update"],
            self.remove_socket_button: tooltip_text["socket_remove"],
            self.socket_rotation_z: tooltip_text["rotation"],
        }
        for widget, tooltip in widget_tooltips.items():
            widget.setToolTip(tooltip)
            widget.setStatusTip(tooltip)
            widget.setAccessibleDescription(tooltip)
        if is_pt:
            self.title.setText("Inspetor da Cena")
            self.selection_label.setText("Nenhum objeto selecionado")
            self.spatial_summary.setText("Camada/profundidade: —")
            self.stage4_group.setTitle("Câmera, Paralaxe e Sockets")
            self.apply_button.setText("Aplicar Transformação")
            self.undo_button.setText("Desfazer")
            self.redo_button.setText("Refazer")
            self.delete_button.setText("Excluir Selecionado")
            self.fit_button.setText("Enquadrar Seleção")
            self.fit_all_button.setText("Enquadrar Tudo")
            self.camera_apply_button.setText("Aplicar Câmera")
            self.parallax_apply_button.setText("Aplicar Paralaxe da Camada")
            self.material_apply_button.setText("Aplicar Material")
            self.material_receives_shadow.setText("Recebe sombras")
            self.material_casts_shadow.setText("Projeta sombras")
            self.flip_x.setText("Inverter X")
            self.flip_y.setText("Inverter Y")
            self.snap_enabled.setText("Snap habilitado")
            self.add_socket_button.setText("Adicionar socket")
            self.update_socket_button.setText("Atualizar posição do socket")
            self.remove_socket_button.setText("Remover socket")
            self.socket_type.setItemText(0, "Luz")
            self.socket_type.setItemText(1, "VFX")
            self.socket_type.setItemText(2, "Gatilho")
            self.socket_light_kind.setItemText(0, "Ponto")
            self.socket_light_kind.setItemText(1, "Direcional")
            self.repeat_x_label = "Repetir X"
            self.repeat_y_label = "Repetir Y"
            self.mirror_x_label = "Espelhar X"
            self.mirror_y_label = "Espelhar Y"
        else:
            self.title.setText("Scene Inspector")
            self.selection_label.setText("No object selected")
            self.spatial_summary.setText("Layer/depth: —")
            self.stage4_group.setTitle("Camera, Parallax & Sockets")
            self.apply_button.setText("Apply Transform")
            self.undo_button.setText("Undo")
            self.redo_button.setText("Redo")
            self.delete_button.setText("Delete Selected")
            self.fit_button.setText("Fit Selection")
            self.fit_all_button.setText("Fit All")
            self.camera_apply_button.setText("Apply Camera")
            self.parallax_apply_button.setText("Apply Layer Parallax")
            self.material_apply_button.setText("Apply Material")
            self.material_receives_shadow.setText("Receives shadows")
            self.material_casts_shadow.setText("Casts shadows")
            self.flip_x.setText("Flip X")
            self.flip_y.setText("Flip Y")
            self.snap_enabled.setText("Snap enabled")
            self.add_socket_button.setText("Add Socket")
            self.update_socket_button.setText("Update Socket Position")
            self.remove_socket_button.setText("Remove Socket")
            self.socket_type.setItemText(0, "light")
            self.socket_type.setItemText(1, "vfx")
            self.socket_type.setItemText(2, "trigger")
            self.socket_light_kind.setItemText(0, "point")
            self.socket_light_kind.setItemText(1, "directional")
            self.repeat_x_label = "Repeat X"
            self.repeat_y_label = "Repeat Y"
            self.mirror_x_label = "Mirror X"
            self.mirror_y_label = "Mirror Y"
        self.parallax_repeat_x.setText(self.repeat_x_label)
        self.parallax_repeat_y.setText(self.repeat_y_label)
        self.parallax_mirror_x.setText(self.mirror_x_label)
        self.parallax_mirror_y.setText(self.mirror_y_label)
        self.refresh()

    def _undo(self) -> None:
        if self.session.undo():
            self.status_message.emit(
                "Desfazer aplicado" if self.current_lang == "pt" else "Undo applied"
            )

    def _redo(self) -> None:
        if self.session.redo():
            self.status_message.emit(
                "Refazer aplicado" if self.current_lang == "pt" else "Redo applied"
            )

    def _delete(self) -> None:
        count = len(self.session.selection.ids)
        try:
            changed = self.session.delete_selected()
        except (KeyError, PermissionError, ValueError) as exc:
            self.status_message.emit(
                user_error_message(exc, operation="edit", language=self.current_lang)
            )
            return
        if changed:
            self.status_message.emit(
                (
                    f"{count} objeto(s) excluído(s)"
                    if self.current_lang == "pt"
                    else f"Deleted {count} object(s)"
                )
            )
        else:
            self.status_message.emit(
                "Nenhum objeto selecionado"
                if self.current_lang == "pt"
                else "No objects selected"
            )
